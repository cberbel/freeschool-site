# Análise crítica — sugestões do Grok sobre arquitetura

- **Material analisado:** [`2026-08-29-grok-arquitetura.md`](2026-08-29-grok-arquitetura.md)
- **Data:** 2026-08-29
- **Escopo:** deliberadamente **sem camada jurídica/LGPD**, a pedido. Só engenharia:
  o que funciona, o que não funciona, e o que fazer no lugar.
- **Status:** `EM ANÁLISE` — este arquivo é opinião, não decisão tomada.

---

## Veredito em uma linha

O Grok entregou uma **arquitetura de dados competente para um problema de medição** —
e problema de medição não se resolve com pipeline. Do "captação" ao "dashboard" está
tudo razoável e nada está errado o suficiente pra jogar fora; mas a pergunta que decide
o projeto ("o que esse número significa e como eu sei que ele está certo?") não aparece
uma única vez no texto. É um projeto de MLOps onde deveria haver um projeto de
psicometria com MLOps em volta.

---

## O que ele acertou (e vale manter)

1. **Híbrido edge + cloud.** Certo, e pelo motivo certo — só que ele não fez a conta que
   prova. Veja [As contas que ele não fez](#as-contas-que-ele-não-fez): 6 câmeras 4K dão
   ~216 GB/dia. Subir isso é inviável de banda e caro de armazenar. Edge não é
   preferência, é aritmética.
2. **Separar vídeo bruto (retenção curta) de features (retenção longa).** Certo — mas
   colide com outra recomendação dele, ver [P8](#p8--embeddings-e-apagar-o-vídeo-são-incompatíveis-como-ele-descreveu).
3. **Gravar a versão do modelo junto com cada predição.** Esse é o melhor item do texto
   inteiro e ele passa batido, como se fosse detalhe de schema. É a semente da trilha de
   auditoria da medida. Eu estenderia: versão do modelo **+ versão da calibração +
   versão do código de features + o vetor de features cru**, pra que qualquer score
   histórico possa ser recalculado.
4. **Embedding por sessão pra comparação longitudinal e clustering.** Ideia boa e
   subestimada no texto. Tem uma armadilha séria embutida (P8).
5. **Começar por 3–4 dimensões, não por "tudo".** Certo, e eu iria além: **comece por
   uma.** Ciclo de trabalho / engajamento. As outras três saem quase de graça depois que
   essa estiver instrumentada.
6. **Python.** Não há discussão, e não era uma decisão difícil.

---

## O furo central: falta a camada de medição

Quatro buracos que, juntos, são o projeto inteiro.

### 1. Não existe definição operacional

"Concentração" não é observável. O que é observável é *tempo contínuo orientado a um
material, com movimento de precisão, sem redirecionar atenção a eventos externos*. O
salto de proxy → score → "desenvolvimento" é exatamente onde o projeto vive ou morre, e
o texto pula esse salto.

**Opção:** escrever o **codebook antes de qualquer linha de modelo**. Não precisa
inventar: a escala de envolvimento de Leuven (LIS-YC, Laevers) é um instrumento de 5
pontos, validado, usado há décadas em educação infantil, e mede *exatamente* o construto
"engajamento/concentração". Adotar um instrumento existente como rótulo dá três coisas
de graça: definição pronta, treinamento de observador pronto, e — o mais importante
comercialmente — a possibilidade de dizer "nosso score concorda X% com um instrumento
aceito", que é a diferença entre uma medida e um gadget. O vocabulário Montessori
(ciclo de trabalho, polarização da atenção, repetição, normalização) entra como camada
própria por cima.

### 2. Não existe rótulo, nem confiabilidade entre observadores

"Validação humana forte" é hand-waving. Não diz o que é um rótulo, quem produz, em que
unidade (frame? clipe? sessão? dia?), nem como se mede se dois adultos concordam.

**Opção:** unidade de rótulo = **clipe de 3 minutos**. Duas professoras pontuam o mesmo
lote de ~100 clipes; mede-se **kappa de Cohen / ICC**. Se as humanas não passarem de
~0,6, o construto está mal definido e você conserta o codebook antes de treinar
qualquer coisa. E o número do acordo humano vira o **teto** do modelo: modelo que
concorda 0,55 com humanas que concordam 0,60 entre si é um modelo *bom*, e sem esse
denominador você não sabe disso.

### 3. Não existe invariância no tempo — e aí a curva longitudinal mede o modelo

Esse é o mais perigoso, porque falha em silêncio e bonito. Você troca uma câmera,
retreina o modelo, muda o layout da sala, chega o inverno e as crianças vestem casaco —
e a "curva de desenvolvimento" sobe. Ela subiu porque a criança se desenvolveu ou porque
o v3 é mais sensível que o v2? Sem resposta, o ativo longitudinal vale zero.

**Opção:** **golden set congelado** — algumas centenas de clipes com rótulo de consenso,
que **toda versão de modelo re-pontua**. Se o v3 dá +0,4 no golden set, esse delta é do
modelo e é subtraído da série histórica. É calibração por âncora, é barato, e é o que
transforma "temos dados de 3 anos" em "temos uma série comparável de 3 anos".

### 4. Não existe separação criança × contexto

Engajamento no dia 200 é maior em parte porque a criança cresceu, em parte porque ela
pegou um material mais fácil, em parte porque era 9h e não 16h, em parte porque a
professora nova é mais calma. Média por criança por semana mistura tudo isso e mede
principalmente a **agenda da escola**.

**Opção:** a camada longitudinal não é "transformer em série temporal" — é **modelo
misto / traço latente**: efeito aleatório por criança (o que você quer), efeitos fixos
ou aleatórios para material, sala, horário, professora, dia da semana. É estatística de
1990, roda em segundos, é interpretável, e é o único jeito de responder "a criança
mudou" em vez de "a segunda-feira é pior".

---

## Problemas específicos

### P1 — Identidade: "YOLO + ByteTrack" não te dá a Maria

Tracker dá *tracklet*, não criança. Numa sala Montessori com 20 crianças pequenas,
oclusão por prateleira, criança engatinhando, saindo e voltando ao quadro, os IDs
fragmentam dezenas de vezes por hora. E o produto inteiro depende de atribuir um ciclo
de trabalho de 40 minutos a *uma* criança nomeada. Re-ID visual clássico é treinado em
adultos com roupa distinta; criança pequena de avental/uniforme, vista de cima e a 5m,
é o pior caso possível.

**Opção (a mais importante deste documento): inverta o papel da visão.**

- **UWB (banda ultralarga) como âncora de identidade e posição.** Tag na sapatilha ou no
  avental, 3–4 âncoras por sala, precisão de ~10–30 cm. Resolve *quem* e *onde* de forma
  determinística, sem modelo, sem drift, sem re-ID. (BLE/RSSI não serve: erro de 2–5 m
  não distingue dois tapetes vizinhos.)
- **RFID/NFC nos materiais, leitor na prateleira.** Tag sai do campo = material foi
  retirado; volta = foi devolvido. Isso te dá, sem nenhuma visão computacional:
  qual material, por quanto tempo, em que sequência, **repetição** (o sinal Montessori
  por excelência) e **devolução à prateleira** (cuidado com o ambiente / ciclo completo).
- **Pareamento:** o leitor da prateleira diz *o quê* e *quando*; o UWB diz *quem estava
  ali naquele instante*. Ciclo de trabalho completo, com nome, sem uma linha de CV.

A visão passa a responder só a pergunta difícil e que só ela responde: **como o corpo
está fazendo** (postura, precisão, orientação da cabeça, afeto). É uma pergunta muito
mais fácil quando você já sabe quem é e onde está.

**Bônus que quase ninguém percebe:** o hardware instrumentado vira **ground truth
automático do sistema de visão**. Você mede a acurácia do seu tracker contra as tags,
todo dia, de graça, sem rotular nada à mão.

### P2 — "Tempo parado concentrado" inverte a pedagogia

Ele sugere isso explicitamente como heurística de fase 1. Em Montessori é uma métrica
**invertida**:

- Criança polindo, varrendo, carregando bandeja, indo e voltando da prateleira — vida
  prática — está profundamente engajada **e se movendo o tempo todo**.
- Criança dispersa, "flutuando" ou olhando o vazio, está **parada**.

Uma métrica de imobilidade pontua vida prática como desatenção e premia zonear. Não é
bug de ajuste, é o sinal com o sentido trocado.

**Opções melhores, em ordem de custo:**

- **Orientação da cabeça em relação ao objeto de trabalho** (não olhar — pose de cabeça
  basta e é robusta). Muito melhor proxy que imobilidade.
- **Resistência à distração — a melhor ideia deste documento depois do UWB.** Detecte o
  evento ambiental (bandeja caindo, porta abrindo, alguém entrando) e meça se e em
  quanto tempo a cabeça da criança vira. É quase um experimento com estímulo natural,
  tem controle embutido (todas as crianças da sala receberam o mesmo estímulo no mesmo
  instante) e é infinitamente mais defensável que qualquer contagem de segundos parados.
- **Persistência após erro:** a torre caiu, a peça não encaixou — a criança recomeça ou
  abandona? Detectável por eventos do material + retomada.
- **Repetição:** mesma criança, mesmo material, N vezes seguidas. Puro RFID.
- **Autonomia:** criança escolhe e conclui com adulto a >2 m. O UWB do adulto te dá isso
  de graça, e é uma das 4 dimensões que ele listou.

### P3 — Feature Store / Feast: over-engineering claro

Feast existe pra resolver *train/serve skew* em serving online de alta vazão, entre
times. Aqui: uma escola, ~50 crianças, inferência em lote, talvez 10 mil linhas de
feature por dia. Feast adiciona registry, store online (Redis) e manutenção, com
benefício zero.

**Opção:** Postgres + views materializadas + snapshot em Parquet pra montar conjunto de
treino + DuckDB pra análise. Reavaliar Feast só se um dia houver N escolas com serving
online — e aí a decisão será outra e com dados na mão.

### P4 — Não jogue keypoint bruto no Postgres

Ele mistura "features" num balaio só. Keypoint de pose é ~4,3 milhões de linhas por dia
(conta abaixo) — 1,5 bilhão de linhas/ano. Postgres aguenta com particionamento, mas
você vai pagar caro em índice, vacuum e backup por um dado que nunca é consultado linha
a linha.

**Opção:** duas camadas, explicitamente.
- **Frio/volumoso:** keypoints e tracks em **Parquet particionado por dia/sala** no
  object storage. Lido por DuckDB pra treino e análise.
- **Quente/consultável:** só o **agregado por sessão** (uma linha por criança × material
  × sessão, com features, score, versão, rótulo humano) no Postgres. É isso que o
  dashboard consulta, e cabe em memória por anos.

Sobre TimescaleDB: cuidado antes de desenhar em cima. A build Apache que plataformas
gerenciadas costumam oferecer não inclui compressão nem continuous aggregates — que são
justamente os dois motivos pra querer Timescale. **Confirmar a disponibilidade real na
plataforma escolhida antes de assumir.** Com a separação acima, provavelmente você nem
precisa.

### P5 — YOLOv8/YOLOv11 é AGPL-3.0 (e você quer licenciar)

O texto termina o roadmap em "versão licenciável" e recomenda Ultralytics no meio do
caminho. Ultralytics YOLOv8/v11 é **AGPL-3.0**: uso comercial fechado exige licença
comercial paga da Ultralytics. Passa despercebido no protótipo e vira problema exatamente
no item 6 do roadmap dele.

**Opção:** ou orça a licença comercial desde já, ou usa detector com licença permissiva
— **YOLOX (Apache-2.0)**, família **RT-DETR**, ou modelos do **MMDetection (Apache-2.0)**.
Para pose, **RTMPose/MMPose (Apache-2.0)** e **MediaPipe (Apache-2.0)** já são
permissivos. Decidir isso agora custa uma tarde; decidir depois custa refazer o pipeline.

### P6 — Modelo de pose não foi treinado em criança de 3 anos

COCO é adulto. Proporção de criança pequena é outra (cabeça ~1/4 da altura vs ~1/7 no
adulto), e os keypoints degradam — justo quando a criança está agachada, de bruços no
tapete ou de costas, que é a metade do dia numa sala Montessori.

**Opção:** rotular algumas centenas de frames próprios e fazer fine-tune do modelo de
pose. É trabalho chato de 2–3 semanas — **e é um ativo real**: um modelo de pose ajustado
para crianças de 2–6 anos em ambiente Montessori não existe pronto, e é bem mais difícil
de copiar do que qualquer dashboard.

### P7 — As fases 2 e 3 apontam para o lugar errado

- "Fine-tuning de ViT/ConvNeXt" trata o problema como classificação de **imagem**. O
  construto é **temporal**: engajamento é o que acontece ao longo de minutos.
- "Self-supervised na fase 3" pressupõe volume que uma escola com 50 crianças **nunca**
  vai ter. SSL do zero precisa de escala industrial.

**Opções:**
- **Modele sobre keypoints e tracks, não sobre pixels.** Um transformer pequeno ou
  ST-GCN sobre sequência de keypoints é ~100× mais barato, muito mais robusto a
  iluminação e troca de câmera, e — o argumento que importa pro licenciamento —
  **transfere pra outra escola**, porque esqueleto normalizado é quase invariante a
  câmera e a sala. Modelo de pixel aprende a *sua* sala.
- **Se quiser sinal visual, use backbone SSL pré-treinado congelado** (DINOv2/v3) como
  extrator, em vez de treinar SSL. Você fica com o benefício sem precisar do volume.
- **VLM como rotulador (o atalho que ele não considerou).** Um modelo de visão-linguagem
  atual pré-rotula os clipes ("essa criança está engajada com um material? qual?"), e a
  professora **corrige** em vez de criar do zero — na prática 3× mais rápido por clipe.
  Nunca como a medida final (não é auditável e muda debaixo de você), só como
  amplificador de rótulo. Variante elegante: renderize um **stick figure a partir dos
  keypoints + caixas dos objetos** e mande *isso* pro VLM em vez do vídeo — nada
  identificável sai do prédio, e para julgar "engajado × vagando" o esqueleto costuma
  bastar. Perde afeto facial; testar antes de confiar.

### P8 — "Embeddings" e "apagar o vídeo" são incompatíveis como ele descreveu

Contradição que ele não percebeu. Embedding só é comparável **dentro da mesma versão de
modelo**. Quando você treina o v3, o espaço vetorial muda e o histórico inteiro perde o
sentido. A solução padrão é **re-embedar o histórico** com o modelo novo — e o histórico
é vídeo, que ele mandou apagar em 30 dias. Ou seja: no dia em que você melhorar o
modelo, perde a comparabilidade longitudinal, que é o ativo do projeto.

**Opção:** **corpus dourado permanente** — algumas centenas de clipes selecionados
(cobrindo idades, materiais, salas, estações do ano, níveis de engajamento) guardados
**indefinidamente**, separados do fluxo geral. Toda versão nova re-embeda e re-pontua
esse corpus. Serve de âncora de calibração (item 3), de conjunto de regressão e de
memória do projeto. O resto do vídeo continua com retenção curta, sem prejuízo.

### P9 — A stack de aplicação ignora o que você já roda

FastAPI + React/Next não está errado, mas você já tem **Supabase (que é Postgres) +
páginas estáticas em HTML/JS puro** funcionando em produção (`dashboard/`, `estudio/`).
Adotar FastAPI + React é manter uma segunda stack, sozinho, pra ganhar o quê?

**Opção:** Supabase continua sendo o banco, auth, storage e realtime. As telas seguem o
padrão que já existe. **Python entra onde ele é insubstituível** — o worker de edge, que
é Python de qualquer jeito, escrevendo no Supabase via client. FastAPI só quando aparecer
um endpoint pesado de verdade. Uma stack a menos pra manter é literalmente semanas de
vida por ano.

### P10 — "Câmeras de boa qualidade, posicionamento estratégico" não é uma decisão

Faltam os três parâmetros que definem custo e viabilidade:

- **Resolução:** 4K é necessário mesmo, e não por capricho — criança a 5 m em 1080p tem
  ~150 px de altura e as **mãos** (que é onde a manipulação do material acontece) somem.
- **FPS:** 5 fps basta pra engajamento e postura. Ninguém precisa de 30. É um corte de
  6× em compute e storage, e é a decisão de maior alavancagem da camada de captação.
  Detecção a 1–2 fps com interpolação de tracking economiza mais ainda.
- **Ângulo:** teto puro (top-down/fisheye) resolve oclusão mas **quebra os modelos de
  pose**, todos treinados em vista frontal/oblíqua — e ainda exige de-warping. Use
  **duas câmeras oblíquas por sala, a ~2,5–3 m, com campos sobrepostos**: a oclusão de
  uma é coberta pela outra, e a sobreposição te dá um teste-reteste de graça (ver P11).
- **Hardware de edge:** não faça um Jetson por câmera. **Um micro com GPU de consumo por
  escola** (uma 3060/4060 dá conta de 6 streams a 5 fps) sai mais barato por stream, é
  muito mais fácil de desenvolver e de manter, e você troca a placa em vez do parque.

### P11 — Nenhum plano de avaliação

O texto não diz uma palavra sobre como você sabe que o sistema funciona. É a omissão que
mais assusta, porque garante 6 meses de trabalho com número bonito e sem sentido.

**Opção — as quatro regras mínimas:**

1. **Split por criança E por dia.** Split aleatório vaza: o modelo decora a camiseta da
   Maria e você comemora 0,95. Teste com **crianças que ele nunca viu**, em **dias que
   ele nunca viu**.
2. **Reporte contra o teto humano**, não contra 100%. Kappa modelo-humano dividido por
   kappa humano-humano.
3. **Teste-reteste de graça:** mesma criança, mesmo instante, **duas câmeras
   sobrepostas**. A diferença entre os dois scores é ruído puro do sistema. Se ela for
   da ordem do efeito que você quer detectar, o sistema não mede nada — e é melhor
   descobrir na semana 4.
4. **Regressão a cada versão** contra o golden set congelado, com o delta registrado.

---

## As contas que ele não fez

Ordem de grandeza, premissa: 3 salas × 2 câmeras = 6 streams, 8 h/dia.

**Vídeo bruto (4K, H.265, ~10 Mbps):**

| Item | Valor |
| --- | --- |
| Por dia | 6 × 10 Mbps × 28.800 s ≈ **216 GB/dia** |
| Retenção 30 dias | **~6,5 TB** |
| Custo em nuvem (~US$0,023/GB/mês) | **~US$150/mês** só de storage, fora egress |
| Custo local | 2 HDDs de 8 TB ≈ **US$300, uma vez** |
| Upload contínuo exigido | **60 Mbps sustentados, 8 h/dia** |

→ A conclusão "edge" não é preferência arquitetural, é a única saída. E "retenção curta"
é decisão de custo antes de qualquer outra coisa.

**Features (keypoints):**

| Item | Valor |
| --- | --- |
| Person-frames/dia | 6 cams × 5 fps × 28.800 s × ~5 pessoas ≈ **4,3 M** |
| Bruto (17 kp × 3 × 4 bytes) | ~880 MB/dia |
| Parquet + zstd + int16 | **~100–180 MB/dia → ~40 GB/ano** |
| Em linhas de Postgres | ~1,5 **bilhão** de linhas/ano |

→ Confirma P4: feature é barata em Parquet e cara em tabela.

**Rótulos — o recurso realmente escasso:**

| Item | Valor |
| --- | --- |
| 1 h/dia de professora, clipe de 3 min a ~1,5 min de avaliação | ~40 clipes/dia |
| Mês letivo (20 dias) | **~800 clipes/mês** |
| Necessário pra um classificador de engajamento em 5 níveis começar a funcionar | ordem de **2.000–5.000** clipes |
| Prazo | **3–6 meses de rotulagem contínua** |

→ E é por isso que o roadmap dele está na ordem errada: rotulagem é o item **4 de 6**
dele, e é a **restrição de maior lead time do projeto inteiro**. Cada mês que você
adia a rotulagem é um mês adiado no fim. Com pré-rotulagem por VLM + amostragem ativa
(só mandar pra humana o clipe em que o modelo está incerto ou em que dois modelos
discordam), dá pra cortar isso substancialmente.

**Hardware (ordem de grandeza, conferir preço real):**

| Item | Estimativa |
| --- | --- |
| 6 câmeras PoE 4K | R$ 4–6 k |
| Switch PoE + cabeamento | R$ ~2 k |
| Micro de edge com GPU | R$ 6–9 k |
| UWB (3–4 âncoras × 3 salas + ~50 tags) | US$ 1,5–3 k |
| Leitor UHF RFID por estante + tags passivas | US$ 300–800/leitor, tags em centavos |

---

## Roadmap alternativo

O dele: captação → pose → dashboard → validação humana → feature store → licenciável.
Problema: **6+ meses antes de alguém na escola receber qualquer valor**, e nenhum rótulo
até a etapa 4.

Proposta, reordenada por *lead time* e por *risco*:

1. **Observação digital no tablet (semana 1–4, zero ML).** A professora Montessori já
   observa e já registra — é a prática central do método. Digitalize esse registro com
   escala estruturada (LIS-YC + campos Montessori). Entrega valor imediato, **produz o
   rótulo desde o dia 1**, não tem risco técnico, e faz a equipe querer o resto. Também
   é o que dá legitimidade interna pra pendurar câmera no teto depois.
2. **Instrumentação do ambiente (mês 2–3).** RFID de retirada/devolução na prateleira +
   UWB de identidade. Ciclo de trabalho, repetição, devolução, autonomia — **métricas
   objetivas com zero visão computacional**. Se o projeto parar aqui, já é um produto.
3. **Câmeras + tracking (mês 4–6),** validados contra as tags. Ground truth de graça.
4. **Modelo de engajamento** treinado nos rótulos acumulados desde o mês 1, com
   amostragem ativa.
5. **Camada longitudinal** (modelo misto, âncoras, invariância, curvas de crescimento).
6. **Multi-escola / licenciável** — e note que só o passo 5 produz algo licenciável de
   verdade; os passos 1–4 qualquer bom time replica em um trimestre.

---

## Decisões: dele × minha

| Decisão | Grok | Minha | Por quê |
| --- | --- | --- | --- |
| Edge vs Cloud | Híbrido | **Híbrido** | Concordo — a conta de 216 GB/dia fecha o assunto |
| Fonte primária | Visão computacional | **Tags (UWB + RFID); visão como camada 2** | Identidade determinística; visão só pra "como o corpo faz" |
| Materiais instrumentados | "Opcional e poderoso" | **Obrigatório, e primeiro** | Maior sinal por real gasto do projeto inteiro |
| Proxy de concentração | Tempo parado | **Orientação de cabeça + resistência à distração + repetição** | Imobilidade inverte a pedagogia |
| Feature Store | Feast | **Postgres + Parquet + DuckDB** | Feast resolve problema que você não tem |
| Keypoints | Junto das features | **Parquet frio; só agregado no Postgres** | 1,5 bi de linhas/ano |
| Detector | YOLOv8/v11 | **YOLOX / RT-DETR / MMDet (Apache-2.0)** | AGPL colide com "versão licenciável" |
| Modelo de comportamento | Fine-tune ViT/ConvNeXt | **Temporal sobre keypoints (ST-GCN / transformer pequeno)** | Barato, robusto, e transfere de escola |
| Fase 3 | Self-supervised próprio | **Backbone SSL pré-treinado congelado** | Volume de uma escola nunca chega lá |
| Rotulagem | Etapa 4 de 6 | **Etapa 1, antes de qualquer ML** | É o maior lead time do projeto |
| Instrumento de rótulo | (ausente) | **LIS-YC/Leuven + codebook + kappa** | Sem isso não existe medida, só número |
| Longitudinal | Transformer temporal | **Modelo misto / traço latente + golden set** | Separa criança de contexto; interpretável |
| Backend/Front | FastAPI + React | **Supabase + o padrão de páginas que já roda** | Uma stack a menos pra manter sozinho |
| Avaliação | (ausente) | **Split por criança e por dia; teto humano; teste-reteste por câmeras sobrepostas** | Sem isso, 0,95 de acurácia não quer dizer nada |

---

## O que eu não sei — e que só um piloto responde

Honestidade sobre os limites desta análise:

1. **UWB funciona mesmo com criança de 3 anos?** A tag tem que sobreviver a queda,
   água, boca e desinteresse. Precisa de teste de campo com 5 crianças por 2 semanas
   antes de comprar 50.
2. **RFID de prateleira consegue distinguir "retirado" de "criança passou perto"?**
   Depende de antena, potência e geometria da estante. Testar com uma estante antes de
   equipar três salas.
3. **Qual o kappa humano-humano real** da sua equipe na escala de envolvimento? Se for
   0,4, o construto precisa ser reescrito antes de qualquer modelo. **Esse é o teste mais
   barato e mais decisivo de todos — dá pra fazer em uma tarde, com dois tablets e nenhum
   hardware novo. Faça esse primeiro.**
4. **O stick figure preserva sinal suficiente** pra um VLM julgar engajamento? Uma tarde
   de teste responde.
5. **Quanto o modelo de pose degrada em criança pequena** de fato, no seu ângulo de
   câmera. Só medindo.
6. **Se o efeito de desenvolvimento é maior que o ruído do sistema.** Essa é a pergunta
   que mata ou salva o projeto, e nenhuma arquitetura — a dele ou a minha — responde
   antes do piloto.
