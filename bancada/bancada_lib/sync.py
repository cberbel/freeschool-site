"""Sincronização entre câmeras por áudio (teste T2): correlação cruzada dos envelopes de áudio
das câmeras da mesma sala num trecho comum → deslocamento em ms por câmera, relativo à primeira.
Repete no fim da janela para estimar deriva. Sem áudio → só o relógio de parede.
"""
from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path

import numpy as np

from .config import Config
from .qa import manifesto

HZ = 8000       # taxa de decodificação
ENV_HZ = 200    # taxa do envelope → resolução de 5 ms


def _pcm(ffmpeg: str, arquivo: str, ss: float, dur: float) -> np.ndarray | None:
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{ss:.3f}", "-t", f"{dur:.3f}",
           "-i", arquivo, "-vn", "-ac", "1", "-ar", str(HZ), "-f", "s16le", "-"]
    out = subprocess.run(cmd, capture_output=True, timeout=120)
    if out.returncode != 0 or len(out.stdout) < HZ:  # menos de 1 s → sem áudio útil
        return None
    return np.frombuffer(out.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def _envelope(x: np.ndarray) -> np.ndarray:
    passo = HZ // ENV_HZ
    n = len(x) // passo
    env = np.abs(x[: n * passo]).reshape(n, passo).mean(axis=1)
    env = np.diff(env, prepend=env[0])          # onsets (mudanças) sincronizam melhor que energia
    env = np.maximum(env, 0)
    env -= env.mean()
    s = env.std()
    return env / s if s > 0 else env


def _lag_ms(ref: np.ndarray, outro: np.ndarray, max_ms: int = 2000) -> tuple[float, float]:
    n = min(len(ref), len(outro))
    ref, outro = ref[:n], outro[:n]
    max_lag = int(max_ms / 1000 * ENV_HZ)
    corr = np.correlate(outro, ref, mode="full")[n - 1 - max_lag: n + max_lag]
    lags = np.arange(-max_lag, max_lag + 1)
    i = int(np.argmax(corr))
    pico = corr[i]
    # confiança: pico principal vs. segundo pico fora de ±50 ms
    mascara = np.abs(lags - lags[i]) > int(0.05 * ENV_HZ)
    segundo = corr[mascara].max() if mascara.any() else 0.0
    conf = float(pico / segundo) if segundo > 0 else float("inf")
    return float(lags[i] * 1000 / ENV_HZ), conf


def _segmentos_cam(regs: list[dict], sala: str, cam: str) -> list[dict]:
    return sorted((r for r in regs if not r.get("erro") and r["sala"] == sala and r["cam"] == cam
                   and r.get("start_time")), key=lambda r: r["start_time"])


def _pcm_intervalo(ffmpeg: str, segs: list[dict], t: float, dur: float) -> np.ndarray | None:
    """PCM do intervalo absoluto [t, t+dur), concatenando segmentos consecutivos quando o trecho
    cruza uma fronteira de arquivo (cada arquivo começa em pts 0 — -reset_timestamps)."""
    partes: list[np.ndarray] = []
    cursor = t
    fim = t + dur
    for seg in segs:
        ini, dur_seg = seg["start_time"], seg["duracao_s"]
        if ini + dur_seg <= cursor or ini >= fim:
            continue
        if ini > cursor + 1.0:          # buraco na gravação → trecho inválido
            return None
        if not seg.get("audio_codec"):
            return None
        ss = max(0.0, cursor - ini)
        pedaco = min(fim, ini + dur_seg) - max(cursor, ini)
        if pedaco <= 0:
            continue
        pcm = _pcm(ffmpeg, seg["arquivo"], ss, pedaco)
        if pcm is None:
            return None
        partes.append(pcm)
        cursor = max(cursor, ini) + pedaco
        if cursor >= fim - 0.5:
            break
    if not partes or cursor < fim - 1.0:
        return None
    return np.concatenate(partes)


def medir(cfg: Config, dia: date, trecho_s: int = 120) -> Path:
    regs = manifesto(cfg, dia)
    from .qa import _janelas_do_dia
    resultado: dict = {"dia": dia.isoformat(), "salas": {}}
    for sala in cfg.salas:
        cams = [c.id for c in cfg.cameras_da_sala(sala)]
        resultado["salas"][sala] = {}
        for (jini, jfim) in _janelas_do_dia(cfg, dia):
            rot = f"{jini:%H:%M}-{jfim:%H:%M}"
            dur_j = jfim.timestamp() - jini.timestamp()
            margem = min(60.0, max(0.0, (dur_j - trecho_s) / 4))
            pontos = {"inicio": jini.timestamp() + margem, "fim": jfim.timestamp() - margem - trecho_s}
            if pontos["fim"] <= pontos["inicio"]:
                pontos = {"inicio": jini.timestamp() + margem}
            saida = {"referencia": cams[0] if cams else None, "cameras": {}, "nota": None}
            for cam in cams:
                saida["cameras"][cam] = {}
            for nome_ponto, t in pontos.items():
                envs: dict[str, np.ndarray] = {}
                for cam in cams:
                    pcm = _pcm_intervalo(cfg.ffmpeg, _segmentos_cam(regs, sala, cam), t, trecho_s)
                    if pcm is not None and pcm.std() > 1e-4:
                        envs[cam] = _envelope(pcm)
                if len(envs) < 2:
                    saida["nota"] = ("menos de duas câmeras com áudio utilizável neste trecho — "
                                     "sincronização só pelo relógio de parede")
                    continue
                ref_cam = cams[0] if cams[0] in envs else sorted(envs)[0]
                saida["referencia"] = ref_cam
                for cam, env in envs.items():
                    if cam == ref_cam:
                        saida["cameras"][cam][nome_ponto] = {"offset_ms": 0.0, "conf": None}
                        continue
                    lag, conf = _lag_ms(envs[ref_cam], env)
                    saida["cameras"][cam][nome_ponto] = {"offset_ms": round(lag, 1), "conf": round(conf, 2)}
            for cam, d in saida["cameras"].items():
                if "inicio" in d and "fim" in d:
                    d["sync_drift_ms"] = round(d["fim"]["offset_ms"] - d["inicio"]["offset_ms"], 1)
            resultado["salas"][sala][rot] = saida
    rdir = cfg.raiz / "relatorios" / dia.isoformat()
    rdir.mkdir(parents=True, exist_ok=True)
    out = rdir / "sync.json"
    out.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# Sincronização por áudio — {dia.isoformat()}", "",
          "Deslocamento de cada câmera em relação à referência (ms; positivo = atrasada). "
          "`conf` = razão entre o pico principal e o segundo pico; abaixo de ~1,5 o resultado é duvidoso. "
          "`sync_drift_ms` = variação do deslocamento entre o início e o fim da janela.", ""]
    for sala, jan in resultado["salas"].items():
        md.append(f"## {sala}")
        for rot, s in jan.items():
            md.append(f"\n**{rot}** — referência `{s['referencia']}`" + (f" — _{s['nota']}_" if s.get("nota") else ""))
            md.append("\n| cam | offset início (ms) | conf | offset fim (ms) | conf | deriva (ms) |")
            md.append("|---|---|---|---|---|---|")
            for cam, d in s["cameras"].items():
                i, f = d.get("inicio", {}), d.get("fim", {})
                md.append(f"| {cam} | {i.get('offset_ms', '-')} | {i.get('conf', '-')} | {f.get('offset_ms', '-')} | "
                          f"{f.get('conf', '-')} | {d.get('sync_drift_ms', '-')} |")
        md.append("")
    md += ["## Leitura", "",
           "- |offset| > 200 ms entre câmeras compromete a análise de atenção conjunta (Parte III §14 do plano) → "
           "exigir sincronização em hardware (PTP/genlock) na especificação de compra.",
           "- deriva > 50 ms em 2 h indica relógios internos das câmeras à deriva; o offset medido aqui é aplicado "
           "automaticamente pela análise (`sync.json`)."]
    (rdir / "sync.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return rdir / "sync.md"


def offsets_para(cfg: Config, dia: date, sala: str, cam: str) -> float:
    """Offset (s) a somar aos timestamps desta câmera, se sync.json existir; senão 0."""
    p = cfg.raiz / "relatorios" / dia.isoformat() / "sync.json"
    if not p.exists():
        return 0.0
    d = json.loads(p.read_text(encoding="utf-8"))
    for _, s in d.get("salas", {}).get(sala, {}).items():
        c = s.get("cameras", {}).get(cam, {})
        if "inicio" in c and c["inicio"].get("offset_ms") is not None:
            return -c["inicio"]["offset_ms"] / 1000.0
    return 0.0
