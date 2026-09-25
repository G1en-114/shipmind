#!/usr/bin/env python3
"""Render ShipMind promo 2: a dark editorial evidence-film inspired by the supplied reference."""
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter,ImageFont,ImageOps

ROOT=Path(__file__).resolve().parents[2];W,H=1920,1080
INK=(11,11,13);PAPER=(232,222,198);GOLD=(199,167,106);IVORY=(242,237,224);RED=(174,76,63);BLUE=(68,127,158)

def font(size,serif=False,bold=False,mono=False):
    names=(['consolab.ttf' if bold else 'consola.ttf'] if mono else
           ['simsun.ttc','simfang.ttf'] if serif else ['msyhbd.ttc' if bold else 'msyh.ttc','arialbd.ttf' if bold else 'arial.ttf'])
    for n in names:
        p=Path('C:/Windows/Fonts')/n
        if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default()
F_KICK=font(18,mono=True,bold=True);F_TITLE=font(58,serif=True);F_HERO=font(86,serif=True);F_BODY=font(27);F_SMALL=font(19);F_MONO=font(17,mono=True);F_CAP=font(27,bold=True)

def cover(im,size=(W,H)):
    s=max(size[0]/im.width,size[1]/im.height);r=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS)
    return r.crop(((r.width-size[0])//2,(r.height-size[1])//2,(r.width+size[0])//2,(r.height+size[1])//2))
def contain(im,size):
    s=min(size[0]/im.width,size[1]/im.height);return im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))),Image.Resampling.LANCZOS)
def ease(x):x=max(0,min(1,x));return 1-(1-x)**3
def fade(x,a=.08,b=.9):return max(0,min(1,x/a))*max(0,min(1,(1-x)/(1-b)))
def alpha(im,a):
    im=im.copy().convert('RGBA');im.putalpha(ImageEnhance.Brightness(im.getchannel('A')).enhance(max(0,a)));return im
def paste(base,im,xy,a=1,shadow=True):
    im=alpha(im,a)
    if shadow:
        sh=Image.new('RGBA',im.size,(0,0,0,0));sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(18)));shade=Image.new('RGBA',im.size,(0,0,0,115));shade.putalpha(sh.getchannel('A'));base.alpha_composite(shade,(xy[0]+13,xy[1]+18))
    base.alpha_composite(im,xy)
def fit_text(draw,text,font_,max_w):
    out=[]
    for para in text.split('\n'):
        line=''
        for ch in para:
            if draw.textlength(line+ch,font=font_)<=max_w:line+=ch
            else:out.append(line);line=ch
        out.append(line)
    return '\n'.join(out)

def archive_bg(bg,t,light=False):
    if light:return Image.new('RGBA',(W,H),PAPER+(255,))
    src=cover(bg);dx=round(18*math.sin(t*.05));src=ImageOps.expand(src,border=25,fill=INK).crop((25+dx,25,25+dx+W,25+H))
    src=ImageEnhance.Color(src).enhance(.38);src=ImageEnhance.Contrast(src).enhance(1.12);base=src.convert('RGBA')
    base=Image.alpha_composite(base,Image.new('RGBA',(W,H),(4,5,7,150)))
    vign=Image.new('L',(W,H));v=np.zeros((H,W),np.uint8);yy,xx=np.ogrid[:H,:W];rr=((xx-W/2)/(W*.72))**2+((yy-H/2)/(H*.72))**2;v[:]=np.clip(rr*180,0,155);vign=Image.fromarray(v)
    veil=Image.new('RGBA',(W,H),(0,0,0,0));veil.putalpha(vign);return Image.alpha_composite(base,veil)

