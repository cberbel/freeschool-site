# Dicionário de variáveis

Artefato vivo do projeto de mensuração longitudinal do desenvolvimento infantil
(ver [`pesquisa-desenvolvimento-infantil.md`](pesquisa-desenvolvimento-infantil.md)).

**Regra de leitura (R1):** tudo aqui é **observado e guardado desde o dia 1**. A coluna
**Camada** diz *quando cada variável é validada e promovida a indicador* — segue a cadeia de
dependência técnica, não a importância.

| Camada | Quando |
|---|---|
| **0** | mês 1 — qualidade e contexto; covariáveis de tudo |
| **A** | mês 3–6 — derivadas de posição + identidade + sono |
| **B** | mês 6–12 — derivadas de work episode e detecção de material |
| **C** | ano 2 — mãos, áudio, afeto, substrato de criatividade |
| **D** | ano 2–3 — derivadas de corpus acumulado |

**Nível:** 1 = observação física · 2 = comportamento · 3 = constructo (não entra como variável
medida; ver o fim do documento).

Toda variável carrega, na tabela derivada: `confidence`, `pipeline_version`, `model_version`,
`definition_version`, e é calculada **por fase do dia** (chegada · ciclo da manhã · refeição ·
soneca · ciclo da tarde · saída), não por dia inteiro, salvo indicação.

---

## 0. Qualidade, observabilidade e presença

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `camera_uptime_frac` | — | sistema | fração da janela de funcionamento com todas as câmeras gravando | log | 0 |
| `sync_drift_ms` | — | sistema | deslocamento máximo entre câmeras e entre áudio e vídeo no dia | palma/flash diários | 0 |
| `calibration_residual_px` | — | fiduciais | erro de reprojeção dos fiduciais fixos, por câmera, por dia | fiduciais medidos | 0 |
| `child_observability_frac` | — | tracking | fração da fase em que a criança foi rastreada com confiança acima do limiar | revisão humana amostral | 0 |
| `id_switch_rate` | — | revisão humana | trocas de identidade corrigidas por criança-hora | UI de revisão de tracks | 0 |
| `audio_snr_db` | — | áudio | relação sinal-ruído por microfone e fase | acústica | 0 |
| `attendance` | 1 | tracking + log | presente/ausente; hora de chegada e saída; motivo da ausência | log de contexto | 0 |
| `age_months` | — | cadastro | idade em meses no dia — **covariável obrigatória** em qualquer análise entre crianças | cadastro | 0 |
| `enrollment_span` | — | cadastro | data de entrada e saída da criança no estudo | cadastro | 0 |
| `context_log_*` | — | log diário | falta e motivo · material novo · rearranjo · doença · medicação · educador substituído · quebra de rotina · recalibração | educadora | 0 |

## 1. Sono

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `night_sleep_min` | 1 | diário / actigrafia | minutos de sono noturno; noite atribuída ao dia letivo seguinte | actigrafia × diário | 0 |
| `nap_min` | 1 | sensor de soneca | minutos de soneca escolar | observador humano (T15) | 0 |
| `nap_flag` | 1 | sensor / diário | houve soneca no dia | — | 0 |
| `total_sleep_24h` | 1 | derivada | noite + soneca | actigrafia × diário | 0 |
| `sleep_onset_latency` | 1 | diário / actigrafia | do deitar ao início do sono | actigrafia | A |
| `waso` | 1 | actigrafia | tempo acordado após o início do sono | actigrafia | A |
| `n_awakenings` | 1 | actigrafia / diário | despertares noturnos | actigrafia | A |
| `sleep_efficiency` | 1 | derivada | tempo dormindo / tempo na cama | actigrafia | A |
| `sleep_midpoint` | 1 | derivada | ponto médio do sono noturno (proxy de cronotipo) | — | A |
| `sleep_regularity_index` | 2 | derivada | regularidade dia a dia, janela de 7 dias (Phillips et al., 2017) | actigrafia | A |
| `weekend_shift_min` | 2 | derivada | deslocamento do ponto médio fim de semana × dias letivos | — | A |
| `nap_onset_latency` | 1 | sensor | do deitar ao início do sono na soneca | observador (T15) | A |
| `nap_awakenings` | 1 | sensor | despertares durante a soneca | observador | A |
| `nap_movement_index` | 1 | sensor | movimento por época de 30/60 s durante a soneca | observador | A |
| `settle_intervention` | 2 | sensor + vídeo | intervenção adulta para adormecer | humano × IA | A |
| `post_nap_reentry_latency` | 2 | sensor + vídeo | do despertar ao próximo work episode | humano × IA | B |
| `nap_dependency` | 2 | derivada | proporção de dias com soneca, janela móvel de 30 dias; **data da transição** por criança | diário | A |
| `sleep_questionnaire_*` | 3 | BISQ-R / CSHQ / SDSC | escores por onda trimestral — critério externo | instrumento validado | A |
| `melatonin_or_med_flag` | — | log | uso de melatonina ou medicação no dia — confundidor | família | 0 |

