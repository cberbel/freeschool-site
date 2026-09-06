# Bifurcação — Projeto A e Projeto B em paralelo

- **Data:** 2026-09-06
- **Decisão do dono:** seguir em **dois projetos** ("Projeto A" e "Projeto B"; "linha A/B" é sinônimo). O **Projeto A** é a revisão 2 (monitoramento
  quase contínuo). O **Projeto B** mantém as **quatro decisões que a revisão derrubou** — clipe
  ancorado numa entrada, ingestão sob demanda, áudio só da observadora, VLM como rotulador
  "barato" — ou seja, o passo a passo de 29/08 como foi escrito.
- **Por quê:** são duas maneiras de aprender a fazer o sistema. A diferença entre o **gap de
  esforço** e o **gap de resultado** é uma das coisas que os dois projetos ensinam — não a
  principal, e não há pressa de escolher entre eles. O norte do caderno é o
  [README](README.md): aprender a fazer o melhor sistema de registro e aprendizado sobre o
  desenvolvimento infantil. Os dois projetos servem a isso; a comparação é um detalhe útil.
- **Status:** `DECIDIDO` (dois projetos, sem data para escolher) / `EM ANÁLISE` (o protocolo
  de comparação abaixo, como instrumento).
- **Escopo:** só engenharia. Camada jurídica fora, a pedido.

---

## Os dois projetos, lado a lado

| | **Projeto B — amostrado** | **Projeto A — contínuo** |
| --- | --- | --- |
| Especificação | [`2026-08-29-passo-a-passo-sistema.md`](2026-08-29-passo-a-passo-sistema.md), Etapas 1–4 (o doc de 29/08 deixa de ser "superado" e vira a spec do Projeto B) | [`2026-09-05-revisao-2-plano.md`](2026-09-05-revisao-2-plano.md) |
| **1. Unidade de medida** | **Clipe de 3 min ancorado numa entrada** da especialista (`[relogio − 90 s, relogio + 90 s]`); `obs_avaliacoes.entrada_id` | **Janela criança × tempo** (2 min para rótulo humano, 5 min para features); `obs_avaliacoes.janela_id`; janelas sorteadas por sala × hora |
| **2. Ingestão** | **Sob demanda**: recorte do NVR existente quando a entrada é salva (`reolink_aio`, início/fim arbitrários). Nada roda o dia inteiro | **Fundação**: go2rtc + Frigate + worker a 5 fps em 16–17 câmeras, o dia inteiro |
| **3. Áudio** | **Só a narração da observadora** (`observacao-audio` → transcrição → índice), como hoje | Gravador **vestível** por criança para linguagem (Etapa 5b) + clima sonoro por zona |
| **4. Papel do VLM** | **Rotulador de todos os clipes** (`claude-opus-5`, 16 quadros, Batch, saída estruturada). A ~800 clipes/mês "o custo não importa" — e neste projeto é verdade | Rotulador **só da amostra** (2–4 mil janelas/mês); a medida contínua vem de modelo local sobre keypoints, RFID, UWB, áudio |
| Fonte de rótulo humano | Sliders na **entrada** (3 dimensões, 15 s) | Sliders na **janela sorteada** + calibração contínua |
| Corpus dourado | 300–500 **clipes de entrada** (`obs_golden` com `entrada_id`) | ≥ 60% **janelas aleatórias** + blocos contínuos (`obs_golden` com `janela_id`) |
| Identidade da criança | A especialista escreve quem é | Tracker + UWB (piloto) + marcador visual |
| Medida por criança | Média das notas (humana + VLM) nos clipes daquela criança na semana | Agregados por janela com cobertura; modelo misto |
| Saída pedagógica | Parágrafo semanal por criança gerado por LLM a partir das notas dos clipes | Idem, a partir das features da semana |
| Hardware novo | **Nenhum** (talvez disco para o NVR reter 14 dias) | Edge com GPU, HDs, pilotos RFID/UWB/áudio (seção 5 da revisão 2) |
| Onde o esforço mora | **Tempo de especialista** (cada clipe nasce de uma entrada humana) | **Tempo de construção e hardware** |
| O que ela não enxerga, por desenho | Rotina, transições, fila, sesta; social; linguagem da criança; qualquer criança sem entrada naquela semana | Nada por desenho — mas tudo depende de sensores ainda não validados |

