#!/usr/bin/env python3
"""
Extrai candidatos a nomes proprios de pessoas do corpus em texto integral.

Entrada : os .txt do Project Gutenberg (espelhados no GITenberg) de cada obra.
Saida   : candidatos.json  -> {candidato: {obra: {"n": ocorrencias, "ctx": [trechos]}}}

O metodo e deliberadamente simples e auditavel:
 1. corta cabecalho/rodape do Gutenberg;
 2. junta as linhas em um texto corrido (o Gutenberg quebra linha a ~70 colunas);
 3. acha sequencias de palavras capitalizadas (com particulas: de, van, von, della...);
 4. descarta o que a propria obra usa em minuscula com frequencia (palavra comum
    que so apareceu capitalizada por estar em inicio de frase ou titulo);
 5. conta e guarda contexto.

O passo 5 nao decide quem e pessoa. Essa curadoria e humana e vive em pessoas.json.
"""
import json
import os
import re
import sys
from collections import defaultdict

RAIZ_CORPUS = os.environ.get("CORPUS", "/home/user/corpus")
SAIDA = os.path.join(os.path.dirname(__file__), "candidatos.json")

# obra_id -> (diretorio do repo GITenberg, arquivo preferido)
OBRAS = {
    "metodo-1912": ("The-Montessori-MethodAuthor_39863", "39863-8.txt"),
    "handbook-1914": ("Dr-Montessori-Own-Handbook_29635", "29635-8.txt"),
    "antropologia-1913": ("Pedagogical-Anthropology_46643", "46643-8.txt"),
    "autoeducacao-1917": ("Spontaneous-Activity-in-Education_24727", "24727-8.txt"),
    "material-1917": ("Montessori-Elementary-MaterialsThe-Advanced-Montessori-Method_42869", "42869-0.txt"),
}

INICIO = re.compile(r"\*\*\*\s*START OF TH(IS|E) PROJECT GUTENBERG", re.I)
FIM = re.compile(r"\*\*\*\s*END OF TH(IS|E) PROJECT GUTENBERG", re.I)

PARTICULAS = {"de", "del", "della", "di", "da", "du", "van", "von", "der", "den",
              "la", "le", "el", "y", "e", "of", "des", "dos", "das"}

# Ruido estrutural do proprio livro e do Gutenberg.
STOP = {
    "the", "and", "but", "for", "not", "chapter", "part", "book", "volume", "page",
    "fig", "figure", "plate", "table", "index", "preface", "introduction", "contents",
    "appendix", "note", "notes", "translator", "author", "title", "gutenberg", "ebook",
    "project", "copyright", "license", "printed", "press", "company", "edition",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday", "god", "christ", "lord", "saint", "st",
    "i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii",
    "dr", "mr", "mrs", "miss", "prof", "professor", "signor", "signora", "madame",
    "yes", "no", "oh", "ah", "if", "when", "then", "now", "here", "there", "this",
    "that", "these", "those", "such", "one", "two", "three", "first", "second",
    "it", "he", "she", "we", "they", "you", "his", "her", "their", "its", "my",
    "a", "an", "in", "on", "at", "to", "by", "with", "from", "as", "is", "are",
    "was", "were", "be", "been", "has", "have", "had", "do", "does", "did", "so",
    "all", "any", "each", "every", "some", "many", "much", "more", "most", "how",
    "what", "who", "which", "why", "where", "let", "thus", "even", "only", "also",
    "children", "child", "school", "schools", "teacher", "life", "man", "men",
    "woman", "women", "little", "new", "old", "great", "good", "same", "other",
}

TOKEN_CAP = r"[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’\-]+\.?"


def le(caminho):
    """Le o arquivo detectando a codificacao: os -8 do Gutenberg sao Latin-1."""
    bruto = open(caminho, "rb").read()
    for cod in ("utf-8", "latin-1"):
        try:
            return bruto.decode(cod)
        except UnicodeDecodeError:
            continue
    return bruto.decode("latin-1", errors="replace")


def corpo(caminho):
    """Devolve o texto da obra sem cabecalho/rodape do Gutenberg."""
    linhas = le(caminho).splitlines(keepends=True)
    ini, fim = 0, len(linhas)
    for i, l in enumerate(linhas):
        if INICIO.search(l):
            ini = i + 1
            break
    for i in range(len(linhas) - 1, -1, -1):
        if FIM.search(linhas[i]):
            fim = i
            break
    return "".join(linhas[ini:fim])