## 2. Trajetória e espaço

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `distance_travelled_h` | 1 | trajetória | integral do deslocamento `(x,y)` por hora, por fase | geométrica | A |
| `mean_speed` | 1 | trajetória | velocidade média em movimento | geométrica | A |
| `speed_variability` | 1 | trajetória | desvio-padrão da velocidade | geométrica | A |
| `time_stationary_frac` | 1 | trajetória | fração da fase parada (velocidade < limiar) | geométrica | A |
| `posture_state_frac` | 1 | pose grossa | fração em pé / sentada / agachada / deitada / no chão | humano × IA (PCK por postura, T8) | A |
| `area_dwell_time` | 1 | trajetória + ontologia da sala | tempo por área pedagógica | geométrica | A |
| `area_transitions_h` | 1 | trajetória | mudanças de área por hora | geométrica | A |
| `area_entropy` | 2 | derivada | entropia de Shannon da distribuição de tempo por área — diversidade espacial | — | A |
| `heatmap_daily` | 1 | trajetória | mapa de ocupação em grade de 25 cm (denso, Parquet) | — | A |
| `path_tortuosity` | 2 | trajetória | distância percorrida / deslocamento líquido — proxy de deambulação sem objetivo | humano × IA | A |
| `shelf_browse_time` | 2 | trajetória + ontologia | tempo a menos de D m de prateleira **sem retirar material** — proxy de indecisão/escolha | humano × IA | B |
| `time_to_first_work` | 2 | trajetória + episódio | da chegada ao primeiro work episode | humano × IA | B |
| `carrying_episodes` | 2 | pose + objeto | transporte de material entre prateleira e local de trabalho | humano × IA | B |

## 3. Social

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `alone_frac` | 1 | trajetória | fração da fase sem ninguém a menos de D m | geométrica | A |
| `proximity_child_frac` | 1 | trajetória | fração a menos de D m de outra criança | geométrica | A |
| `proximity_adult_frac` | 1 | trajetória | fração a menos de D m de adulto | geométrica | A |
| `group_size_dist` | 1 | trajetória | distribuição do tempo em díade / tríade / grupo ≥4 | geométrica | A |
| `n_distinct_peers_day` | 2 | trajetória | número de pares distintos com copresença > T min | — | A |
| `peer_copresence_matrix` | 2 | trajetória | matriz criança × criança de tempo de copresença — preferência entre pares | — | A |
| `approach_initiated` | 2 | trajetória | aproximações iniciadas pela criança (redução de distância abaixo de D, ela em movimento) | humano × IA | A |
| `approach_received` | 2 | trajetória | aproximações recebidas | humano × IA | A |
| `child_approaches_adult` | 2 | trajetória | aproximações a adulto iniciadas pela criança | humano × IA | A |
| `adult_approaches_child` | 2 | trajetória | aproximações do adulto à criança | humano × IA | A |
| `parallel_work_frac` | 2 | trajetória + episódio | mesma área, próximas, sem interação — trabalho paralelo | humano × IA | B |
| `joint_attention_episode` | 2 | pose (cabeça) + objeto | duas pessoas orientadas ao mesmo objeto por > T s | humano × IA | C |
| `imitation_lag` | 2 | ação + proximidade | criança B repete ação de A em janela T após copresença — precursor de difusão | humano × IA | C |
| `withdrawal_after_conflict` | 2 | trajetória + conflito | afastamento e isolamento após episódio de conflito | humano × IA | C |

