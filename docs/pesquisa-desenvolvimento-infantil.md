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
| **IV** | Revisão: lacunas, bancada de testes (Fase 0) e conjunto inicial de variáveis | acréscimo |

O dicionário de variáveis completo (~135 variáveis) vive em arquivo próprio:
[`dicionario-variaveis.md`](dicionario-variaveis.md).

A Parte I está preservada em conteúdo. As Partes II e III alteram algumas decisões dela
(ordem de construção, escopo do MVP, tratamento de áudio) — os pontos de divergência estão
explicitados na Parte III, não escondidos.

## Regras do projeto

Decisões tomadas, não propostas em aberto. O restante do documento se subordina a elas — onde
uma análise anterior contrariava alguma, a análise foi revista, não a regra.

### R1 — Observar amplo, reportar estreito

Um conjunto **grande** de variáveis é observado e armazenado por trás da cena desde o início.
O que é **reportado** começa pequeno e cresce conforme cada indicador passa por validação.

São dois conjuntos distintos e a confusão entre eles é o erro a evitar — não a amplitude da
observação. Reduzir o que se observa hoje é jogar fora dado que não volta; reduzir o que se
reporta hoje custa nada e se reverte a qualquer momento.

### R2 — Emocional e criatividade entram desde o início

Não são temas adiados para o ano 3. **Criatividade é objetivo fundamental do projeto** — é o
constructo mais alinhado à tese pedagógica da escola, e adiá-lo esvaziaria a razão de existir da
medição. Emocional entra junto, pelo mesmo motivo e porque é o principal mediador entre sono e
todo o resto.

O que se observa e guarda é o **substrato** (nível 1 e 2): prosódia, unidades de ação facial,
episódios de distress e tempo de recuperação, uso não-canônico de material, sequências de
estratégia, raridade de ação. O que **não** se produz é rótulo automático de nível 3 —
`criatividade = 8,3`, `a criança está triste`. Ver Parte III §11 para a operacionalização.

### R3 — Armazenar a gravação bruta: 11 h/dia, 5×/semana, nos primeiros 2 anos

Sem descarte por janela curta. A retenção é reavaliada ao fim do período, com conhecimento que
hoje não existe. Ver Parte III §10 para volume, custo e o desenho jurídico que isso exige.

### R4 — Captura é irreversível; extração é repetível

Corolário técnico de R1 e R3, e o critério que decide o que tem pressa:

- **Captura** — câmeras, áudio, sensores de sono, etiquetas, log de contexto, consentimento.
  Não capturou, perdeu para sempre. **Tem pressa. Vai tudo para a fase 1.**
- **Extração** — pose, mãos, objetos, episódios, métricas. Pode ser refeita sobre o arquivo
  quantas vezes o método melhorar. **Não tem pressa. Fazer bem depois > fazer mal agora.**

Toda tabela derivada carrega `pipeline_version`, `model_version` e `definition_version`, e o
histórico é **reprocessado por inteiro** a cada mudança de método — é o que mantém a série
longitudinal comparável enquanto os modelos evoluem.

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

> **A estratégia de compor muitos modelos estreitos está certa** — ver Parte III §14 para por quê,
> e para as três ressalvas que decidem se funciona: sincronização, propagação de erro e ordem de
> entrada dos módulos. Esta tabela é **arquitetura-alvo, não configuração inicial**.

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

> Todas as métricas de interação acima dependem de **atribuição correta de falante**, que numa
> sala de 20 crianças é o elo fraco do pipeline inteiro. Ver Parte III §5 — inclusive por que
> LENA não serve de referência aqui, e como o mapa espacial do sistema de visão pode ancorar a
> atribuição.

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

> **R2 eleva criatividade a objetivo fundamental**, não a tema adiado. A Parte III §11
> operacionaliza as dimensões de Torrance sobre este sistema — incluindo originalidade como
> raridade estatística no corpus da própria sala, e difusão social de invenção entre crianças.

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
7. **Substrato emocional** — prosódia · AUs · episódios de distress · tempo de recuperação ·
   persistência após falha *(acrescentado por R2)*
8. **Substrato de criatividade** — uso não-canônico · combinação de materiais · sequência de
   estratégias · raridade de ação *(acrescentado por R2)*

Com esses sinais deriva-se uma quantidade enorme de indicadores posteriormente.

> **Atenção à leitura desta lista sob R1.** "Começar com poucos outputs" vale para o que é
> **reportado**, não para o que é **observado e guardado** — este último é o mais amplo que a
> captação permitir, desde o dia 1. Confundir as duas coisas descarta dado que não volta.

## 16. Privacidade por desenho

Por serem crianças, desenhar privacidade na arquitetura desde o início:

- vídeo bruto criptografado e com acesso muito restrito
- IDs pseudonimizados
- dataset analítico predominantemente composto por coordenadas/eventos/transcrições
- **evitar reconhecimento facial**
- **não produzir rótulo automático de emoção** (`face → "triste"`) — o que se guarda é o
  substrato físico: unidades de ação facial, prosódia, episódios de distress e tempo de
  recuperação. Ver R2 e Parte III §11: a restrição é sobre o **rótulo de nível 3**, não sobre a
  observação

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

**H6 — regulação emocional** *(entra por R2)*. Noite mais curta ou mais fragmentada → mais
episódios de distress, **tempo de recuperação mais longo** e menor persistência após falha no dia
seguinte. A ligação sono → reatividade emocional é das mais replicadas da literatura de sono
infantil, e o tempo de recuperação é justamente a variável emocional mais defensável deste
sistema (Parte III §11). Provavelmente a hipótese com maior chance de sinal limpo do conjunto.

**H7 — criatividade** *(entra por R2)*. Sono adequado → mais uso não-canônico de material e mais
sequências de estratégia distintas. Hipótese mais especulativa que as anteriores, e só testável
depois que o corpus permitir calcular raridade — mas o substrato precisa estar sendo gravado
desde já, ou o teste nunca fica disponível.

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
- **Recusa de rótulo automático de emoção.** Correto quanto ao rótulo — mas a Parte I generaliza
  demais e acaba excluindo também a *observação* do substrato. R2 corrige: observa-se amplo,
  não se rotula. Ver §11.

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

Três dificuldades somadas, e a proposta trata só da primeira.

**Diarização** em sala com ~20 crianças de vozes acusticamente parecidas, fala sobreposta e
reverberação está no limite de falha do estado da arte. A Parte I reconhece isso.

**ASR infantil** é o problema que a Parte I não menciona. Reconhecimento de fala de criança
pequena é muito pior do que de adulto, e em PT-BR há menos dado de treino ainda. **MLU calculado
sobre transcrição com metade das palavras erradas não é uma medida de linguagem — é ruído com
casas decimais.**

**A forma da sala** é a terceira, e é a que reenquadra as outras duas. Praticamente toda a
literatura de ambiente linguístico infantil foi construída sobre gravação *centrada em uma
criança*, em casa, com poucos falantes por perto. Uma sala Montessori com 20 crianças é um
problema estruturalmente diferente: não é o mesmo problema com mais ruído, é outro problema.

### Por que LENA não serve de referência aqui

Vale registrar explicitamente, porque LENA é a sugestão óbvia e vai reaparecer:

- os modelos são **proprietários, fechados e treinados sobre inglês norte-americano** de um
  corpus antigo, sem atualização substancial por muitos anos — não dá para inspecionar,
  corrigir nem readaptar para PT-BR
