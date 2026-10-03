-- Janela automática por entrada (Projeto B) + backfill. Aditiva e guardada:
-- a função do trigger captura qualquer erro e emite WARNING — nunca aborta o INSERT da página.
-- SECURITY DEFINER: a página escreve como anon/authenticated e dev_janelas tem RLS sem policy;
-- sem isso o INSERT da janela seria negado silenciosamente.

alter table dev_janelas add column if not exists pontuacao_pendente jsonb;
comment on column dev_janelas.pontuacao_pendente is
  'saída do modelo quando a criança-alvo não pôde ser ligada a alunos.id; alguém liga depois e a linha vai para obs_avaliacoes';

create or replace function dev_janela_da_entrada(p_entrada_id uuid) returns uuid
language plpgsql security definer set search_path = public as $$
declare e record; v_id uuid;
begin
  select id, sala, relogio, tipo into e from observacao_entradas where id = p_entrada_id;
  if e.id is null or e.sala is null or e.relogio is null or e.tipo not in ('corte','fala') then
    return null;
  end if;
  if not exists (select 1 from salas_cameras where sala = e.sala) then
    return null;  -- ex.: 'sala 1' até ser confirmada como 'sala 1a3'
  end if;
  select id into v_id from dev_janelas where entrada_id = e.id and origem = 'entrada';
  if v_id is not null then return v_id; end if;
  insert into dev_janelas (projeto, sala, inicio, fim, origem, entrada_id)
  values ('B', e.sala, e.relogio - interval '90 seconds', e.relogio + interval '90 seconds', 'entrada', e.id)
  returning id into v_id;
  return v_id;
end $$;

create or replace function trg_dev_janela_da_entrada() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  begin
    perform dev_janela_da_entrada(new.id);
  exception when others then
    raise warning 'dev_janela_da_entrada falhou para %: %', new.id, sqlerrm;
  end;
  return new;
end $$;

drop trigger if exists observacao_entradas_dev_janela on observacao_entradas;
create trigger observacao_entradas_dev_janela
after insert or update of sala, relogio, tipo on observacao_entradas
for each row execute function trg_dev_janela_da_entrada();

-- Backfill: entradas existentes com sala válida e tipo corte/fala
do $$ begin
  perform dev_janela_da_entrada(id) from observacao_entradas
   where sala is not null and tipo in ('corte','fala');
end $$;
