# Projeto: medir desenvolvimento infantil

## Norte

**Aprender a fazer o melhor sistema de registro e aprendizado sobre o desenvolvimento
infantil do mundo.** (Dono, 06/09/2026.)

Isso ordena tudo o que está nesta pasta: *registro* — tudo o que se observa fica guardado,
comparável ao longo de anos, por criança; *aprendizado* — a equipe aprende sobre cada criança,
e o sistema aprende com a equipe. Não há pressa. Os dois projetos (A e B) são duas maneiras de
aprender a fazer isso; a comparação entre eles é um instrumento, não o objetivo.

**Regra master: tudo para hoje, nada para amanhã.** E o sistema **não espera ninguém**:
começa com as observações e os critérios que temos; o modelo pontua desde já (o que existe e
cada entrada nova); as avaliadoras entram quando puderem e pontuam a mesma janela — ao vivo ou
no passado. Kappa e consenso são portão do que chamamos de "medido", não portão do trabalho.

Pasta de **material bruto e notas** do projeto de medição objetiva e longitudinal do
desenvolvimento infantil no ambiente Montessori. Nada aqui é código do site — é o
caderno do projeto.

## O que tem aqui

| Arquivo | Fonte | Status |
| --- | --- | --- |
| [`2026-08-29-grok-arquitetura.md`](2026-08-29-grok-arquitetura.md) | Grok | Analisado — ver análise ao lado |
| [`2026-08-29-analise-grok-arquitetura.md`](2026-08-29-analise-grok-arquitetura.md) | Nossa | Em análise — opinião, não decisão |
| [`2026-08-29-passo-a-passo-sistema.md`](2026-08-29-passo-a-passo-sistema.md) | Nossa | **Spec do Projeto B (amostrado)** — clipe ancorado em entrada, VLM como rotulador |
| [`2026-09-05-revisao-2-plano.md`](2026-09-05-revisao-2-plano.md) | Nossa (painel de revisão) | **Spec do Projeto A (contínuo)** — inclui a Revisão 2.1 (06/09): erratas, tabela de captação, DDL única, riscos, primeira semana única |
| [`2026-09-06-bifurcacao-projetos-a-b.md`](2026-09-06-bifurcacao-projetos-a-b.md) | Nossa | **Decidido** — Projeto A e Projeto B em paralelo; protocolo de comparação de esforço × resultado |
| [`2026-09-06-codebook-v1.md`](2026-09-06-codebook-v1.md) | Nossa | **Vigente** — codebook v1 (envolvimento, autonomia, persistência); vale para humanos e modelo; gravado em `obs_codebook` |
| [`2026-09-06-decisoes-v0.md`](2026-09-06-decisoes-v0.md) | Nossa | **Vigente** — decisões v0 numa página (regra master, captação, stack, schema, compras) |
| [`2026-09-06-perguntas-escola.md`](2026-09-06-perguntas-escola.md) | Nossa | Pronto para enviar — 15 perguntas; nenhuma bloqueia o trabalho |
| [`sql/2026-09-06-ddl-v0.sql`](sql/2026-09-06-ddl-v0.sql) | Nossa | **Aplicada em 06/09** no projeto `ponto-escola-montessoriana` (aditiva, RLS ligado) |
| [`sql/2026-09-06-trigger-janela-por-entrada.sql`](sql/2026-09-06-trigger-janela-por-entrada.sql) | Nossa | **Aplicada em 06/09** — janela automática (Projeto B) por entrada com sala válida; guardada, nunca aborta a página; backfill feito |
| [`tools/pontuar_entradas.py`](tools/README.md) | Nossa | Pronto para rodar com a chave do Projeto B — o modelo pontua as janelas existentes com o codebook v1 |

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
ativos, 16 câmeras nomeadas (~15 aparelhos) em 10 espaços, 33 sessões com 2 avaliadoras,
75 entradas (40 transcritas — quase todas testes de microfone) e indexação por LLM.
`meal_events` existe como schema, com **0 eventos**. As câmeras nunca foram inventariadas.

**Decisão (06/09): Projeto A e Projeto B em paralelo.** O **Projeto A** segue a revisão 2 (janela
criança × tempo, ingestão contínua, áudio vestível, VLM só na amostra). O **Projeto B** mantém o
passo a passo de 29/08 (clipe ancorado em entrada, recorte sob demanda do NVR, áudio da
observadora, VLM em todos os clipes). Os dois rodam sobre o mesmo codebook, as mesmas
especialistas e o mesmo schema (coluna `projeto`), com esforço apontado por projeto e um conjunto
de comparação semanal. A comparação é um detalhe útil, não o principal: os dois projetos
continuam, sem data para escolher.
Protocolo em [`2026-09-06-bifurcacao-projetos-a-b.md`](2026-09-06-bifurcacao-projetos-a-b.md).

## Próximos passos em aberto

Feito em 06/09: codebook v1 (no repositório e em `obs_codebook`), decisões v0, perguntas à
escola, DDL v0 aplicada (tabelas novas com RLS ligado, `cameras` semeada a partir de
`salas_cameras`, colunas de vídeo/relógio adicionadas). Trigger de janela por entrada aplicado e
backfill feito. Pendências deliberadas: normalização de `especialista`, `sala 1` → `sala 1a3`
(após confirmação), policies das páginas (com os sliders).

Primeira semana (custo zero):

- [ ] **Segunda:** enviar as [perguntas à escola](2026-09-06-perguntas-escola.md); ler a
      [página de decisões](2026-09-06-decisoes-v0.md) com a equipe.
- [ ] **Desde já:** rodar `tools/pontuar_entradas.py` com a chave do Projeto B (o modelo pontua
      as janelas existentes com o codebook v1); depois absorver na rotina `indexa-observacao`.
      **Uma chave de API por projeto.**
- [ ] **T0 — inventário técnico das câmeras** preenchendo `cameras` (modelo, streams, fps, PoE,
      NVR, mic) e **teste de N main streams simultâneos do NVR** (risco crítico, não verificado).
- [ ] Sliders na tela de observação gravando em `obs_avaliacoes` (a janela por entrada já é
      criada por trigger); policies das páginas; RPC `now()` → `relogio_servidor` (T2).
- [ ] **T1 — go2rtc + Frigate no PC existente**, começando com 3 câmeras, sem mexer em fps/bitrate; `captacao_stats`.
- [ ] **Cotar** discos, o piloto RFID (banda 902–928 MHz), o UWB (MaUWB_ESP32S3) e o AP dedicado; pedido só depois do T1, com aprovação.
- [ ] Projeto B, semana 2: job de clipe a partir do **NVR** (não do Frigate) e meta de
      cobertura das entradas (≈ 3 por criança por semana).
- [ ] Semana 3: **kappa nas duas unidades** — 30 clipes de entrada (B) + 30 janelas
      aleatórias (A), 2 avaliadoras cegas (kappa quadrático ≥ 0,6) — portão 1 e primeiro
      resultado da bifurcação.
- [ ] Semana 4: T5 pose offline, T6 identidade, T7 VLM, T8 teste-reteste, T9 áudio de câmera,
      T10 ativar `meal_events` → decisões de compra com número.

O painel terminou (3ª rodada, 06/09): crítico de completude e roadmap integrado incorporados na Revisão 2.1.
