#!/usr/bin/env python3
"""3D-stylized C64 BASIC school lesson, procedurally rendered to MP4.
Requires numpy, Pillow, OpenCV and ffmpeg.  No externally hosted assets.
"""
from __future__ import annotations
import math, os, subprocess, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1280, 720
FPS = 24
DURATION = 16
OUT = '/mnt/data/C64_BASIC_Schultafel_3D.mp4'
PREVIEW = '/mnt/data/C64_BASIC_Schultafel_Vorschau.png'
FONT_BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
FONT_NORMAL = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONT_SANS = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font = lambda path,size: ImageFont.truetype(path, size)
TEXW,TEXH=960,510
quad = np.float32([[392,160], [1217,152], [1190,570], [396,579]])
srcquad=np.float32([[0,0],[TEXW,0],[TEXW,TEXH],[0,TEXH]])
HOM = cv2.getPerspectiveTransform(srcquad,quad)
BOARD_CROP=(388,146,1224,587)
cx0,cy0,cx1,cy1=BOARD_CROP
local_H=np.array([[1.,0.,-cx0],[0.,1.,-cy0],[0.,0.,1.]]) @ HOM
msk=cv2.warpPerspective(np.full((TEXH,TEXW),255,dtype=np.uint8),local_H,(cx1-cx0,cy1-cy0),flags=cv2.INTER_LINEAR)
board_alpha=msk.astype(np.float32)[...,None]/255.
lines=['10 PRINT "HALLO, C64!"', '20 FOR I=1 TO 5','30 PRINT "ZAHL:";I','40 NEXT I','50 END']
line_y=[166,221,276,331,386]

# Helper operations with RGB image

def poly(img, pts, color, antialias=cv2.LINE_AA):
    cv2.fillConvexPoly(img, np.array(pts,dtype=np.int32), color, lineType=antialias)

def line(img, p1, p2, color, thick=2):
    cv2.line(img, tuple(map(int,p1)),tuple(map(int,p2)),color,thick,cv2.LINE_AA)

def ellipse(img,center,axes,col,angle=0):
    cv2.ellipse(img,tuple(map(int,center)),tuple(map(int,axes)),angle,0,360,col,-1,cv2.LINE_AA)

def shaded_oval(img,center,axes,base, h=(.32,-.42)):
    # layered directional ellipsoids approximate a smoothly-lit 3D surface
    ellipse(img,(center[0]+3,center[1]+4),axes,tuple(max(0,int(x*.57)) for x in base))
    ellipse(img,center,axes,base)
    for factor, strength in [(0.83,.14),(.68,.19),(.50,.14),(.31,.10)]:
        xx=center[0]+h[0]*(1-factor)*axes[0]*1.65
        yy=center[1]+h[1]*(1-factor)*axes[1]*1.65
        c=tuple(min(255,int(x+(255-x)*strength)) for x in base)
        ellipse(img,(xx,yy),(axes[0]*factor,axes[1]*factor),c)

