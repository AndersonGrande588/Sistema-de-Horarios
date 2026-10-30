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
import unicodedata
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

# Nombres cortos para las tarjetas del calendario
SHORT_STORES = {
    "tienda1": "Colina",
    "tienda2": "Calle 82",
    "tienda3": "Felicidad",
    "tienda4": "Plaza",
    "tienda5": "Unicentro",
    "tienda6": "Oficina",
    "tienda7": "Titán",
    "tienda8": "Fontanar",
    "tienda9": "Bima",
}

HORA_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def sin_acentos(texto):
    """Minúsculas y sin tildes, para buscar sin pelear con los acentos."""
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


STORE_KEYS = list(STORE_NAMES)


def store_label(key):
    """Etiqueta que se muestra en el desplegable: 'C.C Felicidad — tienda3'."""
    return "%s — %s" % (STORE_NAMES[key], key)


ALL_STORE_LABELS = [store_label(k) for k in STORE_KEYS]


def resolve_store(texto):
    """Convierte lo escrito por el usuario en una clave de tienda.

    Acepta 'tienda3', 'C.C Felicidad', 'C.C Felicidad — tienda3' o una
    búsqueda parcial única como 'felicidad'. Devuelve None si no hay
    coincidencia o si hay varias.
    """
    t = (texto or "").strip()
    if not t:
        return None
    if t in STORE_NAMES:
        return t
    if "—" in t:
        cola = t.split("—")[-1].strip()
        if cola in STORE_NAMES:
            return cola
    n = sin_acentos(t)
    for key in STORE_KEYS:
        if n == sin_acentos(key) or n == sin_acentos(STORE_NAMES[key]):
            return key
    matches = [k for k in STORE_KEYS
               if n in sin_acentos(k) or n in sin_acentos(store_label(k))]
    return matches[0] if len(matches) == 1 else None


def filter_store_labels(texto):
    """Lista de etiquetas que coinciden con lo escrito (para el buscador)."""
    n = sin_acentos(texto)
    if not n:
        return list(ALL_STORE_LABELS)
    return [lbl for lbl in ALL_STORE_LABELS if n in sin_acentos(lbl)]



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
#  Técnicos: alta y baja en personas.json
# ─────────────────────────────────────────────────────────────
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def slugify(texto):
    """'Juan Pérez' -> 'juan-perez' (ID seguro para el nombre del archivo)."""
    base = re.sub(r"[^a-z0-9]+", "-", sin_acentos(texto)).strip("-")
    return base or "tecnico"


def validate_persona(data, personas):
    """Errores de un técnico nuevo (lista vacía si todo está bien)."""
    errors = []
    name = (data.get("name") or "").strip()
    pid = (data.get("id") or "").strip()
    email = (data.get("email") or "").strip()

    if not name:
        errors.append("El nombre es obligatorio.")
    if not pid:
        errors.append("El ID es obligatorio.")
    elif not ID_RE.match(pid):
        errors.append("El ID solo admite minúsculas, números y guiones "
                      "(ej. juan-perez).")
    elif any((p.get("id") or "") == pid for p in personas):
        errors.append("Ya existe un técnico con el ID «%s»." % pid)
    if email and not EMAIL_RE.match(email):
        errors.append("El correo no tiene un formato válido "
                      "(ej. nombre@empresa.com).")
    return errors


def prepare_photo(texto, pid, horarios_dir):
    """Devuelve la ruta relativa de la foto y la copia a tecnicos/web si hace falta."""
    t = (texto or "").strip()
    if not t:
        return ""
    p = Path(t)
    if not p.is_absolute():
        if (Path(horarios_dir) / p).exists():
            return p.as_posix()
        raise ValueError("No se encontró la foto: %s" % t)
    if not p.exists():
        raise ValueError("No se encontró la foto: %s" % t)

    destino_dir = Path(horarios_dir) / "tecnicos" / "web"
    destino_dir.mkdir(parents=True, exist_ok=True)
    ext = p.suffix.lower() or ".webp"
    destino = destino_dir / (pid + ext)
    try:
        if p.resolve() != destino.resolve():
            shutil.copy2(p, destino)
    except OSError as exc:
        raise ValueError("No se pudo copiar la foto: %s" % exc)
    return "tecnicos/web/%s%s" % (pid, ext)


def save_personas(personas, personas_path, backup_dir):
    """Escribe personas.json con respaldo previo y su mismo formato."""
    personas_path = Path(personas_path)
    backup_dir = Path(backup_dir)
    personas_path.parent.mkdir(parents=True, exist_ok=True)

    if personas_path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(personas_path, backup_dir / ("personas_%s.json" % stamp))

    tmp = personas_path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(personas, f, ensure_ascii=False, indent=2)
    os.replace(tmp, personas_path)

    for old in sorted(backup_dir.glob("personas_*.json"))[:-40]:
        try:
            old.unlink()
        except OSError:
            pass
    return personas_path


