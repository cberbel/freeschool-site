# Pipeline — quem Montessori cita

Gera os dados de `../dados/` a partir do texto integral das obras de Montessori
em domínio público. Nada aqui é escrito à mão exceto `curadoria.py`.

## Reproduzir

```sh
./baixar-corpus.sh      # clona os 5 livros do GITenberg em ~/corpus (≈50 MB)
python3 extrair.py      # texto → candidatos.json    (nomes candidatos + contagem)
python3 formais.py      # texto → formais.json       (aparato de referência: AUTOR, «obra»)
python3 sinais.py       # opcional: fila-curadoria.txt, ordena os candidatos por
                        # sinal de citação, para orientar a revisão manual
python3 montar.py       # candidatos + formais + curadoria → ../dados/montessori.json
```

`CORPUS=/outro/caminho` muda onde os textos ficam.

## As cinco obras lidas

| id | obra | Gutenberg | palavras |
|---|---|---|---|
| `metodo-1912` | The Montessori Method (do italiano de 1909) | 39863 | 118.681 |
| `antropologia-1913` | Pedagogical Anthropology (do italiano de 1910) | 46643 | 194.774 |
| `handbook-1914` | Dr. Montessori's Own Handbook (original em inglês) | 29635 | 25.304 |
| `autoeducacao-1917` | Spontaneous Activity in Education (do italiano de 1916) | 24727 | 105.480 |
| `material-1917` | The Montessori Elementary Material (do italiano de 1916) | 42869 | 108.199 |

## O que cada arquivo faz

- **`extrair.py`** — corta o cabeçalho do Gutenberg, junta as quebras de linha de
  composição e procura sequências capitalizadas. Descarta o que a própria obra usa
  em minúscula com frequência, para que uma palavra comum em começo de frase não
  vire nome próprio. Não decide quem é pessoa.
- **`formais.py`** — segunda passada, atrás do aparato de referência: nome em caixa
  alta seguido do título em itálico (`MORSELLI, _Cesare Lombroso..._`). É a camada
  mais forte de evidência, e a primeira passada não a enxerga.
- **`sinais.py`** — pontua cada candidato por sinais de citação no contexto (título
  antes do nome, possessivo seguido de "method"/"law", "according to", referência
  bibliográfica). Só ordena a fila da revisão; não classifica.
- **`curadoria.py`** — a parte humana. Mapeia cada token para uma pessoa, com anos,
  país, campo e **grau de certeza**. Também registra, em `EXCLUIDOS`, o que foi
  descartado e por quê — para que a exclusão seja auditável e não um silêncio.
- **`montar.py`** — junta tudo e escreve `../dados/montessori.json`, incluindo a
  prestação de contas do que ainda não foi revisado.

## A distinção que sustenta a página

A **citação** é um fato: o nome está na página, tantas vezes, nesta obra. Sai do
extrator e pode ser conferida no texto.

A **identificação** é um juízo: quem é essa pessoa. Sai da curadoria e vem com grau
de certeza — `alta`, `media` ou `sobrenome`. Quando só o sobrenome é legível, a
citação continua valendo e a identificação fica em aberto.

## O que falta

`montar.py` imprime quantos candidatos ainda não foram revisados. Hoje são 2.192,
dos quais 317 com três ou mais ocorrências. A maioria é ruído — topônimos, rubricas
do livro, termos de craniometria — mas há pessoas ali dentro. O número de citados
tende a subir.

E falta a Montessori tardia: as cinco obras lidas vão até 1917, e os livros de 1936
em diante ainda têm direitos.
