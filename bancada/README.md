# Bancada — Fase 0

Ferramenta da **Fase 0 (bancada de testes)** do projeto de mensuração longitudinal do
desenvolvimento infantil — ver [`../docs/pesquisa-desenvolvimento-infantil.md`](../docs/pesquisa-desenvolvimento-infantil.md),
Parte IV §2. Faz, num único programa:

| Comando | O que faz | Teste do plano |
|---|---|---|
| `smoke` | testa cada câmera Reolink: codec, resolução, fps, áudio, gravação de 20 s, projeção de GB/dia | pré-voo |
| `capturar` | grava as janelas (09–11 h, 14–16 h) por N dias letivos, um ffmpeg por câmera, segmentos de 10 min, reinício automático, QA ao fim de cada janela | T16 |
| `qa` | uptime por câmera e janela, lacunas, quadros perdidos, GB, bitrate (variáveis de camada 0) | T16 |
| `sync` | deslocamento entre câmeras da mesma sala por correlação de áudio, e deriva ao longo da janela | T2 |
| `proxy` | proxies 1080p (entrada da detecção; o original fica para os crops) | — |
| `frame` / `pxm` | quadro com grade de 100 px; px/m e tamanho projetado de mão e rosto | T1 |
| `analisar` | detecção de pessoas + tracking (YOLO + ByteTrack), pose (17 pontos), mãos (MediaPipe, 21 pontos) em crops; resumo com proxies de troca de ID e de taxa de mão; heatmap | T5 T6 T8 T9 |

Tudo grava em `data/` com o layout do plano: `bruto/AAAA/MM/DD/<sala>/<cam>/`.

## A situação real da escola (do outro projeto)

Dois documentos no Drive do Claudio descrevem o que existe — `fase1rtspreolink.md` (23/07/2026) e
`runbookgravacaofase0.md` (25/08/2026):

- **NVR Reolink RLN16-410**, IP **192.168.15.11**, RTSP 554, ~15 câmeras num só endereço, um canal
  por câmera. Agrupada 1 = câmeras `sala1a3`, Agrupada 2 = `sala3a6`; há ainda `sala meio`,
  `Sala Theo`, `sala2`, recepção, cozinha, corredor, TrackMix. "6 câmeras de sala" no total.
- Câmeras de **12 MP gravam o main em H.265** → o `caminho: auto` deste config testa as três
  variantes de URL da Reolink e guarda a que respondeu.
- Já existe um gravador em PowerShell em `C:\gravador` (`sondar.ps1`, `gravar-tudo.ps1`,
  `verificar.ps1`, `vigia.ps1`) com a mesma filosofia (ffmpeg `-c copy`, MKV, segmentos de 10 min
  alinhados ao relógio, um ffmpeg por fluxo). Âncora medida: **~860 GB/dia gravando todos os canais
  main+sub**. A bancada não substitui aquele gravador; ela **acrescenta QA, sincronização por áudio,
  proxies, medida de resolução e a primeira análise**, e roda em Windows, Linux ou macOS. O
  `canais-ok.csv` do `sondar.ps1` diz os canais certos para o `config.yaml`.
- O `runbookgravacaofase0.md` tem os cuidados de Windows que valem aqui também: `powercfg` para nunca
  suspender, `w32tm /resync` (o nome do arquivo é a linha do tempo), PC **por cabo** na rede da escola,
  HD **NTFS** (exFAT corrompe em queda de luz), HD SMR só para medir — nunca para acervo.
- A especificação do arquivador definitivo (`spec-arquivador.md`, `plano-armazenamento.md`,
  `medicoes-fase0.md`) está na pasta `claude/` daquele projeto, **no PC** — não está no Drive nem em
  nenhum repositório GitHub acessível; a Parte IV §1.2 do plano pede essa especificação.

> **Antes de gravar.** Gravar crianças, mesmo por dois dias de piloto, é tratamento de dado
> pessoal de criança (LGPD art. 14) e de imagem/voz das educadoras. A ferramenta não substitui o
> consentimento dos responsáveis e da equipe (T20 do plano). Resolva isso antes do primeiro `capturar`.

## 1. Instalar (no computador que enxerga as câmeras)

Requisitos: **Python 3.11+** e **ffmpeg** no PATH.

```bash
# Windows (PowerShell):  winget install Gyan.FFmpeg    e depois feche e reabra o terminal
# Ubuntu/Debian:         sudo apt install ffmpeg
# macOS:                 brew install ffmpeg

cd bancada
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt            # captura, QA, sync, proxy, medidas (leve)
pip install -r requirements-analise.txt    # só para `analisar` (pesado: torch, ultralytics, mediapipe)
```

No NVR Reolink o RTSP já vem ligado de fábrica; se nada responder: NVR → **Configurações → Rede →
Avançado → Configuração de porta → RTSP ativado, porta 554**. Reserve o IP 192.168.15.11 do NVR no
DHCP do roteador para ele nunca mudar.

## 2. Configurar

