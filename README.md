# Free School — Grupo Educacional

Site institucional da **Free School**, a empresa "guarda-chuva" (o cérebro) do grupo de
escolas que inclui a Escola Montessoriana de Laranjeiras e o Montessori Open Class.

Filosofia: **educação auto-dirigida** — a criança no comando da própria educação.

## Stack

Site **estático** (HTML + CSS puro, sem build). Deploy na Vercel como projeto estático.

```
index.html      → página única (PT-BR)
styles.css      → estilos (mobile-first, paleta do logo)
favicon.svg     → ícone (os três quadrados do logo)
robots.txt / sitemap.xml
assets/         → logo
```

Paleta do logo: vermelho `#FF0000` · amarelo `#FFED00` · azul `#003BE3` · preto/branco.

## Como editar

Edite `index.html` / `styles.css` e faça `git push origin main`. A Vercel publica automaticamente
(quando o repositório estiver conectado ao projeto). Não há passo de build.

## Domínio

`www.freeschool.com.br` (apontar DNS para a Vercel).