- a validação **degrada fora do inglês** e fora do contexto doméstico
- entre as três métricas, contagem de palavras do adulto é a menos ruim; **vocalizações da
  criança e turnos conversacionais validam pior**
- o pressuposto de projeto é **uma criança-alvo com poucos falantes ao redor**. Com 20 crianças
  na mesma sala, fala de criança vizinha é atribuída à criança-alvo, e é exatamente esse o erro
  dominante aqui

Ou seja: a métrica que mais interessaria (turnos) é a que quebra primeiro, e quebra pelo motivo
que esta sala tem de sobra. **Não adotar, nem como baseline de comparação.**

Isso obriga a uma correção na direção mais conservadora: **contagem de turnos não é uma medida
robusta neste ambiente**, ao contrário do que a tabela anterior deste documento sugeria. Ela
depende de atribuição correta de falante, que é justamente o elo fraco.

### O que usar no lugar

**Modelos abertos, porque podem ser ajustados com o áudio desta sala** — que é a propriedade
decisiva, mais até do que a acurácia de partida:

- **VTC** (*Voice Type Classifier*) — classificação de tipo de falante (criança-alvo / outra
  criança / adulto), treinado sobre corpora de várias línguas
- **ALICE** — estimador aberto de contagem de unidades linguísticas do adulto
- **VCM** — classificador de vocalizações infantis (canônica, não-canônica, choro, riso)
- ecossistema **ChildProject** para gerenciar gravações longas centradas na criança

**Diarização atual** — pyannote 3.x, NeMo Sortformer, abordagens neurais ponta-a-ponta, que
tratam sobreposição muito melhor do que o clustering da geração em que LENA foi construída.

**ASR** — Whisper ou modelos auto-supervisionados (WavLM/wav2vec2) **ajustados com fala infantil**,
não em zero-shot. Para PT-BR, verificar corpora nacionais (ex.: CORAA) e a seção em português do
CHILDES como base de ajuste.

### A correção que de fato resolve: instrumentar a sala, não trocar o modelo

Nenhum modelo resolve atribuição de falante num campo distante com 20 crianças. As duas saídas
são de captação, não de software:

**1. Microfone individual em amostra rotativa.** Em vez de tentar separar 20 vozes de um array
ambiente, 2–3 crianças por dia usam um gravador de contato próximo, rodando entre a turma. Alta
relação sinal-ruído para quem está usando, e o problema de atribuição praticamente desaparece
para essa criança. Troca cobertura contínua por dado confiável — e para desenho longitudinal
intra-sujeito, amostragem periódica basta.

**2. Array de microfones + o mapa espacial que o projeto já tem.** Este é o ponto que diferencia
este projeto e que não estava na Parte I:

> O sistema de visão **já sabe onde cada criança está em coordenadas da sala**, quadro a quadro.

Isso é um *a priori* espacial que nenhum sistema de áudio infantil teve à disposição. Combinando
localização de fonte sonora por array com as posições conhecidas dos falantes, a pergunta deixa
de ser "quantas pessoas falaram e quem são" (diarização cega, mal condicionada) e vira "qual das
posições conhecidas emitiu este som" — que é um problema muito melhor posto. Some-se a isso o
sinal visual de movimento de boca e orientação corporal, e a atribuição fica ancorada em duas
modalidades independentes.

É uma inversão relevante de ordem: **áudio deve vir depois do tracking espacial estar bom,
porque o tracking é o que torna o áudio tratável.** A ordem da Parte I já coloca linguagem depois
de espaço, mas por dependência técnica; o motivo real é este.

### O que se pode afirmar, revisado

| Medida | Viável? |
|---|---|
| duração de fala, volume de vocalização, latência de resposta | sim, com microfone individual; no campo distante, só com atribuição validada |
| turnos conversacionais, quem falou com quem, iniciação × resposta | **condicionado** — depende de atribuição de falante, o elo fraco; só com mic individual ou fusão áudio-espacial validada |
| MLU, diversidade lexical, complexidade sintática, classes gramaticais | **não**, até que a WER seja medida no áudio real desta sala |

### Regra

**Não herdar número de acurácia publicado por ninguém.** Toda cifra de validação desta
literatura foi obtida em outra língua, outro ambiente e outra densidade de falantes. Anotar à
mão algumas horas do áudio *desta* sala e medir localmente diarização, atribuição e WER. Só o
que sobreviver a essa medida entra no dicionário de variáveis; o resto fica marcado como
bloqueado, como está no anexo.

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

## 10. Armazenamento: guardar 2 anos de bruto (R3)

**Correção de uma análise anterior deste documento.** Eu havia recomendado reter bruto por
30–90 dias e depois manter só o derivado, com o argumento de que guardar tudo não seria viável
"nem financeira nem juridicamente". A parte financeira estava errada por má calibragem de escala:
seis câmeras em uma sala não é videomonitoramento urbano. Refeita a conta, a decisão de R3 é a
correta, e por uma razão que vai além de custo.

### A razão de fundo: bruto é a única coisa irreversível

Um estudo longitudinal exige **consistência de método ao longo dos anos**. Mas os métodos vão
melhorar — modelo de pose melhor, definição de "interrupção" corrigida, detector de material
retreinado. Só existem duas formas de conciliar as duas coisas:

1. congelar o método por anos e ficar com medida pior a cada ano que passa; ou
2. **guardar o bruto e reprocessar o histórico inteiro** a cada mudança de método.

A opção 2 é a única que preserva simultaneamente qualidade e comparabilidade. E ela exige o
arquivo. Sem ele, cada melhoria de modelo cria uma descontinuidade na série exatamente onde o
método mudou — e não há como saber se a variação observada em 2028 é da criança ou do detector.

Descartar bruto em 90 dias significa que **tudo o que não foi extraído naquela janela está
perdido para sempre**, inclusive o que só se descobrirá ser importante em 2029.

### O volume

6 câmeras · H.265 · 11 h/dia · 5 dias/semana:

| | GB/dia | TB/ano (200 dias letivos) | TB/ano (260 dias) | 2 anos |
|---|---|---|---|---|
| original 4K @ 12 Mbps/câm | 356 | 71 | 93 | **143–185 TB** |
| original 4K @ 15 Mbps/câm | 446 | 89 | 116 | 178–232 TB |
| proxy 1080p @ 3 Mbps/câm | 89 | 18 | 23 | 36–46 TB |

Ordem de grandeza para dimensionar, não orçamento: com redundância e uma segunda cópia, algo na
casa de **300–500 TB brutos** de capacidade instalada para o período. Em disco rígido de
capacidade, isso é dezenas de milhares de reais — **comparável a uma workstation, não a um
projeto à parte**. Pedir cotação real antes de fechar.

### Onde guardar

**Disco local, não arquivamento frio em nuvem.** O ponto inteiro do arquivo é **relê-lo muitas
vezes** (reprocessamento). Classes tipo Glacier Deep Archive são baratas para guardar e caras e
lentas para ler — exatamente o inverso do padrão de uso aqui. Nuvem fria serve como **segunda
cópia offsite**, criptografada, nunca como arquivo de trabalho.

### Proxy permanente + original com prazo

Desenho que dá as duas coisas:

| Camada | Retenção | Função |
|---|---|---|
| **proxy 1080p** | permanente (ou muito longa) | **entrada real da detecção global** — a Parte I §12 já roda detecção em resolução reduzida. O proxy não é backup, é o insumo de produção. ~18–23 TB/ano é irrisório. |
| **original full-res** | 2 anos, reavaliado em R3 | crops de mão/dedo em alta resolução, reprocessamento futuro, anotação humana |

