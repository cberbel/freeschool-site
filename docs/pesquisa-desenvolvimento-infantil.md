# Projeto de mensuração longitudinal do desenvolvimento infantil

**Status:** rascunho de arquitetura · não implementado
**Contexto:** ambiente Montessori com 6 câmeras de alta resolução + áudio na mesma sala
**Objetivo:** construir infraestrutura de medida longitudinal do desenvolvimento infantil — não um "sistema de visão computacional na escola"

## O que é este documento

Três partes, com origens diferentes e propositalmente separadas:

| Parte | Conteúdo | Origem |
|---|---|---|
| **I** | Arquitetura, stack e o que analisar | sugestão recebida do GPT, reproduzida e organizada aqui |
| **II** | Sono como dimensão do projeto | acréscimo |
| **III** | Comentários críticos, riscos e ordem de execução | acréscimo |

A Parte I está preservada em conteúdo. As Partes II e III alteram algumas decisões dela
(ordem de construção, escopo do MVP, tratamento de áudio) — os pontos de divergência estão
explicitados na Parte III, não escondidos.

---

# Parte I — Arquitetura e stack

## Princípio central

A IA **não** deve produzir diretamente algo como `João: concentração = 82`.

Primeiro ela produz **fatos observáveis**; depois uma camada científica transforma esses
fatos em indicadores de desenvolvimento.

```
Câmeras + áudio → sincronização → tracking multicâmera → pose/mãos/objetos
→ fala → eventos comportamentais → métricas → trajetória longitudinal da criança
```

## Os três níveis de dado

Esta separação é decisiva para o valor científico do projeto.

| Nível | Exemplo | Quem produz |
|---|---|---|
| **1 — observação física** | mão direita tocou cubo às 10:32:17 | IA pode tornar extraordinariamente preciso |
| **2 — comportamento** | criança iniciou trabalho com Torre Rosa às 10:32 | IA pode automatizar boa parte |
| **3 — constructo psicológico/pedagógico** | concentração aumentou | exige validação científica humana |

Mantida essa separação desde o começo, o projeto deixa de ser apenas visão computacional
na escola e vira infraestrutura de mensuração longitudinal.

## 1. O núcleo: identificar e acompanhar cada criança

Com seis câmeras, começar por **NVIDIA DeepStream + CUDA + TensorRT**, em Linux com GPU NVIDIA.

DeepStream trabalha nativamente com múltiplos streams e inferência em GPU: recebe vários RTSP
simultâneos, faz batching, inferência e tracking.

Mais relevante: **Multi-View 3D Tracking (MV3DT)**. Com as seis câmeras calibradas para o mesmo
sistema de coordenadas, ele reconcilia o que a câmera 1 detectou com o que a câmera 4 detectou
e mantém um **ID global** para a pessoa, fundindo estimativas espaciais de câmeras diferentes.

Isso resolve o problema clássico da sala Montessori:

> criança entra atrás de outra → desaparece da câmera → aparece em outra câmera → continua sendo a mesma criança

O banco precisa registrar `child_017`, e **não** `camera1_person_8`, `camera3_person_12`,
`camera5_person_4`.

A NVIDIA fornece ferramenta de calibração multicâmera que calcula parâmetros
intrínsecos/extrínsecos e gera dados compatíveis com MV3DT.

## 2. Visão computacional

Não um modelo só — uma combinação.

| Função | Stack |
|---|---|
| detectar pessoas | YOLO / RTMDet |
| tracking 2D | ByteTrack / BoT-SORT |
| tracking entre câmeras | DeepStream MV3DT |
| pose corporal | RTMPose / MMPose |
| mãos/dedos | MediaPipe Hands + RTMPose Hand |
| corpo + mãos + rosto | MMPose WholeBody |
| objetos Montessori | YOLO customizado |
| ações temporais | modelo temporal PyTorch |
| coordenadas na sala | calibração multicâmera + homografia/3D |

Para pesquisa, MMPose/RTMPose é preferível porque permite trabalhar separadamente com corpo,
mão, face ou whole-body. Para mão, MediaPipe entrega **21 landmarks por mão**, incluindo ponta
e articulações de cada dedo.

Isso permite algo muito mais interessante do que saber onde a criança está. Por exemplo:

```
polegar → indicador → objeto → encaixe    (ao longo de 1,4 s)
```

## 3. Movimentação

Provavelmente a variável mais fácil de tornar excelente.

Calibrada a sala, transforma-se `pixel (2314, 876)` em `x = 4,82 m · y = 2,16 m`.

Para cada criança passa a existir uma trajetória `(x_t, y_t)`, e daí saem automaticamente:

distância percorrida por hora · velocidade · aceleração · tempo sentado · tempo em pé ·
deslocamentos sem objetivo aparente · permanência por área · número de mudanças de área ·
aproximação de adultos · aproximação de outras crianças · formação de grupos · isolamento ·
circulação pelo ambiente

E um **heatmap individual longitudinal**:

> Março: concentração espacial quase exclusiva em Vida Prática.
> Abril: passa a ocupar também Sensorial.
> Junho: grande aumento da permanência em Linguagem.

## 4. Concentração

Não treinar uma rede chamada `concentration_detector`. Construir um estado latente a partir
de comportamentos observáveis.

**Work episode.** A criança: aproxima-se de um material → pega → transporta → começa manipulação
→ permanece → mantém orientação corporal/visual compatível → não abandona → conclui → guarda.

