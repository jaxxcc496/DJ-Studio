import os, json, math, random, time
import pygame
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox

APP_DIR = os.path.join(os.path.expanduser("~"), ".dj_studio")
os.makedirs(APP_DIR, exist_ok=True)
DATA_FILE = os.path.join(APP_DIR, "library.json")

THEMES = {
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
  self.theme_name=tk.StringVar(value="Midnight")
  self.tracks=[]; self.playlists={"All Tracks":[]}; self.current_playlist="All Tracks"
  self.deck_tracks={"A":None,"B":None}; self.cue_points={"A":[],"B":[]}
  self.deck_sounds={"A":None,"B":None}; self.deck_channels={"A":None,"B":None}
  self.audio_ready=False
  try:
   pygame.mixer.init()
   pygame.mixer.set_num_channels(8)
   self.deck_channels={"A":pygame.mixer.Channel(0),"B":pygame.mixer.Channel(1)}
   self.audio_ready=True
  except Exception as e:
   self.audio_error=str(e)
  self.loop_state={"A":False,"B":False}; self.fx_state={}
  self.status=tk.StringVar(value="WELCOME  •  Add music to your library to prepare a set")
  self.load_data()
  self.build()
  self.apply_theme()

 def load_data(self):
  try:
   with open(DATA_FILE,"r",encoding="utf-8") as f:
    d=json.load(f); self.tracks=d.get("tracks",[]); self.playlists=d.get("playlists",{"All Tracks":[]})
    if "All Tracks" not in self.playlists: self.playlists["All Tracks"]=list(self.tracks)
   self.current_playlist="All Tracks"
  except Exception: pass

 def save_data(self):
  try:
   with open(DATA_FILE,"w",encoding="utf-8") as f: json.dump({"tracks":self.tracks,"playlists":self.playlists},f,indent=2)
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
  self.theme_label=self.label(self.top,text="THEME",font=("Segoe UI",8,"bold")); self.theme_label.pack(side="right",padx=6)

  self.deck_row=self.frame(self); self.deck_row.pack(fill="x",pady=(0,9))
  self.deck_ui={}
  for key in ("A","B"): self.build_deck(self.deck_row,key)

  self.middle=self.frame(self); self.middle.pack(fill="both",expand=True)
  self.sidebar=self.frame(self.middle,width=205,padx=10,pady=10); self.sidebar.pack(side="left",fill="y",padx=(0,8)); self.sidebar.pack_propagate(False)
  self.label(self.sidebar,"COLLECTION",font=("Segoe UI",11,"bold")).pack(anchor="w",pady=(2,10))
  self.playlist_box=tk.Listbox(self.sidebar,bd=0,highlightthickness=0,activestyle="none",font=("Segoe UI",10),height=12,exportselection=False)
  self.playlist_box.pack(fill="both",expand=True); self.playlist_box.bind("<<ListboxSelect>>",self.choose_playlist)
  self.button(self.sidebar,"＋  NEW PLAYLIST",self.new_playlist).pack(fill="x",pady=(9,4))
  self.button(self.sidebar,"RENAME",self.rename_playlist).pack(fill="x",pady=3)
  self.button(self.sidebar,"DELETE",self.delete_playlist).pack(fill="x",pady=3)
  self.button(self.sidebar,"SAVE LIBRARY",self.save_data).pack(fill="x",pady=(12,3))

  self.library_panel=self.frame(self.middle,padx=12,pady=10); self.library_panel.pack(side="left",fill="both",expand=True)
  libhead=self.frame(self.library_panel); libhead.pack(fill="x")
  self.label(libhead,"MUSIC LIBRARY",font=("Segoe UI",14,"bold")).pack(side="left")
  self.button(libhead,"＋ ADD TRACKS",self.add_music).pack(side="right")
  self.search=tk.StringVar()
  self.search_entry=tk.Entry(self.library_panel,textvariable=self.search,bd=0,font=("Segoe UI",10),insertbackground="white")
  self.search_entry.pack(fill="x",pady=(10,8),ipady=8); self.search_entry.bind("<KeyRelease>",lambda e:self.refresh_tracks())
  self.table=ttk.Treeview(self.library_panel,columns=("track","folder"),show="headings",selectmode="browse")
  self.table.heading("track",text="TRACK TITLE"); self.table.heading("folder",text="FILE LOCATION")
  self.table.column("track",width=370); self.table.column("folder",width=300)
  self.table.pack(fill="both",expand=True); self.table.bind("<Double-1>",lambda e:self.load_to("A"))
  actionrow=self.frame(self.library_panel); actionrow.pack(fill="x",pady=(8,0))
  self.button(actionrow,"LOAD → DECK A",lambda:self.load_to("A")).pack(side="left",padx=(0,5))
  self.button(actionrow,"LOAD → DECK B",lambda:self.load_to("B")).pack(side="left",padx=5)
  self.button(actionrow,"＋ PLAYLIST",self.add_to_playlist).pack(side="left",padx=5)
  self.button(actionrow,"REMOVE",self.remove_track).pack(side="left",padx=5)

  self.bottom=self.frame(self); self.bottom.pack(fill="x",pady=(9,0))
  self.mixer_panel=self.frame(self.bottom,padx=12,pady=9); self.mixer_panel.pack(side="left",fill="both",expand=True,padx=(0,7))
  self.label(self.mixer_panel,"MIXER  •  LAYOUT PREVIEW",font=("Segoe UI",10,"bold")).pack(anchor="w")
  controls=self.frame(self.mixer_panel); controls.pack(fill="x",pady=(5,0))
  for name in ("GAIN A","LOW A","MID A","HIGH A","CROSSFADER","HIGH B","MID B","LOW B","GAIN B"):
   col=self.frame(controls); col.pack(side="left",expand=True,fill="x",padx=3)
   self.label(col,name,font=("Segoe UI",7,"bold")).pack()
   sc=tk.Scale(col,from_=100,to=0,orient="vertical",length=78,showvalue=False,bd=0,highlightthickness=0,command=lambda v,n=name:self.set_status(n+" visual control changed")); sc.set(50); sc.pack()
  self.sampler_panel=self.frame(self.bottom,width=290,padx=10,pady=9); self.sampler_panel.pack(side="right",fill="y"); self.sampler_panel.pack_propagate(False)
  self.label(self.sampler_panel,"SAMPLE PADS",font=("Segoe UI",10,"bold")).pack(anchor="w")
  pads=self.frame(self.sampler_panel); pads.pack(fill="both",expand=True,pady=5)
  for i in range(8):
   b=self.button(pads,"SAMPLE "+str(i+1),lambda n=i+1:self.set_status("Sample pad "+str(n)+" selected — audio sampler not connected yet"))
   b.grid(row=i//4,column=i%4,sticky="nsew",padx=3,pady=3)
  for i in range(4): pads.columnconfigure(i,weight=1)
  for i in range(2): pads.rowconfigure(i,weight=1)
  self.statusbar=tk.Label(self,textvariable=self.status,font=("Segoe UI",8),anchor="w",padx=10,pady=7,bd=0); self.statusbar.pack(fill="x",pady=(8,0))
  self.refresh_playlists(); self.refresh_tracks()

 def build_deck(self,parent,key):
  p=self.frame(parent,padx=12,pady=10); p.pack(side="left",fill="both",expand=True,padx=4)
  head=self.frame(p); head.pack(fill="x")
  self.label(head,"DECK "+key,font=("Segoe UI",13,"bold")).pack(side="left")
  self.label(head,"●  READY",font=("Segoe UI",8,"bold")).pack(side="right")
  title=self.label(p,"No track loaded",font=("Segoe UI",11,"bold"),anchor="w"); title.pack(fill="x",pady=(8,0))
  time=self.label(p,"00:00.0",font=("Segoe UI",22,"bold")); time.pack(anchor="w")
  wave=tk.Canvas(p,height=64,bd=0,highlightthickness=0); wave.pack(fill="x",pady=(4,6))
  row=self.frame(p); row.pack(fill="x")
  jog=tk.Canvas(row,width=116,height=116,bd=0,highlightthickness=0); jog.pack(side="left",padx=(0,12))
  jog.bind("<Button-1>",lambda e,k=key:self.set_status("Deck "+k+" jogwheel selected — scratch engine not connected"))
  jog.bind("<B1-Motion>",lambda e,k=key:self.set_status("Deck "+k+" jogwheel movement detected — scratch engine is a later audio task"))
  right=self.frame(row); right.pack(side="left",fill="both",expand=True)
  btns=self.frame(right); btns.pack(anchor="w",pady=2)
  self.button(btns,"LOAD",lambda k=key:self.load_to(k)).pack(side="left",padx=2)
  self.button(btns,"CUE",lambda k=key:self.set_status("Deck "+k+" cue point selected (audio cue not active)")).pack(side="left",padx=2)
  self.button(btns,"▶ PLAY",lambda k=key:self.play_deck(k)).pack(side="left",padx=2)
  self.button(btns,"■ STOP",lambda k=key:self.stop_deck(k)).pack(side="left",padx=2)
  row2=self.frame(right); row2.pack(fill="x",pady=4)
  for t in ("− PITCH","＋ PITCH","SYNC","4 BEAT LOOP"):
   self.button(row2,t,lambda x=t,k=key:self.set_status("Deck "+k+" "+x+" control selected")).pack(side="left",padx=2)
  cue=self.frame(right); cue.pack(anchor="w",pady=4)
  for n in range(1,5): self.button(cue,"HOT CUE "+str(n),lambda k=key,x=n:self.set_status("Deck "+k+" hot cue "+str(x)+" selected")).pack(side="left",padx=2)
  self.deck_ui[key]={"panel":p,"title":title,"time":time,"wave":wave,"jog":jog}

 def draw_wave(self,key):
  c=THEMES[self.theme_name.get()]; cv=self.deck_ui[key]["wave"]; cv.delete("all")
  w=max(cv.winfo_width(),420); h=64; mid=h//2
  cv.create_rectangle(0,0,w,h,fill=c["panel"],outline="")
  rnd=random.Random(12 if key=="A" else 28)
  for x in range(0,w,3):
   amp=rnd.randint(5,26)
   cv.create_line(x,mid-amp,x,mid+amp,fill=c["accent"] if x<w*.52 else c["muted"],width=2)
  cv.create_line(w*.52,4,w*.52,h-4,fill=c["hot"],width=2)
  cv.create_text(8,7,text="WAVEFORM DISPLAY MOCKUP",anchor="nw",fill=c["muted"],font=("Segoe UI",7,"bold"))

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

 def add_music(self):
  paths=filedialog.askopenfilenames(title="Add music",filetypes=[("Audio files","*.mp3 *.wav *.flac *.aiff *.aif *.ogg *.m4a"),("All files","*.*")])
  count=0
  for path in paths:
   if path not in self.tracks: self.tracks.append(path); self.playlists.setdefault("All Tracks",[]).append(path); count+=1
  self.refresh_tracks(); self.save_data(); self.set_status(str(count)+" tracks added")
 def refresh_tracks(self):
  if not hasattr(self,"table"): return
  for i in self.table.get_children(): self.table.delete(i)
  for path in self.playlists.get(self.current_playlist,[]):
   name=os.path.basename(path)
   if self.search.get().lower() in name.lower(): self.table.insert("","end",iid=path,values=(name,os.path.dirname(path)))
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
 def load_to(self,key):
  path=self.selected()
  if not path: self.set_status("Select a track in the library first"); return
  self.stop_deck(key, announce=False)
  self.deck_tracks[key]=path; self.deck_ui[key]["title"].configure(text=os.path.basename(path)); self.deck_ui[key]["time"].configure(text="00:00.0")
  if self.audio_ready:
   try:
    self.deck_sounds[key]=pygame.mixer.Sound(path)
   except Exception as e:
    self.deck_sounds[key]=None
    self.set_status("Track loaded, but audio could not be opened: "+str(e))
  self.draw_wave(key); self.set_status(os.path.basename(path)+" loaded into Deck "+key+" — press PLAY")
 def play_deck(self,key):
  if not self.audio_ready:
   self.set_status("Audio device unavailable: "+getattr(self,"audio_error","unknown audio error")); return
  sound=self.deck_sounds.get(key)
  if sound is None:
   path=self.deck_tracks.get(key)
   if not path:
    self.set_status("Load a track into Deck "+key+" first"); return
   try:
    sound=pygame.mixer.Sound(path); self.deck_sounds[key]=sound
   except Exception as e:
    self.set_status("Cannot play this file: "+str(e)); return
  self.deck_channels[key].play(sound)
  self.set_status("Deck "+key+" playing: "+os.path.basename(self.deck_tracks[key]))

 def stop_deck(self,key,announce=True):
  channel=self.deck_channels.get(key) if hasattr(self,"deck_channels") else None
  if channel:
   channel.stop()
  if announce:
   self.set_status("Deck "+key+" stopped")

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
  try: pygame.mixer.quit()
  except Exception: pass
