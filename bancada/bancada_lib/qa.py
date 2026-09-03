"""QA de gravação (teste T16 e variáveis de camada 0): manifesto por segmento, uptime por
câmera e janela, lacunas, GB/dia, estimativa de quadros perdidos."""
from __future__ import annotations

import csv
import json
import re
import time
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import Config
from .ffm import probe, resumo_probe


_RE_NOME = re.compile(r"_(\d{8})[_T](\d{6})\.[A-Za-z0-9]+$")   # _AAAAMMDD_HHMMSS ou _AAAAMMDDTHHMMSS


def inicio_do_nome(arquivo: str | Path) -> float | None:
    """Época Unix do início do segmento a partir de ..._AAAAMMDD_HHMMSS.ext (strftime do ffmpeg,
    que usa o fuso local do computador de captura — daí time.mktime, e não o fuso do config)."""
    m = _RE_NOME.search(Path(arquivo).name)
    if not m:
        return None
    try:
        t = time.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        return float(time.mktime(t))
    except ValueError:
        return None


def _dia_dir(cfg: Config, dia: date) -> Path:
    return cfg.bruto / f"{dia:%Y}" / f"{dia:%m}" / f"{dia:%d}"


def segmentos_do_dia(cfg: Config, dia: date) -> list[Path]:
    base = _dia_dir(cfg, dia)
    return sorted(base.rglob(f"*.{cfg.container}")) if base.exists() else []


def manifesto(cfg: Config, dia: date, recalcular: bool = False) -> list[dict]:
    """Um registro por segmento, com cache em raiz/manifesto/<dia>.jsonl."""
    mdir = cfg.raiz / "manifesto"
    mdir.mkdir(parents=True, exist_ok=True)
    cache_path = mdir / f"{dia.isoformat()}.jsonl"
    cache: dict[str, dict] = {}
    if cache_path.exists() and not recalcular:
        for linha in cache_path.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                r = json.loads(linha)
                cache[r["arquivo"]] = r
    registros: list[dict] = []
    for seg in segmentos_do_dia(cfg, dia):
        chave = str(seg)
        tamanho = seg.stat().st_size
        r = cache.get(chave)
        if r and r.get("tamanho_bytes") == tamanho and not r.get("erro"):
            registros.append(r)
            continue
        p = resumo_probe(probe(cfg.ffprobe, seg, contar_pacotes=True, timeout=300))
        sala, cam = seg.parent.parent.name, seg.parent.name
        r = {"arquivo": chave, "sala": sala, "cam": cam, "dia": dia.isoformat(), **p}
        if not p.get("erro"):
            ini = inicio_do_nome(seg)
            if ini is None:  # arquivo fora do padrão de nome: tenta o relógio do contêiner
                ini = p["start_time"] if p["start_time"] > 1e9 else None
            r["start_time"] = ini if ini is not None else 0.0
            r["inicio_utc"] = datetime.fromtimestamp(ini, ZoneInfo("UTC")).isoformat() if ini else None
            r["fim_utc"] = (datetime.fromtimestamp(ini + p["duracao_s"], ZoneInfo("UTC")).isoformat()
                            if ini else None)
            esperado = p["duracao_s"] * p["fps"] if p["fps"] else 0
            r["quadros_perdidos_est"] = int(round(max(0.0, esperado - p["pacotes_video"]))) if esperado else None
        registros.append(r)
    with cache_path.open("w", encoding="utf-8") as fh:
        for r in registros:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return registros


def _janelas_do_dia(cfg: Config, dia: date) -> list[tuple[datetime, datetime]]:
    """Janelas realmente tentadas (logs/<dia>/janela_*.json); senão, as do config."""
    tz = ZoneInfo(cfg.fuso)
    out = []
    ldir = cfg.raiz / "logs" / dia.isoformat()
    for jf in sorted(ldir.glob("janela_*.json")) if ldir.exists() else []:
        try:
            j = json.loads(jf.read_text(encoding="utf-8"))
            out.append((datetime.fromisoformat(j["inicio_utc"]).astimezone(tz),
                        datetime.fromisoformat(j["fim_utc"]).astimezone(tz)))
        except (KeyError, ValueError):
            continue
    if out:
        return out
    for ini, fim in cfg.janelas:
        h1, m1 = map(int, ini.split(":")); h2, m2 = map(int, fim.split(":"))
        out.append((datetime(dia.year, dia.month, dia.day, h1, m1, tzinfo=tz),
                    datetime(dia.year, dia.month, dia.day, h2, m2, tzinfo=tz)))
    return out


