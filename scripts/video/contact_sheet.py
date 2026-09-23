#!/usr/bin/env python3
"""Export evenly spaced video frames as a review contact sheet."""
from __future__ import annotations
import argparse
from pathlib import Path
import cv2
from PIL import Image, ImageDraw, ImageFont

ap=argparse.ArgumentParser();ap.add_argument('video',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--frames',type=int,default=12);args=ap.parse_args()
tiles=[];font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18)
if args.video.is_dir():
    for path in sorted(args.video.glob('*.jpg')):
        im=Image.open(path).convert('RGB').resize((480,270),Image.Resampling.LANCZOS);d=ImageDraw.Draw(im);d.rectangle((0,0,135,30),fill=(20,48,77));d.text((8,6),path.stem,font=font,fill='white');tiles.append(im)
else:
    cap=cv2.VideoCapture(str(args.video));count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));fps=cap.get(cv2.CAP_PROP_FPS) or 30
    for i in range(args.frames):
        pos=round((count-1)*i/max(1,args.frames-1));cap.set(cv2.CAP_PROP_POS_FRAMES,pos);ok,frame=cap.read()
        if not ok: continue
        frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);im=Image.fromarray(frame).resize((480,270),Image.Resampling.LANCZOS)
        d=ImageDraw.Draw(im);d.rectangle((0,0,110,30),fill=(20,48,77));d.text((8,6),f'{pos/fps:05.2f}s',font=font,fill='white');tiles.append(im)
    cap.release()
cols=3;rows=(len(tiles)+cols-1)//cols;sheet=Image.new('RGB',(cols*480,rows*270),'#e8e3d8')
for i,im in enumerate(tiles):sheet.paste(im,((i%cols)*480,(i//cols)*270))
args.output.parent.mkdir(parents=True,exist_ok=True);sheet.save(args.output,quality=92);print(args.output)
