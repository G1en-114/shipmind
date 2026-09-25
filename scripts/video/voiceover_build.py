#!/usr/bin/env python3
"""Fit SAPI narration to the promo timing and mix it over the effects bed."""
from __future__ import annotations
import argparse,subprocess,wave
from pathlib import Path
import imageio_ffmpeg
import numpy as np

SR=48000;WINDOWS=((.15,5.72),(6.08,16.72),(17.08,27.72),(28.08,43.72),(44.08,53.72),(54.08,59.92))

def wav_read(path:Path):
    with wave.open(str(path),'rb') as w:
        ch=w.getnchannels();sr=w.getframerate();sw=w.getsampwidth();raw=w.readframes(w.getnframes())
    if sw!=2:raise ValueError(f'{path}: expected 16-bit PCM')
    a=np.frombuffer(raw,dtype='<i2').astype(np.float64)/32768
    if ch>1:a=a.reshape(-1,ch).mean(1)
    return sr,a

def wav_write(path:Path,a:np.ndarray,channels=1):
    path.parent.mkdir(parents=True,exist_ok=True);a=np.clip(a,-1,1)
    if channels==2 and a.ndim==1:a=np.column_stack((a,a))
    with wave.open(str(path),'wb') as w:w.setnchannels(channels);w.setsampwidth(2);w.setframerate(SR);w.writeframes((a*32767).astype('<i2').tobytes())

def atempo_chain(value:float):
    vals=[]
    while value<.5:vals.append(.5);value/=.5
    while value>2:vals.append(2.0);value/=2
    vals.append(value);return ','.join(f'atempo={v:.8f}' for v in vals)

ap=argparse.ArgumentParser();ap.add_argument('--raw-dir',type=Path,default=Path('runs/delivery/video/voice_raw'));ap.add_argument('--sfx',type=Path,default=Path('runs/delivery/video/shipmind-promo-v8-sfx.wav'));ap.add_argument('--voice',type=Path,default=Path('runs/delivery/video/shipmind-voiceover-v10.wav'));ap.add_argument('--mix',type=Path,default=Path('runs/delivery/video/shipmind-promo-v10-voice-sfx.wav'));ap.add_argument('--sfx-gain',type=float,default=.12,help='Linear effects gain before voice ducking; 0.12 is about -18.4 dB.');args=ap.parse_args()
ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();work=args.raw_dir/'processed';work.mkdir(parents=True,exist_ok=True)
voice=np.zeros(round(SR*60),dtype=np.float64)
for i,(start,end) in enumerate(WINDOWS,1):
    source=args.raw_dir/f'segment-{i:02d}.wav';sr,a=wav_read(source);source_duration=len(a)/sr;target=end-start
    # Preserve one narration rate across the film. Only accelerate a segment if it would cross its scene boundary.
    tempo=max(1.0,source_duration/target);out=work/f'segment-{i:02d}.wav'
    filters=atempo_chain(tempo)+',highpass=f=68,lowpass=f=11800,bass=g=2.5:f=145:w=.7,equalizer=f=260:t=q:w=1.0:g=1.4,equalizer=f=2100:t=q:w=1.2:g=1.0,treble=g=-1.2:f=6500:w=.6,acompressor=threshold=0.12:ratio=2.4:attack=8:release=105,loudnorm=I=-21:TP=-4:LRA=7'
    subprocess.run([ffmpeg,'-y','-i',str(source),'-af',filters,'-ar',str(SR),'-ac','1','-c:a','pcm_s16le',str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    _,seg=wav_read(out);need=round(target*SR)
    if len(seg)>need:seg=seg[:need]
    fade=min(round(.035*SR),len(seg)//4);seg[:fade]*=np.linspace(0,1,fade);seg[-fade:]*=np.linspace(1,0,fade)
    pos=round(start*SR);voice[pos:pos+len(seg)]+=seg
wav_write(args.voice,voice)

with wave.open(str(args.sfx),'rb') as w:
    if w.getframerate()!=SR or w.getnchannels()!=2 or w.getsampwidth()!=2:raise ValueError('effects bed must be 48 kHz stereo PCM16')
    sfx=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(np.float64).reshape(-1,2)/32768
env=np.abs(voice);kernel=np.ones(round(.12*SR))/round(.12*SR);env=np.convolve(env,kernel,mode='same');duck=1-.62*np.clip(env/.035,0,1)
mix=sfx*duck[:,None]*args.sfx_gain+voice[:,None]*.92;mix=np.tanh(mix*1.08);mix*=.94/max(np.max(np.abs(mix)),1e-9);wav_write(args.mix,mix,2)
print(args.voice);print(args.mix)
