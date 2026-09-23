#!/usr/bin/env python3
"""Render the ShipMind 60s collage promo or a compressed 12s visual preview.

The renderer uses generated art only as a decorative plate. Product evidence comes
from DGX Spark browser captures under runs/ui-review.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
W, H = 1920, 1080
CREAM = "#f5f1e6"
NAVY = "#14304d"
BLUE = "#0071e3"
RED = "#ff3b30"
GREEN = "#248a3d"
INK = "#1d1d1f"


def font(size: int, mono: bool = False, bold: bool = False):
    choices = ([Path("C:/Windows/Fonts/consolab.ttf"), Path("C:/Windows/Fonts/consola.ttf")]
               if mono else [Path("C:/Windows/Fonts/msyhbd.ttc" if bold else "msyh.ttc"),
                              Path("C:/Windows/Fonts/arialbd.ttf" if bold else "arial.ttf")])
    for path in choices:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F_TITLE = font(66, bold=True)
F_HERO = font(104, bold=True)
F_BODY = font(30)
F_MONO = font(23, mono=True)
F_SMALL = font(18, mono=True)
F_CAPTION = font(27, bold=True)
LETTER_FONTS = [
    font(70, bold=True),
    ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 74) if Path("C:/Windows/Fonts/impact.ttf").exists() else font(70, bold=True),
    ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 68) if Path("C:/Windows/Fonts/georgiab.ttf").exists() else font(68, bold=True),
    font(66, mono=True, bold=True),
]
LETTER_FONTS_HERO = [
    ImageFont.truetype("C:/Windows/Fonts/impact.ttf", 108) if Path("C:/Windows/Fonts/impact.ttf").exists() else font(104, bold=True),
    ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 101),
    ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 96) if Path("C:/Windows/Fonts/georgiab.ttf").exists() else font(100, bold=True),
]
LETTER_PAPERS = ("#fff8e7", "#ffd34e", "#ff725e", "#71c9ce", "#b8d8ff", "#f2b5d4", "#d8e698")


def cover(image: Image.Image, size=(W, H)) -> Image.Image:
    scale = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    x = (resized.width - size[0]) // 2
    y = (resized.height - size[1]) // 2
    return resized.crop((x, y, x + size[0], y + size[1]))


def contain(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
    scale = min(max_size[0] / image.width, max_size[1] / image.height)
    return image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)


def ease_out_back(x: float) -> float:
    x = max(0.0, min(1.0, x)); c = 1.42
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def paper_card(size: tuple[int, int], fill="#fffdf8", radius=18) -> Image.Image:
    card = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=fill, outline=(20, 48, 77, 25), width=2)
    return card


def paste_shadow(base: Image.Image, item: Image.Image, xy: tuple[int, int], angle=0.0, alpha=255):
    item = item.copy(); item.putalpha(ImageEnhance.Brightness(item.getchannel("A")).enhance(alpha / 255))
    if angle:
        item = item.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    shadow = Image.new("RGBA", item.size, (0, 0, 0, 0))
    shadow.putalpha(item.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda p: p * .22))
    base.alpha_composite(shadow, (xy[0] + 13, xy[1] + 17))
    base.alpha_composite(item, xy)


def tape(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color=(203, 215, 193, 160)):
    draw.rounded_rectangle(box, 4, fill=color)


def stamp(base: Image.Image, text: str, xy: tuple[int, int], color=RED, angle=-4, size=32):
    f = font(size, mono=True, bold=True)
    box = f.getbbox(text); w, h = box[2] - box[0] + 34, box[3] - box[1] + 26
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle((2, 2, w - 3, h - 3), 7, outline=color, width=4)
    d.text((17, 10 - box[1]), text, font=f, fill=color)
    layer = layer.rotate(angle, Image.Resampling.BICUBIC, expand=True)
    base.alpha_composite(layer, xy)


def ragged_mask(size: tuple[int, int], t: float, seed: int) -> Image.Image:
    """A slowly breathing torn-paper edge, deterministic for each fragment."""
    w, h = size; step = max(28, min(w, h) // 9); amp = 8
    wave = lambda q, side: amp * math.sin(q * .021 + t * .85 + seed * 1.7 + side)
    points = []
    for x in range(8, w - 7, step): points.append((x, round(8 + wave(x, 0))))
    for y in range(8, h - 7, step): points.append((round(w - 8 + wave(y, 1.4)), y))
    for x in range(w - 8, 7, -step): points.append((x, round(h - 8 + wave(x, 2.8))))
    for y in range(h - 8, 7, -step): points.append((round(8 + wave(y, 4.2)), y))
    mask = Image.new("L", size, 0); ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(.7))


def fragment(base: Image.Image, source: Image.Image, source_box: tuple[int, int, int, int],
             dest: tuple[int, int, int, int], angle: float, t: float, seed: int,
             entrance: float, direction: tuple[int, int]):
    w, h = dest[2], dest[3]
    piece = cover(source.crop(source_box), (w, h)).convert("RGBA")
    piece.putalpha(ragged_mask((w, h), t, seed))
    # A moving crease and alternating highlight/shadow sell the folded-paper surface.
    fold_x = round(w * (.48 + .16 * math.sin(t * .38 + seed)))
    fold = Image.new("RGBA", (w, h), (0, 0, 0, 0)); fd = ImageDraw.Draw(fold)
    fd.polygon(((fold_x - 18, 0), (fold_x + 2, 0), (fold_x + 30, h), (fold_x + 8, h)), fill=(255, 255, 255, 38))
    fd.line((fold_x + 3, 0, fold_x + 12, h), fill=(20, 48, 77, 32), width=3)
    piece = Image.alpha_composite(piece, fold)
    p = ease_out_back(max(0, min(1, entrance)))
    x = round(dest[0] + (1 - p) * direction[0] + 4 * math.sin(t * .24 + seed))
    y = round(dest[1] + (1 - p) * direction[1] + 3 * math.sin(t * .31 + seed * .7))
    paste_shadow(base, piece, (x, y), angle=angle + 1.1 * math.sin(t * .18 + seed))


def animated_background(t: float, source: Image.Image) -> Image.Image:
    starts = (0, 6, 17, 28, 44, 54)
    scene = max(i for i, start in enumerate(starts) if t >= start)
    local = t - starts[scene]
    # A quiet chart-paper base remains, while fragments are re-cut and rearranged per scene.
    paper = cover(source.crop((520, 40, 1710, 1010)), (W, H))
    paper = ImageEnhance.Brightness(paper).enhance(1.08).convert("RGBA")
    sources = {
        "ocean": (0, 0, 585, 900), "map": (500, 0, 1690, 960),
        "bottom": (0, 690, 1920, 1080), "blue": (450, 0, 930, 260),
        "right": (1580, 0, 1920, 820), "moon": (0, 0, 560, 430),
    }
    layouts = [
        [("ocean", (-80, -55, 680, 1130), -2, (-760, 30)), ("map", (460, -40, 1190, 930), 1, (80, -820)), ("bottom", (400, 810, 1570, 330), -1, (0, 430)), ("blue", (420, -45, 500, 250), 3, (0, -330))],
        [("map", (-80, -20, 1340, 1030), -1, (-260, -620)), ("ocean", (1210, -80, 770, 1160), 2, (790, 20)), ("bottom", (330, 820, 1220, 300), 1, (0, 380)), ("right", (1500, -30, 450, 710), -3, (480, -120))],
        [("moon", (-70, -35, 790, 640), -3, (-770, -250)), ("map", (570, -60, 1390, 1120), 1, (1100, -120)), ("bottom", (-30, 720, 1540, 410), 2, (-100, 430)), ("blue", (1410, 50, 530, 300), -2, (500, -260))],
        [("map", (-30, -35, 1170, 1130), -1, (-900, 0)), ("ocean", (1040, -70, 960, 1160), 2, (950, 0)), ("bottom", (330, 845, 1320, 300), -2, (0, 360)), ("right", (1550, 20, 420, 780), 3, (450, -80))],
        [("ocean", (-60, 520, 1110, 620), 2, (-780, 500)), ("map", (170, -80, 1510, 1060), -1, (0, -850)), ("blue", (-40, -30, 650, 310), 3, (-520, -250)), ("right", (1560, 290, 420, 760), -3, (500, 120))],
        [("map", (-70, -30, 1480, 1130), 1, (-400, -700)), ("ocean", (1310, -70, 690, 1160), -2, (710, 0)), ("bottom", (160, 820, 1450, 320), 2, (0, 390)), ("blue", (40, -55, 570, 280), -3, (-550, -240))],
    ]
    for i, (key, dest, angle, direction) in enumerate(layouts[scene]):
        fragment(paper, source, sources[key], dest, angle, t, scene * 7 + i,
                 local / 1.15 - i * .11, direction)
    return paper


def torn_text(text: str, text_font, fill="#fffdf8", ink=INK, pad=(24, 14), seed=1) -> Image.Image:
    box = text_font.getbbox(text); w = box[2] - box[0] + pad[0] * 2; h = box[3] - box[1] + pad[1] * 2
    piece = Image.new("RGBA", (w, h), fill); d = ImageDraw.Draw(piece)
    d.text((pad[0], pad[1] - box[1]), text, font=text_font, fill=ink)
    piece.putalpha(ragged_mask(piece.size, seed * .37, seed))
    return piece


def title_block(base: Image.Image, title: str, line: str, x=120, y=105, hero=False):
    """Make every headline character its own colourful, legible paper cutout."""
    fonts=LETTER_FONTS_HERO if hero else LETTER_FONTS; cursor_y=y; seed=17
    for row, raw in enumerate(title.split("\n")):
        # Measure first, then tighten uniformly so long titles stay inside the title safe zone.
        widths=[]
        for i,ch in enumerate(raw):
            f=fonts[(seed+i)%len(fonts)]; widths.append(30 if ch==" " else max(35,round(f.getlength(ch))+22))
        fit=min(1.0,1540/max(1,sum(widths))); cursor_x=x
        for i,ch in enumerate(raw):
            if ch==" ": cursor_x+=round(28*fit); continue
            seed+=1; f=fonts[seed%len(fonts)]; box=f.getbbox(ch); w=max(38,box[2]-box[0]+22); h=(118 if hero else 82)
            tile=Image.new("RGBA",(w,h),LETTER_PAPERS[seed%len(LETTER_PAPERS)]); td=ImageDraw.Draw(tile)
            # Small print marks add handmade variety without competing with the glyph.
            if seed%3==0:
                for yy in range(8,h,13): td.line((5,yy,w-5,yy),fill=(20,48,77,24),width=2)
            elif seed%3==1:
                for xx in range(8,w,15): td.ellipse((xx,8,xx+3,11),fill=(20,48,77,45))
            td.text(((w-(box[2]-box[0]))/2-box[0],(h-(box[3]-box[1]))/2-box[1]-2),ch,font=f,fill=INK)
            tile.putalpha(ragged_mask(tile.size,seed*.27,seed));
            if fit<.999: tile=tile.resize((round(tile.width*fit),round(tile.height*fit)),Image.Resampling.LANCZOS)
            paste_shadow(base,tile,(cursor_x,cursor_y+((seed%3)-1)*4),angle=(-3,-1,1,2.5)[seed%4])
            cursor_x+=tile.width+3
        cursor_y += (126 if hero else 91)
    sub=torn_text(line,F_BODY,"#fffdf8",NAVY,(24,14),seed+8)
    paste_shadow(base,sub,(x+12,cursor_y+14),angle=-1.2)


def voiceover_caption(base: Image.Image, text: str, seed: int):
    words=text.split(); lines=[]; current=""
    for word in words:
        trial=(current+" "+word).strip()
        if F_CAPTION.getlength(trial)>1450 and current: lines.append(current); current=word
        else: current=trial
    if current: lines.append(current)
    h=42*len(lines)+34; card=Image.new("RGBA",(1580,h),"#fffdf8"); d=ImageDraw.Draw(card)
    for i,line in enumerate(lines): d.text((36,17+i*42),line,font=F_CAPTION,fill=NAVY)
    card.putalpha(ragged_mask(card.size,seed*.41,seed)); paste_shadow(base,card,(170,930-h//2),angle=-.35)


def punch_zoom(frame: Image.Image, p: float, strength=.16) -> Image.Image:
    """Fast overscale and damped shake; the framing returns to rest in under a second."""
    p=max(0,min(1,p)); kick=(1-p)**2; scale=1+strength*kick
    w,h=round(W*scale),round(H*scale); enlarged=frame.resize((w,h),Image.Resampling.BICUBIC)
    shake=round(15*kick*math.sin(p*34)); x=(w-W)//2+shake; y=(h-H)//2-round(8*kick*math.cos(p*29))
    return enlarged.crop((x,y,x+W,y+H))


def transition_fx(frame: Image.Image, t: float, desktop: Image.Image, product: Image.Image, radar_art: Image.Image, sonar_art: Image.Image) -> Image.Image:
    """Five narrative transitions, each contained to the first 0.8s of a new scene."""
    starts=(6,17,28,44,54); idx=next((i for i,s in enumerate(starts) if 0<=t-s<.9),None)
    if idx is None:return frame
    local=t-starts[idx];p=max(0,min(1,local/.82));out=punch_zoom(frame,ease_out_back(p),(.21,.16,.13,.1,.19)[idx])
    layer=Image.new("RGBA",(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    if idx==0:  # v6 tear, softened with the reference video's cream-card flash
        retreat=ease_out_back(p); gap=round(80+980*retreat); jag=[]
        for y in range(-30,H+60,48):jag.append((W//2+round(18*math.sin(y*.071)),y))
        left=[(-80,-80),(W//2-gap//2,-80)]+[(x-gap//2,y) for x,y in reversed(jag)]+[(-80,H+80)]
        right=[(W+80,-80),(W//2+gap//2,-80)]+[(x+gap//2,y) for x,y in jag]+[(W+80,H+80)]
        d.polygon(left,fill=(20,48,77,round(250*(1-p))));d.polygon(right,fill=(245,241,230,round(250*(1-p))))
        d.line([(x-gap//2,y) for x,y in jag],fill=(255,114,94,round(230*(1-p))),width=12)
        d.line([(x+gap//2,y) for x,y in jag],fill=(255,211,78,round(230*(1-p))),width=9)
    elif idx==1:  # Spark recedes into a tactile evidence-card stack
        if p<.14:d.rectangle((0,0,W,H),fill=(255,248,231,round(170*(1-p/.14))))
        device=contain(product.convert("RGBA"),(1030,720));scale=max(.24,1-.69*ease_out_back(p));device=device.resize((round(device.width*scale),round(device.height*scale)),Image.Resampling.LANCZOS)
        device.putalpha(ImageEnhance.Brightness(device.getchannel('A')).enhance(max(0,1-p*.9)));x=round(70+(960-70)*p);y=round(260+(520-260)*p)
        if p>.45:device=device.filter(ImageFilter.GaussianBlur((p-.45)*5))
        paste_shadow(out,device,(x,y),angle=-8*p)
        for i,color in enumerate(("#fff8e7","#b8d8ff","#ffd34e")):
            card=paper_card((420,250),fill=color,radius=5);card.putalpha(ragged_mask(card.size,t,410+i));q=max(0,min(1,(p-.16-i*.06)/.7));xx=round(760+i*22+(q*470));yy=round(500-i*18-q*150)
            card.putalpha(round(220*(1-q)));paste_shadow(out,card,(xx,yy),angle=-7+i*7+q*12)
        alpha=round(150*(1-p));cx,cy=960,560
        for k,color in enumerate(((113,201,206),(255,211,78),(255,114,94))):
            r=round(90+p*750-k*100)
            if r>0:d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(*color,alpha),width=8)
    elif idx==2:  # Evidence cards gather into a stack; the fixed AI page is revealed behind them
        if p<.12:d.rectangle((0,0,W,H),fill=(255,248,231,round(150*(1-p/.12))))
        cards=(contain(sonar_art.convert('RGBA'),(620,320)),contain(radar_art.convert('RGBA'),(320,250)),artifact_piece('gauge','SEE','4.7 bar · 98%',(360,220)))
        starts_xy=((160,590),(1050,610),(1450,350));target=(250,560)
        for i,(card,(sx,sy)) in enumerate(zip(cards,starts_xy)):
            q=ease_out_back(max(0,min(1,p*1.15-i*.05)));scale=1-.58*q;card=card.resize((round(card.width*scale),round(card.height*scale)),Image.Resampling.LANCZOS)
            if p>.55:card=card.filter(ImageFilter.GaussianBlur((p-.55)*5))
            card.putalpha(round(255*(1-p*.82)));paste_shadow(out,card,(round(sx+(target[0]+i*16-sx)*q),round(sy+(target[1]-i*13-sy)*q)),angle=(-4+i*5)+q*(8-i*3))
    elif idx==3:  # One live-capture card becomes the six-card platform arrangement
        if p<.13:d.rectangle((0,0,W,H),fill=(255,248,231,round(165*(1-p/.13))))
        crop_h=min(desktop.height,round(desktop.width*.72));shot=contain(desktop.crop((0,0,desktop.width,crop_h)).convert('RGBA'),(1050,650))
        targets=((280,540),(800,540),(1320,540),(280,715),(800,715),(1320,715))
        for i,(tx,ty) in enumerate(targets):
            q=ease_out_back(max(0,min(1,p*1.22-i*.055)));thumb=shot.resize((round(shot.width*(1-.76*q)),round(shot.height*(1-.76*q))),Image.Resampling.LANCZOS)
            if q>.5:thumb=thumb.filter(ImageFilter.GaussianBlur((q-.5)*4));thumb.putalpha(round(230*(1-q)))
            sx,sy=110+i*9,270-i*6;paste_shadow(out,thumb,(round(sx+(tx-sx)*q),round(sy+(ty-sy)*q)),angle=(-8+i*3)*(1-q))
    else:  # Six product cards float out over a cream flash, leaving the final statement
        if p<.18:d.rectangle((0,0,W,H),fill=(255,248,231,round(210*(1-p/.18))))
        names=("DGX SPARK","AGENT SKILLS","DEEPSTREAM","STEPFUN","QWEN","VLLM")
        starts_xy=((280,540),(800,540),(1320,540),(280,715),(800,715),(1320,715))
        dirs=((-700,-420),(0,-650),(680,-430),(-720,420),(0,620),(700,430))
        for i,(name,(sx,sy),(dx,dy)) in enumerate(zip(names,starts_xy,dirs)):
            card=torn_text(name,F_MONO,LETTER_PAPERS[i%len(LETTER_PAPERS)],NAVY,(22,14),700+i);q=ease_out_back(max(0,min(1,p*1.12-i*.025)))
            card.putalpha(round(255*(1-p)));paste_shadow(out,card,(round(sx+dx*q),round(sy+dy*q)),angle=(-7+i*3)+q*(i-3)*8)
    return Image.alpha_composite(out,layer)


def background_energy(base: Image.Image, t: float, scene: int) -> Image.Image:
    """Decorative motion below every subject; framing and readable content stay fixed."""
    layer=Image.new("RGBA",(W,H),(0,0,0,0));d=ImageDraw.Draw(layer)
    if scene==0:
        # A moving chart route and wake marks live behind the entering ship.
        pts=[]
        for i in range(8):
            x=780+i*150;y=700+round(55*math.sin(t*.8+i*.72));pts.append((x,y))
        d.line(pts,fill=(0,113,227,70),width=8)
        for x,y in pts[1::2]:d.ellipse((x-9,y-9,x+9,y+9),fill=(255,114,94,100))
    elif scene==1:
        # Colourful print rays make Spark feel important without moving the product.
        cx,cy=555,585;spin=t*.08
        for i in range(24):
            a=spin+i*math.pi/12;r1=250;r2=760+80*math.sin(t*.7+i)
            col=((255,211,78,34),(113,201,206,32),(255,114,94,28))[i%3]
            d.polygon(((cx+r1*math.cos(a-.025),cy+r1*math.sin(a-.025)),(cx+r2*math.cos(a),cy+r2*math.sin(a)),(cx+r1*math.cos(a+.025),cy+r1*math.sin(a+.025))),fill=col)
    elif scene==2:
        cx,cy=960,630
        for i in range(7):
            r=90+((t*135+i*150)%1040);alpha=round(60*(1-r/1200))
            d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(113,201,206,max(8,alpha)),width=5)
        for a in range(0,360,30):
            rr=math.radians(a+t*3);d.line((cx,cy,cx+900*math.cos(rr),cy+900*math.sin(rr)),fill=(20,48,77,25),width=2)
    elif scene==3:
        # A quiet scan lattice moves behind the fixed live-capture card.
        off=round((t*34)%120)
        for x in range(-120+off,W,120):d.line((x,240,x+360,H),fill=(0,113,227,20),width=3)
        for y in range(260,H,80):d.line((540,y,W,y),fill=(20,48,77,16),width=2)
    elif scene==4:
        # Platform wiring stays below the six paper product labels.
        hubs=((520,606),(1040,606),(1560,606),(520,780),(1040,780),(1560,780))
        for i,(x,y) in enumerate(hubs):
            d.line((960,500,x,y),fill=((0,113,227,60) if i<3 else (255,59,48,50)),width=5)
            pulse=9+6*math.sin(t*2.2+i);d.ellipse((x-pulse,y-pulse,x+pulse,y+pulse),fill=(255,211,78,100))
    else:
        cx,cy=930,360
        for i in range(30):
            a=i*math.pi/15+t*.025;r1=270;r2=980
            d.line((cx+r1*math.cos(a),cy+r1*math.sin(a),cx+r2*math.cos(a),cy+r2*math.sin(a)),fill=((255,211,78,32) if i%2 else (255,114,94,24)),width=7)
    # Confetti is constrained to the outer frame, never over titles, cards or subtitles.
    rng=np.random.default_rng(scene*1000+int(t*4));colors=LETTER_PAPERS
    for i in range(12):
        side=i%2;x=int(rng.integers(8,62) if side==0 else rng.integers(W-62,W-8));y=int(rng.integers(110,900));w=int(rng.integers(8,26))
        d.rectangle((x,y,x+w,y+round(w*.38)),fill=colors[(i+scene)%len(colors)])
    return Image.alpha_composite(base,layer)


def focus_camera(frame: Image.Image, scale: float, center: tuple[int,int]) -> Image.Image:
    """Crop around a chosen subject to create actual editorial shot changes."""
    if scale<=1.001:return frame
    w,h=round(W*scale),round(H*scale);large=frame.resize((w,h),Image.Resampling.BICUBIC)
    x=round(center[0]*scale-W/2);y=round(center[1]*scale-H/2)
    x=max(0,min(w-W,x));y=max(0,min(h-H,y));return large.crop((x,y,x+W,y+H))


def kinetic_edit(frame: Image.Image, t: float) -> Image.Image:
    """A 60-second shot list: hard reframes and short pushes every 2–3 seconds."""
    shots=(
      (2.0,4.15,1.18,1.31,(1320,470)),(4.15,6.0,1.05,1.12,(1190,570)),
      (7.0,9.8,1.02,1.10,(1310,530)),(9.8,12.15,1.42,1.62,(1470,520)),
      (12.15,14.4,1.18,1.29,(450,650)),(14.4,17.0,1.03,1.10,(1110,540)),
      (18.0,20.9,1.28,1.43,(500,690)),(20.9,23.2,1.31,1.46,(1610,480)),
      (23.2,25.5,1.34,1.50,(1190,750)),(25.5,28.0,1.08,1.16,(1260,610)),
      (29.0,31.6,1.03,1.10,(1240,540)),(31.6,34.5,1.29,1.43,(1010,390)),
      (34.5,37.5,1.35,1.50,(1510,390)),(37.5,40.7,1.37,1.52,(1230,690)),
      (40.7,44.0,1.05,1.13,(1250,560)),
      (45.0,47.0,1.10,1.20,(560,620)),(47.0,49.0,1.12,1.23,(1080,620)),
      (49.0,51.0,1.13,1.24,(1580,620)),(51.0,54.0,1.03,1.11,(990,650)),
      (55.0,57.4,1.16,1.30,(900,310)),(57.4,59.2,1.04,1.12,(930,470)),
    )
    for start,end,a,b,center in shots:
        if start<=t<end:
            p=(t-start)/(end-start);return focus_camera(frame,a+(b-a)*p,center)
    return frame


def misregister(frame: Image.Image, amount: int) -> Image.Image:
    arr=np.asarray(frame.convert("RGB"));out=arr.copy()
    out[:,:,0]=np.roll(arr[:,:,0],amount,axis=1);out[:,:,2]=np.roll(arr[:,:,2],-amount,axis=0)
    return Image.fromarray(out,"RGB").convert("RGBA")


def editorial_hits(frame: Image.Image, t: float) -> Image.Image:
    """Short print flashes and paper shrapnel at internal hard cuts."""
    cuts=(2.0,4.15,6,9.8,12.15,14.4,17,20.9,23.2,25.5,28,31.6,34.5,37.5,40.7,44,47,49,51,54,57.4)
    cut=next((c for c in cuts if 0<=t-c<.42),None)
    if cut is None:return frame
    p=(t-cut)/.42;out=misregister(frame,max(1,round(13*(1-p)))) if p<.23 else frame
    layer=Image.new("RGBA",(W,H),(0,0,0,0));d=ImageDraw.Draw(layer);seed=int(cut*10)
    if p<.10:d.rectangle((0,0,W,H),fill=((255,248,231,185) if seed%2 else (255,59,48,150)))
    rng=np.random.default_rng(seed)
    for i in range(18):
        x=int(rng.integers(80,W-80)+(p**1.4)*rng.integers(-480,481));y=int(rng.integers(80,H-80)+(p**1.4)*rng.integers(-360,361))
        ww=int(rng.integers(18,70));hh=int(rng.integers(8,28));color=LETTER_PAPERS[(i+seed)%len(LETTER_PAPERS)]
        d.rectangle((x,y,x+ww,y+hh),fill=color)
    return Image.alpha_composite(out,layer)


def artifact_piece(kind: str, label: str, sub: str, size=(470, 245)) -> Image.Image:
    """A text label and its evidence object live on the same physical paper fragment."""
    w, h = size; piece = paper_card(size, fill="#fffdf8", radius=10); d = ImageDraw.Draw(piece)
    d.text((24, 20), label, font=F_MONO, fill=NAVY); d.text((24, h - 43), sub, font=F_SMALL, fill=NAVY)
    left, top, right, bottom = 26, 72, w - 25, h - 62
    if kind == "wave":
        pts=[]
        for x in range(left, right, 6):
            y=(top+bottom)/2 + 26*math.sin(x*.052) + 10*math.sin(x*.17)
            pts.append((x, y))
        d.line(pts, fill=BLUE, width=4); d.line((left, (top+bottom)/2, right, (top+bottom)/2), fill=(20,48,77,35), width=1)
        d.ellipse((right-38, top+8, right-14, top+32), fill=RED)
    elif kind == "manual":
        d.rounded_rectangle((left+55, top-8, right-65, bottom+8), 8, fill="#f5f1e6", outline=NAVY, width=3)
        for y in range(top+22, bottom-4, 22): d.line((left+82, y, right-92, y), fill=(20,48,77,80), width=2)
        d.polygon(((right-110, top-8), (right-64, top-8), (right-64, top+75), (right-87, top+58), (right-110, top+75)), fill=RED)
    elif kind == "log":
        d.rectangle((left+28, top-5, right-28, bottom+8), outline=NAVY, width=3)
        for y in range(top+24, bottom, 28): d.line((left+28,y,right-28,y), fill=(20,48,77,70), width=2)
        for x in (left+150,left+285): d.line((x,top-5,x,bottom+8), fill=(20,48,77,70), width=2)
        d.line((right-120,bottom-18,right-92,bottom+2,right-48,bottom-42), fill=RED, width=6)
    elif kind == "gauge":
        cx,cy=(left+right)//2,bottom+10; radius=88
        d.arc((cx-radius,cy-radius,cx+radius,cy+radius),180,360,fill=NAVY,width=5)
        for a in range(190,351,32):
            r=math.radians(a); d.line((cx+72*math.cos(r),cy+72*math.sin(r),cx+87*math.cos(r),cy+87*math.sin(r)),fill=NAVY,width=3)
        a=math.radians(292); d.line((cx,cy,cx+76*math.cos(a),cy+76*math.sin(a)),fill=RED,width=6); d.ellipse((cx-8,cy-8,cx+8,cy+8),fill=INK)
    elif kind == "radar":
        cx,cy=(left+right)//2,(top+bottom)//2
        for r in (34,66,98): d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(0,113,227,100),width=2)
        d.line((cx,cy,cx+88,cy-54),fill=BLUE,width=3)
        for dx,dy in ((48,-31),(-63,45)): d.ellipse((cx+dx-7,cy+dy-7,cx+dx+7,cy+dy+7),fill="#ff9500")
    elif kind == "route":
        pts=[(left+15,bottom-10),(left+90,bottom-62),(left+190,bottom-44),(left+285,top+14),(right-18,top+35)]
        d.line(pts,fill=BLUE,width=6)
        d.line([(x,y+24) for x,y in pts],fill=(255,59,48,90),width=2)
        d.ellipse((pts[-1][0]-9,pts[-1][1]-9,pts[-1][0]+9,pts[-1][1]+9),fill=RED)
    elif kind == "device":
        d.rounded_rectangle((left+40,top,right-40,bottom),18,fill="#eaf3ff",outline=BLUE,width=4)
        d.rectangle((left+82,top+35,right-82,bottom-35),outline=NAVY,width=3)
        for x in range(left+115,right-100,52): d.line((x,bottom-28,x,bottom-12),fill=NAVY,width=3)
        d.ellipse((right-125,top+55,right-101,top+79),fill=GREEN)
    elif kind == "checks":
        for i in range(7):
            x=left+28+i*52; y=(top+bottom)//2
            d.ellipse((x-13,y-13,x+13,y+13),outline=GREEN,width=3)
            d.line((x-7,y,x-1,y+7,x+10,y-9),fill=GREEN,width=3)
    elif kind == "logs":
        for i in range(4):
            y=top+10+i*28; d.text((left+20,y),("OBS","YOU","AI ","SYS")[i],font=F_SMALL,fill=(GREEN,RED,BLUE,NAVY)[i]); d.line((left+92,y+11,right-18,y+11),fill=(20,48,77,80),width=2)
        d.arc((right-82,top-5,right-18,top+59),35,320,fill=BLUE,width=4)
    elif kind == "streams":
        cx,cy=(left+right)//2,(top+bottom)//2
        for i,a in enumerate((25,115,205,295)):
            r=math.radians(a); x=cx+115*math.cos(r); y=cy+58*math.sin(r)
            d.line((cx,cy,x,y),fill=(0,113,227,100),width=3); d.ellipse((x-13,y-13,x+13,y+13),fill=(BLUE,GREEN,"#ff9500",RED)[i])
        d.ellipse((cx-18,cy-18,cx+18,cy+18),fill=NAVY)
    piece.putalpha(ragged_mask(size, 0, sum(map(ord, kind))))
    return piece


def intro_artifacts(base: Image.Image, progress: float, t: float):
    specs=(("wave","FAULTS CAUGHT BY EAR","ACOUSTIC TRACE"),("manual","MANUALS HARD TO SEARCH","LOCAL SOURCE"),("log","LOGS WRITTEN BY HAND","AUDIT TRAIL"))
    for i,(kind,label,sub) in enumerate(specs):
        p=ease_out_back(progress*1.45-i*.16)
        if p<=0: continue
        x=105+i*570; y=635+(-22 if i==1 else 0)
        paste_shadow(base,artifact_piece(kind,label,sub),(round(x+(1-p)*(i-1)*650),round(y+(1-p)*330)),angle=(-3+i*3)+math.sin(t*.3+i))


def spark_hero(base: Image.Image, product: Image.Image, progress: float, t: float):
    p=ease_out_back(progress)
    device=contain(product.convert("RGBA"),(980,750))
    x=round(70-(1-p)*1040); y=260+round(6*math.sin(t*.25))
    paste_shadow(base,device,(x,y),angle=1.2*math.sin(t*.18))
    d=ImageDraw.Draw(base); tape(d,(x+95,y-18,x+300,y+27),(203,215,193,180))
    tags=(("GB10 GRACE BLACKWELL","LOCAL AI SUPERCHIP",1250,495,BLUE),("128 GB UNIFIED MEMORY","MODEL + CONTEXT TOGETHER",1275,600,RED),("ALWAYS-ON AGENT WORKLOAD","READY BEYOND THE NETWORK",1240,705,GREEN))
    for i,(label,sub,tx,ty,color) in enumerate(tags):
        back=paper_card((565,94),fill=("#cfe4ef","#f6c7bc","#d9e8c5")[i],radius=4)
        back.putalpha(ragged_mask(back.size,t,850+i));ImageDraw.Draw(back).rectangle((0,0,18,94),fill=color)
        tag=paper_card((535,84),fill=("#fffdf8","#f3ead5","#e9eff2")[i],radius=3);td=ImageDraw.Draw(tag)
        td.rectangle((18,17,47,46),fill=color);td.text((63,12),label,font=F_MONO,fill=NAVY);td.text((63,49),sub,font=F_SMALL,fill=INK)
        td.line((18,69,505,69),fill=color,width=4);tag.putalpha(ragged_mask(tag.size,t,870+i))
        xx=round(tx-(1-p)*(650+i*95));paste_shadow(base,back,(xx-14,ty+9),angle=(-3+i*2));paste_shadow(base,tag,(xx,ty),angle=(-1.5+i*1.4))


def console_sidecar(base: Image.Image, operator: Image.Image, progress: float, t: float):
    """Fill the console's right column with the local inference path that explains the answer."""
    p=ease_out_back(progress*1.5-.18)
    if p<=0:return
    officer=contain(operator.convert("RGBA"),(590,690));x=round(1335+(1-p)*660);y=250
    paste_shadow(base,officer,(x,y),angle=1.2)
    labels=(("ASK",BLUE),("TRACE",RED),("CITE",GREEN))
    for i,(head,color) in enumerate(labels):
        q=ease_out_back(progress*1.7-.30-i*.10)
        if q<=0:continue
        card=torn_text(head,F_MONO,("#fff6d8","#dcebf1","#f3dfda")[i],NAVY,(22,14),910+i)
        cy=590+i*86;cx=round(1370+(1-q)*510)
        paste_shadow(base,card,(cx,cy),angle=(-4+i*4))


