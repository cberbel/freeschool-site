# Ferramentas

| Script | O que faz | Como rodar |
| --- | --- | --- |
| `pontuar_entradas.py` | Pontua com o codebook v1 (modelo `claude-opus-5`, `effort=low`, saída estruturada, codebook em cache) as janelas de entrada do Projeto B que ainda não têm nota do modelo; grava em `obs_avaliacoes` (`avaliador_tipo='modelo'`), liga a criança pelo nome citado, e guarda em `dev_janelas.pontuacao_pendente` o que não conseguiu ligar. Idempotente; nunca toca nota humana | `pip install "anthropic>=1.0" "supabase>=2"`; exportar `ANTHROPIC_API_KEY` (chave do Projeto B), `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`; `python tools/pontuar_entradas.py --dry-run` e depois sem `--dry-run` |

Rodar todo dia (cron ou à mão) até a rotina `indexa-observacao` do sistema escolar absorver
a pontuação. Custo: centavos por janela; teto mensal do projeto US$ 150.
