#!/usr/bin/env python3
"""
Pontua com o codebook v1 as entradas de observação que já existem (Projeto B).

Regra master: o sistema não espera avaliadoras. Este script lê as transcrições das entradas,
pede ao modelo uma nota por dimensão com o codebook v1 como prompt de sistema, e grava em
obs_avaliacoes com avaliador_tipo='modelo'. Nunca sobrescreve nota humana; é idempotente
(uma linha por janela × criança × modelo × versão do codebook).

Uso:
  pip install "anthropic>=1.0" "supabase>=2"
  export ANTHROPIC_API_KEY=...            # chave do Projeto B (uma por projeto)
  export SUPABASE_URL=https://rmpnqrvsmxhnrwlgqmdp.supabase.co
  export SUPABASE_SERVICE_KEY=...         # service role: as tabelas novas têm RLS sem policy
  python tools/pontuar_entradas.py --dry-run          # mostra o que faria, sem chamar a API
  python tools/pontuar_entradas.py --limite 50        # pontua até 50 janelas ainda sem nota do modelo

Custo: ~1 chamada por janela, entrada de ~4–6 k tokens (codebook em cache) + saída curta;
com effort='low' fica em centavos por janela. Teto mensal do projeto: US$ 150.
"""
import argparse, json, os, re, sys, unicodedata
from datetime import datetime, timezone

MODEL = "claude-opus-5"
CODEBOOK_VERSAO = "v1"