Se em algum momento for preciso apagar originais, ainda resta um arquivo reprocessável.

### O que muda de fato: o desenho jurídico, não o custo

Com R3, o binding constraint deixa de ser dinheiro e passa a ser LGPD. Guardar 2 anos é
perfeitamente legítimo — desde que **declarado, justificado e consentido nesses termos**:

- prazo de retenção e finalidade explícitos no RIPD e no termo de consentimento
- **"reprocessamento do material bruto ao longo do projeto" precisa constar como finalidade
  declarada.** Sem isso, guarda-se vídeo que não se pode reanalisar — o pior dos dois mundos
- criptografia em repouso, controle e log de acesso, cópia offsite
- **revogação de consentimento precisa de resposta decidida antes da primeira gravação.** Não é
  possível apagar uma criança de um quadro que contém sete. A regra prática — saída retira a
  criança de todas as análises e apaga o derivado dela, com o bruto sob base e prazo documentados
  — precisa estar escrita e aprovada antes, não improvisada quando a primeira família pedir.

### Não usar gravação por detecção de movimento

Sala vazia também é dado, e janela faltante quebra série temporal. Gravar a janela de
funcionamento inteira, continuamente.

## 11. Emocional e criatividade: como fazer sem produzir lixo (R2)

**Reversão.** Eu havia recomendado cortar criatividade dos dois primeiros anos e evitar qualquer
coisa perto de emoção. R2 decidiu o contrário, e a decisão está certa: criatividade é o constructo
mais alinhado à tese da escola, e emocional é o principal mediador entre sono e todo o resto —
cortar os dois deixaria o projeto medindo bem justamente o que menos importa para ele.

O que a minha objeção original de fato acertava é mais estreito do que eu escrevi, e continua
valendo dentro de R1: **o problema nunca foi observar — foi reportar um número de nível 3 como se
fosse medida.** Observar amplo e reportar estreito resolve isso sem custo nenhum para o escopo.

### Emocional

O que é cientificamente indefensável é uma coisa só: **classificar emoção a partir de face**.
Configuração facial não mapeia de forma confiável em categoria emocional entre contextos e
culturas (revisão de Barrett et al., 2019) — e em criança pequena, menos ainda. `face → "triste"`
está fora.

Tudo o mais está dentro, e é bastante:

**Nível 1 — observáveis físicos, nenhum juízo emocional:**

| Sinal | Fonte |
|---|---|
| prosódia: F0 médio e variância, intensidade, taxa de fala, qualidade de voz | áudio |
| choro / vocalização de distress (evento acústico, não rótulo) | áudio (VCM) |
| riso | áudio |
| **unidades de ação facial (FACS/AUs)** — intensidade de AU é medida física, não emoção | vídeo |
| energia de movimento, agitação, jerk | pose |
| postura: encolhida × ereta, autotoque, mão-ao-rosto | pose |
| aversão de olhar, orientação de cabeça | pose |
| aproximação × afastamento de pessoas | trajetória |

A distinção que sustenta tudo: **AU12 (elevador do canto do lábio) é observável; "feliz" é
interpretação.** Guarda-se o primeiro.

**Nível 2 — episódios comportamentais, onde está o valor real:**

- **episódio de distress** — início, duração, desfecho
- **tempo de recuperação** — do início do distress ao retorno ao comportamento de base ou ao
  trabalho. É provavelmente a variável emocional mais útil e mais defensável do projeto, e é o
  núcleo da literatura de autorregulação
- **corregulação** — adulto se aproxima de criança em distress → tempo até resolução
- **episódio de conflito** — duas crianças, objeto disputado, duração, tipo de resolução
  (autorresolvido / mediado por par / mediado por adulto)
- **frustração no trabalho** — erro → nova tentativa × abandono
- **persistência após falha** — tentativas após o primeiro erro antes de abandonar

Os dois últimos saem **direto dos dados de work episode que já estão sendo coletados, sem face
nenhuma** — driblam por inteiro a controvérsia da computação afetiva e capturam o que de fato
importa no desenvolvimento.

**Nível 3** — autorregulação, reatividade, capacidade de recuperação. Só por combinação de
nível 1–2 com **instrumento externo validado** e humano no circuito. Candidatos: **SDQ**
(curto, gratuito, com versão PT-BR), **CBCL/TRF**, **ERC**. Aplicados por onda, servem de critério
externo contra o qual as métricas automáticas são calibradas.

### Criatividade

Mesmo movimento, e aqui há teoria estabelecida em que ancorar. As dimensões clássicas de Torrance
são operacionalizáveis como contagens sobre comportamento observado:

| Dimensão | Operacionalização neste sistema |
|---|---|
| **fluência** | número de ações/soluções distintas num episódio aberto |
| **flexibilidade** | número de **categorias** distintas de abordagem (esquema de categorias definido por humano) |
| **originalidade** | **raridade estatística da ação no próprio corpus da sala** |
| **elaboração** | retorno a um trabalho anterior e modificação dele |

**Originalidade é o achado deste desenho.** Com um banco longitudinal de tudo que toda criança já
fez com todo material, originalidade vira `P(esta ação | este material, esta sala, este período)`
— uma **frequência nos próprios dados**, não a opinião de um modelo. Nenhum julgamento subjetivo
entra no cálculo. Isso só é possível porque R1 mandou observar amplo desde o começo: a raridade
de uma ação em 2028 depende de ter registrado o que era comum em 2026.

**Eventos específicos de Montessori, todos automatizáveis:**

- **uso não-canônico do material** — a sequência canônica de cada material é **autorada** por
  pedagoga na ontologia de materiais (Parte IV §1.4–1.5; o treino do detector ensina como o
  material *parece*, não como é *usado*). Desvio é detectável **como desvio**, sem julgar.
  Se é erro, exploração ou invenção, é a pergunta da codificação humana — mas a detecção é
  automática, e é um evento de nível 2 excelente
- **combinação de materiais** de áreas diferentes usados juntos — trivial de detectar depois que
  a detecção de objetos funciona, e carregada de sentido em termos montessorianos
- **sequência de estratégias** A → B → C sobre o mesmo problema
- **exploração antes da solução** — razão entre manipulação exploratória e ação dirigida a objetivo
- **retorno e modificação** de trabalho anterior

**E a variável que provavelmente é a mais publicável do projeto inteiro:**

> **Difusão social de uma invenção.** Criança X faz algo não-canônico pela primeira vez. Criança Y
> faz depois? Quanto tempo levou? Houve contato ou proximidade entre elas nesse intervalo?

Isso é **formação de cultura numa sala de aula**, medida. Exige exatamente o que este projeto tem
e quase ninguém mais: identidade persistente, ação categorizada, proximidade espacial e série
longitudinal, tudo junto. É o tipo de pergunta que nenhuma bateria de testes de criatividade
alcança, porque exige observar a sala inteira ao longo de anos.

**Validação:** codificadores humanos avaliam uma amostra de episódios nas dimensões de Torrance,
com concordância medida; nomeações de educadores como critério externo; e, para os mais velhos,
uma prova de tipo TTCT aplicada por onda.

### O guardrail que sobrevive — e que é o próprio R1

Amplo na observação, estreito no relatório:

| | |
|---|---|
| **observado e guardado** | AUs, prosódia, distress, recuperação, raridade de ação, uso não-canônico, difusão — o conjunto largo, desde o dia 1 |
| **reportado a família ou educador** | só o que passou por validação contra critério externo, com incerteza declarada |

