#!/usr/bin/env python3
"""Build the 60-second non-verbal ShipMind promo sound-effects bed."""
from __future__ import annotations
import argparse, math, wave
from pathlib import Path
import numpy as np

SR=48000;DURATION=60.0;RNG=np.random.default_rng(114)
mix=np.zeros((round(SR*DURATION),2),dtype=np.float64)

def add(sound:np.ndarray,start:float,level=1.0,pan=0.0):
    if sound.ndim==1:sound=np.column_stack((sound*np.sqrt((1-pan)/2),sound*np.sqrt((1+pan)/2)))
    i=max(0,round(start*SR));j=min(len(mix),i+len(sound));mix[i:j]+=sound[:j-i]*level

def noise(n):return RNG.standard_normal(n)
def smooth(x,n=48):return np.convolve(x,np.ones(n)/n,mode='same')

def impact(power=1.0,d=.82):
    n=round(SR*d);t=np.arange(n)/SR;env=np.exp(-t*7.2)
    body=(np.sin(2*np.pi*(44*t+20*t*t))+0.48*np.sin(2*np.pi*83*t))*env
    crack=smooth(noise(n),5)*np.exp(-t*28);return power*(.72*body+.28*crack)

def whoosh(d=.62):
    n=round(SR*d);t=np.arange(n)/SR;env=np.sin(np.pi*np.clip(t/d,0,1))**1.7
    air=noise(n)-smooth(noise(n),90);sweep=np.sin(2*np.pi*(130*t+780*t*t))*env
    return (.22*air+.16*sweep)*env

def paper(d=.58):
    n=round(SR*d);t=np.arange(n)/SR;raw=noise(n);fib=raw-smooth(raw,22)
    env=(np.sin(np.pi*t/d)**.65)*(1+.18*np.sin(2*np.pi*17*t));return .3*fib*env

def ping(freq=930,d=1.1):
    n=round(SR*d);t=np.arange(n)/SR;env=np.exp(-t*3.9)
    return (np.sin(2*np.pi*freq*t)+.36*np.sin(2*np.pi*freq*2.01*t))*env*.34

def click():
    n=round(SR*.055);t=np.arange(n)/SR;return (noise(n)*.24+np.sin(2*np.pi*2100*t)*.1)*np.exp(-t*80)

# Quiet ship/room bed: felt more than heard, leaving space for the team's narration.
t=np.arange(len(mix))/SR;bed=smooth(noise(len(mix)),160)*.018+np.sin(2*np.pi*38*t)*.0035
mix[:,0]+=bed;mix[:,1]+=np.roll(bed,120)

major=(6,17,28,44,54)
for i,c in enumerate(major):
    add(whoosh(.7),c-.42,.8,(-.45,.35,-.25,.45,0)[i]);add(impact(1.0 if c in (6,54) else .78),c,.78)
for c in (5.62,43.58):add(paper(.72),c,.82,pan=-.2 if c<10 else .2)
for c,f in ((17.2,510),(23.25,760),(28.12,1050),(54.25,620)):add(ping(f),c,.72)
for c in (4.25,15.2,26.1,40.9,52.1,57.5):add(impact(.48,.52),c,.64)

# Console section: restrained mechanical typing, not a voice substitute.
clock=32.0
while clock<41.4:
    clock+=float(RNG.uniform(.10,.27));add(click(),clock,float(RNG.uniform(.22,.42)),float(RNG.uniform(-.6,.6)))

peak=np.max(np.abs(mix));mix=np.tanh(mix*1.18);mix*=.92/max(np.max(np.abs(mix)),1e-9)
pcm=(mix*32767).astype('<i2')
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=Path('runs/delivery/video/shipmind-promo-v8-sfx.wav'));args=ap.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True)
with wave.open(str(args.output),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
print(args.output)