**Duas perguntas que os projetos ajudam a responder, no seu tempo:** o Projeto B mede a
criança ou mede a agenda da especialista? E o Projeto A paga, em esforço, o que entrega a
mais em resultado? Nenhuma das duas precisa de resposta rápida — precisa de dado bom.

---

## Tronco comum (não duplicar — é o que torna a comparação justa)

1. **Codebook v1** e o dicionário operacional — **um só**, versionado em `obs_codebook`. Os
   dois projetos pontuam com a mesma âncora comportamental.
2. **As 2 avaliadoras** (a coluna `especialista` tem `claudio`, `Claudio` e `Sonia` — duas pessoas; confirmar com a escola) — as mesmas, com o tempo **apontado por projeto** (ver esforço). Com 2, a métrica é o kappa quadrático de Cohen; alfa só se entrar uma 3ª.
3. **Schema** — `obs_codebook`, `obs_avaliacoes`, `obs_golden`, `dev_janelas`, com uma coluna
   nova: `projeto text not null check (projeto in ('A','B','comum'))`. `obs_avaliacoes` já suporta
   os dois ancoradouros (`entrada_id` **ou** `janela_id`); a coluna `projeto` diz qual pipeline
   gerou a linha. Nada mais muda.
4. **Kappa da semana 3 (T3)** — feito **nas duas unidades**: 30 clipes de entrada (B) **e** 30
   janelas aleatórias (A), pelas mesmas 2 avaliadoras, cegas. É o primeiro número da
   bifurcação: **a concordância humana é diferente em "momentos que chamaram atenção" e em
   rotina?** (A revisão prevê que o acordo em rotina é menor. Se for, isso já é resultado.)
5. **Supabase, páginas estáticas, worker Python** — a mesma stack; o Projeto B não ganha uma segunda.
6. **O conjunto de comparação** (abaixo) — sorteado e pontuado uma vez, usado pelos dois.
7. **Mapa de medição** da revisão 2 — os dois projetos reportam nas mesmas dimensões, e o mapa
   diz para cada dimensão o que cada projeto consegue e o que não consegue.

**Contaminação a evitar.** As especialistas produzem as entradas do Projeto B **e** pontuam as
janelas do Projeto A. Regras: (a) os painéis por criança do Projeto A **não são mostrados** às especialistas durante o
período de comparação (senão as entradas de B passam a ser guiadas por A); (b) o tempo é
apontado no ato, por projeto, não reconstruído de memória; (c) o job de clipe do Projeto B lê o **NVR**,
não o Frigate do Projeto A — se B usar a ingestão de A, o gap de esforço de B fica falso.

---

## O que se mede: esforço

Uma tabela, preenchida toda sexta, por projeto. É instrumentação do aprendizado — barata de
manter e impossível de reconstruir depois.

```sql
create table bifurcacao_esforco (
  id           uuid primary key default gen_random_uuid(),
  semana       date not null,                 -- segunda-feira da semana
  projeto      text not null check (projeto in ('A','B','comum')),
  categoria    text not null check (categoria in
                 ('construcao','operacao','especialista','hardware_brl','api_usd','outro')),
  quantidade   numeric not null,              -- horas, R$ ou US$ conforme a categoria
  quem         text,
  nota         text
);
```

| Métrica de esforço | Como se mede | O que se espera (hipótese a testar) |
| --- | --- | --- |
| Horas de construção | Apontamento do construtor, por projeto | A ≫ B |
| Horas de operação | Reinício de stream, recarga de gravadores, troca de bateria de tag, manutenção do NVR | A ≫ B |
| Horas de especialista | Entradas (B) × tempo médio; janelas pontuadas (A); comparação (comum) | **B ≫ A por criança coberta** — é a hipótese central: B só escala com gente |
| Hardware (R$ acumulado) | Notas fiscais | A ≫ B (B ≈ 0) |
| API (US$/mês) | Console da Anthropic, por chave — **uma chave por projeto** | Parecido em valor absoluto; muito diferente por janela medida |
| Dias-calendário até o marco | "primeiro relatório semanal por criança para as 47"; "primeira curva de 3 meses" | B chega primeiro ao relatório; A chega primeiro à curva |

O número que interessa no fim não é o total, é a **razão**: horas e reais **por criança-semana
efetivamente medida**.

## O que se mede: resultado

