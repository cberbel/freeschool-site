-- DDL v0 — desenvolvimento infantil (Projeto A e Projeto B)
-- Aditiva: só cria tabelas e colunas nulas. Não altera nem apaga dado existente.
-- RLS ligado em toda tabela nova, sem policy: só service_role acessa (o worker); as páginas
-- só passam a ver estas tabelas quando uma policy for escrita de propósito.
-- Reverter: drop table das tabelas novas + drop column das colunas novas.

create table if not exists cameras (
  id            text primary key,
  sala          text not null references salas_cameras(sala),
  nome          text not null,
  aparelho      text,
  fabricante    text, modelo text, firmware text,
  canal_nvr     smallint, host_nvr text,
  protocolo     text check (protocolo in ('rtsp','http-flv')),
  path_main     text, path_sub text,
  res_main      text, fps_main smallint, bitrate_kbps_main int,
  res_sub       text, fps_sub smallint,
  codec         text, hfov_graus smallint, altura_m numeric, ptz boolean,
  tem_mic       boolean, tem_stream boolean,
  fps_deteccao  smallint, fps_pose smallint,
  verificado_em timestamptz
);
comment on table cameras is 'Uma linha por câmera (entidade). salas_cameras continua como agrupamento por sala. Nunca guardar usuário/senha aqui.';

create table if not exists obs_codebook (
  versao text primary key, descricao text not null, dimensoes jsonb not null,
  vigente_de date not null, vigente_ate date,
  kappa_inter numeric, kappa_intra numeric, n_clipes int, medido_em date, decisoes jsonb
);

create table if not exists dev_janelas (
  id          uuid primary key default gen_random_uuid(),
  projeto     text not null check (projeto in ('A','B','comum')),
  aluno_id    uuid references alunos(id),
  camera_id   text references cameras(id),
  sala        text not null references salas_cameras(sala),
  inicio      timestamptz not null,
  fim         timestamptz not null,
  duracao_s   int generated always as (extract(epoch from (fim - inicio))::int) stored,
  origem      text not null check (origem in ('entrada','sorteio','evento','corte')),
  entrada_id  uuid references observacao_entradas(id),
  clip_path   text,
  janela_rotulo_inicio_s smallint default 30,
  janela_rotulo_fim_s    smallint default 150,
  presente    boolean,
  criado_em   timestamptz not null default now()
);
create index if not exists dev_janelas_sala_inicio on dev_janelas (sala, inicio);
create index if not exists dev_janelas_aluno_inicio on dev_janelas (aluno_id, inicio);
comment on table dev_janelas is 'Unidade de medida: janela criança × tempo. origem=entrada (Projeto B), sorteio (Projeto A), comum (conjunto de comparação).';

create table if not exists obs_avaliacoes (
  id uuid primary key default gen_random_uuid(),
  projeto    text not null check (projeto in ('A','B','comum')),
  janela_id  uuid not null references dev_janelas(id) on delete cascade,
  entrada_id uuid references observacao_entradas(id),
  aluno_id   uuid not null references alunos(id),
  avaliador  text not null,
  avaliador_tipo text not null check (avaliador_tipo in ('humano','modelo')),
  envolvimento smallint check (envolvimento between 1 and 5),
  autonomia    smallint check (autonomia between 1 and 5),
  persistencia smallint check (persistencia between 1 and 5),
  persistencia_motivo text,
  contexto text, material text, adulto_proximo boolean,
  confianca smallint check (confianca between 1 and 5),
  justificativa text,
  modelo text, codebook_versao text not null references obs_codebook(versao),
  em timestamptz not null default now(),
  unique (janela_id, aluno_id, avaliador, codebook_versao)
);
comment on column obs_avaliacoes.avaliador is 'sempre lower(trim()) — humano: nome da avaliadora; modelo: id do modelo';
comment on column obs_avaliacoes.persistencia_motivo is 'sem_oportunidade quando não houve dificuldade nem interrupção na janela';

create table if not exists obs_golden (
  janela_id uuid primary key references dev_janelas(id),
  projeto   text not null check (projeto in ('A','B','comum')),
  incluido_em date not null default current_date,
  motivo text, consenso jsonb, permanente boolean not null default true
);

create table if not exists materiais (
  id uuid primary key default gen_random_uuid(),
  nome text not null, area text, sala text references salas_cameras(sala),
  tag_epc text unique, estante text, criado_em timestamptz default now()
);

create table if not exists captacao_stats (
  ts timestamptz not null, camera_id text references cameras(id),
  camera_fps numeric, process_fps numeric, skipped_fps numeric, detection_fps numeric,
  cpu_pct numeric, ram_mb int, pipeline_versao text not null, primary key (ts, camera_id)
);

