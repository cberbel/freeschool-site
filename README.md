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
docs/           → documentos de projeto (não publicados no site)
bancada/        → ferramenta de captura e análise da Fase 0 (não publicada)
```

## Documentos

- [`docs/pesquisa-desenvolvimento-infantil.md`](docs/pesquisa-desenvolvimento-infantil.md) —
  arquitetura e stack de IA para mensuração longitudinal do desenvolvimento infantil na sala
  Montessori (visão computacional, áudio/linguagem, sono), com comentários críticos e ordem
  de execução. Rascunho, não implementado.
- [`docs/dicionario-variaveis.md`](docs/dicionario-variaveis.md) — dicionário de ~135 variáveis
  do mesmo projeto, com definição operacional, fonte, validação e camada de promoção.
- [`bancada/`](bancada/README.md) — ferramenta da Fase 0: captura agendada das câmeras Reolink,
  QA, sincronização, proxies e primeira análise (detecção, tracking, pose, mãos). Python + ffmpeg.

`docs/` e `bancada/` não são publicados no site (`.vercelignore`).

O logo do cabeçalho/rodapé é montado em HTML/CSS (três quadrados + "free school"),
então escala perfeitamente e não depende de imagem.

Paleta do logo: vermelho `#FF0000` · amarelo `#FFED00` · azul `#003BE3` · preto/branco.

## Como editar

Edite `index.html` / `styles.css` e faça `git push origin main`. Com o repositório
conectado ao projeto na Vercel, a publicação é automática. Não há passo de build.

## Domínio

`www.freeschool.com.br` (apontar DNS para a Vercel).