Registra-se:

```
WORK_START 09:43:17
WORK_END   09:57:42
→ 14 min 25 s de trabalho contínuo
```

E dentro disso: 2 interrupções · 91% do tempo com orientação para o material · 34 manipulações ·
1 intervenção adulta · retorno espontâneo após interrupção · ciclo completo.

Concentração passa a ser estudada por:

- duração média dos episódios
- duração máxima
- interrupções/minuto
- probabilidade de retornar após interrupção
- proporção de ciclos concluídos

Cientificamente muito mais defensável.

## 5. Coordenação olho-mão / visuomotora

Combinar **head pose + gaze aproximado + mão + objeto**.

Ser conservador com eye tracking à distância: com câmeras ambientais estima-se bem a orientação
da cabeça, mas gaze ocular preciso é outra categoria de problema.

Ainda assim dá para detectar sequências como `olha objeto → estende mão → preensão → transporte
→ posicionamento`, e medir:

trajetória da mão · suavidade · velocidade · correções durante o movimento · erro de aproximação ·
número de tentativas · tempo até encaixe · coordenação bilateral · dominância manual ·
transferência mão direita ↔ esquerda · estabilidade da pinça

Com os 21 landmarks derivam-se abertura dos dedos, pinça polegar-indicador e configurações de
preensão. Marcador longitudinal típico:

> tempo médio para completar determinado movimento cai de 4,1 s para 2,2 s em quatro meses.

## 6. Destreza fina

Ponto fundamental: **ensinar a IA a reconhecer os materiais Montessori**. Não `object = toy`, mas:

```
pink_tower_cube_3 · cylinder_block_1 · metal_inset
movable_alphabet · pouring_jug · bead_chain_10
```

Exige dataset próprio. Anotação em **CVAT** ou **Label Studio**, treino de YOLO/RTMDet.

A combinação vira `criança + mão + objeto + sequência temporal`, o que permite diferenciar:

| | |
|---|---|
| pegou cilindro | pegou cilindro → testou encaixe → corrigiu → colocou corretamente |

A unidade de análise deixa de ser o frame e vira o **evento pedagógico**.

## 7. Linguagem

Pipeline separado. Não confiar no microfone das câmeras como única fonte — em sala cheia,
reverberação e fala sobreposta são brutais para ASR.

Idealmente: áudio ambiente + microfones nos adultos + eventualmente amostragem com microfone
individual em algumas crianças.

```
VAD → diarização → ASR → alinhamento temporal → NLP
```

Diarização: **NVIDIA NeMo (Sortformer)** e **pyannote.audio**.
ASR: **Whisper/WhisperX** como baseline + NeMo para comparar. NeMo fornece timestamps por
palavra, essencial para sincronizar fala e vídeo.

Resultado:

```
10:43:21.420  child_07:   "me dá aquele grande"
10:43:23.110  teacher_02: "qual deles?"
10:43:24.500  child_07:   "o cilindro grande"
```

**Quantidade:** palavras/hora · enunciados/hora · duração de fala · número de turnos.
**Complexidade:** MLU · tamanho do vocabulário · diversidade lexical · substantivos · verbos ·
adjetivos · conectivos · complexidade sintática.
**Interação:** turn-taking · tempo adulto→criança · tempo criança→adulto · turnos consecutivos ·
iniciações espontâneas · respostas · perguntas · expansões do adulto.

E talvez a mais interessante: **latência de resposta** entre a fala do adulto e a resposta infantil.

## 8. Linguagem + vídeo juntos

Aqui começa o projeto realmente diferenciado. Com o banco sabendo simultaneamente:

```
10:32:14  criança olhando uma folha
10:32:16  aponta para objeto
10:32:17  adulto diz "borboleta"
10:32:19  criança toca a imagem
10:32:21  criança diz "borboleta"
```

Não se está estudando apenas linguagem, e sim **atenção conjunta + gesto + input linguístico +
resposta + objeto referenciado**. Essa sincronização multimodal é provavelmente muito mais
valiosa cientificamente do que transcrever o dia inteiro.

## 9. Criatividade

Cautela. Não existe modelo confiável que olhe uma criança e diga `criatividade = 8,3`.
É preciso definir operacionalmente. Em tarefas abertas:

variedade de soluções · usos não previstos de materiais · combinação de elementos ·
transformação de uma construção · número de estratégias diferentes · exploração antes da solução ·
retorno e modificação de um trabalho

A IA identifica `estratégia A → estratégia B → estratégia C`; pesquisadores/educadores validam se
isso representa flexibilidade, fluência ou originalidade. **IA para descobrir e codificar
episódios, não para arbitrar criatividade.**

## 10. Arquitetura de dados

```
                 6 CAMERAS + AUDIO
                         │
             ┌───────────┴───────────┐
             │                       │
          RAW VIDEO               RAW AUDIO
             │                       │
          S3/MinIO                 S3/MinIO
             │                       │
             ▼                       ▼
        DEEPSTREAM              VAD / DIARIZATION
             │                       │
     Detection + Tracking          ASR
             │                       │
       Multi-camera ID              │
             │                       │
     ┌───────┼────────┐              │
     │       │        │              │
   Pose    Hands    Objects          │
     │       │        │              │
     └───────┼────────┘              │
             │                       │
             └──────────┬────────────┘
                        ▼
                  EVENT ENGINE
                        │
    ┌───────────────────┼─────────────────┐
    │                   │                 │
 movement          interaction        language
    │                   │                 │
 motor             engagement       turn-taking
    │                   │                 │
    └───────────────────┼─────────────────┘
                        ▼
                LONGITUDINAL STORE
                        │
                        ▼
               CHILD DEVELOPMENT
                   TIME SERIES
```