def grain(base,t):
    rng=np.random.default_rng(2200+int(t*12));n=rng.integers(0,255,(H//3,W//3),np.uint8);n=Image.fromarray(n).resize((W,H),Image.Resampling.BILINEAR)
    tex=Image.new('RGBA',(W,H),(232,222,198,0));tex.putalpha(n.point(lambda x:round(abs(x-128)*.045)));return Image.alpha_composite(base,tex)
def rule(draw,y,x1=92,x2=W-92):draw.line((x1,y,x2,y),fill=GOLD+(105,),width=1)
def heading(base,kicker,title,dark=True,x=105,y=90,max_w=1250,hero=False):
    d=ImageDraw.Draw(base);col=IVORY if dark else (55,45,37);mut=GOLD if dark else (133,92,59)
    d.text((x,y),kicker,font=F_KICK,fill=mut);d.line((x,y+31,x+86,y+31),fill=mut,width=2)
    f=F_HERO if hero else F_TITLE;wrapped=fit_text(d,title,f,max_w);d.multiline_text((x,y+58),wrapped,font=f,fill=col,spacing=14)
def caption(base,text):
    d=ImageDraw.Draw(base);wrapped=fit_text(d,text,F_CAP,1380);box=d.multiline_textbbox((0,0),wrapped,font=F_CAP,spacing=8);h=box[3]-box[1]+42
    x=270;y=H-72-h;d.rounded_rectangle((x,y,W-x,y+h),5,fill=(5,5,6,218));d.multiline_text((x+30,y+19),wrapped,font=F_CAP,fill=IVORY,spacing=8,align='center')
def frame_card(im,size,label,idx):
    card=Image.new('RGBA',size,(244,238,222,255));d=ImageDraw.Draw(card);d.rectangle((0,0,size[0]-1,size[1]-1),outline=(69,51,39,70),width=2)
    shot=cover(im,(size[0]-26,size[1]-58));card.alpha_composite(shot.convert('RGBA'),(13,34));d.text((13,10),f'OBS {idx:02d}  {label}',font=F_MONO,fill=(49,42,36));return card

def scene_incident(base,p,ship):
    d=ImageDraw.Draw(base);a=fade(p);heading(base,'AN ONBOARD DECISION STORY','一次异常，\n如何成为判断',True,hero=True,max_w=900)
    vessel=contain(ship,(900,580));paste(base,vessel,(980,315),a*.62,False)
    cx,cy=960,525;r=150+ease(p)*440;d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=GOLD+(round(95*a),),width=2);d.line((cx-36,cy,cx+36,cy),fill=GOLD+(150,),width=2);d.line((cx,cy-36,cx,cy+36),fill=GOLD+(150,),width=2)
def scene_evidence(base,p,shots):
    heading(base,'ORIGINAL EVIDENCE','从原始观测开始',False)
    labels=('声学频谱','表盘读数','雷达目标','航线偏移','AI 简报','执行日志');positions=((95,290),(655,290),(1215,290),(180,610),(740,610),(1300,610))
    for i,(label,pos) in enumerate(zip(labels,positions)):
        q=ease(p*1.35-i*.08);card=frame_card(shots[i%len(shots)],(510,265),label,i+1);paste(base,card,(round(pos[0]+(1-q)*(i%3-1)*260),round(pos[1]+(1-q)*180)),q)
def scene_trace(base,p,desktop,radar,sonar):
    heading(base,'IDENTIFY · COMPARE · TRACE','识别、对照、追溯',True)
    shot=cover(desktop,(1180,680)).filter(ImageFilter.GaussianBlur(.25));paste(base,shot,(75,275),.72)
    paste(base,contain(radar,(430,310)),(1395,250),.9);paste(base,contain(sonar,(470,300)),(1360,620),.9)
    d=ImageDraw.Draw(base);nodes=((1110,470,'声学变化'),(1240,610,'仪表读数'),(1500,515,'雷达目标'),(1660,750,'来源与时间'))
    for i,(x,y,label) in enumerate(nodes):
        q=ease(p*1.5-i*.13);d.ellipse((x-13,y-13,x+13,y+13),outline=GOLD+(round(230*q),),width=3);d.line((x+15,y,x+165,y-55),fill=GOLD+(round(170*q),),width=2);d.text((x+175,y-72),label,font=F_SMALL,fill=IVORY)
def scene_threshold(base,p,desktop):
    heading(base,'DECISION SCALE','0.1 — 1.0，逐级比较',True)
    left=cover(desktop,(1500,690));right=ImageEnhance.Color(left).enhance(.35);right=ImageEnhance.Contrast(right).enhance(1.45)
    x0=210;y0=260;paste(base,right,(x0,y0),.88);split=round(left.width*(.18+.68*ease(p)));base.alpha_composite(left.crop((0,0,split,left.height)).convert('RGBA'),(x0,y0))
    d=ImageDraw.Draw(base);d.line((x0+split,y0-10,x0+split,y0+left.height+10),fill=IVORY+(230,),width=3);d.ellipse((x0+split-22,y0+left.height//2-22,x0+split+22,y0+left.height//2+22),fill=IVORY,outline=GOLD,width=3)
    for i in range(11):
        x=x0+i*left.width/10;d.line((x,y0+left.height+28,x,y0+left.height+41),fill=GOLD,width=2);d.text((x-12,y0+left.height+50),f'{i/10:.1f}',font=F_MONO,fill=IVORY)
def scene_judgement(base,p,shots):
    heading(base,'NOT ONE ANSWER','不是一个答案，\n而是三层判断尺度',False,max_w=950)
    specs=(('观察','信号发生了什么','保留原始读数'),('推断','哪些解释更可信','显示证据边界'),('行动','下一步检查什么','始终由人确认'))
    for i,(name,line,sub) in enumerate(specs):
        q=ease(p*1.45-i*.16);x=170+i*560;y=430;card=Image.new('RGBA',(500,410),(246,240,224,255));d=ImageDraw.Draw(card)
        im=cover(shots[i],(460,210));card.alpha_composite(im.convert('RGBA'),(20,20));d.text((25,250),name,font=font(36,serif=True),fill=(58,45,36));d.text((25,305),line,font=F_BODY,fill=(62,54,46));d.text((25,355),sub,font=F_SMALL,fill=RED);paste(base,card,(x,round(y+(1-q)*230)),q)
def scene_workflow(base,p,shots,spark):
    heading(base,'A REPRODUCIBLE WORKFLOW','一条完整工作路径',True)
    names=('DGX SPARK','AGENT SKILLS','DEEPSTREAM','QWEN','VLLM','HUMAN REVIEW')
    for i,name in enumerate(names):
        q=ease(p*1.5-i*.08);col=i%3;row=i//3;x=145+col*575;y=330+row*315
        card=Image.new('RGBA',(510,250),(18,18,18,235));d=ImageDraw.Draw(card);d.rectangle((0,0,509,249),outline=GOLD+(100,),width=2)
        im=cover(spark if i==0 else shots[i%len(shots)],(180,205));card.alpha_composite(ImageEnhance.Color(im).enhance(.65).convert('RGBA'),(18,22));d.text((220,45),f'{i+1:02d}',font=F_MONO,fill=GOLD);d.text((220,86),name,font=font(24,bold=True),fill=IVORY);d.line((220,135,474,135),fill=GOLD+(100,),width=1);d.text((220,158),'LOCAL · TRACEABLE',font=F_MONO,fill=(170,164,151));paste(base,card,(x,round(y+(1-q)*220)),q)
def scene_audit(base,p,reports):
    heading(base,'A TRACEABLE PROCESS','过程留痕\n失败可见\n人工复核',False,max_w=850)
    shot=cover(reports,(870,700));paste(base,shot,(930,260),.9)
    d=ImageDraw.Draw(base)
    for i,(name,state,col) in enumerate((('原始观测写入','PASS',(49,125,73)),('推理过程记录','PASS',(49,125,73)),('失败任务保留','VISIBLE',RED),('关键变化复核','HUMAN',BLUE))):
        q=ease(p*1.6-i*.12);y=430+i*105;d.rectangle((125,y,760,y+74),fill=(44,38,33,18),outline=(86,64,48,75),width=2);d.text((150,y+21),name,font=F_BODY,fill=(57,47,40));d.text((590,y+24),state,font=F_MONO,fill=col+(255,))
def scene_principle(base,p,officer,ship,spark):
    d=ImageDraw.Draw(base)
    if p<.58:
        heading(base,'HUMAN IN REVIEW','AI 辅助 ≠ 自动定论',True,hero=True,max_w=1100)
        paste(base,contain(officer,(650,760)),(1230,240),ease(p*2),False);d.text((110,470),'技术可以提高比较效率，\n判断仍由值班人员完成。',font=font(35,serif=True),fill=IVORY,spacing=18)
    else:
        q=ease((p-.58)/.42);heading(base,'SHIPMIND · POWERED BY NVIDIA DGX SPARK','让证据被看见\n让判断可讨论',True,hero=True,max_w=1000)
        paste(base,contain(ship,(720,500)),(1060,420),q*.72,False);paste(base,contain(spark,(430,330)),(1385,670),q,False);d.text((112,670),'更安全的船舶\n更清晰的决定',font=font(35,serif=True),fill=GOLD,spacing=15)

def render(t,assets,cfg):
    scenes=cfg['scenes'];idx=max(i for i,s in enumerate(scenes) if t>=s['start']);s=scenes[idx];p=(t-s['start'])/(s['end']-s['start']);light=s['id'] in ('evidence','judgement','audit')
    base=archive_bg(assets['bg'],t,light);sid=s['id']
    if sid=='incident':scene_incident(base,p,assets['ship'])
    elif sid=='evidence':scene_evidence(base,p,assets['shots'])
    elif sid=='trace':scene_trace(base,p,assets['desktop'],assets['radar'],assets['sonar'])
    elif sid=='threshold':scene_threshold(base,p,assets['desktop'])
    elif sid=='judgement':scene_judgement(base,p,assets['shots'])
    elif sid=='workflow':scene_workflow(base,p,assets['shots'],assets['spark'])
    elif sid=='audit':scene_audit(base,p,assets['reports'])
    else:scene_principle(base,p,assets['officer'],assets['ship'],assets['spark'])
    if t<71.5:caption(base,s['voiceover'])
    if p<.06:base=Image.blend(Image.new('RGBA',(W,H),INK+(255,)),base,ease(p/.06))
    return grain(base,t).convert('RGB')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('preview','full','stills'),default='preview');ap.add_argument('--fps',type=int,default=30);ap.add_argument('--output',type=Path);args=ap.parse_args()
    cfg=json.loads((ROOT/'scripts/video/promo2_timeline.json').read_text(encoding='utf-8'))
    def img(p):return Image.open(ROOT/p).convert('RGBA')
    assets={'bg':img('scripts/video/assets/gen/nautical-collage-bg-v1.png'),'ship':img('scripts/video/assets/gen/cargo-ship-newspaper-v1.png'),'spark':img('scripts/video/assets/gen/dgx-spark-newspaper-v2.png'),'radar':img('scripts/video/assets/gen/marine-radar-newspaper-v1.png'),'sonar':img('scripts/video/assets/gen/sonar-hydrophone-newspaper-v1.png'),'officer':img('scripts/video/assets/gen/ai-duty-officer-collage-v1.png'),'desktop':img('runs/ui-review/spark-ai-desktop.png'),'reports':img('runs/ui-review/reports.png')}
    assets['shots']=[assets['desktop'],img('runs/ui-review/spark-5min.png'),assets['radar'],assets['sonar'],img('runs/ui-review/spark-ai-english.png'),assets['reports']]
    if args.mode=='stills':
        out=args.output or ROOT/'runs/delivery/video/shipmind-promo2-stills';out.mkdir(parents=True,exist_ok=True)
        for i,t in enumerate((3.2,11.5,21,31,41.5,52,61,68.5)):render(t,assets,cfg).save(out/f'{i+1:02d}-{t:04.1f}.jpg',quality=92)
        print(out);return
    duration=18 if args.mode=='preview' else cfg['duration_s'];out=args.output or ROOT/'runs/delivery/video'/('shipmind-promo2-preview-v1.mp4' if args.mode=='preview' else 'shipmind-promo2-v1-silent.mp4');out.parent.mkdir(parents=True,exist_ok=True)
    writer=cv2.VideoWriter(str(out),cv2.VideoWriter_fourcc(*'mp4v'),args.fps,(W,H));last=None;encoded=None
    try:
        for n in range(duration*args.fps):
            source=(n/args.fps)*(cfg['duration_s']/duration);tick=math.floor(source*cfg['visual_tick_fps'])/cfg['visual_tick_fps']
            if tick!=last:encoded=np.asarray(render(tick,assets,cfg))[:,:,::-1];last=tick
            writer.write(encoded)
    finally:writer.release()
    print(out)
if __name__=='__main__':main()
