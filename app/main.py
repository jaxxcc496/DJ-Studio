import tkinter as tk
from tkinter import ttk

THEMES = {
    "Dark": {"bg": "#17191f", "panel": "#242832", "fg": "#f2f4f8", "accent": "#31c5f4"},
    "VirtualDJ Grey": {"bg": "#292929", "panel": "#3a3a3a", "fg": "#f4f4f4", "accent": "#ff9d2e"},
    "Rekordbox Blue": {"bg": "#101b2b", "panel": "#1b2b42", "fg": "#f1f6ff", "accent": "#2da8ff"},
}

class DJStudio(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DJ Studio")
        self.geometry("1100x700")
        self.minsize(850, 560)
        self.theme_name = tk.StringVar(value="Dark")
        self.configure(bg=THEMES["Dark"]["bg"])
        self.build_ui()
        self.apply_theme()

    def build_ui(self):
        self.header = tk.Frame(self, padx=14, pady=10)
        self.header.pack(fill="x")
        self.brand = tk.Label(self.header, text="DJ STUDIO", font=("Segoe UI", 19, "bold"))
        self.brand.pack(side="left")
        tk.Label(self.header, text="Theme").pack(side="right", padx=(8, 4))
        theme_box = ttk.Combobox(self.header, textvariable=self.theme_name,
                                 values=list(THEMES), state="readonly", width=18)
        theme_box.pack(side="right")
        theme_box.bind("<<ComboboxSelected>>", lambda _event: self.apply_theme())

        self.decks = tk.Frame(self, padx=12, pady=12)
        self.decks.pack(fill="x", padx=12)
        self.deck_widgets = []
        for name in ("DECK A", "DECK B"):
            panel = tk.Frame(self.decks, padx=18, pady=18, relief="flat")
            panel.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(panel, text=name, font=("Segoe UI", 15, "bold")).pack(anchor="w")
            tk.Label(panel, text="00:00.0", font=("Segoe UI", 28, "bold")).pack(pady=16)
            tk.Label(panel, text="BPM  --    KEY  --").pack()
            controls = tk.Frame(panel)
            controls.pack(pady=14)
            for label in ("CUE", "PLAY", "SYNC"):
                tk.Button(controls, text=label, width=8, state="disabled").pack(side="left", padx=4)
            self.deck_widgets.append(panel)

        self.mixer = tk.Frame(self, padx=14, pady=14)
        self.mixer.pack(fill="x", padx=18, pady=8)
        tk.Label(self.mixer, text="MIXER", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(self.mixer, text="Audio engine and controller support are planned for upcoming stages.",
                 wraplength=950).pack(anchor="w", pady=8)

        self.library = tk.Frame(self, padx=14, pady=12)
        self.library.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        tk.Label(self.library, text="MUSIC LIBRARY", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(self.library, text="Your tracks and playlists will appear here in a future build.",
                 anchor="w").pack(fill="x", pady=8)

    def apply_theme(self):
        colors = THEMES[self.theme_name.get()]
        self.configure(bg=colors["bg"])
        for widget in (self.header, self.decks, self.mixer, self.library):
            widget.configure(bg=colors["bg"])
        for widget in (self.brand,):
            widget.configure(bg=colors["bg"], fg=colors["fg"])
        for panel in self.deck_widgets:
            panel.configure(bg=colors["panel"])
            for child in panel.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=colors["panel"], fg=colors["fg"])
                elif isinstance(child, tk.Frame):
                    child.configure(bg=colors["panel"])
                    for button in child.winfo_children():
                        button.configure(bg=colors["accent"], fg="#101010",
                                         activebackground=colors["fg"])
        for panel in (self.mixer, self.library):
            for child in panel.winfo_children():
                child.configure(bg=colors["bg"], fg=colors["fg"])

if __name__ == "__main__":
    DJStudio().mainloop()
