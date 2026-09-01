# 📖 Guía de uso — Gestor de Horarios por Tienda

> Guía práctica: qué es la página, qué hace cada parte, para qué sirve y cómo usarla.

---

## 1. ¿Qué es y para qué sirve?

Es una página web que muestra los **horarios del personal técnico en las tiendas**. Sirve para:

- Ver de un vistazo **quién trabaja en cada tienda**, **en qué día/semana** y **con qué jornada**.
- **Coordinar cobertura**: saber si una tienda tiene personal todos los días y quién tiene la **guardia** en cada tienda (ver todas las guardias juntas).
- Consultar el **dato de contacto** de cada técnico: al **pasar el cursor** sobre un turno se muestra su **foto**, correo, teléfono y tienda.

Todo se muestra en un **calendario mensual**, similar al de Google Calendar, pero por filas de semana.

---

## 2. Cómo abrir la página

1. El proyecto está desplegado en **Vercel** (enlazado al repo GitHub). Se accede por la URL de Vercel.
2. También puedes abrirla **localmente**:
   - Desde una carpeta compartida servida por HTTP (ideal).
   - Con un servidor local, por ejemplo: `python -m http.server 8000` y abrir `http://localhost:8000`.
   > ⚠️ Abrir `index.html` con doble clic puede fallar al cargar los datos por restricciones del navegador (CORS). Usa la versión de Vercel o un servidor local.

---

## 3. Pantalla paso a paso

### Paso 0 — El botón de guardias 🛡️ (está siempre arriba)

Debajo del título hay un botón naranja: **"🛡️ Ver todas las guardias"**. Lo explicamos en la sección 5; sirve para ver **todas las guardias de todas las tiendas a la vez**.

### Paso 1 — Elegir el país 🌍
Desplegable **"Seleccionar País"**. Al elegir un país, se activa el menú de tiendas con solo las tiendas de ese país.
- Países disponibles: Colombia, México, Argentina, Chile, Perú, Ecuador y Panamá. *(Hoy todas las tiendas definidas están en Colombia; "Bima" también es de Colombia.)*

### Paso 2 — Elegir la tienda 🏪
Desplegable **"Seleccionar Tienda"**. Al elegir una tienda:

1. Aparece el **banner azul** con:
   - Nombre y dirección de la tienda.
   - País (con bandera).
   - **nº de empleados asignados** (personas únicas con horarios en esa tienda).
2. Aparece la sección **"Calendario Mensual"** con el calendario del personal.

> Si quieres volver a empezar: elige "Elige una tienda" o cambia de país y todo se reinicia.

---

## 4. El calendario mensual 📅

Es una **tabla** donde:
- La **primera columna** indica la **semana** (Semana 1…5).
- Las **columnas** son los **días** (Lunes…Domingo).
- Cada **celda** muestra el **número del día** (esquina superior derecha) y los **turnos** de los técnicos ese día.
- Arriba aparece el **título** con el mes y año actuales (p. ej. "Septiembre 2026").

### Un turno (tarjetita dentro de la celda)
Cada turno muestra:
- 📸 La **foto** del técnico (o sus **iniciales** si no tiene foto).
- 👤 El **nombre**.
- 🕐 La **hora** (p. ej. `08:00 – 16:00`).
- 🛡️ La etiqueta **"Guardia"** cuando es un turno de guardia (sin horario).

### Pasar el cursor sobre un turno 🔎
Aparece un **recuadro flotante** (tooltip) con:
- **Foto** grande del técnico (o iniciales).
- **Nombre**.
- **Correo** y **teléfono**.
- La **tienda** (solo aparece en el calendario de guardias, para saber de qué tienda es cada guardia).

### Colores de los turnos (importante) 🎨

| Color | Qué significa |
|---|---|
| 🔵 **Azul** | **Jornada completa** (9 horas o más) — día cubierto todo el turno laboral. |
| 🟢 **Verde** | **Jornada parcial** (menos de 9 horas) — cobertura parcial. |
| 🟠 **Naranja** | **Guardia** — turno especial de guardia. |

---

## 5. El botón "Ver todas las guardias" 🛡️ (modo guardias)

Este botón está **siempre visible** justo debajo del título. Al pulsarlo:

1. **Se ocultan** los filtros de **país y tienda** (y el calendario de la tienda).
2. **Aparece el calendario de guardias**: un calendario mensual con **todas las guardias de todas las tiendas**.
   - Cada turno naranja indica **la tienda** (línea inferior) y **quién está asignado** (nombre con su foto).
   - Al pasar el cursor sobre una guardia se ve la **foto, nombre, correo y teléfono** del técnico y la **tienda**.
3. El panel de guardias tiene su **propio selector de mes** (para ver las guardias de otro mes sin salir del modo).

Para **volver a las tiendas**: pulsa de nuevo el botón, que ahora dice **"✖ Cerrar guardias"**. Se restauran los filtros de país/tienda (y el calendario de la tienda que tenías abierta).

> 🎯 Uso típico: ver quién está de guardia hoy, en qué tienda, y contactarlo con un solo hover.

---

