#!/usr/bin/env bash
# Baixa o corpus de Montessori em domínio público (Project Gutenberg, espelho GITenberg).
# Os textos NÃO ficam no repositório: são grandes e já têm casa própria.
set -euo pipefail

DESTINO="${CORPUS:-$HOME/corpus}"
mkdir -p "$DESTINO"

REPOS=(
  "The-Montessori-MethodAuthor_39863"                              # O Método (1912)
  "Pedagogical-Anthropology_46643"                                 # Antropologia Pedagógica (1913)
  "Dr.-Montessori-s-Own-Handbook_29635"                            # Own Handbook (1914)
  "Spontaneous-Activity-in-Education_24727"                        # A autoeducação (1917)
  "Montessori-Elementary-MaterialsThe-Advanced-Montessori-Method_42869"  # O material (1917)
)

for r in "${REPOS[@]}"; do
  # o repo do Handbook tem ponto no nome; a pasta local fica sem
  pasta="${r//./}"
  [ "$r" = "Dr.-Montessori-s-Own-Handbook_29635" ] && pasta="Dr-Montessori-Own-Handbook_29635"
  if [ -d "$DESTINO/$pasta/.git" ]; then
    echo "já existe: $pasta"
    continue
  fi
  echo "baixando $r"
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 \
    "https://github.com/GITenberg/$r" "$DESTINO/$pasta"
done

echo
echo "corpus em $DESTINO"
du -sh "$DESTINO"
