#!/bin/bash
# matricula_batch.sh URLFILE PREFIX  (URLFILE: řádky "<snímek> <url obrázku>" vytažené z prohlížeče) -> stáhne PREFIX_<pg>.jpg (+ _s.jpg zmenšeninu 1900px)
if [ "$1" = -h ] || [ "$1" = --help ] || [ $# -lt 2 ]; then sed -n '2,2p' "$0" | sed 's/^# \{0,1\}//'; exit 2; fi   # nápověda
M=magick   # ImageMagick 6 nemá magick, jen convert (na Windows je convert.exe jiný program, tam ne)
command -v magick >/dev/null || { [ "$OS" != Windows_NT ] && command -v convert >/dev/null && M=convert; }
tr -d '"' < "$1" | sed 's/\\n/\n/g' | grep -E '^[0-9]+ https' | while read p u; do
  out="${2}_$p.jpg"
  [ -s "$out" ] || bash "$(dirname "$0")/matricula_dl.sh" "$u" "$out" || { echo "Dávku končím u snímku $p." >&2; exit 1; }
  "$M" "$out" -resize 1900x "${2}_${p}_s.jpg"; done
