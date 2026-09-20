// pontuar-janelas — Projeto B, regra master ("tudo para hoje"): o sistema não espera avaliadoras.
// Pontua com o codebook VIGENTE (obs_codebook.vigente_ate is null) as janelas criadas por entrada
// de observação (dev_janelas.origem='entrada') cujo texto (transcrição do áudio ou nota) já existe.
// Grava em obs_avaliacoes com avaliador_tipo='modelo' — nunca toca nota humana; uma linha por
// janela × criança × modelo × versão do codebook. O que não consegue ligar a uma criança, ou não é
// avaliável (teste de microfone, conversa entre adultos), fica em dev_janelas.pontuacao_pendente
// e SAI da fila (apagar o jsonb re-enfileira). Falha de IA idem, marcada '#falha' (padrão da casa).
// Ligação da criança citada ao cadastro: nome completo exato → primeiro nome único → apelido
// registrado (aluno_apelidos: Max = Maximiliano) → prefixo do primeiro nome único (3+ letras).
// Roda pelo pg_cron via public.disparar_pontuacao_janelas(); mesma chave Anthropic do bot (secret).
// Fonte no repositório freeschool-site: docs/desenvolvimento-infantil/functions/pontuar-janelas/.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const URL_SUPA = Deno.env.get("SUPABASE_URL")!;
const SERVICE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const ANTHROPIC = (Deno.env.get("ANTHROPIC_API_KEY") ?? "").trim();
const MODELO = "claude-opus-5";
const MIN_CHARS = 40; // abaixo disso é teste de microfone; a fila (RPC) já filtra
const CONF_MAX_SEM_VIDEO = 3; // codebook v1: só transcrição, confiança no máximo 3

const CONTEXTOS = [
  "vida_pratica", "sensorial", "linguagem", "matematica", "cultural_ciencias", "arte_musica",
  "movimento_patio", "refeicao", "roda_circulo", "transicao_arrumacao", "livre_sem_material", "sesta_repouso",
];

const NOTA = { anyOf: [{ type: "integer", enum: [1, 2, 3, 4, 5] }, { type: "null" }] };
const TEXTO_OU_NULO = { anyOf: [{ type: "string" }, { type: "null" }] };

const SAIDA_SCHEMA = {
  type: "object",
  properties: {
    avaliavel: { type: "boolean", description: "false se o texto não descreve uma criança em atividade (teste de microfone, conversa entre adultos, instrução técnica, vazio)" },
    motivo_nao_avaliavel: TEXTO_OU_NULO,
    crianca_citada: { ...TEXTO_OU_NULO, description: "como a criança-alvo aparece no texto; null se nenhuma" },
    crianca_alvo: { ...TEXTO_OU_NULO, description: "nome EXATO da lista fechada (nome e sobrenome como na lista), só quando inequívoco; senão null" },
    envolvimento: NOTA,
    autonomia: NOTA,
    persistencia: NOTA,
    persistencia_motivo: { ...TEXTO_OU_NULO, description: "'sem_oportunidade' quando não houve dificuldade, erro nem interrupção" },
    contexto: { anyOf: [{ type: "string", enum: CONTEXTOS }, { type: "null" }] },
    material: TEXTO_OU_NULO,
    adulto_proximo: { anyOf: [{ type: "boolean" }, { type: "null" }] },
    confianca: { type: "integer", enum: [1, 2, 3, 4, 5] },
    justificativa: { type: "string", description: "até 30 palavras, citando o observável" },
  },
  required: [
    "avaliavel", "motivo_nao_avaliavel", "crianca_citada", "crianca_alvo", "envolvimento", "autonomia",
    "persistencia", "persistencia_motivo", "contexto", "material", "adulto_proximo", "confianca", "justificativa",
  ],
  additionalProperties: false,
};

type Saida = {
  avaliavel: boolean; motivo_nao_avaliavel: string | null; crianca_citada: string | null; crianca_alvo: string | null;
  envolvimento: number | null; autonomia: number | null; persistencia: number | null; persistencia_motivo: string | null;
  contexto: string | null; material: string | null; adulto_proximo: boolean | null; confianca: number; justificativa: string;
};
type Crianca = { id: string; nome: string; sobrenome: string | null; agrupada: number | null };
type Apelido = { aluno_id: string; apelido: string };
type Janela = {
  janela_id: string; projeto: string; sala: string | null; inicio: string; fim: string;
  entrada_id: string; tipo: string; texto: string; especialista: string | null;
};

Deno.serve(async (req) => {
  try {
    return await atender(req);
  } catch (e) {
    console.error("pontuar-janelas:", e);
    return new Response(JSON.stringify({ erro: String(e).slice(0, 300) }), { status: 500 });
  }
});

