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
```

O logo do cabeçalho/rodapé é montado em HTML/CSS (três quadrados + "free school"),
então escala perfeitamente e não depende de imagem.

Paleta do logo: vermelho `#FF0000` · amarelo `#FFED00` · azul `#003BE3` · preto/branco.

## Como editar

Edite `index.html` / `styles.css` e faça `git push origin main`. Com o repositório
conectado ao projeto na Vercel, a publicação é automática. Não há passo de build.

## Domínio

`www.freeschool.com.br` (apontar DNS para a Vercel).
