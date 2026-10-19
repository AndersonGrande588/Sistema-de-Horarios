# 📋 Gestor de Horarios por Tienda — Documentación técnica

> Documentación completa del proyecto: arquitectura, estructura de archivos, modelo de datos, funciones, estilos y despliegue.

---

## 1. Resumen del proyecto

Aplicación web **estática** que permite consultar los horarios de trabajo de un equipo técnico por tienda y país, organizados en un **calendario mensual** estilo rejilla (fila = semana, columna = día).

- **Tecnología:** HTML + CSS + JavaScript puro. Sin frameworks, sin dependencias, sin build tools.
- **Datos:** archivos JSON (`personas.json` + un `horarios/<id>.json` por técnico) cargados en el navegador con `fetch()`.
- **Propósito:** visualizar de un vistazo qué técnico trabaja en cada tienda, en qué días y con qué tipo de jornada (normal o guardia), y coordinar la cobertura de las tiendas mediante una **lista global de guardias** (todas las tiendas en un solo vistazo).

---

## 2. Arquitectura

```
Navegador (cliente)
   │
   ├─ index.html     → estructura de la interfaz
   ├─ styles.css     → estilos visuales
   ├─ funciones.js   → lógica de la aplicación
   │
   └─ Datos (fetch)
       ├─ personas.json        → catálogo de empleados
       └─ horarios/<id>.json   → un archivo por técnico con TODOS sus turnos
```

Todo el procesamiento ocurre en el navegador (**client-side rendering**). No hay servidor ni base de datos: los JSON son la fuente de verdad.

### Flujo general

1. `funciones.js` carga `personas.json` y, en paralelo (`Promise.all`), el archivo `horarios/<id>.json` de cada persona; luego agrupa los turnos por tienda.
2. El usuario elige un **país** → se habilitan las **tiendas** de ese país.
3. El usuario elige una **tienda** → se muestra el banner de la tienda + el **calendario mensual** del personal (filtrable solo por **mes**).
4. El botón **"🛡️ Ver todas las guardias"** abre un **modo global**: oculta los filtros de país/tienda y muestra una **lista agrupada por semanas** con todas las guardias del mes; cada guardia indica el **día con su número** (p. ej. "Domingo 6"), la **tienda** y **todos los datos del técnico** asignado (foto, nombre, correo y teléfono).
5. Al **pasar el cursor** sobre cualquier turno se muestra un tooltip con la **foto**, nombre, correo y teléfono del técnico.

---

## 3. Estructura de archivos

| Archivo | Descripción |
|---|---|
| `index.html` | Interfaz principal (selectores, banner, controles, calendario y panel de guardias). |
| `styles.css` | Todas las reglas de estilo (hoja única). |
| `funciones.js` | Lógica completa: carga de datos, selección país/tienda, filtro de mes, render del calendario, modo guardias y tooltips. |
| `personas.json` | Lista de empleados (id, nombre, email, teléfono, foto). |
| `horarios/<id>.json` | Un archivo por técnico con todos sus turnos (todas las tiendas y meses), cada uno con fecha y número de día reales. |
| `tecnicos/` | Fotografías de los empleados (WebP optimizadas en `tecnicos/web/`). |
| `backup_refactor/` | Respaldo de los archivos previos al refactor (no se usa en producción). |
| `GoogleSites_Calendario.html`, `Horarios.html`, `BORRADOR.html` | Versiones antiguas / borradores; **no forman parte de la app actual**. |

---

## 4. Modelo de datos

### 4.1 Países y tiendas — definidos en código (`funciones.js`)

No vienen de un JSON; están declarados como constantes en JavaScript.

```js
const countries = {
    colombia: { name: "Colombia", flag: "🇨🇴" },
    mexico:   { name: "México",   flag: "🇲🇽" },
    // ... (argentina, chile, peru, ecuador, panama)
};

const stores = {
    tienda1: { name: "C.C Colina",        address: "Centro Comercial Parque la colina", country: "colombia" },
    tienda2: { name: "Zona Calle 82",     address: "Zona Comercial Calle 82",            country: "colombia" },
    tienda3: { name: "C.C Felicidad",     address: "Centro Comercial La Felicidad",      country: "colombia" },
    tienda4: { name: "C.C Plaza Central", address: "Centro Comercial Plaza Central",     country: "colombia" },
    tienda5: { name: "C.C Unicentro",     address: "Centro Comercial Unicentro",         country: "colombia" },
    tienda6: { name: "Oficina Colina",    address: "Oficinas Corporativas Colina",       country: "colombia" },
    tienda7: { name: "C.C Titan",         address: "Centro Comercial Titan Plaza",       country: "colombia" },
    tienda8: { name: "C.C Fontanar",      address: "Centro Comercial Fontanar",          country: "colombia" },
    tienda9: { name: "Bima",              address: "Bodega Bima",                        country: "colombia", city: "chia" }
};
```

