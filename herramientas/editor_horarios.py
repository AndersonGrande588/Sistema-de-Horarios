#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Editor local de horarios  —  HERRAMIENTA INTERNA (no forma parte de la web).

Permite agregar, editar, eliminar y duplicar turnos de cada técnico sin tocar
el JSON a mano. Guarda directamente en HORARIOS/horarios/<id>.json y hace un
respaldo automático antes de sobrescribir.

Uso:
    python -X utf8 herramientas/editor_horarios.py

En Windows también puedes hacer doble clic en INICIAR_EDITOR.bat
"""

import calendar
import datetime
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

# ─────────────────────────────────────────────────────────────
#  Rutas y constantes
# ─────────────────────────────────────────────────────────────
AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
HORARIOS = BASE / "HORARIOS"
HOR = HORARIOS / "horarios"
PERSONAS_JSON = HORARIOS / "personas.json"
RESPALDOS = AQUI / ".respaldos"

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
         "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
MES_NUM = {m: i + 1 for i, m in enumerate(MESES)}

STORE_NAMES = {
    "tienda1": "C.C Colina",
    "tienda2": "Zona Calle 82",
    "tienda3": "C.C Felicidad",
    "tienda4": "C.C Plaza Central",
    "tienda5": "C.C Unicentro",
    "tienda6": "Oficina Colina",
    "tienda7": "C.C Titan",
    "tienda8": "C.C Fontanar",
    "tienda9": "Bima",
}

HORA_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


# ─────────────────────────────────────────────────────────────
#  Lógica de datos (independiente de la interfaz)
# ─────────────────────────────────────────────────────────────
def week_index(year, month, day):
    """Semana del mes (1..6) con el mismo criterio que los JSON existentes."""
    d = datetime.date(year, month, day)
    first = datetime.date(year, month, 1)
    return (day - 1 - d.weekday() + first.weekday()) // 7 + 1


def build_shift(store, year, month, day, typ, start=None, end=None):
    """Crea el turno con el esquema exacto que usa la app."""
    dt = datetime.date(year, month, day)
    rec = {
        "store": store,
        "storeName": STORE_NAMES[store],
        "month": MESES[month - 1],
        "year": year,
        "date": dt.isoformat(),
        "dayNumber": day,
        "weekday": DIAS[dt.weekday()],
        "week": "Semana %d" % week_index(year, month, day),
    }
    if typ == "guardia":
        rec["type"] = "guardia"
    else:
        rec["start"] = start
        rec["end"] = end
        rec["type"] = "normal"
    return rec


def load_personas(base=BASE):
    with open(base / "HORARIOS" / "personas.json", encoding="utf-8") as f:
        return json.load(f)


def load_doc(hor_dir, pid, name):
    path = Path(hor_dir) / ("%s.json" % pid)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        doc.setdefault("id", pid)
        doc.setdefault("name", name)
        doc.setdefault("shifts", [])
        return doc
    return {"id": pid, "name": name, "shifts": []}


def current_year(docs, fallback=2026):
    years = [s.get("year") for d in docs.values() for s in d.get("shifts", [])
             if isinstance(s.get("year"), int)]
    return max(years) if years else fallback


def analyze(doc, cand, ignore_index=None):
    """Valida un turno candidato contra el documento.

    Devuelve (errores, indices_normales_a_reemplazar, hay_guardia_ese_dia).
    """
    errors = []
    repl = []
    guardia_day = False

    if cand.get("store") not in STORE_NAMES:
        errors.append("Selecciona una tienda válida.")

    if cand.get("type") not in ("normal", "guardia"):
        errors.append("Tipo de turno inválido.")
    elif cand["type"] == "normal":
        st, en = cand.get("start"), cand.get("end")
        if not st or not en:
            errors.append("La jornada normal necesita hora de inicio y fin.")
        else:
            if not HORA_RE.match(st) or not HORA_RE.match(en):
                errors.append("Las horas deben tener formato HH:MM (ej. 08:00).")
            elif st >= en:
                errors.append("La hora de inicio debe ser menor que la de fin.")

    for i, s in enumerate(doc.get("shifts", [])):
        if i == ignore_index:
            continue
        if s.get("date") != cand.get("date"):
            continue
        if s.get("store") == cand.get("store") and s.get("type") == cand.get("type"):
            errors.append("Ya existe un turno %s en %s para esa fecha." %
                          ("de guardia" if cand["type"] == "guardia" else "normal",
                           STORE_NAMES.get(cand["store"], cand["store"])))
            break

    for i, s in enumerate(doc.get("shifts", [])):
        if i == ignore_index or s.get("date") != cand.get("date"):
            continue
        if cand.get("type") == "guardia" and s.get("type") == "normal":
            repl.append(i)
        elif cand.get("type") == "normal" and s.get("type") == "guardia":
            guardia_day = True

    return errors, repl, guardia_day


def normalize_doc(doc):
    """Ordena los turnos y deja el documento listo para guardar."""
    doc["shifts"].sort(key=lambda r: (r.get("date", ""), r.get("store", ""),
                                      r.get("type", "")))
    return doc


def save_doc(doc, hor_dir=HOR, backup_dir=RESPALDOS):
    """Escribe el JSON con respaldo previo. Devuelve la ruta escrita."""
    normalize_doc(doc)
    hor_dir = Path(hor_dir)
    backup_dir = Path(backup_dir)
    hor_dir.mkdir(parents=True, exist_ok=True)
    path = hor_dir / ("%s.json" % doc["id"])

    if path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(path, backup_dir / ("%s_%s.json" % (doc["id"], stamp)))

    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

    # conservar solo los 40 respaldos más recientes
    backups = sorted(backup_dir.glob("%s_*.json" % doc["id"]))
    for old in backups[:-40]:
        try:
            old.unlink()
        except OSError:
            pass
    return path


# ─────────────────────────────────────────────────────────────
#  Interfaz (Tkinter)
# ─────────────────────────────────────────────────────────────
def run_gui(test=False):
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog

    class EditorApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Editor de Horarios — herramienta local")
            self.geometry("1180x760")
            self.minsize(1000, 640)
            self.configure(bg="#f3f4f6")

            self.personas = load_personas(BASE)
            self.docs = {}
            self.current_pid = None
            self.current_month = ""
            self.dirty = set()
            self.ignore_index = None      # índice del turno en edición
            self.selected_shift = None    # turno cargado en el formulario
            self.year = 2026
            self._suppress_events = False

            style = ttk.Style(self)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
            style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
            style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))
            style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
            style.configure("TLabel", background="#f3f4f6", font=("Segoe UI", 10))
            style.configure("Title.TLabel", font=("Segoe UI", 11, "bold"))
            style.configure("Hint.TLabel", foreground="#6b7280", font=("Segoe UI", 9))
            style.configure("TLabelframe", background="#f3f4f6")
            style.configure("TLabelframe.Label", background="#f3f4f6",
                            font=("Segoe UI", 10, "bold"))

            self._build_ui()
            self._load_docs()
            self.year = current_year(self.docs)
            self._fill_personas()

            self.protocol("WM_DELETE_WINDOW", self._on_close)
            self.bind("<Control-s>", lambda e: self._save())
            self.bind("<Control-n>", lambda e: self._new_shift())
            self.bind("<Delete>", lambda e: self._delete())

        # ---------- construcción de la interfaz ----------
        def _build_ui(self):
            top = ttk.Frame(self, padding=(14, 12, 14, 6))
            top.pack(fill="x")

            ttk.Label(top, text="👤 Técnico").pack(side="left")
            self.persona_var = tk.StringVar()
            self.cb_persona = ttk.Combobox(top, textvariable=self.persona_var,
                                           state="readonly", width=30)
            self.cb_persona.pack(side="left", padx=(8, 18))
            self.cb_persona.bind("<<ComboboxSelected>>", self._on_persona_change)

            ttk.Label(top, text="📅 Mes").pack(side="left")
            self.mes_var = tk.StringVar()
            self.cb_mes = ttk.Combobox(top, textvariable=self.mes_var,
                                       state="readonly", width=14,
                                       values=MESES)
            self.cb_mes.pack(side="left", padx=(8, 0))
            self.cb_mes.bind("<<ComboboxSelected>>", self._on_month_change)

            self.lbl_estado = ttk.Label(top, text="", style="Hint.TLabel")
            self.lbl_estado.pack(side="right")

            bar = ttk.Frame(self, padding=(14, 0, 14, 8))
            bar.pack(fill="x")
            ttk.Button(bar, text="＋ Nuevo turno", command=self._new_shift).pack(side="left")
            ttk.Button(bar, text="⧉ Duplicar día…", command=self._duplicate_day).pack(side="left", padx=6)
            ttk.Button(bar, text="⬇ Recargar desde disco", command=self._reload).pack(side="left")
            ttk.Button(bar, text="💾 Guardar (Ctrl+S)", style="Accent.TButton",
                       command=self._save).pack(side="right")
            self.lbl_dirty = ttk.Label(bar, text="", style="Hint.TLabel")
            self.lbl_dirty.pack(side="right", padx=10)

            main = ttk.Frame(self, padding=(14, 0, 14, 8))
            main.pack(fill="both", expand=True)
            main.columnconfigure(0, weight=1)
            main.columnconfigure(1, weight=0)
            main.rowconfigure(0, weight=1)

            # --- tabla de turnos ---
            box = ttk.LabelFrame(main, text="Turnos del mes", padding=8)
            box.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
            box.rowconfigure(0, weight=1)
            box.columnconfigure(0, weight=1)

            cols = ("fecha", "dia", "semana", "tienda", "tipo", "horario")
            self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
            heads = {"fecha": ("Fecha", 92), "dia": ("Día", 92), "semana": ("Semana", 82),
                     "tienda": ("Tienda", 150), "tipo": ("Tipo", 92),
                     "horario": ("Horario", 120)}
            for c in cols:
                text, width = heads[c]
                self.tree.heading(c, text=text)
                self.tree.column(c, width=width, anchor="w" if c == "tienda" else "center")
            self.tree.tag_configure("guardia", background="#fff1e0")
            self.tree.grid(row=0, column=0, sticky="nsew")
            self.tree.bind("<<TreeviewSelect>>", self._on_select)

            sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
            sb.grid(row=0, column=1, sticky="ns")
            self.tree.configure(yscrollcommand=sb.set)

            self.lbl_count = ttk.Label(box, text="", style="Hint.TLabel")
            self.lbl_count.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

            # --- formulario ---
            form = ttk.LabelFrame(main, text="Turno", padding=12)
            form.grid(row=0, column=1, sticky="ns")
            form.columnconfigure(0, weight=1)

            self.lbl_modo = ttk.Label(form, text="Nuevo turno", style="Title.TLabel")
            self.lbl_modo.grid(row=0, column=0, sticky="w", pady=(0, 10))

            ttk.Label(form, text="Día del mes").grid(row=1, column=0, sticky="w")
            self.dia_var = tk.StringVar()
            self.cb_dia = ttk.Combobox(form, textvariable=self.dia_var,
                                       state="readonly", width=28)
            self.cb_dia.grid(row=2, column=0, sticky="ew", pady=(2, 8))
            self.cb_dia.bind("<<ComboboxSelected>>", self._on_day_change)

            self.lbl_fecha = ttk.Label(form, text="", style="Hint.TLabel")
            self.lbl_fecha.grid(row=3, column=0, sticky="w", pady=(0, 8))

            ttk.Label(form, text="Tienda").grid(row=4, column=0, sticky="w")
            self.tienda_var = tk.StringVar()
            self.cb_tienda = ttk.Combobox(form, textvariable=self.tienda_var,
                                          state="readonly", width=28)
            self.cb_tienda.grid(row=5, column=0, sticky="ew", pady=(2, 8))

            ttk.Label(form, text="Tipo de turno").grid(row=6, column=0, sticky="w")
            self.tipo_var = tk.StringVar()
            self.cb_tipo = ttk.Combobox(form, textvariable=self.tipo_var,
                                        state="readonly", width=28,
                                        values=["Jornada normal", "Guardia"])
            self.cb_tipo.grid(row=7, column=0, sticky="ew", pady=(2, 8))
            self.cb_tipo.bind("<<ComboboxSelected>>", self._on_type_change)

            times = ttk.Frame(form)
            times.grid(row=8, column=0, sticky="ew", pady=(0, 10))
            times.columnconfigure(1, weight=1)
            times.columnconfigure(3, weight=1)
            ttk.Label(times, text="Inicio").grid(row=0, column=0, sticky="w")
            self.ent_ini = ttk.Entry(times, width=8)
            self.ent_ini.grid(row=0, column=1, sticky="ew", padx=(6, 12))
            ttk.Label(times, text="Fin").grid(row=0, column=2, sticky="w")
            self.ent_fin = ttk.Entry(times, width=8)
            self.ent_fin.grid(row=0, column=3, sticky="ew", padx=(6, 0))

            self.btn_aplicar = ttk.Button(form, text="✔ Aplicar", style="Accent.TButton",
                                          command=self._apply)
            self.btn_aplicar.grid(row=9, column=0, sticky="ew", pady=(4, 4))
            self.btn_limpiar = ttk.Button(form, text="Limpiar", command=self._new_shift)
            self.btn_limpiar.grid(row=10, column=0, sticky="ew", pady=2)
            self.btn_eliminar = ttk.Button(form, text="🗑 Eliminar turno", command=self._delete)
            self.btn_eliminar.grid(row=11, column=0, sticky="ew", pady=2)

            ttk.Separator(form).grid(row=12, column=0, sticky="ew", pady=10)
            ttk.Label(form, text=("Los cambios se aplican en memoria.\n"
                                  "Pulsa «Guardar» para escribir el JSON\n"
                                  "(se crea un respaldo automático)."),
                      style="Hint.TLabel", justify="left").grid(row=13, column=0, sticky="w")

            # --- barra inferior ---
            bottom = ttk.Frame(self, padding=(14, 0, 14, 10))
            bottom.pack(fill="x")
            self.lbl_archivo = ttk.Label(bottom, text="", style="Hint.TLabel")
            self.lbl_archivo.pack(side="left")
            ttk.Label(bottom, text="Herramienta local · no hace parte de la web",
                      style="Hint.TLabel").pack(side="right")

        # ---------- datos ----------
        def _load_docs(self):
            self.docs = {}
            for p in self.personas:
                self.docs[p["id"]] = load_doc(HOR, p["id"], p.get("name", p["id"]))

        def _fill_personas(self):
            labels = ["%s — %s" % (p.get("name", p["id"]), p["id"]) for p in self.personas]
            self.cb_persona["values"] = labels
            if not self.personas:
                self.lbl_estado.config(text="No se encontraron técnicos en personas.json")
                return
            self.current_pid = self.personas[0]["id"]
            self.cb_persona.current(0)

            hoy = datetime.date.today()
            default = MESES[hoy.month - 1] if hoy.year == self.year else "Septiembre"
            self.current_month = default
            self.mes_var.set(default)
            self._new_shift()
            self._refresh()

        def _doc(self):
            return self.docs.get(self.current_pid, {"id": self.current_pid, "shifts": []})

        def _month_shifts(self):
            doc = self._doc()
            return [(i, s) for i, s in enumerate(doc.get("shifts", []))
                    if s.get("month") == self.current_month]

        # ---------- refresco de pantalla ----------
        def _refresh(self):
            self._suppress_events = True
            try:
                self.tree.delete(*self.tree.get_children())
                rows = self._month_shifts()
                rows.sort(key=lambda t: (t[1].get("date", ""), t[1].get("store", ""),
                                         t[1].get("type", "")))
                for idx, s in rows:
                    hora = "🛡 Guardia" if s.get("type") == "guardia" else \
                        "%s–%s" % (s.get("start", ""), s.get("end", ""))
                    tipo = "Guardia" if s.get("type") == "guardia" else "Normal"
                    self.tree.insert("", "end", iid=str(idx), values=(
                        s.get("date", ""), s.get("weekday", ""), s.get("week", ""),
                        STORE_NAMES.get(s.get("store"), s.get("storeName", "")),
                        tipo, hora),
                        tags=("guardia",) if s.get("type") == "guardia" else ())

                n = len(rows)
                g = sum(1 for _, s in rows if s.get("type") == "guardia")
                m = MES_NUM[self.current_month]
                dias = calendar.monthrange(self.year, m)[1]
                total_semanas = week_index(self.year, m, dias)
                self.lbl_count.config(text="%d turnos · %d guardias · Semana 1–%d" %
                                      (n, g, total_semanas))

                self.cb_dia["values"] = [str(d) for d in range(1, dias + 1)]
                if self.dia_var.get() and int(self.dia_var.get()) > dias:
                    self.dia_var.set("1")

                self.lbl_archivo.config(
                    text="Archivo: HORARIOS/horarios/%s.json  ·  Año %d" %
                         (self.current_pid, self.year))
                self._update_dirty_label()
                self._update_day_label()
            finally:
                self._suppress_events = False

        def _update_day_label(self):
            try:
                day = int(self.dia_var.get())
            except (TypeError, ValueError):
                self.lbl_fecha.config(text="")
                return
            m = MES_NUM[self.current_month]
            dt = datetime.date(self.year, m, day)
            self.lbl_fecha.config(text="%s · %s" % (DIAS[dt.weekday()],
                                                    "Semana %d" % week_index(self.year, m, day)))

        def _update_dirty_label(self):
            if self.dirty:
                self.lbl_dirty.config(text="● Cambios sin guardar")
                self.lbl_estado.config(text="● Sin guardar: %s" % ", ".join(sorted(self.dirty)))
            else:
                self.lbl_dirty.config(text="")
                self.lbl_estado.config(text="✔ Todo guardado")

        # ---------- eventos ----------
        def _on_persona_change(self, _evt=None):
            if self._suppress_events:
                return
            idx = self.cb_persona.current()
            pid = self.personas[idx]["id"]
            if pid == self.current_pid:
                return
            if not self._maybe_save():
                self.cb_persona.current(self.personas.index(
                    next(p for p in self.personas if p["id"] == self.current_pid)))
                return
            self.current_pid = pid
            self._new_shift()
            self._refresh()

        def _on_month_change(self, _evt=None):
            if self._suppress_events:
                return
            mes = self.mes_var.get()
            if mes == self.current_month:
                return
            self.current_month = mes
            self._new_shift()
            self._refresh()

        def _on_day_change(self, _evt=None):
            if self._suppress_events:
                return
            self._update_day_label()
            if self.ignore_index is None:
                self._suggest_times()

        def _on_type_change(self, _evt=None):
            guardia = self.tipo_var.get() == "Guardia"
            state = "disabled" if guardia else "normal"
            self.ent_ini.config(state=state)
            self.ent_fin.config(state=state)

        def _on_select(self, _evt=None):
            if self._suppress_events:
                return
            sel = self.tree.selection()
            if not sel:
                return
            idx = int(sel[0])
            doc = self._doc()
            if idx >= len(doc["shifts"]):
                return
            self._load_into_form(idx, doc["shifts"][idx])

        # ---------- formulario ----------
        def _suggest_times(self):
            try:
                day = int(self.dia_var.get())
            except (TypeError, ValueError):
                return
            m = MES_NUM[self.current_month]
            wd = datetime.date(self.year, m, day).weekday()
            if wd == 5:
                ini, fin = "08:00", "12:00"
            elif wd in (1, 2):
                ini, fin = "08:00", "16:00"
            else:
                ini, fin = "08:00", "17:00"
            self.ent_ini.delete(0, "end")
            self.ent_ini.insert(0, ini)
            self.ent_fin.delete(0, "end")
            self.ent_fin.insert(0, fin)

        def _load_into_form(self, idx, s):
            self.ignore_index = idx
            self.selected_shift = s
            self.lbl_modo.config(text="Editando turno del %s" % s.get("date", ""))
            self.dia_var.set(str(s.get("dayNumber")))
            self.tienda_var.set("%s — %s" % (STORE_NAMES.get(s.get("store"), "?"), s.get("store")))
            self.tipo_var.set("Guardia" if s.get("type") == "guardia" else "Jornada normal")
            self.ent_ini.config(state="normal")
            self.ent_fin.config(state="normal")
            self.ent_ini.delete(0, "end")
            self.ent_ini.insert(0, s.get("start", ""))
            self.ent_fin.delete(0, "end")
            self.ent_fin.insert(0, s.get("end", ""))
            self._on_type_change()
            self._update_day_label()

        def _new_shift(self):
            self.ignore_index = None
            self.selected_shift = None
            self.lbl_modo.config(text="Nuevo turno")
            if self.tree.selection():
                self._suppress_events = True
                self.tree.selection_remove(*self.tree.selection())
                self._suppress_events = False
            # tienda habitual del técnico en ese mes
            stores = [s.get("store") for _, s in self._month_shifts()]
            store = stores[0] if stores else "tienda1"
            self.tienda_var.set("%s — %s" % (STORE_NAMES[store], store))
            self.tipo_var.set("Jornada normal")
            dias = calendar.monthrange(self.year, MES_NUM[self.current_month])[1]
            try:
                day = int(self.dia_var.get())
            except (TypeError, ValueError):
                day = 1
            if not 1 <= day <= dias:
                day = 1
            self.dia_var.set(str(day))
            self.ent_ini.config(state="normal")
            self.ent_fin.config(state="normal")
            self.ent_ini.delete(0, "end")
            self.ent_fin.delete(0, "end")
            self._suggest_times()
            self._on_type_change()
            self._update_day_label()

        def _form_values(self):
            """Devuelve (store, tipo, start, end) o lanza ValueError con mensaje."""
            txt = self.tienda_var.get()
            store = txt.split("—")[-1].strip() if "—" in txt else txt.strip()
            if store not in STORE_NAMES:
                raise ValueError("Selecciona una tienda.")
            typ = "guardia" if self.tipo_var.get() == "Guardia" else "normal"
            if typ == "guardia":
                return store, typ, None, None
            return store, typ, self.ent_ini.get().strip(), self.ent_fin.get().strip()

        def _apply(self):
            if not self.current_pid:
                return
            try:
                day = int(self.dia_var.get())
                store, typ, start, end = self._form_values()
            except (TypeError, ValueError) as exc:
                messagebox.showerror("Datos incompletos", str(exc), parent=self)
                return

            m = MES_NUM[self.current_month]
            cand = build_shift(store, self.year, m, day, typ, start, end)
            doc = self._doc()
            errs, repl, guardia_day = analyze(doc, cand, self.ignore_index)

            if errs:
                messagebox.showerror("No se puede guardar", "\n".join(errs), parent=self)
                return
            if guardia_day:
                messagebox.showerror(
                    "Ese día tiene guardia",
                    "Ese día ya tiene una guardia. Una guardia reemplaza la jornada "
                    "normal, no puede haber ambas.\n\nEdita o elimina la guardia primero.",
                    parent=self)
                return
            if repl:
                if not messagebox.askyesno(
                        "La guardia reemplaza la jornada",
                        "Ese día tiene %d jornada(s) normal(es).\n\n"
                        "¿Quieres quitarla(s)? La guardia reemplaza el turno normal." % len(repl),
                        parent=self):
                    return
                for i in sorted(repl, reverse=True):
                    del doc["shifts"][i]
                if self.ignore_index is not None:
                    shift_amt = sum(1 for i in repl if i < self.ignore_index)
                    self.ignore_index -= shift_amt

            if self.ignore_index is not None and self.ignore_index < len(doc["shifts"]):
                doc["shifts"][self.ignore_index] = cand
                target = doc["shifts"][self.ignore_index]
            else:
                doc["shifts"].append(cand)
                target = cand

            self._mark_dirty(self.current_pid)
            self._refresh()
            # volver a seleccionar el turno aplicado
            for iid in self.tree.get_children():
                if int(iid) < len(doc["shifts"]) and doc["shifts"][int(iid)] is target:
                    self._suppress_events = True
                    self.tree.selection_set(iid)
                    self.tree.see(iid)
                    self._suppress_events = False
                    self._load_into_form(int(iid), target)
                    break
            self.lbl_estado.config(text="Turno aplicado · recuerda guardar")
            self._update_dirty_label()

        def _delete(self):
            if self.ignore_index is None or not self.current_pid:
                messagebox.showinfo("Eliminar", "Selecciona un turno de la tabla.", parent=self)
                return
            doc = self._doc()
            if self.ignore_index >= len(doc["shifts"]):
                return
            s = doc["shifts"][self.ignore_index]
            if not messagebox.askyesno(
                    "Eliminar turno",
                    "¿Eliminar el turno del %s en %s?" %
                    (s.get("date"), STORE_NAMES.get(s.get("store"), s.get("store"))),
                    parent=self):
                return
            del doc["shifts"][self.ignore_index]
            self._mark_dirty(self.current_pid)
            self._new_shift()
            self._refresh()

        def _duplicate_day(self):
            if not self.current_pid:
                return
            rows = self.tree.selection()
            if not rows:
                messagebox.showinfo("Duplicar día",
                                    "Selecciona un turno del día que quieres copiar.",
                                    parent=self)
                return
            doc = self._doc()
            src = doc["shifts"][int(rows[0])]
            m = MES_NUM[self.current_month]
            dias = calendar.monthrange(self.year, m)[1]
            target_day = simpledialog.askinteger(
                "Duplicar día",
                "Copia TODOS los turnos del %s al día:\n(1–%d)" % (src["date"], dias),
                parent=self, minvalue=1, maxvalue=dias)
            if not target_day:
                return
            copies = [dict(s) for s in doc["shifts"] if s.get("date") == src["date"]]
            added = 0
            for c in copies:
                cand = build_shift(c["store"], self.year, m, target_day, c["type"],
                                   c.get("start"), c.get("end"))
                errs, repl, guardia_day = analyze(doc, cand)
                if errs or guardia_day:
                    continue
                for i in sorted(repl, reverse=True):
                    del doc["shifts"][i]
                doc["shifts"].append(cand)
                added += 1
            if added:
                self._mark_dirty(self.current_pid)
                self._refresh()
                self.lbl_estado.config(text="Duplicados %d turno(s)" % added)
            else:
                messagebox.showwarning("Duplicar día",
                                       "No se pudo copiar: ya existen turnos iguales "
                                       "o hay conflicto de guardia.", parent=self)

        # ---------- guardar / recargar ----------
        def _mark_dirty(self, pid):
            self.dirty.add(pid)

        def _save(self):
            if not self.current_pid:
                return
            pid = self.current_pid
            if pid not in self.dirty:
                self.lbl_estado.config(text="No hay cambios que guardar")
                return
            try:
                path = save_doc(self._doc())
            except Exception as exc:
                messagebox.showerror("Error al guardar", str(exc), parent=self)
                return
            self.dirty.discard(pid)
            self.lbl_estado.config(text="✔ Guardado %s" % datetime.datetime.now().strftime("%H:%M:%S"))
            self._update_dirty_label()
            try:
                shown = str(path.relative_to(BASE)).replace("\\", "/")
            except ValueError:
                shown = str(path)
            self.lbl_archivo.config(text="Archivo: %s  ·  Año %d" % (shown, self.year))

        def _maybe_save(self):
            """Antes de cambiar de técnico/mes. True = continuar."""
            if not self.dirty:
                return True
            pid = self.current_pid
            name = next((p.get("name", pid) for p in self.personas if p["id"] == pid), pid)
            resp = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Hay cambios sin guardar de %s.\n\n¿Quieres guardarlos?" % name,
                parent=self)
            if resp is None:
                return False
            if resp:
                self._save()
                return True
            # descartar: recargar desde disco
            self.docs[pid] = load_doc(HOR, pid, name)
            self.dirty.discard(pid)
            self._update_dirty_label()
            return True

        def _reload(self):
            if not self.current_pid:
                return
            if not messagebox.askyesno(
                    "Recargar",
                    "Se descartarán los cambios sin guardar de este técnico.\n¿Continuar?",
                    parent=self):
                return
            pid = self.current_pid
            name = next((p.get("name", pid) for p in self.personas if p["id"] == pid), pid)
            self.docs[pid] = load_doc(HOR, pid, name)
            self.dirty.discard(pid)
            self._new_shift()
            self._refresh()
            self.lbl_estado.config(text="Recargado desde disco")

        def _on_close(self):
            if not self._maybe_save():
                return
            self.destroy()

    EditorApp().mainloop()


def ui_test():
    """Prueba de humo de la interfaz. Nunca escribe en los archivos reales."""
    import hashlib
    import tkinter as tk
    from tkinter import messagebox

    real = HOR / "andres-garzon.json"
    before = hashlib.md5(real.read_bytes()).hexdigest()

    tmp = Path(tempfile.mkdtemp(prefix="editor_uitest_"))
    hor_tmp = tmp / "horarios"
    hor_tmp.mkdir()
    resp_tmp = tmp / "respaldos"

    real_save = globals()["save_doc"]
    guardados = []

    def fake_save(doc, hor_dir=hor_tmp, backup_dir=resp_tmp):
        # redirige cualquier guardado a la carpeta temporal
        guardados.append(doc.get("id"))
        return real_save(doc, hor_dir, backup_dir)

    # evitar diálogos modales durante la prueba
    messagebox.askyesno = lambda *a, **k: True
    messagebox.showwarning = lambda *a, **k: None
    messagebox.showinfo = lambda *a, **k: None
    messagebox.showerror = lambda *a, **k: (_ for _ in ()).throw(AssertionError(a))

    captured = {}
    original_mainloop = tk.Tk.mainloop
    tk.Tk.mainloop = lambda self, *a, **k: captured.setdefault("app", self)
    globals()["save_doc"] = fake_save
    try:
        run_gui()
    finally:
        tk.Tk.mainloop = original_mainloop

    app = captured["app"]
    try:
        app.withdraw()
        app.update()

        pid = "andres-garzon"
        idx = next(i for i, p in enumerate(app.personas) if p["id"] == pid)
        app.cb_persona.current(idx)
        app._on_persona_change()
        app.mes_var.set("Diciembre")
        app._on_month_change()
        app.update()
        base = len(app.tree.get_children())
        assert base > 0, "no se listaron turnos"

        # 1) alta de un turno (domingo 6 de diciembre, libre)
        app.dia_var.set("6")
        app.tienda_var.set("C.C Felicidad — tienda3")
        app.tipo_var.set("Jornada normal")
        app.ent_ini.delete(0, "end")
        app.ent_ini.insert(0, "08:00")
        app.ent_fin.delete(0, "end")
        app.ent_fin.insert(0, "17:00")
        app._apply()
        app.update()
        assert len(app.tree.get_children()) == base + 1, "no se agregó el turno"
        assert pid in app.dirty, "no se marcó como modificado"

        # 2) edición del turno recién creado
        app.ent_fin.delete(0, "end")
        app.ent_fin.insert(0, "16:00")
        app._apply()
        app.update()
        assert len(app.tree.get_children()) == base + 1, "la edición duplicó el turno"
        s = app.docs[pid]["shifts"][app.ignore_index]
        assert s["end"] == "16:00", s

        # 3) convertirlo en guardia
        app.tipo_var.set("Guardia")
        app._on_type_change()
        app._apply()
        app.update()
        s = app.docs[pid]["shifts"][app.ignore_index]
        assert s["type"] == "guardia" and "start" not in s, s

        # 4) una jornada normal el mismo día debe bloquearse
        app.tipo_var.set("Jornada normal")
        app._on_type_change()
        app.dia_var.set("6")
        app.ignore_index = None
        try:
            app._apply()
        except AssertionError:
            pass
        else:
            raise AssertionError("debía bloquear jornada en un día con guardia")

        # 5) guardar (redirigido a la carpeta temporal)
        app._save()
        app.update()
        assert guardados == [pid], guardados
        archivo = hor_tmp / ("%s.json" % pid)
        assert archivo.exists(), "no se escribió el archivo temporal"
        doc = json.loads(archivo.read_text(encoding="utf-8"))
        guardia = [x for x in doc["shifts"] if x["date"] == "2026-12-06"]
        assert len(guardia) == 1 and guardia[0]["type"] == "guardia", guardia
        assert pid not in app.dirty, "quedó marcado como modificado tras guardar"

        # 6) eliminar el turno
        n_before = len(app.docs[pid]["shifts"])
        first = app.tree.get_children()[0]
        app.tree.selection_set(first)
        app._on_select()
        app._delete()
        app.update()
        assert len(app.docs[pid]["shifts"]) == n_before - 1, "no se eliminó"

        after = hashlib.md5(real.read_bytes()).hexdigest()
        assert before == after, "¡se modificó el archivo real!"
        print("UITEST OK: alta, edición, guardia, conflicto, guardado y borrado")
        print("           (archivo real intacto: %s)" % real.name)
    finally:
        globals()["save_doc"] = real_save
        app.destroy()
        shutil.rmtree(tmp, ignore_errors=True)


# ─────────────────────────────────────────────────────────────
#  Autoprueba (no abre ventana ni toca los archivos reales)
# ─────────────────────────────────────────────────────────────
def run_selftest():
    print("Autoprueba del editor…")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "HORARIOS").mkdir()
        shutil.copytree(HOR, tmp / "HORARIOS" / "horarios")
        shutil.copy2(PERSONAS_JSON, tmp / "HORARIOS" / "personas.json")

        personas = load_personas(tmp)
        docs = {p["id"]: load_doc(tmp / "HORARIOS" / "horarios", p["id"], p["name"])
                for p in personas}
        print("  personas cargadas:", len(personas))
        assert len(personas) >= 1

        doc = docs["brayan-sanchez"]
        before = len(doc["shifts"])
        year = current_year(docs)
        assert year == 2026, year

        # 1) turno válido en un domingo (brayan no trabaja domingos)
        cand = build_shift("tienda2", year, 12, 6, "normal", "08:00", "12:00")
        errs, repl, gd = analyze(doc, cand)
        assert not errs and not repl and not gd, (errs, repl, gd)
        assert cand["weekday"] == "Domingo" and cand["week"] == "Semana 1", cand

        doc["shifts"].append(cand)
        path = save_doc(doc, tmp / "HORARIOS" / "horarios", tmp / ".respaldos")
        reloaded = load_doc(tmp / "HORARIOS" / "horarios", "brayan-sanchez", "Brayan Sanchez")
        assert len(reloaded["shifts"]) == before + 1
        saved = [s for s in reloaded["shifts"] if s["date"] == "2026-12-06"][0]
        assert list(saved.keys()) == ["store", "storeName", "month", "year", "date",
                                      "dayNumber", "weekday", "week", "start", "end", "type"], saved.keys()

        # 2) duplicado detectado
        errs, _, _ = analyze(reloaded, cand)
        assert errs, "debía detectar el duplicado"

        # 3) guardia el mismo día detecta jornada a reemplazar
        g = build_shift("tienda2", year, 12, 6, "guardia")
        errs, repl, gd = analyze(reloaded, g)
        assert not errs and len(repl) == 1 and not gd, (errs, repl, gd)
        assert repl[0] == [i for i, s in enumerate(reloaded["shifts"])
                           if s["date"] == "2026-12-06"][0]

        # 4) jornada normal en día con guardia -> error de conflicto
        reloaded["shifts"].append(g)
        errs, _, gd = analyze(reloaded, cand)
        assert gd, "debía detectar guardia ese día"

        # 5) respaldo creado al sobrescribir
        save_doc(reloaded, tmp / "HORARIOS" / "horarios", tmp / ".respaldos")
        backups = list((tmp / ".respaldos").glob("brayan-sanchez_*.json"))
        assert backups, "no se creó respaldo"

        # 6) validaciones de horas
        bad = build_shift("tienda2", year, 12, 7, "normal", "17:00", "08:00")
        errs, _, _ = analyze(docs["kevin-alean"], bad)
        assert errs, "debía rechazar inicio >= fin"
        bad2 = build_shift("tienda2", year, 12, 7, "normal", "8:00", "17:00")
        errs, _, _ = analyze(docs["kevin-alean"], bad2)
        assert errs, "debía rechazar formato de hora inválido"

        print("  ✓ alta de turno, esquema y orden de claves")
        print("  ✓ detección de duplicados y conflictos guardia/jornada")
        print("  ✓ respaldo automático y validación de horas")
        print("Autoprueba OK (archivos reales intactos)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        run_selftest()
    elif "--uitest" in sys.argv:
        ui_test()
    else:
        run_gui()
