-- Apelidos de alunos + ligação manual de janela pendente. Aplicado em 07/09/2026 como migration
-- `aluno_apelidos_e_ligar_janela_pendente`. Motivo: o modelo leu "Max" na transcrição e não ligou
-- a Maximiliano (regra "só quando inequívoco" + casamento exato de nome). Agora: apelidos
-- registrados aqui entram na lista fechada que o modelo vê e na ligação por código
-- (nome completo exato → primeiro nome único → apelido → prefixo do primeiro nome, 3+ letras).

create table if not exists public.aluno_apelidos (
  aluno_id  uuid not null references public.alunos(id) on delete cascade,
  apelido   text not null,
  origem    text not null default 'escola',
  criado_em timestamptz not null default now(),
  primary key (aluno_id, apelido)
);
alter table public.aluno_apelidos enable row level security;  -- sem policy: só service role
comment on table public.aluno_apelidos is
  'Apelidos/diminutivos de alunos usados em sala (Max = Maximiliano). Lido por pontuar-janelas para ligar a criança citada.';

-- Liga uma janela com pontuação pendente (modelo pontuou, mas não ligou a criança) a um aluno:
-- move o JSON de dev_janelas.pontuacao_pendente para obs_avaliacoes e limpa o pendente.
-- Uso: select public.ligar_janela_pendente('<janela uuid>', '<aluno uuid>');
create or replace function public.ligar_janela_pendente(p_janela uuid, p_aluno uuid)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare p jsonb; v_id uuid; v_j record;
begin
  select * into v_j from dev_janelas where id = p_janela;
  if not found then raise exception 'janela % nao existe', p_janela; end if;
  p := v_j.pontuacao_pendente;
  if p is null or coalesce((p->>'avaliavel')::boolean, false) is not true then
    raise exception 'janela % nao tem pontuacao pendente avaliavel', p_janela;
  end if;
  if not exists (select 1 from alunos where id = p_aluno) then
    raise exception 'aluno % nao existe', p_aluno;
  end if;
  insert into obs_avaliacoes (projeto, janela_id, entrada_id, aluno_id, avaliador, avaliador_tipo,
     envolvimento, autonomia, persistencia, persistencia_motivo, contexto, material, adulto_proximo,
     confianca, justificativa, modelo, codebook_versao)
  values (v_j.projeto, v_j.id, v_j.entrada_id, p_aluno, p->>'modelo', 'modelo',
     (p->>'envolvimento')::smallint, (p->>'autonomia')::smallint, (p->>'persistencia')::smallint,
     p->>'persistencia_motivo', p->>'contexto', p->>'material', (p->>'adulto_proximo')::boolean,
     coalesce((p->>'confianca')::smallint, 1), coalesce(p->>'justificativa', ''), p->>'modelo', p->>'codebook')
  on conflict (janela_id, aluno_id, avaliador, codebook_versao) do nothing
  returning id into v_id;
  update dev_janelas
     set aluno_id = coalesce(aluno_id, p_aluno), presente = true, pontuacao_pendente = null
   where id = p_janela;
  return v_id;
end;
$$;
revoke execute on function public.ligar_janela_pendente(uuid, uuid) from public, anon, authenticated;

-- Dados (07/09): Max = Maximiliano; janela pendente do cubo do trinômio ligada a ele.
-- insert into aluno_apelidos (aluno_id, apelido) select id, 'Max' from alunos where nome = 'Maximiliano' and status = 'ativo';
-- select public.ligar_janela_pendente(<janela>, <aluno>);
