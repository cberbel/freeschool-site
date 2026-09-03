"""Leitura e validação do config.yaml; montagem das URLs RTSP (Reolink por padrão)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import yaml

PADRAO_ARGS_ENTRADA = ["-rtsp_transport", "tcp", "-rw_timeout", "15000000"]
PADRAO_ARGS_SAIDA = ["-c", "copy", "-map", "0"]
PADRAO_CAMINHO_REOLINK = "auto"
# Os três formatos que a Reolink usa (NVR e câmeras), do mais comum ao mais novo. "auto" testa em ordem.
VARIANTES_REOLINK = ["h264Preview_{canal:02d}_{perfil}", "h265Preview_{canal:02d}_{perfil}", "Preview_{canal:02d}_{perfil}"]


@dataclass
class Camera:
    sala: str
    id: str
    url: str                 # URL final (com credenciais) — nunca logar sem redigir
    args_entrada: list[str] = field(default_factory=lambda: list(PADRAO_ARGS_ENTRADA))
    args_saida: list[str] = field(default_factory=lambda: list(PADRAO_ARGS_SAIDA))
    candidatas: list[str] = field(default_factory=list)   # URLs alternativas a testar no smoke (caminho: auto)

    @property
    def nome(self) -> str:
        return f"{self.sala}_{self.id}"

    @property
    def url_redigida(self) -> str:
        return redigir(self.url)


@dataclass
class Config:
    raiz: Path
    segmento_s: int
    container: str
    janelas: list[tuple[str, str]]   # [("09:00","11:00"), ...]
    dias: int
    apenas_dias_uteis: bool
    fuso: str
    ffmpeg: str
    ffprobe: str
    cameras: list[Camera]
    proxy_altura: int = 1080
    bruto: Path = None  # type: ignore

    def __post_init__(self):
        self.bruto = self.raiz / "bruto"

    def cameras_da_sala(self, sala: str) -> list[Camera]:
        return [c for c in self.cameras if c.sala == sala]

    @property
    def salas(self) -> list[str]:
        vistos: list[str] = []
        for c in self.cameras:
            if c.sala not in vistos:
                vistos.append(c.sala)
        return vistos


def redigir(url: str) -> str:
    """Esconde usuário:senha de uma URL para log."""
    if "@" in url and "://" in url:
        esquema, resto = url.split("://", 1)
        cred, host = resto.split("@", 1)
        return f"{esquema}://***:***@{host}"
    return url


def _janela(texto: str) -> tuple[str, str]:
    ini, fim = texto.replace(" ", "").split("-")
    for t in (ini, fim):
        h, m = t.split(":")
        assert 0 <= int(h) < 24 and 0 <= int(m) < 60, f"janela inválida: {texto}"
    return ini, fim


def carregar(caminho: str | Path = "config.yaml") -> Config:
    caminho = Path(caminho)
    if not caminho.exists():
        raise SystemExit(
            f"config não encontrado: {caminho}\n"
            f"copie config.example.yaml para config.yaml e preencha IPs e credenciais."
        )
    d = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}

    arm = d.get("armazenamento", {})
    reo = d.get("reolink", {})
    ff = d.get("ffmpeg", {})

    cameras: list[Camera] = []
    for sala, sd in (d.get("salas") or {}).items():
        for cd in sd.get("cameras", []):
            usuario = cd.get("usuario", reo.get("usuario", ""))
            senha = str(cd.get("senha", reo.get("senha", "")))
            porta = cd.get("porta", reo.get("porta", 554))
            caminho_rtsp = cd.get("caminho", reo.get("caminho", PADRAO_CAMINHO_REOLINK))
            candidatas: list[str] = []
            if "url" in cd:  # override completo (outra marca, arquivo/stream de teste)
                candidatas = [str(cd["url"])]
            else:
                host = cd.get("host", reo.get("host"))
                if not host:
                    raise SystemExit(f"câmera {sala}/{cd.get('id')} sem host nem url (nem reolink.host)")
                canal = int(cd.get("canal", 1))
                perfil = str(cd.get("perfil", reo.get("perfil", "main")))
                cred = f"{quote(usuario, safe='')}:{quote(senha, safe='')}@" if usuario else ""
                caminhos = (VARIANTES_REOLINK if caminho_rtsp == "auto" else [caminho_rtsp])
                for c in caminhos:
                    path = c.format(canal=canal, perfil=perfil)
                    candidatas.append(f"rtsp://{cred}{host}:{porta}/{path}")
            cameras.append(
                Camera(
                    sala=str(sala),
                    id=str(cd.get("id", f"cam_{len(cameras)+1:02d}")),
                    url=candidatas[0],
                    args_entrada=list(cd.get("args_entrada", ff.get("args_entrada", PADRAO_ARGS_ENTRADA))),
                    args_saida=list(cd.get("args_saida", ff.get("args_saida", PADRAO_ARGS_SAIDA))),
                    candidatas=candidatas,
                )
            )
    if not cameras:
        raise SystemExit("config sem câmeras (bloco 'salas')")

    ids = [c.nome for c in cameras]
    assert len(ids) == len(set(ids)), f"ids de câmera repetidos: {ids}"

    raiz = Path(os.path.expanduser(arm.get("raiz", "./data"))).resolve()
    # URLs resolvidas pelo smoke (qual variante respondeu) têm precedência sobre a primeira candidata
    ok_path = raiz / "canais-ok.yaml"
    if ok_path.exists():
        ok = yaml.safe_load(ok_path.read_text(encoding="utf-8")) or {}
        for c in cameras:
            if c.nome in ok and ok[c.nome] in c.candidatas:
                c.url = ok[c.nome]

    return Config(
        raiz=raiz,
        segmento_s=int(arm.get("segmento_s", 600)),
        container=str(arm.get("container", "mkv")),
        janelas=[_janela(j) for j in d.get("janelas", ["09:00-11:00", "14:00-16:00"])],
        dias=int(d.get("dias", 3)),
        apenas_dias_uteis=bool(d.get("apenas_dias_uteis", True)),
        fuso=str(d.get("fuso", "America/Sao_Paulo")),
        ffmpeg=str(ff.get("binario", "ffmpeg")),
        ffprobe=str(ff.get("ffprobe", "ffprobe")),
        cameras=cameras,
        proxy_altura=int(arm.get("proxy_altura", 1080)),
    )