Cinco componentes, porque "resultado" mistura coisas diferentes e a bifurcação só ensina se
separá-las.

### 1. Cobertura

Fração de **criança-semanas** com medida. Denominador = crianças presentes naquela semana
(o ponto já sabe). Para B, "medida" = ≥ 3 clipes da criança na semana; para A, ≥ 50% das
janelas do tempo presente com cobertura ≥ 0,8. Hoje B parte de **~1,5 entrada por criança por
mês** — cobrir 47 crianças toda semana exige uma mudança de rotina das especialistas, e esse
custo é exatamente o que a tabela de esforço captura.

### 2. Validade do pontuador (o mesmo alvo para os dois)

**Conjunto de comparação:** 20 janelas aleatórias por semana (sorteio por sala × faixa horária,
começando pelas 18 crianças com autorização de imagem), pontuadas cegas por 2 especialistas
→ consenso. **Os dois projetos pontuam as mesmas janelas:** A com o que tiver (VLM sobre a
janela até a Etapa 6; modelo local depois); B com o **seu** pontuador — o VLM sobre um clipe de
3 min recortado do NVR em torno do mesmo instante. Métrica: alfa de Krippendorff ordinal de
cada projeto contra o consenso, por dimensão. Isso separa "o pontuador de B é bom?" de "a
amostragem de B é boa?" — são perguntas diferentes e a segunda é a que o desenho de B
compromete.

### 3. Viés de amostragem (o coração da bifurcação)

Para cada criança-semana em que **os dois** projetos têm medida: `viés = média_B − média_A`.
Se as entradas das especialistas são "momentos que chamaram atenção", B será sistematicamente
mais alto (ou mais extremo) que A para a mesma criança na mesma semana. Reportar: viés médio,
desvio, correlação entre os rankings das crianças (Spearman) e a fração de semanas em que os
dois projetos ordenam as crianças de forma diferente. **Este é o número que ninguém tem hoje e que
só a bifurcação produz.**

### 4. Sensibilidade

Cada projeto consegue detectar uma mudança real? Duas provas: (a) **efeito de idade** em 3 meses
(deve existir em qualquer medida válida de desenvolvimento) — estimado por projeto, contra o
ruído do próprio projeto; (b) **uma intervenção planejada** — a equipe introduz um material novo
numa turma (ou muda um horário) numa data conhecida; quantos dias cada projeto leva para mostrar
a mudança em repetição/envolvimento, e com que confiança. B mede isso só se houver entradas;
A mede por RFID/janela.

### 5. Utilidade pedagógica (o "e daí?")

Toda semana, os parágrafos por criança dos dois projetos vão para a equipe **sem dizer de qual
projeto veio cada um**. A professora responde a duas perguntas por parágrafo: "isso eu já sabia?"
e "isso muda o que eu faço amanhã?". Contagem por projeto. Sem isso, o resultado é acadêmico.

```sql
create table bifurcacao_resultados (
  semana   date not null,
  projeto  text not null check (projeto in ('A','B')),
  metrica  text not null,   -- 'cobertura','alfa_envolvimento','vies_medio','spearman',
                            -- 'dias_para_detectar','util_ja_sabia','util_muda_amanha', ...
  valor    numeric,
  n        integer,
  nota     text,
  primary key (semana, projeto, metrica)
);
```

---

## Cronograma da bifurcação

| Quando | Comum | Projeto B | Projeto A |
| --- | --- | --- | --- |
| Semana 1 | Codebook v1; T0 inventário; DDL única (Revisão 2.1) **com a coluna `projeto`**; sliders; chaves de API separadas; `bifurcacao_esforco` criada | — | T1 captação no PC existente (3 câmeras); RFID/UWB **cotados** (pedido após o T1, com aprovação) |
| Semana 2 | Calibração em voz alta (10 clipes + 10 janelas) | Job de clipe a partir do **NVR** (T4, versão B); especialistas passam a registrar entradas com meta de cobertura (ex.: 3 por criança por semana) | T2 sincronização |
| Semana 3 | **T3 kappa nas duas unidades** (30 clipes + 30 janelas, 2 avaliadoras cegas) → primeiro resultado | VLM sobre os clipes (Etapa 4 de 29/08) | T4 versão A (clipe de janela via Frigate) |
| Semana 4 | Conjunto de comparação começa (20 janelas/semana) | Primeiro relatório semanal por criança (as que tiverem clipe) | T5–T10 |
| Semanas 5–8 | Comparação semanal; esforço apontado | Golden B (clipes) | Golden A (janelas); sorteio diário; RFID instalado |
| Semanas 8–16 | **Janela de comparação** (8 semanas com os dois projetos produzindo medida semanal para as mesmas crianças); intervenção planejada na semana 10 | Regime estável | Etapa 5b áudio piloto; edge se T1/T5 pediram; Etapa 6 começa |
| Mês 4 | **Primeira leitura** (esforço acumulado; cobertura; viés; utilidade) | | |
| Mês 6 | **Segunda leitura**, com efeito de idade por projeto | | |
| Depois | Leituras a cada trimestre, enquanto os dois rodarem | | |