def platform_stack(base: Image.Image, progress: float, t: float):
    specs=(("NVIDIA DGX SPARK","LOCAL GB10 COMPUTE",BLUE),("NVIDIA AGENT SKILLS","6 SKILLS · DISCLOSED",BLUE),("DEEPSTREAM","PIPELINE GENERATED",GREEN),("STEPFUN 3.7 FLASH","ONLINE ENHANCEMENT","#ff9500"),("QWEN3-4B-FP8","LOCAL DUTY MODEL",RED),("VLLM","LOCAL MODEL SERVING",NAVY))
    for i,(name,sub,color) in enumerate(specs):
        p=ease_out_back(progress*1.8-i*.1)
        if p<=0: continue
        card=paper_card((490,154),fill=("#fffdf8","#eee5d1","#dce8ee")[i%3],radius=5); d=ImageDraw.Draw(card)
        d.rectangle((24,25,56,57),fill=color); d.text((72,23),name,font=F_MONO,fill=NAVY); d.text((27,86),sub,font=F_SMALL,fill=INK)
        d.line((27,126,455,126),fill=color,width=5)
        card.putalpha(ragged_mask(card.size,t,120+i)); x=100+i*570; y=610
        col=i%3; row=i//3; x=275+col*520; y=530+row*175
        paste_shadow(base,card,(round(x+(1-p)*(col-1)*720),round(y+(1-p)*330)),angle=(-2+(i%3)*2))


