# Manual de Usuario — Gestor de Horarios por Tienda

**Versión:** 1.1  
**Fecha:** Septiembre 2026  
**Plataforma:** Web (HTML + CSS + JavaScript)

---

## Índice

1. [Descripción general](#1-descripción-general)
2. [Requisitos y cómo abrir la aplicación](#2-requisitos-y-cómo-abrir-la-aplicación)
3. [Vista general de la pantalla](#3-vista-general-de-la-pantalla)
4. [Filtro por País](#4-filtro-por-país)
5. [Filtro por Ciudad](#5-filtro-por-ciudad)
6. [Filtro por Tienda](#6-filtro-por-tienda)
7. [Calendario Mensual](#7-calendario-mensual)
8. [Colores de los turnos](#8-colores-de-los-turnos)
9. [Tooltip: Información del técnico](#9-tooltip-información-del-técnico)
10. [Modo Guardias](#10-modo-guardias)
11. [Filtro de Mes](#11-filtro-de-mes)
12. [Cómo editar horarios y guardias](#12-cómo-editar-horarios-y-guardias)
13. [Preguntas frecuentes (FAQ)](#13-preguntas-frecuentes-faq)

---

## 1. Descripción general

El **Gestor de Horarios por Tienda** es una aplicación web que permite visualizar los horarios del personal técnico en cada tienda de forma clara y organizada.

**Funcionalidades principales:**

- Filtrar por **país**, **ciudad** y **tienda**.
- Ver el **calendario mensual** de turnos por tienda, organizado por semanas y días.
- Consultar **todas las guardias** de todas las tiendas en una sola lista.
- Obtener la **información de contacto** de cada técnico (foto, correo, teléfono) al pasar el cursor.
- **Editar y configurar** horarios fácilmente desde archivos JSON.

---

## 2. Requisitos y cómo abrir la aplicación

### Requisitos
- Un navegador web moderno (Chrome, Firefox, Edge, Safari).
- Conexión a internet (si se accede desde Vercel).

### Formas de acceder

#### Opción A — Desde Vercel (recomendada)
1. Abre la URL proporcionada por el administrador.
2. La aplicación se carga automáticamente.

#### Opción B — Desde tu computadora (local)
1. Abre una terminal en la carpeta del proyecto.
2. Ejecuta: `python -m http.server 8000`
3. Abre tu navegador en: `http://localhost:8000`

> **Nota:** No se recomienda abrir el archivo `index.html` directamente con doble clic, ya que los datos podrían no cargarse correctamente por restricciones del navegador.

---

## 3. Vista general de la pantalla

Al abrir la aplicación verás:

```
┌──────────────────────────────────────────────────────┐
│  🏢 Gestor de Horarios por Tienda                    │
│  Filtra por país, ciudad y tienda                    │
├──────────────────────────────────────────────────────┤
│  🌍 País │ 🏙️ Ciudad │ 🏪 Tienda │ [🛡️ Guardias]   │
│  (una sola barra compacta de filtros)                │
├──────────────────────────────────────────────────────┤
│  (Banner de info de tienda - al seleccionar)         │
├──────────────────────────────────────────────────────┤
│  📅 Calendario Mensual                               │
└──────────────────────────────────────────────────────┘
```

Los tres filtros (País, Ciudad y Tienda) están en una **barra compacta** en una sola fila, para ahorrar espacio y agilizar la navegación.

---

## 4. Filtro por País

**Ubicación:** Barra de filtros compacta, campo "🌍 País".

**Cómo usarlo:**
1. Haz clic en el desplegable.
2. Selecciona el país deseado (ej. 🇨🇴 Colombia).
3. El desplegable de **ciudades** se actualiza mostrando las ciudades de ese país.

**Países disponibles:**
| País | Bandera |
|------|---------|
| Colombia | 🇨🇴 |
| México | 🇲🇽 |
| Argentina | 🇦🇷 |
| Chile | 🇨🇱 |
| Perú | 🇵🇪 |
| Ecuador | 🇪🇨 |
| Panamá | 🇵🇦 |

---

## 5. Filtro por Ciudad

**Ubicación:** Barra de filtros compacta, campo "🏙️ Ciudad".

**Cómo usarlo:**
1. Primero selecciona un país (sección anterior).
2. Haz clic en el desplegable de ciudades.
3. Selecciona la ciudad deseada (ej. Bogotá).

**Ciudades en Colombia:**
| Ciudad |
|--------|
| Bogotá |
| Chía |
| Bojacá |

> **Importante:** Todos los centros comerciales (C.C) están en **Bogotá**. Las excepciones son **Fontanar** (tienda8), que está en **Chía**, y **Bima** (tienda9), que está en **Bojacá**.

Al elegir una ciudad, el desplegable de **tiendas** se actualiza mostrando solo las tiendas de esa ciudad.

---

## 6. Filtro por Tienda

**Ubicación:** Barra de filtros, en el campo "🏪 Tienda".

**Cómo usarlo:**
1. Primero selecciona un país y una ciudad (secciones anteriores).
2. Haz clic en el desplegable de tiendas.
3. Selecciona la tienda que deseas consultar.

**Al seleccionar una tienda:**
- Aparece un **banner azul** con:
  - Nombre de la tienda
  - Dirección
  - Ciudad y país
  - Número de empleados asignados
- Se muestra el **calendario mensual** de esa tienda.

**Botón "🛡️ Guardias en [ciudad]":**
En la barra de filtros, al elegir una ciudad aparece un botón naranja que abre la **lista de guardias de esa ciudad** (por ejemplo, "🛡️ Guardias en Bogotá"), mostrando solo las guardias de las tiendas de esa ciudad.

**Tiendas en Colombia:**
| Tienda | Nombre | Ciudad | Dirección |
|--------|--------|--------|-----------|
| tienda1 | C.C Colina | Bogotá | Centro Comercial Parque la colina |
| tienda2 | Zona Calle 82 | Bogotá | Zona Comercial Calle 82 |
| tienda3 | C.C Felicidad | Bogotá | Centro Comercial La Felicidad |
| tienda4 | C.C Plaza Central | Bogotá | Centro Comercial Plaza Central |
| tienda5 | C.C Unicentro | Bogotá | Centro Comercial Unicentro |
| tienda6 | Oficina Colina | Bogotá | Oficinas Corporativas Colina |
| tienda7 | C.C Titan | Bogotá | Centro Comercial Titan Plaza |
| tienda8 | C.C Fontanar | Chía | Centro Comercial Fontanar |
| tienda9 | Bima | Bojacá | Bodega Bima, Bojacá |

---

## 7. Calendario Mensual

**Ubicación:** Sección principal de la pantalla.

### Estructura
- **Filas:** Cada fila representa una **semana** (Semana 1, Semana 2, ..., Semana 5).
- **Columnas:** Cada columna representa un **día** (Lunes a Domingo).
- **Celdas:** Cada celda muestra:
  - El **número del día** (esquina superior derecha).
  - Los **turnos** de los técnicos ese día.

### Cada turno (tarjeta dentro de la celda) muestra:
- 📸 **Foto** del técnico (o sus **iniciales** si no tiene foto).
- 👤 **Nombre** del técnico.
- 🕐 **Hora** del turno (ej. `08:00 – 16:00`).
- 🛡️ Etiqueta **"Guardia"** si es un turno de guardia.

### Números en gris
Algunos números aparecen en **gris claro**. Son días de otro mes que aparecen en la rejilla para completar la semana. Ejemplo: si el día 1 cae en martes, la celda del lunes mostrará el último día del mes anterior en gris.

---

## 8. Colores de los turnos

| Color | Significado |
|-------|-------------|
| 🔵 **Azul** | **Jornada completa** (9 horas o más) — turno laboral completo |
| 🟢 **Verde** | **Jornada parcial** (menos de 9 horas) — cobertura parcial |
| 🟠 **Naranja** | **Guardia** — turno especial de guardia |

---

## 9. Tooltip: Información del técnico

**Cómo acceder:** Pasa el cursor sobre cualquier turno en el calendario.

**Qué muestra:**
- 📸 **Foto** grande del técnico (o iniciales si no tiene foto).
- 👤 **Nombre** completo.
- 📧 **Correo** electrónico.
- 📱 **Teléfono** de contacto.

> El tooltip aparece como un recuadro flotante al lado del cursor y desaparece al quitar el mouse.

---

## 10. Modo Guardias

Las guardias se consultan **por ciudad** desde la barra de filtros (no hay un botón global).

### Ver guardias por ciudad
1. En la barra de filtros, selecciona un **país** y después una **ciudad**.
2. Aparece el botón naranja **"🛡️ Guardias en [ciudad]"** (ej. "Guardias en Bogotá").
3. Púlsalo: se abren las guardias de las tiendas de esa ciudad.

### Contenido de cada tarjeta de guardia
Cada tarjeta muestra:
- 📸 **Foto** del técnico (o iniciales).
- 👤 **Nombre**, 📧 **correo** y 📱 **teléfono**.
- 📆 **Día con número** (ej. "Domingo 6").
- 🏪 **Nombre de la tienda** donde tiene la guardia.
- 🏙️ **Ciudad** de la tienda.
- 🌍 **País** de la tienda.

### Selectores en las guardias
Dentro del panel hay filtros para:
- **Mes** (ver guardias de otro mes).
- **País** (ver solo las guardias de un país).
- **Ciudad** (ver solo las guardias de una ciudad).

### Agrupación
Las guardias están **agrupadas por semana** (Semana 1, Semana 2, ...) para fácil visualización.

### Cerrar el panel de guardias
Pulsa el botón **"✖ Cerrar"** (arriba a la derecha del panel) para volver a la vista normal.

---

## 11. Filtro de Mes

**Ubicación:** Desplegable "📅 Mes" arriba del calendario de la tienda.

**Cómo usarlo:**
1. Haz clic en el desplegable.
2. Selecciona el mes que deseas consultar.
3. El calendario se actualiza automáticamente.

**Comportamiento:**
- Al entrar a una tienda se **preselecciona el mes actual**.
- Si cambias de mes, **se limpia el calendario** y se carga el nuevo.
- Si un mes no tiene datos, verás: *"No hay horarios para esta tienda."*

> **Nota:** Actualmente solo hay datos de Septiembre. Los demás meses mostrarán vacíos hasta que se carguen horarios.

---

## 12. Cómo editar horarios y guardias

No hay panel de administración visual. Los datos se editan directamente en los archivos JSON.

### Editar personas (`personas.json`)

Para agregar una persona nueva, añade un objeto a la lista:

```json
{
  "id": "juan-perez",
  "name": "Juan Perez",
  "email": "juan.perez@empresa.com",
  "phone": "300 1234567",
  "photo": "tecnicos/web/juan.webp"
}
```

**Campos:**
| Campo | Descripción |
|-------|-------------|
| `id` | Identificador único (sin espacios, usar guiones) |
| `name` | Nombre completo |
| `email` | Correo electrónico |
| `phone` | Número de teléfono |
| `photo` | Ruta a la foto (opcional) |

### Editar horarios (`horarios.json`)

Cada tienda tiene su sección. Ejemplo para tienda1:

```json
"tienda1": [
  {
    "personaId": "juan-perez",
    "month": "Septiembre",
    "week": "Semana 2",
    "day": "Lunes",
    "start": "08:00",
    "end": "17:00",
    "type": "normal"
  }
]
```

**Campos:**
| Campo | Descripción |
|-------|-------------|
| `personaId` | Debe coincidir con un `id` en personas.json |
| `month` | Nombre del mes en español |
| `week` | Semana (Semana 1 a Semana 5) |
| `day` | Día de la semana |
| `start` | Hora de inicio (solo para type normal) |
| `end` | Hora de fin (solo para type normal) |
| `type` | `"normal"` o `"guardia"` |

### Crear una guardia

Para asignar una guardia, crea un registro con `type: "guardia"`:

```json
{
  "personaId": "angel-ortiz",
  "month": "Septiembre",
  "week": "Semana 1",
  "day": "Miércoles",
  "type": "guardia"
}
```

### Agregar una tienda nueva

1. Agrega la tienda en `funciones.js` dentro del objeto `stores`:

```javascript
tienda10: { 
  name: "Nueva Tienda", 
  address: "Dirección de la tienda", 
  country: "colombia",
  city: "bogota"
}
```

2. Si la ciudad no existe, agrégala al objeto `cities` (también en `funciones.js`):

```javascript
const cities = {
  bogota: { name: "Bogotá", country: "colombia" },
  chia: { name: "Chía", country: "colombia" },
  bojaca: { name: "Bojacá", country: "colombia" },
  cali: { name: "Cali", country: "colombia" }
};
```

3. Agrega los horarios en `horarios.json` bajo la clave `"tienda10"`.

> **Importante:** Guarda siempre los archivos JSON con codificación **UTF-8** para que se muestren correctamente los acentos.

---

## 13. Preguntas frecuentes (FAQ)

**¿Por qué no cargan los datos al abrir el archivo directamente?**
Debido a las restricciones de CORS del navegador con el protocolo `file://`. Usa la versión de Vercel o un servidor local.

**¿El mes siempre muestra Septiembre?**
No. Se preselecciona el mes actual del sistema. Cuando se carguen datos de otros meses, podrás cambiar el filtro.

**¿Qué significan los números en gris?**
Son días del mes anterior o siguiente que aparecen en la rejilla para completar la semana.

**¿Dónde veo la información del técnico?**
Al pasar el cursor sobre cualquier turno aparece un tooltip con foto, nombre, correo y teléfono.

**¿Cómo sé quién está de guardia?**
Selecciona una ciudad y pulsa **"🛡️ Guardias en [ciudad]"**. Aparece la lista de guardias de esa ciudad, agrupadas por semana.

**¿Puedo filtrar las guardias por país o ciudad?**
Sí. En el modo guardias hay filtros de país y ciudad para mostrar solo las guardias de esa zona. También puedes pulsar **"🛡️ Guardias en [ciudad]"** en la barra de filtros para ver las guardias de una ciudad concreta al instante.

**¿Qué tiendas NO están en Bogotá?**
Fontanar (tienda8) está en **Chía** y Bima (tienda9) está en **Bojacá**. El resto están en **Bogotá**.

**¿Las guardias tienen horario definido?**
No. Las guardias se muestran con la etiqueta "Guardia" sin horas específicas, ya que cubren todo el día.

**¿Cuántas tiendas y empleados hay actualmente?**
9 tiendas (en Bogotá, Chía y Bojacá) y 7 empleados únicos, con 194 registros de horarios (8 guardias).

---

*Manual de usuario v1.1 — Gestor de Horarios por Tienda — Septiembre 2026*
