#!/bin/bash
# matricula_dl.sh URL OUT  -- stáhne obrázek z img.data.matricula-online.eu (URL s csrf+ctrl z prohlížeče)
if [ "$1" = -h ] || [ "$1" = --help ] || [ $# -lt 2 ]; then sed -n '2,2p' "$0" | sed 's/^# \{0,1\}//'; exit 2; fi   # nápověda
PY=python3; $PY -c "" 2>/dev/null || PY=python; $PY -c "" 2>/dev/null || PY="py -3"
curl() { $PY -I "$(dirname "$0")/slusne.py" curl "$@"; }   # brzda proti zablokování archivem
tok=$(echo "$1" | sed -E 's/.*csrf=([^&]+).*/\1/')
# -f: při chybě (403 = prošlý odkaz) nic neuložit; pak ověřit, že je to opravdu JPEG, ne chybová stránka
if ! curl -sf -A "Mozilla/5.0" -e "https://data.matricula-online.eu/" -b "shared_csrftoken=$tok" "$1" -o "$2" \
   || [ "$(head -c 3 "$2" 2>/dev/null | od -An -tx1 | tr -d ' \n')" != "ffd8ff" ]; then
  rm -f "$2"
  echo "Matricula snímek odmítla nebo nevrátila obrázek (prošlý odkaz?) – vytáhni nové adresy z prohlížeče: $2" >&2
  exit 1
fi
file "$2" | cut -d, -f1,8
