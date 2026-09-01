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

// Datos cargados desde los JSON separados
let personas = [];
let horarios = {};   // { tiendaId: [ { personaId, month, week, day, start, end, type } ] }
let currentStore = "";

// Modo de señalización en el calendario: todas | normal | guardia
let filterMode = "todas";

// Filtros de fecha (mes/año) del calendario
let currentMonth = "";
let currentYear = "";

async function loadData() {
    try {
        const [pRes, hRes] = await Promise.all([
            fetch('personas.json'),
            fetch('horarios.json')
        ]);
        personas = await pRes.json();
        horarios = await hRes.json();
        console.log("Personas:", personas);
        console.log("Horarios:", horarios);
    } catch (error) {
        console.error("Error cargando datos:", error);
        personas = [];
        horarios = {};
    }
}

loadData();


// ═══════════════════════════════════════════════════════════
//  BLOQUE 2: SELECCIÓN DE PAÍS / TIENDA
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
    document.getElementById("dateFilters").classList.add("hidden");

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
        document.getElementById("dateFilters").classList.add("hidden");
        return;
    }

    document.getElementById("staffList").innerHTML = "";
    filterMode = "todas";
    updateButtons();
    populateDateFilters();

    emptyState.classList.add("hidden");
    storeInfo.classList.remove("hidden");
    staffSection.classList.remove("hidden");

    const store = stores[currentStore];
    const country = countries[store.country];

    document.getElementById("storeName").textContent = store.name;
    document.getElementById("storeAddress").textContent = store.address;
    document.getElementById("countryDisplay").textContent = `${country.flag} ${country.name}`;
    const personasStore = new Set((horarios[currentStore] || []).map(r => r.personaId));
    document.getElementById("staffCount").textContent = personasStore.size;

    renderCalendar();
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 3: BOTONES DE SEÑALIZACIÓN
// ═══════════════════════════════════════════════════════════

function selectMode(mode) {
    filterMode = mode;
    updateButtons();
    renderCalendar();
}

