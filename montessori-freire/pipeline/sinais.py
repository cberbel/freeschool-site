#!/usr/bin/env python3
"""
Pontua cada candidato por sinais de que se trata de uma PESSOA CITADA,
para orientar a curadoria humana. Nao decide nada sozinho: so ordena a fila.

Sinais (no contexto imediato da ocorrencia, no texto integral):
  titulo     "Dr. X", "Professor X", "M. X", "Mme X", "Signor X"
  posse      "X's method/law/theory/scale/work/system/table/index/school..."
  atribuicao "according to X", "as X says/wrote/observed/showed/holds..."
  obra       "X, <titulo em italico>" ou "X (1897)"  -> forma bibliografica
  proprio    aparece com prenome ("Cesare Lombroso", "Edward Seguin")
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extrair import OBRAS, RAIZ_CORPUS, corpo, normaliza  # noqa: E402

CAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "candidatos.json")
SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fila-curadoria.txt")

TITULO = r"(?:Dr|Doctor|Prof|Professor|M|Mme|Mlle|Signor|Signora|Sig|Herr|Sir|Miss|Mrs|Mr)\.?\s+"
POSSE = (r"(?:method|law|laws|theory|theories|scale|work|works|system|table|tables|index|"
         r"formula|school|schools|apparatus|material|book|studies|study|research|"
         r"experiments?|classification|principle|discovery|test|tests|writings|ideas?|"
         r"metodo|opera)")
ATRIB = (r"(?:according to|as .{0,3}|by|after|following|cited by|quoted by|in the words of)")
VERBO = (r"(?:says?|said|wrote|writes|observed|observes|showed|shows|demonstrated|holds|"
         r"held|maintains|maintained|affirms|affirmed|calls|called|described|describes|"
         r"proposed|proposes|discovered|found|studied|noted|notes|remarks|remarked|"
         r"believed|believes|considers|considered|points out|has shown|tells us)")

NAO_PESSOA = {
    # nacionalidades / linguas
    "english", "italian", "french", "german", "greek", "latin", "roman", "american",
    "european", "chinese", "japanese", "russian", "spanish", "hebrew", "arab", "arabic",
    "italians", "americans", "europeans", "germans", "mongolian", "negro", "aryan",
    "lombrosian", "mendelian", "darwinian", "freirean",
    # lugares
    "italy", "rome", "paris", "milan", "france", "germany", "england", "america",
    "europe", "york", "london", "naples", "turin", "florence", "venice", "sicily",
    "sardinia", "latium", "orte", "lorenzo", "castelli", "romani", "africa", "asia",
    "boston", "chicago", "washington", "berlin", "vienna", "geneva", "madrid",
    "barcelona", "lisbon", "brazil", "argentina", "chile", "india", "china", "japan",
    "russia", "switzerland", "belgium", "holland", "austria", "hungary", "poland",
    "sweden", "norway", "denmark", "portugal", "spain", "greece", "egypt", "egyptian",
    "mediterranean", "atlantic", "alps", "tiber", "vatican", "capitol",
}

CTX = 200  # janela de caracteres ao redor da ocorrencia


def main():
    cand = json.load(open(CAND, encoding="utf-8"))
    alvos = {t for t, v in cand.items()
             if len(t) > 2 and not re.fullmatch(r"[A-Z][a-z]?|.*-+$|.*\d.*", t)
             and t.lower() not in NAO_PESSOA}

    sinais = defaultdict(lambda: defaultdict(int))
    for obra_id, (pasta, arquivo) in OBRAS.items():
        caminho = os.path.join(RAIZ_CORPUS, pasta, arquivo)
        if not os.path.exists(caminho):
            continue
        texto = normaliza(corpo(caminho))
        for tok in alvos:
            esc = re.escape(tok)
            for m in re.finditer(rf"\b{esc}\b", texto):
                a, b = max(0, m.start() - CTX), m.end() + CTX
                antes, depois = texto[a:m.start()], texto[m.end():b]
                if re.search(TITULO + r"$", antes):
                    sinais[tok]["titulo"] += 1
                if re.search(rf"^['’]s\s+{POSSE}\b", depois, re.I):
                    sinais[tok]["posse"] += 1
                if re.search(rf"\b{ATRIB}\s*$", antes, re.I):
                    sinais[tok]["atribuicao"] += 1
                if re.search(rf"^\s+{VERBO}\b", depois, re.I):
                    sinais[tok]["atribuicao"] += 1
                if re.search(r"^,\s*[_“\"]", depois) or re.search(r"^\s*\(\d{4}\)", depois):
                    sinais[tok]["obra"] += 1
                if re.search(r"\b[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]{2,}\s+$", antes) and not re.search(
                        r"(?:The|A|An|In|Of|And|But|For|To|By|At|On|That|This)\s+$", antes):
                    sinais[tok]["prenome"] += 1

    linhas = []
    for tok in alvos:
        s = sinais[tok]
        peso = (s["titulo"] * 3 + s["posse"] * 3 + s["atribuicao"] * 3
                + s["obra"] * 4 + s["prenome"] * 1)
        v = cand[tok]
        linhas.append((peso, v["total"], tok, dict(s), list(v["formas"])[:3],
                       v["por_obra"]))
    linhas.sort(key=lambda r: (-r[0], -r[1]))

    with open(SAIDA, "w", encoding="utf-8") as fh:
        for peso, total, tok, s, formas, por_obra in linhas:
            fh.write(f"{peso:>4} {total:>4}  {tok:<26} {str(s):<70} {formas} {por_obra}\n")
    print(f"{len(linhas)} candidatos pontuados -> {SAIDA}", file=sys.stderr)
    print(f"com sinal (peso>0): {sum(1 for l in linhas if l[0] > 0)}", file=sys.stderr)


if __name__ == "__main__":
    main()
