-- Pontuação automática das janelas (Projeto B) — fila, contagem, disparo e agendamento.
-- Aplicado em 07/09/2026 como migration `pontuacao_janelas_v0`.
-- Padrão da casa: a fila vem pronta do banco (not exists + limit); o disparo lê a chave do Vault
-- e chama a edge function `pontuar-janelas` via pg_net; pg_cron agenda (deslocado 7 min do
-- `indexa-observacao`, que roda em */15).

-- Fila: janelas de entrada com texto (transcrição ou nota) e sem nota do modelo nesta versão do
-- codebook. Quem tem pontuacao_pendente (não avaliável, criança não ligada, falha) sai da fila;
-- apagar o jsonb (set null) re-enfileira.
create or replace function public._janelas_para_pontuar(
  p_limite int default 5, p_modelo text default 'claude-opus-5', p_versao text default 'v1', p_min int default 40)
returns table (janela_id uuid, projeto text, sala text, inicio timestamptz, fim timestamptz,
               entrada_id uuid, tipo text, texto text, especialista text)
language sql stable
set search_path = public
as $$
  select j.id, j.projeto, j.sala, j.inicio, j.fim, e.id, e.tipo,
         coalesce(nullif(btrim(e.transcricao), ''), nullif(btrim(e.nota), '')) as texto,
         s.especialista
  from dev_janelas j
  join observacao_entradas e on e.id = j.entrada_id
  left join observacao_sessoes s on s.id = e.sessao_id
  where j.origem = 'entrada'
    and j.pontuacao_pendente is null
    and length(coalesce(nullif(btrim(e.transcricao), ''), nullif(btrim(e.nota), ''), '')) >= p_min
    and not exists (select 1 from obs_avaliacoes a
                    where a.janela_id = j.id and a.avaliador = p_modelo and a.codebook_versao = p_versao)
  order by j.inicio
  limit greatest(p_limite, 1);
$$;

create or replace function public._janelas_pendentes_pontuacao(
  p_modelo text default 'claude-opus-5', p_versao text default 'v1', p_min int default 40)
returns bigint
language sql stable
set search_path = public
as $$
  select count(*)
  from dev_janelas j
  join observacao_entradas e on e.id = j.entrada_id
  where j.origem = 'entrada'
    and j.pontuacao_pendente is null
    and length(coalesce(nullif(btrim(e.transcricao), ''), nullif(btrim(e.nota), ''), '')) >= p_min
    and not exists (select 1 from obs_avaliacoes a
                    where a.janela_id = j.id and a.avaliador = p_modelo and a.codebook_versao = p_versao);
$$;

-- Disparo (mesmo desenho de disparar_indexacao_observacao): a chave nunca sai do banco.
create or replace function public.disparar_pontuacao_janelas(p_limite int default 5)
returns bigint
language plpgsql
security definer
set search_path = public, vault, extensions
as $$
declare v_key text; v_id bigint;
begin
  select decrypted_secret into v_key from vault.decrypted_secrets where name = 'observacao_key';
  select net.http_get(
    url := 'https://rmpnqrvsmxhnrwlgqmdp.supabase.co/functions/v1/pontuar-janelas?key=' || v_key
           || '&limite=' || greatest(coalesce(p_limite, 5), 1),
    timeout_milliseconds := 120000
  ) into v_id;
  return v_id;
end;
$$;
revoke execute on function public.disparar_pontuacao_janelas(int) from public, anon, authenticated;
revoke execute on function public._janelas_para_pontuar(int, text, text, int) from anon, authenticated;
revoke execute on function public._janelas_pendentes_pontuacao(text, text, int) from anon, authenticated;

-- Agenda: dias úteis, 11–23 UTC (8–20 h Brasília), a cada 15 min deslocado do indexa-observacao.
select cron.schedule('pontuar-janelas', '7,22,37,52 11-23 * * 1-5', 'select public.disparar_pontuacao_janelas();');