> **Bima** (`tienda9`) está en **Colombia (Chía)** y tiene horarios propios asignados a un único técnico (Andres Bojaca).

### 4.2 `personas.json` — empleados

Lista (array) de objetos:

```json
{
  "id": "kevin-alean",
  "name": "Kevin Alean",
  "email": "kevin.alean@rsg.com.co",
  "phone": "324 5210384",
  "photo": "tecnicos/unnamed (1).webp"
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | string | Identificador único (slug; p. ej. `kevin-alean`). Lo usan los horarios. |
| `name` | string | Nombre completo. |
| `email` | string | Correo corporativo. |
| `phone` | string | Teléfono de contacto. |
| `photo` | string | Ruta de la foto (WebP). Si falta, se muestra un avatar con iniciales. |

Actualmente hay **7 empleados únicos**.

### 4.3 `horarios/<id>.json` — un archivo por técnico

Cada empleado de `personas.json` tiene su propio archivo `horarios/<id>.json` (p. ej. `horarios/kevin-alean.json`). Contiene **todos** sus turnos, en todas las tiendas y meses. Se cargan con `Promise.allSettled`; si a una persona le falta el archivo, se ignora sin romper la app.

```json
{
  "id": "kevin-alean",
  "name": "Kevin Alean",
  "shifts": [
    {
      "store": "tienda1",
      "storeName": "C.C Colina",
      "month": "Septiembre",
      "year": 2026,
      "date": "2026-09-01",
      "dayNumber": 1,
      "weekday": "Martes",
      "week": "Semana 1",
      "start": "08:00",
      "end": "16:00",
      "type": "normal"
    }
  ]
}
```

| Campo (registro) | Tipo | Descripción |
|---|---|---|
| `store` | string | Clave de la tienda (`tienda1`…`tienda9`). |
| `storeName` | string | Nombre de la tienda (informativo). |
| `month` | string | Mes en español (p. ej. `"Septiembre"`, `"Octubre"`). |
| `year` | number | Año (2026). |
| `date` | string | **Fecha real ISO** (`YYYY-MM-DD`), coherente con el calendario. |
| `dayNumber` | number | **Número del día** del mes (1…31). Debe coincidir con la `date`. |
| `weekday` | string | Día de la semana (`"Lunes"`…`"Domingo"`). |
| `week` | string | Semana dentro del mes (`"Semana 1"`…`"Semana 5"`). |
| `start` / `end` | string | Hora inicio/fin en formato `HH:MM` (ausentes en guardias). |
| `type` | string | `"normal"` (jornada) o `"guardia"`. |

`funciones.js` reconstruye con esto el objeto `horarios` agrupado por tienda (usa `store` como clave y `weekday` como `day`; las guardias se marcan como `"Domingo (Guardia)"`).

Totales actuales (generados desde los datos originales): **9 tiendas**, **395 turnos** = **192 de Septiembre** + **203 de Octubre**. Técnicos: Kevin Alean, Angel Ortiz, Julian Garzon (tiendas 3 y 4), Jersoon Gonzalez, Anderson Grande, Andres Garzon y Andres Bojaca (tiendas 8 y 9).

> **Bima (`tienda9`):** turnos de **andres-bojaca**. Lunes, Jueves, Viernes y Sábado `08:00–17:00`; Martes y Miércoles `08:00–16:00`; Domingo **guardia** (Semanas 1–4).
>
> **Octubre:** se repite el patrón de septiembre (mismos días de la semana y misma paridad de semana por persona/tienda) pero con las **fechas reales** de octubre (el día 1 es **jueves**).

> **Guardias del mes (coinciden con la asignación real):**
> - Jersoon Gonzalez → tienda5 · **6 septiembre** (Semana 1 Domingo)
> - Angel Ortiz → tienda2 · **2 septiembre** (Semana 1 Miércoles)
> - Julian Garzon → tienda3 · **13 septiembre** (Semana 2 Domingo)
> - Kevin Alean → tienda1 · **20 septiembre** (Semana 3 Domingo)
> - Andres Bojaca (Bima) → tienda9 · **6, 13, 20 y 27 septiembre** (Semanas 1–4 Domingo)

> **Nota:** cada registro ya trae su **fecha real** (`date`) y su **número de día** (`dayNumber`). El calendario además **recalcula** el número de cada celda a partir de semana + día con el calendario real del mes/año (`new Date(año, mes, n)`), de modo que los días ≤ 0 o > último día del mes caen en el mes vecino y se marcan como `out-month`.

---

## 5. Lógica — `funciones.js`

El archivo está organizado en bloques numerados.

### BLOQUE 1 — Datos de la aplicación

- `countries`, `stores`: catálogos de países y tiendas (constantes).
- Estado global:
  - `personas` / `horarios`: datos cargados desde los JSON.
  - `currentStore`: tienda seleccionada.
  - `currentMonth`: mes del filtro (preseleccionado al **mes actual del sistema**).
  - `guardsMode`: indica si el panel de guardias está abierto.
- `loadData()`: carga `personas.json` y luego, con `Promise.all`, el `horarios/<id>.json` de cada persona (`allSettled`-style: ignora los que falten). Reconstruye el objeto `horarios` agrupado por tienda. Si algo falla, registra el error en consola y deja los datos vacíos.
- `MONTH_NAMES`: lista ordenada de los 12 meses en español (usada para el filtro y para numerar días). Se define en el BLOQUE 3.5.

### BLOQUE 2 — Selección de país / tienda

- `filterStoresByCountry()`: se ejecuta al cambiar el país. Limpia la selección actual y rellena el desplegable de tiendas con las del país elegido.
- `renderStore()`: se ejecuta al elegir tienda. Muestra el banner (nombre, dirección, país, nº de empleados únicos calculado con `Set`), prepara el filtro de mes (`populateDateFilters`) y dibuja el calendario (`renderCalendar`). Si se deselecciona, oculta todo.

### BLOQUE 3.5 — Filtro de mes

- `populateDateFilters()`: llena el selector de **mes** con los 12 meses y preselecciona el **mes actual del sistema** (`MONTH_NAMES[new Date().getMonth()]`).
- `selectMonth()`: al cambiar el mes, **limpia la información previa** (`staffList = ""`) y vuelve a renderizar el calendario.

> No existe filtro de año ni botones de señalización (Todas / Jornada normal / Guardia): fueron eliminados. El único filtro es el **mes**.

### BLOQUE 3.8 — Turnos estándar (optimización)

- `SHIFTS`: constantes de los turnos más repetidos (`08-17`, `08-16`, `09-18`, `09-17`) con su etiqueta.
- `turnoLabel(sch)`: devuelve la etiqueta horaria de un registro: `"Guardia"` si es tipo guardia, la etiqueta de `SHIFTS` si coincide, o el rango `HH:MM–HH:MM` directo.
- `diasSemana`: orden estándar (Lunes…Domingo).
- `normalizeDay(d)`: convierte `"Domingo (Guardia)"` en `"Domingo"`.
- `toMin(t)`: convierte `"HH:MM"` a minutos.
- `turnoColor(sch)`: guardia → naranja; duración ≥ 540 min → azul (jornada completa); si no → verde (jornada parcial).

### BLOQUE 4 — Calendario mensual

- `renderCalendar()`: función principal del render.
  1. Filtra los registros de la tienda por mes.
  2. Si no hay registros para el filtro, muestra una caja de "No hay horarios".
  3. Construye la rejilla: encabezado (Lunes…Domingo) + filas por semana.
  4. Calcula el **número de día real** de cada celda con `new Date(yearNum, monthIndex, dayNum)`:
     - `firstWeekday` → día de la semana del día 1 del mes (lunes = 0).
     - Los días fuera del mes (antes del 1 o después del último) se muestran en gris (`out-month`).
- Helpers internos:
  - `buildHeader()`: genera la fila de encabezado de días.
  - `buildWeekRow(semana, semanaIndex)`: una fila (semana) con sus 7 celdas.
  - `buildDayCell(...)`: celda del día con el número del día y los turnos.

### Render de un turno (evento)

Cada turno se dibuja como `.cal-event` con:
- 📸 **foto** del técnico (18px) o sus **iniciales** si no hay foto.
- 👤 **nombre** (una línea, corta con `…` si es largo).
- 🕐 **hora** (etiqueta de `SHIFTS`, rango `HH:MM–HH:MM` o **"Guardia"**).
- Cada evento lleva `data-tip-id` y `data-tip-store` para alimentar el tooltip.

### BLOQUE 5 — Helpers

- `initials(name)`: devuelve las iniciales de un nombre (usadas como avatar de respaldo).

### BLOQUE 6 — Lista de guardias de todos los técnicos

Modo global activado por el botón **"🛡️ Ver todas las guardias"**:

- `toggleAllGuards()`: alterna `guardsMode`. Al abrir:
  - Oculta los selectores de **país/tienda**, el banner de tienda, la sección de calendario y el estado vacío.
  - Llena su propio selector de **mes** (preselecciona el mes actual) y renderiza la lista de guardias.
  - Al cerrar: restaura los selectores y, si había una tienda seleccionada, re-renderiza con `renderStore()`.
- `guardsMonth()`: devuelve el mes elegido en el selector propio del panel de guardias.
- `selectGuardsMonth()`: al cambiar el mes del panel, limpia el contenido y re-renderiza.
- `renderAllGuards()`: recorre **todas las tiendas**, filtra los registros tipo `guardia` por el mes seleccionado, calcula el **número del día real** de cada guardia (semana + día con el calendario real del mes/año, igual que el calendario de tienda) y agrupa/ordena por **semana**. Dibuja una **lista** con un encabezado `📅 Semana N` y, debajo, una tarjeta (`.guard-card`) por guardia. Cada tarjeta muestra:
  - **Foto** del técnico (o iniciales) y su **nombre**, **correo** y **teléfono**.
  - Badge "📆 Día + número" (p. ej. "Domingo 6") y badge "🏪 Tienda" (en qué tienda tiene la guardia).
  - Si no hay guardias en el mes, muestra "No hay guardias en este mes.".
  - Las tarjetas llevan `data-tip-id`/`data-tip-store`, por lo que el tooltip de la BLOQUE 7 también funciona sobre ellas.
- Helper interno `card(g)`: genera la tarjeta de una guardia con los datos del técnico y los badges día/tienda.

### BLOQUE 7 — Tooltip con foto + info del técnico (hover)

- `getTechTip()`: crea/obtiene el div flotante `#techTooltip`.
- `positionTip(event)`: coloca el tooltip junto al cursor, evitando que se salga de la ventana.
- Listeners globales (delegación de eventos en `document`):
  - `mouseover`: si el objetivo está dentro de un `[data-tip-id]`, construye el tooltip con **foto** (o iniciales), nombre, correo, teléfono y tienda (cuando aplica) y lo muestra.
  - `mousemove`: reposiciona el tooltip mientras esté visible.
  - `mouseout`: oculta el tooltip al salir del elemento con `data-tip-id`.

