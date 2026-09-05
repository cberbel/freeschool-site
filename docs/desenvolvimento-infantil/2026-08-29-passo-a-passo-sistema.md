# Passo a passo — construir o sistema de IA de medição

- **Data:** 2026-08-29
- **Base:** a [análise crítica](2026-08-29-analise-grok-arquitetura.md) + inspeção do
  banco real (`ponto-escola-montessoriana`, Postgres 17, sa-east-1)
- **Status:** `EM ANÁLISE` — proposta de execução, não decisão tomada.
- **Escopo:** só engenharia. Camada jurídica fora, a pedido.

---

## O ponto de partida real

O roadmap da análise anterior assumia começar do zero. Não é o caso — **metade da
fundação já está de pé e rodando há um mês.** O que o banco mostra hoje:

| Já existe | Estado | O que significa para o projeto |
| --- | --- | --- |
| `alunos` | 47 ativos, **100% com data de nascimento**, 3 agrupadas | Idade exata como covariável, de graça. É a variável de confusão nº 1 e ela já está lá |
| `salas_cameras` | **17 câmeras em 10 espaços** (sala 1a3: 4, sala 3a6: 3, pátio: 3, +7) | A camada de captação existe. Não precisa comprar câmera pra começar |
| `observacao_sessoes` | 33 sessões, **3 especialistas**, 01/08 a 24/08, modos `vivo` e `gravacao` | Já há prática de observação estruturada e mais de um observador. É o insumo do kappa |
| `observacao_entradas` | 73 entradas (`corte`/`fala`/`fim`), 40 com transcrição, 45 com sala | O registro por evento já existe, com áudio e texto |
| `observacao_indice` | 36 registros, indexados por `claude-haiku-4-5` | **Já existe pipeline de IA em produção** extraindo pessoas (com `aluno_id`!), materiais, ações, tema, sentimento |
| `observacao_entradas.video_inicio_s` / `video_fim_s` | **existem no schema, 0 de 73 preenchidos** | O gancho para ligar observação a vídeo foi projetado e nunca usado. É o atalho mais barato do projeto |
| `registros_pedagogicos`, `planejamentos` | 21 e 1 | Camada pedagógica de saída já modelada |

**Conclusão que mais importa:** vocês não precisam construir a captação nem o registro.
Precisam transformar **observação narrativa** em **medida comparável**. Hoje a saída é
texto livre + índice semântico — rico para ler, inútil para comparar duas crianças ou a
mesma criança em dois meses. Falta a nota, falta o segundo avaliador no mesmo evento, e
falta o recorte de vídeo.

Uma restrição de amostra a registrar desde já: **18 dos 47 alunos têm
`autorizacao_imagem = true`.** O corpus de vídeo rotulável nasce com 18 crianças; a
escala por observação humana cobre as 47. Isso muda o desenho — não impede nada, mas
define de quem você pode treinar modelo de visão.

---

## O princípio que organiza o plano

**Cada etapa entrega valor sozinha e produz o insumo obrigatório da próxima.** Se o
projeto parar em qualquer ponto, o que foi feito continua servindo. Nenhuma etapa é
"infraestrutura para depois".

```
Etapa 1  escala           → produz RÓTULO      (e já melhora o registro pedagógico)
Etapa 2  kappa            → valida o RÓTULO    (e conserta o codebook antes de custar caro)
Etapa 3  clipe            → ancora rótulo em VÍDEO (e vira acervo de formação da equipe)
Etapa 4  pré-rotulagem    → multiplica RÓTULO  (e devolve tempo pras professoras)
Etapa 5  instrumentação   → MÉTRICA OBJETIVA sem visão (e ground truth grátis pra etapa 6)
Etapa 6  visão            → escala a MEDIDA    (validada contra a etapa 5)
Etapa 7  longitudinal     → vira MEDIDA de verdade (é aqui que nasce o ativo)
```

---

## Etapa 1 — A escala (semanas 1–2)

**Objetivo:** toda entrada de observação passa a carregar nota numérica em dimensões
definidas, sem perder a narrativa.