create table if not exists reteste_cameras (
  instante timestamptz, cam_a text references cameras(id), cam_b text references cameras(id),
  metrica text, valor numeric, pipeline_versao text, primary key (instante, cam_a, cam_b, metrica)
);

create table if not exists eventos_ambiente (
  id uuid primary key default gen_random_uuid(), sala text, camera_id text references cameras(id),
  data date not null, tipo text not null, descricao text
);

create table if not exists bifurcacao_esforco (
  id uuid primary key default gen_random_uuid(), semana date not null,
  projeto text not null check (projeto in ('A','B','comum')),
  categoria text not null check (categoria in ('construcao','operacao','especialista','hardware_brl','api_usd','outro')),
  quantidade numeric not null, quem text, nota text
);

create table if not exists bifurcacao_resultados (
  semana date not null, projeto text not null check (projeto in ('A','B')),
  metrica text not null, valor numeric, n integer, nota text,
  primary key (semana, projeto, metrica)
);

alter table observacao_sessoes
  add column if not exists relogio_servidor timestamptz,
  add column if not exists offset_s numeric;
alter table observacao_entradas
  add column if not exists video_path text,
  add column if not exists video_camera text references cameras(id),
  add column if not exists video_ref_inicio timestamptz;
comment on column observacao_entradas.video_ref_inicio is 'instante real do 1º quadro do clipe (ffprobe após o corte)';
comment on column observacao_entradas.video_inicio_s   is 'offset em s relativo a relogio (−90)';
comment on column observacao_entradas.video_fim_s      is 'offset em s relativo a relogio (+90)';
comment on column observacao_entradas.janela_ini_s     is 'offset em s relativo ao início do clipe (trecho efetivamente assistido)';
comment on column observacao_entradas.janela_fim_s     is 'offset em s relativo ao início do clipe (trecho efetivamente assistido)';

-- RLS: ligado, sem policy (service_role apenas)
alter table cameras enable row level security;
alter table obs_codebook enable row level security;
alter table dev_janelas enable row level security;
alter table obs_avaliacoes enable row level security;
alter table obs_golden enable row level security;
alter table materiais enable row level security;
alter table captacao_stats enable row level security;
alter table reteste_cameras enable row level security;
alter table eventos_ambiente enable row level security;
alter table bifurcacao_esforco enable row level security;
alter table bifurcacao_resultados enable row level security;

-- Semente: câmeras a partir de salas_cameras.cameras[] (ficha técnica vem do T0)
insert into cameras (id, sala, nome, aparelho)
select lower(regexp_replace(regexp_replace(translate(c, 'ÁÀÂÃÄáàâãäÉÈÊËéèêëÍÌÎÏíìîïÓÒÔÕÖóòôõöÚÙÛÜúùûüÇç', 'AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUUuuuuCc'), '[^A-Za-z0-9]+', '-', 'g'), '(^-|-$)', '', 'g')) || '@' ||
       lower(regexp_replace(regexp_replace(translate(sc.sala, 'ÁÀÂÃÄáàâãäÉÈÊËéèêëÍÌÎÏíìîïÓÒÔÕÖóòôõöÚÙÛÜúùûüÇç', 'AAAAAaaaaaEEEEeeeeIIIIiiiiOOOOOoooooUUUUuuuuCc'), '[^A-Za-z0-9]+', '-', 'g'), '(^-|-$)', '', 'g')),
       sc.sala, c, c
from salas_cameras sc, unnest(sc.cameras) as c
on conflict (id) do nothing;