---

## 6. Diseño y estilos — `styles.css`

CSS plano (sin preprocesador). Reglas principales:

| Selector | Uso |
|---|---|
| `:root`, `body`, `.container` | Reset básico, tipografía y fondo. |
| `.card`, `.selector-card` | Tarjetas de los selectores de país y tienda. |
| `select`, `input` | Estilo de los desplegables e inputs. |
| `.store-banner`, `.badge`, `.country-indicator` | Banner azul de la tienda con datos y contador. |
| `.filter-row`, `.filter-group` | Fila de filtros (el único filtro es el **mes**). |
| `.hidden` | Oculta elementos que aún no aplican. |
| `.guards-bar`, `.guards-btn` | Franja y botón global "🛡️ Ver todas las guardias" (naranja). |
| `.guards-panel`, `.guards-head` | Panel de la **lista de guardias** con su selector de mes. |
| `.cal-wrapper` | Contenedor del calendario (scroll horizontal si es necesario). |
| `.cal-month-title` | Título del mes/año mostrado. |
| `.cal-grid` | Rejilla del calendario (ancho mínimo 900px). |
| `.cal-row` | Fila rejilla: columna `100px` (semana) + 7 columnas `1fr` (días). |
| `.cal-header-row` | Encabezado fijo (sticky) de días. |
| `.cal-week-row .cal-week-label` | Etiqueta lateral de la semana. |
| `.cal-cell` | Celda de día: **altura fija 96px**, scroll interno fino. |
| `.cal-day-num` (y `.out-month`) | Número del día en círculo; gris si es de otro mes. |
| `.cal-cell.no-day` | Celda sin turnos. |
| `.cal-event` (+ variantes) | Turno: azul (jornada completa), verde (jornada parcial), naranja (guardia). |
| `.cal-cell-photo`, `.cal-cell-initials` | Foto o avatar de 18px en el turno. |
| `.cal-event-name`, `.cal-event-time` | Texto del turno. |
| `.guard-card`, `.guard-avatar`, `.guard-info`, `.guard-when`, `.guard-badge` | Tarjetas de la **lista de guardias** (datos del técnico + badges cuándo/tienda). |
| `.tech-tooltip`, `.tip-photo`, `.tip-name`, `.tip-meta` | Tooltip flotante con foto + info del técnico. |
| `@media (max-width: 600px)` | Ajustes responsive: columnas simples y banner apilado. |

