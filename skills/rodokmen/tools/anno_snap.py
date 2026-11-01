#!/usr/bin/env python3
"""Download page image (or enlarged region around hit) from ANNO via snippet API hash.
Usage: anno_snap.py DOCID "QUERY" OUTFILE [page] [mode=full|ctx] [width]
mode ctx = hit area expanded (+/-600px vertically, whole column width)"""
import sys,json,re,urllib.request,urllib.parse
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
doc,q,out=sys.argv[1:4]; page=sys.argv[4] if len(sys.argv)>4 else None
mode=sys.argv[5] if len(sys.argv)>5 else 'ctx'; w=sys.argv[6] if len(sys.argv)>6 else '1400'
u='https://anno.onb.ac.at/anno-suche/rest/search/snippet?'+urllib.parse.urlencode({'documentId':doc,'query':q})
d=json.load(urllib.request.urlopen(u,timeout=90))
for sp in d['snippetPages']:
    if page and str(sp['page'])!=page and sp['pageLabel']!=page: continue
    s=sp['snippets'][0]; url=s['imageURL']
    m=re.search(r'iiif=(/[^/]+/[^/]+)/(\d+),(\d+),(\d+),(\d+)/',url)
    base,x,y,ww,hh=m.group(1),*map(int,m.groups()[1:])
    W,H=s['imageWidth'],s['imageHeight']
    if mode=='full': reg='full'
    else:
        y0=max(0,y-700); h=min(H-y0,hh+1400); x0=max(0,x-150); wd=min(W-x0,ww+300)
        reg=f'{x0},{y0},{wd},{h}'
    url2=url.split('&iiif=')[0]+f'&iiif={base}/{reg}/{w},/0/default.jpg'
    open(out,'wb').write(urllib.request.urlopen(url2,timeout=120).read())
    print('saved',out,'page',sp['page'],sp['openURL']); break
