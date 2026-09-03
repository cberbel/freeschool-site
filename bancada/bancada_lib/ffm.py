"""Auxiliares de ffmpeg/ffprobe."""
from __future__ import annotations

import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path


def localizar(binario: str) -> str:
    caminho = shutil.which(binario)
    if not caminho:
        raise SystemExit(
            f"'{binario}' não encontrado no PATH.\n"
            "Instale o ffmpeg (Windows: winget install Gyan.FFmpeg · Ubuntu: sudo apt install ffmpeg · "
            "macOS: brew install ffmpeg) ou aponte 'ffmpeg.binario' no config.yaml."
        )
    return caminho


def fps_de(texto: str | None) -> float:
    if not texto or texto in ("0/0", "N/A"):
        return 0.0
    try:
        return float(Fraction(texto))
    except (ValueError, ZeroDivisionError):
        return 0.0


def probe(ffprobe: str, arquivo: str | Path, contar_pacotes: bool = False, timeout: int = 60) -> dict:
    """ffprobe em JSON. contar_pacotes lê o arquivo inteiro (rápido, sem decodificar)."""
    cmd = [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams"]
    if contar_pacotes:
        cmd += ["-count_packets"]
    cmd += [str(arquivo)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"erro": f"ffprobe timeout ({timeout}s)"}
    if out.returncode != 0:
        return {"erro": (out.stderr or "").strip()[-400:]}
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"erro": "ffprobe: JSON inválido"}


def resumo_probe(p: dict) -> dict:
    """Extrai o que interessa: vídeo (codec, WxH, fps, pacotes), áudio, duração, tamanho, start."""
    if "erro" in p:
        return {"erro": p["erro"]}
    fmt = p.get("format", {})
    v = next((s for s in p.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in p.get("streams", []) if s.get("codec_type") == "audio"), None)
    r = {
        "duracao_s": float(fmt.get("duration") or 0),
        "tamanho_bytes": int(fmt.get("size") or 0),
        "start_time": float(fmt.get("start_time") or 0),
        "bitrate_kbps": int(fmt.get("bit_rate") or 0) // 1000,
        "video_codec": v.get("codec_name") if v else None,
        "largura": int(v.get("width") or 0) if v else 0,
        "altura": int(v.get("height") or 0) if v else 0,
        "fps": fps_de(v.get("avg_frame_rate")) if v else 0.0,
        "pacotes_video": int(v.get("nb_read_packets") or 0) if v else 0,
        "audio_codec": a.get("codec_name") if a else None,
        "audio_hz": int(a.get("sample_rate") or 0) if a else 0,
    }
    return r


def encoders_disponiveis(ffmpeg: str) -> set[str]:
    out = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True)
    nomes = set()
    for linha in out.stdout.splitlines():
        partes = linha.split()
        if len(partes) >= 2 and partes[0] and partes[0][0] in "VAS" and len(partes[0]) == 6:
            nomes.add(partes[1])
    return nomes