### Paleta de colores de los turnos

| Tipo | Color | Significado |
|---|---|---|
| `.jornada-completa` | Azul (`#2563eb → #3b82f6`) | Jornada de 9 h o más. |
| `.jornada-parcial` | Verde (`#059669 → #10b981`) | Jornada de menos de 9 h. |
| `.guardia` | Naranja (`#f97316 → #ea580c`) | Turno de guardia. |

> La antigua sección CSS "VISTA SEMANAL TIPO GOOGLE CALENDAR" (que forzaba alturas/`overflow`) fue **eliminada**; por eso las celdas mantienen altura uniforme y no hay recortes. También se eliminaron los estilos del panel lateral de técnicos y de la barra de señalización.

---

## 7. Despliegue

- **Plataforma:** Vercel.
- **Repositorio:** `https://github.com/AndersonGrande588/Sistema-de-Horarios.git`
- **Requisito:** el sitio debe servirse vía HTTP(S) porque la app usa `fetch()` para los JSON. Abrir `index.html` con doble clic (protocolo `file://`) puede bloquear la carga por CORS; en Vercel funciona sin problema.

---

## 8. Limitaciones y notas técnicas

- **Sin backend:** los datos se editan directamente en los JSON (o se generan con scripts). No hay persistencia desde la UI.
- **Sin build:** no hay minificación ni bundling; los archivos se suben tal cual.
- **Fechas reales:** cada registro incluye `date` y `dayNumber`. La numeración de la rejilla se **recalcula** con semana + día usando el calendario real del mes/año; si los datos de semana/día no coincidieran con un calendario real, la numeración podría desplazarse (los generadores garantizan la coherencia).
- **Horas de guardia:** los registros tipo `guardia` pueden tener `start`/`end`, pero la UI siempre muestra la etiqueta **"Guardia"**.
- **Filtro único:** solo existe el filtro de **mes** (el de año y los botones de señalización fueron retirados).
- **Solo fotos en hover:** la información del técnico (foto + correo + teléfono) se muestra en un tooltip al pasar el cursor; no hay panel lateral permanente.
- **Tooltip propio:** se usa un tooltip HTML personalizado (no el `title` nativo) para poder mostrar imágenes.

