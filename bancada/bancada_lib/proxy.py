"""Proxies 1080p (Parte III §10 do plano): entrada da detecção global; o original fica para crops."""
from __future__ import annotations

import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from .config import Config
from .ffm import encoders_disponiveis
from .qa import segmentos_do_dia


def destino_proxy(cfg: Config, seg: Path) -> Path:
    rel = seg.relative_to(cfg.bruto)
    return cfg.raiz / "proxy" / rel.with_suffix(".mkv")


def _cmd(cfg: Config, seg: Path, dst: Path, enc: str, fps: float | None) -> list[str]:
    vf = f"scale=-2:{cfg.proxy_altura}"
    if fps:
        vf += f",fps={fps}"
    if enc == "libx265":
        v = ["-c:v", "libx265", "-preset", "medium", "-crf", "28", "-tag:v", "hvc1"]
    else:
        v = ["-c:v", "libx264", "-preset", "medium", "-crf", "23"]
    return [cfg.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(seg),
            "-map", "0", "-vf", vf, *v, "-c:a", "copy", "-copyts", str(dst)]


def gerar(cfg: Config, dia: date, fps: float | None = None, workers: int = 2, forcar: bool = False) -> list[Path]:
    encs = encoders_disponiveis(cfg.ffmpeg)
    enc = "libx265" if "libx265" in encs else "libx264"
    print(f"proxy: codec {enc}, altura {cfg.proxy_altura}" + (f", fps {fps}" if fps else ""))
    feitos: list[Path] = []

    def um(seg: Path) -> Path | None:
        dst = destino_proxy(cfg, seg)
        if dst.exists() and not forcar:
            return dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(_cmd(cfg, seg, dst, enc, fps), capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  FALHOU {seg.name}: {r.stderr.strip()[-200:]}")
            return None
        print(f"  ok {dst.relative_to(cfg.raiz)}  {dst.stat().st_size/1e6:.0f} MB")
        return dst

    segs = segmentos_do_dia(cfg, dia)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for d in ex.map(um, segs):
            if d:
                feitos.append(d)
    print(f"proxy: {len(feitos)}/{len(segs)} segmentos")
    return feitos