## 4. Atividade e work episode

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `work_episode_count` | 2 | vídeo | episódios por fase | humano × IA (kappa) | B |
| `work_episode_duration` | 2 | vídeo | do início da manipulação ao abandono/guarda — média, máxima, distribuição | humano × IA (ICC) | B |
| `longest_uninterrupted_work` | 2 | vídeo | maior episódio contínuo do dia | humano × IA | B |
| `work_episode_interruptions` | 2 | vídeo | desengajamentos > limiar T dentro do episódio | humano × IA (kappa) | B |
| `return_after_interruption` | 2 | vídeo | retomou o mesmo material em até T s | humano × IA | B |
| `completed_cycle_ratio` | 2 | vídeo | episódios que terminam em "guardar" / total | humano × IA | B |
| `orientation_to_material_frac` | 1 | pose (cabeça/tronco) | fração do episódio com orientação corporal compatível com o material | humano × IA | B |
| `transition_time_between_episodes` | 2 | vídeo | intervalo entre fim de um episódio e início do próximo — latência de escolha | humano × IA | B |
| `material_id_used` | 1 | detecção + ontologia | material de cada episódio | humano × IA (mAP, T11) | B |
| `material_diversity_day` | 2 | derivada | materiais distintos no dia | — | B |
| `material_repetition` | 2 | derivada | mesmo material em dias consecutivos — **repetição é significativa em Montessori** | — | B |
| `area_of_work_dist` | 2 | derivada | distribuição do tempo de trabalho por área pedagógica | — | B |
| `manipulation_rate` | 1 | mãos + objeto | manipulações por minuto no episódio | humano × IA | C |
| `self_correction_count` | 2 | vídeo + ontologia | correções após erro acusado pelo **controle de erro** do material | humano × IA | B |
| `presentation_received` | 2 | vídeo + adulto | material apresentado por adulto à criança (início, material) | humano × IA | B |
| `adult_intervention_in_episode` | 2 | vídeo | intervenções adultas durante o episódio | humano × IA | B |
| `open_ended_activity_duration` | 2 | vídeo | tempo em atividade aberta (desenho, construção livre) | humano × IA | B |

## 5. Motor fino

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `hand_detect_rate` | — | mãos | fração de quadros do episódio com mão detectada acima do limiar — **qualidade** | T9 | C |
| `hand_dominance_ratio` | 2 | mãos | manipulações direita / total | humano × IA | C |
| `bimanual_frac` | 2 | mãos | fração de manipulações com as duas mãos | humano × IA | C |
| `hand_transfer_events` | 2 | mãos + objeto | transferências de objeto entre mãos | humano × IA | C |
| `pincer_grasp_events` | 1 | mãos | preensões em pinça polegar-indicador | humano × IA | C |
| `pincer_stability` | 1 | mãos | variância da distância polegar-indicador durante preensão | humano × IA | C |
| `grasp_type_dist` | 1 | mãos | distribuição de tipos de preensão (pinça, palmar, trípode…) | humano × IA | C |
| `reach_duration` | 1 | mãos | do início do alcance ao contato | humano × IA | C |
| `reach_smoothness` | 1 | mãos | jerk normalizado da trajetória da mão | humano × IA | C |
| `reach_corrections` | 1 | mãos | inversões de velocidade durante o alcance | humano × IA | C |
| `time_to_fit` | 2 | mãos + objeto | do primeiro contato ao encaixe correto | humano × IA | C |
| `fit_attempts` | 2 | mãos + objeto | tentativas até o encaixe | humano × IA | C |

