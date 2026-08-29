#!/usr/bin/env python3
"""
Junta o que o extrator achou no texto com a curadoria, e escreve os dados do site.

Saidas em ../dados/:
  montessori.json  -> pessoas citadas, contagem por obra, e a prestacao de contas
                      do que ainda nao foi revisado.
"""
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from curadoria import PESSOAS, EXCLUIDOS  # noqa: E402

DADOS = os.path.join(AQUI, "..", "dados")
CAND = os.path.join(AQUI, "candidatos.json")
FORMAIS = os.path.join(AQUI, "formais.json")

OBRAS_ORDEM = ["metodo-1912", "antropologia-1913", "handbook-1914",
               "autoeducacao-1917", "material-1917"]

# rotulos curtos para a interface
ROTULOS = {
    "metodo-1912": "O Método (1909/1912)",
    "antropologia-1913": "Antropologia Pedagógica (1910/1913)",
    "handbook-1914": "Own Handbook (1914)",
    "autoeducacao-1917": "A autoeducação (1916/1917)",
    "material-1917": "O material (1916/1917)",
}


def main():
    cand = json.load(open(CAND, encoding="utf-8"))
    formais = json.load(open(FORMAIS, encoding="utf-8"))

    usados = set()
    pessoas = []
    for nome, (tokens, vida, pais, campo, certeza, nota) in PESSOAS.items():
        por_obra = {}
        formas = set()
        achou = False
        for t in tokens:
            v = cand.get(t)
            if not v:
                continue
            achou = True
            usados.add(t)
            for obra, n in v["por_obra"].items():
                por_obra[obra] = por_obra.get(obra, 0) + n
            formas.update(list(v["formas"])[:3])
        # camada de evidencia mais forte: autor + obra no aparato de referencia
        refs = []
        for t in tokens:
            for obra, itens in formais.get(t, {}).items():
                achou = True
                for it in itens:
                    refs.append({"obra": obra, "como": it["como"],
                                 "obra_citada": it["obra_citada"]})
        if not achou:
            continue
        pessoas.append({
            "nome": nome, "vida": vida, "pais": pais, "campo": campo,
            "certeza": certeza, "nota": nota,
            "total": sum(por_obra.values()),
            "obras": {o: por_obra[o] for o in OBRAS_ORDEM if o in por_obra},
            "formas": sorted(formas),
            "referencias": refs,
        })
    pessoas.sort(key=lambda p: (-p["total"], p["nome"]))
    com_ref = sum(1 for p in pessoas if p["referencias"])

    usados |= set(EXCLUIDOS)
    pendentes = {k: v["total"] for k, v in cand.items() if k not in usados}
    pend_ordenados = sorted(pendentes.items(), key=lambda kv: -kv[1])

    # o corpus efetivamente lido, para a pagina poder declarar o que mediu
    from extrair import OBRAS as _OB, RAIZ_CORPUS as _RC, corpo as _co, normaliza as _no
    corpus = []
    for obra_id in OBRAS_ORDEM:
        pasta, arquivo = _OB[obra_id]
        caminho = os.path.join(_RC, pasta, arquivo)
        palavras = len(_no(_co(caminho)).split()) if os.path.exists(caminho) else 0
        corpus.append({"id": obra_id, "rotulo": ROTULOS[obra_id], "palavras": palavras})

    saida = {
        "corpus": corpus,
        "rotulos": ROTULOS,
        "gerado_por": "pipeline/extrair.py + pipeline/curadoria.py + pipeline/montar.py",
        "pessoas": pessoas,
        "excluidos": EXCLUIDOS,
        "prestacao_de_contas": {
            "tokens_extraidos": len(cand),
            "tokens_atribuidos": len(usados & set(cand)),
            "tokens_pendentes": len(pendentes),
            "pendentes_com_3_ou_mais": sum(1 for _, n in pend_ordenados if n >= 3),
            "com_referencia_formal": com_ref,
            "amostra_pendentes": [k for k, n in pend_ordenados[:60]],
        },
    }
    os.makedirs(DADOS, exist_ok=True)
    destino = os.path.join(DADOS, "montessori.json")
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(saida, fh, ensure_ascii=False, indent=1)

    print(f"{len(pessoas)} pessoas com ocorrencia no corpus")
    print(f"{sum(p['total'] for p in pessoas)} mencoes atribuidas")
    print(f"{com_ref} com referencia bibliografica formal (autor + obra)")
    print(f"{len(pendentes)} tokens ainda nao revisados "
          f"({saida['prestacao_de_contas']['pendentes_com_3_ou_mais']} com 3+ ocorrencias)")
    nao_encontradas = [n for n in PESSOAS if not any(
        t in cand for t in PESSOAS[n][0])]
    if nao_encontradas:
        print("curadas sem ocorrencia (revisar tokens):", nao_encontradas)


if __name__ == "__main__":
    main()
