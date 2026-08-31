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
        return;
    }

    emptyState.classList.add("hidden");
    storeInfo.classList.remove("hidden");
    staffSection.classList.remove("hidden");

    const store = stores[currentStore];
    const country = countries[store.country];

    document.getElementById("storeName").textContent = store.name;
    document.getElementById("storeAddress").textContent = store.address;
    document.getElementById("countryDisplay").textContent = `${country.flag} ${country.name}`;
    document.getElementById("staffCount").textContent = (schedules[currentStore] || []).length;

    document.getElementById("filterMonth").value = "";
    document.getElementById("filterWeek").value = "";
}

function renderStaffList() {
    const container = document.getElementById("staffList");

    const filterMonth = document.getElementById("filterMonth").value;
    const filterWeek = document.getElementById("filterWeek").value;

    let staff = schedules[currentStore] || [];

    if (filterMonth) {
        staff = staff.filter(s => s.month === filterMonth);
    }

    if (filterWeek) {
        staff = staff.filter(s => s.week === filterWeek);
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

    // Días de la semana en orden
    const days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

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
        return days.find(d => day.indexOf(d) === 0) || day;
    }

    const startMin = toMinutes(DAY_START);
    const endMin = toMinutes(DAY_END);
    const totalMin = endMin - startMin;

    function turnoStyle(sch) {
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

    // Encabezado con los 7 días
    function buildHeader() {
        let h =
            '<div class="cal-header">' +
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

        let row =
            '<div class="cal-row">' +
            `<div class="cal-person">
                <div class="cal-avatar">${initials}</div>
                <div>
                    <div class="cal-person-name">${person.name}</div>
                    <div class="cal-person-meta">${person.email}<br>${person.phone}</div>
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
            row += `<div class="cal-cell">${cellInner}</div>`;
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
