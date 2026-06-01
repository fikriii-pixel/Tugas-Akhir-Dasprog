import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque


# ==================== KELAS DATA MAHASISWA ====================
class Mahasiswa:
    def __init__(self, nim, nama, nilai1, nilai2, nilai3, nilai4, nilai5,
                 sks1=3, sks2=3, sks3=3, sks4=3, sks5=3):
        self.nim = str(nim)
        self.nama = nama
        self.mk = [
            {"nama": "Algoritma",         "nilai": nilai1, "sks": sks1},
            {"nama": "Struktur Data",     "nilai": nilai2, "sks": sks2},
            {"nama": "Basis Data",        "nilai": nilai3, "sks": sks3},
            {"nama": "Jaringan Komputer", "nilai": nilai4, "sks": sks4},
            {"nama": "Pemrograman Web",   "nilai": nilai5, "sks": sks5},
        ]
        self.hitung_ipk()

    def hitung_ipk(self):
        total_bobot = 0
        total_sks = 0
        for mk in self.mk:
            nilai = mk["nilai"]
            sks = mk["sks"]
            if   nilai >= 85: bobot, grade = 4.0, "A"
            elif nilai >= 80: bobot, grade = 3.7, "A-"
            elif nilai >= 75: bobot, grade = 3.3, "B+"
            elif nilai >= 70: bobot, grade = 3.0, "B"
            elif nilai >= 65: bobot, grade = 2.7, "B-"
            elif nilai >= 60: bobot, grade = 2.3, "C+"
            elif nilai >= 55: bobot, grade = 2.0, "C"
            elif nilai >= 50: bobot, grade = 1.0, "D"
            else:             bobot, grade = 0.0, "E"
            mk["bobot"] = bobot
            mk["grade"] = grade
            total_bobot += bobot * sks
            total_sks += sks
        self.total_sks = total_sks
        self.ipk = round(total_bobot / total_sks, 2) if total_sks > 0 else 0

    def get_status(self):
        if self.ipk >= 2.5:   return "Lulus"
        elif self.ipk >= 2.0: return "Tangguh"
        else:                 return "Tidak Lulus"

    def get_status_icon(self):
        s = self.get_status()
        return {"Lulus": "✅ Lulus", "Tangguh": "⚠️ Tangguh"}.get(s, "❌ Tidak Lulus")

    def get_status_for_sort(self):
        return {"Lulus": 3, "Tangguh": 2}.get(self.get_status(), 1)

    def to_dict(self):
        return {"nim": self.nim, "nama": self.nama, "mk": self.mk,
                "total_sks": self.total_sks, "ipk": self.ipk}

    @classmethod
    def from_dict(cls, data):
        mk = data["mk"]
        return cls(str(data["nim"]), data["nama"],
                   mk[0]["nilai"], mk[1]["nilai"], mk[2]["nilai"], mk[3]["nilai"], mk[4]["nilai"],
                   mk[0]["sks"],   mk[1]["sks"],   mk[2]["sks"],   mk[3]["sks"],   mk[4]["sks"])


