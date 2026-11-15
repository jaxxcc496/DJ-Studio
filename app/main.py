import os
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox

THEMES = {
    "Midnight": {"bg": "#10141d", "panel": "#1b2330", "panel2": "#263244", "fg": "#edf3fb", "muted": "#9eacbf", "accent": "#23c7d9"},
    "VirtualDJ Grey": {"bg": "#20242b", "panel": "#2b313b", "panel2": "#394352", "fg": "#f4f6f8", "muted": "#b4bdc9", "accent": "#ff9b38"},
    "Rekordbox Blue": {"bg": "#0c1728", "panel": "#14243a", "panel2": "#203653", "fg": "#eff6ff", "muted": "#a9bdd5", "accent": "#38a7ff"},
    "Purple": {"bg": "#171322", "panel": "#241d35", "panel2": "#34294b", "fg": "#f7f0ff", "muted": "#c0b2d5", "accent": "#bd83ff"},
}

class DJStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJ Studio")
        self.geometry("1280x820")
        self.minsize(980, 650)
        self.tracks = []
        self.playlists = {"All Tracks": []}
        self.current_playlist = "All Tracks"
        self.decks = {"A": None, "B": None}
        self.theme_name = tk.StringVar(value="Midnight")
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready — add music files to begin")
        self.build()
        self.apply_theme()

    def build(self):
        self.configure(padx=12, pady=10)
        top = tk.Frame(self)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="DJ STUDIO", font=("Segoe UI", 23, "bold")).pack(side="left")
        tk.Label(top, text="PERFORMANCE  •  LIBRARY  •  PLAYLISTS", font=("Segoe UI", 9, "bold")).pack(side="left", padx=18, pady=(8, 0))
        tk.Label(top, text="THEME").pack(side="right", padx=7)
        theme = ttk.Combobox(top, textvariable=self.theme_name, values=list(THEMES), state="readonly", width=18)
        theme.pack(side="right")
        theme.bind("<<ComboboxSelected>>", lambda _e: self.apply_theme())

        decks = tk.Frame(self)
        decks.pack(fill="x", pady=(0, 10))
        self.deck_panels = {}
        for key in ("A", "B"):
            panel = tk.Frame(decks, padx=16, pady=13)
            panel.pack(side="left", fill="both", expand=True, padx=5)
            self.deck_panels[key] = panel
            tk.Label(panel, text="DECK " + key, font=("Segoe UI", 14, "bold")).pack(anchor="w")
            track_label = tk.Label(panel, text="No track loaded", font=("Segoe UI", 12, "bold"), anchor="w")
            track_label.pack(fill="x", pady=(12, 3))
            self.deck_panels[key + "_track"] = track_label
            time_label = tk.Label(panel, text="00:00", font=("Segoe UI", 25, "bold"))
            time_label.pack(anchor="w")
            self.deck_panels[key + "_time"] = time_label
            tk.Label(panel, text="WAVEFORM PREVIEW", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(8, 2))
            wave = tk.Canvas(panel, height=42, highlightthickness=0)
            wave.pack(fill="x")
            self.deck_panels[key + "_wave"] = wave
            controls = tk.Frame(panel)
            controls.pack(fill="x", pady=(10, 0))
            tk.Button(controls, text="LOAD SELECTED", command=lambda k=key: self.load_selected(k)).pack(side="left", padx=(0, 6))
            tk.Button(controls, text="CUE", command=lambda k=key: self.set_status("Deck " + k + ": cue point interface placeholder")).pack(side="left", padx=4)
            tk.Button(controls, text="PLAY", command=lambda k=key: self.set_status("Deck " + k + ": audio playback will be added with the audio engine")).pack(side="left", padx=4)
            tk.Button(controls, text="STOP", command=lambda k=key: self.set_status("Deck " + k + ": stop control ready for audio engine")).pack(side="left", padx=4)

        mid = tk.Frame(self)
        mid.pack(fill="both", expand=True)
        left = tk.Frame(mid, padx=12, pady=10, width=220)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        tk.Label(left, text="PLAYLISTS", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.playlist_list = tk.Listbox(left, height=14, activestyle="none", exportselection=False)
        self.playlist_list.pack(fill="both", expand=True)
        self.playlist_list.bind("<<ListboxSelect>>", self.select_playlist)
        tk.Button(left, text="+ NEW PLAYLIST", command=self.new_playlist).pack(fill="x", pady=(8, 4))
        tk.Button(left, text="RENAME PLAYLIST", command=self.rename_playlist).pack(fill="x", pady=4)
        tk.Button(left, text="DELETE PLAYLIST", command=self.delete_playlist).pack(fill="x", pady=4)

        center = tk.Frame(mid, padx=12, pady=10)
        center.pack(side="left", fill="both", expand=True)
        bar = tk.Frame(center)
        bar.pack(fill="x", pady=(0, 8))
        tk.Label(bar, text="MUSIC LIBRARY", font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Button(bar, text="+ ADD MUSIC", command=self.add_music).pack(side="right")
        search = tk.Entry(center, textvariable=self.search_var)
        search.pack(fill="x", pady=(0, 8))
        search.insert(0, "")
        search.bind("<KeyRelease>", lambda _e: self.refresh_tracks())
        columns = ("title", "folder")
        self.track_table = ttk.Treeview(center, columns=columns, show="headings", selectmode="browse")
        self.track_table.heading("title", text="TRACK")
        self.track_table.heading("folder", text="LOCATION")
        self.track_table.column("title", width=330)
        self.track_table.column("folder", width=250)
        self.track_table.pack(fill="both", expand=True)
        self.track_table.bind("<Double-1>", lambda _e: self.load_selected("A"))
        actions = tk.Frame(center)
        actions.pack(fill="x", pady=(8, 0))
        tk.Button(actions, text="LOAD TO DECK A", command=lambda: self.load_selected("A")).pack(side="left", padx=(0, 5))
        tk.Button(actions, text="LOAD TO DECK B", command=lambda: self.load_selected("B")).pack(side="left", padx=5)
        tk.Button(actions, text="ADD TO PLAYLIST", command=self.add_selected_to_playlist).pack(side="left", padx=5)
        tk.Button(actions, text="REMOVE TRACK", command=self.remove_selected).pack(side="left", padx=5)

        bottom = tk.Frame(self, padx=10, pady=8)
        bottom.pack(fill="x", pady=(8, 0))
        tk.Label(bottom, text="MIXER", font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(bottom, text="Audio engine • scratch • MIDI mapping • effects are the next development stage").pack(side="left", padx=16)
        self.status = tk.Label(self, textvariable=self.status_var, anchor="w", padx=10, pady=6)
        self.status.pack(fill="x", pady=(7, 0))
        self.refresh_playlists()
        self.refresh_tracks()

    def set_status(self, text):
        self.status_var.set(text)

    def add_music(self):
        paths = filedialog.askopenfilenames(title="Choose music files", filetypes=[("Audio files", "*.mp3 *.wav *.flac *.aiff *.aif *.ogg *.m4a"), ("All files", "*.*")])
        added = 0
        for path in paths:
            if path not in self.tracks:
                self.tracks.append(path)
                self.playlists["All Tracks"].append(path)
                added += 1
        self.refresh_tracks()
        self.set_status(str(added) + " track(s) added to your library")

    def refresh_tracks(self):
        if not hasattr(self, "track_table"):
            return
        for item in self.track_table.get_children():
            self.track_table.delete(item)
        source = self.playlists.get(self.current_playlist, self.tracks)
        query = self.search_var.get().lower().strip()
        for path in source:
            name = os.path.basename(path)
            if query in name.lower():
                self.track_table.insert("", "end", iid=path, values=(name, os.path.dirname(path)))

    def refresh_playlists(self):
        if not hasattr(self, "playlist_list"):
            return
        self.playlist_list.delete(0, "end")
        for name in self.playlists:
            self.playlist_list.insert("end", name)
        names = list(self.playlists)
        if self.current_playlist in names:
            index = names.index(self.current_playlist)
            self.playlist_list.selection_set(index)
            self.playlist_list.activate(index)

    def select_playlist(self, _event=None):
        selection = self.playlist_list.curselection()
        if selection:
            self.current_playlist = self.playlist_list.get(selection[0])
            self.refresh_tracks()

    def new_playlist(self):
        name = simpledialog.askstring("New playlist", "Playlist name:")
        if name and name.strip():
            name = name.strip()
            if name in self.playlists:
                messagebox.showinfo("Playlist exists", "That playlist already exists.")
                return
            self.playlists[name] = []
            self.current_playlist = name
            self.refresh_playlists()
            self.refresh_tracks()

    def rename_playlist(self):
        old = self.current_playlist
        if old == "All Tracks":
            messagebox.showinfo("Not allowed", "The All Tracks library cannot be renamed.")
            return
        new = simpledialog.askstring("Rename playlist", "New name:", initialvalue=old)
        if new and new.strip() and new.strip() not in self.playlists:
            items = self.playlists.pop(old)
            self.playlists[new.strip()] = items
            self.current_playlist = new.strip()
            self.refresh_playlists()
            self.refresh_tracks()

    def delete_playlist(self):
        name = self.current_playlist
        if name == "All Tracks":
            return
        if messagebox.askyesno("Delete playlist", "Delete playlist '" + name + "'? The files stay in All Tracks."):
            del self.playlists[name]
            self.current_playlist = "All Tracks"
            self.refresh_playlists()
            self.refresh_tracks()

    def selected_path(self):
        selection = self.track_table.selection()
        return selection[0] if selection else None

    def load_selected(self, deck):
        path = self.selected_path()
        if not path:
            self.set_status("Select a track in the library first")
            return
        self.decks[deck] = path
        self.deck_panels[deck + "_track"].configure(text=os.path.basename(path))
        self.draw_wave(deck)
        self.set_status(os.path.basename(path) + " loaded into Deck " + deck + " (playback engine not connected yet)")

    def draw_wave(self, deck):
        canvas = self.deck_panels[deck + "_wave"]
        canvas.delete("all")
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 250)
        height = 42
        for x in range(0, width, 5):
            h = 5 + ((x * 17 + len(self.decks[deck] or "" ) * 11) % 29)
            canvas.create_line(x, height // 2 - h // 2, x, height // 2 + h // 2, fill=THEMES[self.theme_name.get()]["accent"], width=2)

    def add_selected_to_playlist(self):
        path = self.selected_path()
        if not path:
            return
        if self.current_playlist == "All Tracks":
            self.set_status("Choose or create a playlist first")
            return
        if path not in self.playlists[self.current_playlist]:
            self.playlists[self.current_playlist].append(path)
        self.set_status("Added to " + self.current_playlist)

    def remove_selected(self):
        path = self.selected_path()
        if not path:
            return
        if self.current_playlist == "All Tracks":
            self.tracks.remove(path)
            for playlist in self.playlists.values():
                if path in playlist:
                    playlist.remove(path)
        else:
            self.playlists[self.current_playlist].remove(path)
        self.refresh_tracks()
        self.set_status("Track removed from current view")

    def apply_theme(self):
        c = THEMES[self.theme_name.get()]
        self.configure(bg=c["bg"])
        for widget in self.winfo_children():
            self.paint(widget, c)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=c["panel"], fieldbackground=c["panel"], foreground=c["fg"], rowheight=28)
        style.configure("Treeview.Heading", background=c["panel2"], foreground=c["fg"], font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", "#10141d")])
        for key in ("A", "B"):
            self.draw_wave(key)

    def paint(self, widget, c):
        # ttk widgets use ttk.Style; classic Tk options such as bg/fg
        # are not valid on ttk.Combobox and other themed controls.
        if not isinstance(widget, ttk.Widget):
            try:
                widget.configure(bg=c["bg"])
            except tk.TclError:
                pass
            if isinstance(widget, (tk.Label, tk.Button, tk.Entry, tk.Listbox)):
                try:
                    widget.configure(fg=c["fg"])
                except tk.TclError:
                    pass
            if isinstance(widget, tk.Button):
                widget.configure(bg=c["panel2"], fg=c["fg"],
                                 activebackground=c["accent"],
                                 activeforeground="#10141d",
                                 relief="flat", padx=9, pady=5,
                                 cursor="hand2")
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=c["panel"], fg=c["fg"],
                                 insertbackground=c["fg"], relief="flat")
            elif isinstance(widget, tk.Listbox):
                widget.configure(bg=c["panel"], fg=c["fg"],
                                 selectbackground=c["accent"],
                                 selectforeground="#10141d", relief="flat")
        for child in widget.winfo_children():
            self.paint(child, c)

if __name__ == "__main__":
    DJStudio().mainloop()