Um número de nível 3 que entra num relatório para família é praticamente impossível de retirar
depois. Isso não é argumento para não medir — é argumento para **medir muito e publicar pouco**,
que é exatamente R1.

## 12. A força real do projeto

Se houvesse uma única recomendação a levar deste documento:

> **Observar amplo e guardar tudo; congelar a definição do que é reportado e reprocessar o
> histórico a cada melhoria de método.**

O ponto delicado, e o mais fácil de esquecer: uma série longitudinal **quebra se a definição da
variável mudar no meio** — toda mudança de definição zera o histórico comparável. Isso é um
argumento forte contra soltar métricas cedo e ir mexendo nelas.

Mas **não** é argumento para observar pouco, e é aí que a versão anterior desta seção errava.
As duas coisas se conciliam por R3 + R4: como o bruto está guardado, mudar uma definição não zera
nada — **reprocessa-se o arquivo inteiro com a definição nova**, e a série volta a ser comparável
de ponta a ponta. Custa GPU, não custa história.

Então o núcleo pequeno e estável é dos **indicadores publicados**, não do que é observado:

| | |
|---|---|
| observado, guardado, versionado | o mais amplo que a captação permitir, desde o dia 1 (R1) |
| definição congelada e reprocessada | o subconjunto que vira indicador longitudinal |
| publicado / reportado | menor ainda: só o que passou por validação externa |

Três anos ininterruptos de duração de work episode + sono + tempo de recuperação emocional, com
definição estável e reprocessamento consistente, valem mais do que 100 indicadores instáveis por
6 meses. O que muda em relação à versão anterior é que os outros 97 continuam sendo **observados
e guardados** — só não são promovidos a indicador antes da hora.

E a vantagem estrutural que quase nenhum estudo da área tem: séries temporais densas, diárias,
in situ, com cada criança como seu próprio controle, ao longo de anos. O padrão da área é medida
esparsa, em laboratório, fora de contexto.

## 13. Ordem de execução recomendada

**Divergência** em relação à §17 da Parte I: aquela é a ordem de dependência *técnica*. Esta
segue R4 — **tudo que é captura vai para a fase 1**, porque não volta; extração vem quando o
método estiver pronto, porque pode ser refeita sobre o arquivo.

| Fase | Frente | Entregas |
|---|---|---|
| **Mês 0** *(sem GPU)* | fundação | trilha jurídica/ética · consentimento granular **incluindo reprocessamento e retenção de 2 anos** · **diário de sono começa a rodar** · dicionário de variáveis v1 · protocolo de codificação humana · **log diário de contexto** · **ontologias de materiais, sala e dia** (Parte IV §1.4) |
| **Fase 0 — bancada** *(2–3 semanas)* | **teste antes de comprar** | os 21 testes da Parte IV §2 com 2 câmeras candidatas, array, mic individual e sensor de soneca · **especificação de captura assinada** (modelo, resolução, posição, sincronização, UPS) · consentimento iterado com famílias e equipe · protocolo humano com concordância medida · dimensionamento de hardware · **análise de poder → hipóteses confirmatórias fixadas antes do pré-registro** |
| **Mês 1–3** | **captura completa** | câmeras + calibração · **fiduciais fixos e verificação diária automática de calibração e sincronização** · UPS e gravação redundante · **áudio: array + mic individual rotativo instalados e gravando desde já** · sensor de soneca (radar/colchonete) · etiquetas de identidade, se aceitas · armazenamento proxy+original · **variáveis de camada 0** (observabilidade, uptime, presença) · humanos codificam 1 semana · concordância entre codificadores |
| **Mês 3–6** | identidade e espaço | tracking · identidade · mapa espacial · **UI de revisão de tracks** · trajetória validada contra codificação humana |
| **Mês 6–12** | atividade e primeiro substrato | detecção de materiais · work episodes · **frustração e persistência após falha** (saem do work episode, sem face) · **comportamento do adulto**, desenhado com a equipe (Parte IV §1.8) · **primeiro cruzamento sono × concentração** |
| **Ano 2** | motor, linguagem, afeto | pose e mãos · atribuição de falante ancorada no mapa espacial, validada localmente · AUs e prosódia · episódios de distress e tempo de recuperação · **uso não-canônico e combinação de materiais** |
| **Ano 2–3** | criatividade e difusão | raridade de ação sobre o corpus acumulado · sequências de estratégia · **difusão social de invenção** · validação humana nas dimensões de Torrance |
| **contínuo** | reprocessamento e coorte | recampanha sobre o arquivo a cada mudança de modelo ou definição · **re-enrolamento de aparência** e gestão de entradas/saídas (Parte IV §1.9) · teste de determinismo a cada versão (§1.12) |

Duas observações sobre a tabela:

**A fase 1 ficou mais cara e mais larga do que na versão anterior**, e é assim que tem que ser
sob R4. Instalar o array de áudio no ano 2 significaria um ano sem áudio nenhum para reprocessar —
perda permanente, contra a qual nenhum modelo futuro pode nada.

**Criatividade só pode chegar no ano 2–3, e isso não contradiz R2.** A originalidade é definida
como raridade no corpus da própria sala: ela é *matematicamente impossível* de calcular antes de
existir corpus. O que R2 exige é que o **substrato seja observado e guardado desde o dia 1** —
e é o que a tabela faz. O cálculo vem depois porque depende de história acumulada, não porque foi
adiado por cautela.

As coisas que custam quase nada e destravam todo o resto — **diário de sono**, **protocolo de
codificação humana** e **log diário de contexto** — estão todas no mês 0. Não é coincidência:
são as únicas que não dependem de nenhuma outra peça, e todas acumulam valor enquanto a
engenharia acontece.

### O log diário de contexto

Acréscimo que a versão anterior não tinha e que R4 torna óbvio. O vídeo mostra a sala, não mostra
o **porquê**. Nada disto é reconstruível depois, e tudo custa alguns minutos por dia:

quem faltou e por quê · material novo introduzido · sala rearranjada · criança doente ·
medicação · educador ausente ou substituído · evento familiar relevante · passeio, festa,
quebra de rotina · recalibração de câmera

Sem isso, uma queda coletiva de concentração numa terça-feira fica para sempre sem explicação —
e o modelo vai atribuí-la a alguma variável interna que nada tem a ver.

## 14. Arquitetura modular: muitos modelos especializados

A Parte I §2 propõe compor o sistema de vários modelos estreitos — um só para pose corporal, outro
só para mãos, outro para objetos, outro para tracking. **Está certo.** Mas o motivo mais forte não
é o que costuma ser dado, e as ressalvas importam mais do que a decisão.

### Por que está certo

**Não é bem uma escolha.** Não existe um modelo único que faça detecção + tracking 3D entre
câmeras + pose de corpo inteiro + 21 landmarks por mão + objetos customizados + segmentação
temporal de ações no nível de qualidade que pesquisa exige. Compor é a única opção disponível
nessa barra. A pergunta real não é "compor ou não", é **como compor sem que a composição vire o
problema**.

**O motivo forte: cada parte pode ser validada separadamente.** Isso liga direto ao §2 — anotação
e validação são o gargalo. Num pipeline modular dá para medir "quão bom é meu landmark de mão"
contra anotação humana, independentemente de "quão bom é meu detector de material". Num monólito
sai um número só para o sistema inteiro e **não há como atribuir o erro a lugar nenhum**.