# ==================== APLIKASI UTAMA ====================
class AplikasiAkademik:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Academic Portal")
        self.root.geometry("1440x860")
        self.root.minsize(1240, 740)

        self.warna = {
            'bg':            '#f1f5f9',
            'surface':       '#ffffff',
            'surface_alt':   '#f8fafc',
            'border':        '#e2e8f0',
            'border_strong': '#cbd5e1',
            'text':          '#0f172a',
            'text_muted':    '#64748b',
            'primary':       '#4f46e5',
            'primary_dark':  '#4338ca',
            'primary_soft':  '#eef2ff',
            'accent':        '#0ea5e9',
            'success':       '#10b981',
            'warning':       '#f59e0b',
            'danger':        '#ef4444',
            'info':          '#06b6d4',
            'purple':        '#8b5cf6',
            'orange':        '#f97316',
            'white':         '#ffffff',
            'light':         '#f1f5f9',
            'dark':          '#0f172a',
            'gray':          '#64748b',
            'secondary':     '#334155',
        }

        self.root.configure(bg=self.warna['bg'])

        self.data_mahasiswa = {}
        self.riwayat = deque(maxlen=20)
        self.file_data = "data_mahasiswa.json"

        self.setup_ui()
        self.load_data()
        self.tambah_riwayat("Aplikasi dimulai", "info")
        self.refresh_tabel()
        self.update_dashboard()

    # ---------- Style helpers ----------
    def _make_btn(self, parent, text, cmd, kind="primary", small=False):
        """Modern flat button with hover."""
        palette = {
            'primary': (self.warna['primary'],  self.warna['primary_dark'], '#ffffff'),
            'success': (self.warna['success'],  '#059669',                   '#ffffff'),
            'danger':  (self.warna['danger'],   '#dc2626',                   '#ffffff'),
            'warning': (self.warna['warning'],  '#d97706',                   '#ffffff'),
            'info':    (self.warna['info'],     '#0891b2',                   '#ffffff'),
            'accent':  (self.warna['accent'],   '#0284c7',                   '#ffffff'),
            'purple':  (self.warna['purple'],   '#7c3aed',                   '#ffffff'),
            'ghost':   (self.warna['surface'],  self.warna['primary_soft'], self.warna['text']),
            'muted':   ('#e2e8f0',              '#cbd5e1',                   self.warna['text']),
        }
        bg, hover, fg = palette.get(kind, palette['primary'])
        padx, pady, fz = (12, 5, 9) if small else (16, 7, 9)
        btn = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                        activebackground=hover, activeforeground=fg,
                        font=("Segoe UI", fz, "bold"),
                        relief="flat", bd=0, padx=padx, pady=pady,
                        cursor="hand2", highlightthickness=0)
        btn.bind("<Enter>", lambda e: btn.config(bg=hover))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg))
        return btn

    def _make_entry(self, parent, width=22, font_size=10):
        wrap = tk.Frame(parent, bg=self.warna['border'], highlightthickness=0)
        e = tk.Entry(wrap, width=width, font=("Segoe UI", font_size),
                     relief="flat", bd=0, bg=self.warna['surface'],
                     fg=self.warna['text'], insertbackground=self.warna['primary'])
        e.pack(fill="both", expand=True, padx=1, pady=1, ipady=5, ipadx=6)
        e.bind("<FocusIn>", lambda ev: wrap.config(bg=self.warna['primary']))
        e.bind("<FocusOut>", lambda ev: wrap.config(bg=self.warna['border']))
        return e, wrap

    def _section_card(self, parent, accent_color=None):
        """White card with subtle border & optional top accent bar."""
        outer = tk.Frame(parent, bg=self.warna['border'])
        if accent_color:
            tk.Frame(outer, bg=accent_color, height=3).pack(fill="x")
        inner = tk.Frame(outer, bg=self.warna['surface'])
        inner.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        return outer, inner

    def _section_title(self, parent, text, color=None):
        color = color or self.warna['text']
        tk.Label(parent, text=text, font=("Segoe UI", 12, "bold"),
                 bg=self.warna['surface'], fg=color).pack(anchor="w", padx=18, pady=(14, 0))
        tk.Frame(parent, bg=self.warna['border'], height=1).pack(fill="x", padx=18, pady=(8, 0))

    # ---------- UI Setup ----------
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook (pill tabs)
        style.configure('TNotebook', background=self.warna['bg'], borderwidth=0)
        style.configure('TNotebook.Tab',
                        background=self.warna['surface'],
                        foreground=self.warna['text_muted'],
                        padding=[22, 10], font=('Segoe UI', 10, 'bold'),
                        borderwidth=0)
        style.map('TNotebook.Tab',
                  background=[('selected', self.warna['primary'])],
                  foreground=[('selected', '#ffffff')],
                  expand=[('selected', [1, 1, 1, 0])])

        # Treeview
        style.configure("Treeview",
                        font=('Segoe UI', 10), rowheight=32,
                        background=self.warna['surface'],
                        fieldbackground=self.warna['surface'],
                        foreground=self.warna['text'],
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=('Segoe UI', 10, 'bold'),
                        background=self.warna['primary_soft'],
                        foreground=self.warna['primary_dark'],
                        relief="flat", borderwidth=0, padding=8)
        style.map("Treeview",
                  background=[('selected', self.warna['primary'])],
                  foreground=[('selected', '#ffffff')])
        style.map("Treeview.Heading",
                  background=[('active', self.warna['primary_soft'])])

        # Combobox
        style.configure("TCombobox",
                        fieldbackground=self.warna['surface'],
                        background=self.warna['surface'],
                        foreground=self.warna['text'],
                        arrowcolor=self.warna['primary'],
                        borderwidth=1, padding=4)

        # Scrollbar
        style.configure("Vertical.TScrollbar", background=self.warna['border'],
                        troughcolor=self.warna['bg'], borderwidth=0, arrowcolor=self.warna['text_muted'])

        main_container = tk.Frame(self.root, bg=self.warna['bg'])
        main_container.pack(fill="both", expand=True, padx=24, pady=(20, 0))

        self.create_header(main_container)

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=(18, 0))

        self.tab_dashboard         = tk.Frame(self.notebook, bg=self.warna['bg'])
        self.tab_data              = tk.Frame(self.notebook, bg=self.warna['bg'])
        self.tab_statistik         = tk.Frame(self.notebook, bg=self.warna['bg'])
        self.tab_daftar_mahasiswa  = tk.Frame(self.notebook, bg=self.warna['bg'])
        self.tab_riwayat           = tk.Frame(self.notebook, bg=self.warna['bg'])

        self.notebook.add(self.tab_dashboard,        text="  📊  Dashboard  ")
        self.notebook.add(self.tab_data,             text="  📝  Data Mahasiswa  ")
        self.notebook.add(self.tab_statistik,        text="  📈  Statistik  ")
        self.notebook.add(self.tab_daftar_mahasiswa, text="  📋  Mahasiswa ")
        self.notebook.add(self.tab_riwayat,          text="  📜  Riwayat  ")

        self.setup_dashboard()
        self.setup_tab_data()
        self.setup_tab_statistik()
        self.setup_tab_daftar_mahasiswa()
        self.setup_tab_riwayat()

        self.create_status_bar()

    def create_header(self, parent):
        header = tk.Frame(parent, bg=self.warna['primary'], height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Frame(header, bg=self.warna['accent'], height=3).pack(fill="x", side="bottom")

        inner = tk.Frame(header, bg=self.warna['primary'])
        inner.pack(fill="both", expand=True, padx=28)

        left = tk.Frame(inner, bg=self.warna['primary'])
        left.pack(side="left", fill="y")

        logo = tk.Frame(left, bg='#ffffff', width=46, height=46)
        logo.pack(side="left", pady=22)
        logo.pack_propagate(False)
        tk.Label(logo, text="🎓", font=("Segoe UI", 20),
                 bg='#ffffff', fg=self.warna['primary']).pack(expand=True)

        text_frame = tk.Frame(left, bg=self.warna['primary'])
        text_frame.pack(side="left", padx=(14, 0), pady=20)
        tk.Label(text_frame, text="Student Academic Portal",
                 font=("Segoe UI", 17, "bold"),
                 bg=self.warna['primary'], fg='#ffffff').pack(anchor="w")
        tk.Label(text_frame, text="Sistem Informasi Akademik Mahasiswa",
                 font=("Segoe UI", 10),
                 bg=self.warna['primary'], fg='#c7d2fe').pack(anchor="w")

        right = tk.Frame(inner, bg=self.warna['primary'])
        right.pack(side="right", fill="y")
        self.header_clock = tk.Label(right, font=("Segoe UI", 11, "bold"),
                                     bg=self.warna['primary'], fg='#ffffff')
        self.header_clock.pack(side="top", pady=(26, 0))
        self.header_date = tk.Label(right, font=("Segoe UI", 9),
                                    bg=self.warna['primary'], fg='#c7d2fe')
        self.header_date.pack(side="top")
        self.update_clock()

    def create_status_bar(self):
        bar_wrap = tk.Frame(self.root, bg=self.warna['border'])
        bar_wrap.pack(side="bottom", fill="x")
        tk.Frame(bar_wrap, bg=self.warna['border'], height=1).pack(fill="x")
        bar = tk.Frame(bar_wrap, bg=self.warna['surface'], height=30)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self.status_label = tk.Label(bar, text="✓ Siap",
                                     font=("Segoe UI", 9),
                                     bg=self.warna['surface'], fg=self.warna['text_muted'])
        self.status_label.pack(side="left", padx=18)

        self.clock_label = self.header_clock

        tk.Label(bar, text="v2.0 · by Fikri",
                 font=("Segoe UI", 9),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="right", padx=18)

    def update_clock(self):
        now = datetime.now()
        if hasattr(self, 'header_clock'):
            self.header_clock.config(text=now.strftime("%H:%M:%S"))
            self.header_date.config(text=now.strftime("%A, %d %b %Y"))
        self.root.after(1000, self.update_clock)

    # ==================== DASHBOARD ====================
    def setup_dashboard(self):
        wrap = tk.Frame(self.tab_dashboard, bg=self.warna['bg'])
        wrap.pack(fill="both", expand=True, padx=24, pady=24)

        cards_frame = tk.Frame(wrap, bg=self.warna['bg'])
        cards_frame.pack(fill="x")

        self.cards = {}
        stats = [
            ("👥", "Total Mahasiswa",    "total",          self.warna['primary']),
            ("📈", "Rata-rata IPK",      "rata_ipk",       self.warna['success']),
            ("🎓", "Tingkat Kelulusan",  "kelulusan",      self.warna['info']),
            ("⭐", "IPK Tertinggi",      "ipk_tertinggi",  self.warna['warning']),
        ]
        for i, (icon, title, key, color) in enumerate(stats):
            card = self.create_stat_card(cards_frame, icon, title, "0", color, i)
            self.cards[key] = card
            cards_frame.grid_columnconfigure(i, weight=1, uniform="cards")

        charts_container = tk.Frame(wrap, bg=self.warna['bg'])
        charts_container.pack(fill="both", expand=True, pady=(20, 0))
        charts_container.grid_columnconfigure(0, weight=1, uniform="ch")
        charts_container.grid_columnconfigure(1, weight=1, uniform="ch")
        charts_container.grid_rowconfigure(0, weight=1)

        left_outer, left_inner   = self._section_card(charts_container, self.warna['primary'])
        right_outer, right_inner = self._section_card(charts_container, self.warna['accent'])
        left_outer.grid (row=0, column=0, sticky="nsew", padx=(0, 10))
        right_outer.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._section_title(left_inner,  "📊  Distribusi IPK",       self.warna['primary'])
        self._section_title(right_inner, "🎯  Distribusi Status",    self.warna['accent'])

        self.fig1, self.ax1 = plt.subplots(figsize=(5, 3.6), dpi=90)
        self.fig2, self.ax2 = plt.subplots(figsize=(5, 3.6), dpi=90)
        for fig, ax in [(self.fig1, self.ax1), (self.fig2, self.ax2)]:
            fig.patch.set_facecolor(self.warna['surface'])
            ax.set_facecolor(self.warna['surface'])
            for spine in ax.spines.values():
                spine.set_color(self.warna['border'])

        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=left_inner)
        self.canvas1.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=14)
        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=right_inner)
        self.canvas2.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=14)

    def create_stat_card(self, parent, icon, title, value, color, col):
        outer = tk.Frame(parent, bg=self.warna['border'])
        outer.grid(row=0, column=col, padx=(0 if col == 0 else 8, 8 if col < 3 else 0), sticky="nsew")
        tk.Frame(outer, bg=color, height=3).pack(fill="x")
        body = tk.Frame(outer, bg=self.warna['surface'])
        body.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        row = tk.Frame(body, bg=self.warna['surface'])
        row.pack(fill="x", padx=20, pady=(18, 6))

        badge_wrap = tk.Frame(row, bg=self.warna['surface'])
        badge_wrap.pack(side="right")
        badge = tk.Label(badge_wrap, text=icon, font=("Segoe UI", 16),
                         bg=self.warna['primary_soft'], fg=color, padx=10, pady=4)
        badge.pack()

        tk.Label(row, text=title.upper(), font=("Segoe UI", 9, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", anchor="w")

        value_label = tk.Label(body, text=value, font=("Segoe UI", 28, "bold"),
                               bg=self.warna['surface'], fg=color)
        value_label.pack(anchor="w", padx=20, pady=(0, 18))
        return value_label

    def update_dashboard(self):
        total = len(self.data_mahasiswa)

        if total == 0:
            self.cards['total'].config(text="0")
            self.cards['rata_ipk'].config(text="0.00")
            self.cards['kelulusan'].config(text="0%")
            self.cards['ipk_tertinggi'].config(text="-")
            self.ax1.clear(); self.ax2.clear()
            for ax in (self.ax1, self.ax2):
                ax.text(0.5, 0.5, "Belum ada data", ha="center", va="center",
                        transform=ax.transAxes, fontsize=12, color=self.warna['text_muted'])
                ax.set_xticks([]); ax.set_yticks([])
            self.canvas1.draw(); self.canvas2.draw()
            return

        ipk_list = [m.ipk for m in self.data_mahasiswa.values()]
        rata_ipk = sum(ipk_list) / total
        lulus = sum(1 for m in self.data_mahasiswa.values() if m.get_status() == "Lulus")
        tertinggi = max(self.data_mahasiswa.values(), key=lambda m: m.ipk)

        self.cards['total'].config(text=str(total))
        self.cards['rata_ipk'].config(text=f"{rata_ipk:.2f}")
        self.cards['kelulusan'].config(text=f"{(lulus/total)*100:.1f}%")
        self.cards['ipk_tertinggi'].config(text=f"{tertinggi.ipk:.2f}")

        self.ax1.clear()
        n_vals, bin_edges, patches = self.ax1.hist(
            ipk_list, bins=10, color=self.warna['primary'],
            alpha=0.85, edgecolor='white', linewidth=1.2)
        self.ax1.set_xlabel("IPK", fontsize=10, color=self.warna['text_muted'])
        self.ax1.set_ylabel("Jumlah", fontsize=10, color=self.warna['text_muted'])
        self.ax1.tick_params(colors=self.warna['text_muted'])
        self.ax1.grid(True, alpha=0.25, linestyle='--')
        for s in self.ax1.spines.values(): s.set_color(self.warna['border'])
        max_n = max(n_vals) if len(n_vals) and max(n_vals) > 0 else 1
        self.ax1.set_ylim(0, max_n * 1.18)
        for count, patch in zip(n_vals, patches):
            if count > 0:
                self.ax1.text(patch.get_x() + patch.get_width()/2, count,
                              f'{int(count)}', ha='center', va='bottom',
                              fontsize=10, fontweight='bold',
                              color=self.warna['text'])
        self.fig1.tight_layout()

        self.ax2.clear()
        status_count = {"Lulus": 0, "Tangguh": 0, "Tidak Lulus": 0}
        for m in self.data_mahasiswa.values():
            status_count[m.get_status()] += 1
        warna_status = [self.warna['success'], self.warna['orange'], self.warna['danger']]
        bars = self.ax2.bar(status_count.keys(), status_count.values(),
                            color=warna_status, edgecolor='white', linewidth=1.2, width=0.55)
        self.ax2.set_ylabel("Jumlah", fontsize=10, color=self.warna['text_muted'])
        self.ax2.tick_params(colors=self.warna['text_muted'])
        self.ax2.grid(True, alpha=0.25, axis='y', linestyle='--')
        for s in self.ax2.spines.values(): s.set_color(self.warna['border'])
        for b in bars:
            self.ax2.text(b.get_x() + b.get_width()/2, b.get_height(),
                          f' {int(b.get_height())}', ha='center', va='bottom',
                          fontsize=10, fontweight='bold', color=self.warna['text'])
        self.fig2.tight_layout()

        self.canvas1.draw(); self.canvas2.draw()

    # ==================== TAB DATA MAHASISWA ====================
    def setup_tab_data(self):
        main_container = tk.Frame(self.tab_data, bg=self.warna['bg'])
        main_container.pack(fill="both", expand=True, padx=24, pady=24)

        left_outer, left_inner = self._section_card(main_container, self.warna['primary'])
        left_outer.pack(side="left", fill="y", padx=(0, 18))

        self._section_title(left_inner, "📝  Form Input Mahasiswa", self.warna['primary'])

        form_frame = tk.Frame(left_inner, bg=self.warna['surface'])
        form_frame.pack(fill="both", expand=True, padx=22, pady=18)
        form_frame.grid_columnconfigure(1, weight=1)

        def lbl(parent, text, **g):
            tk.Label(parent, text=text, bg=self.warna['surface'],
                     fg=self.warna['text'], font=("Segoe UI", 9, "bold")).grid(**g)

        lbl(form_frame, "NIM",          row=0, column=0, sticky="w", pady=(0, 4))
        self.entry_nim, w1 = self._make_entry(form_frame, width=24)
        w1.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        lbl(form_frame, "Nama Lengkap", row=2, column=0, sticky="w", pady=(0, 4))
        self.entry_nama, w2 = self._make_entry(form_frame, width=24)
        w2.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        tk.Frame(form_frame, bg=self.warna['border'], height=1)\
            .grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 12))

        tk.Label(form_frame, text="📚  NILAI MATA KULIAH", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']
                 ).grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.entries_nilai = []
        mk_list = ["Algoritma", "Struktur Data", "Basis Data", "Jaringan Komputer", "Pemrograman Web"]

        head = tk.Frame(form_frame, bg=self.warna['primary_soft'])
        head.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        tk.Label(head, text="Mata Kuliah", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['primary_soft'], fg=self.warna['primary_dark']
                 ).pack(side="left", padx=10, pady=6)
        tk.Label(head, text="SKS", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['primary_soft'], fg=self.warna['primary_dark']
                 ).pack(side="right", padx=14, pady=6)
        tk.Label(head, text="Nilai", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['primary_soft'], fg=self.warna['primary_dark']
                 ).pack(side="right", padx=18, pady=6)

        for i, mk in enumerate(mk_list):
            row_idx = 7 + i
            row = tk.Frame(form_frame, bg=self.warna['surface_alt'])
            row.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=2)

            tk.Label(row, text=mk, bg=self.warna['surface_alt'],
                     fg=self.warna['text'], font=("Segoe UI", 9), width=18, anchor="w"
                     ).pack(side="left", padx=10, pady=8)

            spin_sks = tk.Spinbox(row, from_=1, to=6, width=4,
                                  font=("Segoe UI", 9),
                                  relief="flat", bd=1,
                                  bg=self.warna['surface'], fg=self.warna['text'],
                                  buttonbackground=self.warna['primary_soft'])
            spin_sks.pack(side="right", padx=(4, 10), pady=6)
            spin_sks.delete(0, tk.END); spin_sks.insert(0, "3")

            entry_nilai = tk.Entry(row, width=6, font=("Segoe UI", 9),
                                   relief="flat", bd=0,
                                   bg=self.warna['surface'], fg=self.warna['text'],
                                   justify="center")
            entry_nilai.pack(side="right", padx=(4, 4), ipady=4)
            entry_nilai.insert(0, "0")

            self.entries_nilai.append({"nama": mk, "nilai": entry_nilai, "sks": spin_sks})

        btn_frame = tk.Frame(form_frame, bg=self.warna['surface'])
        btn_frame.grid(row=20, column=0, columnspan=2, pady=(20, 0), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        buttons = [
            ("➕  Tambah", self.tambah_mahasiswa, 'success'),
            ("✏️  Edit",   self.edit_mahasiswa,   'primary'),
            ("🗑️  Hapus",  self.hapus_mahasiswa,  'danger'),
            ("🔄  Reset",  self.reset_form,       'muted'),
        ]
        for i, (text, cmd, kind) in enumerate(buttons):
            b = self._make_btn(btn_frame, text, cmd, kind)
            b.grid(row=i // 2, column=i % 2, sticky="ew", padx=4, pady=4, ipady=2)

        right_panel = tk.Frame(main_container, bg=self.warna['bg'])
        right_panel.pack(side="right", fill="both", expand=True)

        tb_outer, tb_inner = self._section_card(right_panel)
        tb_outer.pack(fill="x", pady=(0, 14))

        tb = tk.Frame(tb_inner, bg=self.warna['surface'])
        tb.pack(fill="x", padx=18, pady=14)

        r1 = tk.Frame(tb, bg=self.warna['surface'])
        r1.pack(fill="x")

        sg = tk.Frame(r1, bg=self.warna['surface'])
        sg.pack(side="left")
        tk.Label(sg, text="🔍", font=("Segoe UI", 11),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self.entry_cari, ec_w = self._make_entry(sg, width=22, font_size=9)
        ec_w.pack(side="left", padx=(0, 6))
        self._make_btn(sg, "Cari",  self.cari_mahasiswa,  'primary', small=True).pack(side="left", padx=(0, 4))
        self._make_btn(sg, "Reset", self.refresh_tabel,   'muted',   small=True).pack(side="left")

        ttk.Separator(r1, orient='vertical').pack(side="left", fill="y", padx=14)

        sortg = tk.Frame(r1, bg=self.warna['surface'])
        sortg.pack(side="left")
        tk.Label(sortg, text="📊", font=("Segoe UI", 11),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self.combo_sort = ttk.Combobox(sortg,
                                       values=["IPK Tertinggi", "IPK Terendah",
                                               "Nama A-Z", "Nama Z-A",
                                               "Keterangan (Lulus→Tidak)", "Keterangan (Tidak→Lulus)"],
                                       width=20, state="readonly")
        self.combo_sort.pack(side="left", padx=(0, 6))
        self.combo_sort.set("IPK Tertinggi")
        self._make_btn(sortg, "Urutkan", self.sort_mahasiswa, 'info', small=True).pack(side="left")

        self.jumlah_data_label = tk.Label(r1, text="📊  Total: 0 data",
                                          font=("Segoe UI", 10, "bold"),
                                          bg=self.warna['surface'], fg=self.warna['primary'])
        self.jumlah_data_label.pack(side="right")

        tk.Frame(tb, bg=self.warna['border'], height=1).pack(fill="x", pady=12)
        r2 = tk.Frame(tb, bg=self.warna['surface'])
        r2.pack(fill="x")

        rg = tk.Frame(r2, bg=self.warna['surface'])
        rg.pack(side="left")
        tk.Label(rg, text="🎯  Range IPK:", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self.ipk_min, w_min = self._make_entry(rg, width=5, font_size=9); w_min.pack(side="left")
        self.ipk_min.insert(0, "0.00")
        tk.Label(rg, text="—", bg=self.warna['surface'], fg=self.warna['text_muted'],
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=6)
        self.ipk_max, w_max = self._make_entry(rg, width=5, font_size=9); w_max.pack(side="left")
        self.ipk_max.insert(0, "4.00")
        self._make_btn(rg, "Filter", self.filter_by_ipk_range, 'purple', small=True).pack(side="left", padx=(8, 4))
        self._make_btn(rg, "Reset",  self.refresh_tabel,       'muted',  small=True).pack(side="left")

        ttk.Separator(r2, orient='vertical').pack(side="left", fill="y", padx=14)

        ie = tk.Frame(r2, bg=self.warna['surface'])
        ie.pack(side="left")
        tk.Label(ie, text="💾", font=("Segoe UI", 11),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self._make_btn(ie, "Export CSV", self.export_csv, 'accent', small=True).pack(side="left", padx=(0, 4))
        self._make_btn(ie, "Import CSV", self.import_csv, 'warning', small=True).pack(side="left")

        self._make_btn(r2, "🗑️  Hapus Semua", self.hapus_semua_data, 'danger', small=True).pack(side="right")

        table_outer, table_inner = self._section_card(right_panel, self.warna['primary'])
        table_outer.pack(fill="both", expand=True)

        self._section_title(table_inner, "📋  Data Mahasiswa", self.warna['primary'])

        tree_container = tk.Frame(table_inner, bg=self.warna['surface'])
        tree_container.pack(fill="both", expand=True, padx=18, pady=14)

        scroll_y = ttk.Scrollbar(tree_container, orient="vertical")
        scroll_x = ttk.Scrollbar(tree_container, orient="horizontal")

        columns = ("NIM", "Nama Mahasiswa", "IPK", "Total SKS", "Status")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings",
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                 height=12)
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        widths = [150, 280, 90, 110, 150]
        aligns = ['center', 'w', 'center', 'center', 'center']
        for col, w, a in zip(columns, widths, aligns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor=a)

        self.tree.tag_configure('odd',  background=self.warna['surface'])
        self.tree.tag_configure('even', background=self.warna['surface_alt'])

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ==================== TAB DAFTAR MAHASISWA ====================
    def setup_tab_daftar_mahasiswa(self):
        container = tk.Frame(self.tab_daftar_mahasiswa, bg=self.warna['bg'])
        container.pack(fill="both", expand=True, padx=24, pady=24)

        tb_outer, tb_inner = self._section_card(container)
        tb_outer.pack(fill="x", pady=(0, 14))

        tb = tk.Frame(tb_inner, bg=self.warna['surface'])
        tb.pack(fill="x", padx=18, pady=14)

        r1 = tk.Frame(tb, bg=self.warna['surface'])
        r1.pack(fill="x")

        sg = tk.Frame(r1, bg=self.warna['surface']); sg.pack(side="left")
        tk.Label(sg, text="🔍", font=("Segoe UI", 11),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self.search_entry_daftar, w = self._make_entry(sg, width=24, font_size=9); w.pack(side="left", padx=(0, 6))
        self._make_btn(sg, "Cari",  self.cari_daftar_mahasiswa,    'primary', small=True).pack(side="left", padx=(0, 4))
        self._make_btn(sg, "Reset", self.refresh_daftar_mahasiswa, 'muted',   small=True).pack(side="left")

        ttk.Separator(r1, orient='vertical').pack(side="left", fill="y", padx=14)

        sortg = tk.Frame(r1, bg=self.warna['surface']); sortg.pack(side="left")
        tk.Label(sortg, text="📊  Urutkan:", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self.combo_sort_daftar = ttk.Combobox(sortg,
            values=["IPK Tertinggi", "IPK Terendah", "Nama A-Z", "Nama Z-A",
                    "NIM Terkecil", "NIM Terbesar",
                    "Keterangan (Lulus→Tidak)", "Keterangan (Tidak→Lulus)"],
            width=24, state="readonly")
        self.combo_sort_daftar.pack(side="left", padx=(0, 6))
        self.combo_sort_daftar.set("IPK Tertinggi")
        self._make_btn(sortg, "Urutkan", self.sort_daftar_mahasiswa, 'info', small=True).pack(side="left")

        self.info_label_daftar = tk.Label(r1, text="📊  Total: 0 mahasiswa",
                                          font=("Segoe UI", 10, "bold"),
                                          bg=self.warna['surface'], fg=self.warna['primary'])
        self.info_label_daftar.pack(side="right")

        tk.Frame(tb, bg=self.warna['border'], height=1).pack(fill="x", pady=12)

        r2 = tk.Frame(tb, bg=self.warna['surface']); r2.pack(fill="x")
        rg = tk.Frame(r2, bg=self.warna['surface']); rg.pack(side="left")
        tk.Label(rg, text="🎯  Filter Range IPK:", font=("Segoe UI", 9, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(side="left", padx=(0, 6))
        self.ipk_min_daftar, w_min = self._make_entry(rg, width=5, font_size=9); w_min.pack(side="left")
        self.ipk_min_daftar.insert(0, "0.00")
        tk.Label(rg, text="—", bg=self.warna['surface'], fg=self.warna['text_muted'],
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=6)
        self.ipk_max_daftar, w_max = self._make_entry(rg, width=5, font_size=9); w_max.pack(side="left")
        self.ipk_max_daftar.insert(0, "4.00")
        self._make_btn(rg, "Filter IPK",   self.filter_daftar_by_ipk_range, 'purple', small=True).pack(side="left", padx=(8, 4))
        self._make_btn(rg, "Reset Filter", self.refresh_daftar_mahasiswa,   'muted',  small=True).pack(side="left")

        self._make_btn(r2, "🔄  Refresh", self.refresh_daftar_mahasiswa, 'primary', small=True).pack(side="right")

        tb2_outer, tb2_inner = self._section_card(container, self.warna['primary'])
        tb2_outer.pack(fill="both", expand=True)

        self._section_title(tb2_inner, "📋  Daftar Seluruh Mahasiswa  ·  Klik dua kali untuk detail nilai", self.warna['primary'])

        tree_container = tk.Frame(tb2_inner, bg=self.warna['surface'])
        tree_container.pack(fill="both", expand=True, padx=18, pady=14)

        scroll_y = ttk.Scrollbar(tree_container, orient="vertical")
        scroll_x = ttk.Scrollbar(tree_container, orient="horizontal")

        columns = ("NIM", "Nama Mahasiswa", "IPK", "Total SKS", "Status")
        self.daftar_tree = ttk.Treeview(tree_container, columns=columns, show="headings",
                                        yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
                                        height=18)
        scroll_y.config(command=self.daftar_tree.yview)
        scroll_x.config(command=self.daftar_tree.xview)

        widths = [150, 320, 100, 110, 150]
        for col, w in zip(columns, widths):
            self.daftar_tree.heading(col, text=col)
            self.daftar_tree.column(col, width=w, anchor='center')
        self.daftar_tree.column("Nama Mahasiswa", anchor='w')

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.daftar_tree.pack(fill="both", expand=True)

        self.daftar_tree.bind("<Double-1>", self.show_nilai_detail)
        self.refresh_daftar_mahasiswa()

    # ==================== TAB STATISTIK ====================
    def setup_tab_statistik(self):
        # Scrollable wrapper supaya semua diagram tidak terpotong
        outer_wrap = tk.Frame(self.tab_statistik, bg=self.warna['bg'])
        outer_wrap.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer_wrap, bg=self.warna['bg'],
                                  highlightthickness=0, bd=0)
        vbar = ttk.Scrollbar(outer_wrap, orient="vertical",
                             command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        container = tk.Frame(scroll_canvas, bg=self.warna['bg'])
        win_id = scroll_canvas.create_window((0, 0), window=container, anchor="nw")

        def _on_cfg(_e=None):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        def _on_canvas_cfg(e):
            scroll_canvas.itemconfigure(win_id, width=e.width)
        container.bind("<Configure>", _on_cfg)
        scroll_canvas.bind("<Configure>", _on_canvas_cfg)

        def _on_mousewheel(e):
            scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        inner_pad = tk.Frame(container, bg=self.warna['bg'])
        inner_pad.pack(fill="both", expand=True, padx=24, pady=24)
        container = inner_pad

        # Title bar with refresh
        title_bar = tk.Frame(container, bg=self.warna['bg'])
        title_bar.pack(fill="x", pady=(0, 14))
        tk.Label(title_bar, text="📈  Ringkasan Statistik Akademik",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.warna['bg'], fg=self.warna['text']).pack(side="left")
        self._make_btn(title_bar, "🔄  Refresh", self.update_statistik, 'primary', small=True).pack(side="right")

        # ----- Row 1: 3 stat cards -----
        row1 = tk.Frame(container, bg=self.warna['bg'])
        row1.pack(fill="x", pady=(0, 14))
        for i in range(3): row1.grid_columnconfigure(i, weight=1, uniform="r1")

        self.stat_cards = {}
        items1 = [
            ("👥", "TOTAL MAHASISWA",            "total_mhs",  self.warna['primary']),
            ("📈", "RATA-RATA IPK",              "avg_ipk",    self.warna['success']),
            ("🎓", "TINGKAT KELULUSAN (≥2.5)",   "pass_rate",  self.warna['info']),
        ]
        for i, (icon, title, key, color) in enumerate(items1):
            card = self.create_stat_card(row1, icon, title, "0", color, i)
            self.stat_cards[key] = card

        # ----- Row 2: IPK tertinggi & terendah -----
        row2 = tk.Frame(container, bg=self.warna['bg'])
        row2.pack(fill="x", pady=(0, 14))
        row2.grid_columnconfigure(0, weight=1, uniform="r2")
        row2.grid_columnconfigure(1, weight=1, uniform="r2")

        # Max
        max_outer, max_inner = self._section_card(row2, self.warna['warning'])
        max_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        body = tk.Frame(max_inner, bg=self.warna['surface'])
        body.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(body, text="🏆  IPK TERTINGGI", font=("Segoe UI", 10, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(anchor="w")
        self.max_ipk_label = tk.Label(body, text="0.00", font=("Segoe UI", 32, "bold"),
                                      bg=self.warna['surface'], fg=self.warna['warning'])
        self.max_ipk_label.pack(anchor="w", pady=(4, 8))
        self.max_nama_label = tk.Label(body, text="-", font=("Segoe UI", 9),
                                       bg=self.warna['surface'], fg=self.warna['text'],
                                       wraplength=420, justify="left")
        self.max_nama_label.pack(anchor="w")

        # Min
        min_outer, min_inner = self._section_card(row2, self.warna['danger'])
        min_outer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        body = tk.Frame(min_inner, bg=self.warna['surface'])
        body.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(body, text="📉  IPK TERENDAH", font=("Segoe UI", 10, "bold"),
                 bg=self.warna['surface'], fg=self.warna['text_muted']).pack(anchor="w")
        self.min_ipk_label = tk.Label(body, text="0.00", font=("Segoe UI", 32, "bold"),
                                      bg=self.warna['surface'], fg=self.warna['danger'])
        self.min_ipk_label.pack(anchor="w", pady=(4, 8))
        self.min_nama_label = tk.Label(body, text="-", font=("Segoe UI", 9),
                                       bg=self.warna['surface'], fg=self.warna['text'],
                                       wraplength=420, justify="left")
        self.min_nama_label.pack(anchor="w")

        # ----- Row 3: Diagram Batang (Distribusi Grade) + Diagram Lingkaran (Status) -----
        row3 = tk.Frame(container, bg=self.warna['bg'])
        row3.pack(fill="both", expand=True, pady=(14, 0))
        row3.grid_columnconfigure(0, weight=1, uniform="r3")
        row3.grid_columnconfigure(1, weight=1, uniform="r3")
        row3.grid_rowconfigure(0, weight=1)

        gr_outer, gr_inner = self._section_card(row3, self.warna['info'])
        gr_outer.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._section_title(gr_inner, "📊  Distribusi Nilai (A · B · C · D · E)", self.warna['info'])

        pie_outer, pie_inner = self._section_card(row3, self.warna['accent'])
        pie_outer.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._section_title(pie_inner, "🥧  Distribusi Status Mahasiswa", self.warna['accent'])

        self.fig_grade,  self.ax_grade  = plt.subplots(figsize=(5.4, 4.2), dpi=90,
                                                       constrained_layout=True)
        self.fig_status, self.ax_status = plt.subplots(figsize=(5.4, 4.2), dpi=90,
                                                       constrained_layout=True)
        for fig, ax in [(self.fig_grade, self.ax_grade), (self.fig_status, self.ax_status)]:
            fig.patch.set_facecolor(self.warna['surface'])
            ax.set_facecolor(self.warna['surface'])
            for spine in ax.spines.values():
                spine.set_color(self.warna['border'])

        self.canvas_grade  = FigureCanvasTkAgg(self.fig_grade,  master=gr_inner)
        self.canvas_grade.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=14)
        self.canvas_status = FigureCanvasTkAgg(self.fig_status, master=pie_inner)
        self.canvas_status.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=14)

        self.update_statistik()

    # ==================== TAB RIWAYAT ====================
    def setup_tab_riwayat(self):
        wrap = tk.Frame(self.tab_riwayat, bg=self.warna['bg'])
        wrap.pack(fill="both", expand=True, padx=24, pady=24)

        title_bar = tk.Frame(wrap, bg=self.warna['bg'])
        title_bar.pack(fill="x", pady=(0, 14))
        tk.Label(title_bar, text="📜  Riwayat Aktivitas",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.warna['bg'], fg=self.warna['text']).pack(side="left")
        bf = tk.Frame(title_bar, bg=self.warna['bg']); bf.pack(side="right")
        self._make_btn(bf, "🔄  Refresh", self.refresh_riwayat, 'primary', small=True).pack(side="left", padx=4)
        self._make_btn(bf, "🗑️  Clear All", self.clear_riwayat, 'danger', small=True).pack(side="left", padx=4)

        outer, inner = self._section_card(wrap, self.warna['primary'])
        outer.pack(fill="both", expand=True)

        text_frame = tk.Frame(inner, bg=self.warna['surface'])
        text_frame.pack(fill="both", expand=True, padx=18, pady=18)

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.text_riwayat = tk.Text(text_frame, font=("Consolas", 10), wrap="word",
                                    yscrollcommand=scrollbar.set,
                                    bg=self.warna['surface_alt'], fg=self.warna['text'],
                                    relief="flat", bd=0, padx=14, pady=12)
        self.text_riwayat.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_riwayat.yview)

        self.refresh_riwayat()

    # ==================== UTILITAS / LOGIKA ====================
    def update_jumlah_data_label(self):
        if hasattr(self, 'jumlah_data_label'):
            self.jumlah_data_label.config(text=f"📊  Total: {len(self.data_mahasiswa)} data")

    def filter_by_ipk_range(self):
        try:
            min_ipk = float(self.ipk_min.get())
            max_ipk = float(self.ipk_max.get())
            if min_ipk > max_ipk:
                messagebox.showerror("Error", "Nilai IPK minimum tidak boleh lebih besar dari maksimum!")
                return
            for item in self.tree.get_children(): self.tree.delete(item)
            filtered = 0
            for i, m in enumerate(self.data_mahasiswa.values()):
                if min_ipk <= m.ipk <= max_ipk:
                    self.tree.insert("", "end",
                                     values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()),
                                     tags=('odd' if i % 2 else 'even',))
                    filtered += 1
            self.update_jumlah_data_label()
            self.tambah_riwayat(f"Filter IPK: {min_ipk:.2f} - {max_ipk:.2f} (hasil: {filtered} data)", "search")
            self.status_label.config(text=f"🎯 Filter IPK: {filtered} data ditemukan dalam range {min_ipk:.2f} - {max_ipk:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Masukkan nilai IPK yang valid!")

    def filter_daftar_by_ipk_range(self):
        try:
            min_ipk = float(self.ipk_min_daftar.get())
            max_ipk = float(self.ipk_max_daftar.get())
            if min_ipk > max_ipk:
                messagebox.showerror("Error", "Nilai IPK minimum tidak boleh lebih besar dari maksimum!")
                return
            for item in self.daftar_tree.get_children(): self.daftar_tree.delete(item)
            filtered = 0
            for m in self.data_mahasiswa.values():
                if min_ipk <= m.ipk <= max_ipk:
                    self.daftar_tree.insert("", "end",
                        values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()))
                    filtered += 1
            self.info_label_daftar.config(text=f"📊  Range {min_ipk:.2f} - {max_ipk:.2f}: {filtered} data")
            self.tambah_riwayat(f"Filter IPK Daftar: {min_ipk:.2f} - {max_ipk:.2f} (hasil: {filtered} data)", "search")
            self.status_label.config(text=f"🎯 Filter IPK: {filtered} data ditemukan dalam range {min_ipk:.2f} - {max_ipk:.2f}")
        except ValueError:
            messagebox.showerror("Error", "Masukkan nilai IPK yang valid!")

    def sort_daftar_mahasiswa(self):
        sort_by = self.combo_sort_daftar.get()
        daftar = list(self.data_mahasiswa.values())
        keymap = {
            "IPK Tertinggi":             (lambda x: x.ipk, True),
            "IPK Terendah":              (lambda x: x.ipk, False),
            "Nama A-Z":                  (lambda x: x.nama.lower(), False),
            "Nama Z-A":                  (lambda x: x.nama.lower(), True),
            "NIM Terkecil":              (lambda x: int(x.nim), False),
            "NIM Terbesar":              (lambda x: int(x.nim), True),
            "Keterangan (Lulus→Tidak)":  (lambda x: x.get_status_for_sort(), True),
            "Keterangan (Tidak→Lulus)":  (lambda x: x.get_status_for_sort(), False),
        }
        if sort_by in keymap:
            k, rev = keymap[sort_by]
            daftar.sort(key=k, reverse=rev)
        for item in self.daftar_tree.get_children(): self.daftar_tree.delete(item)
        for m in daftar:
            self.daftar_tree.insert("", "end",
                values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()))
        self.tambah_riwayat(f"Sort daftar: {sort_by}", "sort")
        self.status_label.config(text=f"✓ Data diurutkan berdasarkan: {sort_by}")

    def cari_daftar_mahasiswa(self):
        keyword = self.search_entry_daftar.get().strip().lower()
        for item in self.daftar_tree.get_children(): self.daftar_tree.delete(item)
        if not keyword:
            self.refresh_daftar_mahasiswa(); return
        found = 0
        for m in self.data_mahasiswa.values():
            if keyword in m.nim.lower() or keyword in m.nama.lower():
                self.daftar_tree.insert("", "end",
                    values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()))
                found += 1
        self.info_label_daftar.config(text=f"📊  Ditemukan: {found} data")
        self.status_label.config(text=f"🔍 Hasil pencarian: {found} data ditemukan")

    def refresh_daftar_mahasiswa(self):
        for item in self.daftar_tree.get_children(): self.daftar_tree.delete(item)
        for m in self.data_mahasiswa.values():
            self.daftar_tree.insert("", "end",
                values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()))
        self.info_label_daftar.config(text=f"📊  Total: {len(self.data_mahasiswa)} mahasiswa")
        self.search_entry_daftar.delete(0, tk.END)
        if hasattr(self, 'combo_sort_daftar'):
            self.combo_sort_daftar.set("IPK Tertinggi")
        self.ipk_min_daftar.delete(0, tk.END); self.ipk_min_daftar.insert(0, "0.00")
        self.ipk_max_daftar.delete(0, tk.END); self.ipk_max_daftar.insert(0, "4.00")

    def hapus_semua_data(self):
        if not self.data_mahasiswa:
            messagebox.showwarning("Peringatan", "Tidak ada data untuk dihapus!"); return
        confirm = messagebox.askyesno(
            "Konfirmasi Hapus Semua Data",
            f"⚠️ PERINGATAN!\n\nAnda akan menghapus SEMUA data mahasiswa.\n"
            f"Total data: {len(self.data_mahasiswa)} mahasiswa\n\n"
            f"Data yang dihapus TIDAK DAPAT DIKEMBALIKAN!\n\nApakah Anda yakin?",
            icon='warning')
        if confirm:
            jumlah = len(self.data_mahasiswa)
            self.data_mahasiswa.clear()
            self.save_data()
            self.refresh_tabel(); self.refresh_daftar_mahasiswa()
            self.update_dashboard(); self.update_statistik()
            self.reset_form(); self.update_jumlah_data_label()
            self.tambah_riwayat(f"Hapus semua data: {jumlah} mahasiswa", "delete")
            messagebox.showinfo("Sukses", f"✓ Berhasil menghapus {jumlah} data mahasiswa!")
            self.status_label.config(text=f"✓ Berhasil menghapus semua data ({jumlah} mahasiswa)")

    def tambah_mahasiswa(self):
        try:
            nim = str(self.entry_nim.get().strip())
            nama = self.entry_nama.get().strip()
            if not nim or not nama:
                messagebox.showerror("Error", "NIM dan Nama harus diisi!"); return
            if nim in self.data_mahasiswa:
                messagebox.showerror("Error", f"NIM {nim} sudah ada!"); return
            if not nim.isdigit():
                messagebox.showerror("Error", "NIM harus berupa angka!"); return
            nilai, sks = [], []
            for entry in self.entries_nilai:
                try:
                    n = int(entry["nilai"].get()); s = int(entry["sks"].get())
                    if n < 0 or n > 100:
                        messagebox.showerror("Error", f"Nilai {entry['nama']} harus 0-100!"); return
                    if s < 1 or s > 6:
                        messagebox.showerror("Error", f"SKS {entry['nama']} harus 1-6!"); return
                    nilai.append(n); sks.append(s)
                except ValueError:
                    messagebox.showerror("Error", f"Input {entry['nama']} tidak valid!"); return
            m = Mahasiswa(nim, nama, nilai[0], nilai[1], nilai[2], nilai[3], nilai[4],
                          sks[0], sks[1], sks[2], sks[3], sks[4])
            self.data_mahasiswa[nim] = m
            self.save_data()
            self.refresh_tabel(); self.refresh_daftar_mahasiswa()
            self.update_dashboard(); self.update_statistik()
            self.update_jumlah_data_label(); self.reset_form()
            self.tambah_riwayat(f"Tambah: {nama} ({nim}) - SKS: {m.total_sks}", "create")
            messagebox.showinfo("Sukses",
                f"✓ Mahasiswa {nama} berhasil ditambahkan!\n\nIPK: {m.ipk}\nStatus: {m.get_status()}\nTotal SKS: {m.total_sks}")
            self.status_label.config(text=f"✓ Berhasil menambah mahasiswa: {nama}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def edit_mahasiswa(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Silakan pilih data yang akan diedit!"); return
        item = self.tree.item(selected[0])
        nim = str(item["values"][0])
        if nim not in self.data_mahasiswa:
            messagebox.showerror("Error", "Data tidak ditemukan!"); return
        try:
            nama = self.entry_nama.get().strip()
            if not nama:
                messagebox.showerror("Error", "Nama harus diisi!"); return
            nilai, sks = [], []
            for entry in self.entries_nilai:
                try:
                    n = int(entry["nilai"].get()); s = int(entry["sks"].get())
                    if n < 0 or n > 100:
                        messagebox.showerror("Error", f"Nilai {entry['nama']} harus 0-100!"); return
                    if s < 1 or s > 6:
                        messagebox.showerror("Error", f"SKS {entry['nama']} harus 1-6!"); return
                    nilai.append(n); sks.append(s)
                except ValueError:
                    messagebox.showerror("Error", f"Input {entry['nama']} tidak valid!"); return
            nama_lama = self.data_mahasiswa[nim].nama
            sks_lama = self.data_mahasiswa[nim].total_sks
            m = Mahasiswa(nim, nama, nilai[0], nilai[1], nilai[2], nilai[3], nilai[4],
                          sks[0], sks[1], sks[2], sks[3], sks[4])
            self.data_mahasiswa[nim] = m
            self.save_data()
            self.refresh_tabel(); self.refresh_daftar_mahasiswa()
            self.update_dashboard(); self.update_statistik()
            self.tambah_riwayat(f"Edit: {nama_lama} -> {nama} (SKS: {sks_lama} -> {m.total_sks})", "update")
            messagebox.showinfo("Sukses",
                f"✓ Data {nama} berhasil diupdate!\n\nIPK: {m.ipk}\nStatus: {m.get_status()}\nTotal SKS: {m.total_sks}")
            self.status_label.config(text=f"✓ Berhasil mengedit mahasiswa: {nama}")
            self.reset_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def hapus_mahasiswa(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Peringatan", "Silakan pilih data yang akan dihapus!"); return
        item = self.tree.item(selected[0])
        nim = str(item["values"][0]); nama = item["values"][1]
        if messagebox.askyesno("Konfirmasi", f"Yakin ingin menghapus mahasiswa {nama}?"):
            if nim in self.data_mahasiswa:
                sks = self.data_mahasiswa[nim].total_sks
                del self.data_mahasiswa[nim]
                self.save_data()
                self.refresh_tabel(); self.refresh_daftar_mahasiswa()
                self.update_dashboard(); self.update_statistik()
                self.update_jumlah_data_label(); self.reset_form()
                self.tambah_riwayat(f"Hapus: {nama} ({nim}) - SKS: {sks}", "delete")
                messagebox.showinfo("Sukses", "✓ Data berhasil dihapus!")
                self.status_label.config(text=f"✓ Berhasil menghapus mahasiswa: {nama}")

    def reset_form(self):
        self.entry_nim.delete(0, tk.END)
        self.entry_nama.delete(0, tk.END)
        for entry in self.entries_nilai:
            entry["nilai"].delete(0, tk.END); entry["nilai"].insert(0, "0")
            entry["sks"].delete(0, tk.END);   entry["sks"].insert(0, "3")
        self.status_label.config(text="✓ Form telah direset")

    def refresh_tabel(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, m in enumerate(self.data_mahasiswa.values()):
            self.tree.insert("", "end",
                             values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()),
                             tags=('odd' if i % 2 else 'even',))
        self.update_jumlah_data_label()
        if hasattr(self, 'ipk_min'):
            self.ipk_min.delete(0, tk.END); self.ipk_min.insert(0, "0.00")
            self.ipk_max.delete(0, tk.END); self.ipk_max.insert(0, "4.00")

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        nim = str(item["values"][0])
        if nim in self.data_mahasiswa:
            m = self.data_mahasiswa[nim]
            self.entry_nim.delete(0, tk.END);  self.entry_nim.insert(0, m.nim)
            self.entry_nama.delete(0, tk.END); self.entry_nama.insert(0, m.nama)
            for i, entry in enumerate(self.entries_nilai):
                if i < len(m.mk):
                    entry["nilai"].delete(0, tk.END); entry["nilai"].insert(0, str(m.mk[i]["nilai"]))
                    entry["sks"].delete(0, tk.END);   entry["sks"].insert(0, str(m.mk[i]["sks"]))

    def cari_mahasiswa(self):
        keyword = self.entry_cari.get().strip().lower()
        if not keyword:
            self.refresh_tabel(); return
        for item in self.tree.get_children(): self.tree.delete(item)
        found = 0
        for i, m in enumerate(self.data_mahasiswa.values()):
            if keyword in m.nim.lower() or keyword in m.nama.lower():
                self.tree.insert("", "end",
                                 values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()),
                                 tags=('odd' if i % 2 else 'even',))
                found += 1
        self.update_jumlah_data_label()
        self.tambah_riwayat(f"Cari: '{keyword}' (ditemukan {found})", "search")
        self.status_label.config(text=f"🔍 Hasil pencarian: {found} data ditemukan")

    def sort_mahasiswa(self):
        sort_by = self.combo_sort.get()
        daftar = list(self.data_mahasiswa.values())
        keymap = {
            "IPK Tertinggi":            (lambda x: x.ipk, True),
            "IPK Terendah":             (lambda x: x.ipk, False),
            "Nama A-Z":                 (lambda x: x.nama.lower(), False),
            "Nama Z-A":                 (lambda x: x.nama.lower(), True),
            "Keterangan (Lulus→Tidak)": (lambda x: x.get_status_for_sort(), True),
            "Keterangan (Tidak→Lulus)": (lambda x: x.get_status_for_sort(), False),
        }
        if sort_by in keymap:
            k, rev = keymap[sort_by]; daftar.sort(key=k, reverse=rev)
        for item in self.tree.get_children(): self.tree.delete(item)
        for i, m in enumerate(daftar):
            self.tree.insert("", "end",
                             values=(m.nim, m.nama, m.ipk, m.total_sks, m.get_status_icon()),
                             tags=('odd' if i % 2 else 'even',))
        self.tambah_riwayat(f"Sort: {sort_by}", "sort")
        self.status_label.config(text=f"✓ Data diurutkan berdasarkan: {sort_by}")

    def show_nilai_detail(self, event):
        selected = self.daftar_tree.selection()
        if not selected: return
        item = self.daftar_tree.item(selected[0])
        nim = str(item["values"][0])
        if nim not in self.data_mahasiswa: return
        m = self.data_mahasiswa[nim]

        win = tk.Toplevel(self.root)
        win.title(f"Detail Nilai - {m.nama}")
        win.geometry("640x600")
        win.configure(bg=self.warna['surface'])
        win.resizable(False, False)
        win.transient(self.root); win.grab_set()
        
        # Pusatkan jendela popup ke tengah layar
        win.update_idletasks()
        w_win, h_win = 640, 600
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - w_win) // 2
        y = (sh - h_win) // 2
        win.geometry(f"{w_win}x{h_win}+{x}+{y}")

        # Header
        header = tk.Frame(win, bg=self.warna['primary'], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Close button
        close_btn = tk.Button(header, text="✕", command=win.destroy,
                              bg=self.warna['primary'], fg='white',
                              font=("Segoe UI", 12, "bold"),
                              relief="flat", bd=0, padx=12, pady=0,
                              cursor="hand2", activebackground=self.warna['danger'])
        close_btn.pack(side="right", padx=10, pady=5)
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg=self.warna['danger']))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg=self.warna['primary']))
        
        tk.Frame(header, bg=self.warna['accent'], height=3).pack(fill="x", side="bottom")
        tk.Label(header, text="📘  Detail Nilai Mahasiswa",
                 font=("Segoe UI", 14, "bold"),
                 bg=self.warna['primary'], fg='#ffffff').pack(pady=15)

        # Info card
        info_outer = tk.Frame(win, bg=self.warna['border'])
        info_outer.pack(fill="x", padx=22, pady=(18, 10))
        info_inner = tk.Frame(info_outer, bg=self.warna['surface_alt'])
        info_inner.pack(fill="both", padx=1, pady=1)
        grid = tk.Frame(info_inner, bg=self.warna['surface_alt'])
        grid.pack(fill="x", padx=18, pady=14)

        def info_pair(parent, label, value, col):
            cell = tk.Frame(parent, bg=self.warna['surface_alt'])
            cell.grid(row=0, column=col, sticky="w", padx=(0, 22))
            tk.Label(cell, text=label.upper(), font=("Segoe UI", 8, "bold"),
                     bg=self.warna['surface_alt'], fg=self.warna['text_muted']).pack(anchor="w")
            tk.Label(cell, text=value, font=("Segoe UI", 11, "bold"),
                     bg=self.warna['surface_alt'], fg=self.warna['text']).pack(anchor="w")

        info_pair(grid, "NIM",       m.nim, 0)
        info_pair(grid, "Nama",      m.nama, 1)
        info_pair(grid, "IPK",       f"{m.ipk}", 2)
        info_pair(grid, "Status",    m.get_status(), 3)
        info_pair(grid, "Total SKS", str(m.total_sks), 4)

        # Table
        table_frame = tk.Frame(win, bg=self.warna['surface'])
        table_frame.pack(fill="both", expand=True, padx=22, pady=10)

        columns_nilai = ("Mata Kuliah", "Nilai", "SKS", "Grade", "Bobot")
        nilai_tree = ttk.Treeview(table_frame, columns=columns_nilai, show="headings", height=6)
        col_widths = [220, 80, 60, 80, 80]
        for col, w in zip(columns_nilai, col_widths):
            nilai_tree.heading(col, text=col)
            nilai_tree.column(col, width=w, anchor="center")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=nilai_tree.yview)
        nilai_tree.configure(yscrollcommand=scroll.set)
        nilai_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for mk in m.mk:
            nilai_tree.insert("", "end", values=(mk["nama"], mk["nilai"], mk["sks"], mk["grade"], mk["bobot"]))

        footer = tk.Frame(win, bg=self.warna['surface'])
        footer.pack(fill="x", side="bottom", pady=(10, 18))
        self._make_btn(footer, "Tutup", win.destroy, 'primary').pack()

    def update_statistik(self):
        if not hasattr(self, 'stat_cards'): return

        if not self.data_mahasiswa:
            for key in self.stat_cards: 
                self.stat_cards[key].config(text="0")
            self.max_ipk_label.config(text="0.00")
            self.max_nama_label.config(text="-")
            self.min_ipk_label.config(text="0.00")
            self.min_nama_label.config(text="-")
            
            if hasattr(self, 'ax_grade'):
                self.ax_grade.clear()
                self.ax_grade.text(0.5, 0.5, "Belum ada data", ha="center", va="center",
                                   transform=self.ax_grade.transAxes,
                                   fontsize=12, color=self.warna['text_muted'])
                self.ax_grade.set_xticks([])
                self.ax_grade.set_yticks([])
                self.canvas_grade.draw()
            
            if hasattr(self, 'ax_status'):
                self.ax_status.clear()
                self.ax_status.text(0.5, 0.5, "Belum ada data", ha="center", va="center",
                                    transform=self.ax_status.transAxes,
                                    fontsize=12, color=self.warna['text_muted'])
                self.ax_status.set_xticks([])
                self.ax_status.set_yticks([])
                self.canvas_status.draw()
            return

        total = len(self.data_mahasiswa)
        lulus       = sum(1 for m in self.data_mahasiswa.values() if m.get_status() == "Lulus")
        tangguh     = sum(1 for m in self.data_mahasiswa.values() if m.get_status() == "Tangguh")
        tidak_lulus = sum(1 for m in self.data_mahasiswa.values() if m.get_status() == "Tidak Lulus")

        ipk_list = [m.ipk for m in self.data_mahasiswa.values()]
        rata_ipk = sum(ipk_list) / total
        persen_lulus = (lulus / total) * 100

        ipk_tertinggi = max(ipk_list)
        ipk_terendah = min(ipk_list)
        mahasiswa_tertinggi = [m for m in self.data_mahasiswa.values() if m.ipk == ipk_tertinggi]
        mahasiswa_terendah  = [m for m in self.data_mahasiswa.values() if m.ipk == ipk_terendah]

        def fmt_list(lst):
            if len(lst) == 1:
                m = lst[0]
                return f"{m.nama} ({m.nim}) — {m.total_sks} SKS"
            return "\n".join(f"• {m.nama} ({m.nim}) — {m.total_sks} SKS" for m in lst)

        self.stat_cards['total_mhs'].config(text=str(total))
        self.stat_cards['avg_ipk'].config(text=f"{rata_ipk:.2f}")
        self.stat_cards['pass_rate'].config(text=f"{persen_lulus:.1f}%")

        self.max_ipk_label.config(text=f"{ipk_tertinggi:.2f}")
        self.max_nama_label.config(text=fmt_list(mahasiswa_tertinggi))
        self.min_ipk_label.config(text=f"{ipk_terendah:.2f}")
        self.min_nama_label.config(text=fmt_list(mahasiswa_terendah))

        # ===== Diagram Batang: Distribusi Grade A-E =====
        if hasattr(self, 'ax_grade'):
            grade_count = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
            for m in self.data_mahasiswa.values():
                for mk in m.mk:
                    g = mk["grade"][0]
                    if g in grade_count:
                        grade_count[g] += 1
            self.ax_grade.clear()
            warna_grade = [self.warna['success'], self.warna['info'],
                           self.warna['warning'], self.warna['orange'], self.warna['danger']]
            bars = self.ax_grade.bar(list(grade_count.keys()), list(grade_count.values()),
                                     color=warna_grade, edgecolor='white', linewidth=1.4, width=0.62)
            self.ax_grade.set_xlabel("Grade", fontsize=10, color=self.warna['text_muted'])
            self.ax_grade.set_ylabel("Jumlah Mata Kuliah", fontsize=10, color=self.warna['text_muted'])
            self.ax_grade.tick_params(colors=self.warna['text_muted'])
            self.ax_grade.grid(True, alpha=0.25, axis='y', linestyle='--')
            for s in self.ax_grade.spines.values(): 
                s.set_color(self.warna['border'])
            max_h = max(grade_count.values()) if any(grade_count.values()) else 1
            self.ax_grade.set_ylim(0, max_h * 1.18)
            for b in bars:
                h = b.get_height()
                self.ax_grade.text(b.get_x() + b.get_width()/2, h,
                                   f'{int(h)}', ha='center', va='bottom',
                                   fontsize=11, fontweight='bold', color=self.warna['text'])
            self.canvas_grade.draw()

        # ===== Diagram Lingkaran: Persentase Status (Lulus, Tangguh, Tidak Lulus) =====
        if hasattr(self, 'ax_status'):
            self.ax_status.clear()
            labels  = ["Lulus", "Tangguh", "Tidak Lulus"]
            values  = [lulus, tangguh, tidak_lulus]
            colors  = [self.warna['success'], self.warna['orange'], self.warna['danger']]
            
            labels_f = [l for l, v in zip(labels, values) if v > 0]
            values_f = [v for v in values if v > 0]
            colors_f = [c for c, v in zip(colors, values) if v > 0]
            total_v  = sum(values_f)

            def autopct_fmt(pct):
                count = int(round(pct * total_v / 100.0))
                return f"{count}\n({pct:.1f}%)"

            if total_v > 0:
                wedges, texts, autotexts = self.ax_status.pie(
                    values_f, labels=labels_f, colors=colors_f,
                    autopct=autopct_fmt, startangle=90,
                    wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                    textprops={'fontsize': 10, 'color': self.warna['text']},
                    pctdistance=0.72,
                )
                for at in autotexts:
                    at.set_color('white')
                    at.set_fontweight('bold')
                    at.set_fontsize(9)
            self.ax_status.set_aspect('equal')
            self.ax_status.set_title(f"Total Mahasiswa: {total}", fontsize=11, 
                                      fontweight='bold', color=self.warna['text'], pad=15)
            self.canvas_status.draw()

        self.tambah_riwayat("Lihat statistik", "stats")
        self.status_label.config(text="✓ Statistik telah diperbarui")

    def tambah_riwayat(self, pesan, tipe):
        waktu = datetime.now().strftime("%H:%M:%S")
        icon = {"create": "➕", "update": "✏️", "delete": "🗑️", "search": "🔍",
                "sort": "🔄", "stats": "📊", "export": "📎", "import": "📂",
                "info": "ℹ️"}.get(tipe, "📌")
        self.riwayat.append(f"[{waktu}] {icon} {pesan}\n")
        self.refresh_riwayat()

    def refresh_riwayat(self):
        self.text_riwayat.delete(1.0, tk.END)
        if not self.riwayat:
            self.text_riwayat.insert(tk.END,
                "Belum ada riwayat aktivitas.\n\nSilakan lakukan operasi seperti menambah, mengedit, atau menghapus data.")
            return
        header = "═" * 68 + "\n"
        header += "  📜  RIWAYAT 20 AKTIVITAS TERAKHIR\n"
        header += "═" * 68 + "\n\n"
        self.text_riwayat.insert(tk.END, header)
        for i, entry in enumerate(reversed(self.riwayat), 1):
            self.text_riwayat.insert(tk.END, f"  {i:2d}. {entry}")
        self.text_riwayat.insert(tk.END, "\n" + "═" * 68)

    def clear_riwayat(self):
        if messagebox.askyesno("Konfirmasi", "Yakin ingin menghapus semua riwayat?"):
            self.riwayat.clear()
            self.tambah_riwayat("Riwayat dibersihkan", "info")
            self.status_label.config(text="✓ Riwayat telah dibersihkan")

    def export_csv(self):
        if not self.data_mahasiswa:
            messagebox.showwarning("Peringatan", "Tidak ada data untuk diexport!"); return
        filename = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV files", "*.csv")])
        if filename:
            try:
                data = []
                for m in self.data_mahasiswa.values():
                    row = {"NIM": m.nim, "Nama": m.nama, "IPK": m.ipk,
                           "Status": m.get_status(), "Total_SKS": m.total_sks}
                    for i, mk in enumerate(m.mk, 1):
                        row[f"Mata_Kuliah_{i}"] = mk["nama"]
                        row[f"Nilai_{i}"]       = mk["nilai"]
                        row[f"SKS_{i}"]         = mk["sks"]
                        row[f"Grade_{i}"]       = mk["grade"]
                    data.append(row)
                pd.DataFrame(data).to_csv(filename, index=False, encoding="utf-8-sig")
                messagebox.showinfo("Sukses", f"✓ Data berhasil diexport ke:\n{filename}")
                self.tambah_riwayat(f"Export CSV: {len(data)} data", "export")
                self.status_label.config(text=f"✓ Export {len(data)} data ke CSV")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def import_csv(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filename: return
        try:
            df = pd.read_csv(filename, encoding="utf-8-sig")
            if "NIM" not in df.columns or "Nama" not in df.columns:
                messagebox.showerror("Error", "Format CSV tidak sesuai!\n\nDiperlukan kolom: NIM, Nama"); return
            imported = skipped = 0
            for _, row in df.iterrows():
                try:
                    nim = str(row["NIM"]); nama = str(row["Nama"])
                    if nim in self.data_mahasiswa: skipped += 1; continue
                    nilai, sks = [], []
                    for i in range(1, 6):
                        if f"Nilai_{i}" in df.columns:
                            n = int(row.get(f"Nilai_{i}", 0)); s = int(row.get(f"SKS_{i}", 3))
                        else:
                            n = 0; s = 3
                        nilai.append(n); sks.append(s)
                    m = Mahasiswa(nim, nama, nilai[0], nilai[1], nilai[2], nilai[3], nilai[4],
                                  sks[0], sks[1], sks[2], sks[3], sks[4])
                    self.data_mahasiswa[nim] = m
                    imported += 1
                except Exception:
                    skipped += 1
                    continue
            self.save_data()
            self.refresh_tabel(); self.refresh_daftar_mahasiswa()
            self.update_dashboard(); self.update_statistik()
            self.update_jumlah_data_label()
            self.tambah_riwayat(f"Import CSV: {imported} data baru, {skipped} skip", "import")
            messagebox.showinfo("Sukses", f"✓ Import selesai!\n\nData baru: {imported}\nData skip (duplikat): {skipped}")
            self.status_label.config(text=f"✓ Import {imported} data dari CSV")
        except Exception as e:
            messagebox.showerror("Error", f"Gagal import CSV:\n{str(e)}")

    def save_data(self):
        try:
            data = {nim: m.to_dict() for nim, m in self.data_mahasiswa.items()}
            with open(self.file_data, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving: {e}")

    def load_data(self):
        try:
            if not os.path.exists(self.file_data):
                self.save_data(); return
            with open(self.file_data, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip(): return
                f.seek(0); data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "nim" in item:
                        nim = str(item["nim"])
                        self.data_mahasiswa[nim] = Mahasiswa.from_dict(item)
            else:
                for nim, m_data in data.items():
                    self.data_mahasiswa[str(nim)] = Mahasiswa.from_dict(m_data)
            self.status_label.config(text=f"✓ Load {len(self.data_mahasiswa)} data mahasiswa")
        except Exception as e:
            print(f"Error loading: {e}")
            self.data_mahasiswa = {}


# ==================== MAIN ====================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    app = AplikasiAkademik(root)
    root.update_idletasks()

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    width = min(1440, max(1100, sw - 80))
    height = min(860, max(680, sh - 120))

    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 3)

    root.geometry(f'{width}x{height}+{x}+{y}')
    root.minsize(1100, 680)
    root.resizable(True, True)

    root.deiconify()
    root.lift()
    root.focus_force()
    try:
        root.attributes('-topmost', True)
        root.after(200, lambda: root.attributes('-topmost', False))
    except Exception:
        pass

    root.mainloop()