def evidence_cards(base: Image.Image, progress: float, radar_art: Image.Image, sonar_art: Image.Image):
    rows = [("wave","LISTEN", "High-frequency energy change"), ("gauge","SEE", "4.7 bar · 98% confidence"),
            ("radar","READ", "2 radar targets detected"), ("route","WATCH", "Route offset 17.8 m")]
    for i, (kind,name,value) in enumerate(rows):
        local = ease_out_back((progress * 1.35 - i * .12))
        if local <= 0: continue
        if kind=="radar": card=contain(radar_art.convert("RGBA"),(360,250))
        else: card=artifact_piece(kind,name,value,(400,245))
        col=i%2; row=i//2; x=round(1000+col*430+(1-local)*520); y=350+row*280
        paste_shadow(base,card,(x,y),angle=(-2+i*1.4),alpha=255)
    sonar=contain(sonar_art.convert("RGBA"),(720,360)); sp=ease_out_back(progress*1.4-.28)
    if sp>0: paste_shadow(base,sonar,(round(180-(1-sp)*760),565),angle=-2.2)


def ui_card(base: Image.Image, image: Image.Image, progress: float):
    p = ease_out_back(progress)
    # Use the evidence-rich first viewport instead of shrinking the whole tall page.
    crop_height = min(image.height, round(image.width * .72))
    shot = contain(image.crop((0, 0, image.width, crop_height)), (1260, 700))
    frame = paper_card((shot.width + 36, shot.height + 68)); frame.alpha_composite(shot.convert("RGBA"), (18, 18))
    ImageDraw.Draw(frame).text((20, shot.height + 29), "LIVE CAPTURE · DGX SPARK", font=F_SMALL, fill=NAVY)
    frame.putalpha(ragged_mask(frame.size,progress*2,301))
    x = round(110 - (1 - p) * 720); y = 270
    paste_shadow(base, frame, (x, y), angle=1.2)
    d = ImageDraw.Draw(base); tape(d, (x + 35, y - 15, x + 190, y + 27)); tape(d, (x + frame.width - 190, y + frame.height - 25, x + frame.width - 35, y + frame.height + 17))


