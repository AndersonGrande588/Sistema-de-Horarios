# 📖 Guía de uso — Gestor de Horarios por Tienda

> Guía práctica: qué es la página, qué hace cada parte, para qué sirve y cómo usarla.

---

## 1. ¿Qué es y para qué sirve?

Es una página web que muestra los **horarios del personal técnico en las tiendas**. Sirve para:

- Ver de un vistazo **quién trabaja en cada tienda**, **en qué día/semana** y **con qué jornada**.
- **Coordinar cobertura**: saber si una tienda tiene personal todos los días y si hay guardias asignadas.
- Consultar el **dato de contacto** de cada técnico (correo y teléfono, al pasar el cursor sobre el turno se muestra su info).

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

### Paso 1 — Elegir el país 🌍
Desplegable **"Seleccionar País"** (arriba). Al elegir un país, se activa el menú de tiendas con solo las tiendas de ese país.
- Países disponibles: Colombia, México, Argentina, Chile, Perú, Ecuador y Panamá. *(Solo Colombia y Panamá tienen tiendas definidas a día de hoy.)*

### Paso 2 — Elegir la tienda 🏪
Desplegable **"Seleccionar Tienda"**. Al elegir una tienda:

1. Aparece el **banner azul** con:
   - Nombre y dirección de la tienda.
   - País (con bandera).
   - **nº de empleados asignados** (personas únicas con horarios en esa tienda).
2. Aparece la sección **"Calendario Mensual"** con el calendario del personal.

> Si solo quieres volver a empezar: elige "Elige una tienda" o cambia de país y todo se reinicia.

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
- 🔎 Al **pasar el cursor** sobre un turno, aparece un recuadro con el nombre y la hora (tooltip).

### Colores de los turnos (importante) 🎨

| Color | Qué significa |
|---|---|
| 🔵 **Azul** | **Jornada completa** (9 horas o más) — día cubierto todo el turno laboral. |
| 🟢 **Verde** | **Jornada parcial** (menos de 9 horas) — cobertura parcial. |
| 🟠 **Naranja** | **Guardia** — turno especial de guardia. |

---

## 5. Botones de señalización 👥

Barra encima del calendario con 3 botones:

| Botón | Qué hace |
|---|---|
| **Todas** *(activo por defecto)* | Muestra todos los turnos (normales y guardias). |
| **Jornada normal** | Muestra SOLO las jornadas normales; oculta las guardias. |
| **Guardia** | Muestra SOLO las guardias; oculta las jornadas normales. |

Útil para, por ejemplo, revisar rápidamente qué días hay guardia o qué días no.

---

## 6. Filtros de Mes y Año 🗓️

Debajo de los botones hay dos desplegables (aparecen al elegir tienda):

- **📅 Mes:** contiene los **12 meses del año**. Al entrar a una tienda se preselecciona el **mes actual** (hoy es Septiembre). Puedes cambiarlo para ver otro mes.
- **🗓️ Año:** el año de los horarios (si los datos no indican año, se usa el año actual).

**Importante:**
- Cada vez que cambias el mes o el año, **la información anterior se limpia** y se renderiza el calendario del mes/año elegido.
- Si eliges un mes **sin horarios**, verás el aviso *"No hay horarios para esta tienda."*

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

> Al editar, guarda el archivo con **codificación UTF-8** (para que se vean bien acentos como "Miércoles").

---

## 9. Preguntas frecuentes (FAQ)

**¿Por qué no cargan los datos al abrir el archivo directamente?**
Por la política CORS del navegador con el protocolo `file://`. Usa Vercel o un servidor local.

**¿El mes siempre va a estar en Septiembre?**
No. Se preselecciona el **mes actual del sistema**. Cuando haya datos de otros meses, verás que salen al cambiar el filtro.

**¿Por qué veo números en gris como "31" o "1"?**
Son días de otro mes que encajan en la rejilla del calendario real (posición de la semana).

**Las guardias muestran "Guardia" en vez de la hora: ¿es un error?**
Es intencional: las guardias no tienen una jornada fija de horas, se marcan como turno de guardia 24/7.

**¿Cuántos empleados y tiendas hay?**
7 empleados únicos; 9 tiendas definidas; 8 tiendas con horarios cargados (todas de Septiembre).

---

## 10. Resumen rápido

1. Países → Tienda.
2. Banner muestra datos de la tienda y nº de empleados.
3. Calendario mensual: semanas abajo, días a la derecha, números + turnos por celda.
4. Botones: Todas / Jornada normal / Guardia.
5. Filtros: Mes (12) y Año, se limpian y recargan al cambiar.
6. Azul = completa, Verde = parcial, Naranja = guardia.
7. Pasa el cursor sobre un turno para ver su detalle.