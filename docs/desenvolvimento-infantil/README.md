# Projeto: medir desenvolvimento infantil

Pasta de **material bruto e notas** do projeto de medição objetiva e longitudinal do
desenvolvimento infantil no ambiente Montessori. Nada aqui é código do site — é o
caderno do projeto.

## O que tem aqui

| Arquivo | Fonte | Status |
| --- | --- | --- |
| [`2026-08-29-grok-arquitetura.md`](2026-08-29-grok-arquitetura.md) | Grok | Analisado — ver análise ao lado |
| [`2026-08-29-analise-grok-arquitetura.md`](2026-08-29-analise-grok-arquitetura.md) | Nossa | Em análise — opinião, não decisão |
| [`2026-08-29-passo-a-passo-sistema.md`](2026-08-29-passo-a-passo-sistema.md) | Nossa | Em análise — plano de execução em 8 etapas |

## Convenções

- Um arquivo por material recebido, nomeado `AAAA-MM-DD-fonte-assunto.md`.
- O texto da fonte fica **preservado**; crítica, veredito e decisões nossas vão em
  arquivo próprio (`AAAA-MM-DD-analise-<assunto>.md`), nunca editando o original.
- Cada arquivo abre com fonte, data e status (`NÃO ANALISADO` / `EM ANÁLISE` /
  `DECIDIDO` / `DESCARTADO`).
- Camada jurídica/LGPD está **fora de escopo** nestes documentos por ora, a pedido —
  a análise é só de engenharia.

## Onde o projeto está

O sistema de observação **já roda** no Supabase `ponto-escola-montessoriana`: 47 alunos
ativos, 17 câmeras mapeadas em 10 espaços, 33 sessões de observação com 3 especialistas,
73 entradas (40 transcritas) e indexação por LLM em produção. O que falta não é captação
nem registro — é transformar observação narrativa em **medida comparável**.

O plano de execução está em
[`2026-08-29-passo-a-passo-sistema.md`](2026-08-29-passo-a-passo-sistema.md).

## Próximos passos em aberto

Etapa 1–2 do plano, em ordem:

- [ ] Escrever o **codebook v1** (3 dimensões × 5 níveis, com âncora comportamental).
      Uma tarde, só texto, antes de qualquer código.
- [ ] Rodar a migração `obs_codebook` / `obs_avaliacoes` / `obs_golden`.
- [ ] Adicionar os sliders de 1–5 na tela de observação que já existe.
- [ ] **Medir o kappa humano-humano** em ~100 entradas com dois avaliadores cegos.
      É o teste mais decisivo do projeto — portão para tudo o que vem depois.

Mais adiante (etapas 3+):

- [ ] Ligar `video_inicio_s` / `video_fim_s` (já no schema, 0 de 73 preenchidos).
- [ ] Teste de campo de tag UWB e de leitor RFID numa estante, antes de comprar escala.
- [ ] Decidir a licença do detector (AGPL do YOLO x alternativas Apache-2.0).