Para um instrumento de medida — que é o que este projeto é — atribuir erro a um estágio não é
conveniência de engenharia. É a diferença entre um instrumento e uma caixa-preta.

**E cada parte pode ser trocada sem reconstruir o resto.** Em cinco anos, estimação de mão vai
melhorar. Se mão é um módulo com interface definida, troca-se, reprocessa-se o arquivo (R3/R4) e
a série continua comparável. Embutida num monólito, seria retreinar tudo.

### Ressalva 1 — a composição é a parte difícil, não os componentes

Todo módulo da lista está a um `pip install` de distância. O que **não** é de graça:

**Alinhamento de tempo e de coordenadas.** MediaPipe devolve landmarks nas coordenadas do próprio
crop; RTMPose nas dele; DeepStream nas suas; cada câmera na sua. Trazer tudo para coordenadas da
sala e para um relógio único é onde projetos assim morrem. Câmeras precisam de sincronização de
timestamp sub-quadro, e o áudio precisa estar alinhado ao vídeo.

> Não é detalhe: a análise multimodal da Parte I §8 — "adulto diz *borboleta* às 10:32:17, criança
> toca a imagem às 10:32:19" — **perde o sentido com 200 ms de deriva**. Atenção conjunta é
> medida em centenas de milissegundos. A sincronização não é infraestrutura de apoio; é
> pré-condição da hipótese científica mais interessante do projeto.

**Propagação de erro.** É o principal risco científico do desenho modular e o outro lado da moeda
da validação por estágio. Erro de detecção vira erro de tracking, vira troca de ID, vira mão da
criança errada, vira métrica de destreza atribuída a quem não fez. Os erros **multiplicam** ao
longo da cadeia:

```
5 estágios a 95% cada  →  0,95⁵ ≈ 77% de ponta a ponta
```

Essa conta precisa estar visível. É também o argumento mais forte para a UI de revisão de tracks
do §4: identidade é o estágio mais a montante, e por isso o que mais contamina.

**Inferno de dependências.** MMPose, MediaPipe, DeepStream, PyTorch e CUDA têm grafos de
dependência que conflitam entre si. A resposta prática é firme: **um contêiner por módulo,
comunicação por arquivo ou fila, nunca um ambiente único.** Tentar `pip install` de tudo no mesmo
venv custa dias — e custa de novo a cada atualização.

### Ressalva 2 — confiança tem que propagar, não ser descartada

Cada estágio produz uma confiança. A métrica final precisa carregar a confiança **conjunta**, e
linhas de confiança baixa precisam ser marcadas, não diluídas na média.

É exatamente isso que separa "modular e honesto" de "caixa-preta com passos extras". Toda linha
derivada carrega `confidence` **e** proveniência — quais versões de quais módulos a produziram —
junto de `pipeline_version` / `model_version` / `definition_version` (R4).

### Ressalva 3 — módulos entram em ordem, não todos no dia 1

A lista da Parte I §2 é **arquitetura-alvo, não configuração inicial**. Cada módulo somado
multiplica superfície de integração, e um módulo só entra depois que o de baixo estiver validado.

Ligar mãos antes de a identidade estar sólida produz medida de altíssima precisão **atribuída à
criança errada** — pior que não medir, porque parece dado bom. A ordem do §13 já reflete isso.

Sob R4 não há perda nenhuma nessa cadência: **captura-se tudo desde o dia 1; extrai-se conforme
cada módulo fica pronto e validado**, reprocessando o arquivo.

### O que **não** deve ser modular: a fusão

Ressalva que inverte a regra, e é onde está o ganho de qualidade. Detectores devem ser modulares;
**a fusão deve ser conjunta, não sequencial.** Três casos:

| Fusão | Sequencial (pior) | Conjunta (melhor) |
|---|---|---|
| áudio × espaço | diarizar e depois casar com posições | inferir falante já condicionado às posições conhecidas (§5) |
| pose entre câmeras | escolher a melhor vista 2D | triangular as 6 vistas com a calibração |
| mão × objeto | estimar mão, depois classificar objeto | cada um restringe o outro — saber o objeto na mão melhora as duas estimativas |

Ou seja: **modular nos detectores, conjunto na fusão.**

### O acoplamento certo: por esquema, não por código

A chave para trocar módulos sem reescrever o sistema é que eles **não se chamem**. Cada módulo lê
e escreve um esquema intermediário versionado em disco — a representação de observações do §11 da
Parte I. Troca-se o módulo de mão por outro que escreva o mesmo esquema, e nada mais muda.

Módulos acoplados por chamada de função viram monólito em seis meses, sem ninguém decidir isso.

### E os modelos de fundação / VLMs?

Pergunta inevitável hoje. A resposta se divide:

**Não como camada de medida.** Um VLM perguntado "esta criança está concentrada?" devolve um
número plausível sem característica de erro mensurável e sem reprodutibilidade entre versões. Pior
para este projeto especificamente: **a saída muda quando o fornecedor atualiza o modelo**, o que
quebra a série longitudinal em silêncio, sem que nada no sistema acuse. Para um estudo de anos,
essa propriedade é fatal. A Parte I §14 já diz isso ("nunca como fonte única da métrica") e vale
manter.

**Sim em dois lugares, e são valiosos:**

1. **Acelerador de anotação** — pré-rotular episódios candidatos para humanos corrigirem. Ataca
   diretamente o gargalo do §2, que é o centro de custo real do projeto.
2. **Índice de busca sobre o arquivo** — "ache todos os trechos em que uma criança combinou dois
   materiais de áreas diferentes". Para o trabalho de criatividade (R2), isso é enorme: é como se
   montam os datasets de uso não-canônico e combinação sem assistir a dois anos de vídeo.

Nos dois casos o VLM **encontra coisas para humanos verificarem**; não mede. É a mesma linha do
nível 1–2–3.

---

# Parte IV — Revisão: lacunas, bancada de testes e conjunto inicial de variáveis

Releitura crítica das Partes I–III. Três blocos: o que falta no plano, quais testes de ferramenta
fazer antes de comprometer dinheiro e captura, e por quais variáveis começar. Onde uma lacuna
corrige algo escrito antes, está dito.

## 1. Lacunas encontradas

Em ordem de consequência. As três primeiras são **decisões de captura** — sob R4, irreversíveis —
e por isso vêm antes de tudo.

### 1.1 Não existe fase piloto

O plano vai do mês 0 direto para "6 câmeras instaladas e gravando" sem que nenhuma ferramenta
tenha sido testada **nesta sala, com estas crianças, nesta luz**. Toda cifra de acurácia da
literatura veio de adultos, de outro ambiente ou de outra língua. Comprar seis câmeras, definir
posição, resolução e microfones antes de um piloto é apostar o que não volta.

Correção: uma **Fase 0 — bancada**, de 2–3 semanas, com 2 câmeras candidatas, 1 array de áudio,
1 microfone individual e 1 sensor de soneca, gravando 2–3 dias inteiros (com consentimento
piloto — o piloto também é coleta). O protocolo está no §2.

### 1.2 Especificação e posicionamento das câmeras não existem

"6 câmeras de alta resolução" é a única especificação no documento. Faltam as decisões que mais
determinam o que será mensurável:

| Decisão | Por que importa |
|---|---|
| **altura e ângulo** | zenital (teto, olhando para baixo) é excelente para trajetória e quase sem oclusão, e péssimo para rosto e detalhe de mão; oblíquo é o inverso. Provavelmente **híbrido**: 4 câmeras altas oblíquas nos cantos para tracking + câmeras baixas nas áreas de trabalho para mão e rosto |
| **taxa de quadros** | 15 fps bastam para trajetória; preensão e ajuste fino de mão pedem **30–60 fps** — em 15 fps um movimento de encaixe de 1,4 s são 21 quadros |
| **obturador** | *rolling shutter* distorce mão em movimento rápido; *global shutter* custa mais e resolve |
| **faixa dinâmica e luz** | sala Montessori costuma ter janelas grandes: contraluz, luz que muda ao longo do dia, sombras duras. Câmera com bom HDR, ou controle de luz, ou aceitar zonas cegas no fim da tarde |
| **sincronização em hardware** | PTP ou genlock **como critério de compra**, não como ajuste depois (Parte III §14: 200 ms de deriva matam a atenção conjunta) |
| **gravação redundante e UPS** | queda de energia é perda irreversível; câmera com cartão local + NVR, e nobreak |

Todas são decisões da Fase 0.

### 1.3 Resolução na mão e no rosto: a conta que faltava

O documento assume análise de 21 landmarks de mão e unidades de ação facial a partir das câmeras
de teto. Vale fazer a conta antes de assumir.

Sala hipotética de 8 × 6 m, seis câmeras, cada uma cobrindo ~4 × 2,25 m no chão (e na prática
**mais**, porque tracking multicâmera exige sobreposição — logo estes números são otimistas):

| Resolução | px/m no chão | mão de criança (~8 cm) | rosto de criança (~12 cm) |
|---|---|---|---|
| 1080p (proxy) | ~500 | ~40 px | ~60 px |
| 4K | ~1000 | ~80 px | ~120 px |
| 8K | ~2000 | ~160 px | ~240 px |
| 12K | ~3200 | ~250 px | ~380 px |

Estimadores de mão como MediaPipe foram desenhados para distância de webcam; **na prática pedem
bem mais de 100 px de mão**. Em 4K de teto, mão é marginal; em 1080p, inviável. Rosto para AUs
precisa de orientação quase frontal além de resolução — de teto, raramente tem.

Consequência: **ou câmeras de resolução muito alta, ou câmeras dedicadas baixas nas mesas de
trabalho, ou aceitar análise de mão só quando a criança está perto de uma câmera.** É a decisão
mais cara do projeto e não estava escrita. O piloto mede o px/m real e decide (§2, teste T1).

### 1.4 Ontologias que humanos precisam escrever antes de qualquer modelo

Três estruturas de conhecimento que o documento usa implicitamente e ninguém está encarregado de
produzir. Nenhuma precisa de GPU; todas são mês 0:

**Ontologia de materiais.** Para cada material: nome canônico e ID · área pedagógica · prateleira
onde vive · **sequência canônica de apresentação e uso** · o que treina (alvo de desenvolvimento)
· faixa etária típica · **controle de erro** (o material acusa o erro sozinho? como?) · peças
confundíveis (cubos adjacentes da Torre Rosa). Escrita por pedagoga montessoriana, versionada.

**Ontologia da sala.** Planta medida · polígonos das áreas · posição de cada prateleira · zonas
(tapetes, mesas, linha, porta) · pontos fixos de calibração. Atualizada a cada rearranjo (e o
rearranjo vai para o log de contexto).

**Ontologia do dia.** Fases: chegada · ciclo de trabalho da manhã · refeição · soneca · ciclo da
tarde · saída. **Métricas se calculam por fase, não por dia** — concentração durante o almoço não
significa nada, e um ciclo de trabalho de 3 h é a unidade natural montessoriana. Fronteiras
logadas ou detectadas automaticamente.

### 1.5 Correção: a sequência canônica não vem do treino do detector

A Parte III §11 afirma que "o sistema conhece a sequência canônica de cada material (é o próprio
dado de treino dos detectores)". Está errado. O dado de treino ensina **como o material parece**,
não **como ele é usado**. A sequência canônica é conhecimento pedagógico, **autorado** na
ontologia de materiais (1.4). Sem ela, `noncanonical_use` não tem contra o que ser calculado.

### 1.6 Observabilidade por criança por dia — a covariável que falta

Nenhuma variável do dicionário registra **quanto do dia a criança foi de fato observada com
confiança**. Sem isso, um dia em que a criança passou 3 h atrás de uma estante parece um dia de
baixa atividade. Precisa existir `child_observability_frac` por criança, por fase, por dia —
e toda métrica derivada deve ser normalizada ou marcada por ela. É provavelmente a covariável
mais importante que não estava escrita.

Junto dela, **presença**: chegada, saída, ausência, motivo (do log de contexto).

### 1.7 Saúde da calibração e da sincronização como verificação diária automática

Câmera esbarrada é silenciosa: coordenadas ficam erradas por semanas sem ninguém notar. Precisa
de **marcadores fiduciais fixos na sala** (tipo AprilTag, em posições medidas) e uma checagem
automática diária de erro de reprojeção e de deriva de relógio, com alarme. Sem isso, R4 não se
sustenta — reprocessar um arquivo com calibração corrompida reproduz o erro.

### 1.8 Comportamento do adulto como classe de variável

O documento trata o adulto como contagem de "intervenções" e como problema trabalhista (§6). Em
Montessori, o adulto é **a principal variável controlável da sala**: apresentações dadas (a quem,
qual material, quando), tempo observando × intervindo, redirecionamentos, posição na sala. Se o
dado deve informar a pedagogia, isso é medida central, não ruído.

Precisa ser desenhado **com** as educadoras, enquadrado como pesquisa pedagógica: reporte
agregado por padrão, dado individual só sob regra escrita e acordada. É a única forma de ter o
dado e a equipe ao mesmo tempo.

### 1.9 Coorte dinâmica

Em três anos as crianças crescem, mudam cabelo e roupa, entram e saem da escola. Qualquer galeria
de aparência para re-identificação precisa de **re-enrolamento periódico**; datas de entrada e
saída por criança precisam existir como dado; e as análises longitudinais precisam lidar com
séries de comprimentos diferentes. Nada disso estava no plano.

### 1.10 Idade em meses como covariável obrigatória

Sala Montessori é multi-idade: 2 a 6 anos juntos. Duração de episódio de trabalho de uma criança
de 2 anos e de uma de 5 **não são comparáveis**. O desenho intra-sujeito resolve para perguntas
dentro da criança; qualquer comparação entre crianças ou de coorte exige idade em meses, e
trajetórias de desenvolvimento devem ser modeladas contra idade, não contra calendário.

### 1.11 Orçamento de tempo humano — a conta que faltava

O §2 da Parte III diz que anotação é o gargalo e não estima nada. Ordens de grandeza:

| Tarefa | Custo |
|---|---|
| revisão de tracks (correção de troca de ID) | **sem etiquetas:** 4–8 h por dia gravado; **com etiquetas UWB:** 1–2 h, só nos trechos sinalizados |
| codificação humana para validação | codificação comportamental detalhada corre a 5–10× tempo real. Ninguém codifica a semana inteira: amostram-se ~20 trechos de 15 min estratificados por criança e fase (~5 h de vídeo) → **25–50 h por codificador por rodada**, dois codificadores, uma rodada por módulo |
| log de contexto | 10 min/dia |
| acompanhamento do diário de sono (cobrar famílias) | 1–2 h/semana |
| verificação de saúde do sistema | 15 min/dia se automatizada; horas se não |

A linha de revisão de tracks é o argumento numérico mais forte a favor das etiquetas UWB do §4:
**a diferença é de uma pessoa em tempo integral.**

