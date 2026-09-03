"""Teste T1 — resolução efetiva: extrai quadro com grade, calcula px/m e projeta mão/rosto em px."""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

from .config import Config

MAO_M = 0.08    # largura da mão de criança
ROSTO_M = 0.12  # largura do rosto de criança
LIMIAR_PX = 100  # abaixo disso, landmarks de mão/AUs de rosto ficam pouco confiáveis


def quadro(cfg: Config, video: Path, t_s: float, saida: Path, grade: int = 100) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    vf = f"drawgrid=w={grade}:h={grade}:t=1:color=yellow@0.6"
    cmd = [cfg.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t_s:.3f}", "-i", str(video),
           "-frames:v", "1", "-vf", vf, "-q:v", "2", str(saida)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"falha ao extrair quadro: {r.stderr.strip()[-300:]}")
    print(f"quadro salvo em {saida} — grade a cada {grade} px (leia coordenadas contando linhas × {grade})")
    return saida


def pxm(p1: tuple[float, float], p2: tuple[float, float], metros: float) -> dict:
    dist_px = math.dist(p1, p2)
    ppm = dist_px / metros
    mao = ppm * MAO_M
    rosto = ppm * ROSTO_M
    r = {"distancia_px": round(dist_px, 1), "px_por_m": round(ppm, 1),
         "mao_px": round(mao), "rosto_px": round(rosto),
         "mao_ok": mao >= LIMIAR_PX, "rosto_ok": rosto >= LIMIAR_PX}
    print(f"{dist_px:.0f} px para {metros} m → {ppm:.0f} px/m nessa profundidade")
    print(f"mão de criança ≈ {mao:.0f} px  {'OK' if r['mao_ok'] else 'ABAIXO de %d px → landmarks de mão pouco confiáveis' % LIMIAR_PX}")
    print(f"rosto de criança ≈ {rosto:.0f} px  {'OK' if r['rosto_ok'] else 'ABAIXO de %d px → AUs pouco confiáveis' % LIMIAR_PX}")
    fator = LIMIAR_PX / mao if mao > 0 else float("inf")
    if not r["mao_ok"]:
        print(f"para mão ≥ {LIMIAR_PX} px aqui: {fator:.1f}× a resolução linear, ou câmera {fator:.1f}× mais perto")
    return r