> Ver Parte II §5 para a **lane de sono**, que entra no Event Engine por fora do pipeline de vídeo.

## 11. Bancos de dados

Separar completamente vídeo bruto de dados científicos derivados.

**Vídeo** — S3 / MinIO:

```
2026/08/29/room_01/cam_01/ … cam_06/
```

**Eventos** — PostgreSQL: `child_id · timestamp · event · object_id · x · y · duration ·
confidence · camera_sources`

**Dados densos** (pose, trajetória) — Parquet + DuckDB. Não colocar coordenadas de
50 landmarks × 30 fps × 12 h × 20 crianças direto no PostgreSQL.

## 12. Não processar em resolução máxima o tempo inteiro

Guardar o original em alta resolução, mas não fazer todo detector trabalhar nela.

```
original → detector em resolução menor → crop da criança/mão → análise fina no crop original
```

Detecção global em 1920×1080 encontra a criança; busca-se no frame original uma região de
~1200×1200 da mão e passa-se isso ao detector de dedos. Economiza uma quantidade enorme de GPU
mantendo a informação fina onde ela importa.

## 13. Hardware

Para começar com uma sala de seis câmeras: workstation local.

Ubuntu · GPU NVIDIA de topo (classe RTX 5090 32 GB ou profissional equivalente) · 128 GB RAM ·
NVMe rápido para buffer · NAS para vídeo.

**Processamento offline/batch no início, não real-time.** Não é preciso descobrir concentração
às 10:42:03 — pode-se processar a madrugada anterior. Isso muda drasticamente o custo
computacional e permite experimentar modelos muito melhores.

## 14. Stack

**Infra** — Ubuntu · Docker · NVIDIA CUDA · TensorRT · DeepStream
**Computer Vision** — PyTorch · YOLO · MMPose/RTMPose · MediaPipe Hands · OpenCV
**Tracking** — ByteTrack · BoT-SORT · DeepStream MV3DT
**Áudio** — Whisper/WhisperX · NVIDIA NeMo · pyannote.audio
**NLP** — spaCy · Transformers · LLM para classificação de episódios, **nunca** como fonte
única da métrica
**Anotação** — CVAT
**Dados** — PostgreSQL · Parquet · DuckDB · S3/MinIO
**ML engineering** — MLflow · DVC · Git · Docker
**Dashboard** — Python/FastAPI · React · Plotly

> Versões específicas de DeepStream, YOLO e NeMo devem ser conferidas no momento da implementação —
> o campo se move rápido e a arquitetura importa mais do que o número da versão.

## 15. MVP: começar com poucos outputs

Não tentar construir tudo simultaneamente. Para cada criança:

1. **Trajetória espacial** — `x(t), y(t)`
2. **Atividade** — material atual · atividade atual · início · fim
3. **Social** — sozinho · criança-criança · criança-adulto · grupo
4. **Linguagem** — quem falou · quando · o quê · para quem
5. **Mãos** — mão esquerda · mão direita · objeto · tipo de manipulação
6. **Sono** — ver Parte II *(acrescentado; e, na prática, o primeiro a entrar em operação)*

Com esses sinais deriva-se uma quantidade enorme de indicadores posteriormente.

## 16. Privacidade por desenho

Por serem crianças, desenhar privacidade na arquitetura desde o início:

- vídeo bruto criptografado e com acesso muito restrito
- IDs pseudonimizados
- dataset analítico predominantemente composto por coordenadas/eventos/transcrições
- **evitar reconhecimento facial e inferência automática de "emoções"**

Assim, para a maior parte das análises, o pesquisador nem precisa abrir o vídeo original.

## 17. Ordem de construção proposta

```
tracking multicâmera → mapa espacial → materiais/atividade → pose e mãos
→ áudio/linguagem → fusão multimodal → métricas longitudinais
```

O primeiro produto tecnicamente funcional pode nascer nos três primeiros blocos. Criatividade e
constructos complexos ficam deliberadamente para depois da criação e validação dos protocolos de
anotação.

Vale estruturar depois um **data dictionary** com 50–100 variáveis mensuráveis, definindo
exatamente como a IA calcularia cada uma — o blueprint científico antes de treinar os modelos
mais específicos.

> A Parte III propõe uma ordem diferente, e o data dictionary **antes** e não depois. Ver §3 lá.

---

# Parte II — Sono

## Por que sono entra no projeto

Sono é, provavelmente, a variável **mais a montante** de tudo o que a Parte I quer medir.
Concentração, aprendizagem motora, vocabulário e regulação emocional são todos sensíveis a
duração, fragmentação e regularidade do sono.

A consequência prática é dura: **medir concentração sem medir sono é atribuir à pedagogia
variância que é do sono.** Se em maio os episódios de trabalho de uma criança encurtam, sem dado
de sono não há como distinguir "mudança no ambiente/material" de "a criança passou o mês dormindo
uma hora a menos". O sono não é mais uma métrica na lista — é a variável de controle sem a qual
as outras não se interpretam.

