"""Primeira análise (testes T5, T6, T8, T9): detecção de pessoas + tracking (YOLO + ByteTrack),
pose (YOLO-pose, 17 pontos COCO) e mãos (MediaPipe Hands, 21 pontos) em crops por pessoa.

Saídas por vídeo, em raiz/analise/<dia>/<sala>/<cam>/<segmento>/:
  tracks.parquet   uma linha por pessoa por quadro (ts_utc, track_id, caixa, conf, keypoints)
  maos.parquet     uma linha por mão detectada (21 landmarks em px do quadro inteiro)
  resumo.json      métricas do arquivo — inclui proxies de T6 (churn de IDs) e T9 (taxa de mão)
  heatmap.png      ocupação dos pés em px

Tudo em pixels até existir calibração (Fase 0, T3). Timestamps = start_time do arquivo + quadro/fps,
corrigidos pelo offset de sincronização de áudio quando sync.json existir.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .config import Config
from .ffm import probe, resumo_probe
from .sync import offsets_para

KP_NOMES = ["nariz", "olho_e", "olho_d", "orelha_e", "orelha_d", "ombro_e", "ombro_d", "cotovelo_e",
            "cotovelo_d", "pulso_e", "pulso_d", "quadril_e", "quadril_d", "joelho_e", "joelho_d",
            "tornozelo_e", "tornozelo_d"]


def _importar_yolo():
    try:
        from ultralytics import YOLO  # noqa
        return YOLO
    except ImportError:
        raise SystemExit("ultralytics não instalado: pip install -r requirements-analise.txt")


URL_MODELO_MAOS = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/"
                   "float16/1/hand_landmarker.task")


class MaoDetector:
    """21 landmarks por mão. Usa a API 'tasks' do MediaPipe (0.10+ e 1.x); cai para mp.solutions se
    for um MediaPipe antigo. detectar(rgb) → [(pts_norm[21,3], lado), ...]"""

    def __init__(self, modelo: Path, max_maos: int = 2, conf: float = 0.5):
        import mediapipe as mp
        self.mp = mp
        self.backend = None
        if hasattr(mp, "tasks"):
            from mediapipe.tasks import python as mpp
            from mediapipe.tasks.python import vision
            if not modelo.exists():
                modelo.parent.mkdir(parents=True, exist_ok=True)
                print(f"  baixando modelo de mãos → {modelo}")
                import urllib.request
                try:
                    urllib.request.urlretrieve(URL_MODELO_MAOS, modelo)
                except Exception as e:
                    raise SystemExit(f"não consegui baixar hand_landmarker.task ({e}). Baixe de\n  {URL_MODELO_MAOS}\n"
                                     f"e salve em {modelo}")
            opts = vision.HandLandmarkerOptions(
                base_options=mpp.BaseOptions(model_asset_path=str(modelo)),
                running_mode=vision.RunningMode.IMAGE, num_hands=max_maos,
                min_hand_detection_confidence=conf)
            self.det = vision.HandLandmarker.create_from_options(opts)
            self.backend = "tasks"
        elif hasattr(mp, "solutions"):
            self.det = mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=max_maos,
                                                min_detection_confidence=conf)
            self.backend = "solutions"
        else:
            raise SystemExit("MediaPipe sem API de mãos reconhecida")

    def detectar(self, rgb: np.ndarray) -> list[tuple[np.ndarray, str | None]]:
        saida = []
        if self.backend == "tasks":
            img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
            r = self.det.detect(img)
            for j, lms in enumerate(r.hand_landmarks or []):
                lado = r.handedness[j][0].category_name if r.handedness and j < len(r.handedness) else None
                saida.append((np.array([[p.x, p.y, p.z] for p in lms], dtype=np.float32), lado))
        else:
            r = self.det.process(rgb)
            for j, lm in enumerate(r.multi_hand_landmarks or []):
                lado = None
                if r.multi_handedness and j < len(r.multi_handedness):
                    lado = r.multi_handedness[j].classification[0].label
                saida.append((np.array([[p.x, p.y, p.z] for p in lm.landmark], dtype=np.float32), lado))
        return saida

    def fechar(self):
        try:
            if self.det is not None:
                self.det.close()
        except Exception:
            pass
        self.det = None  # evita close() duplo no __del__ do MediaPipe


def _info(cfg: Config, video: Path) -> tuple[str, str, date, float, float]:
    """sala, cam, dia, start_time (época), fps — a partir do caminho e do ffprobe."""
    p = resumo_probe(probe(cfg.ffprobe, video))
    if p.get("erro"):
        raise SystemExit(f"ffprobe falhou em {video}: {p['erro']}")
    partes = video.parts
    sala, cam = (partes[-3], partes[-2]) if len(partes) >= 3 else ("?", "?")
    from .qa import inicio_do_nome
    start = inicio_do_nome(video) or (p["start_time"] if p["start_time"] > 1e9 else 0.0)
    if start > 1e9:
        dia = datetime.fromtimestamp(start, ZoneInfo(cfg.fuso)).date()
    else:  # arquivo sem relógio de parede (teste) → usa a data do caminho, se houver
        try:
            dia = date(int(partes[-6]), int(partes[-5]), int(partes[-4]))
        except (ValueError, IndexError):
            dia = date.today()
        start = 0.0
    return sala, cam, dia, start, p["fps"] or 15.0


def analisar(cfg: Config, video: Path, modelo: str = "yolo11n-pose.pt", imgsz: int = 960,
             conf: float = 0.3, stride: int = 1, maos: bool = True, maos_stride: int = 5,
             max_quadros: int | None = None, saida: Path | None = None, dispositivo: str | None = None,
             modelo_maos: Path | None = None) -> Path:
    YOLO = _importar_yolo()
    import cv2

    sala, cam, dia, start, fps = _info(cfg, video)
    offset = offsets_para(cfg, dia, sala, cam)
    saida = saida or (cfg.raiz / "analise" / dia.isoformat() / sala / cam / video.stem)
    saida.mkdir(parents=True, exist_ok=True)
    print(f"analisando {video.name}  ({sala}/{cam}, {dia}, fps {fps:.1f}, offset sync {offset*1000:+.0f} ms)")

    det = YOLO(modelo)
    com_pose = "pose" in modelo
    hands = None
    if maos:
        try:
            hands = MaoDetector(modelo_maos or (cfg.raiz / "modelos" / "hand_landmarker.task"))
            print(f"  mãos: MediaPipe ({hands.backend}), 1 a cada {maos_stride} quadros")
        except ImportError:
            print("  mediapipe não instalado → mãos desligadas (pip install -r requirements-analise.txt)")

    linhas: list[dict] = []
    linhas_maos: list[dict] = []
    n_quadros = 0
    quadros_com_pessoa = 0
    max_simult = 0
    quadros_maos_tentados = 0
    quadros_maos_ok = 0
    largura = altura = 0

    # ultralytics lê o vídeo e faz o tracking com persistência entre quadros
    for r in det.track(source=str(video), stream=True, persist=True, tracker="bytetrack.yaml",
                       classes=[0], conf=conf, imgsz=imgsz, vid_stride=stride, verbose=False,
                       device=dispositivo):
        n_quadros += 1
        if max_quadros and n_quadros > max_quadros:
            break
        idx = (n_quadros - 1) * stride
        ts = start + idx / fps + offset if start else idx / fps
        if r.orig_shape:
            altura, largura = r.orig_shape[:2]
        caixas = r.boxes
        if caixas is None or len(caixas) == 0:
            continue
        quadros_com_pessoa += 1
        ids = caixas.id.int().tolist() if caixas.id is not None else [-1] * len(caixas)
        max_simult = max(max_simult, len(caixas))
        xyxy = caixas.xyxy.cpu().numpy()
        confs = caixas.conf.cpu().numpy()
        kps = r.keypoints.data.cpu().numpy() if (com_pose and r.keypoints is not None) else None
        quadro_bgr = r.orig_img if (hands is not None and n_quadros % maos_stride == 0) else None
        for i, (x1, y1, x2, y2) in enumerate(xyxy):
            linha = {"ts_utc": ts, "quadro": idx, "sala": sala, "cam": cam, "track_id": ids[i],
                     "x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2),
                     "conf": float(confs[i]), "pe_x": float((x1 + x2) / 2), "pe_y": float(y2),
                     "altura_px": float(y2 - y1)}
            if kps is not None and i < len(kps):
                for k, nome in enumerate(KP_NOMES):
                    linha[f"kp_{nome}_x"] = float(kps[i][k][0])
                    linha[f"kp_{nome}_y"] = float(kps[i][k][1])
                    linha[f"kp_{nome}_c"] = float(kps[i][k][2])
            linhas.append(linha)
            if quadro_bgr is not None:
                quadros_maos_tentados += 1
                # crop da metade superior + margem, no quadro original (Parte I §12 do plano)
                w = x2 - x1; h = y2 - y1
                cx1 = int(max(0, x1 - 0.15 * w)); cx2 = int(min(largura, x2 + 0.15 * w))
                cy1 = int(max(0, y1)); cy2 = int(min(altura, y1 + 0.75 * h))
                crop = quadro_bgr[cy1:cy2, cx1:cx2]
                if crop.size == 0:
                    continue
                deteccoes = hands.detectar(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                if deteccoes:
                    quadros_maos_ok += 1
                    for pts_n, lado in deteccoes:
                        pts = np.column_stack([pts_n[:, 0] * (cx2 - cx1) + cx1, pts_n[:, 1] * (cy2 - cy1) + cy1, pts_n[:, 2]])
                        larg_mao = float(pts[:, 0].max() - pts[:, 0].min())
                        m = {"ts_utc": ts, "quadro": idx, "sala": sala, "cam": cam, "track_id": ids[i],
                             "lado": lado, "largura_mao_px": larg_mao}
                        for k in range(21):
                            m[f"h{k}_x"], m[f"h{k}_y"], m[f"h{k}_z"] = map(float, pts[k])
                        linhas_maos.append(m)
        if n_quadros % 500 == 0:
            print(f"  {n_quadros} quadros… pessoas em {quadros_com_pessoa}, ids até agora "
                  f"{len({l['track_id'] for l in linhas})}")

    if hands is not None:
        hands.fechar()

    df = pd.DataFrame(linhas)
    df.to_parquet(saida / "tracks.parquet", index=False) if not df.empty else None
    dm = pd.DataFrame(linhas_maos)
    dm.to_parquet(saida / "maos.parquet", index=False) if not dm.empty else None

    resumo = {"video": str(video), "sala": sala, "cam": cam, "dia": dia.isoformat(), "modelo": modelo,
              "imgsz": imgsz, "conf": conf, "stride": stride, "fps": fps, "resolucao": f"{largura}x{altura}",
              "quadros_processados": n_quadros, "quadros_com_pessoa": quadros_com_pessoa,
              "frac_quadros_com_pessoa": round(quadros_com_pessoa / n_quadros, 4) if n_quadros else 0,
              "max_simultaneas": max_simult}
    if not df.empty:
        ids_validos = df[df.track_id >= 0]
        por_id = ids_validos.groupby("track_id").agg(n=("quadro", "size"), ini=("ts_utc", "min"), fim=("ts_utc", "max"))
        vida = (por_id.fim - por_id.ini)
        resumo.update({
            "ids_unicos": int(por_id.shape[0]),
            # T6 (proxy): quantos IDs o tracker gastou por pessoa realmente presente. 1.0 = perfeito.
            "id_churn": round(por_id.shape[0] / max_simult, 2) if max_simult else None,
            "vida_media_id_s": round(float(vida.mean()), 1) if len(vida) else None,
            "vida_mediana_id_s": round(float(vida.median()), 1) if len(vida) else None,
            "ids_curtos_lt_5s": int((vida < 5).sum()),
            "altura_pessoa_px_mediana": round(float(df.altura_px.median()), 1),
            "conf_mediana": round(float(df.conf.median()), 3),
        })
        if com_pose:
            cols_c = [c for c in df.columns if c.endswith("_c") and c.startswith("kp_")]
            resumo["pose_conf_media"] = round(float(df[cols_c].mean().mean()), 3)
            resumo["pose_frac_pontos_conf_gt_0_5"] = round(float((df[cols_c] > 0.5).mean().mean()), 3)
    if maos:
        resumo.update({
            # T9 (proxy): em que fração das pessoas amostradas o MediaPipe achou alguma mão
            "maos_pessoas_amostradas": quadros_maos_tentados,
            "maos_taxa_deteccao": round(quadros_maos_ok / quadros_maos_tentados, 4) if quadros_maos_tentados else None,
            "maos_largura_px_mediana": round(float(dm.largura_mao_px.median()), 1) if not dm.empty else None,
        })
    (saida / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    if not df.empty:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(8, 8 * altura / max(largura, 1)))
            ax.hist2d(df.pe_x, df.pe_y, bins=[max(8, largura // 40), max(8, altura // 40)],
                      range=[[0, largura], [0, altura]], cmap="magma")
            ax.invert_yaxis(); ax.set_title(f"ocupação (pés, px) — {sala}/{cam} {video.stem}")
            ax.set_xlabel("x px"); ax.set_ylabel("y px")
            fig.tight_layout(); fig.savefig(saida / "heatmap.png", dpi=110); plt.close(fig)
        except Exception as e:  # matplotlib é opcional
            print(f"  heatmap não gerado: {e}")

    print(f"  → {saida}")
    for k in ("quadros_processados", "frac_quadros_com_pessoa", "max_simultaneas", "ids_unicos", "id_churn",
              "vida_mediana_id_s", "altura_pessoa_px_mediana", "pose_conf_media", "maos_taxa_deteccao",
              "maos_largura_px_mediana"):
        if k in resumo:
            print(f"     {k}: {resumo[k]}")
    return saida