**O que construir:** uma tabela de *avaliação* separada de `observacao_entradas` — não
colunas na entrada. O motivo é o coração do projeto: **a mesma entrada precisa poder
receber N avaliações de avaliadores diferentes.** Sem isso não existe kappa, não existe
teto humano, não existe validação de modelo.

```sql
-- versão da definição operacional; muda quando o codebook muda
create table obs_codebook (
  versao       text primary key,           -- 'v1'
  descricao    text not null,
  dimensoes    jsonb not null,             -- {envolvimento:{1..5, ancoras:[...]}, ...}
  vigente_de   date not null,
  vigente_ate  date
);

create table obs_avaliacoes (
  id              uuid primary key default gen_random_uuid(),
  entrada_id      uuid not null references observacao_entradas(id) on delete cascade,
  aluno_id        uuid not null references alunos(id),
  avaliador       text not null,           -- mesmo vocabulário de observacao_sessoes.especialista
  avaliador_tipo  text not null check (avaliador_tipo in ('humano','modelo')),
  envolvimento    smallint check (envolvimento between 1 and 5),
  autonomia       smallint check (autonomia between 1 and 5),
  persistencia    smallint check (persistencia between 1 and 5),
  contexto        text,                    -- 'vida pratica'|'sensorial'|'linguagem'|'matematica'|'livre'
  material        text,
  adulto_proximo  boolean,
  confianca       smallint check (confianca between 1 and 5),
  modelo          text,                    -- null p/ humano; model id p/ modelo
  codebook_versao text not null references obs_codebook(versao),
  em              timestamptz not null default now(),
  unique (entrada_id, aluno_id, avaliador, codebook_versao)
);
create index on obs_avaliacoes (aluno_id, em);
create index on obs_avaliacoes (entrada_id);
```

O `unique` é o que permite duas linhas para a mesma entrada com avaliadores diferentes —
é a estrutura inteira do kappa, embutida no schema.

**Antes do código, o codebook.** Uma tarde de trabalho, e é o documento mais importante
do projeto. Para cada dimensão, 5 níveis com **âncora comportamental** — o que se vê,
não o que se sente. Base sugerida: escala de envolvimento de Leuven (LIS-YC, 5 pontos),
adaptada ao vocabulário Montessori. Exemplo do nível 5 de envolvimento: *"trabalha sem
interrupção por mais de X minutos; movimento preciso; não redireciona atenção quando
outra criança passa ou derruba algo; retoma sozinha após erro."* Repare que "ficar
parada" **não** aparece — é a armadilha que a análise anterior detalha.

**Tela:** um passo a mais na página de observação que já existe. Ao encerrar uma entrada
do tipo `corte`, aparecem 3 sliders de 1–5 + contexto + material. 15 segundos por
entrada, não mais.

**Entregável:** 100% das entradas novas com pelo menos uma avaliação.
**Portão para a etapa 2:** ≥150 entradas avaliadas, sendo ≥100 com **duas** avaliações
independentes.

---

## Etapa 2 — O kappa (semana 3)

Esta é a etapa mais barata e mais decisiva do projeto inteiro. **Não pule, e não a
adie.**

**Objetivo:** descobrir se duas professoras olhando a mesma cena dão a mesma nota. Se não
derem, o construto está mal definido e todo modelo treinado em cima herda o ruído.

**Protocolo:** 2 dos 3 especialistas avaliam as mesmas ~100 entradas, **cegos entre si**
(a tela não mostra a nota do outro). Sem discutir antes.

**Cálculo:** concordância exata e adjacente saem em SQL; o kappa ponderado quadrático
(o correto para escala ordinal) sai num script curto em Python/DuckDB sobre o mesmo
dado.

```sql
-- concordância bruta entre dois avaliadores, por dimensão
with pares as (
  select a.entrada_id, a.aluno_id,
         a.envolvimento e1, b.envolvimento e2
  from obs_avaliacoes a
  join obs_avaliacoes b
    on b.entrada_id = a.entrada_id and b.aluno_id = a.aluno_id
   and b.avaliador > a.avaliador
   and b.codebook_versao = a.codebook_versao
  where a.avaliador_tipo = 'humano' and b.avaliador_tipo = 'humano'
)
select count(*) n,
       round(avg((e1 = e2)::int)::numeric, 3)            concordancia_exata,
       round(avg((abs(e1 - e2) <= 1)::int)::numeric, 3)  concordancia_adjacente,
       round(avg(abs(e1 - e2))::numeric, 2)              erro_medio
from pares;
```

