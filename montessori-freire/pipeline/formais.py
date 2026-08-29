#!/usr/bin/env python3
"""
Segunda passada: o aparato de REFERENCIA FORMAL.

No texto do Gutenberg as referencias bibliograficas de Montessori vem em caixa
alta seguidas do titulo em italico -- MORSELLI, _Cesare Lombroso..._ -- ou de
"Op. cit.". A primeira passada (extrair.py) so reconhece Maiuscula+minusculas,
e portanto perdia exatamente a camada mais forte de evidencia: a citacao formal,
com autor e obra, comparavel a uma nota de rodape de Freire.

Saida: formais.json -> {Sobrenome: {obra: [titulos citados]}}
"""
import json
import os
import re
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from extrair import OBRAS, RAIZ_CORPUS, corpo, normaliza  # noqa: E402

SAIDA = os.path.join(AQUI, "formais.json")

# AUTOR EM CAIXA ALTA seguido de titulo em italico, ou de "Op. cit."
PAT = re.compile(
    r"\b([A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ'\-]{2,}(?:\s+[A-ZÀ-ÖØ-Þ][A-ZÀ-ÖØ-Þ'\-]{1,}){0,2})\s*[,:]\s*"
    r"(?:_([^_]{3,140})_|(Op\. cit\.))"
)

# Cabecalhos e rubricas do proprio livro, que nao sao autor.
NAO_AUTOR = {
    "FIG", "FIGS", "TABLE", "NOTE", "NOTES", "CHAPTER", "PART", "SEE", "OP", "IBID",
    "CF", "THE", "AND", "ILLUSTRATION", "MATERIAL", "APPLICATIONS", "CHILD", "MOTHER",
    "FATHER", "EXERCISE", "EXERCISES", "OBJECT", "AIM", "AGE", "CONTROL", "LESSON",
    "VII", "VIII", "III", "IV", "VI", "IX", "XI", "XII", "II", "I", "V", "X",
}


def titulo_caso(bruto):
    """MORSELLI -> Morselli ; SANTE DE SANCTIS -> Sanctis (ultimo sobrenome util)."""
    partes = [p for p in bruto.split() if p.lower() not in
              {"de", "di", "da", "van", "von", "del", "della", "le", "la"}]
    return partes[-1].capitalize() if partes else bruto.capitalize()


def main():
    ref = defaultdict(lambda: defaultdict(list))
    for obra_id, (pasta, arquivo) in OBRAS.items():
        caminho = os.path.join(RAIZ_CORPUS, pasta, arquivo)
        if not os.path.exists(caminho):
            continue
        texto = normaliza(corpo(caminho))
        for m in PAT.finditer(texto):
            bruto = re.sub(r"\s+", " ", m.group(1)).strip()
            if bruto in NAO_AUTOR or len(bruto.split()) > 3:
                continue
            # rubricas longas do livro ("FIRST SERIES OF INSETS") nao sao autor
            if any(p in NAO_AUTOR for p in bruto.split()):
                continue
            titulo = re.sub(r"\s+", " ", (m.group(2) or m.group(3) or "")).strip()
            ref[titulo_caso(bruto)][obra_id].append({"como": bruto, "obra_citada": titulo})

    saida = {k: dict(v) for k, v in sorted(
        ref.items(), key=lambda kv: -sum(len(x) for x in kv[1].values()))}
    with open(SAIDA, "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1)
    print(f"{len(saida)} autores com referencia formal -> {SAIDA}")
    for k, v in list(saida.items())[:25]:
        ex = list(v.values())[0][0]
        print(f"  {k:<18} {ex['como']:<20} {ex['obra_citada'][:52]}")


if __name__ == "__main__":
    main()