Os dois projetos continuam. As leituras alimentam o aprendizado; não são prazos de decisão.
Se um dia fizer sentido fundir, encolher ou encerrar um deles, será porque o dado mostrou —
não porque o calendário mandou.

---

## Hipóteses que os dois projetos ajudam a testar

Não há regra de decisão nem data. Mas vale escrever agora, antes de ver dado, o que cada
desfecho **significaria** — para não reinterpretar o resultado depois. Três hipóteses:

1. **B ≈ A em validade e utilidade; a cobertura de B basta para a equipe.** Então o produto é
   o B — observação humana ampliada por VLM — e o A vira instrumento de pesquisa, não de operação.
   O gap de esforço foi pago à toa? Não: sem A não haveria como saber que B bastava.
2. **A enxerga o que B não enxerga (rotina, social, linguagem, transições) e a equipe diz que
   isso muda o que faz.** Então o produto é o A, e o custo do A se justifica pelo que só ele mede.
   O B continua como camada de calibração humana — que é exatamente o papel que a revisão 2 lhe
   dá.
3. **Híbrido (o mais provável):** os **sensores de contagem** do A (RFID, UWB, áudio por zona)
   entregam a maior parte do ganho de cobertura por uma fração do esforço da **visão** contínua,
   e os clipes humanos do B seguem sendo a melhor fonte de rótulo de construto. Produto =
   B + sensores de contagem, sem visão contínua; visão fica para o que os sensores não medem
   (postura, orientação de cabeça, resistência à distração).

Se e quando alguém quiser ler o resultado, estes são critérios razoáveis para distinguir
1 de 2 — fixados agora para não serem ajustados ao gosto depois: (a) Spearman entre os
rankings semanais das crianças ≥ 0,8 **e** viés médio < 0,3 ponto → "B ≈ A" em resultado;
(b) utilidade "muda o que faço amanhã" de A ≥ 1,5× a de B → A vale o esforço; (c) horas de
especialista por criança-semana coberta no B > 3× as do A → B não escala. São réguas, não
gatilhos.

---

## O que registrar no doc de cada projeto

- **B:** o passo a passo de 29/08 é a spec; acrescentar só a coluna `projeto`, a meta de cobertura
  (entradas por criança por semana) e a chave de API própria. **Não** "melhorar" o B com peças do
  A durante a comparação — se o B ganhar janelas sorteadas ou Frigate, deixa de ser B.
- **A:** a revisão 2 é a spec; acrescentar a coluna `projeto` e o conjunto de comparação como
  parte da calibração contínua (já prevista: 20 janelas/semana — é o mesmo esforço).

## Riscos da bifurcação

1. **Tempo de especialista é o recurso escasso dos dois projetos.** B precisa de entradas; A
   precisa de janelas pontuadas; a comparação precisa de consenso. Somado, pode passar de
   5 h/semana por avaliadora (portão de realismo da Revisão 2.1). Se estourar, corta-se a comparação para 10 janelas/semana antes de
   cortar qualquer projeto.
2. **O B pode "vencer" por ser a rotina que a equipe já conhece** — a utilidade percebida tem
   viés de familiaridade. Por isso os parágrafos vão cegos.
3. **O A pode "vencer" por novidade** — a mesma razão, ao contrário. Por isso as leituras são
   trimestrais e continuam, em vez de uma leitura única.
4. **Construtor solo:** o A consome quase todo o tempo de construção; o B quase nenhum. Isso é o
   gap de esforço funcionando como previsto — mas significa que atrasos no A não podem ser
   compensados tirando tempo do B, porque o B quase não tem tempo a tirar.