```bash
cp config.example.yaml config.yaml     # Windows: copy config.example.yaml config.yaml
```

Edite `config.yaml`: usuário e senha do NVR, os **canais** das câmeras da `agrupada_1` (sala1a3) e
`agrupada_2` (sala3a6), e `raiz` (disco onde vai gravar). `config.yaml` está no `.gitignore` — a
senha não sobe para o repositório.

Espaço: uma câmera 12 MP H.265 no main deve ficar em **~20–25 GB/dia** nas 4 h de janela (a âncora
do outro projeto é ~860 GB/dia para todos os canais, main+sub, 24 h). Quatro câmeras, três dias ≈
250–300 GB. Deixe o dobro livre. O `smoke` projeta o número real por câmera.

## 3. Rodar — na ordem

```bash
python bancada.py planejar                 # confere janelas, câmeras e destino
python bancada.py smoke                    # OBRIGATÓRIO antes: conecta em cada câmera e grava 20 s
```

O `smoke` testa as três variantes de URL de cada canal, grava a que respondeu em
`data/canais-ok.yaml` (o `capturar` usa essa automaticamente) e mostra codec, resolução, fps e
**se o áudio vem no stream** — a sincronização por áudio depende disso. Se uma câmera falhar, o
erro do ffmpeg está em `data/smoke/<câmera>.log`. Causas comuns: RTSP desligado no NVR; senha errada
(erro 401 em loop); **canal errado** — a foto do `frame` mostra a sala errada, troque o número;
firewall do computador; PC em Wi-Fi (use cabo).

**O RLN16-410 tem limite de clientes RTSP simultâneos** e ninguém sabe qual é sem testar
(runbook do outro projeto). Se o `gravar-tudo.ps1` já estiver puxando os 16 canais nesse PC,
a bancada pode não conseguir abrir mais fluxos — rode uma coisa ou a outra, ou só as 4 câmeras.

```bash
python bancada.py capturar                 # grava as janelas dos próximos N dias letivos
python bancada.py capturar --sala agrupada_1   # só uma sala
python bancada.py capturar --agora --segundos 120   # teste rápido de 2 min, agora
```

Deixe o terminal aberto e **o computador sem suspender** (Windows: Configurações → Energia →
Suspender: Nunca; ou `powercfg /change standby-timeout-ac 0`). O programa aguarda a janela, grava,
roda o QA ao fim de cada janela e imprime onde está o relatório. `Ctrl+C` fecha os segmentos
corretamente.

Ao fim de cada dia:

```bash
python bancada.py qa --dia 2026-09-08          # data/relatorios/<dia>/qa.md e qa.csv
python bancada.py sync --dia 2026-09-08        # data/relatorios/<dia>/sync.md e sync.json
python bancada.py proxy --dia 2026-09-08       # data/proxy/... (1080p)
```

## 4. Medir a resolução (T1) — decide câmera e posição

Ponha uma fita métrica ou objeto de tamanho conhecido no chão e na altura da mesa, em 3–4
posições da sala, durante um minuto de gravação. Depois:

```bash
python bancada.py frame data/bruto/2026/09/08/agrupada_1/cam_01/agrupada_1_cam_01_20260908_091000.mkv --t 45
# abre data/medidas/<nome>_t45.jpg — grade de 100 px; leia as coordenadas das duas pontas da fita
python bancada.py pxm --p1 1210,880 --p2 1790,895 --metros 1.0
```

Saída: px/m naquela profundidade, e o tamanho projetado de **mão (8 cm)** e **rosto (12 cm)** de
criança em px, com veredito contra o limiar de 100 px. Abaixo disso, landmarks de mão e AUs de
rosto não são confiáveis (Parte IV §1.3 do plano) — é o que decide entre resolução maior, câmera
mais baixa nas mesas, ou aceitar análise de mão só perto da câmera.

## 5. Primeira análise (T5, T6, T8, T9)

```bash
python bancada.py analisar data/proxy/2026/09/08/agrupada_1/cam_01/agrupada_1_cam_01_20260908_091000.mkv
python bancada.py analisar <bruto.mkv> --imgsz 1280 --maos-stride 3       # mãos no original (crop em alta)
python bancada.py analisar <video> --modelo yolo11n.pt --sem-maos --stride 3   # só detecção+tracking, rápido
python bancada.py analisar <video> --dispositivo 0                         # GPU NVIDIA
```

Na primeira execução o ultralytics baixa os pesos (`yolo11n-pose.pt`, ~6 MB) do GitHub. Sem
internet, baixe antes e passe `--modelo caminho/yolo11n-pose.pt`.

Saída em `data/analise/<dia>/<sala>/<cam>/<segmento>/`:

- `tracks.parquet` — uma linha por pessoa por quadro: `ts_utc`, `track_id`, caixa, `conf`, 17 keypoints
- `maos.parquet` — uma linha por mão: lado, 21 landmarks em px do quadro inteiro, `largura_mao_px`
- `heatmap.png` — ocupação dos pés em px
- `resumo.json` — as métricas de decisão:

