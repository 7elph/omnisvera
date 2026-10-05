"""Editorial launch assets only. Never accesses experimental or operational databases."""
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / 'AppData/Local/Temp/omnisvera-launch-video-deps'))
import imageio_ffmpeg

BG = '#0a1017'
FG = '#e9edf3'
MUTED = '#9aabbd'
GREEN = '#91ecbd'
FONT = Path('C:/Windows/Fonts/segoeui.ttf')
BOLD = Path('C:/Windows/Fonts/segoeuib.ttf')
W, H = 1920, 1080

def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)

def text(draw, xy, content, size=42, color=FG, bold=False):
    draw.multiline_text(xy, content, font=font(size,bold), fill=color, spacing=18)

def frame(title, lines, image=None, number=1):
    canvas = Image.new('RGB',(W,H),BG)
    d = ImageDraw.Draw(canvas)
    text(d,(90,48),'OMNISVERA',32,GREEN,True)
    text(d,(1080,54),'AUDITED PRESENTATION · NOT LIVE',24,MUTED)
    d.line((90,105,1830,105),fill='#2a3746',width=2)
    if image:
        text(d,(90,132),title,44,FG,True)
        shot = Image.open(ROOT/image).convert('RGB')
        # Preserve the exact captured pixels; no fabricated UI or enlarged screenshot.
        canvas.paste(shot,((W-shot.width)//2,212))
        text(d,(90,992),lines,28,MUTED)
    else:
        text(d,(90,235),title,76,FG,True)
        text(d,(94,540),lines,42,MUTED)
        text(d,(94,976),'Models change. Experience does not have to restart.',28,GREEN)
    path = ROOT / f'video-frame-{number:02d}.png'
    canvas.save(path)
    return path

scenes = [
    (7,'A new AI session.\nThe same ongoing work.',
     'Why explain the accumulated state all over again?\nWhat if the experience lived outside the model?',None),
    (9,'One instruction. No injected state.',
     'A fresh GPT-6 Astra session discovers the persisted experience through Omnisvera.', 'gallery-01.png'),
    (9,'First: recovery without fabrication.',
     'Astra recovered Experience v2.\nThe evidence was insufficient.\nNo new prediction was issued.',None),
    (8,'Then: evidence became available.',
     'Real Coinbase candles were held in a fixed test fixture.\nLegitimate read scopes were corrected.\nThe inherited Experience was preserved.',None),
    (11,'The work continued.',
     'Astra recovered state, discovered signals, validated a candidate and committed Prediction #17.', 'gallery-02.png'),
    (9,'Not just an animation. Inspect the evidence.',
     'The replay exposes recorded tools, timestamps, provenance, hashes and limitations.', 'gallery-03.png'),
    (7,'A specific proof. Honest boundaries.',
     'Test database only. Fixed evidence, not a live market run.\nPrevious model identity is not established.\nFull operating-system isolation was not demonstrated.',None),
    (7,'Models change.\nExperience does not have to restart.',
     'Explore the audited replay.\nWhat would you want your next AI to inherit?',None),
]

frames=[]
for i,(seconds,title,lines,shot) in enumerate(scenes,1):
    frames.append((frame(title,lines,shot,i),seconds))

ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
command=[ffmpeg,'-hide_banner','-loglevel','error','-y']
for path,seconds in frames:
    command += ['-loop','1','-framerate','12','-t',str(seconds),'-i',str(path)]
filters=''.join(f'[{i}:v]setsar=1,format=yuv420p[v{i}];' for i in range(len(frames)))
filters+=''.join(f'[v{i}]' for i in range(len(frames)))+f'concat=n={len(frames)}:v=1:a=0[out]'
command += ['-filter_complex',filters,'-map','[out]','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'demo.mp4')]
subprocess.run(command,check=True)

# A typographic thumbnail, not a new illustrative logo or invented product screenshot.
thumb=Image.new('RGB',(240,240),BG)
d=ImageDraw.Draw(thumb)
d.rectangle((12,12,227,227),outline=GREEN,width=3)
d.text((54,33),'O',font=font(130,True),fill=GREEN)
d.text((43,189),'OMNISVERA',font=font(21,True),fill=FG)
thumb.save(ROOT/'thumbnail.png')
print('Video ready:',ROOT/'demo.mp4')
print('Duration:',sum(s[0] for s in scenes),'seconds; 1920x1080; editorial presentation; no audio.')
