# Free School — Educação auto-dirigida

Site institucional da **Free School**, comunidade de educação auto-dirigida.
Filosofia: a pessoa que aprende no comando do próprio aprendizado.

## Stack

Site **estático** (HTML + CSS puro, sem build). Deploy na Vercel como projeto estático.

```
index.html      → página única (PT-BR)
styles.css      → estilos (mobile-first, paleta do logo)
favicon.svg     → ícone (os três quadrados do logo)
robots.txt / sitemap.xml
assets/         → logo (og:image)

montessori-freire/  → levantamento das citações de Montessori e Freire
  index.html        · a página (abas: obras, citados, comparação, método)
  dados/*.json      · os dados que a página lê
  pipeline/         · como os dados são gerados a partir do texto integral
```

## Montessori × Freire

`/montessori-freire/` compara os dois pela **lista de quem cada um cita**. O lado de
Montessori é medido no texto integral de cinco obras em domínio público (552 mil
palavras); o lado de Freire ainda é uma lista de trabalho, porque nenhuma obra dele
está em domínio público. A página declara essa assimetria em vez de escondê-la.
Para regenerar os dados, veja `montessori-freire/pipeline/README.md`.

O logo do cabeçalho/rodapé é montado em HTML/CSS (três quadrados + "free school"),
então escala perfeitamente e não depende de imagem.

Paleta do logo: vermelho `#FF0000` · amarelo `#FFED00` · azul `#003BE3` · preto/branco.

## Como editar

Edite `index.html` / `styles.css` e faça `git push origin main`. Com o repositório
conectado ao projeto na Vercel, a publicação é automática. Não há passo de build.

## Domínio

`www.freeschool.com.br` (apontar DNS para a Vercel).
