"""Captura agendada: janelas diárias, um ffmpeg por câmera, segmentos de N minutos, reinício
automático, parada graciosa. Os arquivos ficam em raiz/bruto/AAAA/MM/DD/<sala>/<cam>/.

Relógio: o MKV zera os timestamps de cada arquivo (e -copyts corrompe MKV com época Unix), então o
início de cada segmento vem do NOME do arquivo (strftime, relógio do computador, resolução de 1 s),
com as fronteiras alinhadas ao relógio por -segment_atclocktime. O alinhamento fino entre câmeras
(< 1 s) é medido por correlação de áudio (sync.py) — ou, no definitivo, por sincronização em
hardware (PTP/genlock), decisão da Fase 0.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import Camera, Config, redigir
from .ffm import localizar, probe, resumo_probe


@dataclass
class Janela:
    dia: date
    inicio: datetime
    fim: datetime

    @property
    def rotulo(self) -> str:
        return f"{self.dia.isoformat()} {self.inicio:%H:%M}-{self.fim:%H:%M}"

    @property
    def slug(self) -> str:
        return f"{self.dia:%Y%m%d}_{self.inicio:%H%M}-{self.fim:%H%M}"


def planejar(cfg: Config, agora: datetime | None = None) -> list[Janela]:
    """Próximas janelas em `cfg.dias` dias letivos, pulando as que já passaram hoje."""
    tz = ZoneInfo(cfg.fuso)
    agora = agora or datetime.now(tz)
    janelas: list[Janela] = []
    d = agora.date()
    dias_incluidos = 0
    while dias_incluidos < cfg.dias:
        if cfg.apenas_dias_uteis and d.weekday() >= 5:
            d += timedelta(days=1)
            continue
        do_dia: list[Janela] = []
        for ini, fim in cfg.janelas:
            h1, m1 = map(int, ini.split(":"))
            h2, m2 = map(int, fim.split(":"))
            j = Janela(
                dia=d,
                inicio=datetime.combine(d, dtime(h1, m1), tz),
                fim=datetime.combine(d, dtime(h2, m2), tz),
            )
            if j.fim > agora:  # ainda dá para gravar (mesmo que parcialmente)
                do_dia.append(j)
        if do_dia:
            janelas.extend(do_dia)
            dias_incluidos += 1
        d += timedelta(days=1)
    return janelas


def dir_saida(cfg: Config, cam: Camera, dia: date) -> Path:
    return cfg.bruto / f"{dia:%Y}" / f"{dia:%m}" / f"{dia:%d}" / cam.sala / cam.id


def comando_ffmpeg(cfg: Config, cam: Camera, destino: Path, log: Path) -> list[str]:
    padrao = destino / f"{cam.nome}_%Y%m%d_%H%M%S.{cfg.container}"
    return [
        cfg.ffmpeg, "-hide_banner", "-loglevel", "warning", "-nostats",
        *cam.args_entrada,
        "-use_wallclock_as_timestamps", "1",
        "-i", cam.url,
        *cam.args_saida,
        "-f", "segment",
        "-segment_time", str(cfg.segmento_s),
        "-segment_atclocktime", "1",
        "-reset_timestamps", "1",
        "-segment_format", cfg.container,
        "-strftime", "1",
        str(padrao),
    ]


@dataclass
class Gravador:
    cfg: Config
    cam: Camera
    destino: Path
    log: Path
    proc: subprocess.Popen | None = None
    reinicios: int = 0
    backoff: float = 2.0
    ultimo_inicio: float = 0.0
    _log_fh: object = field(default=None, repr=False)

    def iniciar(self):
        self.destino.mkdir(parents=True, exist_ok=True)
        self._log_fh = open(self.log, "a", encoding="utf-8")
        cmd = comando_ffmpeg(self.cfg, self.cam, self.destino, self.log)
        self._log_fh.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] start: "
                           f"{' '.join(redigir(c) for c in cmd)}\n")
        self._log_fh.flush()
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=self._log_fh, stderr=subprocess.STDOUT,
        )
        self.ultimo_inicio = time.time()

    def vivo(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def reiniciar_se_morto(self, agora: float) -> bool:
        if self.vivo():
            # correu bem por um tempo → zera o backoff
            if agora - self.ultimo_inicio > 60:
                self.backoff = 2.0
            return False
        if agora - self.ultimo_inicio < self.backoff:
            return False
        self.reinicios += 1
        self.backoff = min(self.backoff * 2, 60.0)
        self.iniciar()
        return True

    def parar(self, espera_s: float = 10.0):
        if not self.proc:
            return
        if self.vivo():
            try:
                self.proc.stdin.write(b"q")  # parada graciosa: fecha o segmento corrente
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError, ValueError):
                pass
            try:
                self.proc.wait(timeout=espera_s)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
        if self._log_fh:
            self._log_fh.write(f"[{datetime.now().isoformat(timespec='seconds')}] stop "
                               f"(rc={self.proc.returncode}, reinícios={self.reinicios})\n")
            self._log_fh.close()
            self._log_fh = None


def _print(msg: str):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def gravar_janela(cfg: Config, j: Janela, cameras: list[Camera], pos_janela=None) -> dict:
    tz = ZoneInfo(cfg.fuso)
    logs = cfg.raiz / "logs" / f"{j.dia:%Y-%m-%d}"
    logs.mkdir(parents=True, exist_ok=True)
    gravadores = [
        Gravador(cfg, cam, dir_saida(cfg, cam, j.dia), logs / f"{cam.nome}_{j.slug}.log")
        for cam in cameras
    ]
    _print(f"janela {j.rotulo}: iniciando {len(gravadores)} câmera(s)")
    for g in gravadores:
        g.iniciar()
    ultimo_status = 0.0
    try:
        while datetime.now(tz) < j.fim:
            agora = time.time()
            for g in gravadores:
                if g.reiniciar_se_morto(agora):
                    _print(f"  {g.cam.nome}: ffmpeg caiu — reiniciado (#{g.reinicios}, backoff {g.backoff:.0f}s). "
                           f"veja {g.log.name}")
            if agora - ultimo_status > 300:
                vivos = sum(g.vivo() for g in gravadores)
                _print(f"  gravando… {vivos}/{len(gravadores)} câmeras vivas; fim às {j.fim:%H:%M}")
                ultimo_status = agora
            time.sleep(2)
    except KeyboardInterrupt:
        _print("interrompido pelo usuário — fechando segmentos…")
        raise
    finally:
        for g in gravadores:
            g.parar()
    registro = {
        "janela": j.rotulo, "slug": j.slug,
        "inicio_utc": j.inicio.astimezone(ZoneInfo("UTC")).isoformat(),
        "fim_utc": j.fim.astimezone(ZoneInfo("UTC")).isoformat(),
        "cameras": [{"nome": g.cam.nome, "reinicios": g.reinicios, "dir": str(g.destino)} for g in gravadores],
    }
    (cfg.raiz / "logs" / f"{j.dia:%Y-%m-%d}" / f"janela_{j.slug}.json").write_text(
        json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    _print(f"janela {j.rotulo} encerrada. reinícios: " +
           ", ".join(f"{g.cam.nome}={g.reinicios}" for g in gravadores))
    if pos_janela:
        try:
            pos_janela(j)
        except Exception as e:  # QA não pode derrubar a captura
            _print(f"  pós-janela falhou: {e}")
    return registro


def capturar(cfg: Config, cameras: list[Camera] | None = None, agora_teste: bool = False,
             duracao_teste_s: int = 60, pos_janela=None):
    localizar(cfg.ffmpeg)
    cameras = cameras or cfg.cameras
    tz = ZoneInfo(cfg.fuso)
    if agora_teste:
        ini = datetime.now(tz)
        janelas = [Janela(ini.date(), ini, ini + timedelta(seconds=duracao_teste_s))]
    else:
        janelas = planejar(cfg)
    _print(f"plano: {len(janelas)} janela(s)")
    for j in janelas:
        _print(f"  {j.rotulo}")
    for j in janelas:
        espera = (j.inicio - datetime.now(tz)).total_seconds()
        while espera > 0:
            _print(f"aguardando {j.rotulo} ({espera/60:.0f} min)…")
            time.sleep(min(espera, 300))
            espera = (j.inicio - datetime.now(tz)).total_seconds()
        gravar_janela(cfg, j, cameras, pos_janela=pos_janela)
    _print("plano concluído.")


def smoke(cfg: Config, segundos: int = 20) -> list[dict]:
    """Testa cada câmera: ffprobe (codec/resolução/fps/áudio) + gravação curta. Roda ANTES da janela."""
    localizar(cfg.ffmpeg)
    localizar(cfg.ffprobe)
    tmp = cfg.raiz / "smoke"
    tmp.mkdir(parents=True, exist_ok=True)
    resultados = []
    canais_ok: dict[str, str] = {}
    for cam in cfg.cameras:
        print(f"\n== {cam.nome}")
        # 1) probe em cada variante de URL (caminho: auto) até uma responder com vídeo
        r: dict = {}
        if cam.url.startswith("rtsp"):
            for cand in (cam.candidatas or [cam.url]):
                rc = resumo_probe(probe(cfg.ffprobe, cand, timeout=25))
                if not rc.get("erro") and rc.get("video_codec"):
                    cam.url = cand
                    r = rc
                    print(f"   {redigir(cand)}: OK")
                    break
                print(f"   {redigir(cand)}: {rc.get('erro') or 'sem vídeo'}")
        if r.get("video_codec"):
            canais_ok[cam.nome] = cam.url
            print(f"   stream: {r['video_codec']} {r['largura']}x{r['altura']} @ {r['fps']:.1f} fps · "
                  f"áudio: {r['audio_codec'] or 'NENHUM'}")
        elif cam.url.startswith("rtsp"):
            print("   nenhuma variante respondeu — RTSP ligado no NVR? senha? canal certo?")
        # 2) gravação curta
        destino = tmp / cam.nome
        destino.mkdir(parents=True, exist_ok=True)
        for antigo in destino.glob(f"*.{cfg.container}"):
            antigo.unlink()
        g = Gravador(cfg, cam, destino, tmp / f"{cam.nome}.log")
        g.iniciar()
        t0 = time.time()
        while time.time() - t0 < segundos and g.vivo():
            time.sleep(0.5)
        morreu_cedo = not g.vivo()
        g.parar()
        arquivos = sorted(destino.glob(f"*.{cfg.container}"))
        if not arquivos or morreu_cedo:
            cauda = g.log.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-6:]
            print(f"   gravação: FALHOU. últimas linhas do log:")
            for l in cauda:
                print(f"     {l}")
            resultados.append({"camera": cam.nome, "ok": False, "log": str(g.log)})
            continue
        p = resumo_probe(probe(cfg.ffprobe, arquivos[-1], contar_pacotes=True))
        esperado = p["duracao_s"] * p["fps"] if p.get("fps") else 0
        perdidos = max(0, int(round(esperado - p.get("pacotes_video", 0)))) if esperado else None
        print(f"   gravou {p['duracao_s']:.1f}s · {p['largura']}x{p['altura']} @ {p['fps']:.1f} fps · "
              f"{p['bitrate_kbps']} kbps · {p['tamanho_bytes']/1e6:.1f} MB · pacotes {p['pacotes_video']}"
              + (f" · quadros perdidos ≈ {perdidos}" if perdidos is not None else ""))
        gb_dia = p["bitrate_kbps"] * 1000 / 8 * 4 * 3600 / 1e9  # 4 h/dia (duas janelas de 2 h)
        print(f"   projeção: {gb_dia:.1f} GB/dia nesta câmera (4 h/dia)")
        resultados.append({"camera": cam.nome, "ok": True, **p, "gb_dia_4h": round(gb_dia, 2)})
    (tmp / "smoke.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    if canais_ok:
        import yaml
        (cfg.raiz / "canais-ok.yaml").write_text(
            "# gerado pelo smoke: variante de URL que respondeu, por câmera (usada automaticamente pelo capturar)\n"
            + yaml.safe_dump(canais_ok, allow_unicode=True, sort_keys=True), encoding="utf-8")
        print(f"\nURLs que responderam gravadas em {cfg.raiz/'canais-ok.yaml'} (o capturar usa estas).")
    ok = sum(1 for r in resultados if r["ok"])
    print(f"smoke: {ok}/{len(resultados)} câmeras OK. detalhes em {tmp/'smoke.json'}")
    if ok < len(resultados):
        sys.exit(1)
    return resultados
