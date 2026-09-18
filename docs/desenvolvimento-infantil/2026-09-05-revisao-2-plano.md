# Revisão 2 — plano de IA, arquitetura, ferramentas, testes sem hardware e compras

- **Data:** 2026-09-05
- **Revisa:** [`2026-08-29-passo-a-passo-sistema.md`](2026-08-29-passo-a-passo-sistema.md) e
  [`2026-08-29-analise-grok-arquitetura.md`](2026-08-29-analise-grok-arquitetura.md)
- **Status:** `EM ANÁLISE` — proposta; nada aqui é decisão tomada.
- **Revisão 2.1 (06/09):** a terceira rodada do painel terminou; erratas e adendos na seção
  [Revisão 2.1](#revisão-21--o-que-o-crítico-de-completude-acrescentou-0609), perto do fim. **Onde
  houver conflito, vale a 2.1** — em especial: são **2 avaliadoras**, não 3.
- **Escopo:** só engenharia. Camada jurídica fora, a pedido.

---

## A meta mudou, e isso reorganiza tudo

O dono redefiniu o alvo nesta rodada: **monitorar todo o desenvolvimento infantil, de modo
quase contínuo.** Não é observação amostrada de uma dimensão — é sensoriamento passivo, o dia
inteiro, todos os dias, cobrindo motor, linguagem, social, cognitivo, autonomia, autorregulação,
alimentação e sono, para ~47 crianças de 1 a 6 anos. A observação humana amostrada vira
**calibração**, não a medida.

Os documentos de 29/08 foram escritos para o regime amostrado. Esta revisão avalia cada um
contra a meta nova. O resultado, em uma frase: **as decisões estruturais sobrevivem (edge,
Parquet frio, golden permanente, versão por predição, codebook antes do modelo), mas a unidade
de tudo muda de "clipe ancorado numa entrada" para "janela criança × tempo", a ingestão vira
fundação em vez de detalhe, áudio das crianças entra como sensor obrigatório, e o VLM sai do
papel de medida.**

## Como esta revisão foi feita

Painel de agentes independentes, em quatro passos: (1) cinco revisores, um por dimensão, leram
os três documentos e o estado real do banco; (2) cada achado passou por um refutador com acesso
à web, tentando derrubá-lo em duas lentes — é factualmente verdade? faz sentido prático para um
construtor solo?; (3) um redator por dimensão escreveu a partir do que sobreviveu; (4) o crítico
de completude e o roadmap integrado ficaram por conta do editor na primeira publicação, porque o
painel foi cortado duas vezes pelo limite de uso; na terceira rodada o painel terminou, e o
resultado está na seção Revisão 2.1.

| Dimensão | Achados | Verificados | Mantidos | Seção escrita por |
| --- | --- | --- | --- | --- |
| Plano de IA e medição | 8 | 8 | 4 | painel |
| Arquitetura para fluxo contínuo | 8 | 8 | 5 | editor, a partir dos vereditos |
| Ferramentas para começar | 8 | 8 | 6 | editor, a partir dos vereditos |
| Como testar sem hardware novo | 8 | 8 | 2 | editor; achados 5–8 verificados na 3ª rodada (ver 2.1) |
| O que comprar de hardware | 8 | 8 | 2 | editor, a partir dos vereditos |

Uma nota de leitura: "refutado" quase nunca significou "o diagnóstico estava errado". Na maioria
dos casos o refutador confirmou a lacuna e derrubou a **prescrição** (número, produto, ordem ou
premissa). As seções abaixo usam a versão corrigida pelo refutador, não a original. Afirmações
de licença, preço, RTSP e capacidade que não puderam ser confirmadas (o proxy bloqueou
reolink.com, nvidia.com, lojas brasileiras e vários distribuidores) estão marcadas
**"não verificado"**. O apêndice lista achado por achado com o veredito.

---

## Correções de fato sobre o estado atual

O painel consultou o banco de novo em 05/09 e encontrou cinco premissas erradas nos documentos
de 29/08 — inclusive no contexto que este editor deu ao painel. Elas mudam o plano e ficam
registradas aqui antes de qualquer seção.

| Premissa de 29/08 | O que o banco mostra em 05/09 | Consequência |
| --- | --- | --- |
| "`meal_events`: já existe pipeline câmera→foto→IA em produção" | `meal_events` tem **0 linhas**; bucket `meal-photos` tem 0 objetos; `children` (a tabela que ele referencia) tem 0 linhas | Existe o **schema e o desenho**, não o fluxo em uso. "Alimentação já medida" vira "ativar sem compra e criar o golden". Nada pode ser "ligado por trigger" hoje |
| "17 câmeras em 10 espaços" | 17 vagas lógicas, **16 nomes únicos** ("sala MEIO" está nas duas salas); "Patio (Ângulo largo)" + "Patio (Rastreio)" batem com as duas lentes de **um** Reolink TrackMix | Provavelmente ~15 aparelhos físicos. Marca, modelo, RTSP, fps e ângulo não estão registrados para nenhum |
| "73 entradas, 40 transcritas — material para o kappa" | 75 hoje; 32 usam `sala = 'sala 1'`, chave que **não existe** em `salas_cameras`; as transcrições de 04/08 e 24/08 são quase todas **teste de microfone** ("testando, testando", "vou testar o corte") — 2 a 5 descrevem criança | Não há acervo rotulado para resgatar nem para o kappa. O kappa precisa de material **novo**, gravado pela captação contínua |
| "`observacao_indice` extrai pessoas com `aluno_id`" | 4 de 36 linhas têm alguma pessoa com `aluno_id`; 25 têm `pessoas = []` | O índice ainda não é produtor de evento por criança |
| "`registros_pedagogicos` e `planejamentos` modelam apresentação de material" | São texto livre (27 e 6 linhas hoje); **não existe catálogo de materiais** no schema | A tabela `materiais` (tag ↔ material ↔ área) tem de nascer do zero antes do RFID |

Outros fatos novos: a extensão `timescaledb` **não está disponível** no projeto (Postgres 17);
`pg_partman` 5.3.1 está disponível e `pg_cron` 1.6.4 já está instalado.
`observacao_entradas.relogio` é hora do **navegador** (sem default); 4 entradas têm `relogio`
anterior a `iniciada_em` da sessão, com offsets de −3 s a −70 s. As quatro colunas de segundos
de vídeo estão vazias em 75/75 linhas. A única sessão em modo `gravacao` é `pagina-teste`.

---

## 1. Plano de IA e de medição

### O que muda com a meta de monitoramento contínuo

- A unidade de tudo (rótulo, kappa, golden, avaliação de modelo, modelo longitudinal) deixa de ser "clipe de 3 min ancorado numa `observacao_entrada`" e passa a ser **janela fixa criança × tempo**: 2 min para o rótulo humano, 5 min para as features de sensor. Volume: 47 crianças × 96 janelas/dia × 20 dias ≈ **90 mil criança-janelas/mês**, contra ~1,5 entrada/criança/mês hoje (73 entradas em 24 dias).
- A medida contínua vem de **contagens de sensor** (RFID, UWB, áudio, pose) com custo marginal zero por janela; a observação humana vira **calibração de construto**; o VLM vira **rotulador amostrado**, nunca a medida (em regime contínuo ele custa ~40× o que a Etapa 4 calculou).
- Passam a existir **dois tipos de portão**: acurácia (sensor contra evento físico, validada com cronômetro em dois dias) e concordância (classificador contra codebook + kappa). O plano atual só tem o segundo.
- **Linguagem** entra como dimensão e é a única que exige áudio das crianças — o áudio de hoje (`observacao-audio`, 40 transcrições) é a voz da observadora ditando.
- O modelo longitudinal passa a ter de tratar **cobertura por sensor, dependência entre as 96 janelas do mesmo dia e drift físico** (câmera mexida, sala reorganizada) — nada disso está na Etapa 7.

### O que mantemos

- **Codebook antes de qualquer modelo**, com âncora comportamental ("o que se vê, não o que se sente"). Com 90 mil janelas/mês, construto mal definido vira ruído em escala industrial.
- **Kappa humano medido cedo (semana 3), cego, como denominador** de toda comparação modelo↔humano. Deixa de ser "teto global" (ver correção 3), mas continua sendo o número mais decisivo do projeto.
- **Corpus dourado permanente, fora do expurgo, repontuado a cada versão** — é o que torna comparável uma série de 3 anos quando pose, câmera e VLM mudam.
- **Versão do pipeline + versão do codebook em cada predição gerada por máquina**; a nota do modelo nunca sobrescreve a humana.
- **Detector/pose com licença permissiva** (não Ultralytics/AGPL). Modelo temporal sobre keypoints, não sobre pixels. Keypoints em Parquet, não em Postgres. A escolha concreta mudou — YOLOX está sem manutenção e MMPose só entra no contêiner de fine-tune; ver a seção 3, Ferramentas.
- **Split por criança E por dia; teste-reteste com duas câmeras sobrepostas; regressão por versão contra o golden.**
- **`meal_events` como padrão** de "observável concreto + evidência anexada + resultado estruturado" — com a ressalva de que hoje a tabela tem **0 eventos**: prova o desenho, não a execução nem a medida (ver acréscimo 4).
- **Supabase + páginas estáticas + worker Python de edge.** Nenhuma stack nova.
- **NÃO alterar `obs_avaliacoes` na Etapa 1**: continuam 3 dimensões (envolvimento, autonomia, persistência) até o kappa passar. `social` e `autorregulacao` entram como codebook v2 depois do portão da Etapa 2 — 5 sliders na semana 1 dilui o teste mais decisivo do projeto.

### O que corrigimos

**1. Unidade de rótulo e composição do golden (Etapas 1 e 3)**
- *Estava:* rótulo = clipe `[relogio − 90 s, relogio + 90 s]` recortado em torno de uma `observacao_entrada`; `obs_golden.entrada_id` referencia `observacao_entradas`; golden = 300–500 desses clipes.
- *Passa a ser:* tabela `dev_janelas` (DDL única na Revisão 2.1; `origem ∈ {entrada, sorteio, evento, corte}`, `presente boolean`). Job noturno sorteia janelas de **2 min por (sala, faixa horária)**, uniformes no dia — **não por criança**, porque a posição da criança num instante aleatório só existe a partir do UWB (Etapa 5); a avaliadora abre a câmera daquela sala naquele minuto, pontua todas as crianças visíveis e marca ausentes. Em `obs_avaliacoes`, `janela_id` obrigatório e `entrada_id` opcional; no modo vivo a janela nasce como registro de tempo no ato da entrada e o clipe é anexado depois pelo job de recorte — a Etapa 1 continua sem hardware e sem API. Regra do codebook: **nota holística da janela de 2 min conforme o próprio instrumento Leuven** (o nível que predominou/se sustentou); não adotar whole-interval (subestima duração) nem partial-interval (superestima) — são regras para ocorrência binária, não para escala ordinal. Golden = **300–500 janelas aleatórias (≥ 60% do total) + ~100 de `corte` + ≥ 10 blocos contínuos de ≥ 2 h** (manhãs inteiras das 18 crianças com autorização de imagem), para testar continuidade e fronteiras entre estados. Portão da Etapa 3: "golden fechado com ≥ 60% de janelas aleatórias e ≥ 10 blocos de ≥ 2 h". Orçamento: ~1 janela aleatória/criança/dia a ~1,5 min por janela ≈ 1,2 h/dia para 47 crianças, ≈ 30 min/dia para as 18 autorizadas; acima disso, pré-rotulagem (Etapa 4).
- *Por quê:* entradas `corte` são amostra de eventos escolhidos pela especialista (premissa a confirmar com elas), não de tempo; modelo calibrado só nelas não é validado nas transições, esperas e filas onde a medida contínua vive. LIS-YC é definida como nota de ~2 min de observação; janela curta amostrada uniformemente no tempo é o equivalente ao momentary time sampling, que estima prevalência sem os vieses do partial/whole-interval (Devine 2011; Cook & Snyder 2020).

**2. Papel e custo do VLM (Etapa 4)**
- *Estava:* "~800 avaliações/mês, Opus 5, clipe de 16 quadros ≈ US$ 40–60/mês … custo não importa nesta escala".
- *Passa a ser:* três papéis e um "nunca". (a) **Rotulador amostrado**: `claude-opus-5` + Batch + codebook em `cache_control` + saída estruturada, só sobre janelas de amostragem ativa + 10% aleatório — **2.000–4.000 janelas/mês ≈ US$ 120–245/mês** (16 quadros × 1.521 tokens × US$ 2,50/M); `claude-sonnet-5` como meio-termo (US$ 1/M em Batch → ≈ US$ 50–100/mês). (b) **Medida discreta verificável** no padrão `meal_events`, só para observáveis concretos com golden de imagens (foto antes/depois; material devolvido no lugar; cama arrumada pós-sesta) — nunca para construtos. (c) **Sintetizador de texto** para o parágrafo pedagógico da Etapa 7 a partir das features da semana, nunca a partir de vídeo. **Nunca**: identificar criança (a doc de Vision confirma que Claude recusa nomear pessoas — isso é UWB), pontuar todas as janelas do dia, ou produzir número que entre no modelo longitudinal sem passar por `obs_avaliacoes`. Pipeline **deve redimensionar cada quadro para lado maior ≤ 1.092 px** antes de enviar. Trocar a frase do doc por: "custo não importa a ~800 clipes/mês; em regime contínuo é ~40× maior, e por isso o VLM só roda sobre a amostra".
- *Por quê:* 17 câmeras × 96 janelas × 20 dias = 32.640 janelas-câmera/mês (40,8× as 800); × 16 quadros × 1.521 tokens ≈ 794 M tokens/mês → Haiku 4.5 ≈ US$ 794 (Batch ≈ 397), Opus 5 ≈ US$ 3.970 (Batch ≈ 1.985); só nas 10 câmeras de sala/pátio ≈ 467 M tokens → US$ 234 (Haiku-Batch) a US$ 1.168 (Opus-Batch). E isso rotula a cena, não cada criança. Fórmula oficial: ⌈largura/28⌉ × ⌈altura/28⌉ tokens; Opus 5 está no tier de alta resolução (modelos 4.7+): 1920×1080 sem redimensionar custa 2.691 tokens (1,77×), 4K custa 4.784 (3,1×) — os valores acima são piso. `cache_control` no codebook não reduz o custo das imagens (cada quadro é único). Preços verificados na tabela oficial (Haiku 4.5 US$ 1/M; Sonnet 5 US$ 2/M; Opus 5 US$ 5/M; Batch 50%).

**3. Concordância humana (Etapa 2)**
- *Estava:* `join … on b.entrada_id = a.entrada_id`; kappa ponderado ≥ 0,6 em envolvimento; "esse número vira o teto … para sempre"; nenhuma recalibração depois da semana 3.
- *Passa a ser:* join por `janela_id`; **alfa de Krippendorff ordinal como métrica única** (cobre 2 ou 3 avaliadoras e faltantes; com 2 avaliadoras equivale na prática ao kappa quadrático ≈ ICC(2,1), Fleiss & Cohen 1973 — não reportar três coeficientes). Portão **≥ 0,6 no agregado**; por turma (3 agrupadas) é **diagnóstico, não portão**, até haver ≥ 100 pares por turma — turma com alfa < 0,5 e n ≥ 60 dispara revisão das âncoras daquela faixa etária; para ler por turma, elevar a meta da Etapa 1 de 100 para ~200 entradas duplas. **Calibração contínua**: 20 janelas/semana com dupla avaliação cega, sorteadas só entre janelas válidas (criança rastreada ≥ 80% da janela, não em transição), janela de 30–60 s (≈ 15–20 min/semana/avaliadora); alfa calculado em **janela móvel de 4 semanas (~80 pares)**, não semanal; gatilho: alfa móvel < 0,5 em 2 leituras consecutivas → sessão de recalibração em voz alta. **Nova avaliadora** pontua 30 janelas do golden antes de contar como rótulo (alfa ≥ 0,6 contra o consenso). O denominador do modelo é o acordo humano medido **em janelas aleatórias**, não em cortes marcantes.
- *Por quê:* o humano também deriva (recheck de ≥ 20% das sessões com ≥ 80% de acordo é a convenção de Cooper, Heron & Heward); com n ≈ 33 pares por turma o IC95% de um kappa é da ordem de ± 0,25 (aproximação) e um portão por turma passa ou falha por sorte; n = 20 semanal tem IC ≈ ± 0,3 e gera alarme falso. Não é "teto" matemático: modelos treinados em consenso podem superar o acordo par-a-par (Boguslav & Cohen 2017), e o kappa medido em ~100 cortes não cobre sesta, fila e transição.

**4. Modelo longitudinal e unidade no Postgres (Etapas 6 e 7)**
- *Estava:* "só o agregado por sessão no Postgres"; modelo misto com efeitos de material/sala/horário/professora/dia da semana/idade; invariância só por versão de modelo; drift só pela checagem tracker↔UWB da Etapa 5.
- *Passa a ser:* tabela `janelas_features (aluno_id, inicio, fim, sala, camera_id, cobertura_video, cobertura_uwb, cobertura_audio numeric 0–1, material_id, adulto_dist_m, n_criancas_2m, hora_do_dia, …features…, versao_pipeline text, versao_pose text, versao_codebook text, features_hash text)` — uma linha por criança × 5 min (~1,1 M linhas/ano; **sem particionamento**, Postgres 17 resolve até ~10 M); vetor cru fica em Parquet com hash/ponteiro na linha. View materializada diária com cobertura média por sensor. **Unidade do modelo = janela**, efeitos aleatórios aninhados criança > criança-dia (`statsmodels` MixedLM com `vc_formula` — não usar AR(1), que o MixedLM não suporta), intercepto e inclinação por idade em meses, covariáveis de janela (material, `adulto_dist_m`, hora, sala, câmera), **peso = cobertura da janela**; excluir janelas com cobertura < 0,5 no sensor de origem; toda curva sai com a cobertura média do período. **Vigilância diária por câmera sobre dado ao vivo**: distribuição de altura de bounding box, detecções/hora, confiança média de keypoint e concordância tracker↔UWB; alerta quando qualquer uma sai do intervalo dos 14 dias anteriores (limiar derivado do ruído entre duas câmeras sobrepostas medido na Etapa 6, não fixado a priori). Regressão sobre o golden continua **por versão** (repontuar o golden toda noite com o mesmo modelo é determinístico e não detecta nada). Tabela `eventos_ambiente (sala, camera_id, data, tipo, descricao)` para câmera reposicionada, sala reorganizada, professora nova, troca de `versao_pipeline` — entra como efeito fixo e quebra de série. Portão da Etapa 7: efeito de idade estimado em ≥ 3 meses > desvio entre duas câmeras simultâneas **e** > diferença entre janelas de cobertura alta e baixa.
- *Por quê:* com m = 96 janelas/dia e ICC intradiário ρ, o design effect é 1 + (m − 1)ρ — para ρ = 0,5, ≈ 48, N efetivo ≈ 2 por dia; modelo que trata janela como independente declara "mudança significativa" toda semana. Ausência de dado não é aleatória (criança fora do quadro, tag sem bateria) — sem cobertura registrada, a curva mede falha de sensor. `salas_cameras` já tem a "sala MEIO" compartilhada e ajustável entre 1a3 e 3a6: fonte concreta de drift silencioso.

**5. "Métrica de tempo parado — Nunca"**
- *Estava:* linha da tabela "O que NÃO fazer": nunca, sem exceção.
- *Passa a ser:* "Imobilidade como proxy de **concentração** — nunca; imobilidade como proxy de **sono/repouso** — sim, é o padrão".
- *Por quê:* sono entrou no escopo, e actigrafia detecta sono justamente por ausência de movimento (algoritmo de Sadeh validado contra polissonografia em pré-escolares: sensibilidade > 95% para sono, especificidade ~50% para vigília). Em regime contínuo, sem essa distinção a sesta pontuaria como pico de envolvimento.

**6. Codebook "uma tarde"**
- *Estava:* codebook v1 = 3 dimensões × 5 níveis, uma tarde.
- *Passa a ser:* o v1 ordinal continua sendo uma tarde e continua abrindo a Etapa 1. Em paralelo, e sem travar a Etapa 1, um **dicionário de definições operacionais por domínio** (sono, alimentação, motor, linguagem, social: evento, unidade, sensor de origem, janela) — 2–3 semanas, versionado em `obs_codebook`.
- *Por quê:* contagens, durações e eventos não cabem em âncora ordinal 1–5; sem definição operacional, `janelas_features` vira coluna sem significado.

**7. Ordem da Etapa 5**
- *Estava:* Etapa 5 (RFID + UWB) nos meses 3–4, depois do golden.
- *Passa a ser:* **semana 1: encomendar só o piloto RFID** (1 leitor UHF fixo + antena near-field de prateleira + 30 tags passivas; faixa verificada: Chafon CF811 ~US$ 152 a Impinj R700 US$ 1.199–1.499, sem antena/tags) e criar a tabela `materiais` (catálogo tag↔material — **não existe**: `registros_pedagogicos` e `planejamentos` são texto livre, sem coluna de material). Instalação quando chegar (realisticamente semanas 4–6, depois do portão do kappa); validação de **acurácia** em 2 dias: ≥ 95% dos eventos retirar/devolver contra anotação manual. UWB só depois do RFID passar (MDEK1001 e Pozyx Creator descontinuados; opção DIY Makerfabs ESP32-UWB-DW3000 a US$ 43,80/nó, 4 âncoras + 5 tags ≈ US$ 395, com solver próprio), com portão que aceite NLOS por corpo humano (mediana ≤ 30 cm e p90 ≤ 60 cm, sala com crianças presentes). Áudio vai para etapa própria (acréscimo 1) com portão de **concordância**, não de cronômetro.
- *Por quê:* validação de sensor é acurácia contra evento físico, não codebook, então RFID não precisa esperar o golden; mas empilhar três integrações de hardware nas semanas 1–3 compete com o kappa e ignora lead time de importação. O que **não** mudar: não iniciar RFID, UWB e áudio em paralelo na semana 1 — ganho real é ~1 mês na série de eventos de material, não um trimestre. O plano atual não justifica o mês 3–4 por dependência de rótulo (a frase "não teria contra o que ser validada" é da Etapa 6/visão); o motivo é hardware não testado com criança de 3 anos, e isso o piloto pequeno resolve.

### O que acrescentamos

**1. Etapa 5b — Áudio por criança** (em paralelo com UWB, mesmo avental)
- Piloto: 2 semanas, 5 crianças, gravador de lapela USB genérico (~R$ 150–300, a verificar) — não LENA (gravador só funciona com assinatura: US$ 329/unidade em 1–9, US$ 219 em 30+, + US$ 5.000 de setup + US$ 3.000–6.100/ano, fonte LIEPP).
- Pipeline no worker de edge: Silero VAD (MIT, verificado; < 1 ms por chunk de 30 ms em 1 thread de CPU) → diarização pyannote.audio 3.1 (MIT, verificado) → classificador criança/adulto (VTC/ALICE do LAAC-LSCP, classes KCHI/CHI/MAL/FEM; **licença a verificar**) → **portadora vs outra criança**: como todas gravam ao mesmo tempo, atribuir cada segmento de voz infantil ao gravador em que tem maior energia (alinhamento temporal entre canais) — é a maior fonte de erro numa sala cheia (literatura LENA: precisão média 59% / recall 64% nas 4 classes) → contagens por janela de 5 min em `janelas_features`: `vocalizacoes_crianca`, `turnos_adulto_crianca` (janela de 5 s), `duracao_fala_s`, `fala_adulto_dirigida_s`, `cobertura_audio`.
- Transcrição (faster-whisper, MIT, verificado; large-v2 transcreve 13 min em 17 s numa RTX 3070 Ti com batch 8) **só para adultos** (WER 0,119 em professoras, WSW 2.0) e como texto secundário para ≥ 4 anos; nunca como medida de vocabulário abaixo disso (WER 0,238 em pré-escolares com gravador vestido; 54% em sala de aula K-12 mesmo após ajuste).
- Portão de concordância: fonoaudióloga/especialista anota 20 janelas aleatórias/semana (contagem manual de vocalizações e turnos) → ICC ≥ 0,7 para contagem de vocalizações antes de entrar no modelo. Medir no piloto: precisão/recall da atribuição portadora vs outra criança; autonomia de bateria ≥ 8 h; carga operacional de recarga/descarga diária (47 gravadores no regime pleno); RTF da diarização compartilhando GPU com a visão (não verificado).
- Volume: 47 × 8 h ≈ 376 h/dia de áudio; em Opus 32 kbps ≈ 5,4 GB/dia bruto; reter só o Parquet de contagens após o processamento.
- Âncoras: MB-CDI "Palavras e Gestos" (adaptação UFBA; usado em estudo brasileiro até 30 meses, CoDAS 2024) 1×/semestre para 1–2,5 anos; "Palavras e Frases" versão BR normatizada: **a verificar**; 30–36 meses sem âncora de relato dos pais — usar a calibração de janelas. Escrever no doc: **linguagem receptiva não é mensurável passivamente**; único proxy é "responde a pergunta da professora em ≤ 5 s" (métrica do WSW 2.0).

**2. Seção "Mapa de medição" antes da Etapa 1** — a tabela do bloco final, tratada como contrato, com três status honestos (JÁ MEDIDO / PASSIVO-CANDIDATO / NÃO PASSIVO, mais PARCIAL para proxies de currículo). "Passivo-candidato" só vira "sim" depois do piloto do sensor. Contagens de sensor ficam **fora** de `obs_avaliacoes` (vão para `janelas_features`).

**3. Schema:** `dev_janelas`, `dev_agregados` (features por janela), `eventos_ambiente`, `materiais`; `janela_id` em `obs_avaliacoes` e `obs_golden`; view materializada diária de cobertura. DDL única na Revisão 2.1.

**4. `meal_golden`** — ~100 pares servida/devolvida com 2 avaliadoras cegas, consenso de `consumed_overall`, kappa reportado; coluna de versão do modelo em `meal_events` (não existe); repontuar a cada troca de modelo. Uma tarde, depois de o fluxo estar rodando de verdade (hoje: 0 eventos) — e é a primeira aplicação real do padrão golden; só então `meal_events` prova que mede.

**5. Princípio nº 0 no topo do passo a passo:** "A observação humana vira calibração, não a medida." As cinco regras mantidas passam a ser lidas como o que garantem: que a calibração seja confiável.

**6. Dois tipos de portão, escritos no doc:** acurácia (sensor vs evento físico: cronômetro/anotação de contagem, 2 dias) e concordância (classificador vs codebook: alfa/ICC contra anotação humana).

### Mapa de medição

| Dimensão | Sensor | Instrumento de referência | Automatizável hoje? | Como validar |
| --- | --- | --- | --- | --- |
| Alimentação | `meal_events` (câmera → foto servida/devolvida → VLM → `consumed_overall`) | Consenso humano de 2 avaliadoras sobre as fotos | **SCHEMA PRONTO, 0 EVENTOS** — ativar o fluxo na cozinha sem compra | `meal_golden` ~100 pares, kappa reportado, coluna de versão de modelo (não existe), repontuação por versão |
| Envolvimento | Câmera (orientação de cabeça, resistência à distração) + RFID (tempo com o material) | Leuven LIS-YC, 5 pontos, codebook v1 | **PASSIVO-CANDIDATO** — dimensão-piloto, único "sim" previsto no ano 1 | Alfa ≥ 0,6 humano↔humano em janelas aleatórias; modelo ≥ 0,7 × acordo humano; teste-reteste entre câmeras sobrepostas; regressão no golden |
| Persistência | RFID (retomada após interrupção/erro) + câmera | Codebook v1 | PASSIVO-CANDIDATO | Concordância contra rótulo humano de janela; acurácia RFID ≥ 95% |
| Autonomia | UWB do adulto (`adulto_dist_m`) + RFID (escolha auto-iniciada) + `meal_events.served_photo_path` (serve-se sozinha) | Codebook v1 | PASSIVO-CANDIDATO (depende do piloto UWB) | Acurácia UWB (mediana ≤ 30 cm, p90 ≤ 60 cm com crianças presentes); concordância do `adulto_proximo` automático com o digitado |
| Social | UWB (grafo de proximidade: com quem, quanto tempo, reciprocidade); turnos criança–criança só com áudio vestível | Escala do professor (codebook v2) | PASSIVO-CANDIDATO | Acurácia UWB; concordância dos turnos com anotação manual (ICC ≥ 0,7) |
| Motor grosso | Pose 2D (velocidade de deslocamento, contagem de subir/pular) + UWB | TGMD-3 (3–10 anos) como **tarefa eliciada 1×/trimestre**, filmada em vista lateral/frontal; marcos da Caderneta da Criança (1–3 anos) | PASSIVO-CANDIDATO só para métricas grosseiras; "qualidade de marcha" e pontuação TGMD-3 **não** são passivas (validações existentes são de passarela instrumentada, n ≈ 96, ou idade média 7,8 anos; UEL 2023 = 350 imagens, só salto, 84%) | Fine-tune de pose em criança pequena; pose vs TGMD-3 eliciado; velocidade de pose vs UWB |
| Motor fino | RFID por material de precisão + foto de refeição (talher) | PDMS-2 (nasc.–71 meses, validado no Brasil) / álbum Montessori | **PARCIAL** — proxy de currículo, não medida passiva de mão (mãos a 5 m somem mesmo em 4K) | Progressão em materiais de precisão vs PDMS-2 semestral |
| Linguagem expressiva | Áudio vestível (CVC, turnos, duração de fala) | MB-CDI BR ("Palavras e Gestos", até 30 meses; "Palavras e Frases" a verificar); MLU/diversidade lexical de transcrição adulta-validada para ≥ 4 anos | PASSIVO-CANDIDATO, condicionado à Etapa 5b | ICC ≥ 0,7 contagens vs anotação manual (20 janelas/semana); precisão/recall portadora vs outra criança medidos no piloto |
| Linguagem receptiva | — (único proxy: "responde a pergunta da professora em ≤ 5 s") | Instrumento aplicado | **NÃO PASSIVO** — o sistema agenda e registra, não mede | Aplicação do instrumento; o proxy só como covariável |
| Cognitivo | RFID + `registros_pedagogicos` (progressão apresentado → repetido → dominado) | Álbum Montessori; ASQ-BR (Filgueiras 2011, 10–54 meses) como triagem trimestral | PARCIAL — referenciado a currículo, não passivo puro | Sequência de materiais vs registro da professora; ASQ-3 como âncora externa |
| Autorregulação | Câmera (latência de virada de cabeça a evento ambiental; latência em transições) + eventos acústicos sem ASR (choro/conflito por hora) | HTKS-R (3–8 anos, validado no Brasil), eliciado | PARCIAL | Concordância com codebook v2; correlação com HTKS-R semestral |
| Sono (sesta) | Câmera IR da sala de sesta → vídeo-actigrafia (latência, duração, despertares) | Observação da professora; relato dos pais para a noite (fora da escola) | PASSIVO-CANDIDATO só para a sesta (evidência disponível: 10 bebês em laboratório, kappa 0,733) | Validação local contra anotação da professora (kappa ≥ 0,7) antes de virar "sim"; imobilidade aqui é o sinal, não a armadilha |

### Fontes

- Preços e tokens de imagem: https://platform.claude.com/docs/en/about-claude/pricing ; https://platform.claude.com/docs/en/build-with-claude/vision (fórmula ⌈w/28⌉×⌈h/28⌉; tiers; "cannot be used to name people in images")
- Leuven LIS-YC: https://www.structural-learning.com/post/leuven-scale-a-teachers-guide ; https://irresistible-learning.co.uk/resource/leuven-scales-of-involvement-and-well-being/
- Amostragem por intervalo/MTS: https://onlinelibrary.wiley.com/doi/abs/10.1002/bin.328 (Devine 2011) ; https://pmc.ncbi.nlm.nih.gov/articles/PMC7070120/ ; https://www.nature.com/articles/s41598-022-07169-5
- Concordância: https://en.wikipedia.org/wiki/Krippendorff's_alpha ; https://journals.sagepub.com/doi/10.1177/001316447303300309 (Fleiss & Cohen 1973) ; https://pmc.ncbi.nlm.nih.gov/articles/PMC2713814/ ; https://www.researchgate.net/publication/322252759_Inter-Annotator_Agreement_and_the_Upper_Limit_on_Machine_Performance_Evidence_from_Biomedical_Natural_Language_Processing
- Design effect / MixedLM: https://cran.r-project.org/web/packages/PracTools/vignettes/Design-effects.html ; https://raw.githubusercontent.com/statsmodels/statsmodels/main/docs/source/mixed_linear.rst
- Áudio: https://arxiv.org/abs/2505.09972 (WSW 2.0) ; https://bergelsonlab.fas.harvard.edu/sites/g/files/omnuum3941/files/2025-01/cristia_etal_2020_BRM.pdf ; https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2024.1322665/full ; https://ieeexplore.ieee.org/document/10447428/ (ISAT) ; https://www.idee-education.fr/wp-content/uploads/2024/04/fiche-methodologique-LENA-LIEPP.pdf ; https://huggingface.co/pyannote/speaker-diarization-3.1 ; https://github.com/pyannote/pyannote-audio/blob/main/LICENSE ; https://github.com/snakers4/silero-vad (MIT, verificado) ; https://github.com/SYSTRAN/faster-whisper (MIT, verificado) ; https://github.com/MarvinLvn/voice-type-classifier (licença não exibida — a verificar) ; https://repositorio.ufba.br/handle/ri/27339 ; https://codas.org.br/journal/codas/article/doi/10.1590/2317-1782/20242023268pt
- Licenças de visão: https://github.com/Megvii-BaseDetection/YOLOX/blob/main/LICENSE (Apache-2.0, verificado) ; https://github.com/open-mmlab/mmpose/blob/main/LICENSE (Apache-2.0, verificado) ; https://github.com/blakeblackshear/frigate/blob/dev/LICENSE (MIT, verificado)
- Sono/actigrafia: https://jcsm.aasm.org/doi/10.5664/jcsm.2844 ; https://www.mdpi.com/1424-8220/19/5/1075
- Instrumentos-âncora: https://pubmed.ncbi.nlm.nih.gov/39513254/ (HTKS-R BR) ; https://pubmed.ncbi.nlm.nih.gov/33571789/ (PDMS-2 BR) ; https://www.redalyc.org/journal/3953/395354131011/html/ (ASQ-BR) ; https://ojs.uel.br/revistas/uel/index.php/semexatas/article/view/48131 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11893606/ (marcha, passarela) ; https://portaldeboaspraticas.iff.fiocruz.br/atencao-crianca/caderneta-de-saude-da-crianca-avaliacao-dos-marcos-do-desenvolvimento/
- Hardware: https://www.atlasrfidstore.com/impinj-r700-RAIN-rfid-reader/ ; https://www.accio.com/plp/fixed-rfid-reader-price ; https://www.makerfabs.com/esp32-uwb-dw3000.html ; https://www.tindie.com/products/drm0hr/decawave-now-qorvo-mdek1001-uwb-dev-kit/ ; https://www.pozyx.io/creator ; https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10575093/ (UWB NLOS)
- **Não verificado nesta revisão:** modelo/RTSP/ONVIF/fps das câmeras Reolink TrackMix (reolink.com e docs.frigate.video bloqueados pelo proxy) ; RTF de pyannote 3.1 em GPU compartilhada ; preço de gravador de lapela USB ; https://library.ncirl.ie/items/29347 ; MB-CDI "Palavras e Frases" versão BR normatizada.

---

## 2. Arquitetura para fluxo contínuo

### O que muda com a meta de monitoramento contínuo

- A ingestão deixa de ser um detalhe da Etapa 3 ("gravação contínua no gravador local") e vira
  a **fundação** do sistema: 16–17 streams, o dia inteiro, com um ponto único de conexão por
  câmera que alimenta gravação, recorte de clipe e inferência ao mesmo tempo.
- Toda a aritmética dos documentos foi feita para **6 câmeras × 8 h**. O parque real é ~3×
  maior, e o gargalo muda de inferência para **decodificação** (H.265 obriga a decodificar o
  GOP inteiro para extrair 5 fps).
- A unidade primária de dado passa a ser a **janela criança × intervalo × câmera** e a série de
  eventos que a gerou. `entrada_id` só existe quando alguém aperta um botão; no contínuo, 95%
  das janelas nunca terão entrada.
- **Cobertura** vira coluna obrigatória: sem denominador, "minutos engajados por dia" mede o
  uptime das câmeras, não a criança.
- Falhas (câmera cai, internet cai, disco enche, modelo muda) deixam de ser "sem clipe hoje" e
  passam a corromper a série longitudinal em silêncio. Nenhum dos três documentos trata disso.

### O que mantemos

- **Edge obrigatório**; vídeo e áudio contínuos brutos nunca saem do prédio. As contas refeitas
  confirmam: 275–551 GB/dia no cenário-teto exigiriam 70–140 Mbps de upload sustentado e
  US$ 200–400/mês só de storage, contra 2 HDs de 8 TB uma vez.
- **Parquet frio + agregado quente no Postgres.** Para 16,5 M person-frames/dia seriam ~3
  bilhões de linhas por ano letivo em tabela; em Parquet+zstd são 80–160 GB/ano, ~US$ 2–4/mês.
- **Versão de modelo em toda predição + corpus dourado repontuado por versão** — no contínuo o
  modelo roda todo dia; uma troca sem âncora contamina a série inteira.
- **Supabase como banco/auth/storage; Python só no worker de edge.** O worker deixa de ser "um
  script" e vira serviços em docker compose. Nenhuma stack nova.
- **Piloto do modelo nas 2 salas principais** — mas a infra (ingestão, Parquet, eventos) nasce
  para 16–17 câmeras desde o primeiro dia.

### O que corrigimos

**1. As contas (Etapa 3 e "As contas que ele não fez")**
- *Estava:* "~216 GB/dia em 6 streams 4K; com 17 câmeras, dimensione o disco antes" — e nunca
  dimensiona. "Uma 3060/4060 dá conta de 6 streams a 5 fps."
- *Passa a ser:* a tabela de dimensionamento abaixo, com três decisões explícitas. (a) Fixar o
  **fps do stream principal na própria câmera** em 5–10 (a TrackMix aceita 2–25): é a única
  alavanca que corta decodificação, porque H.265 não permite "pular quadros" — o decoder
  processa o fps de origem. Efeito colateral: também muda o que o NVR e a visualização ao vivo
  da escola gravam; combinar com a direção. (b) Disco é decidido pelo **teto de bitrate**, não
  pelo fps: em CBR (o que o Frigate recomenda para Reolink) reduzir fps não reduz um byte.
  (c) Retenção-alvo de 14 dias de vídeo bruto; main stream só nas 2 salas + pátio, substream
  nos 7 espaços únicos.
- *Por quê:* a 8 Mbps (teto Reolink em 4K), 17 × 32.400 s = 551 GB/dia; a 4 Mbps, 275 GB/dia.
  Decodificar 17 streams 4K a 25 fps = 425 quadros/s ≈ 3,5 Gpixel/s — no limite ou acima de um
  único NVDEC (~3,4 Gpixel/s em Ada). RTX 4060/5060/4070 têm **1** NVDEC; 4070 Ti/4080/4090
  têm 2. Gravar não decodifica (`-c copy`); só o stream de detecção decodifica. A faixa
  275–551 GB/dia é **teto** (todas 4K) — só a câmera do pátio é confirmadamente TrackMix; se
  parte for 2K/1080p, cai para ~140–300 GB/dia.

**2. Topologia física (lacuna: nenhum documento a define)**
- *Estava:* "gravação contínua no gravador local"; "detecção + tracking nas 2 salas".
- *Passa a ser:* **uma caixa de edge por escola**, com três processos: (1) **go2rtc** (MIT) puxa
  cada câmera **uma vez** e restreama localmente — para Reolink, a recomendação oficial do
  Frigate é **HTTP-FLV como primeira opção**, RTSP conforme a geração da câmera, (Neolink, AGPL-3.0, **não** entra — ver 2.1); (2)
  **Frigate** (MIT) grava o main stream sem re-encode, com retenção por dias, e serve o recorte
  de clipe pela API (`/api/<cam>/start/<ts>/end/<ts>/clip.mp4`); (3) o **worker Python** lê o
  restream a 5 fps e escreve Parquet + eventos. Antes de comprar qualquer coisa de rede:
  as câmeras provavelmente já estão nas portas PoE de um **NVR Reolink existente** — nesse
  caso a caixa puxa cada canal do NVR e não há switch a comprar; o gargalo é o uplink
  NVR → edge.
- *Por quê:* sem ponto único, gravação, recorte, detecção e áudio abrem 3–4 sessões por câmera
  numa implementação RTSP que o mantenedor do Frigate chama de "flawed". O tracker do Frigate
  é orientado a eventos de segurança e só detecta em regiões com movimento — ruim para criança
  parada minutos num tapete; por isso ele é NVR + fonte de quadros, e o cérebro é o worker.
- *Atenção:* o Frigate **não** tem retenção por marca-d'água nem alerta de "retenção efetiva
  < N dias" — só uma limpeza de emergência quando resta ~1 h de espaço. Isso tem de ser
  construído (regra 3 do item 6).

**3. Modelo de dados do contínuo (lacuna real; prescrição corrigida)**
- *Estava:* `obs_avaliacoes` e `obs_golden` referenciam `entrada_id not null`; "só o agregado
  por sessão no Postgres"; análise pede "confirmar TimescaleDB".
- *Passa a ser, em dois tempos.* **Agora (1 dia):** tabela `dev_janelas (id, aluno_id nullable,
  sala, camera_id, inicio, fim, gerada_por, clip_path)`; `janela_id` em `obs_avaliacoes` e
  `obs_golden`, `entrada_id` opcional — a entrada humana vira **uma** forma de gerar janela, o
  sorteio vira outra. **Quando existir o primeiro mês de eventos reais (Etapa 5/6):**
  `dev_eventos` append-only (`ts, fonte, tipo, sujeito = track_id ou aluno_id, sala/camera_id,
  payload jsonb, modelo_versao, pipeline_versao, config_versao`), com índice `(aluno_id, ts)` e
  BRIN em `ts` — **sem partição** até haver volume (a própria doc do Supabase: "se você não
  sabe como particionar, é cedo demais"); `pg_partman` entra depois, para expurgo por retenção.
  `dev_agregados` por janela de 5 min → hora → dia (`aluno_id, inicio, fim, dimensao, valor,
  n_amostras, cobertura, modelo_versao`): 47 × 108 × 8 dimensões × 200 dias ≈ 8 M linhas/ano
  — cabe (~1–2 GB). `track_identidade (track_id, aluno_id, origem, vigencia)` versionada no
  Postgres; **`aluno_id` nunca vai no Parquet frio** — a identidade será recomputada quando o
  modelo melhorar, e não se reescreve histórico imutável.
- *Onde mora cada dado:* Postgres = janelas, avaliações, eventos, agregados, ligações, versões,
  cobertura. Storage = Parquet (espelho diário via **rclone** pelo endpoint S3 — rsync não fala
  com o Storage), clipes do golden e de janelas sorteadas, áudios e fotos **curtos** (como já
  acontece hoje em `observacao-audio`). Edge = vídeo e áudio **contínuos** brutos e quadros.
- *Por quê:* TimescaleDB não existe no projeto (PG 17) — item fechado. "Sessão" até é
  definível numa escola (dia letivo, ciclo de 3 h), mas a janela de 5 min é a única unidade que
  carrega `cobertura`.

**4. Produtores de evento existentes (refutado: não há o que ligar hoje)**
- *Estava (no contexto do painel):* "`meal_events` e `observacao_indice` já produzem eventos;
  ligue-os ao mesmo modelo por trigger."
- *Passa a ser:* definir o **contrato de evento** (sujeito, instante, sala/câmera, tipo,
  evidência mínima, `modelo_versao`) **antes** do worker de visão, como nota de desenho — e
  não integrar nada por trigger agora: `meal_events` tem 0 linhas, `meal_events.child_id`
  aponta para `children` (vazia), e `camera_id` é texto sem FK porque `salas_cameras` não tem
  uma linha por câmera. Quando houver dado, uma view `UNION ALL` sobre as fontes é menos
  manutenção que triggers com idempotência. Pré-requisito real: **normalizar `salas_cameras`**
  (uma linha por câmera) — que é exatamente o que o inventário técnico da seção 4 produz.

**5. Áudio contínuo (refutado no diagnóstico de compute; mantido no de qualidade)**
- *Estava (no painel):* "153 h/dia de áudio; transcrever tudo é inviável em compute."
- *Passa a ser:* compute **não** é o problema — pyannote community-1 faz 31 s por hora de áudio
  numa H100 (153 h ≈ 79 min; numa GPU de consumo, 2,5–5 GPU-h), e faster-whisper large-v2 int8
  roda ~49× tempo real numa RTX 3070 Ti (153 h ≈ 3 GPU-h). Cabe numa noite. O problema é
  **qualidade** (WER de criança ~24% com gravador vestido e >50% em campo distante barulhento)
  e **atribuição** (diarização dá "locutor A", não "Maria"; embedding de voz de criança de
  2–4 anos não é estável). Regra: microfone de câmera/teto → **métricas por zona** (fração de
  voz, energia, eventos de ruído, turnos grosseiros) em `dev_agregados` com sujeito = zona;
  **linguagem por criança → gravador vestível** (seção 1, Etapa 5b). Transcrição só de adultos
  e das janelas amostradas. Áudio bruto: buffer circular de 48 h no edge.
- *Não verificado:* se as câmeras das salas têm microfone e se a 3 m ele separa voz de criança
  de ruído de sala — é o teste T9 da seção 4.

**6. Operação contínua — o que acontece quando…**
- *Estava:* nada, em nenhum documento (grep: "cobertura" e "offline" não aparecem).
- *Passa a ser, como requisito de schema e código:* (1) **câmera cai** → tabela `dev_cobertura
  (zona, janela 5 min, quadros_recebidos, quadros_esperados, motivo_gap)`; cobertura por
  **zona** (alguma câmera cobrindo), não por câmera — sala 1a3 tem 4 câmeras e a queda de uma
  redundante não é perda; denominador da criança = "minutos em que ela estava **presente** e a
  zona dela estava coberta" — a presença já existe no sistema de ponto; criança que faltou
  não vira "zero engajamento". A cobertura entra como **peso e covariável** no modelo misto
  da Etapa 7; corte duro só como exclusão extrema. (2) **Internet cai** → worker escreve
  **local-first** (Parquet + SQLite de eventos) e um processo `sync` sobe em lotes com upsert
  idempotente por `(fonte, camera_id, ts, tipo)`; o Supabase é destino, nunca dependência.
  Teste de aceitação: 2 h sem internet, zero perda. (3) **Disco enche** → retenção por idade
  **e** por marca-d'água (apagar vídeo bruto antes de Parquet quando < 15% livre) + alerta
  quando a retenção efetiva < 14 dias — construído, porque o Frigate não faz. (4) **Modelo,
  fps ou câmera muda** → `modelo_versao`, `pipeline_versao`, `config_versao` em todo evento e
  agregado; Parquet guarda detecções, keypoints, track_ids e calibração da câmera; um job
  `reprocessar(desde, ate, versao)` regenera agregados a partir do Parquet **sem o vídeo** —
  esse job é o que prova que a série é recomputável.
- *Por quê:* a análise de 29/08 já pedia "versão do modelo + calibração + código de features +
  vetor cru" (modo 4 é lacuna de especificação, não de ideia); os modos 1–3 são lacunas reais.

**7. Clipes → contínuo (mantido)**
- *Estava:* clipe só nasce "ao salvar uma entrada com sala"; "custo não importa nesta escala";
  Etapa 6 "nas 2 salas principais".
- *Passa a ser:* janela como unidade (item 3); sorteio diário de janelas por **sala × faixa
  horária** (não por criança — a posição da criança num instante aleatório só existe a partir
  do UWB/tracking); a frase de custo vira "não importa **na amostra**; em regime contínuo é
  ~40× maior, por isso o VLM só roda sobre a amostra"; Etapa 6 separa "infra para 16–17
  câmeras desde o dia 1" de "modelo validado primeiro em sala 1a3 e 3a6, depois pátio (motor
  grosso) e cozinha (alimentação)".

### Fluxo contínuo

```
 câmeras (16–17; HTTP-FLV/RTSP)          gravador vestível (áudio por criança, Etapa 5b)
        │ uma conexão por câmera                  │ descarga diária
        ▼                                          ▼
 ┌─ go2rtc ──────────────┐             ┌─ worker-audio ──────────────┐
 │ restream local        │             │ VAD → diarização → contagens │
 └───┬──────────────┬────┘             └──────────────┬──────────────┘
     │              │                                 │
     ▼              ▼                                 │
 Frigate (NVR)   worker-visao (5 fps)                 │
 main stream     detecção → tracking → pose           │
 retenção 14 d   ──► Parquet (keypoints, tracks) ─────┼──► DuckDB (análise, treino)
 clipe por API   ──► dev_eventos / dev_cobertura ◄────┘
     │                    │
     │            agregados por janela 5 min (com cobertura, versões)
     │                    │  local-first (SQLite) → sync idempotente
     ▼                    ▼
 clipes de janela     Supabase (Postgres): janelas, avaliações, eventos,
 sorteada → Storage   agregados, ligações, versões  ──► páginas estáticas
                      Storage: Parquet (espelho rclone/S3), clipes golden
 NUNCA sobe: vídeo e áudio contínuos brutos, quadros
```

### Dimensionamento (16–17 câmeras, 9 h/dia)

| Item | Cenário-teto (todas 4K) | Cenário provável (2 salas + pátio em 4K; 7 espaços únicos em substream) |
| --- | --- | --- |
| Vídeo bruto/dia | 275–551 GB (4–8 Mbps) | ~140–300 GB |
| Retenção 14 dias | 3,9–7,7 TB | 2–4 TB → 2 × 8 TB em espelho cabe |
| Decodificação p/ detecção | 425 quadros 4K/s a 25 fps — **não cabe em 1 NVDEC** | fps fixado em 5–10 na câmera → 85–170 quadros/s, cabe em 1 NVDEC ou QuickSync |
| Person-frames/dia (5 fps) | ~16,5 M (teto; corredor/entrada quase vazios) | ~10–12 M |
| Parquet keypoints | 0,4–0,8 GB/dia → 80–160 GB/ano | 0,3–0,5 GB/dia |
| Eventos + agregados no Postgres | ~0,5–1 M eventos/mês; ~8 M agregados/ano | idem |
| Storage Supabase | ~US$ 2–4/mês (cumulativo; ano 1 quase dentro dos 100 GB do Pro) | idem |
| GPU | 5060 Ti 16 GB se pose + áudio + treino na mesma placa | 5060 8 GB cobre 7 câmeras a 5 fps; pose contínua em 17 é "a medir" |

---

## 3. Ferramentas para começar

### O que muda com a meta de monitoramento contínuo

- Aparece uma camada que nenhum documento tinha: **ingestão e NVR** (go2rtc + Frigate), porque
  17 streams 8 h/dia precisam de quem mantenha a conexão, decodifique, grave e recorte.
- O **VLM muda de categoria**: de "custo irrelevante" para "orçamento explícito da amostra";
  a medida contínua vem de modelos locais sobre keypoints, com custo marginal zero.
- Entra uma **stack de áudio** (VAD, diarização, classificação de tipo de voz) — e ela se
  divide em duas: clima sonoro da sala (microfone de câmera) e linguagem por criança
  (gravador vestível).
- Várias sugestões dos documentos estão **obsoletas ou com licença que morde na Etapa 8**:
  YOLOX parou em 2023, MMDetection/MMPose dependem de mmcv que não compila em PyTorch 2.x/CUDA
  12.8 sem wheel oficial, BoxMOT é AGPL apesar de embalar trackers MIT, YOLO-NAS e Sapiens são
  não-comerciais, D-FINE só é limpo nos checkpoints COCO, PYSKL está pinado em Python 3.7.

### O que mantemos

- **Supabase + páginas estáticas + worker Python** (agora um docker compose com `frigate`,
  `worker-visao`, `worker-audio`, escrevendo no Supabase via `supabase-py` com service key;
  nenhum endpoint HTTP próprio até existir consumidor externo).
- As **mecânicas** da Etapa 4 — Batch API (50%), `cache_control` no codebook, saída estruturada
  (`output_config.format`), resultados chaveados por `custom_id` — sobrevivem; o **papel** muda.
- **Parquet + DuckDB** para o frio; **só agregado no Postgres**.
- **Detector e pose com licença permissiva; nunca Ultralytics.**

### O que corrigimos

**1. Custo e papel do VLM (Etapa 4)**
- *Estava:* "~800 avaliações/mês … US$ 40–60/mês … custo não importa nesta escala".
- *Passa a ser:* duas faixas. **Contínuo, custo zero de API:** detector + tracker + pose no edge,
  8 h/dia. **Amostrado, com orçamento:** Claude recebe (i) o golden e as ~800 entradas/mês das
  professoras (`claude-opus-5`, como hoje), (ii) 2.000–4.000 janelas/mês de amostragem ativa
  + 10% aleatório (≈ US$ 120–245/mês em Opus + Batch), (iii) eventos disparados por regra.
  Regras técnicas: redimensionar todo quadro para **lado maior ≤ 1.092 px** antes de enviar
  (Opus 5 está no tier de alta resolução — um quadro 4K custa 4.784 tokens, 3,1× mais); preferir
  **recortes de 448×448 por criança** (256 tokens, 5× mais barato que o quadro inteiro); nunca
  GIF/vídeo (a API usa só o primeiro quadro); até 600 imagens por request em modelos de 1M
  (100 no Haiku 4.5). Duas armadilhas verificadas: o **mínimo cacheável do Haiku 4.5 é 4.096
  tokens** (Opus 5: 512; Sonnet 5: 1.024) — um codebook curto **não** será cacheado no Haiku e
  custará mais que a própria imagem por chamada; e o **limite de 256 MB por batch** — 16 JPEGs
  em base64 (~2,5 MB/request) dão ~95 requests por batch, então ou se sobem quadros pela Files
  API ou se fatiam dezenas de batches por dia.
- *Por quê:* em regime contínuo, 10 câmeras × 8 h × 1 quadro/10 s = 28.800 quadros/dia ≈
  37 M tokens/dia; com Batch e 22 dias: Haiku ≈ US$ 410/mês, Sonnet 5 ≈ US$ 820, Opus 5 ≈
  US$ 2.050 — e US$ 7.500 se mandar 4K sem reduzir. A saída estruturada soma ~US$ 240/mês só
  no Haiku. Preços verificados (Opus 5 US$ 5/25, Sonnet 5 US$ 2/10, Haiku 4.5 US$ 1/5 por MTok).

**2. Ingestão (lacuna: definir Frigate + go2rtc + inventário)**
- *Estava:* "gravação contínua no gravador local … dimensione o disco antes".
- *Passa a ser:* Frigate 0.17.x (MIT; imagem `stable-tensorrt`, `preset-nvidia` para NVDEC) como
  **NVR e fonte de quadros**, com go2rtc (MIT) embutido fazendo a conexão única por câmera
  (HTTP-FLV para Reolink como primeira opção). Gravação do main stream sem re-encode; `retain`
  de **14 dias**, não 30 — 17 streams a 8 Mbps × 30 dias ≈ 14,7 TB não cabem em 2 × 8 TB.
  Detecção **não** dentro do Frigate para este projeto (ver item 3). Migração em
  `salas_cameras`: uma linha por câmera com `fabricante, modelo, poe_wifi, nvr_canal, stream_main,
  stream_sub, fps_main, bitrate, codec, hfov, altura_m, ptz, tem_microfone, verificado_em` —
  **sem credencial no banco** (as páginas estáticas leem o Postgres via anon key). DeepStream e
  GStreamer artesanal ficam fora nesta fase.
- *Por quê:* verificado: Frigate MIT, v0.17.2 estável; rotas de clipe e export existem no
  código; RTX 5060/5060 Ti têm 1 NVDEC; Reolink vem com RTSP/ONVIF desligados por padrão (liga
  em Network → Advanced → Port Settings); TrackMix PoE expõe main 4K H.265 e um substream
  fixo de 640×360.

**3. Detector e tracker (nomear os que têm licença e manutenção verificadas)**
- *Estava:* "detector com licença permissiva — não Ultralytics"; análise: "YOLOX, RT-DETR ou
  MMDetection".
- *Passa a ser:* **RF-DETR Small ou Nano** (`pip install rfdetr`, Apache-2.0 nos pesos
  Nano/Small/Medium/Large; **nunca XL/2XL**, que são "PML 1.0" e exigem contrato com a Roboflow),
  exportado para ONNX/TensorRT, rodando **no worker próprio** a 5 fps sobre o substream,
  alimentando **ByteTrack ou BoT-SORT copiados das implementações originais (MIT)** e a pose
  no mesmo loop. Alternativa de mesma licença: RT-DETRv2-S. D-FINE só com checkpoints treinados
  exclusivamente em COCO. **Proibidos:** Ultralytics (AGPL-3.0), YOLO-NAS (pesos não
  comerciais), YOLOX (último changelog 02/2023), MMDetection (mmcv), **BoxMOT (AGPL-3.0**, mesmo
  embalando ByteTrack/BoT-SORT/OC-SORT). Re-ID visual não entra: criança de avental vista de
  cima não tem assinatura visual estável — a identidade do tracklet vem do UWB (ou do marcador
  visual da seção 4), e o fallback é atribuição manual na tela de observação.
- *Por quê:* a arquitetura "detector dentro do Frigate + ByteTrack no worker" é incoerente — o
  Frigate usa o Norfair (BSD-3) e não expõe detecções cruas por quadro; e só detecta em regiões
  com movimento. Se um dia quiser detectar no Frigate, o tracker é o Norfair e ponto. Ressalva
  registrada: os pesos RF-DETR também vêm de pré-treino em Objects365, mas a Roboflow os
  declara Apache-2.0 — o critério prático é o que o licenciante declara.

**4. Pose e modelo temporal**
- *Estava:* "Pose (RTMPose/MediaPipe, Apache-2.0), fine-tune próprio"; "modelo temporal sobre
  keypoints (ST-GCN / transformer pequeno)".
- *Passa a ser:* **rtmlib** (Apache-2.0; só numpy/opencv/onnxruntime, sem mmcv; ativo em 2026,
  já com detector RF-DETR integrado) com **RTMO-s** (multi-pessoa num passo, 67,7 AP COCO,
  ~9 ms em V100/ONNX) para inferência contínua; RTMPose-m top-down só nos recortes do golden e
  da calibração. **Fine-tune infantil em contêiner separado** com MMPose **v1.3.2** (última
  versão, 07/2024) + mmcv pinado na combinação que compilar, exportando ONNX para o rtmlib — o
  worker de produção **nunca importa mmcv**. **Proibidos:** Sapiens (CC-BY-NC-4.0), MediaPipe
  como modelo principal (single-person: `num_poses` existe mas o modelo só suporta uma pessoa;
  issue fechada como "stale"). RF-DETR keypoint (Apache-2.0) é candidato a "detector + pose num
  modelo só", mas está em status **Preview**. Modelo temporal em duas fases: (a) **features em
  janelas de 30 s / 3 min calculadas em DuckDB** sobre o Parquet (orientação de cabeça vs objeto,
  energia de movimento, distância ao adulto, latência de virada após evento) + gradient
  boosting; (b) só depois do golden fechado, ST-GCN++ **reimplementado em PyTorch puro** (é um
  modelo pequeno) — **não PYSKL**, que está sem manutenção desde 2023 e pinado em Python 3.7 /
  PyTorch 1.11 / mmcv-full 1.5. Backbone visual opcional: DINOv2 (Apache-2.0) congelado; DINOv3
  só com o aviso "Built with DINOv3" (licença não verificada).
- *Por quê:* RTMO não faz tracking — identidade continua vindo do tracker ou do UWB. O estudo
  que mostra RTMPose como o melhor ponto de partida sem fine-tune (Baby Grow) é sobre
  recém-nascidos filmados por celular — proxy fraco para 1–6 anos numa sala; por isso o teste
  T5 da seção 4 mede a degradação nas câmeras reais.

**5. Áudio (lacuna real; prescrição corrigida pelo refutador)**
- *Estava (no painel):* "VAD + diarização + voice-type-classifier sobre o áudio das câmeras dá
  vocalizações e turnos por criança".
- *Passa a ser, em duas stacks.* **Clima sonoro da sala (microfone de câmera):** Silero VAD (MIT;
  < 1 ms por chunk de 30 ms em 1 thread de CPU) → fração de voz, energia, eventos de ruído
  (bandeja caindo = o estímulo de "resistência à distração"), turnos grosseiros por zona;
  **nunca** "por criança". **Linguagem por criança (gravador vestível):** pyannote.audio (código
  MIT; pipeline `speaker-diarization-community-1` é **CC-BY-4.0, gated** no Hugging Face —
  aceitar as condições e guardar o token como segredo) → classificador criança/adulto → atribuir
  cada vocalização ao gravador em que tem mais energia (alinhamento temporal entre canais) →
  contagens por janela. **Não adotar o voice-type-classifier (VTC/ALICE) como está**: os
  repositórios não exibem LICENSE (404) — sem licença, o padrão é "todos os direitos
  reservados"; além disso, foi treinado para gravador **preso no colete da criança**, e a classe
  KCHI significa "a criança que usa o microfone" — não existe num microfone a 3–5 m. Se
  precisar, treinar um classificador de 4 classes sobre embeddings do pyannote com ~2 h de
  áudio próprio rotulado. Transcrição: **faster-whisper** (MIT; large-v3 / turbo) ou
  `distil-whisper-large-v3-ptbr` (WER 8,2% em fala **adulta**) só para adultos e crianças ≥ 4
  anos; WhisperX (BSD-2) se precisar de timestamps por palavra.
- *Por quê:* pyannote em sala barulhenta/far-field tem DER da ordem de 34% (contra < 8% em
  áudio limpo); o estado da arte em pré-escola (WSW 2.0) só resolve criança × professora e usa
  gravadores vestidos. Prometer "turnos por criança" com microfone de teto é prometer uma medida
  que não existe.

**6. Armazenamento e análise**
- *Estava:* "keypoints em Parquet particionado por dia/sala no Storage (lidos com DuckDB)".
- *Passa a ser:* layout `keypoints/ano=/mes=/dia=/sala=/`, colunas `ts, camera_id, track_id,
  kp int16[17][3], bbox int16[4], modelo_versao` — **sem `aluno_id`** (identidade fica em
  `track_identidade`, versionada no Postgres). Escrita com pyarrow em **um arquivo por sala por
  hora**, compactado para **um por sala por dia** — não "lotes de 5 min", que geram ~300–400
  mil arquivos/ano e anulam o DuckDB via httpfs (2 requisições HTTP por arquivo). Cópia primária
  no NVMe do edge (é onde treino e DuckDB rodam); espelho no bucket `keypoints` do Supabase
  Storage via **rclone/S3** — motivo real é latência e simplicidade, não egress (o Pro inclui
  250 GB/mês, reler o ano inteiro uma vez por mês cabe na cota). DuckDB lê o bucket pela
  extensão httpfs com credenciais S3 (há exemplo oficial da Supabase). **pgvector** (licença
  PostgreSQL, 0.8.6, incluído no Supabase) só para `obs_golden.embedding halfvec(768)` — busca
  de clipes parecidos e dedupe da amostragem ativa; **proibido** usar distância de embedding
  como medida longitudinal (P8 da análise). Para 300–500 clipes nem precisa de índice.
- *Ambiente:* Python 3.12, **uv** (MIT/Apache-2.0) com `uv.lock` versionado, CUDA 12.x,
  onnxruntime-gpu; três contêineres no compose (`frigate`, `worker-visao`, `worker-audio`) + um
  contêiner de treino separado com MMPose.

**7. Anotação**
- *Estava:* "fine-tune próprio em algumas centenas de quadros" — sem ferramenta.
- *Passa a ser:* **CVAT Community (MIT)** para os 300–500 quadros de keypoints — mas **não** ao
  lado do NVR: o compose oficial sobe 18 contêineres (Postgres, Redis, ClickHouse, Grafana…) e
  pede 8–16 GB de RAM; é tarefa única de algumas horas, então roda temporariamente em outro
  computador e desliga. Quadros **esparsos e diversos** (crianças, posturas, câmeras), não
  consecutivos; **pré-anotar com o próprio RTMPose e corrigir** (import COCO Keypoints); usar
  modo *shape* por quadro e validar o JSON exportado antes de treinar (houve bug de esqueleto em
  modo *track* exportando keypoints vazios). Não usar os modelos da pasta `/serverless` do CVAT
  (podem ter licença não comercial). **Label Studio (Apache-2.0)** só para segmentos temporais,
  se a tela própria não bastar. A nota 1–5 da professora **nunca** sai da página de observação.

**8. Etapa 4 e stack (refutado em parte)**
- *Estava (no painel):* "manter a Etapa 4 como está; a única mudança é docker compose".
- *Passa a ser:* stack mantida (item acima), mas a Etapa 4 é reescrita pelo item 1 desta seção
  e pelo item 2 da seção 1 — o Claude deixa de ser candidato a medida e vira rotulador
  amostrado com orçamento. Migrar a rotina `indexa-observacao` para `output_config.format` se
  ainda parseia texto livre. Cache em Batch é *best-effort*; a própria doc recomenda TTL de 1 h
  para lotes.

### Tabela de ferramentas

| Ferramenta | Versão | Licença | Função | Por que esta e não outra |
| --- | --- | --- | --- | --- |
| go2rtc | atual (MIT) | MIT ✔ | Conexão única por câmera + restream local; HTTP-FLV para Reolink | Recomendação oficial do Frigate para Reolink; evita 3–4 sessões RTSP por câmera |
| Frigate | 0.17.x | MIT ✔ | NVR: gravação sem re-encode, retenção, clipe por API, decode NVDEC | Único NVR open source com API de clipe e preset NVIDIA; **não** como cérebro |
| Neolink | — | AGPL-3.0 | — | **Não usar** (2.1): AGPL e desnecessário, HTTP-FLV resolve |
| RF-DETR | `rfdetr` 1.10 | Apache-2.0 (N/S/M/L) ✔ | Detector de pessoas a 5 fps no substream | Ativo (release 09/2026), permissivo, ONNX/TensorRT; XL/2XL proibidos |
| RT-DETRv2-S | — | Apache-2.0 ✔ | Detector alternativo | Mesma licença; repo ativo (v4 em 11/2025) |
| ByteTrack / BoT-SORT | originais | MIT ✔ | Tracking multi-objeto | Copiar do repo original; **nunca BoxMOT (AGPL)** |
| rtmlib + RTMO-s | 0.0.15+ | Apache-2.0 ✔ | Pose multi-pessoa contínua sem mmcv | Único caminho RTMPose/RTMO sem a dependência que quebra |
| MMPose (só treino) | 1.3.2 | Apache-2.0 ✔ | Fine-tune infantil, exporta ONNX | Isolado em contêiner; nunca no worker |
| DuckDB + pyarrow | atual | MIT / Apache-2.0 ✔ | Parquet, features em janela, treino | Padrão da indústria; lê o Storage via S3/httpfs |
| Silero VAD | atual | MIT ✔ | Fração de voz / eventos por zona (mic de câmera) | Custo zero de CPU |
| pyannote.audio + community-1 | 3.x/4.x | MIT (código) / CC-BY-4.0 gated (pipeline) | Diarização no áudio vestível | Melhor open source; CC-BY exige atribuição, não é restritiva |
| faster-whisper | 1.1+ | MIT ✔ | Transcrição de adultos e amostras | ~49× tempo real em GPU de consumo (int8) |
| Claude API (`claude-opus-5`, `claude-sonnet-5`, `claude-haiku-4-5`) | — | comercial | Rotulador amostrado (Batch, cache, saída estruturada) | Já em uso na escola; **nunca** scorer do fluxo |
| Supabase (Postgres 17, Storage S3, pg_cron; pg_partman quando precisar) | — | — | Banco, auth, storage | Já em produção; TimescaleDB indisponível |
| pgvector | 0.8.6 | PostgreSQL ✔ | Só `obs_golden.embedding` | Incluído; sem custo |
| CVAT Community | atual | MIT ✔ | Anotação de keypoints (temporária) | Esqueleto COCO-17 + import de pré-anotação |
| Label Studio | atual | Apache-2.0 ✔ | Segmentos temporais, se necessário | Template "video timeline segmentation" |
| uv, Python 3.12, CUDA 12.x, onnxruntime-gpu, docker compose | — | permissivas ✔ | Ambiente | `uv.lock` versionado; 3 contêineres + 1 de treino |
| **Fora:** Ultralytics, YOLO-NAS, YOLOX, MMDetection, BoxMOT, Sapiens, MediaPipe (principal), PYSKL, VTC/ALICE (sem licença), DeepStream, Feast, TimescaleDB | | | | Motivos nos itens 3–5 |

---

## 4. Como testar sem hardware novo

### O que muda com a meta de monitoramento contínuo

O documento de 29/08 tinha um único teste decisivo: o kappa humano. Ele continua decisivo, mas
para a meta nova a pergunta que decide em 4 semanas é outra: **as câmeras que já existem
entregam stream contínuo que um computador comum aguenta 8 h/dia, 5 dias seguidos — e o
sistema devolve o mesmo número quando duas câmeras olham a mesma criança?** Nada disso exige
compra, e nada disso estava no documento. Três premissas de "já existe" caíram (correções de
fato acima): não há vídeo rotulado a resgatar, `meal_events` está vazio e as câmeras não têm
ficha técnica.

### O que mantemos

- **O kappa antes de qualquer modelo** — mas com material novo, não com as 40 transcrições
  (são testes de microfone).
- **A semana 1 com custo zero** (codebook + sliders + migração mínima) — os testes de captação
  rodam **em paralelo**, não na frente dela.
- **Teste-reteste entre câmeras sobrepostas e split por criança e por dia** como regras de
  avaliação — antecipados da Etapa 6 para a Etapa 3.

### Protocolo (4 semanas, custo zero em hardware; um HD é a única compra possível)

| # | Teste | O que precisa | Duração | Critério de aprovação | Se falhar |
| --- | --- | --- | --- | --- | --- |
| T0 | **Inventário técnico das câmeras.** Uma linha por câmera: fabricante, modelo, PoE/Wi-Fi, está num NVR? (canal), stream main/sub (host/canal, **sem credencial no banco**), resolução × fps × bitrate configurados, codec, HFOV, altura/ângulo, PTZ?, microfone? Ligar RTSP/HTTP e NTP. Confirmar com o dono: `'sala 1'` = `'sala 1a3'`?; "sala MEIO" é uma câmera?; pátio = 1 TrackMix com 2 lentes? | Acesso ao NVR/Reolink Client, meio dia | Dia 1–2 | 100% das câmeras de sala com stream testado (`ffprobe` no HTTP-FLV **e** no RTSP — RTSP sozinho pode dar falso negativo) | Câmera sem stream utilizável sai do plano contínuo |
| T1 | **Prova de vida da captação.** go2rtc (HTTP-FLV p/ Reolink) + Frigate no PC existente; **detect** no substream a 5 fps (OpenVINO se houver iGPU Intel ≥ 6ª gen; senão CPU com detector leve); **record** do **main stream** (gravar não decodifica; 640×360 destruiria o golden). Registrar por minuto em `captacao_stats`: `camera_fps`, `process_fps`, `skipped_fps`, `inference_speed`, CPU, RAM, reconexões | PC comum; ~140 GB/dia para 7 câmeras em 4K → HD de 1–2 TB para 7–14 dias (a única compra possível; talvez zero se o NVR já retém) | Dias 2–5 de montagem; 15 dias úteis rodando | 5 dias × 8 h com uptime ≥ 98% por câmera; `camera_fps` ≈ configurado; `skipped_fps` = 0; CPU média < 70%. **Não** usar `detection_fps` como critério (cai a 0 em sala vazia) | CPU saturada → o número da compra de edge (seção 5). Quedas de stream → trocar protocolo (HTTP-FLV/Neolink), **não** cabo |
| T2 | **Sincronização de relógio.** NTP (a.ntp.br) nas câmeras/NVR; gravar `now()` do servidor ao lado do `relogio` do tablet; evento de luz (acender/apagar 2×) visto nas 4 câmeras da sala 1a3 | T1 rodando | 1 dia, semana 2 | Offset ≤ 0,5 s entre câmeras (2–3 quadros a 5 fps); offset tablet↔servidor medido e gravado por sessão | Sem sincronia, "mesmo instante" não existe — bloqueia T7/T8 |
| T3 | **Kappa humano em janelas.** 60 janelas de 2 min gravadas pelo T1 (sala 1a3 e 3a6, horários variados), as 2 avaliadoras pontuam cegas com o codebook v1, criança-alvo marcada por caixa no 1º quadro; **alfa de Krippendorff ordinal**; 7 dias depois, 15 janelas repontuadas sem ver a nota anterior (intra-observador). Registrar `alfa_inter, alfa_intra, n, medido_em` em `obs_codebook` | T1 + sliders; ~3 h por especialista | Semana 3 (+ 1 dia na semana 4) | Alfa inter ≥ 0,6 no agregado; intra ≥ 0,7. Por turma é diagnóstico, não portão (n pequeno) | Reescrever âncoras; repetir. **Não** avançar para modelo |
| T4 | **Preencher `video_inicio_s`/`video_fim_s`.** Semântica: offsets **relativos a `relogio`** (−90/+90); `janela_*` relativos ao início do clipe; adicionar `video_path`, `video_camera`. Job: clipe pela API do Frigate (ou `reolink_aio` `NvrDownload` com início/fim arbitrários — não precisa de "blocos de 5 min"); `ffmpeg -ss … -c copy` corta em keyframe → registrar o instante real do 1º quadro (`ffprobe`); pular `modo = 'gravacao'`; 1 câmera por padrão, N só para golden/T8 | T1, T2 | 2 dias, semana 3–4 | 100% das entradas novas com sala recebem clipe em < 5 min; em 10 clipes ao acaso, o evento narrado aparece na janela em ≥ 9 | Ajustar offset/GOP |
| T5 | **Pose infantil offline.** 200 quadros 4K estratificados por postura (em pé / sentada / agachada / de bruços), câmera e faixa (1–3, 3–6), das 18 autorizadas; anotar 100 (pré-anotar com RTMPose, corrigir); RTMPose-m via rtmlib em CPU; PCK@0,5 e OKS por postura e grupo de keypoints; altura em px da criança mais distante; confiança média de punho | Clipes do T1 | 3 dias, semana 4 | PCK@0,5 ≥ 0,7 em pé/sentada (cabeça+ombros+punhos), ≥ 0,5 agachada/de bruços; altura ≥ 150 px; punho > 0,5 em ≥ 70% dos quadros | Parcial → plano B (caixa + orientação de cabeça). Total numa câmera → reposicionar "sala MEIO" (grátis) e repetir; se persistir, 2 câmeras fixas oblíquas por sala (seção 5) |
| T6 | **Persistência de identidade.** RF-DETR-N + ByteTrack a 5 fps em 10 min × 3 câmeras da sala 1a3 (mesmo intervalo); auditoria manual a cada 5 s de qual criança está em cada track; opcional: marcador visual na peça usada o dia inteiro (topo/ombros/costas), como verdade "entre avistamentos" | T1, T2 | 2 dias, semana 4 | **Sem portão** — mede: mediana e p90 de duração de track, trocas por criança-hora, fração recuperável por fusão entre câmeras | Mediana < 60 s (esperado) → UWB obrigatório; fusão recupera > 50% → começar com 2 âncoras por sala |
| T7 | **VLM em quadros amostrados.** 60 janelas com consenso humano do T3; 3 variantes: A = quadro inteiro do substream com caixa na criança; B = recorte 512² do main; C = 4 quadros em vez de 16. `claude-opus-5`, Batch, codebook em `cache_control`, saída estruturada, `custom_id = janela:variante`; gravar com `avaliador_tipo = 'modelo'` | T3, T4; **< US$ 5** | 2 dias, semana 4 | Alfa modelo×consenso ≥ 0,7 × alfa humano em envolvimento; entre câmeras (T8) ≥ 0,6 | B ≫ A → substream não basta para o VLM (mais um número para disco/GPU) |
| T8 | **Teste-reteste entre câmeras** (na Etapa 3, não na semana 2). Camada 1 (sanidade): contagem de pessoas por segundo entre câmeras que **veem a mesma região** — não a "sala MEIO", que tem campo distinto; camada 2 (o teste de verdade): nota humana ou do VLM da **mesma criança** em duas câmeras no mesmo instante. Tabela `reteste_cameras (instante, cam_a, cam_b, metrica, valor)` como série histórica de ruído | T2, T3/T7 | Junto com T7 | Alfa entre câmeras ≥ 0,6; ruído entre câmeras < efeito que se quer detectar | Ângulo/oclusão inviabilizam a medida contínua naquela sala → reposicionar ou trocar câmera |
| T9 | **Áudio das câmeras.** 30 min de áudio de uma câmera de sala + anotação manual: o VAD separa fala de ruído a 3 m? | T1 | 1 tarde | Fração de voz concorda com anotação (ICC ≥ 0,7) | Mic de câmera não serve nem para clima sonoro → array de sala entra na lista |
| T10 | **Ativar `meal_events`.** Rodar o fluxo existente na cozinha por 1 semana (0 eventos hoje); 2 avaliadoras cegas em ~100 pares → `meal_golden`; adicionar coluna de versão de modelo | Nada novo | 1 semana, em paralelo | Kappa humano em `consumed_overall` reportado; pipeline roda 5 dias | É a primeira aplicação real do padrão golden |

### O que NÃO dá para testar sem comprar

| O que | Por que nenhum teste com o parque atual responde | O que produz o número para a compra |
| --- | --- | --- |
| Identidade determinística por criança | Visão sozinha fragmenta ID (T6 mede quanto) | T6 → piloto UWB (seção 5) |
| Material, sequência, repetição, devolução | Não há tag nem catálogo de materiais | Encomendar o piloto RFID na semana 1 (lead time) |
| Linguagem por criança | Microfone de câmera não atribui fala; não há gravador | T9 diz se o mic de câmera serve para clima sonoro; vestível é compra |
| Pose contínua em 16–17 câmeras | Não roda em CPU (T5 é offline) | T1 (CPU) + T5 (px/mão) → GPU |
| Sono | Confirmar **onde** é a sesta (as salas 1a3/3a6 já têm câmera; a lista de 10 espaços não tem "sala de sono") | Só se a sesta for em espaço sem câmera |
| Retenção de vídeo > alguns dias | Depende do disco que existe | T1 → HD |

Achados 5–8 da dimensão de testes foram refutados na terceira rodada (todos os quatro, na
prescrição): kappa não pode usar as transcrições e são 2 avaliadoras; pose offline mede com
OKS/AP e ~120 quadros corrigidos, não PCK em 100; o VLM custa pela saída com thinking (usar
`effort = 'low'`); T6 não dimensiona âncoras UWB (≥ 3 por sala é geometria). A tabela acima já
reflete isso; detalhes na Revisão 2.1.

---

## 5. O que comprar de hardware

### O que muda com a meta de monitoramento contínuo

O documento de 29/08 dizia "não comprar câmera — já tem 17", não dimensionava disco para o
parque real, não tinha nenhum microfone para as crianças e não nomeava produto nem preço para
UWB e RFID. Sob a meta nova isso vira uma lista de compras real — mas a regra mais importante
que o painel deixou é a **ordem**: nada se compra antes do inventário (T0) e da prova de vida
(T1), e cada item entra com o **teste que produz o número** ao lado. Dos 8 achados desta
dimensão, 6 foram refutados na prescrição (produto fora de linha, preço não verificado, conta
de decodificação errada, lista que não se conecta) — a tabela abaixo é a versão corrigida.

### O que mantemos

- **Desktop com GPU de consumo, não um Jetson por câmera** (análise P10). Correção: Jetson não é
  excluído por decodificação (Orin Nano decodifica 11 × 1080p30; Orin NX 18 ×) — é excluído por
  simplicidade para um construtor solo e por preço por stream.
- **2 HDs de vigilância no próprio desktop de edge, sem NVR proprietário nem NAS** na fase
  mínima; 245–612 GB/dia são 3–7 MB/s de escrita, trivial.
- **Pilotos pequenos antes de escala** (1 estante, 5 crianças, 2 semanas).
- **Nenhuma compra na primeira semana** — continua verdade.

### O que corrigimos

- **"Não comprar câmera"** → "não comprar câmera **antes do T5**". As câmeras nunca foram
  inventariadas; a do pátio é um TrackMix (PTZ com auto-tracking que **move a câmera** e
  destrói a geometria fixa do tracking; substream fixo de 640×360; RTSP instável). Regra:
  toda PTZ fica **travada em guard position com auto-tracking desligado** ou sai da visão
  computacional. Se o T5 mostrar criança < 150 px ou punho invisível numa sala, aí sim 2
  câmeras fixas 4K oblíquas por sala.
- **Caixa de edge:** a conta "17 × 4K × 5 fps = 85 quadros/s de decode" estava **errada** —
  H.265 não deixa pular quadros; o decoder processa o fps de origem. Ou se fixa o fps na
  câmera (5–10) ou se infere no substream; caso contrário são 425 quadros 4K/s, que saturam a
  placa "recomendada". A spec abaixo já assume fps fixado na câmera.
- **Rede:** "nenhum documento fala de rede" era falso (a análise tinha "60 Mbps sustentados" e
  "switch PoE R$ ~2 k"); o que falta é especificação. E o diagnóstico "quedas de RTSP → cabear"
  estava errado: a câmera que cai na discussão do Frigate é a TrackMix **PoE**; o remédio é
  protocolo (HTTP-FLV / go2rtc / Neolink), não cabo. Se as câmeras já estão num NVR PoE, o
  switch é compra redundante.
- **Microfones:** LENA (US$ 329/unid. + US$ 5.000 de setup + US$ 3–6 k/ano) sai da lista — o
  que dá AWC/CTC/CVC é o pipeline, não o hardware, e o pipeline livre existe (com a ressalva de
  licença do VTC, seção 3). Gravador Sony ICD-PX470 no bolso de criança de 1–3 anos é
  inadequado (74 g, 114 mm, plástico rígido). Array de mesa (ReSpeaker) no teto sobre 20
  crianças tende a capturar a voz mais alta e mascarar as baixas — só para clima sonoro/DOA.
- **UWB:** MDEK1001 e Pozyx Creator constam como descontinuados (**não verificado** — sites
  bloqueados). O repositório Makerfabs **já traz** exemplo multi-âncora/multi-tag com TDMA
  testado em 8 tags — logo "firmware de 2–4 semanas" era exagero; o que falta é trilateração
  (~1 dia) e, o risco real, **escalar o escalonador de 8 para 55 tags a 1 Hz**. Capacidade
  "150 tags @ 1 Hz" é do PANS do DWM1001 (outro produto) — não transfere.
- **RFID:** "leitor US$ 300–800 está subestimado" era falso — essa faixa é exatamente a classe
  Chainway/Chafon de 4 portas que um solo compraria; Impinj/Zebra (US$ 1,2–1,5 k) são a classe
  acima. Antena near-field **não** é o ponto de partida: 25–50 zonas por sala com mux e coaxial
  ao alcance de crianças é integração demais. Primeiro **1 antena far-field por estante em
  potência baixa + histerese em software** (ausência contínua > 20–30 s = retirado; presença
  > 60 s = devolvido); near-field como fallback se o piloto mostrar falso "retirou" com criança
  trabalhando a < 1 m da estante. Hub de antenas Impinj só funciona com leitor Impinj — a lista
  "Chafon + hub Impinj" não se conecta. Banda brasileira: **902–907,5 e 915–928 MHz**; leitor
  ETSI 865–868 não serve.
- **Identidade barata antes do UWB (marcador visual):** ideia mantida, fundamentação corrigida.
  "12 cm a 5 m" vinha de um threshold configurável do OpenCV (`minMarkerPerimeterRate`, default
  0,03, não 0,05) e de um HFOV de câmera suposta — não é capacidade medida; degrada forte acima
  de 45–60° de inclinação e com blur. O marcador tem de ir na peça usada **o dia inteiro**
  (camiseta/colete/boné — o avental Montessori é de vida prática, não do dia todo), na
  superfície que a câmera de teto vê (topo, ombros, costas). Métrica honesta: "entre
  avistamentos" (marcador k visto como tracklet A em t1 e B em t2 — o tracker ligou?), não
  "minutos com identidade correta / minutos visível".

### Lista por prioridade

Câmbio assumido R$ 5,50/US$ (verificado em 05/09: R$ 5,12). **As conversões abaixo não incluem
imposto de importação** — acima de US$ 50 são 60% − US$ 30 + ICMS 17–20%, o que quase dobra o
preço "landed" (ver 2.1). Preços marcados ✔ foram verificados pelo painel; os demais são ordem
de grandeza **não verificada** — cotar com data antes de comprar.

| # | Item | Spec mínima | Faixa de preço | Pré-requisito de teste | Por quê |
| --- | --- | --- | --- | --- | --- |
| 0 | **Nada** | — | R$ 0 | T0 inventário + T1 prova de vida | Metade dos itens abaixo pode ser zero dependendo do que o inventário mostrar (NVR existente, PoE existente, mic nas câmeras) |
| 1 | **HD de vigilância** | 2 × 8 TB (WD Purple ou equivalente), espelho | R$ 1.100–2.100 cada (não verificado) | T1 passa e o PC/NVR atual não retém 7–14 dias de main stream | 14 dias de 2 salas + pátio em 4K cabem; 30 dias de 17 × 4K **não** cabem em 16 TB |
| 2 | **Caixa de edge** | Desktop Ryzen 5 7600 / i5-13400 (iGPU Intel dá QuickSync), 32 GB, NVMe 2 TB, fonte 650 W, 2 baias 3,5", nobreak. GPU **mínimo** RTX 5060 8 GB; **recomendado** RTX 5060 Ti 16 GB (pose + áudio + fine-tune na mesma placa; VRAM é o gargalo). 1 NVDEC em 4060/5060/4070; 2 em 4070 Ti/4080/4090 | RTX 5060: R$ 2.200–2.600 (parcial ✔, mín. histórico R$ 1.800); 5060 Ti 16 GB ≈ R$ 3.960 (não verificado). Máquina: **R$ 6–7 k** mínimo, **R$ 9–11 k** recomendado | T1 mostra CPU/iGPU saturados **ou** T5 aprova pose e a meta pede pose contínua. Antes: fixar fps 5–10 no main stream das câmeras e medir decode com `ffmpeg -hwaccel` | Só decide GPU com número; Jetson só se um dia quiser nó fanless por sala (≤ 4 câmeras) |
| 3 | **Rede** | Só após T0. Se câmeras Wi-Fi: cabear (Cat6, ~R$ 500 em material). Se não há PoE: switch PoE+ 24 portas com orçamento ≥ 250 W (~R$ 2–3 k, não verificado); VLAN de câmeras sem rota à internet | R$ 0–3,5 k | T0 | Provavelmente já existe NVR PoE Reolink → puxar RTSP do NVR por canal; não comprar antes de saber |
| 4 | **Câmeras fixas** | 2 × 4K PoE oblíquas por sala principal, a 2,5–3 m, campos sobrepostos. Reolink RLC-810A (8 MP, 87° HFOV, fixa) ✔ US$ 90–130 ou Intelbras VIP 3830 IA (preço BR não verificado) | US$ 90–130 cada ✔ (BR não verificado) | **T5 reprova** px/mão numa sala, depois de tentar reposicionar a "sala MEIO" | Não comprar antes de medir nas câmeras reais |
| 5a | **Gravador vestível (piloto de linguagem)** | 5 gravadores de lapela USB leves, no mesmo colete/camiseta do UWB; formato que sobreviva a criança de 1–3 anos | R$ 150–300 cada (não verificado) | T9 feito; Etapa 5b aprovada; codebook de linguagem escrito | Única forma de "linguagem por criança"; LENA descartado |
| 5b | **Array de sala (opcional)** | ReSpeaker XVF3800 4 mics, 1–2 por sala, teto ~2,5 m | US$ 50–55 cada (não verificado) | T9 mostra que o mic de câmera não serve nem para clima sonoro | Só clima sonoro/DOA; nunca "quem falou" sozinho |
| 6 | **RFID piloto** (1 estante, 30 materiais, 2 semanas) | Leitor UHF 4 portas classe Chainway/Chafon, **banda 902–928 MHz**, 1 antena far-field/estante em potência baixa (near-field como fallback), 100 tags passivas; tabela `materiais` no banco | US$ 150–700 leitor (cotar) + antena + tags ≈ **R$ 2–4 k** (não verificado, sem imposto) | **Cotar nas semanas 1–2; pedir no fim da semana 2 se o T1 provar captação, com aprovação do dono** (ver 2.1); instalar após o kappa | Portão de acurácia: ≤ 2% falsos "retirou" em 50 passagens a 30 cm; ≥ 95% retiradas detectadas em < 2 s |
| 7 | **UWB piloto** (4 âncoras + 5 tags, 2 semanas) | 9 × Makerfabs **MaUWB_ESP32S3** (comandos AT, 8 âncoras + 64 tags/rede) + 5 LiPo 500 mAh + caixas + carregador; trilateração própria no edge; MQTT a 1 Hz; alternativa DWM3001CDK ≈ US$ 30 | US$ 54,80/placa (não verificado) ≈ **R$ 3,3–5 k landed** com imposto (ver 2.1) | **T6 mede** a fragmentação; RFID piloto passou | Portão: mediana ≤ 30 cm e p90 ≤ 60 cm **com crianças presentes** (NLOS); tag intacta e bateria ≥ 8 h em 100% dos dias; nenhuma retirada pela criança em > 1 de 10 dias. Riscos: escalar TDMA 8 → 55 tags; bateria sem deep sleep ~5–8 h; volume da tag em 1–3 anos. Alternativa comercial por orçamento (Sewio, Pozyx Enterprise) |
| 8 | **Marcador visual** | Impresso em tecido/termocolante na peça usada o dia inteiro, 18 autorizadas | ≈ R$ 100 | Antes do T6 | Verdade de identidade "entre avistamentos" para medir o tracker; não substitui UWB |
| 9 | **Câmera IR na sala de sesta** | 1 × PoE com IR | US$ 90–130 (não verificado) | Só se a sesta for em espaço **sem** câmera (confirmar) | Sono só entra com sensor |
| — | **Escala** (depois dos pilotos passarem) | 12 âncoras + 55 tags UWB ≈ 67 placas; 2 leitores RFID + 8 antenas + 500 tags; 47 gravadores vestíveis; 17 câmeras em fps fixo | UWB ≈ R$ 16 k + R$ 3 k; RFID R$ 8–25 k; vestíveis R$ 7–14 k (tudo não verificado) | Todos os portões de piloto | Não orçar escala antes de os pilotos produzirem número |

### Orçamento por fase

| Fase | O que entra | Total (ordem de grandeza) |
| --- | --- | --- |
| 0 — 4 semanas de teste (seção 4) | Nada; talvez 1 HD | **R$ 0–2 k** |
| 1 — mínimo viável (2 salas, 7 câmeras, edge, HDs, pilotos RFID/UWB/áudio) | Itens 1, 2 (mín.), 6, 7, 5a, 8 | **R$ 12–20 k** (não verificado) |
| 2 — recomendado (16–17 câmeras, áudio vestível para 47, UWB em 3 salas, RFID em 2 salas, sem LENA) | Item 2 (rec.), rede se preciso, câmeras se T5 reprovar, escala | **R$ 40–65 k** (não verificado) |

A linha "escala" só existe depois dos pilotos. O painel foi explícito: **todo preço deve
entrar com cotação e data**, não com ordem de grandeza — esta tabela é o teto de expectativa,
não a ordem de compra.

---

## Roadmap integrado (revisão 2)

O que mudou de posição em relação a 29/08: **testes de captação (T0–T2) entram na semana 1 em
paralelo com o codebook**, não na Etapa 3; **kappa usa janelas gravadas, não transcrições**;
**RFID é encomendado na semana 1 e instalado após o kappa** (não no mês 3); **áudio vestível
vira etapa própria (5b)**; **modelo de dados do contínuo entra em dois tempos** (janela agora,
eventos quando houver evento); **visão continua na Etapa 6, mas a infra nasce para 16–17
câmeras**; **compras só com número medido**.

| Quando | O quê | Portão | Custo acumulado |
| --- | --- | --- | --- |
| Semana 1 | Codebook v1 (uma tarde) · T0 inventário técnico (meio dia) · migração única (DDL da 2.1: `cameras`, `dev_janelas`, `obs_*`, `materiais`) · sliders na página · T1 montado no PC existente com 3 câmeras · **cotar** piloto RFID/UWB (pedido só após o T1, com aprovação) | 100% das câmeras de sala com stream testado; N de main streams do NVR registrado | R$ 0 |
| Semana 2 | T1 rodando · T2 sincronização · sexta: calibração em voz alta com 10 janelas do T1 · começa o dicionário operacional por domínio (2–3 semanas, em paralelo) | Uptime ≥ 98% por câmera em 5 dias | R$ 0 (talvez 1 HD) |
| Semana 3 | **T3 kappa** em 60 janelas × 2 avaliadoras · T4 job de clipe | **Portão 1:** alfa inter ≥ 0,6 — senão reescrever âncoras e repetir | R$ 0 |
| Semana 4 | T5 pose offline · T6 identidade · T7 VLM · T8 teste-reteste · T9 áudio de câmera · T3 intra-observador · T10 `meal_events` ativado | Decisões de compra **com número**: GPU sim/não, câmera sim/não, UWB quantas âncoras, mic de câmera serve? | < US$ 5 de API |
| Semanas 5–6 (Etapa 3 revista) | Sorteio diário de janelas por sala × hora · golden ≥ 60% aleatórias + ≥ 10 blocos contínuos de ≥ 2 h · `meal_golden` · RFID piloto instalado quando chegar | Golden fechado; RFID: ≥ 95% retiradas, ≤ 2% falsos | R$ 2–4 k |
| Semanas 6–8 (Etapa 4 revista) | VLM como rotulador amostrado (2–4 k janelas/mês) · calibração contínua semanal (20 janelas, alfa em janela móvel de 4 semanas) | Alfa modelo ≥ 0,7 × alfa humano | + ≈ US$ 120–245/mês |
| Mês 3 | Compra do edge se T1/T5 pediram · UWB piloto (5 crianças) · **Etapa 5b** áudio vestível piloto (5 crianças) · `dev_eventos`/`dev_cobertura` nascem com o primeiro evento real | UWB: mediana ≤ 30 cm, p90 ≤ 60 cm; áudio: ICC ≥ 0,7 nas contagens | R$ 12–20 k acumulado |
| Meses 4–6 (Etapa 6) | Infra para 16–17 câmeras · modelo em 2 salas · fine-tune de pose · local-first + sync · job `reprocessar` · vigilância diária por câmera | Modelo dentro do teto humano; ruído entre câmeras < efeito; 2 h offline sem perda | idem |
| Mês 6+ (Etapa 7) | `janelas_features` · MixedLM aninhado criança > criança-dia com peso de cobertura · `eventos_ambiente` · estender a pátio e cozinha · escala de UWB/RFID/vestíveis se os pilotos passaram | Efeito de idade em ≥ 3 meses > ruído entre câmeras **e** > diferença de cobertura | R$ 40–65 k acumulado (não verificado) |
| Depois | Etapa 8 licenciável | — | — |

## Contradições resolvidas entre as dimensões

| Contradição | Prevalece | Por quê |
| --- | --- | --- |
| Hardware: "comprar 2 câmeras fixas por sala" × Testes: "medir nas câmeras reais primeiro" | **Medir (T5)** | Reposicionar a "sala MEIO" é grátis; comprar antes é o erro que o próprio painel condena |
| Testes: "gravar só o substream 640×360" × Arquitetura/Ferramentas: "gravar o main stream" | **Main stream** | Gravar não decodifica; 360p destruiria o golden (mãos somem) |
| Plano de IA: "RFID/UWB/áudio na semana 1" × refutador: "empilhar hardware dilui o kappa" | **Encomendar RFID na semana 1, instalar após o kappa; UWB e áudio depois, uma modalidade por vez** | Lead time de importação; o kappa é o portão mais decisivo e cabe em 3 semanas |
| Hardware: "Jetson nem decodifica" × refutador | **Desktop, por simplicidade — não por decode** | Orin Nano decodifica 11 × 1080p30; a exclusão era por premissa errada |
| Arquitetura: "Etapa 0 com `dev_eventos` particionada agora" × refutador | **`dev_janelas` agora; `dev_eventos` quando houver evento; partição depois** | Quatro tabelas vazias até o mês 3 violam "nenhuma etapa é infraestrutura para depois" |
| Contexto: "`meal_events` em produção" × banco | **0 eventos** | Corrigido nas correções de fato; T10 ativa |
| "17 câmeras" × banco | **16 nomes, ~15 aparelhos** | "sala MEIO" compartilhada; pátio = 1 TrackMix com 2 lentes (provável) |
| "Custo de VLM não importa" × meta contínua | **"Não importa na amostra"** | 40× em regime contínuo; scorer contínuo é local |
| "TimescaleDB — confirmar" | **Fora** | Indisponível em PG 17 no projeto |
| "Tempo parado — nunca" × sono no escopo | **Nunca para concentração; padrão para sono** | Actigrafia detecta sono por imobilidade |
| "Kappa vira o teto para sempre" × modelo treinado em consenso | **Denominador no subconjunto amostrado, em janelas aleatórias; recalibrado** | Modelos podem superar o acordo par-a-par; cortes não cobrem sesta/fila/transição |
| "Sala MEIO ajustável = Wi-Fi/móvel" | **Não há evidência de Wi-Fi**; é uma câmera física, fonte de drift | A coluna real diz "como complemento — ajustável" |
| "Frigate faz retenção por marca-d'água e alerta" | **Não faz** — só limpeza de emergência | Construir |
| "Kappa com as 40 transcrições" | **Não** — são testes de microfone | Material novo do T1 |

## Riscos que continuam de pé

1. **O kappa pode não passar** — e agora ele depende do T1 estar gravando; se a captação
   atrasar, o portão 1 atrasa junto. Mitigação: T1 começa na quarta da semana 1.
2. **As câmeras podem não servir** para pose (px/mão) em alguma sala — T5 decide na semana 4,
   não no mês 5.
3. **Identidade:** visão sozinha vai fragmentar (T6 mede), UWB DIY tem risco real em escalar
   de 8 para 55 tags, e a tag pode não sobreviver a criança de 1–3 anos. Sem identidade
   determinística, o sistema mede a sala, não a criança.
4. **Linguagem por criança exige vestível em 47 crianças** — carga operacional diária de
   carga/descarga que ninguém dimensionou.
5. **Efeito menor que o ruído** — só o T8 e a Etapa 7 respondem.
6. **18 de 47 com autorização de imagem** limita o corpus de vídeo; a escala humana cobre 47.

## Primeira semana depois desta revisão

- **(Esta primeira semana foi substituída pela versão única da Revisão 2.1 — mantida aqui como
registro.)**

- **Segunda:** manhã — T0: abrir cada câmera/NVR, anotar modelo, streams, fps, bitrate, PoE,
  microfone; ligar RTSP/HTTP e NTP; confirmar com a equipe o que é "sala 1", "sala MEIO" e as
  duas lentes do pátio. Tarde — codebook v1 (3 dimensões × 5 níveis, âncora comportamental).
- **Terça:** migração mínima (`obs_codebook`, `obs_avaliacoes` com `janela_id`/`entrada_id`
  opcional, `dev_janelas`, `obs_golden` por janela, `salas_cameras` normalizada, `materiais`
  vazia); corrigir `'sala 1'` → `'sala 1a3'` se confirmado; **encomendar o piloto RFID**
  (banda 902–928 MHz) e as tags.
- **Quarta:** go2rtc + Frigate no PC existente com as 7 câmeras das salas (HTTP-FLV; detect
  no substream a 5 fps; record do main); `captacao_stats` gravando — T1 começa.
- **Quinta:** sliders na página de observação (3 dimensões, 15 s por entrada); T2 evento de
  luz + `now()` do servidor ao lado do `relogio`.
- **Sexta:** as 2 avaliadoras pontuam em voz alta 10 janelas de 2 min **gravadas pelo T1**
  (não as transcrições), calibrando a leitura do codebook antes do kappa cego da semana 3.

Custo da semana: R$ 0 em hardware, R$ 0 em API — mais o RFID em trânsito.

---

## Revisão 2.1 — o que o crítico de completude acrescentou (06/09)

A terceira rodada do painel terminou completa (52 agentes): as 4 refutações que faltavam, as
4 seções que o painel escreveu por conta própria, um crítico de completude com 10 lacunas e
um roadmap integrado. Esta seção registra o que muda em relação ao texto acima. Onde o adendo
contradiz uma seção anterior, **vale o adendo**; o texto anterior fica como está para
preservar o raciocínio.

### Erratas — o que estava errado nas seções acima

| Onde | Estava | Passa a ser | Fonte |
| --- | --- | --- | --- |
| Toda a revisão e a bifurcação | "3 especialistas" | **2 avaliadoras** (a coluna `especialista` tem `claudio`, `Claudio` e `Sonia`; `count(distinct)` contou 3). Confirmar com a escola quem são e quantas horas/semana cada uma pode dar. Com 2 avaliadoras, **kappa quadrático de Cohen** basta (equivale ao alfa ordinal); alfa só se entrar uma 3ª | banco, 05/09 |
| Seção 1, "Plano de IA" | tabela `obs_janelas` | **`dev_janelas`** — uma só tabela de janela, com `origem ∈ {entrada, sorteio, evento, corte}` | lacuna 3 |
| Seção 2, item 2 | Neolink como fallback | **Neolink sai de todas as seções** — AGPL-3.0 e desnecessário: HTTP-FLV via go2rtc é a recomendação oficial do Frigate para Reolink | lacuna 2 |
| Seção 2, itens 1 e 6 | fps do main "5–10"; retenção "14 dias" | Ver **tabela de captação v0** abaixo: main a **15 fps** (motor grosso a 5 fps é inanalisável — um salto de 400 ms são 2 quadros; em Reolink o bitrate independe do fps); retenção operacional **3 dias no piso, 7–14 se o disco permitir**, com cópia para o Storage do que precisa sobreviver | lacuna 1 |
| Seção 5, item 7 | "9 × Makerfabs ESP32 UWB DW3000, US$ 43,80/placa" | **Makerfabs MaUWB_ESP32S3** (US$ 54,80, não verificado): STM32 pré-programado com comandos AT, **8 âncoras + 64 tags por rede**, precisão declarada 0,5 m — não exige firmware de rádio, só trilateração em Python. Alternativa: Qorvo DWM3001CDK ≈ **US$ 30** (não US$ 130–150), com firmware sobre o QM33 SDK. Texto: "10–30 cm em linha de visada; planejar 30–50 cm com corpos no caminho"; portão do piloto **p90 ≤ 60 cm com crianças presentes** (o critério de 30 cm sai) | seção do painel + lacuna 7 |
| Seção 5, todos os itens em US$ | conversão a R$ 5,50 sem imposto | Câmbio verificado 05/09: **R$ 5,12**; **imposto de importação** acima de US$ 50: 60% − US$ 30 + ICMS 17–20% → um XVF3800 de US$ 54 chega perto de **R$ 450**; UWB piloto ≈ **R$ 3,3–5 k landed** (não R$ 2,7 k); UWB escala 67 placas ≈ R$ 19–24 k + baterias/caixas ≈ R$ 3 k | seção do painel |
| Seção 5, item 6 e roadmap | "encomendar o piloto RFID na semana 1" | **Cotação nas semanas 1–2; pedido só no fim da semana 2, se o T1 provar captação, com aprovação do dono**; instalação após o kappa e a chegada (importação 30–60 dias) | lacuna 7 |
| Seção 4, T5 | "PCK@0,5" | **OKS/AP** (PCK sem normalização definida não é reprodutível; PCKh é frouxo em criança porque a cabeça é proporcionalmente grande). 100 quadros não sustentam estratificação postura × faixa × câmera × grupo de keypoints — colapsar estratos ou anotar ~120 quadros com correção sobre RTMPose pré-anotado (6–10 min/quadro com 3–8 crianças, não 2) | veredito T6 |
| Seção 4, T7 | "< US$ 5" | Em `claude-opus-5` o custo é dominado pela **saída com thinking** (US$ 25/M): 180 requisições × 1–3 k tokens de raciocínio = US$ 4,5–13. Usar `output_config.effort = 'low'`; limite de imagem no Opus 5 é 2.576 px / 4.784 tokens, não 1.568 px | veredito T7 |
| Seção 4, T6 | "se a fusão entre câmeras recupera > 50%, começar com 2 âncoras" | **Errado**: trilateração 2D exige ≥ 3 âncoras (4 em 3D); o número de âncoras é geométrico, não depende do tracker. T6 vira baseline sem portão; a acurácia real do tracker vem da Etapa 5, contra as tags, todo dia | veredito T8 |
| Correções de fato | offsets de `relogio` "−3 a −70 s" | Medidos contra `now()` do servidor: **+40 s** (24/08 17:43) e **−14 s** (24/08 18:24 em diante; 03/09), no mesmo PC — quase metade da margem de ±90 s do clipe. Gravar `relogio_servidor` e aplicar `offset_s` no corte | veredito T4 |
| Seção 4, T0 | substream "640×360" | Fixo em 640×360 **só na TrackMix**; vários modelos 4K Reolink têm substream 896×512. Ler da câmera, não assumir | veredito T6 |
| Seção 1, mapa | Sono "PASSIVO-CANDIDATO" | **NÃO PASSIVO** até a escola responder onde e quando cada agrupada dorme e se há câmera ali | lacuna 5 |

### Vereditos que oscilaram entre as duas rodadas

A verificação adversarial rodou duas vezes em 12 achados (a segunda rodada refez alguns em vez
de reaproveitar). Onde as duas rodadas discordaram, o achado está marcado **"dividido"** no
apêndice — leia como "diagnóstico aceito, prescrição em disputa", e não como veredito. São
eles: contas de 17 câmeras (arquitetura 1), modelo de dados (arquitetura 3), áudio contínuo
(arquitetura 5), ingestão/decodificação (ferramentas 2), detector e tracker (ferramentas 3),
pose e modelo temporal (ferramentas 4), anotação (ferramentas 7), stack mantida (ferramentas
8), ativos que já existem (testes 1), caixa de edge (hardware 2), armazenamento (hardware 3),
linguagem sem captação (hardware 5). Nenhum deles muda uma decisão: em todos os casos o que
está em disputa é número, produto ou ordem — que a tabela de captação, a linha de stack e o
roadmap abaixo fixam.

### Tabela de captação v0 (uma só; substitui as quatro contas das seções)

Escrita agora; a coluna "medido" é preenchida no T0/T1 e a conta é refeita **uma vez**.

| Parâmetro | Decisão v0 | Medido (T0/T1) |
| --- | --- | --- |
| Aparelhos | 15–16 ("sala MEIO" é 1 aparelho em 2 salas; pátio provavelmente 1 TrackMix) | — |
| Canais no NVR | = aparelhos (TrackMix = 1 canal) | — |
| Streams de inferência | = aparelhos + 1 (TrackMix = 2 lentes) → 16–17 | — |
| Resolução gravada (main) | 4K nativo, sem downscale (TrackMix: resolução/codec fixos, só fps) | — |
| fps do main | **15** (bitrate independe do fps em Reolink) | — |
| fps de inferência | **5** nas 7 câmeras das salas (envolvimento, autonomia, social); **15** em "Patio (Ângulo largo)" + PATIO-B nas faixas de pátio (motor grosso); **2** nos outros 7 espaços (presença) | — |
| Codec / bitrate | H.265, CBR "fluency first" 4–8 Mbps (faixa da TrackMix; hipótese para as demais) | por câmera, 72 h, ffprobe/iftop |
| Detecção | substream (640×360 TrackMix; 896×512 em vários 4K) a 5 fps; OpenVINO CPU/iGPU até haver GPU | — |
| Retenção operacional | **3 dias** no piso (é o que o plano exige); 7–14 se o disco permitir. Expurgo: vídeo bruto → clipes não-golden → nunca Parquet nem golden | — |
| Cópia para o Storage | clipes de janela com rótulo, golden (permanente), reteste entre câmeras, 10 quadros/dia/câmera para vigilância; nunca vídeo contínuo | — |
| GB/dia (17 × 9 h) | 275–551 GB/dia → 3 dias = 0,8–1,7 TB; 7 câmeras = 113–227 GB/dia | refazer com o bitrate medido |
| Decodificação | 17 × 15 fps = 255 quadros 4K/s ≈ 2,1 Gpixel/s — cabe em 1 NVDEC (Ada ≈ 3,4) ou QuickSync; medir com `ffmpeg -hwaccel` antes de comprar | — |
| Disco | 2 × WD Purple 8 TB independentes (R$ 2,2–4,2 k, a verificar); 1 cobre 3 dias das 17; o 2º é folga e cópia local do golden | — |
| Alteração na câmera | fps 25 → 15 e CBR **alteram a gravação de segurança da escola** — só depois de confirmar com a direção. T1 começa sem mexer em nada | — |
| "sala MEIO" ajustável | posição fixada por foto + linha em `eventos_ambiente` a cada mudança | — |

### Linha de stack v0 (uma só, para todas as seções)

`pipeline-v0` = go2rtc (HTTP-FLV, 1 conexão/câmera) → Frigate 0.17.2 (record + detect
OpenVINO no substream) → worker Python 3.12/uv: **RF-DETR-S** (`rfdetr`, Apache-2.0;
alternativa RT-DETRv2-S) → **ByteTrack** (código copiado, MIT) → **rtmlib + RTMO-s** (ONNX
Runtime) no contínuo; RTMPose-m só em recortes do golden; Silero VAD no áudio de zona;
pyannote community-1 + faster-whisper só na amostra; Parquet (pyarrow) + DuckDB; sem mmcv no
worker (MMPose 1.3.2 só no contêiner de treino). **Nada de YOLOX, MMDetection, Neolink,
BoxMOT, MediaPipe.** T5, T6 e o baseline de tracker usam exatamente isto — resultado com
YOLOX é descartado. GPU: nenhuma antes de T1 + T5 + golden fechado; quando comprar, RTX 5060
Ti 16 GB. Registro: linha `pipeline-v0` em `obs_codebook` e coluna `pipeline_versao` em
`dev_eventos`, `dev_agregados`, `captacao_stats`, `reteste_cameras`.

### DDL única da semana 1 (substitui os trechos de schema das seções 1 e 2)

Inclui a coluna `projeto` da bifurcação. `dev_eventos`, `dev_agregados`, `dev_ligacoes` e as
tabelas de cobertura **não** entram agora — nascem com o primeiro produtor automático (semana
4+), como a seção 2 já dizia.

```sql
-- entidade câmera (sem credenciais: salas_cameras tem SELECT público)
create table cameras (
  id            text primary key,              -- 'sala1a3-A', 'patio-largo', ...
  sala          text not null references salas_cameras(sala),
  nome          text not null,
  aparelho      text,                          -- id físico; 'sala MEIO' tem 1 aparelho em 2 salas
  fabricante    text, modelo text, firmware text,
  canal_nvr     smallint, host_nvr text,
  protocolo     text check (protocolo in ('rtsp','http-flv')),
  path_main     text, path_sub text,           -- só o caminho, nunca usuário/senha
  res_main      text, fps_main smallint, bitrate_kbps_main int,
  res_sub       text, fps_sub smallint,
  codec         text, hfov_graus smallint, altura_m numeric, ptz boolean,
  tem_mic       boolean, tem_stream boolean,
  fps_deteccao  smallint, fps_pose smallint,   -- da tabela de captação v0
  verificado_em timestamptz
);

create table obs_codebook (
  versao text primary key, descricao text not null, dimensoes jsonb not null,
  vigente_de date not null, vigente_ate date,
  kappa_inter numeric, kappa_intra numeric, n_clipes int, medido_em date, decisoes jsonb
);

create table dev_janelas (
  id          uuid primary key default gen_random_uuid(),
  projeto     text not null check (projeto in ('A','B','comum')),
  aluno_id    uuid references alunos(id),      -- null até haver identidade (UWB) ou marcação manual
  camera_id   text references cameras(id),
  sala        text not null references salas_cameras(sala),
  inicio      timestamptz not null,
  fim         timestamptz not null,
  duracao_s   int generated always as (extract(epoch from (fim - inicio))::int) stored,
  origem      text not null check (origem in ('entrada','sorteio','evento','corte')),
  entrada_id  uuid references observacao_entradas(id),
  clip_path   text,                            -- bucket observacao-video
  janela_rotulo_inicio_s smallint default 30,  -- 2 min centrais do clipe de 3 min
  janela_rotulo_fim_s    smallint default 150,
  presente    boolean,                         -- 'criança fora do quadro' é resultado válido
  criado_em   timestamptz not null default now()
);
create index on dev_janelas (sala, inicio);
create index on dev_janelas (aluno_id, inicio);

create table obs_avaliacoes (
  id uuid primary key default gen_random_uuid(),
  projeto    text not null check (projeto in ('A','B','comum')),
  janela_id  uuid not null references dev_janelas(id) on delete cascade,
  entrada_id uuid references observacao_entradas(id),
  aluno_id   uuid not null references alunos(id),
  avaliador  text not null,                    -- sempre lower(trim())
  avaliador_tipo text not null check (avaliador_tipo in ('humano','modelo')),
  envolvimento smallint check (envolvimento between 1 and 5),
  autonomia    smallint check (autonomia between 1 and 5),
  persistencia smallint check (persistencia between 1 and 5),
  contexto text, material text, adulto_proximo boolean,
  confianca smallint check (confianca between 1 and 5),
  modelo text, codebook_versao text not null references obs_codebook(versao),
  em timestamptz not null default now(),
  unique (janela_id, aluno_id, avaliador, codebook_versao)
);

create table obs_golden (
  janela_id uuid primary key references dev_janelas(id),
  projeto   text not null check (projeto in ('A','B','comum')),
  incluido_em date not null default current_date,
  motivo text, consenso jsonb, permanente boolean not null default true
);

create table materiais (
  id uuid primary key default gen_random_uuid(),
  nome text not null, area text, sala text references salas_cameras(sala),
  tag_epc text unique, estante text, criado_em timestamptz default now()
);

create table captacao_stats (
  ts timestamptz not null, camera_id text references cameras(id),
  camera_fps numeric, process_fps numeric, skipped_fps numeric, detection_fps numeric,
  cpu_pct numeric, ram_mb int, pipeline_versao text not null, primary key (ts, camera_id)
);

create table reteste_cameras (
  instante timestamptz, cam_a text references cameras(id), cam_b text references cameras(id),
  metrica text, valor numeric, pipeline_versao text, primary key (instante, cam_a, cam_b, metrica)
);

create table eventos_ambiente (
  id uuid primary key default gen_random_uuid(), sala text, camera_id text references cameras(id),
  data date not null, tipo text not null, descricao text
);

create table bifurcacao_esforco (
  id uuid primary key default gen_random_uuid(), semana date not null,
  projeto text not null check (projeto in ('A','B','comum')),
  categoria text not null check (categoria in ('construcao','operacao','especialista','hardware_brl','api_usd','outro')),
  quantidade numeric not null, quem text, nota text
);

create table bifurcacao_resultados (
  semana date not null, projeto text not null check (projeto in ('A','B')),
  metrica text not null, valor numeric, n integer, nota text,
  primary key (semana, projeto, metrica)
);

alter table observacao_sessoes add column relogio_servidor timestamptz, add column offset_s numeric;
alter table observacao_entradas
  add column video_path text, add column video_camera text references cameras(id),
  add column video_ref_inicio timestamptz;
comment on column observacao_entradas.video_ref_inicio is 'instante real do 1º quadro do clipe (ffprobe após o corte)';
comment on column observacao_entradas.video_inicio_s   is 'offset em s relativo a relogio (−90)';
comment on column observacao_entradas.video_fim_s      is 'offset em s relativo a relogio (+90)';

update observacao_sessoes set especialista = lower(trim(especialista));
-- só após confirmação com a Sonia:
-- update observacao_entradas set sala = 'sala 1a3' where sala = 'sala 1';
-- alter table observacao_entradas add foreign key (sala) references salas_cameras(sala);
```

Decisões escritas junto com a DDL: rótulo humano = **2 min centrais** (LIS-YC) de um clipe de
**3 min** (±30 s de contexto); feature = **5 min**; um trigger cria `dev_janelas(origem =
'entrada', projeto = 'B')` para cada entrada com sala — o fluxo humano do Projeto B não muda;
o sorteio cria janelas com `projeto = 'A'`; o conjunto de comparação cria com `projeto =
'comum'`.

### Linguagem: regime declarado para o ano 1

**Regime amostrado-rotativo** (`PASSIVO-AMOSTRADO` no mapa de medição): 8–10 gravadores
vestíveis, cada criança 1 dia por semana, bolso costurado; 1 pessoa da escola recarrega e
descarrega por USB no fim do dia (~20 min/dia). Arrays de sala só para clima sonoro. O regime
contínuo (47 gravadores, ~R$ 25 k + estação de carga + operação diária de 47 aparelhos + 16–39
GPU-h/dia de diarização — não cabe na placa da visão) só volta à mesa se o piloto de 2
semanas com 5 crianças fechar **quatro números**: (1) RTF real do pyannote na GPU alvo;
(2) drift entre gravadores (palma no início e no fim do dia; quartzo de consumo deriva ~0,6 s
em 8 h, a verificar); (3) minutos/dia de operação efetiva por gravador; (4) precisão/recall da
atribuição "portadora vs outra criança" em 20 janelas com contagem manual (ICC ≥ 0,7). A
atribuição por canal de maior energia **exige alinhamento entre gravadores** (job de
correlação cruzada por blocos de 10 min) — que não estava em nenhum pipeline.

### Sono e motor grosso: sensor de fato

**Sono:** pergunta à escola na segunda da semana 1 — onde e quando cada agrupada dorme, e se há
câmera nesse espaço. Até a resposta, `NÃO PASSIVO`; se houver espaço sem câmera, decisão de
compra explícita (câmera IR fixa ≈ R$ 900–1.300 landed, a verificar; actígrafo de pulso para
47 crianças é inviável em preço e software).

**Motor grosso:** acontece no pátio, e o pátio estava fora de todos os sensores (UWB em 3
salas; TrackMix travada ou excluída; pose a 2 fps). Correção: "Patio (Ângulo largo)" + PATIO-B
como câmeras de pose a **15 fps nas faixas de pátio**; **+4 âncoras UWB no pátio** no piloto de
escala (≈ R$ 1,5–2,2 k landed); TrackMix travada em Monitor Point com auto-tracking desligado
— se a escola não aceitar (perde a função de segurança), a TrackMix sai da visão e só PATIO-B
cobre o pátio. Se (a) e (b) falharem, motor grosso é reclassificado como "tarefa eliciada
trimestral (TGMD-3 filmado em PATIO-B) + eventos grosseiros da câmera fixa".

### Carga humana com 2 avaliadoras (portão de realismo: > 5 h/semana por avaliadora → cortar)

| Semanas | Cada avaliadora | Construtor (estimativa) | Escola |
| --- | --- | --- | --- |
| S1–2 | 1 h (voz alta + sliders nas entradas novas) | ~40 h/sem | 1 h (perguntas da S1, acesso ao NVR) |
| S3 | 2,5 h (kappa: 60 clipes × 2,5 min) + 2 h (correção de 60 quadros de pose pré-anotados) = **4,5 h** | 35 h/sem | — |
| S4 | 0,7 h (reteste 15 clipes) + 1 h (sorteio) + 0,4 h (20 janelas duplas/sem) ≈ 2,1 h | 30 h/sem | — |
| S5–12 | 1 h sorteio + 0,4 h duplas + 1,25 h blocos (10 blocos de 1 h ÷ 8 sem) + `meal_golden` ≈ **2,8 h** | 20–25 h/sem | 5 min/dia foto da refeição |
| S9–14 (pilotos) | + 0,5 h (20 janelas de vocalização/proximidade com contagem manual) ≈ 3,3 h | 25 h/sem | 20 min/dia recarga de gravadores (S13–14) |

Cortes já aplicados para caber: golden **300** (não 500); blocos contínuos de **1 h** (não
≥ 2 h); anotação de pose só como correção sobre RTMPose pré-anotado (~120 quadros; as ≥ 1.000
instâncias do fine-tune ficam para o mês 5+, com terceirização a orçar); VLM amostrado
limitado ao que 10% de revisão humana comporta (≤ 1.000 janelas/mês); **teto único de API
US$ 150/mês** em `obs_config`. Instrumentos-âncora reduzidos ao mínimo da Etapa 7: ASQ-BR
(pais, trimestral, licença BR a verificar), HTKS-R (gratuito, ≥ 3 anos, semestral), TGMD-3
(kit US$ 183, semestral, filmado em PATIO-B), MB-CDI BR "Palavras e Gestos" (≤ 30 meses, pais);
PDMS-3 (US$ 820, 45–60 min/criança) só com fisioterapeuta/TO parceiro.

### Custo total do ano 1 (capex + opex + horas), sem pressa de gastar nada

| Cenário | Capex ano 1 | Opex mensal | Horas |
| --- | --- | --- | --- |
| Mínimo (2 salas, 7 câmeras, edge, pilotos) | ≈ **R$ 26–35 k** (inclui 12 × Supabase Pro, 8 × API no teto, energia R$ 0,8–3 k, TGMD-3) | Supabase Pro US$ 25 + API ≤ US$ 150 ≈ R$ 900 + energia da caixa 24/7 (~250 kWh/mês; R$ 100–370, tarifa a verificar na conta) | construtor ≈ 1.000–1.200 h/ano (estimativa); cada avaliadora ≈ 110–130 h/ano |
| Recomendado (16–17 streams, UWB em 3 salas + pátio, RFID em 2 salas, áudio amostrado) | ≈ **R$ 63–89 k** (+ R$ 0–6 k câmeras condicionais) | idem | idem |
| Opcionais | + LENA R$ 31–33 k; + linguagem contínua ≈ R$ 25 k + compute a orçar | — | + 1 h/dia de operação de gravadores |

Expectativa honesta, por marco: mês 3 = kappa medido, golden ≥ 300, alimentação medida com
`meal_golden`, piloto RFID rodando; mês 6 = envolvimento contínuo em 2 salas com cobertura
reportada; mês 7–8 = **primeira dimensão passiva validada** (envolvimento); mês 12 = curvas
longitudinais com cobertura para envolvimento, alimentação e autonomia; linguagem no regime
amostrado; sono só se houver espaço com câmera. Nenhuma dimensão além de alimentação vira
"medida" antes do mês 7 — e isso é normal para um sistema que pretende ser o melhor do mundo.

### Riscos técnicos com dono, teste e data

| Risco | Dono | Teste | Quando |
| --- | --- | --- | --- |
| **NVR Reolink limita streams simultâneos** (relato: 12 = 2 main + 10 sub; página oficial bloqueada — **não verificado**). Se for assim, 16–17 main 4K para pose são impossíveis sem tirar as câmeras da sub-rede do NVR, e o switch PoE vira obrigatório | construtor | T0: abrir N main streams em paralelo com `ffprobe` até falhar; registrar N. Se N < câmeras de sala → switch PoE 24p (R$ 2–3 k, a verificar) sobe para junto dos discos | terça S1 |
| Sincronia entre fontes (câmeras NTP; UWB MQTT 1 Hz; RFID Ethernet; gravadores autônomos; navegador +40/−14 s) | construtor | `dev_eventos` com `fonte_relogio` + `offset_s` por fonte; evento diário de sincronia (luz 2× + palma) capturado por câmera, UWB e gravadores | S4 (câmeras), S11 (UWB), S13 (áudio) |
| 65+ clientes no Wi-Fi 2,4 GHz da escola (55 tags + ESP32 + arrays) | construtor | piloto UWB num AP dedicado (EAP225 R$ 590–1.645, a verificar) ou âncoras por PoE; medir perda de pacotes a 1 Hz com 5 e 20 tags | S11–12 |
| Handover de tag UWB entre salas/PANs (firmware MaUWB multi-PAN — não verificado) | construtor | criança com tag caminha 1a3 → corredor → pátio; medir tempo de reaquisição e lacunas de cobertura | S11–12 |
| TrackMix PTZ quebra homografia e reteste | escola + construtor | pedir travamento em Monitor Point; se negado, excluir da visão | S1 (pergunta), S4 |
| Mudar fps/bitrate altera a gravação de segurança | direção | confirmar antes de tocar; T1 começa sem alterar nada | segunda S1 |
| Disco enche | construtor | cron diário: alerta < 15% livre ou retenção < 3 d; teste forçado em S4 | S4 |
| Internet cai | construtor | 2 h sem internet, zero perda (fila SQLite + sync idempotente) | S5 |
| Drift de gravadores de consumo | construtor | palma início/fim do dia; correlação cruzada por 10 min | S13–14 |
| Egress do Supabase > 250 GB/mês | construtor | Parquet sempre lido local; monitorar egress mensal | mensal |
| "sala MEIO" reposicionada sem registro | escola | foto da posição + linha em `eventos_ambiente` | contínuo |

### Primeira semana — versão única (substitui as anteriores)

**Segunda — decisões e perguntas (R$ 0).** (1) Doc de decisões de 1 página: tabela de captação
v0, linha de stack v0, DDL única, regime de linguagem amostrado, sono `NÃO PASSIVO` até
resposta, portão UWB p90 ≤ 60 cm, teto de API US$ 150/mês, riscos com dono. (2) Perguntas à
escola: onde e quando cada agrupada dorme e se há câmera; **quem são as 2 avaliadoras** e
quantas h/semana; onde fica o NVR e como acessá-lo; ponto de rede e energia para a caixa;
`sala 1` = `sala 1a3`?; a TrackMix pode ficar travada?; fps/bitrate das câmeras podem mudar?
(3) Codebook v1 — 3 dimensões × 5 níveis com âncora comportamental; só texto.

**Terça — inventário e migração única (R$ 0).** (1) T0 no NVR/câmeras: `ffprobe` em RTSP **e**
HTTP-FLV por câmera; modelo, firmware, canal, resolução/fps/bitrate main e sub, codec, HFOV,
altura, PTZ, microfone; **abrir N main streams em paralelo até falhar e registrar N**; retenção
real do NVR. (2) Rodar a DDL única; `lower(trim(especialista))`; `sala 1` → `sala 1a3` só
depois da confirmação. (3) Preencher `cameras` (sem credenciais); cadastrar `pipeline-v0` em
`obs_codebook`.

**Quarta — codebook no banco e tela (R$ 0).** Codebook v1 em `obs_codebook`; sliders (3 × 1–5 +
contexto + material + adulto próximo + confiança) gravando em `obs_avaliacoes` via
`dev_janelas(origem = 'entrada', projeto = 'B')` criada por trigger; RPC `select now()` salvo
em `relogio_servidor` ao abrir a sessão, `offset_s` calculado.

**Quinta — T1 no PC atual (R$ 0).** Docker + Frigate 0.17.2 com go2rtc (`preset-http-reolink`),
**3 câmeras** (sala1a3-A, SALA 3a6-A, "sala MEIO"): detect OpenVINO no substream a 5 fps;
record do main **como está hoje** (sem mexer em fps/bitrate até a escola responder); retenção
3 d. Job a cada minuto lendo `/api/stats` → `captacao_stats`; medição de bitrate por 72 h
começa. Se sobrar tempo: 2 h sem internet com a fila local.

**Sexta — calibração e cotações (R$ 0).** Calibração em voz alta (2 avaliadoras + construtor,
1 h): os ~3 áudios úteis de 24/08 + 5 clipes novos de quinta, com o codebook v1; ajustes de
âncora viram v1.1. Cotação nacional de 2 × WD Purple 8 TB e cotação de importação do piloto
RFID (Chafon CF815 / Chainway UR4 + 100 tags), do UWB (9 × MaUWB_ESP32S3 + baterias/caixas) e
do AP dedicado — **para aprovação do dono no fim da semana 2, condicionada ao T1**.

**Não fazer na semana 1:** comprar GPU, instalar CVAT, ligar áudio, alterar fps/bitrate das
câmeras, comprar switch, criar `dev_eventos`/`dev_agregados` (ficam para a semana 4, com o
primeiro produtor automático), ligar `meal_events` por trigger a qualquer coisa.

---

## Apêndice — achados e vereditos, por dimensão

Registro do que o painel produziu, com o veredito das **duas rodadas** de refutação (a segunda rodada refez parte das verificações). "Mantido" e "refutado" = as duas rodadas concordam; **"dividido"** = discordaram — leia como prescrição em disputa, não como veredito. "Refutado" quase sempre = diagnóstico aceito, prescrição corrigida.

### Plano de IA e de medição

_Resumo do revisor:_ O passo a passo atual é um bom plano de psicometria para um sistema AMOSTRADO e centrado em UMA dimensão (envolvimento): rótulo = clipe de 3 min ancorado numa entrada de observação, VLM como pré-rotulador de ~800 avaliações/mês, sensores só na etapa 5. Contra a meta nova (sensoriamento passivo o dia inteiro, todas as dimensões, observação humana como calibração) ele tem quatro furos estruturais: (1) a fonte de rótulo (`observacao_entradas`, tipo `corte`, disparada pela especialista) é uma amostra enviesada de "momentos interessantes", e o corpus dourado feito só dela não representa o dia inteiro que o sensor vai medir; (2) áudio das CRIANÇAS não existe no plano (o áudio atual é a ditação da observadora), e linguagem expressiva é a única dimensão que só se mede com áudio; (3) o papel e o custo do VLM foram calculados para 800 avaliações/mês, e a versão contínua são ~32.600 janelas-câmera/mês (US$ ~415 a ~2.075/mês só de rotulagem, e não auditável como medida); (4) o modelo longitudinal não trata cobertura por sensor, autocorrelação de 96 janelas/dia e drift diário. O que está certo — codebook antes do modelo, kappa como teto, corpus dourado permanente, versão do modelo em cada predição, proibição de "tempo parado" — continua certo e fica MAIS importante, não menos. Adaptação principal: trocar a unidade de tudo (rótulo, kappa, golden, avaliação, modelo) de "clipe/entrada" para "janela fixa criança×tempo", e mover os sensores de contagem (UWB/RFID/áudio) para o começo, porque contagem não precisa de rótulo.

| # | Achado | Tipo | Sev | Veredito | Resumo do motivo (3ª rodada) |
| --- | --- | --- | --- | --- | --- |
| 1 | A unidade de rótulo (clipe ancorado em entrada) não serve para medida contínua: a fonte é enviesada e o golden não cobre o dia | erro | 5 | mantido | LENTE FACTUAL — sustenta. (1) O plano define de fato a unidade de rótulo como clipe [relogio-90s, relogio+90s] ancorado em observacao_entradas (Etapa 3, item 2) e obs_golden.entrada_id referencia observacao_entradas (linha 182), logo o corpus dourado é estruturalmente restrito a trechos disparados por evento. 73 entradas em 24 dias para 47 crianças é amostra de eventos, não de tempo; a meta atualizada do dono é sensoriamento contínuo, então o golden não cobre o domínio que o modelo vai pontuar. (2) Leuven/LIS-YC: procedimento de 'scanning', observar ~2 min e atribuir nota 1–5 — confirmado (str… |
| 2 | Linguagem exige áudio das crianças e o plano só tem áudio da observadora; é a lacuna de sensor mais cara de fechar depois | lacuna | 5 | mantido | Lente FACTUAL — o núcleo se sustenta. (1) O passo-a-passo (/home/user/freeschool-site/docs/desenvolvimento-infantil/2026-08-29-passo-a-passo-sistema.md) não contém a palavra "áudio" em nenhuma das 8 etapas; as dimensões da escala (envolvimento, autonomia, persistência) e a instrumentação (RFID, UWB, visão sobre keypoints) não geram nenhum sinal de linguagem expressiva. O Grok põe áudio como "opcional na fase 1" e a análise crítica não trata linguagem. Contra a meta atualizada (monitorar TODO o desenvolvimento, quase contínuo), é lacuna real. (2) O áudio existente é da observadora: `observacao_… |
| 3 | Falta o mapa dimensão × sensor × instrumento; o plano cobre 3 dimensões visuais e a meta pede 8 | lacuna | 4 | refutado | A LACUNA em si é real e confirmada: o passo-a-passo (linhas 77-97) só tem `envolvimento`, `autonomia`, `persistencia`; nenhuma seção declara, dimensão por dimensão, o que é mensurável passivamente e o que não é, e a meta atualizada pede 8 dimensões. Isso deve ser mantido. O que derruba o achado COMO ESCRITO são as duas lentes:  (a) FACTUAL — a evidência central está mal citada e não sustenta as classificações "passivo e forte": 1. "TGMD-3 automatizado com PoseNet em 1.063 crianças" mistura dois estudos. O artigo da UEL (ojs.uel.br 48131) usou 350 IMAGENS, só o 1º critério da habilidade "saltar… |
| 4 | VLM como medida contínua é 40× o custo calculado e não auditável; o lugar dele é rotulador amostrado e sintetizador, com uma exceção já em produção | erro | 4 | mantido | Lente factual: o achado se sustenta. (1) Preços conferidos na tabela oficial: Haiku 4.5 US$ 1/M entrada (Batch US$ 0,50), Opus 5 US$ 5/M (Batch US$ 2,50), desconto Batch 50% em entrada e saída. (2) A tabela da Etapa 4 (linhas 225–237 do passo a passo) diz literalmente '~800 avaliações/mês ... Clipe (16 quadros) ~US$ 40–60/mês' e 'a conclusão é que ele não importa nesta escala'; refiz a conta: 800 × 16 × 1.521 tokens × US$ 2,50/M ≈ US$ 49 — a tabela original está certa PARA 800 clipes. (3) Em regime quase contínuo (meta atualizada do dono), 17 câmeras × 96 janelas de 5 min × 20 dias = 32.640 ja… |
| 5 | Com 96 janelas/dia por criança, o modelo longitudinal precisa de cobertura por sensor, autocorrelação e sentinela de drift — nada disso está no plano | lacuna | 4 | mantido | LENTE FACTUAL — o núcleo do achado se sustenta. Leitura integral do passo a passo e grep por "cobertura\|missing\|autocorrel\|AR(1)\|independ\|drift\|janela\|5 min" mostram que o plano não contém nenhuma variável de cobertura por sensor, nenhum tratamento de missingness e nenhuma menção a dependência entre observações intradiárias; a Etapa 7 (linhas 302–316) descreve só o modelo misto com efeitos de material/sala/horário/professora/dia da semana/idade, e a invariância é por versão de modelo (linha 310), como o achado diz. A Etapa 6 fixa "agregado por sessão" como unidade no Postgres (linha 287… |
| 6 | Contagem de sensor não precisa de rótulo: a Etapa 5 (UWB/RFID/áudio) deve começar em paralelo com a Etapa 1, não no mês 3 | melhoria | 3 | refutado | O núcleo conceitual do achado (validação de sensor é ACURÁCIA contra evento físico; validação de construto é CONCORDÂNCIA contra codebook — portões diferentes) está correto e vale registrar. Mas o achado cai nas duas lentes. FACTUAL: (1) a evidência principal é mal atribuída — a frase "Só agora. Antes disso ela não teria contra o que ser validada" está na Etapa 6 (visão), não na Etapa 5; o plano não argumenta "rótulo antes de sensor", o único motivo dado para o mês 3–4 é "hardware que ninguém testou com criança de 3 anos" (seção Riscos, item 4). (2) A evidência de banco é falsa: verifiquei o s… |
| 7 | Codebook, kappa e corpus dourado continuam certos, mas a concordância precisa ser calculada por janela e os humanos também precisam de recalibração periódica | melhoria | 3 | refutado | DIAGNÓSTICO SE SUSTENTA; A PRESCRIÇÃO NUMÉRICA NÃO. Lente factual: (a) confirmado — alfa de Krippendorff trata ordinal, N avaliadores e dados faltantes (Hayes & Krippendorff 2007); mas o revisor omite que kappa ponderado quadrático é algebricamente ≈ ICC(2,1) (Fleiss & Cohen 1973), logo 'kappa E alfa E ICC' é redundância, não ganho. (b) confirmado por leitura: linha 142 do passo a passo faz `join ... on b.entrada_id = a.entrada_id`; com janelas aleatórias de captação contínua a chave muda mesmo. (c) confirmado: deriva de observador e recalibração periódica são práticas documentadas (PMC2713814… |
| 8 | Manter: codebook antes do modelo, teto humano, corpus dourado permanente, versão em cada predição e a proibição de 'tempo parado'; meal_events prova que o padrão funciona | confirmacao | 4 | refutado | As cinco citações existem no passo-a-passo e na análise (verificado no texto: 'Antes do código, o codebook', 'vira o teto', `obs_golden ... permanente`, 'Métrica de tempo parado — Nunca', 'versão do modelo + calibração + código de features + vetor cru'). O que cai é o núcleo do achado — 'manter LITERALMENTE' as cinco regras sob a meta de sensoriamento quase contínuo de 8 domínios — e a premissa de que meal_events 'prova que o padrão funciona'.  FACTUAL: (1) Regra 5 ('tempo parado — Nunca'): com SONO dentro do escopo, imobilidade deixa de ser proibida e vira o sinal-padrão do domínio. A actigra… |

### Arquitetura para fluxo contínuo

_Resumo do revisor:_ Os três documentos foram escritos para um regime de "clipes amostrados" (entrada de observação → recorte de ±90 s → rótulo → modelo), e a meta mudou para sensoriamento passivo quase contínuo em 17 câmeras, ~9 h/dia, todas as dimensões. O que sobrevive à mudança: edge obrigatório, vídeo bruto com retenção curta e local, Parquet frio + agregado quente no Postgres, versão de modelo em toda predição, corpus dourado como âncora. O que quebra: (a) toda a aritmética foi feita para 6 câmeras × 8 h e o número real é ~3,2× maior (275–550 GB/dia de vídeo conforme bitrate, 16–17 M person-frames/dia); (b) não existe topologia de ingestão — "gravador local" não é uma decisão, e as Reolink (a linha TrackMix é confirmada pela nota "TrackMix = rastreio automático") têm RTSP notoriamente instável, então a caixa precisa de um único ponto de ingestão (go2rtc/Neolink) que alimenta gravação e inferência; (c) não existe modelo de dados para contínuo — a unidade de tudo (obs_avaliacoes, golden, portões) é `entrada_id`, que não existe num fluxo que roda sem ninguém apertar botão; falta uma tabela de eventos append-only, agregados por janela (5 min/hora/dia) com denominador de cobertura, e a resposta para "o que vai no Postgres × Parquet × nunca sai do prédio"; (d) o TimescaleDB que a análise mandou "confirmar" está descontinuado no Supabase em Postgres 17, que é exatamente a versão do projeto — o caminho é partição nativa + pg_partman; (e) áudio contínuo são 153 h/dia: transcrever tudo é inviável em compute numa GPU de consumo e ruim em qualidade (WER de criança 24% em condição boa, 56–62% em campo distante e barulhento), então o que se guarda são métricas por janela, não transcrição; (f) o custo de rotulagem por VLM, "irrelevante" a 800 clipes/mês, vira US$ 5–7 mil/mês se alguém usar o VLM como scorer contínuo (100 k janelas/mês) — o scorer contínuo tem de ser o modelo local sobre keypoints, e o VLM fica só na amostra de calibração; (g) o pipeline de refeições (camera_id → foto → ai_summary) e a indexação de observação já são "produtores de evento" e devem escrever no mesmo modelo de evento, senão nascem três sistemas. Falhas (câmera cai, internet cai, disco enche, modelo muda) não são tratadas em nenhum dos docs e cada uma corrompe a série longitudinal de um jeito silencioso; a correção é barata se entrar no schema agora (cobertura como denominador, buffer local com sincronização idempotente, retenção por marca-d'água, keypoints brutos versionados para reprocessar sem o vídeo).

| # | Achado | Tipo | Sev | Veredito | Resumo do motivo (3ª rodada) |
| --- | --- | --- | --- | --- | --- |
| 1 | As contas foram feitas para 6 câmeras × 8 h; para 17 × 9 h o vídeo é 275–550 GB/dia e o gargalo passa a ser decode, não inferência | erro | 4 | **dividido** | O núcleo do achado é válido e útil: o passo a passo (Etapa 3, linhas 173–174) de fato carrega a conta de 6 streams × 8 h (216 GB/dia) e despacha o parque real de 17 câmeras com "dimensione o disco antes"; a aritmética de storage do revisor (4–8 Mbps × 32.400 s × 17 = 275–551 GB/dia; 14 dias = 3,9–7,7 TB) confere, e a faixa 4096–8192 kbps / 2–25 fps da TrackMix e a limitação de codec/resolução (Frigate #19650) foram confirmadas. Porém o achado cai em pontos centrais, nas duas lentes. FACTUAL: (1) "toda GeForce tem um único NVDEC" é falso — RTX 4070 Ti tem 2 NVDEC ativos, 4070 Ti Super 2, e a pr… |
| 2 | Não existe topologia de ingestão: 'gravador local' não é decisão, e Reolink por RTSP direto derruba stream | lacuna | 5 | mantido | O núcleo do achado sobrevive às duas lentes. FACTUAL: a lacuna é real — o passo a passo (Etapa 3 item 1 'gravação contínua no gravador local'; Etapa 6 item 1 'detecção + tracking nas 2 salas') não nomeia caixa, software de gravação, forma de entrega de quadros ao worker nem topologia de rede para 17 câmeras; a análise (linhas 280-281) só diz 'um micro com GPU de consumo por escola'. Para a meta atualizada (sensoriamento passivo o dia inteiro em todos os espaços), isso é bloqueante, e severidade 5 é correta. Frigate e go2rtc são MIT (verificado nos LICENSE); Frigate detecta a 5 fps no substream… |
| 3 | Falta o modelo de dados do contínuo: eventos append-only + agregados por janela + cobertura; e TimescaleDB está descontinuado no Supabase em PG17 | lacuna | 5 | **dividido** | FACTUAL: o núcleo do achado se confirma em fonte oficial. Docs Supabase (via MCP search_docs e raw GitHub do repo supabase/supabase): "The timescaledb extension is deprecated in projects using Postgres 17" e, no guia de migração, "Starting from Postgres 17, Supabase projects do not have the timescaledb extension available"; caminho oficial = partição nativa + pg_partman + pg_cron. Prova mais forte: o projeto real ponto-escola-montessoriana (ref rmpnqrvsmxhnrwlgqmdp) roda Postgres 17.6.1.141 e a lista de extensões do projeto NÃO contém timescaledb; contém pg_partman 5.3.1 (disponível, não insta… |
| 4 | meal_events e observacao_indice já são produtores de evento; conectá-los ao mesmo modelo evita nascer um terceiro sistema | melhoria | 3 | refutado | Lente FACTUAL derruba a premissa central. Verifiquei direto no Postgres do projeto ponto-escola-montessoriana (rmpnqrvsmxhnrwlgqmdp) em 2026-09-05: (1) `meal_events` tem 0 linhas, `children` tem 0 linhas, o bucket `meal-photos` tem 0 objetos. As edge functions `analyze-meal`, `analyze-meal-internal` e `camera-ingest` existem (v9, criadas em jul/2026), mas o pipeline nunca produziu um único evento — "em produção" descreve código implantado, não um produtor de dados. (2) `meal_events.child_id` referencia `children(id)`, não `alunos(id)`; `alunos` só é alcançado por `children.aluno_id` (nullable,… |
| 5 | Áudio contínuo são 153 h/dia: transcrever tudo é inviável em compute e ruim em qualidade; guarde métricas por janela, transcreva só a amostra | lacuna | 4 | **dividido** | FACTUAL: os fatos centrais conferem. (1) pyannote-audio é MIT e o README reporta community-1 a 31 s por hora de áudio (AMI) e 37 s/h (DIHARD 3) em H100 80GB — confirmado. (2) WSW 2.0 (arXiv 2505.09972 / IEEE 11204438): WER 0,119 professora e 0,238 criança, F1 ponderado 0,845, kappa corrigido 0,672 para classificação criança×professora — confirmado, mas note que o corpus são 235 min de gravações individuais (12 crianças, 5 professoras), não microfone de teto; o F1 0,845 é otimista para campo distante, o que o próprio achado admite ao pedir teste. (3) Colorado ICASSP24: 54% WER no ISAT (sala de … |
| 6 | Nenhum doc trata falhas (câmera cai, internet cai, disco enche, modelo muda) — e cada uma corrompe a série longitudinal em silêncio | lacuna | 4 | mantido | Tentei derrubar pelas duas lentes e o achado sobrevive no essencial, com quatro correções de precisão.  FACTUAL. (a) A lacuna é real: li o passo-a-passo inteiro; as únicas menções a robustez são "gravação contínua com retenção curta… dimensione o disco" (Etapa 3), "Retenção indefinida" do golden e "toda versão nova repontua o corpus dourado" (Etapa 7). Nenhum DDL tem coluna de cobertura, nenhum trecho fala de operação offline, marca-d'água de disco ou job de reprocessamento. A análise (item 3 de "O que ele acertou") até pede "versão do modelo + calibração + código de features + vetor cru, pra … |
| 7 | O que quebra ao ir de clipes para contínuo: unidade de rótulo, viés da amostra de calibração, custo do VLM ×125 e portão da etapa 6 restrito a 2 salas | erro | 4 | mantido | FACTUAL — as quatro citações do passo-a-passo conferem literalmente (Etapa 1 linha 93: unique por entrada_id; Etapa 3 linhas 175-177: clipe só nasce ao salvar entrada; Etapa 4 linhas 228-231 e 225: tabela de custo e "custo não importa nesta escala"; Etapa 6 linha 277: "2 salas principais"). obs_golden também é chaveada por entrada_id (linha 182). Preços verificados em platform.claude.com: Opus 5 US$5/25 por MTok (Batch 2,50/12,50), Haiku 4.5 US$1/5 (Batch 0,50/2,50); imagem custa ⌈w/28⌉×⌈h/28⌉ tokens, teto 1.560/quadro 1080p no Haiku e 2.691 no Opus 5 (tier alta resolução, Claude 4.7+). Recont… |
| 8 | Manter: Parquet frio + agregado quente, vídeo só no edge, versão de modelo em toda predição e corpus dourado — as contas refeitas confirmam que escala para 17 câmeras | confirmacao | 3 | mantido | FACTUAL — as contas do revisor batem quando refeitas com as premissas que a própria análise fixa (5 fps, ~5–6 pessoas/quadro, int16+zstd, 200 dias letivos): 17 câm × 5 fps × 32.400 s × 6 ≈ 16,5 M person-frames/dia (≈3,3 bi/ano letivo); escalando os 100–180 MB/dia da análise (4,3 M pf) dá 0,38–0,69 GB/dia → 76–138 GB/ano, coerente com '0,4–0,8 GB/dia; 80–160 GB/ano'. Vídeo: com bitrate real de 4K H.265 (Reolink RLC-810A 4–6 Mbps; H.265+ 3–5 Mbps; fonte cctvinfo/pvrblog), 17 × 9 h × 4–8 Mbps = 275–550 GB/dia, upload em tempo real 68–136 Mbps, 30 dias = 8–16 TB × US$0,0213 = US$176–351/mês (o rev… |

### Ferramentas para começar

_Resumo do revisor:_ O passo a passo acerta na arquitetura de dados (Supabase + Parquet/DuckDB, Batch API, saídas estruturadas, detector sem AGPL) mas foi escrito para observação amostrada: a Etapa 6 diz "detector permissivo" e "RTMPose/MediaPipe" sem nomear versão, licença dos pesos nem taxa de quadros, e não existe nenhuma linha sobre ingestão de 17 streams RTSP, decodificação em GPU, áudio contínuo ou o que roda 8 h/dia contra o que roda por amostra. Sob a meta atualizada (sensoriamento passivo, quase contínuo, todas as dimensões, 47 crianças), três coisas mudam de categoria: (1) o custo do VLM deixa de "não importar" — Claude como rotulador contínuo custa US$400–2.000/mês, então Claude vira calibração/pré-rotulagem amostrada e os modelos locais viram a medida; (2) a camada NVR/decodificação vira pré-requisito (Frigate + go2rtc + ffmpeg/NVDEC numa RTX de consumo, detecção no sub-stream e gravação 4K só para clipes); (3) a stack de áudio, ausente nos três documentos, é obrigatória para linguagem em 1–3 anos (VAD + diarização + classificador de tipo de voz, não ASR). Várias alternativas citadas na análise estão obsoletas ou com licença que morde depois: YOLOX parou em 2023, MMDetection/MMPose dependem de mmcv que quebra em PyTorch 2.x/CUDA 12.8, BoxMOT é AGPL apesar de embalar ByteTrack/BoT-SORT (MIT), Sapiens e YOLO-NAS são não-comerciais, D-FINE só é limpo nos checkpoints COCO. A lista concreta proposta abaixo tem licença verificada item a item; o que não consegui verificar está marcado.

| # | Achado | Tipo | Sev | Veredito | Resumo do motivo (3ª rodada) |
| --- | --- | --- | --- | --- | --- |
| 1 | Etapa 4 trata custo de VLM como irrelevante — só vale para 800 avaliações/mês; contínuo custa 30–50× mais e muda quem é a medida | erro | 4 | mantido | Lente factual: todos os fatos centrais conferem na documentação oficial. Vision doc: custo = ⌈largura/28⌉×⌈altura/28⌉ tokens; 1000×1000 = 1.296 tokens; tier alta resolução (Claude 4.7+, inclui Opus 5/Sonnet 5) = 2576 px / 4.784 tokens, 3840×2160 → 4.784 tokens; Haiku 4.5 ≈ US$1,30/mil imagens de 1 MP, Opus 5 ≈ US$6,48 (1 MP) e US$23,92 (4K) por mil — os números do revisor são citações literais da página. GIF/animação: só o primeiro quadro é usado. Limites: 600 imagens/request (100 em modelos de 200k, i.e. Haiku 4.5), 8000×8000 máx., e acima de 20 imagens por request cada imagem precisa ter ≤20… |
| 2 | Não existe camada de ingestão/decodificação para 17 streams contínuos — definir Frigate + go2rtc + ffmpeg/NVDEC e inventariar as câmeras | lacuna | 4 | **dividido** | O núcleo do achado sobrevive: nenhum dos três documentos nomeia software de ingestão/NVR (grep por Frigate, go2rtc, RTSP, NVR, NVDEC nos três arquivos: zero ocorrências; a Etapa 3 diz só "gravador local"), e as escolhas Frigate (MIT, confirmado no LICENSE), go2rtc (MIT, embutido desde 0.12), imagem `-tensorrt`, `preset-nvidia`, endpoint `/api/<camera>/start/<ts>/end/<ts>/clip.mp4` (existe desde 0.13.2), NVDEC sem limite de sessões, RTX 5060 com 1 NVDEC (~8× 4K60 por engine, segundo Puget), preço ~R$ 2.279 (mín. R$ 1.799 em nov/2025) e TrackMix PoE 4K/25 fps com duas lentes (Preview_01/Preview_… |
| 3 | Detector e tracker: nomear os que têm licença e manutenção verificadas (RF-DETR/RT-DETRv2 + ByteTrack original), e apontar as armadilhas (YOLOX parado, MMDet/mmcv, BoxMOT AGPL, YOLO-NAS e D-FINE-obj365 não comerciais) | erro | 3 | **dividido** | LENTE FACTUAL — quase tudo se sustenta: Ultralytics LICENSE = AGPL-3.0 (verificado); YOLOX Apache-2.0 com último item de "Updates" em 28/02/2023 e último commit em jun/2025 sendo correção de typo em .rst — ou seja, sem manutenção funcional (verificado); RT-DETR/RT-DETRv2 Apache-2.0, v2-S 48,1 AP (verificado); RF-DETR Apache-2.0 para Nano/Small/Medium/Large (48,4/53,0/54,7/56,5 AP; 2,3/3,5/4,4/6,8 ms) e XL/2XL sob PML 1.0 (verificado); D-FINE Apache-2.0 com o aviso literal sobre checkpoints *_obj365/*_obj2coco (verificado); YOLO-NAS "you may not use the Software for any commercial use" (verific… |
| 4 | Pose e modelo temporal: MediaPipe é single-person, MMPose está preso ao mmcv, Sapiens é não-comercial — usar rtmlib (RTMO/RTMPose) em inferência e isolar MMPose só no fine-tune | erro | 3 | **dividido** | Refutação PARCIAL: o núcleo do achado sobrevive (MediaPipe Pose Landmarker é single-person — issue #5842 do google-ai-edge confirma que num_poses>1 não é suportado pelo modelo; rtmlib é Apache-2.0 e depende só de numpy/opencv/onnxruntime, com RTMO one-stage multi-pessoa; Sapiens é CC BY-NC 4.0; features em janela antes de ST-GCN é decisão prudente). Mas a evidência que sustenta a severidade 3/'erro' tem quatro falhas: (1) FACTUAL — 'MMPose último release jan/2024 (1.3.0)' está errado: o último é v1.3.2 de 12/07/2024 (página de releases). (2) FACTUAL — 'mmcv não instala limpo em PyTorch 2.x/CUD… |
| 5 | Áudio contínuo não tem stack em nenhum documento — para 1–3 anos a medida de linguagem é vocalização/turnos, não transcrição | lacuna | 4 | refutado | A lacuna em si é verdadeira (nenhum dos três documentos de 29/08 cita VAD, diarização ou ASR), mas a prescrição cai em duas frentes.  FACTUAL: (1) O portão (b) manda "medir WER do Whisper em 30 trechos de fala infantil já transcritos pelas especialistas no bucket observacao-audio". Consultei observacao_entradas no projeto rmpnqrvsmxhnrwlgqmdp: as 40 transcrições são a VOZ DA OBSERVADORA ditando ("testando, testando", "outro microfone agora", "do microfone 3", "Claudio, você está me ouvindo?", "Maria trabalhando com Max no cubo do trinômio"). Não há um único trecho de fala infantil transcrito. … |
| 6 | Armazenamento e análise: Parquet+DuckDB está certo, mas faltam volumes para 17 câmeras, o caminho DuckDB→Supabase Storage e o papel (limitado) do pgvector | melhoria | 2 | mantido | Lente factual: os fatos centrais se confirmam. DuckDB é MIT e a linha 2.0 já é o release atual (v2.0-cyanoptera), não "em desenvolvimento". pgvector: v0.8.6, licença PostgreSQL, vector e halfvec até 16.000 dimensões (índice HNSW/IVFFlat só até 2.000/4.000 — irrelevante para 768). uv: dual MIT/Apache-2.0. Supabase Storage: US$0,021/GB-mês, egress US$0,09/GB acima de 250 GB/mês no Pro, egress cacheado 3× mais barato (fontes terceiras; supabase.com bloqueado pelo proxy). O endpoint S3 do Supabase existe (`https://<ref>.storage.supabase.co/storage/v1/s3`, path-style, ainda rotulado "public alpha")… |
| 7 | Anotação: CVAT (MIT) para keypoints/caixas do fine-tune e Label Studio (Apache-2.0) para segmentos temporais — a escala LIS-YC continua na tela própria | melhoria | 2 | **dividido** | LENTE FACTUAL — o núcleo se sustenta: CVAT Community é MIT com o aviso literal de que /serverless "may use third-party assets under separate licenses (including non-commercial)"; sobe com `docker compose up -d`; tem esqueletos e interpolação por keyframe em modo track (CVAT Academy: "interpolates each keypoint position independently"); exporta esqueletos em "COCO Keypoints 1.0" (docs: "Skeletons can be exported in two formats: CVAT for image and COCO Keypoints"; há issues antigas #5831/#7161 de export vazio — testar o export no primeiro job). Label Studio é Apache-2.0 e o template 'Video timel… |
| 8 | Manter: Supabase + páginas estáticas + Python só no worker, e Batch/caching/saídas estruturadas na Etapa 4 | confirmacao | 3 | **dividido** | Lente factual: todos os fatos centrais do achado foram confirmados na fonte oficial. (a) Vision: "600 per request on the API, for all other models" e "100 per request ... for models with a 200k-token context window" — correto. (b) Batch: "reducing costs by 50%", resultados "in any order ... always use the custom_id field", limite 100.000 requests ou 256 MB, expira em 24 h — correto. (c) Prompt caching: "up to 4 cache breakpoints" — correto. (d) `output_config.format` é a forma atual e `output_format` está deprecado — confirmado na referência da API carregada nesta sessão. (e) Frigate é MIT, gr… |

### Como testar sem hardware novo

_Resumo do revisor:_ O passo a passo está certo em colocar o kappa humano antes de qualquer modelo, mas o protocolo de teste que ele descreve é de OBSERVAÇÃO AMOSTRADA (clipe de 3 min, tarde de teste, etapa 6 daqui a 5 meses) e não da meta atualizada de SENSORIAMENTO QUASE CONTÍNUO. Para essa meta, a pergunta que decide o projeto em 4 semanas não é "o construto se sustenta?" (que continua importante) e sim "as 16–17 câmeras entregam stream contínuo que um computador comum aguenta processar 8 h/dia, 5 dias seguidos, e o sistema devolve o MESMO número quando duas câmeras olham a mesma criança?". Nada disso exige compra e nada disso está no documento. Além disso, três premissas de "já existe" não se confirmam no banco (verificado em 05/09/2026): meal_events tem 0 linhas; a única sessão em modo 'gravacao' é 'pagina-teste' com 1 entrada 'fim' sem sala; 32 das 45 entradas com sala usam "sala 1", chave que não existe em salas_cameras (a chave real é "sala 1a3"); salas_cameras não guarda modelo, IP nem URL de stream; "sala MEIO" está listada nas duas salas, logo são 16 nomes únicos (e "Patio Ângulo largo" + "Patio Rastreio" são compatíveis com as duas lentes de UM TrackMix). O vídeo das únicas observações reais (04/08 e 24/08) só existe se o NVR ainda não sobrescreveu — é a primeira coisa a resgatar.

Ordem, duração e portão de cada teste (4 semanas, custo zero em hardware):
Semana 1 — T0 Resgate e inventário (dia 1–2): exportar do NVR o vídeo de 24/08 17:39–18:30 UTC (sala 1a3 e 3a6) e 04/08 19:28–20:30 UTC; preencher modelo/IP/RTSP por câmera. Portão: 100% das câmeras de sala com URL RTSP testada por ffprobe. T1 Prova de vida da captação contínua (dia 2–5, depois roda em paralelo por 15 dias úteis): Frigate/go2rtc no notebook lendo sub-stream 640x360 @5 fps das 7 câmeras das duas salas; portão: 5 dias × 8 h sem queda, detection fps = 5 por câmera, CPU < 70%. T5a Kappa de leitura (uma tarde): 2 especialistas pontuam as 40 transcrições existentes; portão: kappa ponderado quadrático ≥ 0,6 ou reescrever âncoras.
Semana 2 — T3 Sincronização + teste-reteste entre câmeras (5 dias): NTP nas câmeras, evento visível nas 4 câmeras da sala 1a3, gravação simultânea; portão: offset ≤ 0,5 s e concordância de contagem de pessoas entre câmeras MAE ≤ 1. T4 Preencher video_inicio_s/video_fim_s (2 dias): backfill das 13 entradas de 24/08 + job para entradas novas; portão: 100% das entradas novas com sala recebem clipe em < 5 min. T5b Kappa de cena (3 dias): 3 especialistas × 30 clipes cegos; portão: kappa ≥ 0,6 e kappa intra-observador ≥ 0,7.
Semana 3 — T6 Pose em criança pequena (offline, 3 dias): 100 quadros anotados em 4 posturas; portão: PCK@0,5 ≥ 0,7 em pé, ≥ 0,5 agachada/de bruços, senão plano B (caixa + orientação de cabeça). T7 Persistência de ID do tracker (2 dias): auditoria manual de 10 min × 3 câmeras; portão: registrar mediana de duração de track e trocas/hora (esperado < 60 s — isso justifica a compra de UWB, não a reprova). T8 VLM "engajado × vagando" (2 dias): 60 clipes × 16 quadros no claude-opus-5 via Batch com saída estruturada; portão: kappa modelo-humano ≥ 0,7 × kappa humano-humano.
Semana 4 — consolidação, teste-reteste com a nota do VLM entre câmeras (portão: kappa entre câmeras ≥ 0,6), e lista de compras derivada dos números medidos, não de opinião: GPU/mini-PC (pose contínua em 4K), UWB/RFID (identidade), microfones (linguagem).

| # | Achado | Tipo | Sev | Veredito | Resumo do motivo (3ª rodada) |
| --- | --- | --- | --- | --- | --- |
| 1 | Os 'ativos que já existem' para teste não existem como o documento assume — resgate o vídeo de 24/08 antes que o NVR sobrescreva (Teste 0) | erro | 4 | **dividido** | LENTE FACTUAL — todas as afirmações centrais foram reconfirmadas em 06/09/2026 no projeto rmpnqrvsmxhnrwlgqmdp: meal_events = 0 linhas e bucket meal-photos sem objetos (pipeline de refeição é só schema; a alegação "JÁ EXISTE pipeline" está no contexto da rodada, não no passo a passo — o documento não cita meal_events, o revisor misturou as duas fontes); única sessão modo 'gravacao' = Sonia, 01/08, origem 'pagina-teste', 1 entrada 'fim', sala null; group by sala = 'sala 1':32 / null:30 / 'sala 1a3':9 / 'sala 3a6':4 (os 32 'sala 1' são todos da sessão da Sonia em 04/08, 30 com áudio, só 2 do tip… |
| 2 | Falta a prova de vida da captação quase contínua: RTSP em todas as câmeras e orçamento de CPU de um computador comum (Teste 1) | lacuna | 5 | refutado | O núcleo do achado sobrevive (o passo a passo não tem prova de vida da captação antes do mês 5; Frigate é MIT; /api/stats expõe camera_fps/process_fps/skipped_fps/detection_fps e cpu_usages — confirmado no código frigate/stats/util.py; câmeras Reolink a bateria não expõem RTSP sozinhas — confirmado; TrackMix expõe RTSP só cabeado — confirmado). Mas quatro pontos derrubam o achado como está escrito. (1) FACTUAL: a evidência para 'um computador comum NÃO decodifica 4K' é um post da Intel sobre decodificação em SOFTWARE de um stream 4K60 a 100 Mbps — nada a ver com stream de câmera 4K/15fps/8 Mbp… |
| 3 | Teste-reteste com as câmeras sobrepostas da sala 1a3 dá pra fazer na semana 2 — não na Etapa 6 — e exige sincronização de relógio que o documento não menciona (Teste 3) | lacuna | 4 | refutado | A direção do achado é boa (antecipar o teste-reteste e exigir sincronização de relógio), mas ele cai nas duas lentes como está escrito.  FACTUAL — evidência errada, embora a tese sobreviva com outra evidência: (1) O exemplo citado (sessão iniciada 20:21:14 com entrada 20:21:07) é uma entrada tipo 'fala'. No banco, TODAS as 4 entradas com relogio < iniciada_em são 'fala' (deltas -3,4 s a -70,6 s), e para 'fala' relogio − criado_em vai de -1,7 s a -369,9 s (mediana -5,6 s): é o instante de início da gravação de áudio, gravado antes do insert da sessão/entrada — lógica da aplicação, não offset de… |
| 4 | Como preencher video_inicio_s/video_fim_s: falta definir a referência temporal, o arquivo e o job — receita concreta com backfill das 13 entradas de 24/08 (Teste 4) | melhoria | 3 | mantido | O núcleo do achado sobrevive às duas lentes; o que cai são duas premissas técnicas da receita e um excesso prático, todos corrigíveis sem inverter a conclusão.  FACTUAL — confirmado no banco real (projeto rmpnqrvsmxhnrwlgqmdp): observacao_entradas tem relogio timestamptz (sem default — vem do navegador), video_inicio_s/video_fim_s/janela_ini_s/janela_fim_s numeric, sala text, audio_path text, e NENHUMA coluna de caminho de vídeo ou câmera; nenhuma coluna tem comentário no catálogo (col_description = null), logo a semântica dos segundos não está documentada em lugar nenhum. As quatro colunas de… |
| 5 | O kappa humano-humano com as 3 especialistas pode começar hoje com as 40 transcrições, mas o documento subestima o que falta: as entradas existentes não identificam criança, 3 avaliadoras pedem estatística de 3, e falta o kappa intra-observador (Teste 5) | melhoria | 3 | refutado (1 rodada) | Lente FACTUAL derruba a premissa central do achado (o teste T5a "kappa de leitura, uma tarde, esta semana, com as 40 transcrições existentes"). Consultei o banco ponto-escola-montessoriana (rmpnqrvsmxhnrwlgqmdp) e: (1) as contagens do revisor estão certas — 75 entradas: corte 5, fala 40 (40 com transcrição), fim 30; aluno_id não existe em observacao_entradas — MAS o CONTEÚDO das 40 transcrições inviabiliza pontuar envolvimento/autonomia/persistência: as 30 de 04/08 (sala 1, 20:12–20:29 UTC) são testes de microfone ("testando, testando", "Muito bem.", "Beleza!", "do microfone 3", 3 strings vazi… |
| 6 | Pose em criança de 2 anos no ângulo atual: o teste precisa ser offline no stream principal (4K exportado), com anotação própria de 100 quadros por postura — não dá pra 'só medir' sem isso (Teste 6) | lacuna | 4 | refutado (1 rodada) | A recomendação de fundo (testar pose offline no stream principal, com anotação própria e portão de decisão antes da Etapa 6) sobrevive; o que cai são dois fatos centrais e o desenho estatístico do teste.  FACTUAL. (1) O número "30–40 px a 4–5 m no sub-stream 640x360" está errado por ~1,5–2×. Com a FOV publicada do TrackMix (wide 104° H / 60° V) a focal em 640 px é ~250 px: criança de 0,9 m fica com ~45 px a 5 m e ~56 px a 4 m; numa Reolink fixa típica (~87–90° H) dá ~60–76 px. Continua pequeno para RTMPose (crop 256×192), então a conclusão "use o stream principal" fica de pé, mas por outro mot… |
| 7 | VLM 'engajado × vagando' em quadros amostrados: teste concreto com Claude, 60 clipes, 16 quadros, custo < US$ 5, medido contra o consenso humano do Teste 5 (Teste 8) | lacuna | 3 | refutado (1 rodada) | A ideia central (testar o VLM em quadros amostrados cedo, com variantes de entrada, antes do stick figure) sobrevive, mas o achado cai em três pontos verificáveis. (1) FACTUAL — dois dos três fatos citados da doc de Vision estão desatualizados para o modelo escolhido: em claude-opus-5 (tier 'high-resolution', Claude 4.7+) o limite é 2576 px no lado maior e 4784 tokens visuais, não 1568 px; um quadro 4K inteiro vira 2576x1449 = 4784 tokens (~US$ 0,024/quadro), 16x o quadro do sub-stream. O teto de 100 imagens/requisição vale só para modelos de 200k (Haiku 4.5); Opus 5 aceita 600 (acima de 20 im… |
| 8 | O tracker não vai segurar identidade numa sala Montessori — meça isso em 2 dias (Teste 7) e use o resultado para a lista do que NÃO dá pra testar sem comprar | lacuna | 4 | refutado (1 rodada) | FACTUAL — o que se sustenta: ByteTrack é MIT e YOLOX é Apache-2.0 (verificado); meal_events tem 0 linhas e meal_event_items 0 (verificado no banco: o 'pipeline em produção' do contexto é só schema); salas_cameras tem 10 espaços sem sala de sono (verificado). O que cai: (1) o critério central 'se a fusão entre câmeras recupera >50% das quebras, compre 2 âncoras em vez de 4 por sala' é tecnicamente errado — trilateração UWB em 2D exige no mínimo 3 âncoras (4 em 3D); com 2 há ambiguidade especular e não há posição. O número de âncoras é ditado pela geometria da sala e NLOS, não pela persistência … |

### O que comprar de hardware

_Resumo do revisor:_ Os três documentos foram escritos para observação amostrada de UMA dimensão (engajamento) e, coerentes com isso, mandam "não comprar câmera nova", não dimensionam disco para 17 câmeras, não têm nenhum microfone para as crianças e não nomeiam produto nem preço para UWB/RFID. Contra a meta atualizada (sensoriamento passivo, o dia inteiro, motor+linguagem+social+cognitivo+autonomia+autorregulação+alimentação+sono, 47 crianças), isso vira quatro furos de severidade alta: (1) as câmeras existentes não foram inventariadas — as do pátio são Reolink TrackMix (PTZ com auto-tracking que MOVE a câmera, substream de só 640x360, RTSP instável) e as das salas têm marca/modelo desconhecidos; (2) a dimensão "linguagem" não tem captação nenhuma — o áudio que existe é a narração da especialista; (3) o edge foi dimensionado para 6 streams, não 17+ e áudio; (4) UWB e RFID são propostos com kits que já saíram de linha (MDEK1001, Pozyx Creator) e com faixa de preço subestimada (leitor UHF fixo custa US$ 1.274–1.499, não US$ 300–800). Nada disso muda a ordem do plano — a primeira semana continua custando zero — mas o passo a passo precisa de uma "Etapa 0: inventário técnico das câmeras" e de uma lista de compras por fase com critério de gatilho. Ordem de prioridade de compra: (1) desktop de edge com GPU de consumo (não Jetson) + 2 HDD Purple 8 TB; (2) switch PoE + cabear qualquer câmera Wi‑Fi; (3) 2 câmeras fixas 4K PoE oblíquas por sala principal se o teste de pixels/mão falhar; (4) 2 arrays de microfone USB por sala + 3 gravadores de bolso para calibração; (5) piloto UWB com 9 placas Makerfabs; (6) piloto RFID com 1 leitor de 4 portas + antenas near‑field; (7) ArUco impresso no avental (R$ 0) como verdade de identidade antes de qualquer tag. Orçamento (câmbio assumido R$ 5,50/US$; ajustar): MÍNIMO VIÁVEL (2 salas, 7 câmeras, pilotos) ≈ R$ 18–24 mil; RECOMENDADO (17 câmeras, áudio em 3 espaços, UWB em 3 salas, RFID em 2 salas, sem LENA) ≈ R$ 45–70 mil; +≈R$ 33 mil se optar por 3 gravadores LENA com licença de software. Muitos preços de loja brasileira e alguns distribuidores (DigiKey, Makerfabs, Pozyx, Atlas) ficaram atrás de bloqueio de rede nesta revisão e foram marcados como "não verificado" onde só havia snippet.

| # | Achado | Tipo | Sev | Veredito | Resumo do motivo (3ª rodada) |
| --- | --- | --- | --- | --- | --- |
| 1 | "Não comprar câmera nova — já tem 17" está errado para a meta contínua: as câmeras nunca foram inventariadas e as do pátio são PTZ de auto-tracking | erro | 5 | mantido | O núcleo do achado sobrevive às duas lentes. FACTUAL: (1) o banco realmente só tem nome+sala das 17 câmeras — marca, modelo, RTSP, fps, HFOV, PoE/Wi-Fi e altura nunca foram registrados (fato do contexto); (2) as specs da Reolink TrackMix PoE citadas conferem com o que a busca retornou do spec sheet oficial e de support.reolink.com: main 3840x2160 @ até 25 fps, faixa 2–25 fps, H.264/H.265, substream 640x360, RTSP/ONVIF, auto-tracking desligável em Alarm Settings e "Monitor Point" com auto-retorno; (3) a discussão Frigate #19650 confirma quedas de RTSP nativo em Reolink 8MP e o uso de Neolink/go… |
| 2 | Caixa de edge: o doc dimensiona para 6 streams; 17 câmeras + áudio exigem desktop com GPU de consumo (Jetson Orin Nano nem decodifica o volume) | lacuna | 4 | **dividido** | O núcleo do achado sobrevive às duas lentes. (a) FACTUAL: a lacuna é real — a análise fixa "6 streams a 5 fps" (P10 e a tabela "Micro de edge com GPU R$ 6–9 k", premissa "3 salas × 2 câmeras") e o passo a passo só diz "com 17 câmeras, dimensione o disco antes" (Etapa 3) e "nas 2 salas principais" (Etapa 6), sem nenhuma conta de compute. Verifiquei: aumento de preço Jetson em jul/2026 (Orin Nano Super US$ 249→399; AGX Orin dev kit US$ 1.999→3.499; módulo Orin Nano US$ 99→199) — confirmado em hwbusters/videocardz/notebookcheck; decode Orin Nano 1×4K60\|2×4K30\|11×1080p30, Orin NX 2×4K60\|4×4K30\… |
| 3 | Armazenamento: o passo a passo manda "dimensionar o disco antes" e nunca dimensiona; para 17 câmeras contínuas são ~245 GB/dia a 5 fps (ou 612 GB/dia a 25 fps) | lacuna | 3 | **dividido** | O núcleo do achado (lacuna) é verdadeiro: o passo a passo, Etapa 3 item 1, diz literalmente "com 17 câmeras, dimensione o disco antes" e a dimensão nunca aparece; a única conta está na análise (6 × 10 Mbps × 28.800 s ≈ 216 GB/dia; "2 HDDs de 8 TB ≈ US$ 300"). Mas o achado cai nas duas lentes por causa dos números e da recomendação central. FACTUAL: (1) O número-manchete "245 GB/dia" depende de "4K @ 5 fps ≈ 3–4 Mbps", que o revisor não verificou e que é frágil: em câmeras Reolink o bitrate é um parâmetro independente do fps (faixa do main stream 1024–8192 kbps; RLC-1212A default 8192 kbps; mod… |
| 4 | Rede/PoE não aparece em nenhum documento: 17 streams 4K sustentados exigem cabo, switch PoE+ e VLAN — e há indício de câmera Wi‑Fi/móvel | lacuna | 4 | refutado | FACTUAL — três pilares do achado não se sustentam. (1) "Nenhum dos três documentos fala de switch, cabeamento" é falso: a análise (2026-08-29-analise-grok-arquitetura.md, linhas 316 e 352) traz "Upload contínuo exigido: 60 Mbps sustentados, 8 h/dia" e a linha "Switch PoE + cabeamento R$ ~2 k" — a própria evidência do revisor admite isso ("único registro"). A lacuna real é de ESPECIFICAÇÃO, não de ausência; isso derruba o título e reduz a severidade. (2) A inferência "sala MEIO (compartilhada, ajustável) → câmera Wi‑Fi" não tem base: o texto real em salas_cameras.observacao é "sala MEIO como co… |
| 5 | Linguagem não tem captação nenhuma: o áudio existente é a narração da especialista; faltam microfones para as crianças (array de sala + gravador de bolso; LENA como opção cara) | lacuna | 5 | **dividido** | LENTE FACTUAL — o núcleo do achado se sustenta: (1) o passo-a-passo (8 etapas) não contém a palavra "microfone" nem qualquer captação de áudio das crianças; o único áudio é o bucket observacao-audio com a narração da especialista (40/73 entradas); o Grok classifica áudio como "opcional na fase 1". Com a meta atualizada (linguagem e social quase contínuos), isso é lacuna real de severidade 5. (2) Fatos de produto verificados: Shure MXA910 descontinuado em maio/2022 e substituído pelo MXA920 (Shure/323.tv); ES945O/XLR US$ 219 no site da Audio-Technica (MSRP antigo US$ 249); Sony ICD-PX470 R$ 527… |
| 6 | UWB: os documentos não nomeiam produto, e os kits que o mercado conhece (MDEK1001, Pozyx Creator) saíram de linha; a faixa "US$ 1,5–3 k" só fecha com placas Makerfabs e firmware próprio | lacuna | 4 | refutado | O núcleo do achado (documentos não nomeiam produto; MDEK1001 e Pozyx Creator saíram de linha; PANS 750/150/15 tags; "10–30 cm" é otimista) confere. Mas duas afirmações centrais que sustentam o título e a mudança proposta caem: (1) "a faixa US$ 1,5–3 k só fecha com placas Makerfabs e firmware próprio" é falsa — o DWM3001CDK custa US$ 29,50 (loja Qorvo, 1–24 un.) / US$ 31,61 (Avnet, 20+), não os "US$ 130–150" que o revisor chutou sem verificar; 67 placas ≈ US$ 2,0 k, dentro da faixa e mais barato que Makerfabs. (2) "Makerfabs sem stack de posicionamento pronto — exige firmware próprio (2–4 seman… |
| 7 | RFID: preço de leitor UHF subestimado (US$ 300–800 vs US$ 1.274–1.499 reais), sem antena near‑field o "passou perto" é garantido, e a banda UHF do Brasil precisa ser a certa | erro | 3 | refutado | LENTE FACTUAL — o núcleo do achado ("US$ 300–800 está subestimado") cai. (1) A análise escreve "ordem de grandeza, conferir preço real" e "por leitor"; o achado compara essa faixa só com a classe enterprise (Impinj R700 US$ 1.499 confirmado; Zebra FX9600 4 portas ≈ US$ 1.213–1.274, MSRP US$ 1.685) e omite que a classe que um construtor solo compraria está ABAIXO da faixa: Chafon CF815 com chip Impinj E710, 4 portas RP‑TNC, 0–33 dBm, opção 902–928 MHz, US$ 196–206 (Alibaba), Chafon US$ 279/unidade e Ascend IoT US$ 232 (Accio). O próprio achado admite "Chafon ≈ US$ 150–300", contradizendo o títu… |
| 8 | Identidade barata antes de qualquer tag: ArUco impresso no avental custa R$ 0 e serve de verdade de identidade para validar o tracker nas 18 crianças autorizadas; BLE só serve para presença por sala; cor não escala para 47 | melhoria | 3 | refutado | Refutação PARCIAL: a ideia central (ArUco no avental como verdade de identidade barata antes de comprar UWB) sobrevive, mas três pontos do achado não se sustentam como escritos.  (a) FACTUAL — 1. "O OpenCV exige perímetro mínimo de 0,05 × largura" é errado: minMarkerPerimeterRate é parâmetro ajustável com default 0,03, relativo à MAIOR dimensão da imagem; o 0,05 é só o exemplo do tutorial (640×0,05 = 32 px). Com 0,03 o mínimo seria 115 px de perímetro (~29 px de lado, ~7 cm a 5 m). O limite real não é esse parâmetro, e sim resolução por célula (4×4 + borda = 6 células; ~8 px/célula em 48 px), … |

### Lacunas apontadas pelo crítico de completude (3ª rodada)

1. **Captação: as quatro seções técnicas assumem parques, fps, bitrate, resolução e retenção diferentes — e duas delas se contradizem no que é inegociável (4K e fps do pátio)** — Arquitetura: 17 câmeras, main a 8–10 fps, 4–8 Mbps 4K, retenção 3 dias, 275–551 GB/dia, pose a 2 fps fora das salas. Ferramentas: 17 × 10 Mbps ≈ 612 GB/dia, retenção 7 dias. Como testar: 15–16 aparelhos (sala MEIO duplicada; TrackMix = 1 canal), gravar main a 1080p–1440p/15 fps/3 Mbps ≈ 76 GB/dia (7 câm.), 30 dias. Hardware: 17–19 streams (TrackMix = 2 lentes), main 4K a 15 fps, 245–670 GB/dia, 14 dias, e afirma que na TrackMix resolução/codec não são alteráveis. Duas contradições de fundo: (a) …
2. **Stack de visão e GPU divergentes: três detectores, dois modelos de pose, duas gerações de GPU e um proxy proibido (Neolink) que reaparece** — Plano de IA, Arquitetura e Como testar usam YOLOX + RTMPose-m; Ferramentas descarta YOLOX (sem release funcional desde fev/2023) e MMDetection (mmcv não compila em PyTorch 2.9) e propõe RF-DETR Nano/Small ou RT-DETRv2-S + rtmlib/RTMO-s (one-stage) para o contínuo; Hardware escreve 'YOLOX-s/RT-DETR + RTMPose-m'. GPU: Arquitetura orça RTX 4060 8 GB; Ferramentas e Hardware orçam RTX 5060/5060 Ti 16 GB; Como testar diz que nenhuma GPU é comprada antes de T1+T6 e roda OpenVINO em CPU/iGPU. Hardware a…
3. **Schema divergente e um erro estrutural: colunas por câmera numa tabela cuja chave é a sala; nomes, comprimento de janela e métrica de concordância diferem entre seções** — Como testar (`alter table salas_cameras add column modelo, canal_nvr, rtsp_path_main…`) e Ferramentas (`fabricante, modelo, stream_main_url, tem_microfone…` em `salas_cameras`) põem atributos por câmera numa tabela cuja PK é `sala` e cujas câmeras são `text[]` (sala 1a3 tem 4) — não há onde guardar 4 modelos/4 URLs numa linha; Arquitetura cria `cameras(id, sala, nome, modelo, …)`, que é o certo. Também: `obs_janelas` (Plano de IA) vs `dev_janelas` (Arquitetura); `janelas_features` vs `dev_agrega…
4. **Linguagem em regime pleno não tem hardware, compute, sincronia nem operação — só o piloto está orçado** — Plano de IA diz que o regime pleno são 47 gravadores vestíveis e 376 h/dia de áudio; Hardware orça 2–3 Sony ICD-PX470 (R$ 527/un.) 'rotativas' (= amostrado, não contínuo) e arrays XVF3800 que entregam um único azimute (fonte dominante) numa sala com 20 crianças. Ninguém orça 47 × R$ 527 ≈ R$ 24,8 k, nem quem recarrega/descarrega 47 gravadores por USB todo dia. Compute: pyannote community-1 leva 31–37 s por hora de áudio numa H100 (README verificado: https://raw.githubusercontent.com/pyannote/pya…
5. **Duas dimensões sem sensor de fato: sono não tem espaço nem câmera confirmados; motor grosso perde o pátio (sem UWB, câmera PTZ travada, pose a 2 fps)** — Plano de IA classifica sono como PASSIVO-CANDIDATO via 'câmera IR na sala de sesta'; Como testar verifica que não há sala de sono em `salas_cameras` e Ferramentas manda 'registrar onde acontece a soneca' — ou seja, o sensor é hipótese. Motor grosso depende, no Plano de IA, de pose + UWB (velocidade, subir/pular), que acontece no pátio; mas o UWB em escala cobre 3 salas (Hardware), a Hardware manda travar ou excluir a TrackMix do pátio, e a Arquitetura roda pose a 2 fps fora das salas. Na prática…
6. **Carga humana e instrumentos-âncora nunca foram somados — e com 2 avaliadoras reais a soma provavelmente não cabe** — Somando o que as seções pedem às mesmas 2 pessoas nas primeiras 12 semanas: 9 janelas/dia ≈ 25 min/dia (Plano de IA) + sorteio 15 min/dia (Arquitetura) + 20 janelas/semana em dupla cega + golden com 10 blocos ≥2 h (60 janelas de 2 min por bloco × 2 avaliadoras ≈ 20–40 h) + `meal_golden` 100 pares × 2 + T5 (60 clipes × 2 + reteste 15) + ~960 caixas à mão para T8 (3–4 h) + 10–15 h de anotação de pose (T6) + ≥1.000 instâncias no CVAT (Ferramentas). Mais os instrumentos do item E do Plano de IA, sem…
7. **Roadmap integrado: as cinco seções mudaram a ordem e os portões do plano original sem consolidar — e discordam entre si sobre quando comprar RFID/UWB e a GPU** — Original: E1 (s1–2) → E2 (s3) → E3 (s4–6) → E4 (s6–8) → E5 RFID/UWB (m3–4) → E6 visão (m5–8) → E7 (m9+). Mudanças não conciliadas: três 'Etapas 0' diferentes (inventário na Hardware, ingestão na Ferramentas, 'sem etapa 0 bloqueante' na Arquitetura); Como testar liga gravação contínua na semana 1 (T1) e faz kappa sobre clipes (T5) em vez de sobre entradas; Plano de IA exige que o golden da E3 tenha ≥60% de janelas aleatórias + 10 blocos ≥2 h — só fecha com gravação rodando semanas antes; Plano de…
8. **Custo total (capex + opex + horas) e prazo total nunca foram somados; várias linhas de API se sobrepõem** — Hardware: R$ 15–21 k (mínimo) / R$ 45–68 k (recomendado) / +R$ 31–33 k (LENA) — só hardware. Opex espalhado e parcialmente duplicado: Plano de IA US$ 120–245/mês (VLM amostrado); Arquitetura US$ 50–110 (calibração) + US$ 30–50 (transcrição); Ferramentas US$ 13/mês (crops Haiku) — três estimativas para a mesma amostra. Faltam: Supabase Pro (US$ 25/mês + disco/egress), energia de uma caixa 24/7 (~350 W ≈ 250 kWh/mês ≈ R$ 200–300/mês; tarifa não verificada), 47 gravadores (lacuna 4), UWB do pátio (…
9. **Riscos técnicos sem dono: NVR Reolink como gargalo de streams, sincronia entre sensores, 65+ clientes ESP32 no Wi‑Fi e handover de tag UWB entre salas** — (a) Se as 17 câmeras pendem de um NVR Reolink (provável: 33 sessões ao vivo, nota 'TrackMix'), elas ficam na sub-rede PoE do NVR e o edge só as acessa por canal do NVR; há relato de limite de 12 streams simultâneos por NVR (2 main + 10 sub — trecho de busca; página oficial https://support.reolink.com/articles/360008742233 bloqueada nesta sessão, não verificado). Se for assim, 17–19 main 4K para pose são impossíveis sem tirar as câmeras do NVR — e o switch PoE que a Hardware manda não comprar 'an…
10. **A primeira semana do construtor solo está em cinco versões diferentes — precisa de uma só, e ela tem que resolver as contradições antes de cristalizá-las na migração** — Plano original: codebook → migração → sliders → calibração em voz alta. Plano de IA: + encomendar RFID + criar `materiais`. Arquitetura: + `dev_janelas`/`cameras`. Ferramentas: + migração em `salas_cameras` + Frigate TensorRT. Como testar: T0 (inventário, resgate 24/08), T1 (Frigate no PC atual), T2 (`relogio_servidor`). Hardware: Etapa 0 (inventário), ArUco, teste de px/punho. Feitas todas ao mesmo tempo, sem a lacuna 3 resolvida, a migração de terça grava o schema errado (`salas_cameras` com c…
