# Herramientas internas

Esta carpeta **no hace parte de la aplicación web** y no se publica.
Son utilidades de escritorio para el administrador.

## Editor de horarios

`editor_horarios.py` es una ventana (Python + Tkinter) para **agregar, editar,
eliminar y duplicar turnos** sin tocar los JSON a mano, y también para **agregar
y eliminar técnicos**. Escribe directamente en `HORARIOS/horarios/<id>.json` y
en `HORARIOS/personas.json`, que es lo que lee la web.

### Cómo abrirlo

- Doble clic en **`INICIAR_EDITOR.bat`**, o
- desde una terminal:

```bat
python -X utf8 herramientas\editor_horarios.py
```

Requiere Python 3.9 o superior con Tkinter (viene incluido en la instalación
normal de Windows). No necesita internet ni instalar paquetes.

### Uso rápido

1. Elige el **técnico** y el **mes**.
2. Selecciona un turno de la tabla para editarlo, o pulsa **Nuevo turno**.
3. Ajusta día, tienda, tipo y horas. Pulsa **Aplicar**.
   - En **Tienda** puedes escribir para buscar: `felicidad`, `plaza`,
     `unicentro`, `tienda3`, etc. La lista se filtra sola.
4. Pulsa **Guardar (Ctrl+S)** para escribir el JSON. El cambio se ve en la web
   al recargar la página.

### Agregar y eliminar técnicos

Los botones **＋ Técnico** y **🗑 Técnico** están junto al desplegable de
técnico, arriba a la izquierda.

- **Agregar:** pide nombre, ID, correo, teléfono y foto.
  - El **ID** se genera solo desde el nombre (`Juan Pérez` → `juan-perez`) y se
    usa para el archivo `horarios/<id>.json`. Puedes cambiarlo mientras escribes.
  - El correo es opcional, pero si lo escribes debe tener formato válido.
  - La foto es opcional: al elegirla se copia a `HORARIOS/tecnicos/web/<id>.<ext>`.
  - Al guardar, el técnico se añade a `personas.json`, se crea su archivo de
    horarios vacío y queda seleccionado para empezar a cargarle turnos.
- **Eliminar:** pide confirmación e indica cuántos turnos tiene.
  - Se quita de `personas.json` y su `horarios/<id>.json` se mueve a
    `herramientas/.respaldos/<id>_eliminado_AAAAMMDD-HHMMSS.json`.
  - No permite borrar al último técnico.
  - Si el técnico tiene cambios sin guardar, lo advierte antes de continuar.

Después de agregar o eliminar, recarga la web para ver el cambio.

### Reglas que valida

- La fecha, el día de la semana y el número de semana se calculan solos
  (no se escriben a mano).
- No permite dos turnos iguales (misma fecha, tienda y tipo).
- **Una guardia reemplaza la jornada normal de ese día**: si agregas una
  guardia, te ofrece quitar la jornada; si intentas poner una jornada en un día
  con guardia, lo bloquea.
- Las horas deben ser `HH:MM` y la de inicio menor que la de fin.
- Advierte si hay cambios sin guardar antes de cambiar de técnico o cerrar.

### Respaldos

Antes de sobrescribir un JSON, el editor guarda una copia en
`herramientas/.respaldos/<id>_AAAAMMDD-HHMMSS.json`. Conserva los 40 más
recientes de cada técnico. `personas.json` se respalda como
`personas_AAAAMMDD-HHMMSS.json` y, al eliminar un técnico, su archivo queda como
`<id>_eliminado_AAAAMMDD-HHMMSS.json`.

Para restaurar uno: copia el respaldo elegido sobre
`HORARIOS/horarios/<id>.json` y recarga la web.

### Pruebas automáticas

No abren la interfaz ni tocan los archivos reales:

```bat
python -X utf8 herramientas\editor_horarios.py --selftest
python -X utf8 herramientas\editor_horarios.py --uitest
```

`--selftest` prueba la lógica de datos (esquema, duplicados, conflictos,
respaldos, horas, alta/baja de técnicos y copia de foto). `--uitest` abre la
ventana de forma invisible y simula alta, edición, guardia, guardado, borrado y
alta/baja de técnicos.

### Notas

- La carpeta está excluida del despliegue (`.vercelignore`) y los respaldos
  están en `.gitignore`.
- Si el editor muestra un error al guardar, normalmente es porque el archivo
  está abierto o bloqueado por otra aplicación.