Há também um ganho positivo, não só de controle: o sistema da Parte I sabe **qual material** cada
criança praticou e **quando**. Isso torna testável, dentro da própria escola, a consolidação
motora dependente de sono — algo que normalmente exige laboratório.

## 1. O que medir

### A. Soneca na escola

Para a faixa etária que ainda dorme na escola:

| Variável | Definição |
|---|---|
| `nap_onset_latency` | do deitar até o início do sono |
| `nap_duration` | duração total |
| `nap_count` | número de sonecas no dia |
| `n_awakenings` | despertares durante a soneca |
| `movement_index` | movimento por época (proxy actigráfico) |
| `position_changes` | mudanças de posição |
| `settle_intervention` | houve intervenção adulta para adormecer |
| `post_nap_reentry_latency` | tempo entre acordar e retomar trabalho |

A última é interessante e só este projeto consegue medir: o sistema já sabe quando um work
episode começa, então a transição soneca → trabalho é observável de graça.

### B. Sono em casa

É a maior parte do sono e **não** pode ser medida por câmera — nem deve. Três fontes, em ordem
de custo:

**1. Diário de sono preenchido pela família** — padrão da área. Horário de deitar, latência
estimada, despertares, horário de acordar. Custa ~30 s/dia por família e nenhuma GPU.

**2. Instrumentos validados**, aplicados em ondas (ex.: trimestral):
- **BISQ / BISQ-R** — *Brief Infant Sleep Questionnaire*, crianças menores
- **CSHQ** — *Children's Sleep Habits Questionnaire*, ~4–10 anos
- **SDSC** — *Sleep Disturbance Scale for Children*

> Conferir na implementação quais têm versão validada em PT-BR e sob quais condições de uso.

**3. Actigrafia de pulso** — padrão de pesquisa abaixo da polissonografia. Não precisa ser
contínua: 7–14 noites consecutivas por criança, em 3–4 ondas por ano, já dá excelente estimativa
de duração, eficiência e **regularidade**. Classificação sono/vigília por algoritmo validado para
crianças (Sadeh; Cole-Kripke como alternativa).

Wearables de consumo são mais baratos, porém pouco validados nessa faixa etária — servem para
tendência, não para o dado primário.

### C. Constructos derivados

O que de fato entra nos modelos:

- `total_sleep_24h` — soneca escolar + noite
- `sleep_efficiency` — tempo dormindo / tempo na cama
- `sleep_onset_latency`
- `waso` — *wake after sleep onset*
- `sleep_midpoint` — proxy de cronotipo
- `sleep_regularity_index` — regularidade dia a dia (Phillips et al., 2017)
- `weekend_shift` — deslocamento fim de semana × dias letivos
- `nap_dependency` — ainda depende de soneca; a **transição de abandono da soneca** é ela própria
  um marco de desenvolvimento e deve ser datada por criança

**Regularidade merece destaque.** Em boa parte da literatura, a *variabilidade* do horário de sono
prediz desfechos tão bem ou melhor do que a duração média — e é justamente o que um diário diário
captura bem e uma medida pontual não captura de jeito nenhum.

Faixas de referência para comparação (consenso AASM): 10–13 h/24 h para 3–5 anos, incluindo
sonecas; 9–12 h para 6–12 anos. Servem de referência descritiva, não de critério clínico.

## 2. A análise que justifica o esforço

O ganho real não é ter uma coluna "horas de sono" no dashboard. É o acoplamento:

```
sono(noite n) → métricas(dia n+1)
```

Como o sistema já produz métricas por criança e por dia, o sono vira **preditor intra-sujeito**.
Modelos de efeitos fixos por criança: cada criança é seu próprio controle. Isso elimina de saída
a maior parte dos confundidores que arruínam correlação entre crianças — nível socioeconômico,
temperamento, ambiente familiar, personalidade.

Hipóteses que valem ser **pré-registradas** antes de olhar os dados:

**H1 — concentração.** Noite mais curta ou mais fragmentada → menor duração média dos work
episodes, mais interrupções e menor probabilidade de retorno após interrupção no dia seguinte.

**H2 — consolidação motora.** Ganho de desempenho em um material praticado no dia *n* medido no
dia *n+1* é maior após noites mais longas/eficientes. Testável porque o sistema registra tempo de
conclusão do **mesmo material** ao longo do tempo. Esta é a hipótese mais forte do conjunto e a
mais difícil de obter fora de laboratório.

**H3 — linguagem.** Regularidade do sono → volume e complexidade da produção verbal.

**H4 — soneca intradia.** Soneca no dia *n* → concentração na tarde do dia *n*, comparada com dias
sem soneca na mesma criança.

**H5 — transição da soneca.** O período em torno do abandono da soneca é de instabilidade
comportamental — visível como queda temporária na duração dos episódios de trabalho, seguida de
recuperação.

## 3. Como instrumentar a soneca sem ser invasivo

**Vídeo de criança dormindo é o dado mais sensível do projeto inteiro.** Opções em ordem crescente
de proteção:

| Opção | O que dá | Observação |
|---|---|---|
| Câmeras existentes, vídeo descartado | movimento, posição | processar na borda, guardar só o sinal derivado; retenção curta |
| Câmera de profundidade / térmica | movimento, posição | sem imagem identificável |
| **Radar mmWave (60 GHz)** | presença, movimento, frequência respiratória | **sem imagem nenhuma** |
| Sensor sob o colchonete (balistocardiografia) | movimento, FC, respiração, estágios | sem contato, sem imagem; viável em colchonetes/catres |

