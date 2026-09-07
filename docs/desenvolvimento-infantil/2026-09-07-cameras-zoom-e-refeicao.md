# Câmeras: agente com zoom, e refeição pela câmera

Fonte: perguntas do Cláudio em 07/09/2026. Status: EM ANÁLISE (resposta técnica; o que depende do
modelo de cada câmera fica para o inventário T0). Sem busca na web nesta semana: os pontos
marcados "a verificar" são de memória e se confirmam numa tarde no PC de captação.

## 1. Um agente pode operar as câmeras Reolink, principalmente dar zoom?

**Pelo app, não. Pela API da câmera, sim. E só vale a pena onde há zoom óptico.**

- O app Reolink é interface para pessoas; não tem automação. Mas tudo o que o app faz a câmera
  aceita por HTTP, na mesma rede: API própria da Reolink (login por token; comandos de pan, tilt,
  zoom, foco, presets e patrulha) e ONVIF (PTZ padrão). Há biblioteca Python mantida para isso
  (a que o Home Assistant usa). Um agente no PC de captação, ao lado do NVR, comanda e lê o
  estado da câmera (posição, zoom). A verificar: nomes exatos dos comandos por firmware e se o
  firmware das câmeras da escola já expõe a API.
- **O que é "zoom" em cada câmera.** Na câmera de parede com lente fixa (a maioria das 4K), o
  zoom do app é digital: só recorta a imagem. O sistema já faz esse recorte no software, a partir
  do quadro 4K gravado, sem tocar na câmera, e faz melhor (recorta para todas as crianças ao
  mesmo tempo). Zoom óptico de verdade só existe nos modelos com lente motorizada ou PTZ e no
  TrackMix (duas lentes, grande-angular + tele, com pan e tilt). Quais dos 16 aparelhos têm isso
  é exatamente o que o inventário T0 responde. Sem ele, a resposta honesta é: no pátio sim
  (TrackMix), nas salas provavelmente não.
- **Para que serviria um agente com zoom.** (a) Projeto B, "câmera-repórter": quando a observadora
  marca uma entrada, o agente aponta a tele do TrackMix para a criança citada e o clipe sai em
  alta resolução. (b) Pose e expressão de perto, que o quadro largo a 4–5 m não dá (criança com
  45–75 px). (c) Verificação sob demanda: o modelo pede "zoom na mesa 3" e recebe a imagem.
- **Custo escondido.** Câmera que se mexe deixa de ser referência fixa. Rastrear identidade ao
  longo do dia precisa de câmera parada e calibrada; mexer invalida a calibração e as zonas do
  Frigate. Regra proposta: **câmeras de sala fixas sempre**; zoom e PTZ só em câmera dedicada a
  isso: o TrackMix do pátio hoje e, se o teste de pose T5 mostrar que o recorte do 4K não basta,
  uma PTZ por sala depois (R$ 900 a 1.800 cada, a cotar), comandada pelo agente.

## 2. Foto do prato pela câmera da sala, com zoom? Cardápio conferido pela câmera, automático?

- Pela câmera da sala, um prato ocupa uns 80 a 150 px no quadro 4K (mesa a 3–5 m). Isso dá para
  o modelo dizer "cheio, meio, vazio" e reconhecer itens grandes (arroz, feijão, salada, proteína)
  com acerto razoável. Não dá quantidade, nem item pequeno, nem prato tampado pela criança ou
  pelo adulto. Zoom digital não acrescenta pixel; zoom óptico só ajudaria no pátio.
- **O que resolve de verdade: uma câmera de cima, dedicada.** Uma câmera PoE 4K a 1–1,5 m sobre o
  ponto onde os pratos são servidos, e outra sobre onde voltam (ou uma só, se é o mesmo balcão).
  O prato passa a ter 600+ px: o modelo lê item por item, compara servido × devolvido e confere
  contra o cardápio do dia. É o desenho padrão dos sistemas de medição de desperdício em cozinha.
  Custo: 1 ou 2 câmeras (R$ 500 a 900 cada) mais porta PoE e cabo. Sem foto à mão: `meal_events`
  passa a ser preenchido pelo sistema.
- Conferência do cardápio: automática com a câmera de cima. O modelo descreve o prato e compara
  com o cardápio do dia (existe um projeto de cardápio da escola; falta ver se o cardápio do dia
  está numa tabela ou só na página). Pela câmera da sala, a conferência sai como "provável", não
  como registro.
- Enquanto a câmera de cima não vem: Laís fotografa no almoço (prato servido, prato devolvido),
  como respondido. Essas fotos viram a verdade de calibração da câmera depois.

## O que muda no plano

- Inventário T0 ganha duas colunas obrigatórias: modelo exato por câmera (zoom óptico sim/não,
  PTZ sim/não, API sim/não) e qual câmera cobre a sala do soninho.
- T1 ganha uma entrega: descobrir o horário do pátio (e das outras rotinas) pela ocupação por
  câmera e hora, até o terceiro dia de captação.
- Carga humana revista: Sonia 7 h/dia nas câmeras. Corpus dourado e kappa deixam de ser gargalo.
- Compra candidata nova, barata e independente do resto: câmera de cima na cozinha (1 ou 2).