def end_hero(base: Image.Image, ship: Image.Image, progress: float, t: float):
    """Give the closing promise a concrete subject: the vessel that keeps its intelligence onboard."""
    p=ease_out_back(progress*1.45)
    vessel=contain(ImageOps.mirror(ship.convert("RGBA")),(1040,680))
    x=round(900+(1-p)*1050); y=300+round(5*math.sin(t*.35))
    paste_shadow(base,vessel,(x,y),angle=1.0)
    d=ImageDraw.Draw(base)
    # A restrained route line ties the final vessel back to the evidence story.
    pts=[(1110,825),(1260,780),(1410,805),(1575,700),(1760,735)]
    d.line(pts,fill=(0,113,227,150),width=5)
    for px,py in pts:d.ellipse((px-7,py-7,px+7,py+7),fill=(255,59,48,215))
    q=ease_out_back(progress*1.8-.32)
    if q>0:
        back=paper_card((650,136),fill="#ffd34e",radius=5);back.putalpha(ragged_mask(back.size,t,970))
        label=paper_card((620,122),fill="#fffdf8",radius=4);ld=ImageDraw.Draw(label)
        ld.text((28,20),"SAFER SHIPS · CLEARER DECISIONS",font=F_MONO,fill=NAVY)
        ld.text((30,67),"EVIDENCE FOR EVERY WATCH",font=F_SMALL,fill=RED);ld.line((28,101,585,101),fill=BLUE,width=5)
        label.putalpha(ragged_mask(label.size,t,971));lx=round(1115+(1-q)*760);ly=750
        paste_shadow(base,back,(lx-12,ly+11),angle=2.2);paste_shadow(base,label,(lx,ly),angle=-1.4)