**Recomendação:** radar ou sensor sob o colchonete. Dão sinal melhor que o vídeo para sono
(respiração é discriminativa e a câmera não pega bem sob cobertor) e removem por completo o
problema ético mais espinhoso do projeto. É um caso raro em que a opção mais privada é também a
tecnicamente superior.

Consentimento para monitoramento de sono deve ser **separado e granular**, não embutido no
consentimento de vídeo da sala.

## 4. Extração de sinal a partir de vídeo (se for usado)

- **Actigrafia por vídeo:** diferença de frames / fluxo óptico dentro da bounding box da criança →
  índice de movimento por época. Usar épocas de 30 s ou 60 s, para casar com o padrão da
  actigrafia e permitir aplicar algoritmos já validados (Sadeh).
- **Não usar pose/esqueleto durante a soneca.** Sob cobertor, o estimador de pose falha e produz
  ruído com aparência de sinal. Usar energia de movimento, não landmarks.
- Respiração por vídeo é possível, mas frágil. Radar resolve melhor.

## 5. Onde o sono entra na arquitetura

Sono é uma **lane paralela**, que não passa pelo pipeline de vídeo do DeepStream e desemboca
direto no Event Engine:

```
   SONECA ESCOLAR                    SONO EM CASA
 radar / sensor de colchonete    diário família · actigrafia · questionários
   (ou vídeo → actigrafia)                    │
             │                                │
             ▼                                ▼
      SLEEP EPISODES  ◄───────────────────────┘
             │
             ▼
      SLEEP DAILY  (agregação 24 h + regularidade)
             │
             ▼
       EVENT ENGINE ──► LONGITUDINAL STORE
                             │
                    junção sono(n) × métricas(n+1)
```

## 6. Modelo de dados

```sql
-- episódio bruto de sono
sleep_episode (
  child_id, date, type, source,
  start_ts, end_ts,
  onset_latency_s, waso_s, n_awakenings,
  movement_index, efficiency, confidence
)
-- type   : nap_school | night_home
-- source : radar | mat_sensor | video_actigraphy | wearable | parent_diary

-- agregação diária, o que entra nos modelos
sleep_daily (
  child_id, sleep_day,
  total_sleep_24h_min, night_sleep_min, nap_min, nap_flag,
  midpoint, onset_latency_s, efficiency,
  regularity_index_7d, weekend_shift_min,
  source_quality, is_imputed
)
```

**Convenção de "dia de sono", definir e documentar antes de coletar:** a noite de terça para
quarta é atribuída à **quarta-feira**, o dia letivo que ela precede. Sem essa convenção fixada por
escrito, metade das análises sai deslocada em um dia — e é um erro que só aparece depois de meses
de coleta.

`is_imputed` e `source_quality` não são opcionais: diário de família tem faltas, e um modelo que
trata dado ausente como zero produz resultado invertido.

## 7. Confundidores a registrar

Sem estes campos, os modelos de sono não se sustentam:

doença · medicação (**uso de melatonina é comum e precisa ser registrado**) · tempo de tela ·
eventos familiares (mudança, nascimento de irmão, separação) · estação/luz natural ·
**idade** (a transição da soneca ocorre por volta dos 3–5 anos e cria forte efeito de coorte) ·
dia da semana (segunda-feira carrega o deslocamento do fim de semana)

## 8. Por que o sono deve começar antes de tudo

O diário de sono é o dado de **melhor razão valor/custo do projeto inteiro**:

- custa um formulário e ~30 s por dia por família
- não depende de GPU, calibração, dataset anotado ou modelo treinado
- pode começar **na semana que vem**, não daqui a um ano
- acumula série temporal longitudinal enquanto a stack de visão está sendo construída
- é a variável que pode **invalidar** qualquer conclusão das outras se estiver ausente

Quando o pipeline de visão finalmente produzir métricas confiáveis de concentração — o que
realisticamente leva de 6 a 12 meses — já existirá um ano de sono para cruzar com elas. Sem isso,
o relógio das análises longitudinais só começa a correr no dia em que a última peça da IA ficar
pronta.

**Nenhuma outra parte deste projeto tem essa propriedade.**

---

# Parte III — Comentários, riscos e ordem de execução

Comentários sobre a Parte I. Onde há divergência, ela está marcada como **divergência**.

## 1. O que a proposta acerta

Vale registrar, porque são decisões que a maioria dos projetos parecidos erra:

- **A separação em três níveis** (observação física / comportamento / constructo) é a melhor ideia
  do documento. É ela que separa este projeto de um sistema de vigilância com dashboard.
- **Não treinar um `concentration_detector`.** Correto. Concentração não é um objeto que uma rede
  detecta; é uma inferência sobre uma sequência de comportamentos.
- **Work episode como unidade de análise.** Além de tecnicamente sólido, casa com a teoria
  Montessori — o ciclo de trabalho é um conceito da própria Montessori, não uma invenção do
  projeto. Isso importa para publicar.
- **Batch em vez de tempo real.** Corta custo de GPU em uma ordem de grandeza e libera modelos
  melhores. Correto.
- **Crop em alta resolução depois de detecção em baixa.** Correto.
- **Separar vídeo bruto de dado científico derivado.** Correto, e é o que torna a maior parte das
  análises possível sem ninguém reabrir vídeo de criança.
