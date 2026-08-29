/* ============================================================
   Montessori × Freire — levantamento de citações
   Sem build, sem dependência. Lê os JSON de ./dados/ e monta a página.
   ============================================================ */
(function () {
  "use strict";

  var CAMPOS = {
    medicina: "Medicina", antropologia: "Antropologia", biologia: "Biologia",
    psicologia: "Psicologia", pedagogia: "Pedagogia", filosofia: "Filosofia",
    politica: "Política", literatura: "Literatura", arte: "Arte e música",
    ciencia: "Ciências exatas", estatistica: "Estatística", historia: "História",
    religiao: "Religião", outros: "Outros"
  };

  var num = function (n) { return n.toLocaleString("pt-BR"); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var el = function (sel) { return document.querySelector(sel); };
  var normal = function (s) {
    return String(s).normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .toLowerCase().replace(/[^a-z ]/g, "").trim();
  };
  var sobrenome = function (nome) {
    var p = normal(nome).split(" ").filter(function (x) {
      return x.length > 2 && ["de", "del", "van", "von", "da", "dos", "das"].indexOf(x) < 0;
    });
    return p.length ? p[p.length - 1] : normal(nome);
  };

  var DADOS = {};

  /* ---------------- abas ---------------- */
  function abas() {
    var botoes = Array.prototype.slice.call(document.querySelectorAll(".mf-tabs button"));
    botoes.forEach(function (b) {
      b.addEventListener("click", function () {
        var alvo = b.dataset.painel;
        botoes.forEach(function (o) { o.setAttribute("aria-selected", String(o === b)); });
        document.querySelectorAll(".mf-painel").forEach(function (p) {
          p.hidden = p.dataset.painel !== alvo;
        });
        var topo = el(".mf-tabs-wrap");
        if (topo && window.scrollY > topo.offsetTop) {
          window.scrollTo({ top: topo.offsetTop - 60, behavior: "smooth" });
        }
        if (history.replaceState) history.replaceState(null, "", "#" + alvo);
      });
    });
    var inicial = (location.hash || "").replace("#", "");
    var achou = botoes.filter(function (b) { return b.dataset.painel === inicial; })[0];
    if (achou) achou.click();
  }

  /* ---------------- estado do corpus ---------------- */
  function estado() {
    var m = DADOS.montessori, f = DADOS.freire, obras = DADOS.obras;
    var palavras = m.corpus.reduce(function (a, o) { return a + o.palavras; }, 0);
    var pc = m.prestacao_de_contas;

    el("#stats-montessori").innerHTML = [
      ["<b>" + m.corpus.length + "</b> de " + obras.montessori.obras.length, "obras lidas por inteiro"],
      ["<b>" + num(palavras) + "</b>", "palavras processadas"],
      ["<b>" + num(m.pessoas.length) + "</b>", "pessoas citadas identificadas"],
      ["<b>" + num(m.pessoas.reduce(function (a, p) { return a + p.total; }, 0)) + "</b>", "menções contadas"],
      ["<b>" + pc.com_referencia_formal + "</b>", "com referência formal (autor + obra)"]
    ].map(function (x) { return "<li>" + x[0] + "<span>" + x[1] + "</span></li>"; }).join("");

    el("#stats-freire").innerHTML = [
      ["<b>0</b> de " + obras.freire.obras.length, "obras lidas por inteiro"],
      ["<b>0</b>", "palavras processadas"],
      ["<b>" + f.pessoas.length + "</b>", "nomes na lista de trabalho"],
      ["<b>—</b>", "menções contadas"],
      ["<b>—</b>", "com referência formal"]
    ].map(function (x) { return "<li>" + x[0] + "<span>" + x[1] + "</span></li>"; }).join("");

    el("#m-palavras").textContent = num(palavras);
    el("#m-tokens").textContent = num(pc.tokens_extraidos);
    el("#m-pendentes").textContent = num(pc.tokens_pendentes);
    el("#m-pendentes3").textContent = num(pc.pendentes_com_3_ou_mais);
  }

  /* ---------------- obras ---------------- */
  function bibliografia(chave, destino) {
    var d = DADOS.obras[chave];
    var linhas = d.obras.map(function (o) {
      var meta = [];
      if (o.coautor) meta.push("com " + esc(o.coautor));
      if (o.tipo === "dialogo") meta.push("livro dialogado");
      if (o.tipo === "postumo") meta.push("póstumo");
      if (o.tipo === "tese") meta.push("tese");
      if (o.tipo === "conferencias" || o.tipo === "conferencia") meta.push("conferências");
      if (o.nota) meta.push(esc(o.nota));
      if (o.edicao_lida) meta.push("lido em: " + esc(o.edicao_lida));
      return '<div class="mf-obra' + (o.corpus ? " mf-obra--corpus" : "") + '">' +
        '<div class="mf-ano">' + o.ano + "</div>" +
        '<div class="mf-tit">' + esc(o.titulo) +
        (o.corpus ? ' <span class="mf-tag-corpus">no corpus</span>' : "") +
        (meta.length ? '<span class="mf-meta">' + meta.join(" · ") + "</span>" : "") +
        "</div></div>";
    }).join("");

    el(destino).innerHTML =
      "<h3>" + esc(d.autor) + "</h3>" +
      '<p class="mf-vida">' + esc(d.vida) + " · " + d.obras.length + " títulos</p>" +
      '<p class="mf-bibnota">' + esc(d.nota_bibliografica) + "</p>" + linhas;
  }

  /* ---------------- lista de Montessori ---------------- */
  function cartaoMontessori(p, rotulos) {
    var badges = ['<span class="mf-badge mf-badge--campo">' + (CAMPOS[p.campo] || p.campo) + "</span>"];
    if (p.pais) badges.push('<span class="mf-badge mf-badge--pais">' + esc(p.pais) + "</span>");
    if (p.referencias && p.referencias.length) {
      badges.push('<span class="mf-badge mf-badge--formal">referência formal</span>');
    }
    if (p.certeza === "sobrenome") {
      badges.push('<span class="mf-badge mf-badge--sobrenome">só o sobrenome</span>');
    } else if (p.certeza === "media") {
      badges.push('<span class="mf-badge mf-badge--media">identificação provável</span>');
    }

    var porObra = Object.keys(p.obras).map(function (k) {
      return "<span>" + esc((rotulos[k] || k).replace(/ \(.*\)$/, "")) + " <b>" + p.obras[k] + "</b></span>";
    }).join("");

    var refs = "";
    if (p.referencias && p.referencias.length) {
      var vistos = {};
      refs = '<div class="mf-refs">' + p.referencias.filter(function (r) {
        if (vistos[r.obra_citada]) return false;
        vistos[r.obra_citada] = 1; return true;
      }).map(function (r) {
        return "<p>" + esc(r.como) + ", <em>" + esc(r.obra_citada) + "</em></p>";
      }).join("") + "</div>";
    }

    return '<article class="mf-pessoa">' +
      '<div class="mf-pessoa-nome">' + esc(p.nome) +
      (p.vida ? '<span class="mf-vida-inline">' + esc(p.vida) + "</span>" : "") + "</div>" +
      '<div class="mf-contagem-total">' + p.total + "<small>menções</small></div>" +
      '<div class="mf-pessoa-linha2">' + badges.join("") + "</div>" +
      (p.nota ? '<p class="mf-pessoa-nota">' + esc(p.nota) + "</p>" : "") +
      '<div class="mf-porobra">' + porObra + "</div>" + refs +
      "</article>";
  }

  function listaMontessori() {
    var m = DADOS.montessori;
    var busca = el("#f-busca"), campo = el("#f-campo"), obra = el("#f-obra"),
        formal = el("#f-formal"), ordem = el("#f-ordem");

    var campos = {};
    m.pessoas.forEach(function (p) { campos[p.campo] = (campos[p.campo] || 0) + 1; });
    campo.innerHTML = '<option value="">Todos os campos</option>' +
      Object.keys(campos).sort(function (a, b) { return campos[b] - campos[a]; })
        .map(function (c) {
          return '<option value="' + c + '">' + (CAMPOS[c] || c) + " (" + campos[c] + ")</option>";
        }).join("");

    obra.innerHTML = '<option value="">Todas as obras</option>' +
      m.corpus.map(function (o) {
        return '<option value="' + o.id + '">' + esc(o.rotulo) + "</option>";
      }).join("");

    el("#montessori-resumo").innerHTML =
      "Todas as pessoas nomeadas nas cinco obras lidas — de Séguin, que ela declara como mestre, " +
      "a poetas citados só uma vez num exercício de métrica. São <strong>" + m.pessoas.length +
      "</strong> pessoas e <strong>" + num(m.pessoas.reduce(function (a, p) { return a + p.total; }, 0)) +
      "</strong> menções. O número de menções mede presença no texto, não concordância: " +
      "boa parte das citações a Lombroso é para discordar dele.";

    function desenha() {
      var q = normal(busca.value);
      var itens = m.pessoas.filter(function (p) {
        if (campo.value && p.campo !== campo.value) return false;
        if (obra.value && !p.obras[obra.value]) return false;
        if (formal.checked && !(p.referencias && p.referencias.length)) return false;
        if (q && normal(p.nome + " " + (CAMPOS[p.campo] || "") + " " + p.nota).indexOf(q) < 0) return false;
        return true;
      });

      if (ordem.value === "nome") {
        itens.sort(function (a, b) { return a.nome.localeCompare(b.nome, "pt-BR"); });
      } else if (ordem.value === "campo") {
        itens.sort(function (a, b) {
          return (CAMPOS[a.campo] || a.campo).localeCompare(CAMPOS[b.campo] || b.campo, "pt-BR")
            || b.total - a.total;
        });
      } else {
        itens.sort(function (a, b) { return b.total - a.total || a.nome.localeCompare(b.nome, "pt-BR"); });
      }

      var total = itens.reduce(function (a, p) { return a + p.total; }, 0);
      el("#montessori-contagem").textContent =
        itens.length + (itens.length === 1 ? " pessoa" : " pessoas") +
        " · " + num(total) + (total === 1 ? " menção" : " menções");

      el("#lista-montessori").innerHTML = itens.length
        ? itens.map(function (p) { return cartaoMontessori(p, m.rotulos); }).join("")
        : '<p class="mf-vazio">Nenhuma pessoa com esses filtros.</p>';
    }

    [busca, campo, obra, formal, ordem].forEach(function (c) {
      c.addEventListener("input", desenha);
      c.addEventListener("change", desenha);
    });
    desenha();

    el("#montessori-excluidos").innerHTML =
      "<ul>" + Object.keys(m.excluidos).map(function (k) {
        return "<li><b>" + esc(k) + "</b> — " + esc(m.excluidos[k]) + "</li>";
      }).join("") + "</ul>" +
      '<p style="margin-top:12px;font-size:.91rem;color:var(--ink-soft)">' +
      "Nomes que o extrator devolveu e que não são citação: revisores da digitalização, " +
      "créditos de foto, topônimos, personagens de exercício. Ficam listados para que a " +
      "exclusão seja auditável, e não um silêncio.</p>";
  }

  /* ---------------- lista de Freire ---------------- */
  function listaFreire() {
    var f = DADOS.freire;
    el("#freire-aviso").innerHTML = "<strong>Lista de trabalho, não medição.</strong> " + esc(f.aviso);
    el("#freire-contagem").textContent =
      f.pessoas.length + " nomes · nenhuma contagem, porque nenhum texto foi lido";

    el("#lista-freire").innerHTML = f.pessoas.map(function (p) {
      var badges = ['<span class="mf-badge mf-badge--campo">' + (CAMPOS[p.campo] || p.campo) + "</span>"];
      if (p.pais) badges.push('<span class="mf-badge mf-badge--pais">' + esc(p.pais) + "</span>");
      badges.push('<span class="mf-badge' + (p.certeza === "media" ? " mf-badge--media" : "") + '">' +
        (p.certeza === "alta" ? "referência bem documentada" : "a confirmar") + "</span>");
      return '<article class="mf-pessoa">' +
        '<div class="mf-pessoa-nome">' + esc(p.nome) +
        (p.vida ? '<span class="mf-vida-inline">' + esc(p.vida) + "</span>" : "") + "</div>" +
        '<div class="mf-contagem-total" style="font-size:.8rem;font-family:var(--font-body);font-weight:400;color:var(--ink-soft)">' +
        esc(p.onde) + "</div>" +
        '<div class="mf-pessoa-linha2">' + badges.join("") + "</div>" +
        (p.nota ? '<p class="mf-pessoa-nota">' + esc(p.nota) + "</p>" : "") +
        "</article>";
    }).join("");
  }

  /* ---------------- comparação ---------------- */
  function comparacao() {
    var m = DADOS.montessori.pessoas, f = DADOS.freire.pessoas;

    var mapaM = {}, mapaMS = {};
    m.forEach(function (p) { mapaM[normal(p.nome)] = p; mapaMS[sobrenome(p.nome)] = p; });
    var comuns = [];
    f.forEach(function (p) {
      var a = mapaM[normal(p.nome)] || mapaMS[sobrenome(p.nome)];
      if (a) comuns.push({ m: a, f: p });
    });

    el("#comp-interseccao").innerHTML =
      '<div class="mf-numero">' + comuns.length + "</div>" +
      "<p><strong>pessoas aparecem nas duas listas.</strong> " +
      (comuns.length === 0
        ? "Nenhuma. Dois autores que recusam a escola transmissiva e não têm um único nome em comum " +
          "na fundamentação. Montessori se apoia em médicos, antropólogos e biólogos do século XIX; " +
          "Freire, em filósofos e pensadores políticos do século XX. É resultado preliminar em dois " +
          "sentidos: o lado de Freire ainda não foi medido, e a lista de Montessori ainda vai crescer " +
          "com a revisão dos candidatos pendentes."
        : "São elas: " + comuns.map(function (c) { return esc(c.f.nome); }).join(", ") + ".") +
      "</p>" +
      (comuns.length ? '<div class="mf-nomes">' + comuns.map(function (c) {
        return "<span>" + esc(c.f.nome) + "</span>";
      }).join("") + "</div>" : "");

    var cM = {}, cF = {};
    m.forEach(function (p) { cM[p.campo] = (cM[p.campo] || 0) + 1; });
    f.forEach(function (p) { cF[p.campo] = (cF[p.campo] || 0) + 1; });
    var todos = Object.keys(CAMPOS).filter(function (c) { return cM[c] || cF[c]; });
    // as listas tem tamanhos muito diferentes (223 x 42), entao a barra mostra a
    // PARTICIPACAO de cada campo na propria lista, e as duas usam a mesma escala.
    var parteM = function (c) { return m.length ? (cM[c] || 0) / m.length : 0; };
    var parteF = function (c) { return f.length ? (cF[c] || 0) / f.length : 0; };
    var teto = Math.max.apply(null, todos.map(function (c) {
      return Math.max(parteM(c), parteF(c));
    })) || 1;
    var pct = function (x) { return Math.round(x * 100); };

    el("#comp-campos").innerHTML =
      '<div class="mf-legenda"><span class="m"><i></i>Montessori (' + m.length + " pessoas)</span>" +
      '<span class="f"><i></i>Freire (' + f.length + " nomes, provisório)</span></div>" +
      todos.sort(function (a, b) { return parteM(b) + parteF(b) - parteM(a) - parteF(a); })
        .map(function (c) {
          var vm = cM[c] || 0, vf = cF[c] || 0;
          return '<div class="mf-campo-linha">' +
            '<div class="mf-campo-nome">' + CAMPOS[c] + "</div>" +
            '<div class="mf-barras">' +
            '<div class="mf-barra"><i style="width:' + (parteM(c) / teto) * 100 + '%"></i><span>' +
              vm + " · " + pct(parteM(c)) + "%</span></div>" +
            '<div class="mf-barra mf-barra--f"><i style="width:' + (parteF(c) / teto) * 100 + '%"></i><span>' +
              vf + " · " + pct(parteF(c)) + "%</span></div>" +
            "</div></div>";
        }).join("");

    var leituras = [
      ["Ela cita um laboratório; ele cita uma biblioteca de combate.",
       "Em Montessori, os três campos maiores são medicina, antropologia e biologia — " +
       "a autoridade vem da bancada, do instrumento de medir, do caso clínico. Na lista provisória " +
       "de Freire, os maiores são filosofia e política. A pergunta não é a mesma: uma quer saber " +
       "como a criança se desenvolve; o outro, quem manda em quem."],
      ["A literatura pesa mais em Montessori do que se imagina.",
       "Depois da medicina, o segundo maior campo dela é literatura — Dante, Manzoni, Shakespeare, " +
       "Tennyson. Boa parte vem de um lugar específico: o volume sobre o material didático, onde " +
       "poemas viram exercício de métrica e gramática. Citação de uso, não de fundamentação."],
      ["Quase ninguém vivo, quase ninguém do próprio país.",
       "As referências de Montessori são majoritariamente europeias e do século XIX. O corpus lido " +
       "devolve uma única referência brasileira, o pediatra Figueira, do Rio de Janeiro, citado " +
       "de passagem numa nota. Freire, ao contrário, cita brasileiros e africanos vivos, " +
       "e vários deles são seus interlocutores diretos."],
      ["O que falta para a comparação ficar de pé.",
       "Os textos de Freire. Enquanto eles não passarem pelo mesmo extrator, comparar as duas colunas " +
       "é comparar uma medição com uma lembrança. E falta também a Montessori tardia — de 1936 em " +
       "diante, quando ela abandona o vocabulário da antropometria e passa a escrever sobre paz."]
    ];
    el("#comp-leituras").innerHTML = leituras.map(function (l) {
      return '<div class="mf-leitura"><h4>' + l[0] + "</h4><p>" + l[1] + "</p></div>";
    }).join("");
  }

  /* ---------------- início ---------------- */
  function erro(e) {
    var alvo = el("#lista-montessori") || document.body;
    alvo.innerHTML = '<p class="mf-vazio">Não consegui carregar os dados (' + esc(e.message) +
      "). Esta página lê arquivos JSON e precisa ser servida por HTTP — abrir o arquivo direto do " +
      "disco não funciona.</p>";
  }

  Promise.all(["dados/montessori.json", "dados/freire.json", "dados/obras.json"].map(function (u) {
    return fetch(u).then(function (r) {
      if (!r.ok) throw new Error(u + " → " + r.status);
      return r.json();
    });
  })).then(function (r) {
    DADOS.montessori = r[0]; DADOS.freire = r[1]; DADOS.obras = r[2];
    estado();
    bibliografia("montessori", "#obras-montessori");
    bibliografia("freire", "#obras-freire");
    listaMontessori();
    listaFreire();
    comparacao();
    abas();
    var y = el("#year"); if (y) y.textContent = new Date().getFullYear();
  }).catch(erro);
})();