### 1.12 Determinismo do pipeline

R4 depende de reprocessar e obter o mesmo resultado quando nada mudou. Modelos com
não-determinismo de GPU, trackers com dependência de ordem e amostragem aleatória quebram isso em
silêncio. Precisa de teste de **test-retest da máquina**: rodar o mesmo dia duas vezes e exigir
igualdade (ou diferença abaixo de limiar declarado). Se a máquina não concorda consigo mesma, a
concordância com humanos não significa nada.

### 1.13 Marcadores fiduciais nos materiais

Truque barato que pode tornar identidade de material quase determinística: etiqueta fiducial
pequena (AprilTag) na **base ou no verso** de cada material. Dá identidade e orientação sem
depender de classificador visual, e resolve os confundíveis (cubos adjacentes da Torre Rosa).

Contras a testar: estética montessoriana (o material é desenhado para ser belo; a etiqueta fica
onde a criança não vê), oclusão pela mão durante o uso, e se a criança passa a brincar com a
etiqueta. Vale um teste na Fase 0 antes de descartar.

### 1.14 Piloto para análise de poder antes de pré-registrar

O §8 pede pré-registro de H1–H7. Pré-registrar sem estimativa de tamanho de efeito e de variância
intra-criança é pré-registrar no escuro. Os dias de piloto fornecem a variância; com ela se calcula
se 200 dias/ano e ~20 crianças dão poder para cada hipótese — e as que não dão saem do
confirmatório para o exploratório **antes**, não depois.

### 1.15 Governança de acesso em camadas

Mencionada em pedaços (§6, §10), não desenhada. Três camadas mínimas: **bruto** (pouquíssimas
pessoas, log de cada acesso) · **derivado por criança** (pesquisadores, pseudonimizado) ·
**agregado** (educadoras e famílias). Quem está em cada camada fica escrito no RIPD.

### 1.16 O que a família vê

R1 diz "reportar estreito" e o documento não desenha o relatório. Adiado é aceitável; ausente
não. Registrar aqui que **o relatório à família é um entregável a desenhar no ano 1**, com a regra
já fixada: só indicadores validados contra critério externo, com incerteza declarada, nunca
nível 3 sem validação.

## 2. Bancada de testes — Fase 0

**Objetivo:** tomar toda decisão de captura (irreversível, R4) e toda escolha de ferramenta com
dado **desta sala**, antes de comprar seis câmeras e antes do primeiro dia de gravação definitiva.

**Duração:** 2–3 semanas. **Equipamento:** 2 câmeras candidatas (uma de cada tipo em disputa —
ex.: 4K oblíqua e 8K/12K zenital, ou uma alta e uma baixa de mesa), 1 array de microfones,
1–2 microfones individuais, 1 sensor de soneca (radar ou colchonete), 1 workstation com GPU
candidata. **Coleta:** 2–3 dias inteiros de gravação com **consentimento piloto** — o piloto
também é coleta de dado de criança e precisa da mesma base legal.

**Ground truth:** amostra estratificada por criança × fase do dia, anotada à mão. Toda métrica
abaixo é medida contra ela, nunca herdada da literatura (Parte III §5, regra).

### Os testes

| ID | Teste | O que medir | Contra o quê | Métrica | Decisão que destrava |
|---|---|---|---|---|---|
| **T1** | resolução e posicionamento | px/m real no chão e na altura da mesa; tamanho em px de mão e rosto de criança nas posições típicas; % do tempo com mão > 100 px e rosto quase frontal | régua/tabuleiro em posições medidas | px/m; distribuição de px de mão e rosto | **resolução, lente, altura, ângulo; se precisa de câmeras baixas de mesa** |
| **T2** | sincronização | deslocamento entre câmeras e entre áudio e vídeo no início e no fim do dia | palma/flash no início e no fim | deriva em ms ao longo de 11 h | **PTP/genlock como critério de compra; modelo de câmera** |
| **T3** | calibração e saúde | erro de reprojeção; erro em metros em ≥10 pontos medidos com fita; esbarrar a câmera 1° e ver se o alarme dispara | fita métrica, fiduciais fixos | erro em cm; detecção da perturbação | procedimento, posição dos fiduciais, limiar de alarme |
| **T4** | luz | exposição e contraste por hora por zona; quadros perdidos por contraluz/estouro | inspeção por hora | % de quadros inutilizáveis por zona e hora | câmera com HDR, cortinas, zonas cegas aceitas |
| **T5** | detecção de pessoas | YOLO × RTMDet em criança engatinhando, embaixo da mesa, deitada, parcialmente ocluída | ~2.000 quadros com caixas anotadas | recall e precisão @IoU 0,5, **por postura e oclusão** | detector |
| **T6** | **tracking e identidade** | ByteTrack × BoT-SORT × DeepStream MV3DT | ~10 trechos contínuos de 15 min com identidade anotada | **trocas de ID por criança-hora**, IDF1, HOTA | tracker; **se trocas/criança-hora passam do limiar, etiquetas UWB viram obrigatórias** |
| **T7** | etiquetas UWB/BLE | posição da etiqueta × posição pela visão; % do tempo que a criança mantém a etiqueta; conversa de aceitação com famílias | visão + observação | erro em cm; % de uso; objeções | adotar ou não |
| **T8** | pose corporal | RTMPose × MMPose WholeBody destes ângulos | ~500 quadros com keypoints anotados | PCK@0,2 **por postura** (em pé, sentada, agachada, deitada) | modelo; quais posturas são confiáveis |
| **T9** | mãos | MediaPipe Hands × RTMPose Hand em crops na distância real | ~500 crops com landmarks anotados | erro normalizado; **taxa de detecção confiante por tamanho de mão em px** | viabilidade de análise de mão por tipo de câmera → alimenta T1 |
| **T10** | rosto e AUs | OpenFace / py-feat ou equivalente em crianças destes ângulos | codificador treinado em FACS avalia presença e intensidade de AUs numa amostra | % de quadros com rosto utilizável; ICC por AU | viabilidade; posição das câmeras baixas |
| **T11** | materiais | ~20 materiais anotados (incluindo confundíveis), YOLO pequeno treinado; **AprilTag na base** dos mesmos materiais | anotação | mAP; matriz de confusão nos cubos adjacentes da Torre Rosa e nos blocos de cilindros; **taxa de leitura da etiqueta durante o uso** | tamanho do dataset necessário; etiquetar materiais ou não |
| **T12** | áudio: captação | array × microfone individual | fala marcada à mão | SNR por posição na sala; acurácia de VAD | estratégia de microfones |
| **T13** | áudio: atribuição | VTC (tipo de falante), pyannote/NeMo (diarização), **atribuição áudio-visual usando as posições da visão** | ~1 h com falante atribuído à mão | acurácia de tipo de falante; DER; **acurácia de atribuição** | quais métricas de linguagem saem da coluna "condicionado" |
| **T14** | áudio: ASR | Whisper zero-shot × ajustado em fala infantil | 30–60 min de fala infantil transcrita à mão (mic individual) | **WER por faixa etária** | se alguma métrica lexical é viável; desbloqueia ou mantém `mlu` bloqueada |
| **T15** | sensor de soneca | radar × colchonete × actigrafia por vídeo | **observador humano** registra início do sono, despertar e surtos de movimento (padrão da área) | concordância de início/fim em minutos; concordância sono/vigília por época | sensor |
| **T16** | armazenamento e vazão | gravar todos os canais um dia inteiro no bitrate-alvo; gerar proxy; rodar o pipeline candidato inteiro de madrugada | — | quadros perdidos; GB/dia real; **horas de processamento por hora gravada** — um dia processa em < 12 h? | dimensionamento de hardware e bitrate |
| **T17** | determinismo | rodar o mesmo dia duas vezes | a própria saída | % de saídas idênticas; desvio máximo por métrica | quais módulos precisam de semente/modo determinístico; limiar de aceitação (Parte IV §1.12) |
| **T18** | ferramenta de anotação | CVAT × Label Studio nas tarefas reais: caixas, keypoints, eventos temporais | cronômetro | **minutos de anotador por minuto de vídeo, por tipo de tarefa** | ferramenta; e o orçamento real de tempo humano (§1.11) |
| **T19** | **protocolo de codificação humana** | dois codificadores codificam as mesmas 2 h com o protocolo-rascunho: work episodes, interrupções, distress, uso não-canônico | um ao outro | **kappa / ICC por variável** | iterar o protocolo até concordância aceitável **antes** de qualquer automação mirar nele |
| **T20** | consentimento | apresentar os termos a 3–5 famílias e às educadoras | questionário curto de compreensão; objeções | compreensão; o que é recusado | redação final; **quais tipos de dado são aceitos** |
| **T21** | efeito do observador | *(planejado aqui, executado após a instalação)* semana 1 × 4 × 12 nas mesmas métricas | a própria série | estabilização | quantas semanas iniciais descartar por protocolo |