**Portão:** kappa ponderado ≥ 0,6 em envolvimento.
- **Se passar:** siga. Esse número vira o **teto** contra o qual todo modelo é medido
  para sempre.
- **Se não passar:** **pare e reescreva o codebook.** Olhe os pares onde as notas
  divergiram 2+ pontos, descubra o que cada uma estava vendo, reescreva a âncora, e
  refaça. Duas ou três iterações são normais e são trabalho útil — não é atraso, é o
  projeto.

---

## Etapa 3 — O clipe (semanas 4–6)

**Objetivo:** ancorar cada avaliação num pedaço de vídeo recuperável. É o que
transforma um registro em **dado de treino**.

**Por que é barato aqui:** `video_inicio_s` e `video_fim_s` já estão no schema e estão
vazios. As 17 câmeras já estão mapeadas por sala. O trabalho é ligar os dois.

**O que construir:**
1. Gravação contínua no gravador local, com retenção curta (a análise tem a conta:
   ~216 GB/dia em 6 streams 4K; com 17 câmeras, dimensione o disco antes).
2. Um recorte automático: ao salvar uma entrada com `sala` preenchida, um job extrai
   o trecho `[relogio - 90s, relogio + 90s]` da câmera daquela sala e grava o clipe no
   Supabase Storage, preenchendo `video_inicio_s`/`video_fim_s`.
3. **Corpus dourado** — tabela nova, pequena, e a coisa mais valiosa que vocês vão ter:

```sql
create table obs_golden (
  entrada_id   uuid primary key references observacao_entradas(id),
  incluido_em  date not null default current_date,
  motivo       text,          -- por que este clipe entrou (cobertura de idade, material, nível)
  consenso     jsonb,         -- notas de consenso das 2+ avaliadoras humanas
  permanente   boolean not null default true
);
```

300–500 clipes cobrindo idades, salas, materiais, níveis de envolvimento e estações do
ano. **Retenção indefinida**, fora da política de expurgo. Toda versão futura de modelo
repontua esse conjunto — é a âncora de calibração que impede a "curva de
desenvolvimento" de medir a troca de modelo (o furo nº 3 da análise). Comece pelas 18
crianças com autorização de imagem.

**Entregável:** ≥300 clipes com avaliação humana ligada.
**Portão:** o corpus dourado fechado e congelado, com consenso registrado.

---

## Etapa 4 — Pré-rotulagem por modelo (semanas 6–8)

**Objetivo:** multiplicar rótulo. A professora deixa de **criar** a nota e passa a
**corrigir** uma nota proposta — na prática ~3× mais rápido por entrada.

Vocês já têm metade disso: a rotina `indexa-observacao` já roda `claude-haiku-4-5` sobre
a transcrição e extrai pessoas, materiais, ações e tema. Estender para propor as notas da
escala é uma mudança de prompt e de schema de saída, não um sistema novo.

**Como fazer:**
- **Saída estruturada** (`output_config.format` / `messages.parse()`) com o schema exato
  das dimensões. Nada de parsear texto solto.
- **Cache do prefixo:** o codebook inteiro vai no prompt e não muda entre chamadas —
  põe `cache_control` nele. É o maior corte de custo e não custa nada implementar.
- **Batch API** (`messages.batches.create`) para o lote noturno: metade do preço, e nada
  aqui é sensível a latência. Resultados voltam **fora de ordem** — chaveie por
  `custom_id`, nunca por posição.
- Toda linha gerada entra em `obs_avaliacoes` com `avaliador_tipo = 'modelo'` e o
  `modelo` preenchido. **A nota do modelo nunca sobrescreve a humana** — convivem, e a
  diferença entre elas é exatamente a métrica de qualidade.
- **Amostragem ativa:** mande para revisão humana só (a) onde o modelo tem baixa
  confiança, (b) onde dois modelos discordam, (c) uma fatia aleatória de controle ~10%
  para medir viés. Isso vale 5–10× em relação a sortear aleatoriamente.