def render(source_t: float, bg: Image.Image, desktop: Image.Image, product: Image.Image, ship: Image.Image, operator: Image.Image, radar_art: Image.Image, sonar_art: Image.Image, scenes: list[dict]) -> Image.Image:
    base = animated_background(source_t, bg)
    tick_t = math.floor(source_t * 12) / 12
    base = Image.alpha_composite(base, Image.new("RGBA", (W, H), (245, 241, 230, 28)))
    scene_index=max(i for i,s in enumerate(scenes) if tick_t>=s["start"])
    base=background_energy(base,tick_t,scene_index)
    # The vessel is the first foreground layer: it may pass behind labels, never over them.
    if tick_t < 6:
        ship_p=ease_out_back(min(1,tick_t/3.2))
        vessel=contain(ImageOps.mirror(ship.convert("RGBA")),(1180,760))
        ship_x=round(790+(1-ship_p)*1280); ship_y=165+round(7*math.sin(tick_t*.55))
        paste_shadow(base,vessel,(ship_x,ship_y),angle=1.2)
    d = ImageDraw.Draw(base)
    if tick_t < 6:
        p = tick_t / 6; title_block(base, "03:00 · MID-OCEAN", "One watch. Too many signals.")
        stamp(base, "OFFLINE FIRST", (125, 410), RED, -5, 38)
        intro_artifacts(base,p,tick_t)
    elif tick_t < 17:
        p = (tick_t - 6) / 11; title_block(base, "NVIDIA DGX SPARK", "The local compute behind ShipMind.", hero=True)
        stamp(base, "RUNNING THE WORKLOAD", (1260, 425), BLUE, -3, 32)
        spark_hero(base,product,min(1,p*1.45),tick_t)
    elif tick_t < 28:
        p = (tick_t - 17) / 11; title_block(base, "FOUR STREAMS", "One evidence-bound briefing.")
        evidence_cards(base, p, radar_art, sonar_art)
        stamp(base, "HUMAN REVIEW", (126, 425), RED, -6, 38)
    elif tick_t < 44:
        p = (tick_t - 28) / 16; title_block(base, "ASK THE DUTY OFFICER", '“How are things now?”')
        ui_card(base, desktop, min(1, p * 2.2))
        console_sidecar(base,operator,p,tick_t)
        if p > .55: stamp(base, "~3s ON SPARK", (1515, 225), GREEN, -5, 38)
    elif tick_t < 54:
        p = (tick_t - 44) / 10; title_block(base, "THE PLATFORM STACK", "Sponsor products inside the working path.")
        platform_stack(base,p,tick_t); stamp(base,"34 / 34 CURRENT CHECKS",(126,455),RED,-4,31)
    else:
        p = (tick_t - 54) / 6; title_block(base, "INTELLIGENCE\nSTAYS ON BOARD", "ShipMind · Team Devx", hero=True)
        end_hero(base,ship,p,tick_t)
        stamp(base, "SYNTHETIC · REVIEWED · REPRODUCIBLE", (122, 650), RED, -4, 31)
        d.text((124, 875), "github.com/G1en-114/shipmind", font=F_MONO, fill=NAVY)
        fade = max(0, min(1, (p - .88) / .12))
        base = Image.alpha_composite(base, Image.new("RGBA", (W, H), (0, 0, 0, round(255 * fade))))
    base=transition_fx(base,tick_t,desktop,product,radar_art,sonar_art)
    if tick_t<59.85: voiceover_caption(base,scenes[scene_index]["voiceover"],500+scene_index)
    return base.convert("RGB")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=("preview", "intro-preview", "transition-preview", "full", "stills", "intro-stills"), default="preview")
    ap.add_argument("--output", type=Path); ap.add_argument("--fps", type=int, default=30); args = ap.parse_args()
    cfg = json.loads((ROOT / "scripts/video/timeline.json").read_text(encoding="utf-8"))
    bg = cover(Image.open(ROOT / "scripts/video/assets/gen/nautical-collage-bg-v1.png").convert("RGB"))
    desktop_path=ROOT / "runs/ui-review/spark-ai-english.png"
    if not desktop_path.exists(): desktop_path=ROOT / "runs/ui-review/spark-ai-desktop.png"
    desktop = Image.open(desktop_path).convert("RGB")
    product = Image.open(ROOT / "scripts/video/assets/gen/dgx-spark-newspaper-v2.png").convert("RGBA")
    ship=Image.open(ROOT / "scripts/video/assets/gen/cargo-ship-newspaper-v1.png").convert("RGBA")
    operator=Image.open(ROOT / "scripts/video/assets/gen/ai-duty-officer-collage-v1.png").convert("RGBA")
    radar_art=Image.open(ROOT / "scripts/video/assets/gen/marine-radar-newspaper-v1.png").convert("RGBA")
    sonar_art=Image.open(ROOT / "scripts/video/assets/gen/sonar-hydrophone-newspaper-v1.png").convert("RGBA")
    if args.mode in ("stills","intro-stills"):
        intro=args.mode=="intro-stills";outdir=args.output or ROOT / "runs/delivery/video" / ("shipmind-collage-v5-intro-stills" if intro else "shipmind-collage-v5-stills");outdir.mkdir(parents=True,exist_ok=True)
        times=(.7,1.8,3.3,5.2) if intro else (1.8,8.5,20.0,34.0,49.0,56.0)
        for i,t in enumerate(times):
            frame=render(t,bg,desktop,product,ship,operator,radar_art,sonar_art,cfg["scenes"]);frame.save(outdir/f"{i+1:02d}-{t:04.1f}s.jpg",quality=94)
        print(outdir);return
    duration = 7 if args.mode=="transition-preview" else 6 if args.mode=="intro-preview" else 12 if args.mode == "preview" else cfg["duration_s"]
    default_name="shipmind-collage-v10-transition-preview.mp4" if args.mode=="transition-preview" else "shipmind-collage-v5-intro-preview.mp4" if args.mode=="intro-preview" else "shipmind-collage-preview-v10.mp4" if args.mode=="preview" else "shipmind-promo-v10-silent.mp4"
    output = args.output or ROOT / "runs/delivery/video" / default_name
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))
    if not writer.isOpened(): raise RuntimeError("OpenCV could not open the MP4 writer")
    try:
        last_tick = None; encoded = None
        for frame_no in range(duration * args.fps):
            t = frame_no / args.fps
            if args.mode=="transition-preview":
                cuts=(6,17,28,44,54);seg=min(4,int(t//1.4));source_t=cuts[seg]-.2+(t-seg*1.4)
            else: source_t = t if args.mode=="intro-preview" else t * (cfg["duration_s"] / duration)
            tick = math.floor(source_t * cfg["visual_tick_fps"]) / cfg["visual_tick_fps"]
            if tick != last_tick:
                encoded = np.asarray(render(tick, bg, desktop, product, ship, operator, radar_art, sonar_art, cfg["scenes"]))[:, :, ::-1]
                last_tick = tick
            writer.write(encoded)
    finally:
        writer.release()
    print(output)


if __name__ == "__main__":
    main()