def roundline(img,p1,p2,th,col):
    line(img,p1,p2,col,th)
    ellipse(img,p1,(th//2,th//2),col)
    ellipse(img,p2,(th//2,th//2),col)


def create_background():
    rng=np.random.default_rng(42)
    ys,xx=np.mgrid[0:H,0:W]
    wall=np.stack([
        197-25*(xx/W)+8*(ys/H),
        173-27*(xx/W)+4*(ys/H),
        136-23*(xx/W)+5*(ys/H)],axis=-1)
    noise=rng.normal(0,1.8,(H,W,1))
    img=np.uint8(np.clip(wall+noise,0,255)).copy()
    # cozy, low-poly classroom wall with pilasters
    for x in [18,122,316,1249]:
        poly(img,[(x,5),(x+13,5),(x+14,580),(x,580)],(178,142,102))
        line(img,(x,7),(x,575),(232,204,151),3)
    # poster / window on left
    poly(img,[(29,73),(276,73),(285,252),(27,249)],(106,80,58))
    poly(img,[(45,85),(262,85),(268,238),(43,237)],(84,143,161))
    # arched soft outdoor light
    for y in range(92,237,6):
        t=(y-92)/145
        line(img,(47,y),(264,y),(int(102+49*t),int(175+18*t),int(195+2*t)),6)
    line(img,(154,83),(155,244),(239,218,171),10)
    line(img,(40,161),(268,161),(236,209,162),10)
    for x in [34,267]: line(img,(x,75),(x,248),(94,67,43),9)
    line(img,(31,75),(269,75),(224,174,111),11)
    # shadow underneath board and desk
    poly(img,[(0,547),(1280,533),(1280,720),(0,720)],(114,75,49))
    poly(img,[(0,566),(1280,551),(1280,720),(0,720)],(160,111,68))
    for y in [594,637,696]:
        line(img,(0,y),(1279,y-13),(110,74,47),3)
        line(img,(0,y+3),(1279,y-10),(203,146,89),2)
    for x in [144,399,677,936,1177]:
        line(img,(x,565),(x+int((x-640)*.34),720),(128,85,53),2)
    # subtle broad sunlight on floor
    overlay=img.copy()
    poly(overlay,[(60,552),(267,552),(483,720),(2,720)],(227,180,108))
    img=cv2.addWeighted(overlay,.17,img,.83,0)
    # left foreground desk and lesson objects
    poly(img,[(45,630),(370,625),(398,654),(53,660)],(75,49,34))
    poly(img,[(38,618),(377,614),(392,639),(45,645)],(169,110,63))
    line(img,(48,618),(373,613),(237,169,94),5)
    poly(img,[(88,637),(110,637),(104,720),(82,720)],(99,64,42))
    # little chalk piece shadow on tray later
    return img


def create_board_frame(bg):
    im=bg.copy()
    poly(im,[(370,139),(1258,125),(1242,611),(378,621)],(63,47,32)) # deep cast shadow
    poly(im,[(367,122),(1246,111),(1223,607),(368,615)],(116,69,38))
    poly(im,[(373,128),(1239,118),(1218,594),(377,606)],(203,140,69))
    poly(im,[(378,132),(1234,124),(1212,586),(381,599)],(102,58,30))
    # bevel catchlight
    line(im,(377,128),(1239,116),(238,186,107),8)
    line(im,(380,130),(381,600),(234,161,85),8)
    line(im,(1237,119),(1217,600),(81,47,27),10)
    line(im,(384,597),(1220,589),(81,47,30),12)
    # inner dark glass-esque plane
    poly(im,quad,(14,52,48))
    # lower chalk trough with real extrusion
    poly(im,[(370,603),(1221,586),(1241,606),(390,625)],(99,61,34))
    poly(im,[(374,601),(1219,585),(1231,595),(382,614)],(212,146,73))
    line(im,(386,605),(1217,591),(246,189,117),4)
    # chalk + eraser sitting on chalk ledge
    poly(im,[(975,591),(1059,589),(1066,601),(980,604)],(42,42,38))
    poly(im,[(973,588),(1056,587),(1063,595),(979,599)],(135,91,51))
    line(im,(1085,591),(1136,590),(224,224,181),5)
    line(im,(1090,587),(1138,586),(249,249,208),2)
    for x,y in [(378,129),(1232,122),(386,604),(1212,592)]:
        ellipse(im,(x,y),(4,4),(73,48,31))
        ellipse(im,(x-1,y-1),(2,2),(241,206,139))
    return im

BASEBG=create_background()
BASEBG=create_board_frame(BASEBG)

rng=np.random.default_rng(123)
ys,xs=np.mgrid[0:TEXH,0:TEXW]
texbase=np.zeros((TEXH,TEXW,3),dtype=np.uint8)
base=np.array([14,60,53],dtype=float)
vignette=(((xs-TEXW*.47)/(TEXW*.80))**2+((ys-TEXH*.5)/(TEXH*.71))**2)*15
chalknoise=rng.normal(0,2,(TEXH,TEXW))
for c in range(3):
    texbase[:,:,c]=np.uint8(np.clip(base[c]+chalknoise-vignette,0,255))
# add subtle chalk scratches, chalky wear
for i in range(1050):
    x=int(rng.integers(0,TEXW)); y=int(rng.integers(0,TEXH))
    col=(34,79,69)
    if rng.random()<.18: col=(24,72,64)
    line(texbase,(x,y),(x+int(rng.integers(2,21)),y),col,1)

FONT_TITLE=font(FONT_SANS,45)
FONT_LESSON=font(FONT_BOLD,20)
FONT_CODE=font(FONT_BOLD,30)
FONT_RUNNING=font(FONT_BOLD,29)
FONT_C64=font(FONT_BOLD,16)
FONT_OUTPUT=font(FONT_BOLD,18)
FONT_SMALL=font(FONT_NORMAL,14)

# Static chalkboard title / region layout
baseim=Image.fromarray(texbase)
draw=ImageDraw.Draw(baseim)
draw.text((51,22),'C64 BASIC',font=FONT_TITLE,fill=(230,241,205),stroke_width=0)
draw.text((54,92),'LEKTION 01   |   PRINT · FOR/NEXT · RUN',font=FONT_LESSON,fill=(160,204,173))
draw.line([(50,136),(919,136)],fill=(130,170,143),width=2)
draw.line([(576,156),(576,479)],fill=(119,150,130),width=2)
draw.text((606,160),'C64 AUSGABE',font=FONT_LESSON,fill=(217,232,188))
# small sketch stars and corner details
for xx,yy in [(904,47),(888,62),(916,79)]:
    draw.ellipse((xx-2,yy-2,xx+2,yy+2),fill=(170,217,167))
for j in range(12):
    yy=486+j%2
    draw.line((55+j*16,yy,62+j*16,yy),fill=(107,143,123),width=1)
STATIC_TEX=np.array(baseim)

# Console panel baseline draw with characteristic C64 colors
PANEL_X,PANEL_Y,PANEL_W,PANEL_H=603,202,332,276


def animated_board_texture(t):
    tex=STATIC_TEX.copy()
    # underpaint RUN panel (projected on chalk surface)
    cv2.rectangle(tex,(PANEL_X+4,PANEL_Y+7),(PANEL_X+PANEL_W+5,PANEL_Y+PANEL_H+7),(5,24,27),-1)
    cv2.rectangle(tex,(PANEL_X-2,PANEL_Y-2),(PANEL_X+PANEL_W+2,PANEL_Y+PANEL_H+2),(166,154,125),-1)
    cv2.rectangle(tex,(PANEL_X+4,PANEL_Y+4),(PANEL_X+PANEL_W-4,PANEL_Y+PANEL_H-4),(64,61,154),-1)
    cv2.rectangle(tex,(PANEL_X+14,PANEL_Y+14),(PANEL_X+PANEL_W-14,PANEL_Y+PANEL_H-14),(39,38,115),-1)
    for yy in range(PANEL_Y+18,PANEL_Y+PANEL_H-15,5):
        cv2.line(tex,(PANEL_X+14,yy),(PANEL_X+PANEL_W-14,yy),(46,45,123),1)
    pil=Image.fromarray(tex)
    d=ImageDraw.Draw(pil)
    # Typewriter timeline with pauses between statements
    starts=[1.15,2.45,3.75,5.05,6.30]
    durations=[1.12,1.02,1.10,.94,.67]
    for i,(s,span) in enumerate(zip(starts,durations)):
        if t < s: continue
        n=max(0,min(len(lines[i]),int((t-s)/span*len(lines[i]))))
        ink=(224,235,194) if i != 2 else (225,245,202)
        d.text((56,line_y[i]),lines[i][:n],font=FONT_CODE,fill=ink)
        if n<len(lines[i]) and t<s+span and int(t*3)%2==0:
            xx=56+d.textlength(lines[i][:n],font=FONT_CODE)
            d.rectangle((xx+2,line_y[i]+4,xx+6,line_y[i]+30),fill=(224,233,184))
    # RUN label with dynamic highlight
    if t>7.70:
        n=max(0,min(3,int((t-7.7)/.45*3)))
        d.text((56,440),'RUN'[:n],font=FONT_RUNNING,fill=(249,222,137))
    # output screen emulate BASIC execution
    white=(182,180,240)
    cstart=PANEL_Y+20
    labels=[('**** COMMODORE 64 ****',.0),('BASIC V2     38911 BYTES',.0),('FREE',.0),('READY.',.0),('RUN',8.55),('HALLO, C64!',9.15),('ZAHL:1',9.75),('ZAHL:2',10.35),('ZAHL:3',10.95),('ZAHL:4',11.55),('ZAHL:5',12.15),('READY.',13.05)]
    cy=cstart
    # Make initial lines small enough to fit everything with 20 pixel spacing
    for j,(s,at) in enumerate(labels):
        if t<at: continue
        if t < at+.23 and at>0:
            count=max(1,int((t-at)/.23*len(s)))
        else: count=len(s)
        txt=s[:count]
        d.text((PANEL_X+22,cy),txt,font=FONT_C64,fill=white)
        cy += 20
    if t>13.40 and math.sin(t*7.3)>-.06:
        d.rectangle((PANEL_X+22,cy+4,PANEL_X+31,cy+19),fill=white)
    # code highlighting bar as execution trace
    if t>8.45 and t<13.05:
        active=min(4,max(0,int((t-9.1)/.76)+1))
        active=[0,1,2,2,3][active]
        yy=line_y[active]
        # vertical bracket and small arrow (chalk marker)
        d.text((30,yy+1),'›',font=FONT_CODE,fill=(255,206,108))
        d.line((50,yy+36,480,yy+36),fill=(132,178,136),width=2)
    if t>=13.65:
        # successful ending status with warm chalk mark
        d.text((398,440),'OK ✓',font=FONT_RUNNING,fill=(237,216,132))
    return np.asarray(pil)


def uv_to_xy(u,v):
    v4=HOM@np.array([u,v,1.],dtype=float)
    return tuple((v4[:2]/v4[2]).tolist())


def draw_teacher(img,t,aim):
    c=img
    breath=math.sin(t*2.1)*2
    bounce=math.sin(t*.85)*2
    x=207+int(math.sin(t*.52)*2)
    yoffset=int(bounce)
    # cast shadow on floor
    ellipse(c,(218,664),(123,22),(105,71,45))
    ellipse(c,(223,656),(98,13),(120,82,52))
    # shoes, trousers and shadowed hem
    roundline(c,(181,544+yoffset),(171,635+yoffset),39,(38,57,78))
    roundline(c,(246,544+yoffset),(246,635+yoffset),39,(43,62,89))
    roundline(c,(174,554+yoffset),(169,628+yoffset),15,(74,92,108))
    roundline(c,(240,555+yoffset),(239,628+yoffset),14,(71,93,114))
    shaded_oval(c,(156,648+yoffset),(44,17),(75,49,39))
    shaded_oval(c,(256,648+yoffset),(44,17),(75,49,39))
    line(c,(121,650+yoffset),(194,652+yoffset),(204,141,78),2)
    line(c,(220,651+yoffset),(295,651+yoffset),(204,141,78),2)
    # left arm with white cuff, holds book
    roundline(c,(169,434+yoffset),(124,500+yoffset),37,(43,87,112))
    roundline(c,(169,430+yoffset),(128,494+yoffset),29,(72,138,154))
    roundline(c,(127,496+yoffset),(127,517+yoffset),24,(197,143,111))
    shaded_oval(c,(126,520+yoffset),(18,19),(222,170,126))
    # book in left hand
    poly(c,[(72,484+yoffset),(145,479+yoffset),(158,548+yoffset),(85,557+yoffset)],(26,52,96))
    poly(c,[(82,486+yoffset),(150,480+yoffset),(162,547+yoffset),(95,553+yoffset)],(45,81,126))
    line(c,(91,500+yoffset),(138,496+yoffset),(238,204,146),3)
    line(c,(95,510+yoffset),(141,506+yoffset),(238,204,146),2)
    poly(c,[(92,536+yoffset),(162,533+yoffset),(161,547+yoffset),(94,550+yoffset)],(209,188,138))
    # torso: three dimensional coat split into central lapels
    poly(c,[(153,415+yoffset),(224,401+yoffset),(272,421+yoffset),(285,542+yoffset),(143,548+yoffset)],(33,72,88))
    poly(c,[(151,411+yoffset),(218,411+yoffset),(235,544+yoffset),(142,547+yoffset)],(74,141,158))
    poly(c,[(219,411+yoffset),(271,420+yoffset),(285,540+yoffset),(236,544+yoffset)],(40,102,126))
    poly(c,[(174,420+yoffset),(226,410+yoffset),(248,537+yoffset),(177,538+yoffset)],(230,217,180))
    poly(c,[(168,416+yoffset),(207,472+yoffset),(177,517+yoffset),(150,425+yoffset)],(87,161,174))
    poly(c,[(250,418+yoffset),(208,475+yoffset),(246,519+yoffset),(275,425+yoffset)],(51,120,144))
    line(c,(209,472+yoffset),(236,535+yoffset),(29,82,102),3)
    shaded_oval(c,(231,502+yoffset),(3,4),(224,185,132))
    # striped tie
    poly(c,[(214,430+yoffset),(229,430+yoffset),(231,448+yoffset),(224,453+yoffset)],(201,95,58))
    poly(c,[(223,450+yoffset),(233,474+yoffset),(229,501+yoffset),(213,480+yoffset)],(204,102,56))
    line(c,(221,457+yoffset),(229,468+yoffset),(239,168,97),2)
    # neck and ears
    shaded_oval(c,(211,412+yoffset),(25,28),(207,151,115))
    shaded_oval(c,(158,330+yoffset),(17,21),(213,158,123))
    shaded_oval(c,(262,328+yoffset),(17,21),(214,158,125))
    # head low-poly ellipse and skin lighting
    shaded_oval(c,(209,333+yoffset),(59,75),(215,170,132))
    # cheek highlights and chin
    ellipse(c,(180,365+yoffset),(13,9),(229,176,133))
    ellipse(c,(239,365+yoffset),(11,8),(226,172,135))
    # hair cap and cowlick
    cv2.ellipse(c,(210,305+yoffset),(60,54),0,180,355,(70,55,46),-1,cv2.LINE_AA)
    poly(c,[(152,297+yoffset),(161,258+yoffset),(198,258+yoffset),(224,267+yoffset),(254,291+yoffset),(259,306+yoffset),(231,289+yoffset),(210,296+yoffset),(192,279+yoffset),(167,300+yoffset)],(72,58,48))
    poly(c,[(159,293+yoffset),(167,266+yoffset),(197,260+yoffset),(215,276+yoffset),(196,273+yoffset),(178,290+yoffset)],(120,84,53))
    # side burn
    ellipse(c,(157,310+yoffset),(8,24),(72,54,43))
    # eyeglasses with live blinking
    line(c,(158,335+yoffset),(178,338+yoffset),(55,54,46),4)
    line(c,(240,338+yoffset),(260,335+yoffset),(55,54,46),4)
    ellipse(c,(189,337+yoffset),(20,18),(40,57,58))
    ellipse(c,(230,337+yoffset),(20,18),(40,57,58))
    ellipse(c,(188,336+yoffset),(17,15),(219,206,161))
    ellipse(c,(230,336+yoffset),(17,15),(221,206,159))
    line(c,(207,333+yoffset),(212,332+yoffset),(57,65,61),4)
    blinking= t%5.8 > 5.60
    if blinking:
        line(c,(177,340+yoffset),(199,340+yoffset),(63,49,39),3)
        line(c,(217,340+yoffset),(239,340+yoffset),(63,49,39),3)
    else:
        shaded_oval(c,(192,340+yoffset),(4,6),(61,69,65))
        shaded_oval(c,(233,340+yoffset),(4,6),(61,69,65))
    # nose nose shiny highlight
    shaded_oval(c,(210,363+yoffset),(11,13),(218,157,118))
    # cheerful professor moustache and smile
    cv2.ellipse(c,(198,383+yoffset),(16,7),-6,180,340,(92,64,48),4,cv2.LINE_AA)
    cv2.ellipse(c,(221,383+yoffset),(16,7),6,200,355,(94,65,49),4,cv2.LINE_AA)
    cv2.ellipse(c,(210,390+yoffset),(16,10),0,15,160,(123,75,59),2,cv2.LINE_AA)
    # right reaching arm angled toward board, with an exaggerated 3d cap
    targetx,targety=aim
    elbow=(305+math.sin(t*1.15)*3,421+yoffset+math.cos(t*.9)*3)
    shoulder=(254,434+yoffset)
    hand=(334+int(math.sin(t*.8)*2),413+yoffset)
    roundline(c,shoulder,elbow,34,(30,75,91))
    roundline(c,shoulder,(elbow[0]-2,elbow[1]-3),25,(53,131,148))
    roundline(c,elbow,hand,25,(45,112,125))
    line(c,(306,411+yoffset),(327,409+yoffset),(143,198,186),3)
    roundline(c,(hand[0]-5,hand[1]),hand,24,(228,198,147))
    shaded_oval(c,(hand[0]+3,hand[1]+2),(16,15),(221,171,129))
    # tapering pointer rod, casts a shadow on chalkboard (3D cue)
    anchor=(hand[0]+11,hand[1]-3)
    tip=(targetx,targety)
    line(c,(anchor[0]+3,anchor[1]+4),(tip[0]+3,tip[1]+4),(8,27,29),7)
    line(c,anchor,tip,(101,62,31),8)
    line(c,anchor,tip,(210,157,79),4)
    line(c,(anchor[0]+2,anchor[1]-2),(tip[0],tip[1]),(255,217,143),1)
    shaded_oval(c,tip,(5,5),(242,213,157))
    # pointing tip golden light dot reflected from chalk
    ellipse(c,(tip[0]+3,tip[1]-3),(2,2),(255,237,172))
    return c


def make_audio(path):
    sr=22050
    t=np.arange(int(sr*DURATION),dtype=np.float64)/sr
    signal=np.zeros_like(t)
    # quiet original SID-flavored chip notes, choppy arpeggiated triangular/square synthesis
    notes=[261.63,329.63,392,523.25,392,329.63,293.66,349.23,440,587.33,440,349.23,261.63,329.63,392,659.26,
           587.33,440,392,329.63,261.63,329.63,392,523.25,587.33,523.25,440,392,329.63,293.66,261.63,196]
    def add_note(s,d,f,v):
        start=int(sr*s); n=min(int(sr*d),len(signal)-start)
        if n<=0:return
        tau=np.arange(n)/sr
        osc=(2/np.pi)*np.arcsin(np.sin(2*np.pi*f*tau))
        osc += .18*np.sign(np.sin(2*np.pi*2*f*tau))
        env=(1-np.exp(-tau*45))*(np.exp(-tau/(d*.65)))*(np.maximum(0,np.minimum(1,(d-tau)/.045)))
        signal[start:start+n]+=v*env*osc
    for i in range(int(DURATION/.35)):
        if i%8==7:continue
        add_note(i*.35,.30,notes[i%len(notes)]*.5,.055)
    for at in [1.15,2.45,3.75,5.05,6.30,7.7]:
        add_note(at,.065,850,.05)
    for at in [8.55,9.15,9.75,10.35,10.95,11.55,12.15,13.05]:
        add_note(at,.14,700+80*(int(at)%3),.058)
    for i,f in enumerate([523,659,784,1047]):
        add_note(13.8+i*.12,.34,f,.075)
    # normalize and fade ends
    signal*=np.minimum(1,np.minimum(t/.4,(DURATION-t)/.9))
    signal=np.clip(signal,-.8,.8)
    with wave.open(path,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(sr)
        wav.writeframes((signal*32767).astype(np.int16).tobytes())


def render_frame(t):
    frame=BASEBG.copy()
    tex=animated_board_texture(t)
    warp=cv2.warpPerspective(tex,local_H,(cx1-cx0,cy1-cy0),flags=cv2.INTER_LINEAR)
    sub=frame[cy0:cy1,cx0:cx1]
    sub[:]=np.uint8(warp.astype(np.float32)*board_alpha+sub.astype(np.float32)*(1-board_alpha))
    # corner nail accents, small light chalk dust near pointer
    if t<1.10: aimuv=(145,188)
    elif t<8: aimuv=(145,line_y[min(4,max(0,int((t-1.15)/1.3)))]+22)
    elif t<13: aimuv=(165,line_y[min(4,max(0,int((t-8.6)/.9)))]+22)
    else: aimuv=(87,452)
    aim=uv_to_xy(*aimuv)
    # soft pointer dust before foreground character
    if t<8.8:
        rng=np.random.default_rng(int(t*24)+57)
        for i in range(9):
            xx=aim[0]+rng.uniform(-13,13);yy=aim[1]+rng.uniform(-13,13)
            r=int(rng.integers(1,3))
            ellipse(frame,(xx,yy),(r,r),(157,190,157))
    draw_teacher(frame,t,aim)
    # screen-space film edge / vignette
    if t<=2.5:
        # opening classroom caption in foreground
        alpha=min(1,max(0,(t-.35)/.5))*min(1,max(0,(2.65-t)/.5))
        if alpha>0:
            p=Image.fromarray(frame)
            canvas=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(canvas)
            f=font(FONT_SANS,27)
            x,y=432,633
            d.rounded_rectangle((x-18,y-11,x+645,y+52),16,fill=(17,41,43,int(186*alpha)))
            d.text((x,y),'LERNEN WIE 1984  •  DER C64 IM UNTERRICHT',font=f,fill=(246,220,155,int(255*alpha)))
            p=Image.alpha_composite(p.convert('RGBA'),canvas)
            frame=np.asarray(p.convert('RGB')).copy()
    if t>14.05:
        a=min(1,(t-14.05)/.7)
        p=Image.fromarray(frame)
        canvas=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(canvas)
        d.rounded_rectangle((520,627,1137,686),radius=18,fill=(22,48,48,int(195*a)))
        d.text((549,639),'GUT GEMACHT!  PROGRAMM BEENDET.',font=font(FONT_SANS,24),fill=(238,233,178,int(255*a)))
        frame=np.asarray(Image.alpha_composite(p.convert('RGBA'),canvas).convert('RGB')).copy()
    return frame


def render():
    audio='/mnt/data/c64_basic_tafel_audio.wav'
    make_audio(audio)
    # encode video stream via ffmpeg (lossless-ish input rgb24; h264/yuv420p playback compatible)
    temp='/mnt/data/c64_basic_render_temp.mp4'
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-', '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',temp]
    ff=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for j in range(DURATION*FPS):
        t=j/FPS
        frame=render_frame(t)
        if j==int(11*FPS):
            Image.fromarray(frame).save(PREVIEW)
        try:ff.stdin.write(frame.tobytes())
        except BrokenPipeError:
            raise RuntimeError(ff.stderr.read().decode('utf-8','replace'))
        if j%48==0: print('Rendering',j,'/',DURATION*FPS,flush=True)
    ff.stdin.close()
    err=ff.stderr.read().decode('utf8','replace')
    res=ff.wait()
    if res!=0: raise RuntimeError('ffmpeg failed: '+err)
    mux=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',temp,'-i',audio,'-c:v','copy','-c:a','aac','-b:a','128k','-shortest','-movflags','+faststart',OUT]
    subprocess.run(mux,check=True)
    os.remove(temp)
    print('Created',OUT,os.path.getsize(OUT),flush=True)

if __name__=='__main__':
    render()