- **Cautela com criatividade e recusa de inferência automática de emoções.** Correto, e por razões
  éticas além das técnicas.

O resto desta parte é sobre o que falta.

## 2. O gargalo real não são os modelos — é anotação e validação

Este é o ponto mais importante da minha leitura.

A Parte I é uma lista de componentes técnicos, e todos eles são obteníveis. O que ela subestima é
que **cada métrica precisa de ground truth humano**. Alguém precisa assistir a dezenas de horas de
vídeo e codificar manualmente o que é um work episode, quando começa, quando termina, o que conta
como interrupção. Sem isso não existe como afirmar que o detector automático funciona — e uma
métrica não validada não é dado, é opinião com carimbo de número.

Isso implica, concretamente:

- **Protocolo de codificação escrito**, com regras de decisão para os casos ambíguos (a criança
  olhou para o lado por 4 s — interrompeu o trabalho ou não?).
- **Dois ou mais codificadores humanos independentes** e medida de concordância entre eles
  (kappa de Cohen para categorias, ICC para variáveis contínuas). Se dois humanos treinados não
  concordam sobre o que é um work episode, nenhuma IA vai resolver isso — a definição é que está
  ruim.
- Só depois: treinar o detector automático para **reproduzir a codificação humana**, e reportar a
  concordância IA × humano como se reporta humano × humano.

Custa tipicamente 2–3× mais do que se estima. É o principal centro de custo do projeto e não
aparece na Parte I.

## 3. **Divergência:** o data dictionary vem antes, não depois

A Parte I coloca o dicionário de variáveis no fim ("vale estruturar depois"). Eu inverteria.

O dicionário e o protocolo de codificação **definem o que está sendo construído**. Sem eles,
constroem-se detectores para coisas que depois se revelam a unidade de análise errada — e aí se
joga fora meses de engenharia porque a definição de "interrupção" mudou.

Ordem que eu seguiria:

```
1. dicionário de variáveis (50–100)     ─┐
2. protocolo de codificação humana       ├─ nenhum destes precisa de GPU
3. humanos codificam 1 semana de vídeo   │
4. concordância entre codificadores      ─┘
5. só então: construir a automação que reproduz (3)
```

Bônus: o passo 3 produz **de graça** o conjunto de validação do passo 5.

## 4. Risco nº 1 à validade: troca de identidade

Rastrear entre câmeras crianças pequenas, parecidas entre si, que se movem rápido, se ocluem o
tempo todo, usam avental igual e entram embaixo da mesa é **substancialmente mais difícil** do que
o caso de adultos para o qual esses sistemas foram desenhados. Re-identificação por aparência
funciona mal quando a aparência é uniforme por desenho.

E o erro é traiçoeiro: **um único ID switch contamina toda a série longitudinal das duas crianças
envolvidas.** Não degrada suavemente — corrompe.

Duas mitigações, e eu faria as duas:

**(a) Ferramenta de revisão de tracks com humano no circuito.** Uma UI onde alguém percorre o dia
processado e corrige trocas de ID. Não é um extra: é infraestrutura obrigatória, e precisa estar
no plano desde o começo. Sem ela, toda métrica por criança herda o erro de identidade.

**(b) Considerar identificação passiva.** Etiquetas BLE ou UWB no avental resolvem identidade e
posição aproximada por fora da visão computacional, deixando o vídeo cuidar do comportamento fino
— que é onde ele é insubstituível. UWB dá dezenas de centímetros de precisão. É bem mais barato e
mais confiável do que resolver re-ID infantil entre seis câmeras.

Contras honestos de (b): crianças tiram; é mais um item de consentimento; e tem carga simbólica
maior ("etiquetar criança") mesmo sendo, do ponto de vista de dado, menos invasivo que a câmera.
Vale a discussão com as famílias, não a decisão de bastidor.

## 5. Áudio: a Parte I é otimista demais

Duas dificuldades somadas, e a proposta trata só da primeira.

**Diarização** em sala com ~20 crianças de vozes acusticamente parecidas, fala sobreposta e
reverberação está no limite de falha do estado da arte. A Parte I reconhece isso.

**ASR infantil** é o problema que a Parte I não menciona. Reconhecimento de fala de criança
pequena é muito pior do que de adulto — as taxas de erro costumam ser altas o bastante para que
métricas lexicais fiquem sem sentido, e em PT-BR há menos dado de treino ainda. **MLU calculado
sobre transcrição com 50% de erro não é uma medida de linguagem — é ruído com casas decimais.**

Isso não invalida o pipeline; muda o que se pode afirmar com ele:

| Medida | Viável? |
|---|---|
| duração de fala, número de turnos, contagem de vocalizações, latência de resposta | sim — dependem de detecção acústica, não de reconhecer palavras |
| quem falou com quem, iniciação × resposta | sim, com diarização decente |
| MLU, diversidade lexical, complexidade sintática, classes gramaticais | **não**, até que a WER seja medida no áudio real desta sala |

**Referência que falta na Parte I: LENA** (*Language ENvironment Analysis*) — gravador vestível
mais software, usado em centenas de estudos de ambiente linguístico infantil, que entrega
exatamente a tríade contagem de palavras do adulto / vocalizações da criança / turnos
conversacionais, **sem transcrever**. É o ponto de comparação estabelecido nesta área. Caro por
dispositivo, e muito mais barato do que construir o equivalente. Vale conferir o estado da
validação em PT-BR antes de adotar.

