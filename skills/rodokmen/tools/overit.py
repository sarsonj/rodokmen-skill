#!/usr/bin/env python3
# Ověření čtení (např. po pomocníkovi): výřez zápisu rozdělený na dvě poloviny 1900 px. Použití: overit.py <snímek.jpg> x0,y0,x1,y1 <prefix> [v]  (v = dělit vodorovně)
import glob,os,shutil,sys,subprocess
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")
def magick():  # když ImageMagick chybí, skončí hned (před stahováním) srozumitelnou hláškou
    m=shutil.which("magick") or next(iter(sorted(glob.glob(r"C:\Program Files\ImageMagick*\magick.exe"))),None) or (os.name!="nt" and shutil.which("convert"))  # IM6 bez magick; na Windows je convert.exe jiný program
    if not m: sys.exit("Chybí ImageMagick (příkaz magick). Nainstaluj ho (macOS: brew install imagemagick, Windows: winget install ImageMagick.ImageMagick a restart Claude Code / Codexu / OMP) a spusť nástroj znovu.")
    return m
MAGICK=magick()
f,box,pre=sys.argv[1:4]; mode=sys.argv[4] if len(sys.argv)>4 else 'h'
W,H=map(int,subprocess.run([MAGICK,f+'[0]','-format','%w %h','info:'],capture_output=True,text=True).stdout.split())
x0,y0,x1,y1=map(float,box.split(','))
if not (0<=x0<x1<=1 and 0<=y0<y1<=1): sys.exit(f'Oblast {box} musí být zlomky 0..1 (x0 < x1, y0 < y1), ne pixely.')
if mode=='v': ym=(y0+y1)/2; parts=[(x0,y0,x1,ym+0.02),(x0,ym-0.02,x1,y1)]
else: xm=(x0+x1)/2; parts=[(x0,y0,xm+0.02,y1),(xm-0.02,y0,x1,y1)]
for i,(a,b,c,d) in enumerate(parts):
    o=f'{pre}_{i}.jpg'; subprocess.run([MAGICK,f,'-crop','%dx%d+%d+%d'%((c-a)*W,(d-b)*H,a*W,b*H),'+repage','-resize','1900x',o]); print(o)