function updateButtons() {
    ["todas", "normal", "guardia"].forEach(m => {
        const btn = document.getElementById("btn-" + m);
        if (btn) {
            if (m === filterMode) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        }
    });
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 3.5: FILTROS DE MES Y AÑO
// ═══════════════════════════════════════════════════════════

const MONTH_NAMES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

function populateDateFilters() {
    const recs = horarios[currentStore] || [];
    const mesSet = new Set();
    const anioSet = new Set();
    recs.forEach(r => {
        if (r.month) mesSet.add(String(r.month));
        if (r.year) anioSet.add(String(r.year));
    });
    if (anioSet.size === 0) anioSet.add(String(new Date().getFullYear()));

    const mesSel = document.getElementById("monthSelect");
    const anoSel = document.getElementById("yearSelect");
    if (!mesSel || !anoSel) return;

    mesSel.innerHTML = '<option value="">-- Mes --</option>' +
        MONTH_NAMES.map(m => `<option value="${m}">${m}</option>`).join("");
    anoSel.innerHTML = '<option value="">-- Año --</option>' +
        [...anioSet].sort((a, b) => a - b)
                    .map(y => `<option value="${y}">${y}</option>`).join("");

currentMonth = MONTH_NAMES[new Date().getMonth()] || "";
currentYear = [...anioSet].sort((a, b) => a - b)[0] || "";
    mesSel.value = currentMonth;
    anoSel.value = currentYear;

    document.getElementById("dateFilters").classList.remove("hidden");
}

function selectMonth() {
    currentMonth = document.getElementById("monthSelect").value;
    document.getElementById("staffList").innerHTML = "";
    if (!currentMonth) return;
    renderCalendar();
}

function selectYear() {
    currentYear = document.getElementById("yearSelect").value;
    document.getElementById("staffList").innerHTML = "";
    if (!currentYear) return;
    renderCalendar();
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 4: CALENDARIO MENSUAL
// ═══════════════════════════════════════════════════════════

function renderCalendar() {
    const container = document.getElementById("staffList");
    const records = (horarios[currentStore] || []).filter(r =>
        (!currentMonth || String(r.month) === currentMonth) &&
        (!currentYear || !r.year || String(r.year) === currentYear)
    );

    if (records.length === 0) {
        container.innerHTML = `
            <div class="empty-box">
                <div style="font-size: 36px; margin-bottom: 8px;">&#x1F4ED;</div>
                <p style="margin: 0; font-size: 15px;">No hay horarios para esta tienda.</p>
            </div>`;
        return;
    }

    // Mapa por id de persona
    const personaById = {};
    personas.forEach(p => { personaById[p.id] = p; });

    // Días de la semana en orden
    const diasSemana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

    // Semanas que aparecen (en orden natural Semana 1..5)
    const semanaSet = new Set();
    records.forEach(r => semanaSet.add(r.week));
    const semanas = [...semanaSet].sort((a, b) => {
        const na = parseInt(a.replace(/\D/g, ""), 10) || 0;
        const nb = parseInt(b.replace(/\D/g, ""), 10) || 0;
        return na - nb;
    });

    // Normaliza un día ("Domingo (Guardia)" -> "Domingo")
    function normalizeDay(d) {
        return diasSemana.find(x => String(d).indexOf(x) === 0) || String(d);
    }

    // Color de un turno según su tipo
    function turnoColor(sch) {
        if (sch.type === "guardia") return "guardia";
        const dur = toMin(sch.end) - toMin(sch.start);
        if (dur >= 540) return "jornada-completa";
        return "jornada-parcial";
    }

    function toMin(t) {
        const [h, m] = String(t).split(":").map(Number);
        return (isNaN(h) ? 0 : h) * 60 + (isNaN(m) ? 0 : m);
    }

    // ¿Debe mostrarse un turno según el modo de señalización?
    function visible(sch) {
        if (filterMode === "todas") return true;
        return sch.type === filterMode;
    }

    // Encabezado de días
    function buildHeader() {
        let h = '<div class="cal-row cal-header-row">' +
                '<div class="cal-corner">Semana</div>';
        diasSemana.forEach(d => {
            h += `<div class="cal-day-header">${d}</div>`;
        });
        h += '</div>';
        return h;
    }

    // Fecha real del mes mostrado (para numerar los días)
    const monthIndex = MONTH_NAMES.indexOf(currentMonth);
    const yearNum = parseInt(currentYear, 10) || new Date().getFullYear();
    const firstDate = new Date(yearNum, monthIndex, 1);
    const daysInMonth = new Date(yearNum, monthIndex + 1, 0).getDate();
    const firstWeekday = (firstDate.getDay() + 6) % 7; // 0 = lunes

    // Fila de una semana
    function buildWeekRow(semana, semanaIndex) {
        let cells = '';
        diasSemana.forEach((dia, dIdx) => {
            const dayNum = semanaIndex * 7 + dIdx - firstWeekday + 1;
            const turnos = records.filter(r => r.week === semana && normalizeDay(r.day) === dia && visible(r));
            cells += buildDayCell(turnos, personaById, dayNum, daysInMonth);
        });
        return `<div class="cal-row cal-week-row"><div class="cal-week-label">${semana}</div>${cells}</div>`;
    }

    // Celda de un día: número del día + lista de turnos de las personas
    function buildDayCell(turnos, personaById, dayNum, daysInMonth) {
        const inMonth = dayNum >= 1 && dayNum <= daysInMonth;
        const dayLabel = `<div class="cal-day-num${inMonth ? "" : " out-month"}">${dayNum}</div>`;
        if (turnos.length === 0) {
            return `<div class="cal-cell no-day">${dayLabel}<span class="libre">—</span></div>`;
        }
        let inner = dayLabel;
        turnos.forEach(sch => {
            const p = personaById[sch.personaId] || {};
            const name = p.name || "?";
            const initials = name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
            const hora = sch.type === "guardia" ? "Guardia" : ((sch.start && sch.end) ? `${sch.start}–${sch.end}` : "—");
            const photo = p.photo;
            const avatar = photo
                ? `<img class="cal-cell-photo" src="${photo}" alt="${name}">`
                : `<span class="cal-cell-initials">${initials}</span>`;
            inner += `
                <div class="cal-event ${turnoColor(sch)}" title="${name} ${hora}">
                    ${avatar}
                    <div class="cal-event-info">
                        <span class="cal-event-name">${name}</span>
                        <span class="cal-event-time">${hora}</span>
                    </div>
                </div>`;
        });
        return `<div class="cal-cell">${inner}</div>`;
    }

    let rows = '';
    semanas.forEach((s, i) => { rows += buildWeekRow(s, i); });

    container.innerHTML = `
        <div class="cal-wrapper">
            <div class="cal-month-title">${currentMonth} ${currentYear}</div>
            <div class="cal-grid">
                ${buildHeader()}
                ${rows}
            </div>
        </div>`;
}