---

## 9. Estado del proyecto (resumen de lo hecho)

- ✅ Base de datos en `personas.json` + un `horarios/<id>.json` por técnico (un archivo por persona con todos sus turnos, con fecha y número de día reales).
- ✅ Horarios de **Octubre** generados repitiendo el patrón de Septiembre con fechas reales.
- ✅ Calendario mensual en rejilla (semana × día) con numeración de días (soporta mes anterior/siguiente en gris).
- ✅ Etiqueta "Guardia" en los turnos de guardia (sin horario).
- ✅ Celdas con altura fija uniforme (96px) y scroll interno para días muy cargados (se removió el CSS obsoleto de la vista semanal).
- ✅ Filtro de **mes** (12 meses) que preselecciona el mes actual del sistema; limpieza de la información al cambiar.
- ✅ **Bima** agregada en Colombia (Chía), con horarios propios de Andres Bojaca (Lun/Sáb 08-17, Mar/Mié 08-16, Dom guardia).
- ✅ Constantes `SHIFTS` y helper `turnoLabel()` para optimizar etiquetas de turnos.
- ✅ Fotos de los técnicos en los turnos (18px) + **tooltip** al pasar el cursor con foto, nombre, correo, teléfono y tienda.
- ✅ **Modo guardias**: botón global que oculta los filtros de tienda y muestra una lista agrupada por semanas con todas las guardias del mes: día con su número, tienda y datos completos del técnico (foto, nombre, correo, teléfono).
- ✅ Eliminados: panel lateral de técnicos, barra de señalización (Todas/Normal/Guardia) y filtro de año.