// ═══════════════════════════════════════════════════════════
//  BLOQUE 1: DATOS DE LA APLICACIÓN
// ═══════════════════════════════════════════════════════════

const countries = {
    colombia: { name: "Colombia", flag: "\uD83C\uDDE8\uD83C\uDDF4" },
    mexico: { name: "México", flag: "\uD83C\uDDF2\uD83C\uDDFD" },
    argentina: { name: "Argentina", flag: "\uD83C\uDDE6\uD83C\uDDF7" },
    chile: { name: "Chile", flag: "\uD83C\uDDE8\uD83C\uDDF1" },
    peru: { name: "Perú", flag: "\uD83C\uDDF5\uD83C\uDDEA" },
    ecuador: { name: "Ecuador", flag: "\uD83C\uDDEA\uD83C\uDDEC" },
    panama: { name: "Panamá", flag: "\uD83C\uDDF5\uD83C\uDDF8" }
};

const stores = {
    tienda1: { name: "C.C Colina", address: "Centro Comercial Parque la colina", country: "colombia" },
    tienda2: { name: "Zona Calle 82", address: "Zona Comercial Calle 82", country: "colombia" },
    tienda3: { name: "C.C Felicidad", address: "Centro Comercial La Felicidad", country: "colombia" },
    tienda4: { name: "C.C Plaza Central", address: "Centro Comercial Plaza Central", country: "colombia" },
    tienda5: { name: "C.C Unicentro", address: "Centro Comercial Unicentro", country: "colombia" },
    tienda6: { name: "Oficina Colina", address: "Oficinas Corporativas Colina", country: "colombia" },
    tienda7: { name: "C.C Titan", address: "Centro Comercial Titan Plaza", country: "colombia" },
    tienda8: { name: "C.C Fontanar", address: "Centro Comercial Fontanar", country: "colombia" },
    tienda9: { name: "Bima", address: "Bodega Bima", country: "panama" }
};

let schedules = {};
let currentStore = "";

// ═══════════════════════════════════════════════════════════
//  FOTOS DE EMPLEADOS (carpeta /tecnicos)
//  Edita aquí para cambiar la imagen de cada empleado.
//  Si quieres añadir o corregir una foto, actualiza la ruta
//  y coloca el archivo dentro de la carpeta "tecnicos".
// ═══════════════════════════════════════════════════════════
const photos = {
    "Kevin Alean": "tecnicos/unnamed (1).webp",
    "Jersoon Gonzalez": "tecnicos/web/jersoon.webp",
    "Andres Bojaca": "tecnicos/web/bojaca.webp",
    "Julian Garzon": "tecnicos/web/julian.webp",
    "Anderson Grande": "tecnicos/web/anderson.webp",
    "Angel Ortiz": "tecnicos/unnamed (2).webp",
    "Andres Garzon": "tecnicos/unnamed (3).webp"
};

async function loadSchedules() {
    try {
        const response = await fetch('horarios.json');
        schedules = await response.json();
        console.log("Datos cargados:", schedules);
    } catch (error) {
        console.error("Error cargando datos:", error);
        schedules = {};
    }
}

loadSchedules();


// ═══════════════════════════════════════════════════════════
//  BLOQUE 2: FUNCIONES PRINCIPALES
// ═══════════════════════════════════════════════════════════

function filterStoresByCountry() {
    const countrySelect = document.getElementById("countrySelect");
    const storeSelect = document.getElementById("storeSelect");
    const selectedCountry = countrySelect.value;

    currentStore = "";
    storeSelect.value = "";
    document.getElementById("storeInfo").classList.add("hidden");
    document.getElementById("staffSection").classList.add("hidden");
    document.getElementById("emptyState").classList.remove("hidden");
    document.getElementById("staffList").innerHTML = "";
    document.getElementById("filterMonth").value = "";
    document.getElementById("filterWeek").value = "";
    document.getElementById("filterType").value = "";

    if (!selectedCountry) {
        storeSelect.innerHTML = '<option value="">-- Primero selecciona un país --</option>';
        storeSelect.disabled = true;
        return;
    }

    let options = '<option value="">-- Elige una tienda --</option>';

    for (const [storeId, storeData] of Object.entries(stores)) {
        if (storeData.country === selectedCountry) {
            options += `<option value="${storeId}">${storeData.name}</option>`;
        }
    }

    storeSelect.innerHTML = options;
    storeSelect.disabled = false;
}