**Sobre custo — a conclusão é que ele não importa nesta escala.** Ordem de grandeza, com
prefixo cacheado e Batch (50%):

| Volume | Transcrição (texto) | Clipe (16 quadros amostrados) |
| --- | --- | --- |
| ~800 avaliações/mês, Opus 5 | **~US$ 5–10/mês** | **~US$ 40–60/mês** |
| mesmo volume, Haiku 4.5 | ~US$ 1–2/mês | ~US$ 8–12/mês |

A diferença mensal entre o modelo mais forte e o mais barato é **menos que o custo de
uma hora de trabalho da equipe**. Então a decisão certa aqui é qualidade, não preço:
use o modelo mais capaz na rotulagem (`claude-opus-5`), e deixe o Haiku onde ele já está
bem — a indexação semântica, que é tarefa fácil e de volume maior. Se um dia o volume
crescer 100×, aí a conta muda e você reavalia com dado na mão.

**Detalhe prático que costuma pegar:** a API recebe **imagens, não arquivo de vídeo**.
"Rotular um clipe" significa amostrar N quadros (10–20 para 3 minutos) e mandar como
sequência de imagens. Vale testar a variante do stick figure descrita na análise —
renderizar esqueleto + caixas dos objetos em vez do quadro cru — mas só depois da etapa 6,
quando existir keypoint.

**Portão:** concordância modelo↔humano ≥ 0,7 × (o kappa humano↔humano medido na etapa 2).
Abaixo disso, o modelo entra só como sugestão e não conta como rótulo.

---

## Etapa 5 — Instrumentação do ambiente (meses 3–4)

**Objetivo:** métrica objetiva de ciclo de trabalho **sem nenhuma visão computacional.**

- **RFID na prateleira:** tag no material, antena por estante. Saída do campo =
  retirada; volta = devolução. Dá material, duração, sequência, **repetição** e
  **devolução** — os sinais Montessori mais fortes que existem, e nenhum deles precisa
  de câmera.
- **UWB para identidade e posição:** tag na sapatilha/avental, 3–4 âncoras por sala,
  ~10–30 cm. Resolve *quem* e *onde* de forma determinística. Também dá `adulto_proximo`
  — a base da dimensão autonomia — automaticamente.
- **Pareamento:** a prateleira diz *o quê e quando*; o UWB diz *quem estava lá*.

Comece por **uma estante e cinco crianças, por duas semanas**, antes de comprar escala.
Os dois testes que decidem: a tag sobrevive a criança de 3 anos? o leitor distingue
"retirou" de "passou perto"?

**Entregável:** eventos de material e presença gravados automaticamente.
**Bônus que paga a etapa 6:** isso vira **ground truth automático** — você mede a acurácia
do tracker de visão contra as tags, todo dia, sem rotular nada à mão.

---

## Etapa 6 — Visão computacional (meses 5–8)

Só agora. Antes disso ela não teria contra o que ser validada.

1. **Detecção + tracking** nas 2 salas principais (sala 1a3 e sala 3a6, que já têm 4 e 3
   câmeras). Detector com licença permissiva — **não Ultralytics/AGPL**, que colide com
   licenciar o produto depois.
2. **Pose** (RTMPose/MediaPipe, Apache-2.0), com fine-tune próprio em algumas centenas de
   quadros de criança pequena. Modelo de pose ajustado para 2–6 anos em ambiente
   Montessori **não existe pronto** — é ativo real.
3. **Modelo temporal sobre keypoints** (não sobre pixels): ~100× mais barato, robusto a
   luz e troca de câmera, e transfere para outra escola — que é o argumento de
   licenciamento.
4. **Armazenamento em duas camadas:** keypoints em Parquet particionado por dia/sala no
   Storage (lidos com DuckDB); só o **agregado por sessão** no Postgres. Keypoint cru em
   linha de Postgres seriam ~1,5 bilhão de linhas/ano — não faça.

**Avaliação, as quatro regras inegociáveis:** split por **criança E por dia** (nunca
aleatório, senão o modelo decora a camiseta); reporte contra o teto humano da etapa 2;
teste-reteste de graça usando duas câmeras da mesma sala no mesmo instante; regressão
contra o corpus dourado a cada versão.

