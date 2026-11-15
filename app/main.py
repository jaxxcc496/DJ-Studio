import os, json, math, random, time, threading
from audio_engine import AudioEngine
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox

APP_DIR = os.path.join(os.path.expanduser("~"), ".dj_studio")
os.makedirs(APP_DIR, exist_ok=True)
DATA_FILE = os.path.join(APP_DIR, "library.json")

THEMES = {
 "VirtualDJ Black": {"bg":"#080a0e","panel":"#11151c","panel2":"#202733","line":"#303b49","fg":"#f2f5fa","muted":"#9aa8b8","accent":"#36a9ff","hot":"#ff4d70"},
 "Midnight": {"bg":"#0b1018","panel":"#151e2b","panel2":"#202d3d","line":"#2d3c50","fg":"#edf4ff","muted":"#91a4bb","accent":"#25d6c5","hot":"#ff5378"},
 "VirtualDJ Grey": {"bg":"#17191e","panel":"#242932","panel2":"#343c49","line":"#465160","fg":"#f4f6f9","muted":"#aeb8c5","accent":"#ff9e36","hot":"#ff5378"},
 "Rekordbox Blue": {"bg":"#081525","panel":"#11243a","panel2":"#1b3552","line":"#294866","fg":"#eef7ff","muted":"#9bb7d2","accent":"#39aaff","hot":"#ff5378"},
 "Purple": {"bg":"#130f20","panel":"#211a32","panel2":"#302544","line":"#49365f","fg":"#f8f0ff","muted":"#b9a8ce","accent":"#c28aff","hot":"#ff668d"}
}

