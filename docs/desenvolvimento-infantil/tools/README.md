# Ferramentas

**Caminho canônico (nuvem, sem credencial local):** a edge function `pontuar-janelas`
(fonte em `../functions/pontuar-janelas/index.ts`, SQL em `../sql/2026-09-07-pontuacao-janelas.sql`)
faz o mesmo que o script abaixo, roda no Supabase com a chave Anthropic que já existe nos secrets
do projeto e é disparada pelo pg_cron (job `pontuar-janelas`, dias úteis 11–23 UTC, a cada 15 min).
Disparo manual: `select public.disparar_pontuacao_janelas(10);` (o número é o limite de janelas).
O script Python fica como alternativa local (mesma lógica, mesmas tabelas).

| Script | O que faz | Como rodar |
| --- | --- | --- |
| `pontuar_entradas.py` | Pontua com o codebook v1 (modelo `claude-opus-5`, `effort=low`, saída estruturada, codebook em cache) as janelas de entrada do Projeto B que ainda não têm nota do modelo; grava em `obs_avaliacoes` (`avaliador_tipo='modelo'`), liga a criança pelo nome citado, e guarda em `dev_janelas.pontuacao_pendente` o que não conseguiu ligar. Idempotente; nunca toca nota humana | `pip install "anthropic>=1.0" "supabase>=2"`; exportar `ANTHROPIC_API_KEY` (chave do Projeto B), `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`; `python tools/pontuar_entradas.py --dry-run` e depois sem `--dry-run` |

Custo: centavos por janela; teto mensal do projeto US$ 150.