## 6. Motor grosso

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `gait_speed` | 1 | trajetória + pose | velocidade em marcha | geométrica | A |
| `balance_events` | 1 | pose | tropeços, quedas, apoios súbitos | humano × IA | B |
| `climb_jump_events` | 1 | pose | subidas, saltos | humano × IA | B |
| `posture_transitions_h` | 1 | pose | mudanças de postura por hora | humano × IA | A |
| `carry_stability` | 1 | pose + objeto | oscilação do tronco ao transportar material (bandeja, jarra) | humano × IA | C |

## 7. Linguagem e áudio

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `speaker_attribution_accuracy` | — | áudio | acurácia de atribuição contra anotação manual **desta sala** — **pré-requisito** das linhas abaixo | T13 | C |
| `vocalization_count` | 1 | áudio (mic individual) | vocalizações por hora | humano × IA | C |
| `speech_duration` | 1 | áudio | tempo de fala atribuído à criança | humano × IA; exige atribuição validada | C |
| `child_initiations` | 2 | áudio | enunciados não precedidos por fala dirigida a ela em janela T | humano × IA | C |
| `child_responses` | 2 | áudio | enunciados em janela T após fala dirigida a ela | humano × IA | C |
| `conversational_turns` | 2 | áudio | trocas alternadas em janela T — **condicionada** a `speaker_attribution_accuracy` | humano × IA | C |
| `response_latency` | 2 | áudio | do fim da fala do adulto ao início da resposta | humano × IA; mais robusta com mic individual | C |
| `adult_speech_to_child_duration` | 1 | áudio + posição | fala adulta dirigida à criança (proximidade + orientação) | humano × IA | C |
| `prosody_f0_mean` / `prosody_f0_var` | 1 | áudio | F0 médio e variância na fala da criança | acústica | C |
| `prosody_intensity` | 1 | áudio | intensidade média | acústica | C |
| `speech_rate` | 1 | áudio | sílabas por segundo (estimativa acústica) | acústica | C |
| `laughter_events` | 1 | áudio | risos detectados | humano × IA | C |
| `cry_events` | 1 | áudio (VCM) | choro / vocalização de distress — **evento acústico, não rótulo emocional** | humano × IA | C |
| `singing_humming_frac` | 1 | áudio | fração com canto ou murmúrio melódico | humano × IA | C |
| `mlu` | 2 | ASR | **bloqueada** até WER medida em T14 | — | D |
| `lexical_diversity` | 2 | ASR | **bloqueada** até WER medida | — | D |

## 8. Substrato emocional

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `face_usable_frac` | — | rosto | fração de quadros com rosto em resolução e orientação utilizáveis — **qualidade** | T10 | C |
| `au_intensity_*` | 1 | rosto | intensidade por unidade de ação facial (FACS) — **medida física, sem rótulo emocional** | codificador FACS (ICC) | C |
| `motion_agitation_index` | 1 | pose | energia de movimento e jerk do corpo por época | — | A |
| `self_touch_events` | 1 | mãos + pose | mão ao rosto, autotoque, sucção de dedo | humano × IA | C |
| `posture_closed_frac` | 1 | pose | fração em postura encolhida | humano × IA | C |
| `gaze_aversion_events` | 1 | pose (cabeça) | desvios de orientação de cabeça em interação | humano × IA | C |
| `distress_episode` | 2 | áudio + vídeo | início, duração, desfecho | humano × IA (kappa) | C |
| `recovery_time` | 2 | multimodal | do início do distress ao retorno ao comportamento de base ou ao trabalho | humano × IA (ICC) | C |
| `coregulation_latency` | 2 | trajetória + distress | aproximação do adulto → resolução | humano × IA | C |
| `self_resolved_distress_ratio` | 2 | derivada | distress resolvido sem adulto / total | — | C |
| `conflict_episode` | 2 | multimodal | duas crianças, objeto disputado, duração, tipo de resolução (autorresolvido / par / adulto) | humano × IA | C |
| `persistence_after_error` | 2 | vídeo | tentativas após o primeiro erro antes de abandonar — **sai do work episode, sem rosto** | humano × IA | **B** |
| `frustration_abandon_ratio` | 2 | vídeo | erro → abandono / erro → nova tentativa — **sem rosto** | humano × IA | **B** |
| `external_ser_scores` | 3 | SDQ / ERC / CBCL-TRF | escores por onda — **critério externo** para calibrar as linhas acima | instrumento validado | B |

