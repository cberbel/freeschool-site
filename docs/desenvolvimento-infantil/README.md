# Projeto: medir desenvolvimento infantil

Pasta de **material bruto e notas** do projeto de medição objetiva e longitudinal do
desenvolvimento infantil no ambiente Montessori. Nada aqui é código do site — é o
caderno do projeto.

## O que tem aqui

| Arquivo | Fonte | Status |
| --- | --- | --- |
| [`2026-08-29-grok-arquitetura.md`](2026-08-29-grok-arquitetura.md) | Grok | Analisado — ver análise ao lado |
| [`2026-08-29-analise-grok-arquitetura.md`](2026-08-29-analise-grok-arquitetura.md) | Nossa | Em análise — opinião, não decisão |
| [`2026-08-29-passo-a-passo-sistema.md`](2026-08-29-passo-a-passo-sistema.md) | Nossa | Superado em parte pela revisão 2 (unidade, ingestão, áudio, ordem) — ler junto |
| [`2026-09-05-revisao-2-plano.md`](2026-09-05-revisao-2-plano.md) | Nossa (painel de revisão) | Em análise — revisão contra a meta de monitoramento quase contínuo; roadmap integrado |

## Convenções

- Um arquivo por material recebido, nomeado `AAAA-MM-DD-fonte-assunto.md`.
- O texto da fonte fica **preservado**; crítica, veredito e decisões nossas vão em
  arquivo próprio (`AAAA-MM-DD-analise-<assunto>.md`), nunca editando o original.
- Cada arquivo abre com fonte, data e status (`NÃO ANALISADO` / `EM ANÁLISE` /
  `DECIDIDO` / `DESCARTADO`).
- Camada jurídica/LGPD está **fora de escopo** nestes documentos por ora, a pedido —
  a análise é só de engenharia.

## Onde o projeto está

**Meta (05/09):** monitorar todo o desenvolvimento, de modo quase contínuo — sensoriamento
passivo o dia inteiro, todas as dimensões; a observação humana vira calibração.

O sistema de observação **já roda** no Supabase `ponto-escola-montessoriana`: 47 alunos
ativos, 16 câmeras nomeadas (~15 aparelhos) em 10 espaços, 33 sessões com 3 especialistas,
75 entradas (40 transcritas — quase todas testes de microfone) e indexação por LLM.
`meal_events` existe como schema, com **0 eventos**. As câmeras nunca foram inventariadas.

O plano vigente é a **revisão 2**
([`2026-09-05-revisao-2-plano.md`](2026-09-05-revisao-2-plano.md)), que corrige o passo a
passo de 29/08 para a meta contínua: unidade = janela criança × tempo; ingestão como
fundação (go2rtc + Frigate); áudio vestível para linguagem; VLM só na amostra; compras só
com número medido.

## Próximos passos em aberto

Primeira semana da revisão 2 (custo zero):

- [ ] **T0 — inventário técnico das câmeras** (modelo, streams, fps, PoE, NVR, mic) e
      confirmar `'sala 1'`, "sala MEIO" e as duas lentes do pátio.
- [ ] Escrever o **codebook v1** (3 dimensões × 5 níveis, âncora comportamental). Uma tarde.
- [ ] Migração mínima: `obs_codebook`, `obs_avaliacoes` com `janela_id`, `dev_janelas`,
      `obs_golden` por janela, `salas_cameras` normalizada, `materiais` vazia.
- [ ] **Encomendar o piloto RFID** (banda 902–928 MHz) — lead time.
- [ ] **T1 — go2rtc + Frigate no PC existente** com as 7 câmeras das salas; `captacao_stats`.
- [ ] Sliders na tela de observação; T2 sincronização de relógio.
- [ ] Semana 3: **kappa em 60 janelas gravadas** × 3 especialistas (alfa ≥ 0,6) — portão 1.
- [ ] Semana 4: T5 pose offline, T6 identidade, T7 VLM, T8 teste-reteste, T9 áudio de câmera,
      T10 ativar `meal_events` → decisões de compra com número.

Pendente do painel: crítico de completude e refutação dos achados 5–8 de testes (cortados
pelo limite de uso; podem ser retomados).