def normaliza(texto):
    """Junta quebras de linha de composicao, preservando paragrafos."""
    texto = texto.replace("\r\n", "\n")
    texto = re.sub(r"([A-Za-zà-öø-ÿ,;:])\n(?=[A-Za-zà-öø-ÿ])", r"\1 ", texto)
    return re.sub(r"[ \t]+", " ", texto)


def vocabulario_minusculo(texto):
    v = defaultdict(int)
    for p in re.findall(r"\b[a-zà-öø-ÿ]{2,}\b", texto):
        v[p] += 1
    return v


def candidatos(texto, vocab):
    """Sequencias capitalizadas que nao sao palavra comum da propria obra."""
    padrao = re.compile(
        rf"{TOKEN_CAP}(?:\s+(?:{'|'.join(PARTICULAS)})\s+{TOKEN_CAP}|\s+{TOKEN_CAP}){{0,3}}"
    )
    achados = []
    for m in padrao.finditer(texto):
        bruto = m.group(0).strip(" .,;:")
        partes = bruto.split()
        if not partes:
            continue
        # descarta se TODOS os tokens forem palavras comuns na propria obra
        significativos = [
            p for p in partes
            if p.lower().strip(".,;:'’") not in STOP
            and p.lower().strip(".,;:'’") not in PARTICULAS
        ]
        if not significativos:
            continue
        # um token isolado so vale se a obra quase nunca o usa em minuscula
        chave = " ".join(partes)
        raros = [
            p for p in significativos
            if vocab.get(p.lower().strip(".,;:'’"), 0) <= 2
        ]
        if not raros:
            continue
        achados.append((chave, m.start()))
    return achados


def limpa(tok):
    tok = tok.strip(" .,;:!?()[]\"'’")
    tok = re.sub(r"['’]s$", "", tok)
    return tok


TITULOS = {"dr", "mr", "mrs", "miss", "prof", "professor", "signor", "signora",
           "signorina", "madame", "mme", "sir", "lady", "don", "donna", "m",
           "st", "saint", "father", "doctor", "count", "baron"}


def main():
    # token canonico -> obra -> contagem ; e as formas compostas em que aparece
    conta = defaultdict(lambda: defaultdict(int))
    formas = defaultdict(lambda: defaultdict(int))
    contexto = defaultdict(list)

    for obra_id, (pasta, arquivo) in OBRAS.items():
        caminho = os.path.join(RAIZ_CORPUS, pasta, arquivo)
        if not os.path.exists(caminho):
            print(f"AUSENTE {caminho}", file=sys.stderr)
            continue
        texto = normaliza(corpo(caminho))
        vocab = vocabulario_minusculo(texto)
        for chave, pos in candidatos(texto, vocab):
            partes = [limpa(p) for p in chave.split()]
            partes = [p for p in partes if p]
            nucleo = [p for p in partes
                      if p.lower() not in TITULOS
                      and p.lower() not in PARTICULAS
                      and p.lower() not in STOP
                      and len(p) > 1
                      and vocab.get(p.lower(), 0) <= 2]
            if not nucleo:
                continue
            forma = " ".join(p for p in partes if p.lower() not in TITULOS)
            for tok in nucleo:
                conta[tok][obra_id] += 1
                formas[tok][forma] += 1
                if len(contexto[tok]) < 4:
                    trecho = texto[max(0, pos - 130):pos + 170].replace("\n", " ")
                    contexto[tok].append(f"[{obra_id}] " + re.sub(r"\s+", " ", trecho).strip())
        print(f"{obra_id}: {len(texto.split()):>7} palavras", file=sys.stderr)

    saida = {}
    for tok, por_obra in conta.items():
        total = sum(por_obra.values())
        saida[tok] = {
            "total": total,
            "por_obra": dict(por_obra),
            "formas": dict(sorted(formas[tok].items(), key=lambda kv: -kv[1])[:8]),
            "ctx": contexto[tok],
        }
    saida = dict(sorted(saida.items(), key=lambda kv: -kv[1]["total"]))
    with open(SAIDA, "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1)
    print(f"{len(saida)} tokens candidatos -> {SAIDA}", file=sys.stderr)


if __name__ == "__main__":
    main()