**Recomendação:** começar pelas medidas de quantidade e interação, que são robustas; tratar as
medidas lexicais/sintáticas como uma segunda fase condicionada a medir a WER no áudio real —
com uma amostra transcrita à mão como referência.

## 6. Jurídico e ético: a frente que pode matar o projeto

É a única parte capaz de inutilizar todo o dataset depois de coletado. Precisa correr **em
paralelo desde o mês 1**, não depois que a tecnologia funcionar.

**LGPD (Lei 13.709/2018).** Dado de criança tem proteção específica: o art. 14 exige
**consentimento específico e em destaque** de ao menos um dos pais ou responsável, e sujeita todo
o tratamento ao melhor interesse da criança. Além disso, boa parte do que o projeto coleta é
**dado pessoal sensível** pelo art. 5º, II — biometria (pose, marcha, face, voz) e dado de saúde
(**o dado de sono cai aqui**). Implica:

- **RIPD** (Relatório de Impacto à Proteção de Dados Pessoais)
- consentimento **granular e revogável** por família e por tipo de dado — vídeo / áudio / sono /
  wearable separadamente, nunca em bloco
- **encarregado** (DPO) nomeado
- política de retenção escrita **antes** da primeira gravação

**Ética em pesquisa.** Se a intenção é publicar, aprovação em **CEP/CONEP** é obrigatória no
Brasil (Res. CNS 466/2012 e 510/2016) e exigida pelos periódicos. Inclui TCLE dos responsáveis e
**TALE — assentimento da própria criança**, na medida do desenvolvimento dela. Não é formalidade:
submeter depois de coletar costuma significar não poder usar o que já foi coletado.

**Funcionários.** As educadoras estão sendo gravadas continuamente, e a Parte I não trata disso.
É questão trabalhista e de direito de imagem, exige consentimento próprio, e é fonte real de
atrito com a equipe. Um sistema que conta "intervenções adultas" por educadora é, do ponto de
vista delas, avaliação de desempenho — mesmo que o projeto jure que não é. Precisa ser negociado
abertamente, com regra escrita sobre quem pode ver dado individualizado de adulto. Melhor decidir
isso antes, e não na primeira vez que alguém pedir o relatório.

## 7. Efeito do observador

Crianças e adultos se comportam diferente sabendo que estão sendo gravados. Há habituação, mas
ela precisa ser **medida**, não presumida: comparar semana 1 × semana 4 × semana 12 das mesmas
métricas e verificar se estabilizam.

O caso mais perverso: uma educadora que sabe que "intervenções adultas" estão sendo contadas
intervém menos. Aí não se está medindo a sala — está-se medindo a medição. As primeiras semanas
provavelmente devem ser descartadas das análises por protocolo, e isso fica decidido de antemão.

## 8. Estatística: o jardim de caminhos que se bifurcam

Um sistema que produz milhares de variáveis por criança por dia produz, por construção, resultados
"significativos" em qualquer direção que se procure. Com testes suficientes, tudo correlaciona
com tudo em algum recorte.

Contramedidas, todas baratas se adotadas desde o início e impossíveis depois:

- **Pré-registro** das hipóteses (OSF) antes de olhar os dados — as H1–H5 da Parte II são um bom
  primeiro conjunto
- separação explícita entre análise **confirmatória** (pré-registrada) e **exploratória**
  (permitida, mas rotulada como tal e não vendida como achado)
- correção para comparações múltiplas
- *holdout* temporal: reservar meses inteiros que ninguém olha até o modelo estar fechado

## 9. O que este projeto é — e o que não é

Uma sala ≈ 20 crianças, sem grupo de controle, em uma escola. Isso significa:

**Não é** um estudo de eficácia. Não sustenta "a Free School / o método Montessori funciona".
Qualquer afirmação causal comparativa está fora do alcance deste desenho, e tentar fazê-la é o
caminho mais rápido para queimar a credibilidade do resto.

**É** — e isso é genuinamente valioso — um **estudo longitudinal intensivo de medida**. Séries
temporais densas, diárias, in situ, de comportamento infantil real, com cada criança como seu
próprio controle, ao longo de anos. Esse tipo de dado quase não existe na literatura: o padrão da
área é medida esparsa (algumas avaliações por ano, em laboratório, fora do contexto).

Vale ser explícito sobre esse enquadramento desde o começo, inclusive com as famílias.

## 10. O custo esquecido: armazenamento

Estimativa de ordem de grandeza — 6 câmeras, 4K, H.265, ~15 Mbps cada, 10 h/dia:

```
15 Mbps × 6 = 90 Mbps ≈ 11,25 MB/s
× 36.000 s/dia          ≈  405 GB/dia
× 20 dias letivos/mês   ≈  8,1 TB/mês
× 200 dias/ano          ≈   81 TB/ano
```

Em resolução muito mais alta, multiplique por vários. Ou seja: **guardar vídeo bruto para sempre
não é uma opção** — nem financeira, nem jurídica (a LGPD pede necessidade e prazo definido).

Política de retenção a definir antes da primeira gravação, algo como: bruto por 30–90 dias →
depois só dado derivado + clipes curtos anotados que fundamentam validação. Isso é
simultaneamente economia e conformidade, e é bem mais fácil de decidir agora do que quando já
existirem 40 TB e alguém tiver medo de apagar.

## 11. Criatividade: cortar do roadmap