**Portão:** score do modelo concorda com o humano dentro do teto, **e** a diferença entre
duas câmeras simultâneas é menor que o efeito que você quer detectar. Se o ruído entre
câmeras for do tamanho do efeito, o sistema não está medindo nada — e é melhor saber aqui
do que no mês 12.

---

## Etapa 7 — A camada longitudinal (mês 9+)

É aqui que vira medida, e é a única etapa que ninguém replica em um trimestre.

- **Modelo misto / traço latente:** efeito aleatório por criança (o que você quer medir),
  efeitos para material, sala, horário, professora, dia da semana e **idade** — que vocês
  já têm exata para os 47. Sem isso, a "curva de desenvolvimento" mede principalmente a
  agenda da escola.
- **Invariância:** toda versão nova repontua o corpus dourado; o delta é do modelo e sai
  da série histórica.
- **Saída pedagógica:** conecte em `registros_pedagogicos` e `planejamentos`, que já
  existem. O sistema não devolve um número — devolve *"a Ana repetiu o material X sete
  vezes em três dias e o ciclo dela dobrou desde maio"*, dentro do fluxo de trabalho que
  a equipe já usa.

---

## Etapa 8 — Licenciável

Só depois da 7. E note o que é o ativo, em ordem:

1. **O corpus rotulado** com metadado de confiabilidade — ninguém mais tem.
2. **O codebook validado** + a demonstração de que o score concorda com um instrumento
   aceito. É a diferença entre uma medida e um gadget.
3. **A receita de integração** (salas, tags, calibração, fine-tune de pose infantil).

O dashboard, o banco e o pipeline não são ativo — qualquer time bom refaz em um
trimestre.

---

## A primeira semana, concretamente

1. **Segunda:** escrever o codebook v1 — 3 dimensões × 5 níveis com âncora
   comportamental. Só texto. Ninguém toca em código.
2. **Terça:** rodar a migração (`obs_codebook`, `obs_avaliacoes`, `obs_golden`) e
   cadastrar o codebook v1.
3. **Quarta/quinta:** adicionar os sliders na tela de observação que já existe.
4. **Sexta:** as 3 especialistas avaliam juntas 10 entradas antigas, **em voz alta**,
   pra calibrar a leitura do codebook antes de começar o kappa cego.
5. **Semana seguinte:** rodar as ~100 entradas duplas.

Custo da primeira semana: **zero em hardware, zero em API.** E ao fim dela vocês sabem se
o construto se sustenta — que é a pergunta que decide o resto.

---

## O que NÃO fazer agora

| Não faça | Por quê | Quando reconsiderar |
| --- | --- | --- |
| Comprar câmera nova | Já tem 17 mapeadas | Se a etapa 6 mostrar ângulo ruim numa sala específica |
| Feature store (Feast) | Postgres + Parquet + DuckDB resolve nessa escala | N escolas com serving online |
| FastAPI + React | Supabase + as páginas que já rodam entregam igual, com uma stack a menos | Quando aparecer compute pesado de verdade |
| Treinar modelo de visão | Sem rótulo validado, treina-se ruído | Depois do portão da etapa 3 |
| Self-supervised próprio | 47 crianças nunca darão o volume | Use backbone pré-treinado congelado |
| Métrica de "tempo parado" | Inverte a pedagogia — vida prática é engajamento em movimento | Nunca |

---

## Riscos que continuam de pé

1. **O kappa pode não passar.** É o risco nº 1, e por isso ele está na semana 3 e não no
   mês 8. Custo de descobrir agora: uma semana. Custo de descobrir depois: o projeto.
2. **18 de 47 com autorização de imagem** limita o corpus de treino de visão. A escala
   humana cobre todos; o modelo de vídeo nasce com amostra pequena.
3. **Efeito menor que o ruído.** Se a diferença entre duas câmeras simultâneas for do
   tamanho da mudança que você quer detectar, nenhuma arquitetura salva. Só o
   teste-reteste da etapa 6 responde.
4. **A etapa 5 depende de hardware que ninguém testou** com criança de 3 anos. Piloto
   pequeno antes de comprar escala.