### Ordem e dependências

```
semana 1   T1 T2 T3 T4 T16 T20          ← decisões de captura + consentimento; nada depende de modelo
           T19 começa (protocolo humano, sem GPU)
semana 2   T5 → T6 (+T7 em paralelo)     ← precisam do vídeo gravado; T6 é o teste decisivo
           T12 → T13 → T14               ← precisam do áudio gravado
           T15                           ← precisa das sonecas gravadas
semana 3   T8 T9 T10 T11                 ← rodam sobre o mesmo vídeo, depois de T5
           T17 T18                       ← sobre tudo o que rodou
           T19 fecha; T21 planejado
```

### Critérios de saída da Fase 0

Nenhuma câmera definitiva é comprada antes de existir, por escrito:

1. **Relatório por teste** com a métrica medida e a decisão tomada
2. **Especificação de captura assinada:** modelo, resolução, lente, posição e altura de cada
   câmera; microfones e posições; sensor de soneca; etiquetas sim/não; sincronização; UPS
3. **Termo de consentimento iterado** com as famílias e a equipe, e a lista do que foi aceito
4. **Protocolo de codificação humana** com concordância medida e aceitável
5. **Dimensionamento de hardware** a partir de T16 (GPU, disco, rede)
6. **Variância intra-criança dos dias de piloto** → análise de poder → **quais hipóteses H1–H7
   ficam no confirmatório** e quais vão para o exploratório antes do pré-registro (§1.14)

O que falhar aqui custa semanas. O que falharia depois custaria o arquivo.

## 3. Conjunto inicial de variáveis — mais é melhor, organizado por quando fica confiável

**Regra de leitura (R1):** tudo o que a captação permite é **observado e guardado desde o dia 1**.
"Por onde começar" não é uma lista curta de variáveis — é a **ordem em que cada grupo é validado
e promovido a indicador**. Essa ordem segue a cadeia de dependência e a prontidão de validação,
**não** a importância. Sono e log de contexto são o exemplo: baratos, sem GPU, e por isso
primeiros — não porque importam menos ou mais.

O dicionário completo, com ~120 variáveis, definição operacional, fonte, validação e camada de
cada uma, está em **[`dicionario-variaveis.md`](dicionario-variaveis.md)**. Aqui, só a estrutura:

| Camada | Quando valida | Grupos | Por que nesta ordem |
|---|---|---|---|
| **0 — qualidade e contexto** | mês 1 | observabilidade por criança · uptime · deriva · resíduo de calibração · presença · log de contexto · **diário de sono** | são as covariáveis sem as quais **nada** do que vem depois se interpreta; e as únicas que não dependem de nenhum modelo |
| **A — espaço, social, sono** | mês 3–6 | trajetória · postura grossa · áreas · proximidade · grupos · preferência entre pares · sono completo | derivam de posição + identidade, que é o primeiro módulo validado; robustas, baratas, densas |
| **B — atividade e adulto** | mês 6–12 | work episodes e tudo que deriva deles (inclusive **persistência após erro e frustração**, que não precisam de rosto) · uso de materiais · repetição · **comportamento do adulto** | dependem de detecção de material sobre identidade validada; é onde nasce a métrica de concentração |
| **C — motor fino, áudio, afeto, criatividade-substrato** | ano 2 | mãos · detalhe de pose · atribuição de falante · prosódia · AUs · distress e recuperação · uso não-canônico · combinação de materiais | dependem de resolução, de áudio validado localmente e de camadas anteriores estáveis |
| **D — derivadas de corpus** | ano 2–3 | raridade de ação · difusão de invenção · `mlu` se desbloqueada | matematicamente exigem história acumulada |

**Onde concentrar esforço de validação nos primeiros 6 meses:** camadas 0 e A inteiras, e o
protocolo humano da camada B (T19). Isso já dá algo em torno de 45 variáveis promovidas no
primeiro semestre — enquanto as ~120 são observadas desde o primeiro dia.

Três observações:

**Camada 0 é a novidade desta revisão.** Nenhuma variável de qualidade estava no dicionário
anterior. Sem `child_observability_frac`, um dia atrás da estante vira um dia parado.

**A camada B contém as duas variáveis emocionais mais defensáveis do projeto** — persistência
após erro e razão de abandono por frustração — e elas chegam **um ano antes** do resto do bloco
afetivo, porque saem do work episode sem nenhuma análise de rosto.

**O dicionário é um artefato vivo e versionado** (Parte III §3): toda variável entra com
definição operacional, unidade, fonte, regra de valor ausente e método de validação, e ganha
`definition_version` quando a definição muda. É o documento que o protocolo de codificação humana
implementa e que a automação depois reproduz.

## 4. Alterações decorrentes ao plano de execução

O §13 da Parte III foi atualizado em consequência desta revisão:

- **Fase 0 — bancada** inserida antes do mês 1, com os 21 testes do §2 e seus critérios de saída
- **Mês 0** ganha as três ontologias (materiais, sala, dia), a especificação de câmeras como
  entregável explícito, e a análise de poder antes do pré-registro
- **Mês 1–3** ganha fiduciais fixos, verificação diária automática de calibração e sincronização,
  UPS e gravação redundante, e as variáveis de camada 0
- **comportamento do adulto** entra na fase de atividade (mês 6–12), desenhado com a equipe
- **re-enrolamento de aparência** e gestão de coorte entram como tarefa contínua

---

## Anexo — Dicionário de variáveis

O dicionário foi movido para arquivo próprio, porque cresceu para ~135 variáveis e é um artefato
vivo, versionado à parte: **[`dicionario-variaveis.md`](dicionario-variaveis.md)**.

Estrutura: dez grupos (qualidade e presença · sono · trajetória e espaço · social · atividade ·
motor fino · motor grosso · linguagem · substrato emocional · substrato de criatividade · adulto),
cada variável com nível, fonte, definição operacional, validação e **camada** — quando é validada
e promovida a indicador (Parte IV §3). Nível 3 fecha o arquivo como constructos derivados, nunca
como variável medida.
