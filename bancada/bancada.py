#!/usr/bin/env python3
"""Bancada — Fase 0. Uso: python bancada.py <comando> [opções]. Veja README.md."""
from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bancada_lib import capture, config as cfgmod  # noqa: E402


def _dia(texto: str | None) -> date:
    return date.fromisoformat(texto) if texto else date.today()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bancada", description="Fase 0 — captura, QA, sync, proxy, medidas, análise")
    ap.add_argument("--config", default="config.yaml", help="arquivo de configuração (padrão: config.yaml)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("planejar", help="mostra as janelas que seriam gravadas")

    p = sub.add_parser("smoke", help="testa cada câmera: probe + gravação curta (RODE ANTES da janela)")
    p.add_argument("--segundos", type=int, default=20)

    p = sub.add_parser("capturar", help="grava as janelas configuradas por N dias; roda QA ao fim de cada janela")
    p.add_argument("--sala", help="só esta sala")
    p.add_argument("--agora", action="store_true", help="ignora o plano e grava já, por --segundos (teste)")
    p.add_argument("--segundos", type=int, default=60)
    p.add_argument("--sem-qa", action="store_true")

    p = sub.add_parser("qa", help="relatório de qualidade da gravação de um dia")
    p.add_argument("--dia", help="AAAA-MM-DD (padrão: hoje)")
    p.add_argument("--recalcular", action="store_true")

    p = sub.add_parser("sync", help="deslocamento entre câmeras por áudio (T2)")
    p.add_argument("--dia")
    p.add_argument("--trecho", type=int, default=120, help="segundos de áudio por medição")

    p = sub.add_parser("proxy", help="gera proxies 1080p do dia")
    p.add_argument("--dia")
    p.add_argument("--fps", type=float, help="reduzir fps do proxy (ex.: 15)")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--forcar", action="store_true")

    p = sub.add_parser("frame", help="extrai um quadro com grade de 100 px (T1)")
    p.add_argument("video")
    p.add_argument("--t", type=float, default=30.0, help="segundo do vídeo")
    p.add_argument("--saida", default=None)

    p = sub.add_parser("pxm", help="px/m a partir de dois pontos e a distância real (T1)")
    p.add_argument("--p1", required=True, help="x,y em px")
    p.add_argument("--p2", required=True, help="x,y em px")
    p.add_argument("--metros", type=float, required=True)

    p = sub.add_parser("analisar", help="detecção + tracking + pose + mãos num vídeo (T5/T6/T8/T9)")
    p.add_argument("video")
    p.add_argument("--modelo", default="yolo11n-pose.pt", help="yolo11n-pose.pt · yolo11s-pose.pt · yolo11n.pt (sem pose)")
    p.add_argument("--imgsz", type=int, default=960)
    p.add_argument("--conf", type=float, default=0.3)
    p.add_argument("--stride", type=int, default=1, help="processa 1 a cada N quadros")
    p.add_argument("--sem-maos", action="store_true")
    p.add_argument("--maos-stride", type=int, default=5)
    p.add_argument("--modelo-maos", help="hand_landmarker.task (padrão: data/modelos/, baixado na 1ª vez)")
    p.add_argument("--max-quadros", type=int)
    p.add_argument("--dispositivo", help="cpu · 0 (GPU NVIDIA) · mps")
    p.add_argument("--saida")

    a = ap.parse_args(argv)
    cfg = cfgmod.carregar(a.config)

    if a.cmd == "planejar":
        for j in capture.planejar(cfg):
            print(j.rotulo)
        print(f"{len(cfg.cameras)} câmera(s) em {len(cfg.salas)} sala(s): " + ", ".join(c.nome for c in cfg.cameras))
        print(f"destino: {cfg.bruto}")
        return

    if a.cmd == "smoke":
        capture.smoke(cfg, segundos=a.segundos)
        return

    if a.cmd == "capturar":
        cams = cfg.cameras_da_sala(a.sala) if a.sala else None
        if a.sala and not cams:
            raise SystemExit(f"sala '{a.sala}' não existe no config. salas: {cfg.salas}")
        from bancada_lib import qa
        def pos(j):
            if a.sem_qa:
                return
            rel = qa.relatorio(cfg, j.dia)
            print(f"  QA: {rel}")
        capture.capturar(cfg, cameras=cams, agora_teste=a.agora, duracao_teste_s=a.segundos, pos_janela=pos)
        return

    if a.cmd == "qa":
        from bancada_lib import qa
        rel = qa.relatorio(cfg, _dia(a.dia), recalcular=a.recalcular)
        print(rel.read_text(encoding="utf-8"))
        return

    if a.cmd == "sync":
        from bancada_lib import sync
        rel = sync.medir(cfg, _dia(a.dia), trecho_s=a.trecho)
        print(rel.read_text(encoding="utf-8"))
        return

    if a.cmd == "proxy":
        from bancada_lib import proxy
        proxy.gerar(cfg, _dia(a.dia), fps=a.fps, workers=a.workers, forcar=a.forcar)
        return

    if a.cmd == "frame":
        from bancada_lib import medida
        v = Path(a.video)
        saida = Path(a.saida) if a.saida else cfg.raiz / "medidas" / f"{v.stem}_t{int(a.t)}.jpg"
        medida.quadro(cfg, v, a.t, saida)
        return

    if a.cmd == "pxm":
        from bancada_lib import medida
        p1 = tuple(map(float, a.p1.split(","))); p2 = tuple(map(float, a.p2.split(",")))
        medida.pxm(p1, p2, a.metros)
        return

    if a.cmd == "analisar":
        from bancada_lib import analyze
        analyze.analisar(cfg, Path(a.video), modelo=a.modelo, imgsz=a.imgsz, conf=a.conf, stride=a.stride,
                         maos=not a.sem_maos, maos_stride=a.maos_stride, max_quadros=a.max_quadros,
                         saida=Path(a.saida) if a.saida else None, dispositivo=a.dispositivo,
                         modelo_maos=Path(a.modelo_maos) if a.modelo_maos else None)
        return


if __name__ == "__main__":
    main()
