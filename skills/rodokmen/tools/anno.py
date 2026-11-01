#!/usr/bin/env python3
"""ANNO (Rakouská národní knihovna) – fulltext v novinách 1700–1950. Jen REST API, bez prohlížeče.
Volitelně ANNO_TITLE=<zkratka listu> omezí hledání na jeden list.
Usage: anno.py "TEXT QUERY" [yearFrom] [yearTo] [maxpages] [--snip]
API: GET https://anno.onb.ac.at/anno-suche/rest/search/complex?text=..&dateFrom=YYYY&dateTo=YYYY&from=1&facets=true
     GET https://anno.onb.ac.at/anno-suche/rest/search/snippet?documentId=<docId>&query=<textQuery>
"""
import html, os, re, sys, json, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
B='https://anno.onb.ac.at/anno-suche/rest/search/'
def get(path, params):
    u=B+path+'?'+urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'genealogy-research'}),timeout=90) as r:
        return json.load(r)
args=[a for a in sys.argv[1:] if a!='--snip']; snip='--snip' in sys.argv
q=args[0]; yf=args[1] if len(args)>1 else ''; yt=args[2] if len(args)>2 else ''
maxp=int(args[3]) if len(args)>3 else 1
for p in range(maxp):
    prm={'text':q,'from':1+p*10,'facets':'false'}
    if yf: prm['dateFrom']=yf
    if yt: prm['dateTo']=yt
    if os.environ.get('ANNO_TITLE'): prm['title']=os.environ['ANNO_TITLE']
    d=get('complex',prm)
    if p==0: print('TOTAL',d.get('totalHits'),'|',d.get('textQuery'))
    for doc in d.get('documents',[]):
        print('-',doc['docId'],'|',doc['displayTitle'],'| hits',doc.get('totalHitsInDoc'),'|',doc['openUrl'])
        if snip:
            try:
                s=get('snippet',{'documentId':doc['docId'],'query':d.get('textQuery',q)})
                for sp in s.get('snippetPages',[])[:3]:
                    for sn in sp.get('snippets',[])[:2]:
                        t=html.unescape(re.sub(r'<[^>]+>',' ',sn['text']))
                        print('   p.%s: %s'%(sp['pageLabel'],re.sub(r'\s+',' ',t)[:400]))
            except Exception as e: print('   snip err',e)
            time.sleep(0.5)
    if d.get('lastHit',0)>=d.get('totalHits',0): break
    time.sleep(1)