class DJStudio(tk.Tk):
 def __init__(self):
  super().__init__()
  self.title("DJ Studio")
  self.geometry("1440x900")
  self.minsize(1120,740)
  self.theme_name=tk.StringVar(value="VirtualDJ Black")
  self.queue=[]
  self.tracks=[]; self.playlists={"All Tracks":[]}; self.current_playlist="All Tracks"
  self.deck_tracks={"A":None,"B":None}; self.cue_points={"A":[],"B":[]}
  self.deck_started={"A":None,"B":None}; self.deck_duration={"A":0.0,"B":0.0}
  self.deck_sounds={"A":None,"B":None}; self.deck_channels={"A":None,"B":None}
  self.deck_cues={"A":{},"B":{}}; self.deck_play_offset={"A":0.0,"B":0.0}
  self.deck_loop_sound={"A":None,"B":None}; self.deck_loop_active={"A":False,"B":False}
  self.deck_loop_beats={"A":4,"B":4}
  self.deck_playing_sound={"A":None,"B":None}
  self.deck_gain={"A":1.0,"B":1.0}; self.crossfade=0.0
  self.jog_drag={"A":None,"B":None}
  self.analysis_cache={}; self.deck_waveforms={"A":[],"B":[]}; self.deck_bpms={"A":None,"B":None}
  self.audio_engine=AudioEngine()
  self.audio_ready=self.audio_engine.start()
  if not self.audio_ready:self.audio_error=self.audio_engine.error or "Audio output unavailable"
  self.deck_pitch={"A":0.0,"B":0.0}
  self.loop_state={"A":False,"B":False}; self.fx_state={}
  self.status=tk.StringVar(value="WELCOME  •  Add music to your library to prepare a set")
  self.load_data()
  self.build()
  self.apply_theme()

 def load_data(self):
  try:
   with open(DATA_FILE,"r",encoding="utf-8") as f:
    d=json.load(f); self.tracks=d.get("tracks",[]); self.playlists=d.get("playlists",{"All Tracks":[]})
    self.theme_name.set(d.get("theme","VirtualDJ Black"))
    if "All Tracks" not in self.playlists: self.playlists["All Tracks"]=list(self.tracks)
   self.current_playlist="All Tracks"
  except Exception: pass

 def save_data(self):
  try:
   with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump({"tracks":self.tracks,"playlists":self.playlists,"theme":self.theme_name.get()},f,indent=2)
   self.set_status("Library and playlists saved on this computer")
  except Exception as e: self.set_status("Could not save library: "+str(e))

 def set_status(self,s): self.status.set(s)
 def frame(self,parent,**kw): return tk.Frame(parent,bd=0,**kw)
 def label(self,parent,text,**kw): return tk.Label(parent,text=text,bd=0,**kw)
 def button(self,parent,text,command=None,**kw):
  b=tk.Button(parent,text=text,command=command,bd=0,relief="flat",cursor="hand2",font=("Segoe UI",9,"bold"),padx=10,pady=7,**kw); return b

 def build(self):
  self.configure(padx=12,pady=10)
  self.top=self.frame(self); self.top.pack(fill="x",pady=(0,10))
  self.brand=self.label(self.top,text="DJ",font=("Segoe UI",23,"bold")); self.brand.pack(side="left")
  self.brand2=self.label(self.top,text="STUDIO",font=("Segoe UI",23)); self.brand2.pack(side="left",padx=(3,18))
  self.tag=self.label(self.top,text="PERFORMANCE  /  LIBRARY  /  CREATIVE",font=("Segoe UI",8,"bold")); self.tag.pack(side="left",pady=(10,0))
  self.theme_var=self.theme_name
  self.theme_box=ttk.Combobox(self.top,textvariable=self.theme_var,values=list(THEMES),state="readonly",width=17); self.theme_box.pack(side="right",padx=5)
  self.theme_box.bind("<<ComboboxSelected>>",lambda e:self.apply_theme())
  self.settings_btn=self.button(self.top,"SETTINGS",self.open_settings); self.settings_btn.pack(side="right",padx=(8,2))
  self.theme_label=self.label(self.top,text="THEME",font=("Segoe UI",8,"bold")); self.theme_label.pack(side="right",padx=6)

  self.rhythm_wave=tk.Canvas(self,height=112,bd=0,highlightthickness=0)
  self.rhythm_wave.pack(fill="x",pady=(0,8))
  self.deck_row=self.frame(self); self.deck_row.pack(fill="x",pady=(0,9))
  self.deck_ui={}
  for key in ("A","B"): self.build_deck(self.deck_row,key)
  self.beatmatch_label=self.label(self,"BEATMATCH  •  Load tracks in both decks to compare BPM",font=("Segoe UI",10,"bold"),anchor="center")
  self.beatmatch_label.pack(fill="x",pady=(0,8))

  self.middle=self.frame(self); self.middle.pack(fill="both",expand=True)
  self.sidebar=self.frame(self.middle,width=205,padx=10,pady=10); self.sidebar.pack(side="left",fill="y",padx=(0,8)); self.sidebar.pack_propagate(False)
  self.label(self.sidebar,"COLLECTION",font=("Segoe UI",11,"bold")).pack(anchor="w",pady=(2,10))
  self.playlist_box=tk.Listbox(self.sidebar,bd=0,highlightthickness=0,activestyle="none",font=("Segoe UI",10),height=12,exportselection=False)
  self.playlist_box.pack(fill="both",expand=True); self.playlist_box.bind("<<ListboxSelect>>",self.choose_playlist)
  self.button(self.sidebar,"＋  NEW PLAYLIST",self.new_playlist).pack(fill="x",pady=(9,4))
  self.button(self.sidebar,"RENAME",self.rename_playlist).pack(fill="x",pady=3)
  self.button(self.sidebar,"DELETE",self.delete_playlist).pack(fill="x",pady=3)
  self.button(self.sidebar,"SAVE LIBRARY",self.save_data).pack(fill="x",pady=(12,3))
  self.label(self.sidebar,"UP NEXT",font=("Segoe UI",10,"bold")).pack(anchor="w",pady=(18,6))
  self.queue_box=tk.Listbox(self.sidebar,bd=0,highlightthickness=0,activestyle="none",font=("Segoe UI",9),height=7,exportselection=False)
  self.queue_box.pack(fill="both",expand=False)
  self.button(self.sidebar,"PLAY NEXT",self.play_next).pack(fill="x",pady=(6,3))
  self.button(self.sidebar,"CLEAR QUEUE",self.clear_queue).pack(fill="x",pady=3)

  self.library_panel=self.frame(self.middle,padx=12,pady=10); self.library_panel.pack(side="left",fill="both",expand=True)
  libhead=self.frame(self.library_panel); libhead.pack(fill="x")
  self.label(libhead,"MUSIC LIBRARY",font=("Segoe UI",14,"bold")).pack(side="left")
  self.button(libhead,"＋ ADD TRACKS",self.add_music).pack(side="right")
  self.search=tk.StringVar()
  self.search_entry=tk.Entry(self.library_panel,textvariable=self.search,bd=0,font=("Segoe UI",10),insertbackground="white")
  self.search_entry.pack(fill="x",pady=(10,8),ipady=8); self.search_entry.bind("<KeyRelease>",lambda e:self.refresh_tracks())
  table_wrap=self.frame(self.library_panel); table_wrap.pack(fill="both",expand=True)
  self.table=ttk.Treeview(table_wrap,columns=("track","bpm","duration","folder"),show="headings",selectmode="browse")
  self.table.heading("track",text="TRACK TITLE"); self.table.heading("bpm",text="BPM"); self.table.heading("duration",text="LENGTH"); self.table.heading("folder",text="FILE LOCATION")
  self.table.column("track",width=270); self.table.column("bpm",width=65,anchor="center"); self.table.column("duration",width=80,anchor="center"); self.table.column("folder",width=260)
  table_scroll=ttk.Scrollbar(table_wrap,orient="vertical",command=self.table.yview)
  self.table.configure(yscrollcommand=table_scroll.set)
  self.table.pack(side="left",fill="both",expand=True); table_scroll.pack(side="right",fill="y")
  self.table.bind("<Double-1>",lambda e:self.load_to("A"))
  actionrow=self.frame(self.library_panel); actionrow.pack(fill="x",pady=(8,0))
  self.button(actionrow,"LOAD → DECK A",lambda:self.load_to("A")).pack(side="left",padx=(0,5))
  self.button(actionrow,"LOAD → DECK B",lambda:self.load_to("B")).pack(side="left",padx=5)
  self.button(actionrow,"＋ QUEUE",self.add_to_queue).pack(side="left",padx=5)
  self.button(actionrow,"＋ PLAYLIST",self.add_to_playlist).pack(side="left",padx=5)
  self.button(actionrow,"REMOVE",self.remove_track).pack(side="left",padx=5)

  self.bottom=self.frame(self); self.bottom.pack(fill="x",pady=(9,0))
  self.mixer_panel=self.frame(self.bottom,padx=12,pady=9); self.mixer_panel.pack(side="left",fill="both",expand=True,padx=(0,7))
  self.label(self.mixer_panel,"MIXER  •  AUDIO LEVELS",font=("Segoe UI",10,"bold")).pack(anchor="w")
  controls=self.frame(self.mixer_panel); controls.pack(fill="x",pady=(5,0))
  self.eq_controls={}
  for name in ("GAIN A","LOW A","MID A","HIGH A","CROSSFADER","HIGH B","MID B","LOW B","GAIN B"):
   col=self.frame(controls); col.pack(side="left",expand=True,fill="x",padx=3)
   self.label(col,name,font=("Segoe UI",7,"bold")).pack()
   if name=="GAIN A":
    sc=tk.Scale(col,from_=100,to=0,orient="vertical",length=78,showvalue=False,bd=0,highlightthickness=0,command=lambda v,k="A":self.set_deck_gain(k,v)); sc.set(100); sc.pack()
   elif name=="GAIN B":
    sc=tk.Scale(col,from_=100,to=0,orient="vertical",length=78,showvalue=False,bd=0,highlightthickness=0,command=lambda v,k="B":self.set_deck_gain(k,v)); sc.set(100); sc.pack()
   elif name=="CROSSFADER":
    sc=tk.Scale(col,from_=-100,to=100,orient="horizontal",length=100,showvalue=False,bd=0,highlightthickness=0,command=self.set_crossfade); sc.set(100); sc.pack()
   else:
    sc=tk.Scale(col,from_=100,to=0,orient="vertical",length=78,showvalue=False,bd=0,highlightthickness=0,command=lambda v,n=name:self.set_eq_control(n,v)); sc.set(50); sc.pack()
    self.eq_controls[name]=sc
  self.sampler_panel=self.frame(self.bottom,width=290,padx=10,pady=9); self.sampler_panel.pack(side="right",fill="y"); self.sampler_panel.pack_propagate(False)
  self.label(self.sampler_panel,"SAMPLE PADS",font=("Segoe UI",10,"bold")).pack(anchor="w")
  pads=self.frame(self.sampler_panel); pads.pack(fill="both",expand=True,pady=5)
  for i in range(8):
   b=self.button(pads,"SAMPLE "+str(i+1),lambda n=i+1:self.set_status("Sample pad "+str(n)+" selected — audio sampler not connected yet"))
   b.grid(row=i//4,column=i%4,sticky="nsew",padx=3,pady=3)
  for i in range(4): pads.columnconfigure(i,weight=1)
  for i in range(2): pads.rowconfigure(i,weight=1)
  self.statusbar=tk.Label(self,textvariable=self.status,font=("Segoe UI",8),anchor="w",padx=10,pady=7,bd=0); self.statusbar.pack(fill="x",pady=(8,0))
  self.refresh_playlists(); self.refresh_tracks(); self.refresh_queue()
  self.after(50,self.update_deck_displays)

 def build_deck(self,parent,key):
  p=self.frame(parent,padx=12,pady=10); p.pack(side="left",fill="both",expand=True,padx=4)
  head=self.frame(p); head.pack(fill="x")
  self.label(head,"DECK "+key,font=("Segoe UI",13,"bold")).pack(side="left")
  self.label(head,"●  READY",font=("Segoe UI",8,"bold")).pack(side="right")
  title=self.label(p,"No track loaded",font=("Segoe UI",11,"bold"),anchor="w"); title.pack(fill="x",pady=(8,0))
  time=self.label(p,"00:00 / 00:00  •  LEFT 00:00",font=("Segoe UI",10,"bold")); time.pack(anchor="w")
  bpm=self.label(p,"BPM  —",font=("Segoe UI",11,"bold")); bpm.pack(anchor="w",pady=(2,0))
  wave=tk.Canvas(p,height=64,bd=0,highlightthickness=0); wave.pack(fill="x",pady=(4,6))
  row=self.frame(p); row.pack(fill="x")
  jog=tk.Canvas(row,width=116,height=116,bd=0,highlightthickness=0); jog.pack(side="left",padx=(0,12))
  jog.bind("<Button-1>",lambda e,k=key:self.jog_start(k,e))
  jog.bind("<B1-Motion>",lambda e,k=key:self.jog_move(k,e))
  jog.bind("<ButtonRelease-1>",lambda e,k=key:self.jog_end(k,e))
  right=self.frame(row); right.pack(side="left",fill="both",expand=True)
  btns=self.frame(right); btns.pack(anchor="w",pady=2)
  self.button(btns,"LOAD",lambda k=key:self.load_to(k)).pack(side="left",padx=2)
  cue_btn=self.button(btns,"CUE")
  cue_btn.pack(side="left",padx=2)
  cue_btn.bind("<ButtonPress-1>",lambda e,k=key:self.cue_hold_start(k))
  cue_btn.bind("<ButtonRelease-1>",lambda e,k=key:self.cue_hold_end(k))
  self.deck_play_button=self.deck_play_button if hasattr(self,"deck_play_button") else {}
  play_btn=self.button(btns,"▶ PLAY",lambda k=key:self.toggle_deck(k))
  play_btn.pack(side="left",padx=2)
  self.deck_play_button[key]=play_btn
  row2=self.frame(right); row2.pack(fill="x",pady=4)
  for t in ("− PITCH","＋ PITCH","SYNC"):
   self.button(row2,t,lambda x=t,k=key:self.adjust_pitch(k,-0.5 if x=="− PITCH" else 0.5) if x!="SYNC" else self.sync_deck(k)).pack(side="left",padx=2)
  self.button(row2,"− LOOP",lambda k=key:self.change_loop_beats(k,-1)).pack(side="left",padx=2)
  self.loop_labels=self.loop_labels if hasattr(self,"loop_labels") else {}
  loop_label=self.label(row2,"4 BEATS",font=("Segoe UI",8,"bold")); loop_label.pack(side="left",padx=3)
  self.loop_labels[key]=loop_label
  self.button(row2,"＋ LOOP",lambda k=key:self.change_loop_beats(k,1)).pack(side="left",padx=2)
  self.button(row2,"LOOP ON/OFF",lambda k=key:self.toggle_loop(k)).pack(side="left",padx=2)
  cue=self.frame(right); cue.pack(anchor="w",pady=4)
  for n in range(1,5): self.button(cue,"HOT CUE "+str(n),lambda k=key,x=n:self.set_hot_cue(k,str(x))).pack(side="left",padx=2)
  self.deck_ui[key]={"panel":p,"title":title,"time":time,"bpm":bpm,"wave":wave,"jog":jog}

 def format_time(self,seconds):
  seconds=max(0,int(seconds)); return "%02d:%02d"%(seconds//60,seconds%60)

 def draw_rhythm_wave(self):
  if not hasattr(self,"rhythm_wave") or not hasattr(self,"deck_ui"): return
  cv=self.rhythm_wave
  c=THEMES[self.theme_name.get()]
  cv.delete("all")
  w=max(500,cv.winfo_width()); h=112
  cv.create_rectangle(0,0,w,h,fill="#080d15",outline=c["line"])
  row_h=52
  colors={"A":"#28b8ff","B":"#ff526d"}
  for row,key in enumerate(("A","B")):
   y0=row*56
   cv.create_line(0,y0+row_h,w,y0+row_h,fill="#263343")
   path=self.deck_tracks.get(key)
   values=self.deck_waveforms.get(key,[])
   duration=self.deck_duration.get(key,0.0)
   if not path or not values or duration<=0:
    cv.create_text(10,y0+row_h/2,text="DECK "+key+"  •  LOAD A TRACK TO VIEW WAVEFORM",anchor="w",fill="#77889b",font=("Segoe UI",8,"bold"))
    continue
   pos=self.current_position(key)
   window=14.0
   start=max(0.0,pos-window/2)
   end=min(duration,start+window)
   if end-start<window: start=max(0.0,end-window)
   span=max(0.001,end-start)
   bars=max(1,w//5)
   for x in range(bars):
    t=start+(x/max(1,bars-1))*span
    idx=max(0,min(len(values)-1,int((t/duration)*len(values))))
    amp=max(1,min(21,int(values[idx]*21)))
    px=int(x*w/bars)
    cv.create_line(px,y0+row_h/2-amp,px,y0+row_h/2+amp,fill=colors[key],width=3)
   bpm=self.deck_bpms.get(key)
   if bpm and bpm>0:
    beat=60.0/bpm
    first=math.ceil(start/beat)
    last=int(end/beat)
    for n in range(first,last+1):
     x=int(((n*beat-start)/span)*w)
     if 0<=x<w: cv.create_line(x,y0+3,x,y0+row_h-3,fill="#42546a",width=1,dash=(2,4))
   center=w//2
   cv.create_line(center,y0+2,center,y0+row_h-2,fill="#ffffff",width=2)
   cv.create_text(8,y0+4,text="A" if key=="A" else "B",anchor="nw",fill=colors[key],font=("Segoe UI",8,"bold"))
  cv.create_text(w-8,4,text="LIVE RHYTHM WAVEFORM",anchor="ne",fill="#aab8c8",font=("Segoe UI",7,"bold"))

 def update_deck_displays(self):
  a=self.deck_bpms.get("A");b=self.deck_bpms.get("B")
  if a and b:self.beatmatch_label.configure(text="BEATMATCH • A %.1f BPM | B %.1f BPM | DIFFERENCE %.1f BPM"%(a,b,abs(a-b)))
  else:self.beatmatch_label.configure(text="BEATMATCH • Load and analyse tracks in both decks")
  self.draw_rhythm_wave()
  for k in ("A","B"):
   if self.deck_started[k] is not None:
    p=self.current_position(k);left=max(0,self.deck_duration[k]-p)
    self.deck_ui[k]["time"].configure(text=self.format_time(p)+" / "+self.format_time(self.deck_duration[k])+" • LEFT "+self.format_time(left))
    self.draw_wave(k)
    if left<=0 and not self.deck_loop_active[k]:self.deck_started[k]=None;self.deck_play_button[k].configure(text="▶ PLAY")
  self.after(50,self.update_deck_displays)

 def draw_wave(self,key):
  c=THEMES[self.theme_name.get()]; cv=self.deck_ui[key]["wave"]; cv.delete("all")
  w=max(cv.winfo_width(),420); h=64; mid=h//2
  cv.create_rectangle(0,0,w,h,fill=c["panel"],outline="")
  values=self.deck_waveforms.get(key,[])
  if values:
   step=max(1,len(values)//max(1,w//3))
   for x in range(0,w,3):
    idx=min(len(values)-1,int(x/max(1,w)*len(values)))
    amp=max(2,min(28,int(values[idx]*28)))
    cv.create_line(x,mid-amp,x,mid+amp,fill=c["accent"],width=2)
   cv.create_text(8,6,text="ANALYSED AUDIO",anchor="nw",fill=c["muted"],font=("Segoe UI",7,"bold"))
  else:
   cv.create_text(8,7,text="ANALYSING AUDIO WHEN TRACK IS LOADED",anchor="nw",fill=c["muted"],font=("Segoe UI",7,"bold"))
  duration=self.deck_duration.get(key,0.0) or 0.0
  pos=0.0
  if self.deck_started.get(key) is not None:
   pos=self.deck_play_offset.get(key,0.0)+max(0,time.monotonic()-self.deck_started[key])
   if self.deck_loop_active.get(key) and self.deck_loop_sound.get(key):
    loop_len=self.deck_loop_sound[key].get_length()
    if loop_len>0: pos=self.deck_play_offset.get(key,0.0)+(pos-self.deck_play_offset.get(key,0.0))%loop_len
  for name,stamp in self.deck_cues.get(key,{}).items():
   if duration>0:
    cx=max(0,min(w,int(stamp/duration*w)))
    cv.create_line(cx,2,cx,h-2,fill=c["hot"],width=1)
  if duration>0:
   px=max(0,min(w,int(pos/duration*w)))
   cv.create_line(px,1,px,h-1,fill="#ffffff",width=2)

 def analyse_track(self,path,key):
  if path in self.analysis_cache:
   self.apply_analysis(path,key,*self.analysis_cache[path]); return
  def worker():
   try:
    import librosa
    import numpy as np
    audio,sr=librosa.load(path,sr=8000,mono=True)
    rms=librosa.feature.rms(y=audio,frame_length=1024,hop_length=512)[0]
    peak=float(max(rms)) if len(rms) else 0.0
    waveform=[float(v/peak) if peak else 0.0 for v in rms]
    onset=librosa.onset.onset_strength(y=audio,sr=sr,hop_length=512)
    tempo_values=librosa.feature.tempo(onset_envelope=onset,sr=sr,hop_length=512,aggregate=None)
    tempo=float(np.median(tempo_values)) if len(tempo_values) else 0.0
    bpm=float(tempo)
    if 70 <= bpm/2 <= 180 and bpm>180: bpm/=2.0
    elif bpm<70 and bpm*2<=180: bpm*=2.0
    if not 70 <= bpm <= 180: bpm=None
    result=(waveform,bpm)
   except Exception as e:
    result=([],None)
    error=str(e)
   else: error=None
   self.analysis_cache[path]=result
   try: self.after(0,lambda:self.apply_analysis(path,key,*result,error=error))
   except Exception: pass
  threading.Thread(target=worker,daemon=True).start()

 def apply_analysis(self,path,key,waveform,bpm,error=None):
  if self.deck_tracks.get(key)==path:
   self.deck_waveforms[key]=waveform
   self.deck_bpms[key]=bpm
   self.deck_ui[key]["bpm"].configure(text=("BPM  %.1f"%bpm) if bpm else "BPM  not detected")
   self.draw_wave(key)
  if error:
   self.set_status("Audio analysis unavailable for "+os.path.basename(path)+": "+error[:100])
  else:
   self.set_status("Audio waveform analysed: "+os.path.basename(path))
  if hasattr(self,"table"):
   for item in self.table.get_children():
    if self.table.item(item,"values") and item==path:
     vals=list(self.table.item(item,"values")); vals[1]=("%.1f"%bpm) if bpm else "—"; self.table.item(item,values=vals)

 def draw_jog(self,key):
  c=THEMES[self.theme_name.get()]; cv=self.deck_ui[key]["jog"]; cv.delete("all")
  cv.create_oval(4,4,112,112,fill="#080b10",outline=c["line"],width=3)
  cv.create_oval(13,13,103,103,fill="#202a38",outline=c["muted"],width=1)
  for angle in range(0,360,15):
   rad=math.radians(angle); x1=58+39*math.cos(rad); y1=58+39*math.sin(rad); x2=58+44*math.cos(rad); y2=58+44*math.sin(rad)
   cv.create_line(x1,y1,x2,y2,fill=c["muted"],width=1)
  cv.create_oval(35,35,81,81,fill=c["panel2"],outline=c["accent"],width=2)
  cv.create_text(58,58,text=key,fill=c["fg"],font=("Segoe UI",14,"bold"))
  cv.create_text(58,94,text="JOG",fill=c["muted"],font=("Segoe UI",7,"bold"))

 def refresh_queue(self):
  if not hasattr(self,"queue_box"): return
  self.queue_box.delete(0,"end")
  for path in self.queue: self.queue_box.insert("end",os.path.basename(path))

 def add_to_queue(self):
  path=self.selected()
  if not path:
   self.set_status("Select a track in the library first"); return
  self.queue.append(path); self.refresh_queue()
  self.set_status(os.path.basename(path)+" added to queue")

 def clear_queue(self):
  self.queue.clear(); self.refresh_queue(); self.set_status("Queue cleared")

 def play_next(self):
  if not self.queue:self.set_status("Queue is empty");return
  path=self.queue.pop(0);self.refresh_queue();self.load_track_path("A",path);self.play_deck("A")

 def open_settings(self):
  win=tk.Toplevel(self); win.title("DJ Studio Settings"); win.geometry("440x300"); win.resizable(False,False)
  c=THEMES[self.theme_name.get()]; win.configure(bg=c["bg"])
  tk.Label(win,text="SETTINGS",bg=c["bg"],fg=c["fg"],font=("Segoe UI",18,"bold")).pack(anchor="w",padx=22,pady=(20,4))
  tk.Label(win,text="Appearance and library",bg=c["bg"],fg=c["muted"],font=("Segoe UI",9)).pack(anchor="w",padx=22)
  body=tk.Frame(win,bg=c["panel"],padx=18,pady=18); body.pack(fill="both",expand=True,padx=18,pady=18)
  tk.Label(body,text="INTERFACE THEME",bg=c["panel"],fg=c["fg"],font=("Segoe UI",9,"bold")).pack(anchor="w")
  choice=tk.StringVar(value=self.theme_name.get())
  combo=ttk.Combobox(body,textvariable=choice,values=list(THEMES),state="readonly"); combo.pack(fill="x",pady=(8,16))
  def apply():
   self.theme_name.set(choice.get()); self.theme_box.set(choice.get()); self.apply_theme(); self.save_data(); win.destroy()
  tk.Button(body,text="APPLY AND SAVE",command=apply,bg=c["accent"],fg="#06111c",relief="flat",font=("Segoe UI",9,"bold"),padx=12,pady=9).pack(anchor="e")

 def add_music(self):
  paths=filedialog.askopenfilenames(title="Add music",filetypes=[("Audio files","*.mp3 *.wav *.flac *.aiff *.aif *.ogg *.m4a"),("All files","*.*")])
  count=0
  for path in paths:
   if path not in self.tracks: self.tracks.append(path); self.playlists.setdefault("All Tracks",[]).append(path); count+=1
  self.refresh_tracks(); self.save_data(); self.set_status(str(count)+" tracks added")
 def refresh_tracks(self):
  if not hasattr(self,"table"):return
  for i in self.table.get_children():self.table.delete(i)
  for path in self.playlists.get(self.current_playlist,[]):
   name=os.path.basename(path)
   if self.search.get().lower() in name.lower():
    length="—"
    try:
     import soundfile as sf
     length=self.format_time(sf.info(path).duration)
    except Exception:pass
    bpm=self.analysis_cache.get(path,([],None))[1]
    self.table.insert("","end",iid=path,values=(name,("%.1f"%bpm) if bpm else "—",length,os.path.dirname(path)))

 def refresh_playlists(self):
  if not hasattr(self,"playlist_box"): return
  self.playlist_box.delete(0,"end")
  for name in self.playlists: self.playlist_box.insert("end",name)
  names=list(self.playlists)
  if self.current_playlist in names:
   i=names.index(self.current_playlist); self.playlist_box.selection_set(i); self.playlist_box.activate(i)
 def choose_playlist(self,e=None):
  s=self.playlist_box.curselection()
  if s: self.current_playlist=self.playlist_box.get(s[0]); self.refresh_tracks()
 def new_playlist(self):
  n=simpledialog.askstring("New playlist","Playlist name:")
  if n and n.strip():
   n=n.strip()
   if n in self.playlists: messagebox.showinfo("Playlist","That playlist already exists"); return
   self.playlists[n]=[]; self.current_playlist=n; self.refresh_playlists(); self.refresh_tracks(); self.save_data()
 def rename_playlist(self):
  old=self.current_playlist
  if old=="All Tracks": messagebox.showinfo("Playlist","All Tracks cannot be renamed"); return
  n=simpledialog.askstring("Rename playlist","New name:",initialvalue=old)
  if n and n.strip() and n.strip() not in self.playlists:
   self.playlists[n.strip()]=self.playlists.pop(old); self.current_playlist=n.strip(); self.refresh_playlists(); self.refresh_tracks(); self.save_data()
 def delete_playlist(self):
  n=self.current_playlist
  if n!="All Tracks" and messagebox.askyesno("Delete playlist","Delete "+n+"? Files remain in All Tracks."):
   del self.playlists[n]; self.current_playlist="All Tracks"; self.refresh_playlists(); self.refresh_tracks(); self.save_data()
 def selected(self):
  s=self.table.selection(); return s[0] if s else None
 def load_track_path(self,key,path):
  self.stop_deck(key,announce=False);self.deck_tracks[key]=path;self.deck_started[key]=None
  try:self.deck_duration[key]=self.audio_engine.load(key,path);self.deck_sounds[key]=True
  except Exception as e:self.deck_sounds[key]=None;self.set_status("Audio file could not be loaded: "+str(e));return
  self.deck_ui[key]["title"].configure(text=os.path.basename(path))
  self.deck_ui[key]["time"].configure(text="00:00 / "+self.format_time(self.deck_duration[key])+" • LEFT "+self.format_time(self.deck_duration[key]))
  self.deck_waveforms[key]=[];self.deck_bpms[key]=None;self.deck_play_offset[key]=0.0
  self.deck_ui[key]["bpm"].configure(text="BPM analysing…");self.draw_wave(key);self.analyse_track(path,key)
  self.set_status(os.path.basename(path)+" loaded into Deck "+key+" — press PLAY")

 def load_to(self,key):
  path=self.selected()
  if not path:self.set_status("Select a track in the library first");return
  self.load_track_path(key,path)

 def toggle_deck(self,key):
  if self.deck_started[key] is not None:
   self.audio_engine.pause(key);self.deck_play_offset[key]=self.audio_engine.position(key);self.deck_started[key]=None
   self.deck_play_button[key].configure(text="▶ PLAY");self.set_status("Deck "+key+" paused")
  else:self.play_deck(key)

 def apply_deck_mix(self,key):
  self.audio_engine.set_gain(key,self.deck_gain.get(key,1.0))

 def set_deck_gain(self,key,value):
  self.deck_gain[key]=max(0.0,min(1.0,float(value)/100.0));self.apply_deck_mix(key)
  self.set_status("Deck "+key+" gain: "+str(int(float(value)))+"%")

 def sync_deck(self,key):
  other="B" if key=="A" else "A";target=self.deck_bpms.get(other);own=self.deck_bpms.get(key)
  if not target or not own or own<=0:self.set_status("SYNC needs analysed tracks in both decks");return
  pct=(target/own-1)*100
  if abs(pct)>30:self.set_status("SYNC target exceeds ±30%");return
  self.deck_pitch[key]=pct;self.audio_engine.set_pitch(key,pct);self.set_status("Deck "+key+" synced to %.1f BPM"%target)

 def adjust_pitch(self,key,delta):
  self.deck_pitch[key]=max(-30.0,min(30.0,self.deck_pitch.get(key,0.0)+delta))
  self.audio_engine.set_pitch(key,self.deck_pitch[key]);self.set_status("Deck "+key+" pitch: %+.1f%%"%self.deck_pitch[key])

 def set_eq_control(self,name,value):
  band="low" if "LOW" in name else ("mid" if "MID" in name else "high")
  deck="A" if name.endswith("A") else "B";self.audio_engine.set_eq(deck,band,(float(value)-50.0)/50.0)

 def set_crossfade(self,value):
  self.crossfade=max(-1.0,min(1.0,float(value)/100.0));self.audio_engine.set_crossfade(self.crossfade)
  self.set_status("Crossfader: "+str(int(float(value))))

 def jog_start(self,key,event):
  if not self.deck_tracks.get(key):
   self.set_status("Load a track into Deck "+key+" before using the jogwheel"); return
  self.jog_drag[key]={"x":event.x,"position":self.current_position(key),"was_playing":bool(self.deck_started.get(key) is not None)}
  self.set_status("Deck "+key+" jog: drag left or right to seek")

 def jog_move(self,key,event):
  state=self.jog_drag.get(key)
  if not state:return
  p=max(0,min(self.deck_duration[key],state["position"]+(event.x-state["x"])*.025))
  self.audio_engine.seek(key,p);self.deck_play_offset[key]=p;self.draw_wave(key)

 def jog_end(self,key,event):
  state=self.jog_drag.get(key)
  if not state:return
  p=self.current_position(key)
  if state["was_playing"]:self.audio_engine.play(key);self.deck_started[key]=time.monotonic();self.deck_play_button[key].configure(text="■ STOP")
  else:self.deck_started[key]=None
  self.jog_drag[key]=None;self.set_status("Deck "+key+" seek: "+self.format_time(p))

 def play_deck(self,key):
  if not self.audio_ready:self.set_status("Audio output unavailable: "+getattr(self,"audio_error","unknown"));return
  if not self.deck_tracks.get(key):self.set_status("Load a track into Deck "+key+" first");return
  self.audio_engine.seek(key,self.deck_play_offset.get(key,0));self.audio_engine.play(key)
  self.deck_started[key]=time.monotonic();self.deck_play_button[key].configure(text="■ STOP")
  self.set_status("Deck "+key+" playing: "+os.path.basename(self.deck_tracks[key]))


 def current_position(self,key):
  return self.audio_engine.position(key) if self.deck_tracks.get(key) else 0.0

 def cue_hold_start(self,key):
  if not self.deck_tracks.get(key):self.set_status("Load a track into Deck "+key+" first");return
  if "CUE" not in self.deck_cues[key]:self.deck_cues[key]["CUE"]=0.0
  p=self.deck_cues[key]["CUE"];self.audio_engine.seek(key,p);self.audio_engine.play(key)
  self.deck_started[key]=time.monotonic();self.deck_play_button[key].configure(text="■ CUE")

 def cue_hold_end(self,key):
  if "CUE" not in self.deck_cues.get(key,{}):return
  self.audio_engine.pause(key);self.audio_engine.seek(key,self.deck_cues[key]["CUE"])
  self.deck_started[key]=None;self.deck_play_button[key].configure(text="▶ PLAY")

 def set_hot_cue(self,key,name):
  if not self.deck_tracks.get(key):
   self.set_status("Load a track into Deck "+key+" first"); return
  if name in self.deck_cues[key]:
   self.deck_play_offset[key]=self.deck_cues[key][name]
   self.deck_loop_active[key]=False; self.deck_loop_sound[key]=None
   self.play_from_position(key,self.deck_play_offset[key])
   self.set_status("Deck "+key+" jumped to cue "+name)
  else:
   self.deck_cues[key][name]=self.current_position(key)
   self.draw_wave(key)
   self.set_status("Deck "+key+" cue "+name+" saved at "+self.format_time(self.deck_cues[key][name]))

 def play_from_position(self,key,position):
  self.audio_engine.seek(key,position);self.audio_engine.play(key);self.deck_started[key]=time.monotonic()
  self.deck_play_button[key].configure(text="■ STOP");self.draw_wave(key)

 def change_loop_beats(self,key,direction):
  sizes=(1,2,4,8,16,32)
  current=self.deck_loop_beats.get(key,4)
  index=sizes.index(current) if current in sizes else 2
  index=max(0,min(len(sizes)-1,index+direction))
  self.deck_loop_beats[key]=sizes[index]
  if hasattr(self,"loop_labels") and key in self.loop_labels:
   self.loop_labels[key].configure(text=str(sizes[index])+" BEATS")
  if self.deck_loop_active.get(key):
   self.toggle_loop(key)
   self.toggle_loop(key)
  self.set_status("Deck "+key+" loop length: "+str(sizes[index])+" beats")

 def toggle_loop(self,key):
  if not self.deck_tracks.get(key):self.set_status("Load a track into Deck "+key+" first");return
  if self.deck_loop_active[key]:self.audio_engine.clear_loop(key);self.deck_loop_active[key]=False;self.set_status("Loop disabled");return
  bpm=self.deck_bpms.get(key)
  if not bpm:self.set_status("Loop needs a detected BPM first");return
  start=self.current_position(key);length=60.0/float(bpm)*self.deck_loop_beats[key];end=min(self.deck_duration[key],start+length)
  if end-start<length*.8:start=max(0,self.deck_duration[key]-length);end=min(self.deck_duration[key],start+length)
  self.audio_engine.set_loop(key,start,end);self.audio_engine.seek(key,start);self.audio_engine.play(key)
  self.deck_loop_active[key]=True;self.deck_started[key]=time.monotonic();self.deck_play_button[key].configure(text="■ STOP")
  self.set_status("Deck "+key+" loop active")

 def stop_deck(self,key,announce=True):
  self.audio_engine.stop(key,reset=True);self.deck_started[key]=None;self.deck_play_offset[key]=0.0;self.deck_loop_active[key]=False
  if hasattr(self,"deck_play_button") and key in self.deck_play_button:self.deck_play_button[key].configure(text="▶ PLAY")
  if announce:self.set_status("Deck "+key+" stopped")

 def add_to_playlist(self):
  p=self.selected()
  if not p: return
  if self.current_playlist=="All Tracks": self.set_status("Select or create a playlist first"); return
  if p not in self.playlists[self.current_playlist]: self.playlists[self.current_playlist].append(p)
  self.refresh_tracks(); self.save_data()
 def remove_track(self):
  p=self.selected()
  if not p:return
  if self.current_playlist=="All Tracks":
   self.tracks.remove(p)
   for arr in self.playlists.values():
    if p in arr: arr.remove(p)
  elif p in self.playlists[self.current_playlist]: self.playlists[self.current_playlist].remove(p)
  self.refresh_tracks(); self.save_data()
 def apply_theme(self):
  c=THEMES[self.theme_name.get()]; self.configure(bg=c["bg"])
  for w in self.winfo_children(): self.paint(w,c)
  st=ttk.Style(self); st.theme_use("clam")
  st.configure("Treeview",background=c["panel"],fieldbackground=c["panel"],foreground=c["fg"],rowheight=30,borderwidth=0)
  st.configure("Treeview.Heading",background=c["panel2"],foreground=c["fg"],font=("Segoe UI",9,"bold"),relief="flat")
  st.map("Treeview",background=[("selected",c["accent"])],foreground=[("selected","#081018")])
  st.configure("TCombobox",fieldbackground=c["panel"],background=c["panel2"],foreground=c["fg"])
  for k in ("A","B"): self.draw_wave(k); self.draw_jog(k)
 def paint(self,w,c):
  if not isinstance(w,ttk.Widget):
   try:w.configure(bg=c["bg"])
   except tk.TclError:pass
   if isinstance(w,tk.Label):
    try:w.configure(fg=c["fg"])
    except tk.TclError:pass
   if isinstance(w,tk.Button):
    w.configure(bg=c["panel2"],fg=c["fg"],activebackground=c["accent"],activeforeground="#071018",relief="flat")
   elif isinstance(w,tk.Entry): w.configure(bg=c["panel"],fg=c["fg"],insertbackground=c["fg"],relief="flat")
   elif isinstance(w,tk.Listbox): w.configure(bg=c["panel"],fg=c["fg"],selectbackground=c["accent"],selectforeground="#071018",relief="flat")
   elif isinstance(w,tk.Scale): w.configure(bg=c["panel"],fg=c["muted"],troughcolor=c["panel2"],activebackground=c["accent"])
   elif isinstance(w,tk.Canvas): w.configure(bg=c["panel"])
  for child in w.winfo_children(): self.paint(child,c)

if __name__=="__main__":
 app=DJStudio()
 try:
  app.mainloop()
 finally:
  try: app.audio_engine.close()
  except Exception: pass