## 9. Substrato de criatividade

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `noncanonical_use` | 2 | ação + ontologia de materiais | desvio da sequência canônica autorada — detectado **como desvio**, sem julgar | humano × IA | C |
| `material_combination` | 2 | detecção + ontologia | materiais de áreas distintas usados juntos | humano × IA | C |
| `strategy_sequence_n` | 2 | ação | abordagens distintas sobre o mesmo problema num episódio (fluência) | humano × IA | C |
| `strategy_category_n` | 2 | ação + esquema humano | categorias distintas de abordagem (flexibilidade) | humano × IA | C |
| `exploration_ratio` | 2 | ação | manipulação exploratória / ação dirigida a objetivo antes da solução | humano × IA | C |
| `return_and_modify` | 2 | episódio | retorno a trabalho anterior com modificação (elaboração) | humano × IA | C |
| `construction_element_n` | 2 | detecção | elementos distintos numa construção livre | humano × IA | C |
| `action_rarity` | 2 | derivada | `P(ação \| material, sala, período)` no corpus acumulado — **frequência, não julgamento** (originalidade) | interna; exige ≥1 ano | D |
| `first_occurrence_flag` | 2 | derivada | primeira ocorrência da ação no corpus da sala | interna | D |
| `novelty_diffusion_lag` | 2 | derivada | intervalo entre a 1ª ocorrência de uma ação e sua repetição por outra criança, com copresença no intervalo | humano × IA | D |
| `novelty_adopters_n` | 2 | derivada | número de crianças que repetem uma ação nova em janela T | interna | D |
| `external_creativity_scores` | 3 | TTCT-tipo / nomeação de educador | por onda — **critério externo** | instrumento | C |

## 10. Adulto

| Variável | Nível | Fonte | Definição operacional | Validação | Camada |
|---|---|---|---|---|---|
| `adult_presentations_given` | 2 | vídeo | apresentações de material (a quem, qual, quando) | humano × IA | B |
| `adult_observing_frac` | 2 | trajetória + pose | fração parada, orientada a crianças, sem interação | humano × IA | B |
| `adult_intervening_frac` | 2 | vídeo | fração em interação direta | humano × IA | B |
| `adult_redirections` | 2 | vídeo + áudio | redirecionamentos de criança | humano × IA | B |
| `adult_position_dist` | 1 | trajetória | distribuição do adulto por área | geométrica | A |
| `adult_child_ratio_by_area` | 1 | trajetória | adultos / crianças por área por fase | geométrica | A |

> Reporte de adulto é **agregado por padrão**; dado individual só sob regra escrita acordada com
> a equipe (Parte III §6, Parte IV §1.8).

---

## Nível 3 — constructos

**Não entram como variável medida.** Cada um é um constructo derivado, com o conjunto de
variáveis de nível 1–2 que o compõe declarado explicitamente e validado contra critério externo:

| Constructo | Compõe-se de | Critério externo |
|---|---|---|
| concentração | duração, interrupções, retorno, ciclo completo, orientação ao material | codificação humana; escala de engajamento |
| autorregulação | recovery_time, self_resolved_ratio, persistence_after_error, frustration_abandon_ratio | SDQ, ERC |
| coordenação visuomotora | reach_*, time_to_fit, fit_attempts | prova motora padronizada por onda |
| destreza fina | pincer_*, grasp_type_dist, manipulation_rate | idem |
| criatividade | strategy_*, exploration_ratio, return_and_modify, action_rarity, noncanonical_use | TTCT-tipo, nomeação de educador |
| desenvolvimento linguístico | speech_duration, initiations, response_latency, (mlu se desbloqueada) | instrumento de linguagem por onda |

**Contagem:** ~135 variáveis observadas. Camadas 0 + A somam ~55 e são o foco de validação do
primeiro semestre. R1 em forma de tabela: **a lista que cresce é esta; a lista de constructos
reportados permanece curta.**