function norm(s: string | null | undefined): string {
  return (s ?? "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, " ").trim().toLowerCase();
}
function nomeCompleto(c: Crianca): string {
  return [c.nome, c.sobrenome].filter((x) => x && String(x).trim()).join(" ").replace(/\s+/g, " ").trim();
}
function nota(v: unknown): number | null {
  const n = Number(v);
  return Number.isInteger(n) && n >= 1 && n <= 5 ? n : null;
}
function texto(v: unknown, max: number): string | null {
  const s = v == null ? "" : String(v).trim();
  return s ? s.slice(0, max) : null;
}

// Devolve exatamente 1 criança quando a ligação é inequívoca; várias quando é ambígua (vão para
// o pendente como candidatas); nenhuma quando não há pista.
function resolver(criancas: Crianca[], apelidos: Apelido[], alvo: string | null, citada: string | null): Crianca[] {
  const a = norm(alvo);
  if (a) {
    const exato = criancas.filter((c) => norm(nomeCompleto(c)) === a);
    if (exato.length === 1) return exato;
  }
  const citado = norm(citada).replace(/\(.*$/, "").replace(/\s+(com|e)\s+.*$/, "").trim();
  let ambiguas: Crianca[] = [];
  for (const t of [a, citado].filter(Boolean)) {
    const primeiro = t.split(" ")[0];
    const regras = [
      () => criancas.filter((c) => norm(c.nome).split(" ")[0] === primeiro),
      () => {
        const ids = new Set(apelidos.filter((x) => norm(x.apelido) === primeiro || norm(x.apelido) === t).map((x) => x.aluno_id));
        return criancas.filter((c) => ids.has(c.id));
      },
      () => (primeiro.length >= 3 ? criancas.filter((c) => norm(c.nome).split(" ")[0].startsWith(primeiro)) : []),
    ];
    for (const r of regras) {
      const cand = r();
      if (cand.length === 1) return cand;
      if (cand.length > 1 && !ambiguas.length) ambiguas = cand;
    }
  }
  return ambiguas;
}

function montarSistema(codebook: unknown, lista: string[]): string {
  return (
    "Você pontua observações de crianças numa escola Montessori usando o CODEBOOK abaixo (JSON). Regras:\n" +
    "- Pontue só o que o texto descreve; nunca invente. Só há transcrição de áudio ou nota escrita, sem vídeo: " +
    `confianca no máximo ${CONF_MAX_SEM_VIDEO}.\n` +
    "- Se o texto não descreve uma criança em atividade (teste de microfone, conversa entre adultos sobre método, " +
    "instrução técnica, vazio), responda avaliavel=false com um motivo curto e as notas em null.\n" +
    "- Se descreve mais de uma criança, a criança-alvo é a que o texto mais descreve.\n" +
    "- crianca_alvo: nome EXATO da lista fechada abaixo (nome e sobrenome como na lista), apenas quando a menção " +
    "for inequívoca (primeiro nome que só existe uma vez na lista conta). Apelidos e diminutivos contam " +
    "(Max é Maximiliano, Bia é Beatriz) quando só uma criança da lista combina; os apelidos já conhecidos " +
    "aparecem na lista. Na dúvida, null. crianca_citada: como apareceu no texto.\n" +
    "- Persistência só recebe nota se houve dificuldade, erro ou interrupção; senão persistencia=null e " +
    "persistencia_motivo='sem_oportunidade'.\n" +
    "- justificativa: até 30 palavras, citando o observável.\n\n" +
    `CRIANÇAS (lista fechada):\n${lista.join("\n")}\n\n` +
    `CODEBOOK (JSON):\n${JSON.stringify(codebook, null, 1)}`
  );
}

async function atender(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const db = createClient(URL_SUPA, SERVICE);

  // Falhar fechado: sem chave em mãos, recusa (mesmo padrão de indexa-observacao).
  const { data: chave, error: erroChave } = await db.rpc("_segredo", { p_nome: "observacao_key" });
  if (erroChave) throw new Error(`nao li a chave: ${erroChave.message}`);
  if (!chave || url.searchParams.get("key") !== chave) {
    return new Response("nao autorizado", { status: 401 });
  }
  if (!ANTHROPIC) {
    return new Response(JSON.stringify({ erro: "ANTHROPIC_API_KEY ausente nos secrets" }), { status: 500 });
  }
  const limite = Math.max(1, Math.min(20, Number(url.searchParams.get("limite") ?? 5) || 5));
  const seco = url.searchParams.get("seco") === "1"; // só lista a fila, não chama a IA nem grava

  const { data: cb, error: erroCb } = await db.from("obs_codebook")
    .select("versao, dimensoes").is("vigente_ate", null)
    .order("vigente_de", { ascending: false }).limit(1).maybeSingle();
  if (erroCb) throw new Error(`codebook: ${erroCb.message}`);
  if (!cb) return Response.json({ erro: "nenhum codebook vigente em obs_codebook" }, { status: 500 });
  const VERSAO = cb.versao as string;

  const { data: fila, error: erroFila } = await db.rpc("_janelas_para_pontuar", {
    p_limite: limite, p_modelo: MODELO, p_versao: VERSAO, p_min: MIN_CHARS,
  });
  if (erroFila) throw new Error(`fila: ${erroFila.message}`);
  const janelas = (fila ?? []) as Janela[];

  const resultado = {
    modelo: MODELO, codebook: VERSAO, estruturado: true as boolean | null,
    pontuadas: 0, pendentes: 0, nao_avaliaveis: 0, falhas: 0, restantes: 0,
    tokens: { entrada: 0, saida: 0, cache_escrita: 0, cache_leitura: 0 },
    janelas: [] as Array<Record<string, unknown>>,
  };

  if (seco) {
    resultado.estruturado = null;
    resultado.janelas = janelas.map((j) => ({ janela_id: j.janela_id, sala: j.sala, inicio: j.inicio, tipo: j.tipo, texto: j.texto.slice(0, 80) }));
  } else if (janelas.length) {
    const { data: criancas, error: erroAl } = await db.from("alunos")
      .select("id, nome, sobrenome, agrupada").eq("status", "ativo");
    if (erroAl) throw new Error(`alunos: ${erroAl.message}`);
    const { data: apelidosBrutos, error: erroAp } = await db.from("aluno_apelidos").select("aluno_id, apelido");
    if (erroAp) console.warn("aluno_apelidos:", erroAp.message);
    const apelidos = (apelidosBrutos ?? []) as Apelido[];
    const apelidosPor = new Map<string, string[]>();
    for (const x of apelidos) apelidosPor.set(x.aluno_id, [...(apelidosPor.get(x.aluno_id) ?? []), x.apelido]);
    const lista = (criancas as Crianca[]).map((c) =>
      `${nomeCompleto(c)} (agrupada ${c.agrupada ?? "?"}${apelidosPor.has(c.id) ? "; apelido: " + apelidosPor.get(c.id)!.join(", ") : ""})`
    );
    const sistema = montarSistema(cb.dimensoes, lista);

    for (const j of janelas) {
      const usuario =
        `Sala: ${j.sala || "(nao informada)"}\nQuem observou: ${j.especialista || "(nao informado)"}\n` +
        `Tipo da entrada: ${j.tipo}\nInício da janela: ${j.inicio}\n\n` +
        `TRANSCRIÇÃO/NOTA DA OBSERVADORA:\n${j.texto.slice(0, 8000)}`;
      const r = await chamarIA(sistema, usuario);
      if (r.uso) {
        resultado.tokens.entrada += r.uso.input_tokens ?? 0;
        resultado.tokens.saida += r.uso.output_tokens ?? 0;
        resultado.tokens.cache_escrita += r.uso.cache_creation_input_tokens ?? 0;
        resultado.tokens.cache_leitura += r.uso.cache_read_input_tokens ?? 0;
      }
      if (r.estruturado === false) resultado.estruturado = false;
      const em = new Date().toISOString();

      if (!r.saida) {
        resultado.falhas++;
        await db.from("dev_janelas").update({
          pontuacao_pendente: { modelo: MODELO + "#falha", codebook: VERSAO, erro: r.erro ?? "?", em },
        }).eq("id", j.janela_id);
        resultado.janelas.push({ janela_id: j.janela_id, resultado: "falha", erro: r.erro });
        continue;
      }
      const s = r.saida;
      if (!s.avaliavel) {
        resultado.nao_avaliaveis++;
        await db.from("dev_janelas").update({
          pontuacao_pendente: { modelo: MODELO, codebook: VERSAO, avaliavel: false, motivo: texto(s.motivo_nao_avaliavel, 200), em },
        }).eq("id", j.janela_id);
        resultado.janelas.push({ janela_id: j.janela_id, resultado: "nao_avaliavel", motivo: texto(s.motivo_nao_avaliavel, 120) });
        continue;
      }

      const linha = {
        envolvimento: nota(s.envolvimento),
        autonomia: nota(s.autonomia),
        persistencia: nota(s.persistencia),
        persistencia_motivo: texto(s.persistencia_motivo, 80),
        contexto: CONTEXTOS.includes(String(s.contexto)) ? String(s.contexto) : null,
        material: texto(s.material, 120),
        adulto_proximo: typeof s.adulto_proximo === "boolean" ? s.adulto_proximo : null,
        confianca: Math.min(nota(s.confianca) ?? 1, CONF_MAX_SEM_VIDEO),
        justificativa: texto(s.justificativa, 400) ?? "",
      };

      // Liga a criança (nome exato → primeiro nome → apelido → prefixo); ambíguo fica pendente.
      const cand = resolver(criancas as Crianca[], apelidos, s.crianca_alvo, s.crianca_citada);

      if (cand.length === 1) {
        const { error: erroGrava } = await db.from("obs_avaliacoes").insert({
          ...linha, projeto: j.projeto, janela_id: j.janela_id, entrada_id: j.entrada_id, aluno_id: cand[0].id,
          avaliador: MODELO, avaliador_tipo: "modelo", modelo: MODELO, codebook_versao: VERSAO,
        });
        if (erroGrava) {
          resultado.falhas++;
          resultado.janelas.push({ janela_id: j.janela_id, resultado: "falha", erro: erroGrava.message });
          continue;
        }
        await db.from("dev_janelas").update({ aluno_id: cand[0].id, presente: true }).eq("id", j.janela_id).is("aluno_id", null);
        await db.from("dev_janelas").update({ presente: true }).eq("id", j.janela_id);
        resultado.pontuadas++;
        resultado.janelas.push({
          janela_id: j.janela_id, resultado: "pontuada", crianca: nomeCompleto(cand[0]),
          envolvimento: linha.envolvimento, autonomia: linha.autonomia, persistencia: linha.persistencia, confianca: linha.confianca,
        });
      } else {
        resultado.pendentes++;
        await db.from("dev_janelas").update({
          pontuacao_pendente: {
            ...linha, modelo: MODELO, codebook: VERSAO, avaliavel: true,
            crianca_citada: texto(s.crianca_citada, 80), crianca_alvo: texto(s.crianca_alvo, 80),
            candidatas: cand.map((c) => c.id), em,
          },
        }).eq("id", j.janela_id);
        resultado.janelas.push({ janela_id: j.janela_id, resultado: "pendente", crianca_citada: s.crianca_citada, candidatas: cand.length });
      }
    }
  }

  const { data: rest } = await db.rpc("_janelas_pendentes_pontuacao", { p_modelo: MODELO, p_versao: VERSAO, p_min: MIN_CHARS });
  resultado.restantes = Number(rest ?? 0);
  return Response.json(resultado);
}

type Uso = { input_tokens?: number; output_tokens?: number; cache_creation_input_tokens?: number; cache_read_input_tokens?: number };

async function chamarIA(sistema: string, usuario: string): Promise<{ saida?: Saida; erro?: string; uso?: Uso; estruturado?: boolean }> {
  const base = {
    model: MODELO,
    max_tokens: 1024,
    system: [{ type: "text", text: sistema, cache_control: { type: "ephemeral" } }],
    messages: [{ role: "user", content: usuario }],
  };
  // 1ª tentativa: saída estruturada (JSON garantido) com esforço baixo — custo dominado pela saída.
  let estruturado = true;
  let resp = await postar({ ...base, output_config: { format: { type: "json_schema", schema: SAIDA_SCHEMA }, effort: "low" } });
  if (resp.status === 400) {
    console.warn("sem saida estruturada:", (await resp.text()).slice(0, 200));
    estruturado = false;
    resp = await postar({
      ...base,
      temperature: 0,
      system: [{ ...base.system[0], text: sistema + "\n\nResponda apenas o JSON com as chaves: " + Object.keys(SAIDA_SCHEMA.properties).join(", ") + ". Sem cerca de código." }],
    });
  }
  if (!resp.ok) {
    const t = (await resp.text()).slice(0, 300);
    console.error("anthropic:", resp.status, t);
    return { erro: `http ${resp.status}: ${t}`, estruturado };
  }
  const dados = await resp.json();
  const uso: Uso = dados?.usage ?? {};
  if (dados?.stop_reason === "refusal") return { erro: "refusal", uso, estruturado };
  const textoResp: string = (dados?.content ?? []).filter((b: { type: string }) => b.type === "text").map((b: { text: string }) => b.text).join("");
  try {
    const limpo = textoResp.replace(/^```(?:json)?\s*/i, "").replace(/\s*```\s*$/, "");
    return { saida: JSON.parse(limpo) as Saida, uso, estruturado };
  } catch {
    console.error("resposta nao-JSON:", textoResp.slice(0, 200));
    return { erro: "resposta nao-JSON", uso, estruturado };
  }
}

function postar(body: unknown): Promise<Response> {
  return fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": ANTHROPIC, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify(body),
  });
}