SAIDA_SCHEMA = {
    "type": "object",
    "properties": {
        "avaliavel": {"type": "boolean", "description": "false se a transcrição não descreve uma criança em atividade (teste de microfone, conversa entre adultos, vazio)"},
        "motivo_nao_avaliavel": {"type": ["string", "null"]},
        "crianca_alvo": {"type": ["string", "null"], "description": "nome da criança-alvo exatamente como aparece no texto; null se não há"},
        "envolvimento": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
        "autonomia": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
        "persistencia": {"type": ["integer", "null"], "minimum": 1, "maximum": 5},
        "persistencia_motivo": {"type": ["string", "null"], "description": "'sem_oportunidade' quando não houve dificuldade nem interrupção"},
        "contexto": {"type": ["string", "null"], "enum": ["vida_pratica", "sensorial", "linguagem", "matematica", "cultural_ciencias", "arte_musica", "movimento_patio", "refeicao", "roda_circulo", "transicao_arrumacao", "livre_sem_material", "sesta_repouso", None]},
        "material": {"type": ["string", "null"]},
        "adulto_proximo": {"type": ["boolean", "null"]},
        "confianca": {"type": "integer", "minimum": 1, "maximum": 5},
        "justificativa": {"type": "string", "description": "até 30 palavras, citando o observável"},
    },
    "required": ["avaliavel", "motivo_nao_avaliavel", "crianca_alvo", "envolvimento", "autonomia", "persistencia",
                 "persistencia_motivo", "contexto", "material", "adulto_proximo", "confianca", "justificativa"],
    "additionalProperties": False,
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().lower()


def montar_system(codebook_json):
    return (
        "Você pontua observações de crianças numa escola Montessori com o codebook abaixo. "
        "Pontue só o que o texto descreve; não invente. Se o texto não descreve uma criança em atividade "
        "(teste de microfone, conversa entre adultos, vazio), responda avaliavel=false. "
        "Só há transcrição, sem vídeo: confianca no máximo 3. "
        "Persistência só recebe nota se houve dificuldade, erro ou interrupção; senão persistencia=null e "
        "persistencia_motivo='sem_oportunidade'.\n\nCODEBOOK (JSON):\n" + json.dumps(codebook_json, ensure_ascii=False, indent=2)
    )


def chamar_modelo(client, system, transcricao):
    kwargs = dict(
        model=MODEL,
        max_tokens=1024,
        system=system,
        cache_control={"type": "ephemeral"},  # cacheia o codebook (prefixo estável)
        output_config={"format": {"type": "json_schema", "schema": SAIDA_SCHEMA}, "effort": "low"},
        messages=[{"role": "user", "content": "Transcrição da observadora:\n\n" + transcricao}],
    )
    try:
        # fallback server-side por categoria de recusa (recomendado para claude-opus-5)
        resp = client.beta.messages.create(betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)
    except TypeError:
        resp = client.messages.create(**kwargs)
    if resp.stop_reason == "refusal":
        return None, "refusal"
    text = next(b.text for b in resp.content if b.type == "text")
    return json.loads(text), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=50)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-chars", type=int, default=40, help="ignora transcrições menores (testes de microfone)")
    args = ap.parse_args()

    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    cb = sb.table("obs_codebook").select("versao,dimensoes").eq("versao", CODEBOOK_VERSAO).single().execute().data
    system = montar_system(cb["dimensoes"])

    alunos = sb.table("alunos").select("id,nome,sobrenome,agrupada").eq("status", "ativo").execute().data
    por_primeiro_nome = {}
    for a in alunos:
        por_primeiro_nome.setdefault(norm(a["nome"]).split(" ")[0], []).append(a)

    janelas = (sb.table("dev_janelas").select("id,sala,inicio,fim,entrada_id,projeto")
               .eq("origem", "entrada").not_.is_("entrada_id", "null").order("inicio").execute().data)
    ja = sb.table("obs_avaliacoes").select("janela_id").eq("avaliador_tipo", "modelo").eq("avaliador", MODEL).eq("codebook_versao", CODEBOOK_VERSAO).execute().data
    ja_ids = {r["janela_id"] for r in ja}
    pend = sb.table("dev_janelas").select("id").not_.is_("pontuacao_pendente", "null").execute().data
    ja_ids |= {r["id"] for r in pend}

    fila = []
    for j in janelas:
        if j["id"] in ja_ids:
            continue
        e = sb.table("observacao_entradas").select("id,tipo,transcricao,nota").eq("id", j["entrada_id"]).single().execute().data
        texto = (e.get("transcricao") or "").strip() or (e.get("nota") or "").strip()
        if len(texto) < args.min_chars:
            continue
        fila.append((j, e, texto))
    fila = fila[: args.limite]
    print(f"{len(fila)} janela(s) a pontuar (modelo {MODEL}, codebook {CODEBOOK_VERSAO})")
    if args.dry_run:
        for j, e, texto in fila:
            print(f"  - {j['id']} {j['sala']} {j['inicio']}  [{e['tipo']}] {texto[:80]!r}")
        return

    import anthropic
    client = anthropic.Anthropic()
    gravadas = pendentes = puladas = 0
    for j, e, texto in fila:
        out, err = chamar_modelo(client, system, texto)
        if err:
            print(f"  ! {j['id']}: {err}"); puladas += 1; continue
        if not out["avaliavel"]:
            sb.table("dev_janelas").update({"presente": False, "pontuacao_pendente": {"modelo": MODEL, "avaliavel": False, "motivo": out["motivo_nao_avaliavel"], "em": datetime.now(timezone.utc).isoformat()}}).eq("id", j["id"]).execute()
            print(f"  · {j['id']}: não avaliável — {out['motivo_nao_avaliavel']}"); puladas += 1; continue
        cand = por_primeiro_nome.get(norm(out["crianca_alvo"] or "").split(" ")[0], []) if out["crianca_alvo"] else []
        if len(cand) > 1 and out["crianca_alvo"]:
            alvo = norm(out["crianca_alvo"])
            cand = [a for a in cand if norm(f"{a['nome']} {a.get('sobrenome') or ''}").startswith(alvo)] or cand
        linha = {k: out.get(k) for k in ["envolvimento", "autonomia", "persistencia", "persistencia_motivo", "contexto", "material", "adulto_proximo", "confianca", "justificativa"]}
        if len(cand) == 1:
            sb.table("obs_avaliacoes").insert({**linha, "projeto": j["projeto"], "janela_id": j["id"], "entrada_id": j["entrada_id"], "aluno_id": cand[0]["id"],
                                               "avaliador": MODEL, "avaliador_tipo": "modelo", "modelo": MODEL, "codebook_versao": CODEBOOK_VERSAO}).execute()
            sb.table("dev_janelas").update({"aluno_id": cand[0]["id"], "presente": True}).eq("id", j["id"]).execute()
            print(f"  ✓ {j['id']}: {cand[0]['nome']} env={out['envolvimento']} aut={out['autonomia']} per={out['persistencia']} conf={out['confianca']}"); gravadas += 1
        else:
            sb.table("dev_janelas").update({"pontuacao_pendente": {**linha, "modelo": MODEL, "crianca_alvo": out["crianca_alvo"], "candidatas": [c["id"] for c in cand], "em": datetime.now(timezone.utc).isoformat()}}).eq("id", j["id"]).execute()
            print(f"  ? {j['id']}: criança '{out['crianca_alvo']}' não ligada a alunos ({len(cand)} candidatas) — pendente"); pendentes += 1
    print(f"gravadas={gravadas} pendentes={pendentes} puladas={puladas}")


if __name__ == "__main__":
    sys.exit(main())