function renderStore() {
    const select = document.getElementById("storeSelect");
    currentStore = select.value;

    const storeInfo = document.getElementById("storeInfo");
    const staffSection = document.getElementById("staffSection");
    const emptyState = document.getElementById("emptyState");

    if (!currentStore) {
        storeInfo.classList.add("hidden");
        staffSection.classList.add("hidden");
        emptyState.classList.remove("hidden");
        document.getElementById("staffList").innerHTML = "";
        return;
    }

    // Limpiar lista y filtros al elegir una tienda distinta
    document.getElementById("staffList").innerHTML = "";
    document.getElementById("filterMonth").value = "";
    document.getElementById("filterWeek").value = "";
    document.getElementById("filterType").value = "";

    emptyState.classList.add("hidden");
    storeInfo.classList.remove("hidden");
    staffSection.classList.remove("hidden");

    const store = stores[currentStore];
    const country = countries[store.country];

    document.getElementById("storeName").textContent = store.name;
    document.getElementById("storeAddress").textContent = store.address;
    document.getElementById("countryDisplay").textContent = `${country.flag} ${country.name}`;
    document.getElementById("staffCount").textContent = (schedules[currentStore] || []).length;
}

function renderStaffList() {
    const container = document.getElementById("staffList");

    const filterMonth = document.getElementById("filterMonth").value;
    const filterWeek = document.getElementById("filterWeek").value;
    const filterType = document.getElementById("filterType").value;

    let staff = schedules[currentStore] || [];

    // No mostrar el horario hasta que se elija una semana
    if (!filterWeek) {
        container.innerHTML = `
            <div class="empty-box">
                <div style="font-size: 36px; margin-bottom: 8px;">&#x1F4C5;</div>
                <p style="margin: 0; font-size: 15px;">Selecciona una semana para ver el horario del personal.</p>
            </div>`;
        return;
    }

    if (filterMonth) {
        staff = staff.filter(s => s.month === filterMonth);
    }

    if (filterWeek) {
        staff = staff.filter(s => s.week === filterWeek);
    }

    if (filterType) {
        staff = staff.filter(s => {
            const esGuardia = String(s.day).indexOf("Guardia") !== -1;
            if (filterType === "guardia") return esGuardia;
            if (filterType === "normal") return !esGuardia;
            return true;
        });
    }

    if (staff.length === 0) {
        container.innerHTML = `
            <div class="empty-box">
                <div style="font-size: 36px; margin-bottom: 8px;">&#x1F4ED;</div>
                <p style="margin: 0; font-size: 15px;">No hay personal para los filtros seleccionados.</p>
            </div>`;
        return;
    }

    // Agrupar horarios por persona
    const byPerson = {};
    staff.forEach(s => {
        if (!byPerson[s.name]) {
            byPerson[s.name] = {
                name: s.name,
                email: s.email,
                phone: s.phone,
                schedules: []
            };
        }
        byPerson[s.name].schedules.push(s);
    });

    // Orden fijo de la semana (para normalizar y ordenar)
    const ordenSemana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

    // Solo los días que se trabajan en la selección actual (en orden semanal)
    const days = ordenSemana.filter(d =>
        staff.some(s => String(s.day).indexOf(d) === 0)
    );

    // Constantes del calendario (coinciden con el CSS)
    const DAY_START = "08:00";   // hora de inicio del día
    const DAY_END = "17:00";     // hora de fin del día
    const CELL_HEIGHT = 300;     // alto en px de cada celda

    function toMinutes(time) {
        const [h, m] = time.split(":").map(Number);
        return h * 60 + m;
    }

    // Normaliza un día para que coincida con la lista (ej. quita " (Guardia)")
    function normalizeDay(day) {
        return ordenSemana.find(d => day.indexOf(d) === 0) || day;
    }

    const startMin = toMinutes(DAY_START);
    const endMin = toMinutes(DAY_END);
    const totalMin = endMin - startMin;

    function turnoStyle(sch) {
        // Guardia: ocupa todo el día, igual que un turno normal (08:00 - 17:00)
        if (String(sch.day).indexOf("Guardia") !== -1) {
            return `top:0;height:${CELL_HEIGHT}px;`;
        }
        const topMin = Math.max(toMinutes(sch.start), startMin);
        const bottomMin = Math.min(toMinutes(sch.end), endMin);
        if (bottomMin <= topMin) return null;
        const top = ((topMin - startMin) / totalMin) * CELL_HEIGHT;
        const height = ((bottomMin - topMin) / totalMin) * CELL_HEIGHT;
        return `top:${top}px;height:${height}px;`;
    }

    function turnoClass(sch) {
        const dur = toMinutes(sch.end) - toMinutes(sch.start);
        if (String(sch.day).indexOf("Guardia") !== -1) return "guardia";
        if (dur >= 540) return "jornada-completa";
        return "jornada-parcial";
    }

    // Encabezado con los días que se trabajan
    function buildHeader() {
        const cols = `180px repeat(${days.length}, 1fr)`;
        let h =
            `<div class="cal-header" style="grid-template-columns:${cols}">` +
            '<div class="cal-corner">Personal</div>';
        days.forEach((d, i) => {
            h += `<div class="cal-day-header">${d}<span class="cal-day-date">Horario</span></div>`;
        });
        h += '</div>';
        return h;
    }

    // Filas: una por persona
    function buildRow(person) {
        const initials = person.name
            .split(' ')
            .map(n => n[0])
            .join('')
            .substring(0, 2)
            .toUpperCase();

        // Foto del empleado: foto arriba del nombre si hay, sino iniciales
        const photo = photos[person.name];
        const photoHtml = photo
            ? `<img class="cal-photo" src="${photo}" alt="${person.name}">`
            : `<div class="cal-avatar">${initials}</div>`;

        // Disponibilidad semanal: días con turno / días laborales
        let diasConTurno = 0;
        days.forEach(day => {
            if (person.schedules.some(s => normalizeDay(s.day) === day)) diasConTurno++;
        });

        let row =
            `<div class="cal-row" style="grid-template-columns:180px repeat(${days.length}, 1fr)">` +
            `<div class="cal-person cal-person-column">
                ${photoHtml}
                <div>
                    <div class="cal-person-name">${person.name}</div>
                    <div class="cal-person-meta">${person.email}<br>${person.phone}</div>
                    <div class="cal-disp-badge">${diasConTurno}/${days.length} días disponibles</div>
                </div>
            </div>`;

        days.forEach(day => {
            const daySchedules = person.schedules.filter(s => normalizeDay(s.day) === day);
            if (daySchedules.length === 0) {
                row += '<div class="cal-cell no-day"></div>';
                return;
            }
            let cellInner = '';
            daySchedules.forEach(sch => {
                const style = turnoStyle(sch);
                if (!style) return;
                cellInner += `
                    <div class="cal-turno ${turnoClass(sch)}" style="${style}" title="${sch.day} ${sch.start}-${sch.end}">
                        ${sch.start}-${sch.end}
                    </div>`;
            });
            // Marcador de disponibilidad: clase según cobertura del horario normal
            let dispClass = 'disponible-parcial';
            if (daySchedules.some(s => (toMinutes(s.end) - toMinutes(s.start)) >= 540)) {
                dispClass = 'disponible-completo';
            }
            row += `<div class="cal-cell ${dispClass}">${cellInner}</div>`;
        });

        row += '</div>';
        return row;
    }

    let rows = '';
    Object.values(byPerson).forEach(p => { rows += buildRow(p); });

    container.innerHTML = `
        <div class="cal-wrapper">
            <div class="cal-grid">
                ${buildHeader()}
                ${rows}
            </div>
        </div>`;
}