| Campo | Lê-se como |
|---|---|
| `frac_quadros_com_pessoa` | cobertura da detecção (T5) — compare com o que você vê no vídeo |
| `max_simultaneas` | pico de pessoas detectadas ao mesmo tempo |
| `ids_unicos` / **`id_churn`** | IDs que o tracker gastou / pico de pessoas. **1,0 = perfeito.** 8 crianças virando 60 IDs em 10 min é o problema de T6 — etiquetas UWB viram obrigatórias |
| `vida_mediana_id_s`, `ids_curtos_lt_5s` | fragmentação das trajetórias |
| `pose_conf_media` | qualidade da pose destes ângulos (T8) |
| **`maos_taxa_deteccao`**, `maos_largura_px_mediana` | em que fração das pessoas o MediaPipe achou mão, e de que tamanho (T9) — cruze com o `pxm` |

Tudo em **pixels** até a calibração (T3). Os timestamps são relógio de parede do computador de
captura, corrigidos pelo offset de `sync.json` quando existir — as câmeras da mesma sala ficam
na mesma linha do tempo.

## 6. O que foi verificado e o que não foi

Testado neste ambiente (sem acesso à rede da escola), com três "câmeras" sintéticas em tempo real
por UDP e uma janela de 5 minutos:

| Verificado | Como |
|---|---|
| captura agendada, 3 câmeras, segmentos alinhados ao relógio, parada graciosa | 9 segmentos, `qa` com uptime 100 % |
| **reinício automático** quando o stream cai | emissor derrubado por 20 s → `ffmpeg caiu — reiniciado (#1)` → gravação retomada; QA mostra uptime 75 % e a lacuna de 19,8 s |
| relógio: início do segmento pelo nome do arquivo + `-reset_timestamps` | 2º segmento começa em pts 0 |
| **sincronização por áudio** | estimador devolve −350 / +350 / 0 ms para deslocamentos conhecidos de 350 ms (conf ≈ 4); trechos que cruzam fronteira de segmento são concatenados |
| proxies | 9/9 segmentos, HEVC |
| `frame` e `pxm` | quadro com grade; px/m e veredito de mão/rosto |
| **mãos (MediaPipe tasks API)** | 2 mãos, Left/Right, 21 landmarks mapeados para px do quadro inteiro, numa imagem real de mãos |
| ramo por detecção da análise (parquet, keypoints, crops, `id_churn`, heatmap) | com um detector-dublê sobre imagem real: `id_churn` acusou a troca de ID injetada |

**Não verificado aqui:** YOLO com pesos treinados (o ambiente bloqueia o download dos pesos; o
código roda de ponta a ponta com o modelo sem treino), a conexão real ao NVR, e as janelas de 2 h.
A primeira execução na escola é o teste dessas três coisas — comece pelo `smoke` e por um
`capturar --agora --segundos 120`.

## 7. O que mandar de volta para análise

Nunca o vídeo. Só `data/relatorios/`, `data/smoke/smoke.json`, `data/analise/**/resumo.json`
e os `heatmap.png`. É o que basta para decidir câmera, posição, tracker e microfones.

## Estrutura

```
bancada.py                 CLI
bancada_lib/config.py      config.yaml → URLs RTSP (Reolink por padrão; url: para NVR/outras)
bancada_lib/capture.py     agendamento, um ffmpeg por câmera, segmentos, reinício, parada graciosa, smoke
bancada_lib/qa.py          manifesto por segmento (ffprobe), uptime, lacunas, GB — camada 0
bancada_lib/sync.py        correlação de envelopes de áudio → offset por câmera e deriva
bancada_lib/proxy.py       1080p x265/x264
bancada_lib/medida.py      quadro com grade; px/m; mão e rosto em px
bancada_lib/analyze.py     YOLO+ByteTrack, YOLO-pose, MediaPipe Hands em crops → parquet + resumo
```

Detalhes de projeto que importam:

- **O relógio vem do nome do arquivo.** O MKV zera os timestamps de cada segmento (e `-copyts`
  corrompe MKV com época Unix), então o início de cada segmento é lido do nome — `strftime`,
  relógio do computador, resolução de 1 s — e cada arquivo começa em pts 0 (`-reset_timestamps`).
  `-segment_atclocktime 1` alinha as fronteiras ao relógio em todas as câmeras, então os
  segmentos das 7 câmeras começam no mesmo minuto.
- **O alinhamento fino (< 1 s) é medido**, não presumido: `sync` correlaciona os envelopes de
  áudio das câmeras da mesma sala. No sistema definitivo isso vira sincronização em hardware
  (PTP/genlock) — decisão da Fase 0, teste T2.
- **Cópia de stream** (`-c copy`) → CPU quase zero na captura; o gargalo é rede e disco.
- **MKV, não MP4:** se a luz cair no meio do segmento, o MKV abre mesmo truncado; o MP4 vira lixo.
