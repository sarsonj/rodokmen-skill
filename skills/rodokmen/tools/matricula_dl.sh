#!/bin/bash
# matricula_dl.sh URL OUT  -- stáhne obrázek z img.data.matricula-online.eu (URL s csrf+ctrl z prohlížeče)
PY=python3; $PY -c "" 2>/dev/null || PY=python; $PY -c "" 2>/dev/null || PY="py -3"
curl() { $PY -I "$(dirname "$0")/slusne.py" curl "$@"; }   # brzda proti zablokování archivem
tok=$(echo "$1" | sed -E 's/.*csrf=([^&]+).*/\1/')
curl -s -A "Mozilla/5.0" -e "https://data.matricula-online.eu/" -b "shared_csrftoken=$tok" "$1" -o "$2"; file "$2" | cut -d, -f1,8