Concordo com a cautela da Parte I e iria além: **remover criatividade dos dois primeiros anos** e
não prometê-la a ninguém. O mesmo para qualquer coisa perto de emoção, engajamento afetivo ou
bem-estar inferido automaticamente.

Não por ser impossível, mas porque a chance de produzir um número que parece medir algo e não mede
é altíssima — e um número desses, uma vez que entra num relatório para família, é praticamente
impossível de retirar depois.

## 12. A força real do projeto

Se houvesse uma única recomendação a levar deste documento:

> **Priorizar continuidade e consistência de poucas medidas bem validadas, em vez de amplitude de
> muitas medidas frágeis.**

Três anos ininterruptos de duração de work episode + sono + contagem de turnos conversacionais,
com definição estável e validação humana, valem cientificamente mais do que 100 variáveis ruidosas
por 6 meses. E — isso é o mais fácil de esquecer — uma série longitudinal **quebra se a definição
da variável mudar no meio**. Toda mudança de definição zera o histórico comparável.

Isso é um argumento forte para congelar cedo um núcleo pequeno de variáveis, versioná-las como se
versiona código, e só então expandir por fora.

## 13. Ordem de execução recomendada

**Divergência** em relação à §17 da Parte I: aquela ordem é a ordem de dependência *técnica*.
Esta é a ordem de dependência *do valor científico*, e as duas não coincidem.

| Fase | Frente | Entregas |
|---|---|---|
| **Mês 0** *(sem GPU)* | fundação | trilha jurídica/ética iniciada · consentimentos desenhados · **diário de sono começa a rodar** · dicionário de variáveis v1 · protocolo de codificação humana |
| **Mês 1–3** | captura | câmeras instaladas · calibração · pipeline de gravação e armazenamento com retenção definida · humanos codificam 1 semana · concordância entre codificadores |
| **Mês 3–6** | identidade e espaço | tracking · identidade (com etiquetas, se aceitas) · mapa espacial · **UI de revisão de tracks** · trajetória automática validada contra codificação humana |
| **Mês 6–12** | atividade | dataset de materiais Montessori · detecção de material · work episodes automáticos · **primeiro cruzamento sono × concentração** |
| **Ano 2** | motor e linguagem | pose e mãos · áudio começando por quantidade/turnos · fusão multimodal |
| **Ano 3+** | — | constructos complexos, se e quando os protocolos sustentarem |

As duas coisas que custam quase nada e destravam todo o resto — **o diário de sono** e **o
protocolo de codificação humana** — são as duas que estão no mês 0. Não é coincidência: são as
únicas que não dependem de nenhuma outra peça, e ambas acumulam valor enquanto a engenharia
acontece.

---

## Anexo — Dicionário de variáveis (semente)

Ponto de partida para o dicionário de 50–100 variáveis. Cada uma precisa, antes de ser
implementada: definição operacional, unidade, fonte, regra de valor ausente e método de validação.

| Variável | Nível | Fonte | Definição operacional | Validação |
|---|---|---|---|---|
| `work_episode_duration` | 2 | vídeo | do início da manipulação ao abandono/guarda | humano × IA (ICC) |
| `work_episode_interruptions` | 2 | vídeo | eventos de desengajamento > limiar T durante o episódio | humano × IA (kappa) |
| `return_after_interruption` | 2 | vídeo | retomou o mesmo material em até T s | humano × IA |
| `completed_cycle_ratio` | 2 | vídeo | episódios que terminam em "guardar" / total | humano × IA |
| `distance_travelled_h` | 1 | trajetória | integral de `(x,y)` por hora | geométrica |
| `area_dwell_time` | 1 | trajetória | tempo por área pedagógica da sala | geométrica |
| `area_transitions` | 1 | trajetória | mudanças de área por hora | geométrica |
| `proximity_child` / `proximity_adult` | 1 | trajetória | tempo a menos de D m de outra pessoa | geométrica |
| `pincer_stability` | 1 | mãos | distância polegar-indicador durante preensão | humano × IA |
| `time_to_fit` | 2 | mãos + objeto | do primeiro contato ao encaixe correto | humano × IA |
| `hand_dominance` | 2 | mãos | razão de manipulações direita/esquerda | humano × IA |
| `speech_duration` | 1 | áudio | tempo de fala atribuído à criança | humano × IA (WER-independente) |
| `conversational_turns` | 2 | áudio | trocas alternadas dentro de janela T | humano × IA |
| `response_latency` | 2 | áudio | do fim da fala do adulto ao início da resposta | humano × IA |
| `mlu` | 2 | áudio | *bloqueada até WER medida no áudio real* | — |
| `total_sleep_24h` | 1 | sono | soneca + noite, dia de sono definido na Parte II §6 | actigrafia × diário |
| `sleep_regularity_index` | 2 | sono | regularidade dia a dia, janela de 7 dias | actigrafia |
| `nap_onset_latency` | 1 | sono | do deitar ao início do sono | radar × observação |
| `post_nap_reentry_latency` | 2 | sono + vídeo | do despertar ao próximo work episode | humano × IA |
| `nap_dependency` | 2 | sono | proporção de dias com soneca, janela móvel | diário |

Nível 3 (concentração, coordenação, destreza, criatividade) **não entra no dicionário como
variável medida** — entra como constructo derivado, com o conjunto de variáveis de nível 1 e 2 que
o compõem declarado explicitamente e validado à parte.