def create_persona(personas, personas_path, hor_dir, backup_dir, data):
    """Agrega el técnico a personas.json y le crea su JSON de horarios vacío."""
    errors = validate_persona(data, personas)
    if errors:
        raise ValueError("\n".join(errors))

    persona = {
        "id": (data.get("id") or "").strip(),
        "name": (data.get("name") or "").strip(),
        "email": (data.get("email") or "").strip(),
        "phone": (data.get("phone") or "").strip(),
        "photo": (data.get("photo") or "").strip(),
    }

    hor_dir = Path(hor_dir)
    doc_path = hor_dir / (persona["id"] + ".json")
    if doc_path.exists():
        try:
            viejo = json.loads(doc_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            viejo = {}
        if viejo.get("shifts"):
            raise ValueError("Ya existe horarios/%s.json con turnos. "
                             "Usa otro ID." % persona["id"])

    personas.append(persona)
    creado = False
    if not doc_path.exists():
        hor_dir.mkdir(parents=True, exist_ok=True)
        with open(doc_path, "w", encoding="utf-8") as f:
            json.dump({"id": persona["id"], "name": persona["name"], "shifts": []},
                      f, ensure_ascii=False, indent=2)
        creado = True

    try:
        save_personas(personas, personas_path, backup_dir)
    except Exception:
        personas.remove(persona)
        if creado:
            try:
                doc_path.unlink()
            except OSError:
                pass
        raise
    return persona


def delete_persona(personas, personas_path, hor_dir, backup_dir, pid):
    """Quita el técnico de personas.json y archiva/borra su JSON de horarios."""
    persona = next((p for p in personas if p.get("id") == pid), None)
    if not persona:
        raise ValueError("No se encontró el técnico «%s»." % pid)

    personas.remove(persona)
    save_personas(personas, personas_path, backup_dir)

    doc_path = Path(hor_dir) / ("%s.json" % pid)
    if doc_path.exists():
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(doc_path, backup_dir / ("%s_eliminado_%s.json" % (pid, stamp)))
        doc_path.unlink()
    return persona


# ─────────────────────────────────────────────────────────────
#  Interfaz (Tkinter)
# ─────────────────────────────────────────────────────────────
def run_gui(test=False):
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog, filedialog

    class EditorApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Editor de Horarios — herramienta local")
            pantalla_w = self.winfo_screenwidth()
            pantalla_h = self.winfo_screenheight()
            ancho = min(1180, max(980, pantalla_w - 60))
            alto = min(760, max(620, pantalla_h - 100))
            x = max(0, (pantalla_w - ancho) // 2)
            y = max(0, (pantalla_h - alto) // 2 - 10)
            self.geometry("%dx%d+%d+%d" % (ancho, alto, x, y))
            self.minsize(980, 600)
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
            style.configure("TFrame", background="#f3f4f6")
            style.configure("CalHead.TLabel", background="#f3f4f6",
                            foreground="#6b7280", font=("Segoe UI", 9, "bold"))
            style.configure("Toolbutton", font=("Segoe UI", 9), padding=(10, 5))

            self._build_ui()
            self._load_docs()
            self.year = current_year(self.docs)
            self._fill_personas()

            self.protocol("WM_DELETE_WINDOW", self._on_close)
            self.bind("<Control-s>", lambda e: self._save())
            self.bind("<Control-n>", lambda e: self._new_shift())

        # ---------- construcción de la interfaz ----------
        def _build_ui(self):
            top = ttk.Frame(self, padding=(14, 12, 14, 6))
            top.pack(fill="x")

            ttk.Label(top, text="👤 Técnico").pack(side="left")
            self.persona_var = tk.StringVar()
            self.cb_persona = ttk.Combobox(top, textvariable=self.persona_var,
                                           state="readonly", width=30)
            self.cb_persona.pack(side="left", padx=(8, 6))
            self.cb_persona.bind("<<ComboboxSelected>>", self._on_persona_change)
            self.btn_add_persona = ttk.Button(top, text="＋ Técnico",
                                              command=self._add_persona)
            self.btn_add_persona.pack(side="left")
            self.btn_del_persona = ttk.Button(top, text="🗑 Técnico",
                                              command=self._delete_persona)
            self.btn_del_persona.pack(side="left", padx=(4, 18))

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

            # --- turnos del mes: calendario o tabla ---
            box = ttk.LabelFrame(main, text="Turnos del mes", padding=8)
            box.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
            box.rowconfigure(1, weight=1)
            box.columnconfigure(0, weight=1)

            vista = ttk.Frame(box)
            vista.grid(row=0, column=0, sticky="ew", pady=(0, 6))
            self.vista_var = tk.StringVar(value="calendario")
            ttk.Radiobutton(vista, text="🗓 Calendario", value="calendario",
                            variable=self.vista_var, style="Toolbutton",
                            command=lambda: self._set_view("calendario")).pack(side="left")
            ttk.Radiobutton(vista, text="☰ Tabla", value="tabla",
                            variable=self.vista_var, style="Toolbutton",
                            command=lambda: self._set_view("tabla")).pack(
                side="left", padx=(4, 0))

            leyenda = tk.Frame(vista, bg="#f3f4f6")
            leyenda.pack(side="right")
            for texto, fondo, color in ((" Jornada ", "#dbeafe", "#1e3a8a"),
                                        (" Guardia ", "#ffe3c2", "#9a3412")):
                tk.Label(leyenda, text=texto, bg=fondo, fg=color,
                         font=("Segoe UI", 8, "bold"), padx=4,
                         pady=1).pack(side="left", padx=(4, 0))

            cont = ttk.Frame(box)
            cont.grid(row=1, column=0, sticky="nsew")
            cont.rowconfigure(0, weight=1)
            cont.columnconfigure(0, weight=1)

            # --- vista de tabla ---
            self.view_table = ttk.Frame(cont)
            self.view_table.grid(row=0, column=0, sticky="nsew")
            self.view_table.rowconfigure(0, weight=1)
            self.view_table.columnconfigure(0, weight=1)

            cols = ("fecha", "dia", "semana", "tienda", "tipo", "horario")
            self.tree = ttk.Treeview(self.view_table, columns=cols, show="headings",
                                     selectmode="browse")
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
            self.tree.bind("<Double-1>", self._on_select)
            self.tree.bind("<Return>", self._on_select)
            self.tree.bind("<Delete>", lambda e: self._delete())

            sb = ttk.Scrollbar(self.view_table, orient="vertical", command=self.tree.yview)
            sb.grid(row=0, column=1, sticky="ns")
            self.tree.configure(yscrollcommand=sb.set)

            # --- vista de calendario (mes en curso del técnico) ---
            self.view_calendar = ttk.Frame(cont)
            self.view_calendar.grid(row=0, column=0, sticky="nsew")
            for c in range(7):
                self.view_calendar.columnconfigure(c, weight=1, uniform="dias")
            for c, nombre in enumerate(("Lun", "Mar", "Mié", "Jue", "Vie",
                                        "Sáb", "Dom")):
                ttk.Label(self.view_calendar, text=nombre, anchor="center",
                          style="CalHead.TLabel").grid(
                    row=0, column=c, sticky="ew", padx=1, pady=(0, 2))

            self.cal_cells = []
            for r in range(6):
                for c in range(7):
                    frame = tk.Frame(self.view_calendar, bd=0, highlightthickness=1,
                                     highlightbackground="#e5e7eb", bg="#ffffff")
                    frame.grid(row=r + 1, column=c, sticky="nsew", padx=1, pady=1)
                    head = tk.Frame(frame, bg="#ffffff")
                    head.pack(fill="x", padx=4, pady=(2, 0))
                    lbl_dia = tk.Label(head, text="", anchor="w", bg="#ffffff",
                                       fg="#374151", font=("Segoe UI", 9, "bold"))
                    lbl_dia.pack(side="left")
                    lbl_tag = tk.Label(head, text="", anchor="e", bg="#ffffff",
                                       fg="#9a3412", font=("Segoe UI", 7, "bold"))
                    lbl_tag.pack(side="right")
                    body = tk.Frame(frame, bg="#ffffff")
                    body.pack(fill="both", expand=True, padx=3, pady=(1, 3))
                    self.cal_cells.append({"frame": frame, "head": head,
                                           "day": lbl_dia, "tag": lbl_tag,
                                           "body": body})

            self.lbl_count = ttk.Label(box, text="", style="Hint.TLabel")
            self.lbl_count.grid(row=2, column=0, sticky="w", pady=(6, 0))
            self.lbl_hint = ttk.Label(box, text="", style="Hint.TLabel")
            self.lbl_hint.grid(row=2, column=0, sticky="e", pady=(6, 0))

            self._set_view("calendario")

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

            ttk.Label(form, text="Tienda (escribe para buscar)").grid(row=4, column=0, sticky="w")
            self.tienda_var = tk.StringVar()
            self.cb_tienda = ttk.Combobox(form, textvariable=self.tienda_var,
                                          width=28, values=ALL_STORE_LABELS)
            self.cb_tienda.grid(row=5, column=0, sticky="ew", pady=(2, 8))
            self.cb_tienda.bind("<KeyRelease>", self._filter_stores)
            self.cb_tienda.bind("<<ComboboxSelected>>", self._on_store_selected)

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
            self.ent_ini.bind("<Return>", lambda e: self._apply())
            self.ent_fin.bind("<Return>", lambda e: self._apply())

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
            self._refresh_persona_choices()
            if not self.personas:
                return

            hoy = datetime.date.today()
            default = MESES[hoy.month - 1] if hoy.year == self.year else "Septiembre"
            self.current_month = default
            self.mes_var.set(default)
            self._new_shift()
            self._refresh()

        def _refresh_persona_choices(self, select_pid=None):
            """Repinta el desplegable de técnicos y elige uno."""
            labels = ["%s — %s" % (p.get("name", p["id"]), p["id"])
                      for p in self.personas]
            self.cb_persona["values"] = labels
            if not self.personas:
                self.current_pid = None
                self.persona_var.set("")
                self.lbl_estado.config(text="No hay técnicos en personas.json")
                return
            objetivo = select_pid or self.current_pid
            idx = next((i for i, p in enumerate(self.personas)
                        if p["id"] == objetivo), 0)
            self.current_pid = self.personas[idx]["id"]
            self.cb_persona.current(idx)

        # ---------- alta y baja de técnicos ----------
        def _persona_dialog(self):
            """Formulario modal de alta. Devuelve los datos o None si se cancela."""
            import tkinter as tk

            dlg = tk.Toplevel(self)
            dlg.title("Agregar técnico")
            dlg.transient(self)
            dlg.resizable(False, False)
            dlg.configure(bg="#f3f4f6")
            result = {"data": None}

            body = ttk.Frame(dlg, padding=14)
            body.pack(fill="both", expand=True)
            body.columnconfigure(1, weight=1)

            nombre_var = tk.StringVar()
            pid_var = tk.StringVar()
            email_var = tk.StringVar()
            tel_var = tk.StringVar()
            foto_var = tk.StringVar()
            auto = {"on": True}

            def on_name(*_args):
                if auto["on"]:
                    pid_var.set(slugify(nombre_var.get()))

            def on_pid(*_args):
                auto["on"] = False

            def browse():
                elegida = filedialog.askopenfilename(
                    parent=dlg, title="Elegir foto",
                    filetypes=[("Imágenes", "*.webp *.png *.jpg *.jpeg *.gif"),
                               ("Todos los archivos", "*.*")])
                if elegida:
                    foto_var.set(elegida)

            def cancel():
                dlg.destroy()

            def ok():
                data = {
                    "id": pid_var.get().strip(),
                    "name": nombre_var.get().strip(),
                    "email": email_var.get().strip(),
                    "phone": tel_var.get().strip(),
                    "photo": foto_var.get().strip(),
                }
                errs = validate_persona(data, self.personas)
                if errs:
                    messagebox.showerror("Datos del técnico", "\n".join(errs),
                                         parent=dlg)
                    return
                result["data"] = data
                dlg.destroy()

            ttk.Label(body, text="Nombre completo").grid(row=0, column=0,
                                                        sticky="w", pady=4)
            ent_nombre = ttk.Entry(body, textvariable=nombre_var, width=34)
            ent_nombre.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

            ttk.Label(body, text="ID (archivo)").grid(row=1, column=0,
                                                      sticky="w", pady=4)
            ent_pid = ttk.Entry(body, textvariable=pid_var, width=34)
            ent_pid.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

            ttk.Label(body, text="Correo").grid(row=2, column=0, sticky="w", pady=4)
            ent_email = ttk.Entry(body, textvariable=email_var, width=34)
            ent_email.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=4)

            ttk.Label(body, text="Teléfono").grid(row=3, column=0, sticky="w", pady=4)
            ent_tel = ttk.Entry(body, textvariable=tel_var, width=34)
            ent_tel.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=4)

            ttk.Label(body, text="Foto").grid(row=4, column=0, sticky="w", pady=4)
            fila_foto = ttk.Frame(body)
            fila_foto.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=4)
            fila_foto.columnconfigure(0, weight=1)
            ent_foto = ttk.Entry(fila_foto, textvariable=foto_var, width=24)
            ent_foto.grid(row=0, column=0, sticky="ew")
            ttk.Button(fila_foto, text="Buscar…", command=browse).grid(
                row=0, column=1, padx=(6, 0))

            ttk.Label(body, text="El ID se usa para horarios/<id>.json y se genera "
                                 "solo a partir del nombre.",
                      style="Hint.TLabel", wraplength=380).grid(
                row=5, column=0, columnspan=2, sticky="w", pady=(4, 10))

            botones = ttk.Frame(body)
            botones.grid(row=6, column=0, columnspan=2, sticky="e")
            ttk.Button(botones, text="Cancelar", command=cancel).pack(side="left")
            ttk.Button(botones, text="＋ Agregar", style="Accent.TButton",
                       command=ok).pack(side="left", padx=(6, 0))

            ent_nombre.bind("<KeyRelease>", on_name)
            ent_pid.bind("<KeyRelease>", on_pid)
            for w in (ent_nombre, ent_pid, ent_email, ent_tel, ent_foto):
                w.bind("<Return>", lambda e: ok())
            dlg.bind("<Escape>", lambda e: cancel())

            dlg.update_idletasks()
            x = self.winfo_rootx() + max(0, (self.winfo_width() - dlg.winfo_width()) // 2)
            y = self.winfo_rooty() + max(0, (self.winfo_height() - dlg.winfo_height()) // 3)
            dlg.geometry("+%d+%d" % (x, y))
            dlg.grab_set()
            ent_nombre.focus_set()
            self.wait_window(dlg)
            return result["data"]

        def _add_persona(self):
            data = self._persona_dialog()
            if not data:
                return

            errs = validate_persona(data, self.personas)
            if errs:
                messagebox.showerror("Agregar técnico", "\n".join(errs), parent=self)
                return
            try:
                data["photo"] = prepare_photo(data.get("photo"), data["id"], HORARIOS)
            except ValueError as exc:
                messagebox.showerror("Foto del técnico", str(exc), parent=self)
                return
            try:
                persona = create_persona(self.personas, PERSONAS_JSON, HOR,
                                         RESPALDOS, data)
            except ValueError as exc:
                messagebox.showerror("Agregar técnico", str(exc), parent=self)
                return
            except Exception as exc:
                messagebox.showerror("Agregar técnico",
                                     "No se pudo guardar: %s" % exc, parent=self)
                return

            pid = persona["id"]
            self.docs[pid] = load_doc(HOR, pid, persona["name"])
            self.dirty.discard(pid)
            self._refresh_persona_choices(pid)
            self._new_shift()
            self._refresh()
            self.lbl_estado.config(text="✔ Técnico agregado: %s" % persona["name"])

        def _delete_persona(self):
            if not self.current_pid:
                return
            if len(self.personas) <= 1:
                messagebox.showwarning("Eliminar técnico",
                                       "Debe quedar al menos un técnico.",
                                       parent=self)
                return

            pid = self.current_pid
            persona = next((p for p in self.personas if p["id"] == pid), None)
            if persona is None:
                return
            n = len(self.docs.get(pid, {}).get("shifts", []))
            aviso = "\n\n⚠ Tiene cambios sin guardar que se perderán." \
                if pid in self.dirty else ""
            if not messagebox.askyesno(
                    "Eliminar técnico",
                    "¿Eliminar a %s (%s)?\n\nSe quitará de personas.json y su "
                    "archivo horarios/%s.json (%d turnos) se moverá a la carpeta "
                    "de respaldos.%s"
                    % (persona.get("name", pid), pid, pid, n, aviso),
                    parent=self):
                return
            try:
                delete_persona(self.personas, PERSONAS_JSON, HOR, RESPALDOS, pid)
            except Exception as exc:
                messagebox.showerror("Eliminar técnico", str(exc), parent=self)
                return

            self.docs.pop(pid, None)
            self.dirty.discard(pid)
            self.current_pid = None
            self._refresh_persona_choices()
            self._new_shift()
            self._refresh()
            self.lbl_estado.config(text="✔ Técnico eliminado: %s"
                                         % persona.get("name", pid))

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
                self._render_calendar()
            finally:
                self._suppress_events = False

        # ---------- calendario ----------
        def _set_view(self, modo):
            """Muestra el calendario o la tabla sin perder el estado."""
            self.view_mode = modo
            if hasattr(self, "vista_var"):
                self.vista_var.set(modo)
            if modo == "calendario":
                self.view_table.grid_remove()
                self.view_calendar.grid()
                self.lbl_hint.config(
                    text="Clic en un día para cargarlo · clic en una tarjeta para editarla")
                self._render_calendar()
            else:
                self.view_calendar.grid_remove()
                self.view_table.grid()
                self.lbl_hint.config(
                    text="Doble clic o Enter sobre una fila para editarla")

        def _calendar_entries(self):
            """{día: [(índice, turno)]} de los turnos del mes mostrado."""
            out = {}
            for idx, s in enumerate(self._doc().get("shifts", [])):
                if s.get("month") != self.current_month:
                    continue
                try:
                    dia = int(s.get("dayNumber"))
                except (TypeError, ValueError):
                    continue
                out.setdefault(dia, []).append((idx, s))
            for filas in out.values():
                filas.sort(key=lambda t: (t[1].get("type", ""),
                                          t[1].get("store", "")))
            return out

        @staticmethod
        def _short_store(s):
            store = s.get("store")
            if store in SHORT_STORES:
                return SHORT_STORES[store]
            nombre = s.get("storeName") or store or ""
            for prefijo in ("C.C ", "Centro Comercial ", "Oficina "):
                if nombre.startswith(prefijo):
                    nombre = nombre[len(prefijo):]
                    break
            return nombre

        @staticmethod
        def _short_time(hora):
            """'08:00' -> '08'; si hay minutos distintos de 00, deja HH:MM."""
            hora = hora or ""
            return hora[:2] if hora.endswith(":00") else hora

        def _render_calendar(self):
            if not getattr(self, "cal_cells", None) or not self.current_month:
                return
            m = MES_NUM[self.current_month]
            dias = calendar.monthrange(self.year, m)[1]
            primer = datetime.date(self.year, m, 1).weekday()   # lunes = 0
            filas = (primer + dias + 6) // 7
            entradas = self._calendar_entries()
            hoy = datetime.date.today()
            try:
                dia_sel = int(self.dia_var.get())
            except (TypeError, ValueError):
                dia_sel = None

            for r in range(6):
                self.view_calendar.rowconfigure(
                    r + 1, weight=1 if r < filas else 0)

            for pos, cell in enumerate(self.cal_cells):
                frame = cell["frame"]
                if pos // 7 >= filas:
                    frame.grid_remove()
                    continue
                frame.grid()

                dia = pos - primer + 1
                for w in cell["body"].winfo_children():
                    w.destroy()

                if not 1 <= dia <= dias:
                    frame.config(bg="#f9fafb", highlightthickness=1,
                                 highlightbackground="#eef0f2")
                    cell["head"].config(bg="#f9fafb")
                    cell["day"].config(text="", bg="#f9fafb")
                    cell["tag"].config(text="", bg="#f9fafb")
                    self._bind_cal_cell(cell, None)
                    continue

                es_hoy = (self.year == hoy.year and m == hoy.month
                          and dia == hoy.day)
                es_sel = (dia_sel == dia)
                borde = "#0f766e" if es_sel else "#2563eb" if es_hoy else "#e5e7eb"
                frame.config(bg="#ffffff", highlightbackground=borde,
                             highlightthickness=2 if (es_sel or es_hoy) else 1)
                cell["head"].config(bg="#ffffff")
                cell["day"].config(
                    text=str(dia), bg="#ffffff",
                    fg="#0f766e" if es_sel else "#2563eb" if es_hoy else "#374151")

                filas_dia = entradas.get(dia, [])
                guardias = sum(1 for _, s in filas_dia
                               if s.get("type") == "guardia")
                cell["tag"].config(text=("🛡 %d" % guardias) if guardias else "",
                                   bg="#ffffff")
                self._bind_cal_cell(cell, dia)

                for idx, s in (filas_dia if len(filas_dia) <= 2
                               else filas_dia[:1]):
                    if s.get("type") == "guardia":
                        texto = "🛡 " + self._short_store(s)
                        fondo, color = "#ffe3c2", "#9a3412"
                    else:
                        texto = "%s %s–%s" % (
                            self._short_store(s),
                            self._short_time(s.get("start", "")),
                            self._short_time(s.get("end", "")))
                        fondo, color = "#dbeafe", "#1e3a8a"
                    chip = tk.Label(cell["body"], text=texto, anchor="w",
                                    bg=fondo, fg=color, padx=3,
                                    font=("Segoe UI", 7))
                    chip.pack(fill="x", pady=(0, 1))
                    chip.bind("<Button-1>",
                              lambda e, i=idx: self._calendar_open(i))

                if len(filas_dia) > 2:
                    visibles = 1
                    extra = len(filas_dia) - visibles
                    mas = tk.Label(cell["body"], text="+%d más" % extra,
                                   anchor="w", bg="#ffffff", fg="#6b7280",
                                   padx=3, font=("Segoe UI", 7, "italic"))
                    mas.pack(fill="x")
                    mas.bind("<Button-1>",
                             lambda e, i=filas_dia[visibles][0]:
                             self._calendar_open(i))

        def _bind_cal_cell(self, cell, dia):
            def pick(_evt=None):
                self._calendar_pick(dia)

            for w in (cell["frame"], cell["head"], cell["day"],
                      cell["tag"], cell["body"]):
                w.bind("<Button-1>", pick)

        def _calendar_pick(self, dia):
            """Clic en una celda: elige el día (y edita si tiene un solo turno)."""
            if not dia or not self.current_month:
                return
            filas_dia = self._calendar_entries().get(dia, [])
            if len(filas_dia) == 1:
                self._calendar_open(filas_dia[0][0])
                return

            self.dia_var.set(str(dia))
            self.ignore_index = None
            self.selected_shift = None
            self.lbl_modo.config(text="Nuevo turno")
            self._suggest_times()
            self._update_day_label()
            self._render_calendar()

        def _calendar_open(self, idx):
            doc = self._doc()
            if not 0 <= idx < len(doc.get("shifts", [])):
                return
            if self.tree.exists(str(idx)):
                self._suppress_events = True
                try:
                    self.tree.selection_set(str(idx))
                    self.tree.see(str(idx))
                finally:
                    self._suppress_events = False
            self._load_into_form(idx, doc["shifts"][idx])

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
            self._render_calendar()

        def _on_type_change(self, _evt=None):
            guardia = self.tipo_var.get() == "Guardia"
            state = "disabled" if guardia else "normal"
            self.ent_ini.config(state=state)
            self.ent_fin.config(state=state)

        def _filter_stores(self, event=None):
            """Filtra la lista de tiendas mientras se escribe."""
            if event is not None and event.keysym in (
                    "Up", "Down", "Return", "Escape", "Tab", "Home", "End",
                    "Left", "Right", "Prior", "Next"):
                return
            self.cb_tienda["values"] = filter_store_labels(self.tienda_var.get())

        def _on_store_selected(self, _evt=None):
            store = resolve_store(self.tienda_var.get())
            if store:
                self.tienda_var.set(store_label(store))
            self.cb_tienda["values"] = ALL_STORE_LABELS

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
            self.tienda_var.set(store_label(s.get("store")) if s.get("store") in STORE_NAMES else "")
            self.tipo_var.set("Guardia" if s.get("type") == "guardia" else "Jornada normal")
            self.ent_ini.config(state="normal")
            self.ent_fin.config(state="normal")
            self.ent_ini.delete(0, "end")
            self.ent_ini.insert(0, s.get("start", ""))
            self.ent_fin.delete(0, "end")
            self.ent_fin.insert(0, s.get("end", ""))
            self._on_type_change()
            self._update_day_label()
            self._render_calendar()

        def _new_shift(self):
            self.ignore_index = None
            self.selected_shift = None
            self.lbl_modo.config(text="Nuevo turno")
            if self.tree.selection():
                self._suppress_events = True
                self.tree.selection_remove(*self.tree.selection())
                self._suppress_events = False
            # tienda habitual del técnico en ese mes (la que más usa)
            conteo = {}
            for _, s in self._month_shifts():
                conteo[s.get("store")] = conteo.get(s.get("store"), 0) + 1
            store = max(conteo, key=conteo.get) if conteo else "tienda1"
            if store not in STORE_NAMES:
                store = "tienda1"
            self.tienda_var.set(store_label(store))
            self.cb_tienda["values"] = ALL_STORE_LABELS
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
            self._render_calendar()

        def _form_values(self):
            """Devuelve (store, tipo, start, end) o lanza ValueError con mensaje."""
            store = resolve_store(self.tienda_var.get())
            if not store:
                raise ValueError("Selecciona una tienda válida.\n\n"
                                 "Puedes escribir para buscar: por ejemplo "
                                 "\"Felicidad\" o \"tienda3\".")
            self.tienda_var.set(store_label(store))
            typ = "guardia" if self.tipo_var.get() == "Guardia" else "normal"
            if typ == "guardia":
                return store, typ, None, None
            return store, typ, self.ent_ini.get().strip(), self.ent_fin.get().strip()

        def _apply(self):
            if not self.current_pid:
                return
            m = MES_NUM[self.current_month]
            dias = calendar.monthrange(self.year, m)[1]
            try:
                day = int(self.dia_var.get())
            except (TypeError, ValueError):
                messagebox.showerror("Día inválido",
                                     "Escribe un día del mes (1–%d)." % dias, parent=self)
                return
            if not 1 <= day <= dias:
                messagebox.showerror("Día inválido",
                                     "%s de %d solo tiene %d días." %
                                     (self.current_month, self.year, dias), parent=self)
                return
            try:
                store, typ, start, end = self._form_values()
            except ValueError as exc:
                messagebox.showerror("Datos incompletos", str(exc), parent=self)
                return

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
    before_personas = hashlib.md5(PERSONAS_JSON.read_bytes()).hexdigest()

    tmp = Path(tempfile.mkdtemp(prefix="editor_uitest_"))
    hor_tmp = tmp / "horarios"
    shutil.copytree(HOR, hor_tmp)
    resp_tmp = tmp / "respaldos"
    personas_tmp = tmp / "personas.json"
    shutil.copy2(PERSONAS_JSON, personas_tmp)

    originales = {k: globals()[k] for k in
                  ("PERSONAS_JSON", "HOR", "RESPALDOS", "HORARIOS")}
    globals()["PERSONAS_JSON"] = personas_tmp
    globals()["HOR"] = hor_tmp
    globals()["RESPALDOS"] = resp_tmp
    globals()["HORARIOS"] = tmp / "webroot"

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

        # el desplegable de tiendas debe venir lleno
        assert len(app.cb_tienda["values"]) == len(STORE_NAMES), app.cb_tienda["values"]
        # los botones de alta/baja de técnicos deben existir
        assert app.btn_add_persona.winfo_exists() and app.btn_del_persona.winfo_exists()

        pid = "andres-garzon"
        idx = next(i for i, p in enumerate(app.personas) if p["id"] == pid)
        app.cb_persona.current(idx)
        app.cb_persona.event_generate("<<ComboboxSelected>>")
        app.update()
        app.cb_mes.set("Diciembre")
        app.cb_mes.event_generate("<<ComboboxSelected>>")
        app.update()
        assert app.current_pid == pid and app.current_month == "Diciembre"
        base = len(app.tree.get_children())
        assert base > 0, "no se listaron turnos"

        # 1) alta de un turno buscando la tienda por texto ("feli")
        app.dia_var.set("6")
        app.cb_dia.event_generate("<<ComboboxSelected>>")
        app.tienda_var.set("feli")
        app._filter_stores()
        assert list(app.cb_tienda["values"]) == ["C.C Felicidad — tienda3"], app.cb_tienda["values"]
        app.tipo_var.set("Jornada normal")
        app._on_type_change()
        app.ent_ini.delete(0, "end")
        app.ent_ini.insert(0, "08:00")
        app.ent_fin.delete(0, "end")
        app.ent_fin.insert(0, "17:00")
        app._apply()
        app.update()
        assert len(app.tree.get_children()) == base + 1, "no se agregó el turno"
        assert pid in app.dirty, "no se marcó como modificado"
        assert app.docs[pid]["shifts"][app.ignore_index]["store"] == "tienda3"

        # 2) edición del turno recién creado
        app.ent_fin.delete(0, "end")
        app.ent_fin.insert(0, "16:00")
        app._apply()
        app.update()
        assert len(app.tree.get_children()) == base + 1, "la edición duplicó el turno"
        s = app.docs[pid]["shifts"][app.ignore_index]
        assert s["end"] == "16:00", s

        # 2b) cambiar la tienda del mismo turno buscando "plaza"
        app.tienda_var.set("plaza")
        app._filter_stores()
        assert list(app.cb_tienda["values"]) == ["C.C Plaza Central — tienda4"], app.cb_tienda["values"]
        app._apply()
        app.update()
        s = app.docs[pid]["shifts"][app.ignore_index]
        assert s["store"] == "tienda4" and s["storeName"] == "C.C Plaza Central", s
        assert len(app.tree.get_children()) == base + 1, "cambiar tienda duplicó el turno"

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

        # 4b) una tienda inexistente debe rechazarse
        app.tienda_var.set("zzz")
        app.dia_var.set("8")
        try:
            app._apply()
        except AssertionError:
            pass
        else:
            raise AssertionError("debía rechazar una tienda inexistente")

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
        app.tree.event_generate("<<TreeviewSelect>>", when="now")
        app.update()
        assert app.ignore_index is not None, "el clic no cargó el turno en el formulario"
        app._delete()
        app.update()
        assert len(app.docs[pid]["shifts"]) == n_before - 1, "no se eliminó"

        # 6b) vista de calendario: celdas, cambio de vista y clic en un día
        assert len(app.cal_cells) == 42
        assert app.view_calendar.winfo_manager() == "grid"
        app._set_view("tabla")
        assert app.view_calendar.winfo_manager() == "" \
            and app.view_table.winfo_manager() == "grid"
        app._set_view("calendario")
        assert app.view_calendar.winfo_manager() == "grid" \
            and app.view_table.winfo_manager() == ""
        # diciembre 2026 empieza martes y ocupa 5 filas: la 6.ª debe ocultarse
        primer = datetime.date(2026, 12, 1).weekday()
        assert app.cal_cells[35]["frame"].winfo_manager() == "", \
            "no se ocultó la sexta fila"
        doc_dic = app.docs[pid]
        por_dia = {}
        for i, s in enumerate(doc_dic["shifts"]):
            if s["month"] == "Diciembre":
                por_dia.setdefault(s["dayNumber"], []).append(i)
        dia = sorted(d for d, v in por_dia.items() if len(v) == 1)[0]
        app._calendar_pick(dia)
        app.update()
        assert app.dia_var.get() == str(dia)
        assert app.ignore_index == por_dia[dia][0], "el clic no abrió el turno"
        assert app.docs[pid]["shifts"][app.ignore_index]["dayNumber"] == dia
        celda = app.cal_cells[primer + dia - 1]
        assert celda["body"].winfo_children(), "la celda no dibujó el turno"

        # 7) alta de técnico con el diálogo simulado
        app._persona_dialog = lambda: {
            "id": "prueba-test", "name": "Prueba Test",
            "email": "prueba@rsg.com.co", "phone": "300 1112233", "photo": ""}
        app._add_persona()
        app.update()
        assert app.current_pid == "prueba-test", app.current_pid
        assert any(p["id"] == "prueba-test" for p in app.personas), "no se agregó"
        assert (hor_tmp / "prueba-test.json").exists(), "no se creó su JSON"
        guardadas = json.loads(personas_tmp.read_text(encoding="utf-8"))
        assert any(p["id"] == "prueba-test" for p in guardadas), "no se guardó personas.json"
        assert len(app.cb_persona["values"]) == len(guardadas)

        # 7b) un ID repetido debe rechazarse
        app._persona_dialog = lambda: {
            "id": pid, "name": "Repetido", "email": "", "phone": "", "photo": ""}
        try:
            app._add_persona()
        except AssertionError:
            pass
        else:
            raise AssertionError("debía rechazar un ID repetido")

        # 8) baja del técnico (se archiva su JSON)
        app._delete_persona()
        app.update()
        assert not any(p["id"] == "prueba-test" for p in app.personas), "no se quitó"
        assert not (hor_tmp / "prueba-test.json").exists(), "no se quitó su JSON"
        assert list(resp_tmp.glob("prueba-test_eliminado_*.json")), "sin respaldo"
        assert app.current_pid and app.current_pid != "prueba-test"
        guardadas = json.loads(personas_tmp.read_text(encoding="utf-8"))
        assert not any(p["id"] == "prueba-test" for p in guardadas)

        after = hashlib.md5(real.read_bytes()).hexdigest()
        assert before == after, "¡se modificó el archivo real!"
        assert hashlib.md5(
            originales["PERSONAS_JSON"].read_bytes()).hexdigest() == before_personas, \
            "¡se modificó personas.json real!"
        print("UITEST OK: tiendas, alta, edición, cambio de tienda, guardia,")
        print("           conflicto, guardado, borrado y alta/baja de técnicos")
        print("           (archivos reales intactos)")
    finally:
        globals()["save_doc"] = real_save
        globals().update(originales)
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

        # 7) búsqueda y resolución de tiendas
        assert resolve_store("tienda3") == "tienda3"
        assert resolve_store("C.C Felicidad — tienda3") == "tienda3"
        assert resolve_store("felicidad") == "tienda3"
        assert resolve_store("PLAZA central") == "tienda4"
        assert resolve_store("bima") == "tienda9"
        assert resolve_store("colina") is None, "colina es ambiguo (2 tiendas)"
        assert resolve_store("no existe") is None
        labels = filter_store_labels("unicentro")
        assert labels == ["C.C Unicentro — tienda5"], labels
        assert len(filter_store_labels("")) == len(STORE_NAMES)
        assert len(filter_store_labels("tienda")) == len(STORE_NAMES)

        # 8) alta y baja de técnicos (personas.json + su JSON de horarios)
        assert slugify("Juan Pérez Gómez") == "juan-perez-gomez"
        assert slugify("  ÁNGELA  ") == "angela"
        assert slugify("!!!") == "tecnico"
        assert not validate_persona(
            {"id": "juan-perez", "name": "Juan Pérez",
             "email": "juan@rsg.com.co"}, personas)
        assert validate_persona({"id": "", "name": ""}, personas)
        assert validate_persona({"id": "Juan Perez", "name": "Juan"}, personas)
        assert validate_persona({"id": "juan-perez", "name": "Juan",
                                 "email": "correo-sin-arroba"}, personas)
        assert validate_persona({"id": personas[0]["id"], "name": "Otro"}, personas)

        hor_dir = tmp / "HORARIOS" / "horarios"
        personas_path = tmp / "HORARIOS" / "personas.json"
        respaldos_dir = tmp / ".respaldos"

        nuevo = create_persona(
            personas, personas_path, hor_dir, respaldos_dir,
            {"id": "juan-perez", "name": "Juan Pérez",
             "email": "juan@rsg.com.co", "phone": "300 0000000", "photo": ""})
        assert nuevo["id"] == "juan-perez"
        assert (hor_dir / "juan-perez.json").exists(), "no se creó el JSON"
        doc_nuevo = json.loads((hor_dir / "juan-perez.json").read_text(encoding="utf-8"))
        assert list(doc_nuevo) == ["id", "name", "shifts"] and not doc_nuevo["shifts"]
        assert any(p["id"] == "juan-perez" for p in load_personas(tmp))
        assert list(respaldos_dir.glob("personas_*.json")), "sin respaldo de personas.json"

        # ID repetido y datos inválidos
        try:
            create_persona(personas, personas_path, hor_dir, respaldos_dir,
                           {"id": "juan-perez", "name": "Juan Pérez 2"})
        except ValueError:
            pass
        else:
            raise AssertionError("debía rechazar un ID repetido")

        # la foto se copia a tecnicos/web/<id>.<ext>
        foto = tmp / "foto.png"
        foto.write_bytes(b"PNG")
        rel = prepare_photo(str(foto), "juan-perez", tmp / "HORARIOS")
        assert rel == "tecnicos/web/juan-perez.png", rel
        assert (tmp / "HORARIOS" / rel).read_bytes() == b"PNG"
        try:
            prepare_photo(str(tmp / "no-existe.png"), "juan-perez", tmp / "HORARIOS")
        except ValueError:
            pass
        else:
            raise AssertionError("debía avisar que la foto no existe")

        # baja: se archiva el JSON con sus turnos
        doc_juan = load_doc(hor_dir, "juan-perez", "Juan Pérez")
        doc_juan["shifts"].append(
            build_shift("tienda2", year, 12, 8, "normal", "08:00", "12:00"))
        save_doc(doc_juan, hor_dir, respaldos_dir)
        delete_persona(personas, personas_path, hor_dir, respaldos_dir, "juan-perez")
        assert not (hor_dir / "juan-perez.json").exists(), "no se quitó el JSON"
        assert not any(p["id"] == "juan-perez" for p in load_personas(tmp))
        archivados = list(respaldos_dir.glob("juan-perez_eliminado_*.json"))
        assert archivados, "no se archivó el JSON del técnico eliminado"
        assert len(json.loads(archivados[0].read_text(encoding="utf-8"))["shifts"]) == 1
        try:
            delete_persona(personas, personas_path, hor_dir, respaldos_dir, "no-existe")
        except ValueError:
            pass
        else:
            raise AssertionError("debía fallar al borrar un técnico inexistente")

        print("  ✓ alta de turno, esquema y orden de claves")
        print("  ✓ detección de duplicados y conflictos guardia/jornada")
        print("  ✓ respaldo automático y validación de horas")
        print("  ✓ búsqueda de tiendas por nombre, clave o texto parcial")
        print("  ✓ alta y baja de técnicos con respaldo y copia de foto")
        print("Autoprueba OK (archivos reales intactos)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        run_selftest()
    elif "--uitest" in sys.argv:
        ui_test()
    else:
        run_gui()