def relatorio(cfg: Config, dia: date, recalcular: bool = False) -> Path:
    regs = manifesto(cfg, dia, recalcular=recalcular)
    tz = ZoneInfo(cfg.fuso)
    janelas = _janelas_do_dia(cfg, dia)
    por_cam: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in regs:
        if not r.get("erro") and r.get("inicio_utc"):
            por_cam[(r["sala"], r["cam"])].append(r)
    # garante que o dia começa às 00:00 no fuso do config, para bater com as janelas

    linhas: list[dict] = []
    for (sala, cam), segs in sorted(por_cam.items()):
        segs.sort(key=lambda r: r["start_time"])
        for (jini, jfim) in janelas:
            t0, t1 = jini.timestamp(), jfim.timestamp()
            dentro = [s for s in segs if s["start_time"] + s["duracao_s"] > t0 and s["start_time"] < t1]
            gravado = sum(min(s["start_time"] + s["duracao_s"], t1) - max(s["start_time"], t0) for s in dentro)
            lacunas = []
            cursor = t0
            for s in dentro:
                if s["start_time"] - cursor > 2.0:
                    lacunas.append((cursor, s["start_time"]))
                cursor = max(cursor, s["start_time"] + s["duracao_s"])
            if t1 - cursor > 2.0 and dentro:
                lacunas.append((cursor, t1))
            gb = sum(s["tamanho_bytes"] for s in dentro) / 1e9
            perd = sum(s.get("quadros_perdidos_est") or 0 for s in dentro)
            fps = max((s["fps"] for s in dentro), default=0)
            res = f"{dentro[0]['largura']}x{dentro[0]['altura']}" if dentro else "-"
            linhas.append({
                "dia": dia.isoformat(), "sala": sala, "cam": cam,
                "janela": f"{jini:%H:%M}-{jfim:%H:%M}",
                "segmentos": len(dentro),
                "camera_uptime_frac": round(min(1.0, gravado / (t1 - t0)), 4) if t1 > t0 else 0,
                "gravado_min": round(gravado / 60, 1),
                "lacunas": len(lacunas),
                "maior_lacuna_s": round(max((b - a for a, b in lacunas), default=0), 1),
                "quadros_perdidos_est": perd,
                "resolucao": res, "fps": round(fps, 2),
                "gb": round(gb, 3),
                "bitrate_medio_kbps": int(sum(s["bitrate_kbps"] for s in dentro) / len(dentro)) if dentro else 0,
            })

    rdir = cfg.raiz / "relatorios" / dia.isoformat()
    rdir.mkdir(parents=True, exist_ok=True)
    csv_path = rdir / "qa.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        campos = list(linhas[0].keys()) if linhas else ["dia", "sala", "cam", "janela"]
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)

    gb_total = sum(l["gb"] for l in linhas)
    erros = [r for r in regs if r.get("erro")]
    md = [f"# QA de gravação — {dia.isoformat()}", "",
          f"segmentos: **{len(regs)}** · com erro de leitura: **{len(erros)}** · total: **{gb_total:.2f} GB**", "",
          "| sala | cam | janela | seg. | uptime | gravado (min) | lacunas | maior lacuna (s) | quadros perdidos ≈ | res | fps | GB | kbps |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for l in linhas:
        md.append(f"| {l['sala']} | {l['cam']} | {l['janela']} | {l['segmentos']} | {l['camera_uptime_frac']:.1%} | "
                  f"{l['gravado_min']} | {l['lacunas']} | {l['maior_lacuna_s']} | {l['quadros_perdidos_est']} | "
                  f"{l['resolucao']} | {l['fps']} | {l['gb']:.2f} | {l['bitrate_medio_kbps']} |")
    if erros:
        md += ["", "## Arquivos com erro", ""] + [f"- `{e['arquivo']}` — {e['erro']}" for e in erros]
    md += ["", "## Leitura", "",
           "- `camera_uptime_frac` < 0.98 numa janela → câmera caiu; veja `logs/<dia>/<cam>_<janela>.log`.",
           "- `quadros_perdidos_est` alto com uptime alto → rede/RTSP soltando pacotes; considere sub-stream ou cabo.",
           "- GB e kbps por câmera projetam o armazenamento (Parte III §10 do plano): GB/dia × 200 dias/ano.",
           "- Os tempos vêm do relógio do computador de captura (`-use_wallclock_as_timestamps`); a sincronização fina "
           "entre câmeras é medida em `bancada.py sync`."]
    (rdir / "qa.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rdir / "qa.md"