## 6. Filtro de Mes 🗓️

Arriba del calendario de la tienda hay un desplegable **📅 Mes** (aparece al elegir tienda):

- Contiene los **12 meses del año**.
- Al entrar a una tienda se preselecciona el **mes actual** (hoy es Septiembre). Puedes cambiarlo para ver otro mes.

**Importante:**
- Cada vez que cambias el mes, **la información anterior se limpia** y se renderiza el calendario del mes elegido.
- Si eliges un mes **sin horarios**, verás el aviso *"No hay horarios para esta tienda."*
- No hay filtro de año: los horarios usan el año actual (o el indicado en los datos).

> Hoy solo hay datos de **Septiembre**; los demás meses saldrán vacíos hasta que se carguen horarios para ellos.

---

## 7. La numeración de días 🔢

Cada celda tiene un **número** (1…31) en la parte superior derecha, calculado con el calendario real del mes/año.
- Los números en **gris claro** corresponden a días que **no pertenecen al mes** (restos de la semana anterior o posterior en la rejilla).

Ejemplo: si el día 1 cae en martes, la celda del lunes de la primera semana muestra el **31 del mes anterior en gris** y el mes empieza a numerarse desde el martes.

---

## 8. Cómo agregar o modificar horarios ✏️

**No hay panel de administración**: los datos se editan directamente en los archivos JSON (o con un script que los genere). Pasos básicos:

### Añadir una persona (`personas.json`)
Añade un objeto nuevo a la lista con: `id` (único), `name`, `email`, `phone`, `photo`.
```json
{
  "id": "juan-perez",
  "name": "Juan Perez",
  "email": "juan.perez@rsg.com.co",
  "phone": "300 0000000",
  "photo": "tecnicos/web/juan.webp"
}
```

### Añadir un horario (`horarios.json`)
Dentro del objeto de la tienda (p. ej. `"tienda1"`), añade un registro:
```json
{
  "personaId": "juan-perez",
  "month": "Septiembre",
  "week": "Semana 2",
  "day": "Lunes",
  "start": "08:00",
  "end": "17:00",
  "type": "normal"
}
```
- `personaId` **debe** coincidir con un `id` de `personas.json`.
- `type` es `"normal"` o `"guardia"` (en guardia la app muestra la etiqueta "Guardia", no la hora).
- Para otro mes cambia `month` (p. ej. `"Octubre"`); opcionalmente añade `"year": "2026"`.
- Si una tienda no existe, crea su clave (p. ej. `"tienda10"`) y añade la tienda al objeto `stores` en `funciones.js` con su `country` y `address`.

> Al editar, guarda el archivo con **codificación UTF-8** (para que se vean bien acentos como "Miércoles", "Sábado").

---

## 9. Preguntas frecuentes (FAQ)

**¿Por qué no cargan los datos al abrir el archivo directamente?**
Por la política CORS del navegador con el protocolo `file://`. Usa Vercel o un servidor local.

**¿El mes siempre va a estar en Septiembre?**
No. Se preselecciona el **mes actual del sistema**. Cuando haya datos de otros meses, verás que salen al cambiar el filtro.

**¿Por qué veo números en gris como "31" o "1"?**
Son días de otro mes que encajan en la rejilla del calendario real (posición de la semana).

**¿Dónde está la información del técnico? ¿Hay algún panel lateral?**
No hay panel lateral. Al **pasar el cursor** sobre cualquier turno (del calendario de la tienda o del de guardias) aparece su **foto, nombre, correo, teléfono y tienda**.

**¿Qué significa el botón "Ver todas las guardias"?**
Abre el **modo guardias**: se ocultan los filtros de tienda y se muestra un calendario con todas las guardias de todas las tiendas (mes elegible). El botón pasa a "Cerrar guardias" para volver.

**¿Cómo sé qué tienda tiene una guardia en el modo guardias?**
Cada turno naranja muestra el **nombre de la tienda** en la línea de la hora (y en el tooltip al pasar el cursor).

**Las guardias muestran "Guardia" en vez de la hora: ¿es un error?**
Es intencional: las guardias no tienen una jornada fija de horas, se marcan como turno de guardia 24/7.

**¿Cuántos empleados y tiendas hay?**
7 empleados únicos; 9 tiendas con horarios cargados (incl. Bima en Colombia), ≈205 registros (9 guardias), todos de Septiembre.

---

## 10. Resumen rápido

1. Países → Tienda (o pulsa directamente **"🛡️ Ver todas las guardias"**).
2. Banner muestra datos de la tienda y nº de empleados.
3. Calendario mensual: semanas a la izquierda, días arriba, números + turnos por celda.
4. Filtro: **Mes** (12 meses), preselecciona el mes actual; se limpia y recarga al cambiar.
5. Azul = completa, Verde = parcial, Naranja = guardia.
6. **Pasa el cursor sobre un turno** para ver foto + datos del técnico (y la tienda en el modo guardias).
7. Para ver todas las guardias de todas las tiendas: botón **"Ver todas las guardias"** → calendario con tienda + técnico asignado → "Cerrar guardias" para volver.