-- Semente: codebook v1
insert into obs_codebook (versao, descricao, dimensoes, vigente_de)
values ('v1', 'Envolvimento (LIS-YC adaptada), autonomia e persistência — 5 níveis com âncora comportamental. Vale para humanos e modelo.',
        '{
  "versao": "v1",
  "data": "2026-09-06",
  "base": "Escala de Envolvimento de Leuven (LIS-YC, Laevers) adaptada ao vocabulário Montessori; autonomia e persistência definidas para o ciclo de trabalho Montessori.",
  "principio": "Pontua-se o que se vê, não o que se supõe. Movimento não é desatenção (vida prática é engajamento em movimento); imobilidade não é concentração (sesta, fila e olhar vago são imóveis).",
  "unidade": {
    "janela": "2 minutos centrais de um clipe de 3 minutos (±30 s de contexto). Ao vivo: os 2 minutos anteriores ao registro da entrada.",
    "alvo": "Uma nota por criança-alvo por janela. Outras crianças visíveis ≥ 50% da janela podem receber nota como alvo secundário.",
    "nota": "Holística: o nível que melhor caracteriza a janela inteira. Se houver mudança clara no meio, registrar o predominante e anotar ''mudança'' no comentário.",
    "nao_avaliavel": [
      "criança fora do quadro ou de costas > 50% da janela",
      "áudio/vídeo inutilizável",
      "criança ausente da escola"
    ],
    "confianca": "1 = quase chute (visibilidade ruim); 3 = razoável; 5 = vi tudo com clareza."
  },
  "campos": {
    "contexto": [
      "vida_pratica",
      "sensorial",
      "linguagem",
      "matematica",
      "cultural_ciencias",
      "arte_musica",
      "movimento_patio",
      "refeicao",
      "roda_circulo",
      "transicao_arrumacao",
      "livre_sem_material",
      "sesta_repouso"
    ],
    "material": "Nome do material como a equipe chama (ex.: ''torre rosa'', ''encaixes de cilindros'', ''lavar a mesa''). Texto livre até existir o catálogo `materiais`.",
    "adulto_proximo": "true se um adulto ficou a ≤ 2 m da criança por ≥ 30 s na janela — é contexto, não nota: adulto perto sem intervir não reduz autonomia."
  },
  "dimensoes": {
    "envolvimento": {
      "definicao": "Intensidade da atividade mental da criança na tarefa que escolheu ou em que está: concentração, energia, precisão, persistência da atenção, resistência a distração.",
      "observaveis": [
        "postura e olhar orientados ao material/tarefa",
        "precisão e ritmo do movimento (mãos ocupadas com o material)",
        "reação a estímulos externos: vira a cabeça? retorna?",
        "continuidade: pausas e retomadas",
        "sinais de energia: fala consigo, ritmo, repetição espontânea, expressão"
      ],
      "armadilhas": [
        "pontuar alto porque a criança está parada e quieta (pode ser dispersão ou sono)",
        "pontuar baixo porque a criança se move (carregar bandeja, varrer, lavar é trabalho)",
        "pontuar a tarefa ''difícil'' em vez da criança na tarefa"
      ],
      "niveis": {
        "1": "Extremamente baixo — sem atividade: olhar vago, vagando, parada sem direção; ou gesto mecânico/estereotipado sem sinal de energia mental. Não há tarefa, ou a tarefa é só aparência.",
        "2": "Baixo — atividade com interrupções frequentes: começa, distrai-se, olha em volta, mexe em outra coisa; ações sem continuidade; abandona fácil; qualquer estímulo tira a atenção e ela não volta.",
        "3": "Moderado — atividade contínua mas sem intensidade: faz o que a tarefa pede, em rotina; pouca precisão, pouca energia; vira a cabeça quando algo acontece e demora a voltar; não há sinal de satisfação nem de esforço.",
        "4": "Alto — atividade contínua com momentos claros de intensidade: concentração visível, movimento preciso em parte da janela, retoma sozinha após distração breve; energia em alguns trechos (ritmo, cuidado, repetição de um passo).",
        "5": "Extremamente alto — absorvida quase toda a janela: corpo e olhar no material, movimento preciso, ritmo próprio; estímulo externo não desvia (ou desvia e a atenção volta em ≤ 2 s); sinais de satisfação/energia (fala consigo, repete o ciclo, ajusta detalhes). É a ''polarização da atenção'' de Montessori."
      },
      "exemplos_montessori": {
        "5": "Desmonta e remonta a torre rosa três vezes seguidas sem olhar a sala; lava a mesa cumprindo a sequência inteira com ritmo, molhando, esfregando, secando, e volta a esfregar um canto que ficou sujo.",
        "3": "Coloca os cilindros nos encaixes na ordem, sem erro e sem prazer aparente; olha para a porta cada vez que alguém entra e demora a voltar.",
        "1": "Anda pela sala com um material na mão sem usá-lo; senta no tapete olhando o teto."
      }
    },
    "autonomia": {
      "definicao": "Quanto do ciclo de trabalho (escolher, buscar, executar, corrigir o erro, guardar) a criança faz por iniciativa própria e sem depender de adulto.",
      "observaveis": [
        "quem iniciou: a criança ou o adulto?",
        "número e tipo de intervenções do adulto na janela (instrução, correção, ajuda física)",
        "resolve obstáculo simples sozinha? (busca o pano, ajusta o tapete, pega o que falta)",
        "usa o controle de erro do material?",
        "guarda no lugar sem ser lembrada?"
      ],
      "armadilhas": [
        "reduzir a nota só porque há adulto perto (registrar em adulto_proximo, não na nota)",
        "confundir autonomia com envolvimento: dá para ser autônoma e pouco envolvida, e vice-versa",
        "pontuar 5 uma criança que faz sozinha porque foi mandada passo a passo"
      ],
      "niveis": {
        "1": "Não inicia nem sustenta atividade sem adulto: espera instrução; só age quando dirigida; pede ajuda antes de tentar; para assim que o adulto se afasta.",
        "2": "Inicia com sugestão ou convite do adulto e precisa de acompanhamento contínuo; várias intervenções na janela; não guarda sem ser lembrada.",
        "3": "Escolhe o material sozinha ou com leve sugestão; executa com 1–2 intervenções pontuais; pede ajuda depois de tentar; guarda com lembrete.",
        "4": "Escolhe, busca, executa e guarda com no máximo uma intervenção; resolve obstáculos simples sozinha; usa o controle de erro do material ao menos uma vez.",
        "5": "Ciclo completo autoiniciado: escolhe, transporta, executa, corrige o próprio erro, guarda no lugar; adulto ausente ou presente sem interferir; pode ajudar outra criança sem que lhe peçam."
      },
      "exemplos_montessori": {
        "5": "Pega o tapete, escolhe os encaixes, trabalha, percebe o cilindro que sobrou, refaz, enrola o tapete e devolve tudo à prateleira — sem ninguém falar com ela.",
        "2": "Só começa quando a professora senta ao lado e oferece o material; para de trabalhar quando ela levanta."
      }
    },
    "persistencia": {
      "definicao": "Manter ou retomar a atividade diante de dificuldade, erro ou interrupção; e repetir por vontade própria até dominar.",
      "observaveis": [
        "o que aconteceu de difícil na janela: erro, peça que não encaixa, queda, interrupção por outra criança/adulto",
        "após a dificuldade: tenta de novo? muda de estratégia? pede ajuda? abandona?",
        "retoma depois de interrupção? em quanto tempo?",
        "repete o ciclo inteiro espontaneamente?"
      ],
      "armadilhas": [
        "pontuar sem ter havido dificuldade ou interrupção — nesse caso marcar ''sem_oportunidade'' e não dar nota",
        "confundir teimosia sem estratégia (bater a peça no lugar errado 20 vezes) com persistência de nível 5: repetição sem ajuste é 3, não 5"
      ],
      "sem_oportunidade": "Se não houve erro, dificuldade nem interrupção observável na janela, a persistência fica em branco com motivo ''sem_oportunidade''. Isso é dado válido.",
      "niveis": {
        "1": "Abandona à primeira dificuldade ou interrupção; não retoma; troca de material sem concluir.",
        "2": "Tenta uma vez, desiste ou pede que o adulto faça; só retoma se for conduzida de volta.",
        "3": "Repete tentativas após o erro por algum tempo, sem mudar de estratégia; retoma após interrupção curta, mas conclui só parcialmente ou muda de estratégia com ajuda.",
        "4": "Persiste até concluir apesar do erro ou interrupção; muda de estratégia sozinha; retoma após interrupções sem ajuda.",
        "5": "Conclui e recomeça por vontade própria (repete o ciclo inteiro ≥ 2 vezes) ou insiste até dominar; interrupções não quebram o ciclo — retoma exatamente de onde parou."
      },
      "exemplos_montessori": {
        "5": "A torre cai; ela ri, desmonta o que sobrou e refaz do início; depois de pronta, desmonta e faz de novo.",
        "1": "O encaixe não entra; ela larga a peça na mesa e vai para outra prateleira."
      }
    }
  },
  "regras_para_modelo": {
    "papel": "O modelo pontua com este mesmo codebook e grava com avaliador_tipo = ''modelo'' e o id do modelo; nunca sobrescreve nota humana. A nota humana pode chegar a qualquer momento, sobre a mesma janela — ao vivo ou no passado.",
    "entrada": "Transcrição da observadora e/ou 4–16 quadros amostrados da janela (recorte 512×512 na criança-alvo). Se só há transcrição, pontuar o que ela descreve e marcar confianca ≤ 3.",
    "saida": {
      "envolvimento": "1-5 ou null",
      "autonomia": "1-5 ou null",
      "persistencia": "1-5, null ou ''sem_oportunidade''",
      "contexto": "um valor da lista",
      "material": "texto ou null",
      "adulto_proximo": "true/false/null",
      "confianca": "1-5",
      "justificativa": "≤ 30 palavras citando o observável"
    }
  },
  "versionamento": "Mudança de âncora = v1.1, v1.2… com data; kappa/alfa medido por versão e registrado em obs_codebook (kappa_inter, kappa_intra, n_clipes, medido_em). Notas de versões diferentes não se misturam numa mesma análise sem reponderação."
}'::jsonb, date '2026-09-06')
on conflict (versao) do nothing;

-- Pendências deliberadas (não estão nesta migração):
--   * trigger que cria dev_janelas(origem='entrada', projeto='B') a cada entrada com sala — entra junto com os sliders, testado;
--   * update observacao_sessoes set especialista = lower(trim(especialista)) — a página pode comparar o valor; normalizar na leitura até confirmar;
--   * update observacao_entradas set sala='sala 1a3' where sala='sala 1' — só após confirmação com a escola;
--   * policies para as páginas (anon/authenticated) — escrever quando a tela dos sliders existir.
