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
    tienda9: { name: "Bima", address: "Bodega Bima, Bojacá", country: "colombia" }
};

// Datos cargados desde los JSON separados
let personas = [];
let horarios = {};   // { tiendaId: [ { personaId, month, week, day, start, end, type } ] }
let currentStore = "";

// Filtro de fecha (mes) del calendario
let currentMonth = "";

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

    document.getElementById("staffList").innerHTML = "";
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
//  BLOQUE 3.5: FILTRO DE MES
// ═══════════════════════════════════════════════════════════

const MONTH_NAMES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];

function populateDateFilters() {
    const mesSel = document.getElementById("monthSelect");
    if (!mesSel) return;

    mesSel.innerHTML = '<option value="">-- Mes --</option>' +
        MONTH_NAMES.map(m => `<option value="${m}">${m}</option>`).join("");
    currentMonth = MONTH_NAMES[new Date().getMonth()] || "";
    mesSel.value = currentMonth;
}

function selectMonth() {
    currentMonth = document.getElementById("monthSelect").value;
    document.getElementById("staffList").innerHTML = "";
    if (!currentMonth) return;
    renderCalendar();
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 3.8: TURNOS ESTÁNDAR (optimización)
// ═══════════════════════════════════════════════════════════

const SHIFTS = {
    "08-17": { start: "08:00", end: "17:00", label: "08:00–17:00" },
    "08-16": { start: "08:00", end: "16:00", label: "08:00–16:00" },
    "09-18": { start: "09:00", end: "18:00", label: "09:00–18:00" },
    "09-17": { start: "09:00", end: "17:00", label: "09:00–17:00" }
};

function turnoLabel(sch) {
    if (sch.type === "guardia") return "Guardia";
    if (sch.start && sch.end) {
        const f = Object.values(SHIFTS).find(x => x.start === sch.start && x.end === sch.end);
        return f ? f.label : `${sch.start}–${sch.end}`;
    }
    return "—";
}

const diasSemana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

function normalizeDay(d) {
    return diasSemana.find(x => String(d).indexOf(x) === 0) || String(d);
}

function toMin(t) {
    const [h, m] = String(t).split(":").map(Number);
    return (isNaN(h) ? 0 : h) * 60 + (isNaN(m) ? 0 : m);
}

function turnoColor(sch) {
    if (sch.type === "guardia") return "guardia";
    const dur = toMin(sch.end) - toMin(sch.start);
    if (dur >= 540) return "jornada-completa";
    return "jornada-parcial";
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 4: CALENDARIO MENSUAL
// ═══════════════════════════════════════════════════════════

function renderCalendar() {
    const container = document.getElementById("staffList");
    const records = (horarios[currentStore] || []).filter(r =>
        !currentMonth || String(r.month) === currentMonth
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

    // Semanas que aparecen (en orden natural Semana 1..5)
    const semanaSet = new Set();
    records.forEach(r => semanaSet.add(r.week));
    const semanas = [...semanaSet].sort((a, b) => {
        const na = parseInt(a.replace(/\D/g, ""), 10) || 0;
        const nb = parseInt(b.replace(/\D/g, ""), 10) || 0;
        return na - nb;
    });

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
    const dataYear = records.find(r => r.year);
    const yearNum = dataYear ? (parseInt(dataYear.year, 10) || new Date().getFullYear()) : new Date().getFullYear();
    const firstDate = new Date(yearNum, monthIndex, 1);
    const firstWeekday = (firstDate.getDay() + 6) % 7; // 0 = lunes

    // Fila de una semana
    function buildWeekRow(semana, semanaIndex) {
        let cells = '';
        diasSemana.forEach((dia, dIdx) => {
            const dayNum = semanaIndex * 7 + dIdx - firstWeekday + 1;
            const turnos = records.filter(r => r.week === semana && normalizeDay(r.day) === dia);
            cells += buildDayCell(turnos, personaById, dayNum);
        });
        return `<div class="cal-row cal-week-row"><div class="cal-week-label">${semana}</div>${cells}</div>`;
    }

    // Celda de un día: número del día real + lista de turnos de las personas
    // new Date(año, mes, N) se ajusta solo: N<=0 -> día del mes anterior,
    // N > días del mes -> día del mes siguiente (así no hay día 0 ni 32).
    function buildDayCell(turnos, personaById, dayNum) {
        const cellDate = new Date(yearNum, monthIndex, dayNum);
        const inMonth = cellDate.getMonth() === monthIndex && cellDate.getFullYear() === yearNum;
        const dayLabel = `<div class="cal-day-num${inMonth ? "" : " out-month"}">${cellDate.getDate()}</div>`;
        if (turnos.length === 0) {
            return `<div class="cal-cell no-day">${dayLabel}<span class="libre">—</span></div>`;
        }
        let inner = dayLabel;
        turnos.forEach(sch => {
            const p = personaById[sch.personaId] || {};
            const name = p.name || "?";
            const hora = turnoLabel(sch);
            const foto = p.photo
                ? `<img class="cal-cell-photo" src="${p.photo}" alt="${name}">`
                : `<span class="cal-cell-initials">${initials(name)}</span>`;
            const tienda = (stores[currentStore] || {}).name || "";
            inner += `
                <div class="cal-event ${turnoColor(sch)}" data-tip-id="${sch.personaId}" data-tip-store="${tienda}">
                    ${foto}
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
            <div class="cal-month-title">${currentMonth} ${yearNum}</div>
            <div class="cal-grid">
                ${buildHeader()}
                ${rows}
            </div>
        </div>`;
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 5: HELPERS
// ═══════════════════════════════════════════════════════════

function initials(name) {
    return String(name).split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 6: PANEL DE GUARDIAS DE TODOS LOS TÉCNICOS (CALENDARIO)
// ═══════════════════════════════════════════════════════════

let guardsMode = false;

function guardsMonth() {
    const sel = document.getElementById("guardsMonthSelect");
    return sel ? sel.value : currentMonth;
}

function guardsCountry() {
    const sel = document.getElementById("guardsCountrySelect");
    return sel ? sel.value : "";
}

function toggleAllGuards() {
    guardsMode = !guardsMode;
    const panel = document.getElementById("allGuardsPanel");
    const btn = document.getElementById("btnAllGuards");
    if (!panel) return;

    if (btn) btn.textContent = guardsMode ? "✖ Cerrar guardias" : "🛡️ Ver todas las guardias";

    if (guardsMode) {
        document.querySelectorAll(".selector-card").forEach(c => c.classList.add("hidden"));
        document.getElementById("storeInfo").classList.add("hidden");
        document.getElementById("staffSection").classList.add("hidden");
        document.getElementById("emptyState").classList.add("hidden");

        const sel = document.getElementById("guardsMonthSelect");
        if (sel) {
            sel.innerHTML = '<option value="">-- Mes --</option>' +
                MONTH_NAMES.map(m => `<option value="${m}">${m}</option>`).join("");
            sel.value = currentMonth || MONTH_NAMES[new Date().getMonth()];
        }

        const monthVal = sel ? sel.value : (currentMonth || MONTH_NAMES[new Date().getMonth()]);
        const countriesInMonth = new Set();
        for (const [tid, recs] of Object.entries(horarios)) {
            recs.forEach(r => {
                if (r.type !== "guardia") return;
                if (monthVal && String(r.month) !== monthVal) return;
                const t = stores[tid];
                if (t && t.country) countriesInMonth.add(t.country);
            });
        }
        const cSel = document.getElementById("guardsCountrySelect");
        if (cSel) {
            cSel.innerHTML = '<option value="">🌍 Todos los países</option>' +
                [...countriesInMonth].sort().map(cc => {
                    const c = countries[cc];
                    return `<option value="${cc}">${c ? c.flag + " " + c.name : cc}</option>`;
                }).join("");
        }

        panel.classList.remove("hidden");
        renderAllGuards();
    } else {
        panel.classList.add("hidden");
        document.querySelectorAll(".selector-card").forEach(c => c.classList.remove("hidden"));
        if (currentStore) {
            renderStore();
        } else {
            document.getElementById("storeInfo").classList.add("hidden");
            document.getElementById("staffSection").classList.add("hidden");
            document.getElementById("emptyState").classList.remove("hidden");
        }
    }
}

function selectGuardsFilters() {
    const list = document.getElementById("allGuardsList");
    if (list) list.innerHTML = "";
    renderAllGuards();
}

// Lista de guardias de todos los técnicos (con los datos de cada uno)
function renderAllGuards() {
    const list = document.getElementById("allGuardsList");
    if (!list) return;

    const monthSel = guardsMonth();
    const countrySel = guardsCountry();
    const personaById = {};
    personas.forEach(p => { personaById[p.id] = p; });

    const guardias = [];
    for (const [tiendaId, recs] of Object.entries(horarios)) {
        recs.forEach(r => {
            if (r.type !== "guardia") return;
            if (monthSel && String(r.month) !== monthSel) return;
            const t = stores[tiendaId] || {};
            if (countrySel && t.country !== countrySel) return;
            guardias.push({ tiendaId: tiendaId, ...r });
        });
    }

    if (guardias.length === 0) {
        list.innerHTML = '<p class="tech-empty">No hay guardias en este mes/país.</p>';
        return;
    }

    const dayOrder = { "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6 };
    const monthIndex = MONTH_NAMES.indexOf(guardsMonth());
    const dataYear = guardias.find(r => r.year);
    const yearNum = dataYear ? (parseInt(dataYear.year, 10) || new Date().getFullYear()) : new Date().getFullYear();
    const firstDate = new Date(yearNum, monthIndex, 1);
    const firstWeekday = (firstDate.getDay() + 6) % 7;

    guardias.forEach(g => {
        const weekIdx = parseInt(String(g.week).replace(/\D/g, ""), 10) || 0;
        const dayIdx = dayOrder[normalizeDay(g.day)] !== undefined ? dayOrder[normalizeDay(g.day)] : 9;
        const cellDate = new Date(yearNum, monthIndex, (weekIdx - 1) * 7 + dayIdx - firstWeekday + 1);
        g._week = weekIdx;
        g._dayNum = cellDate.getDate();
    });

    guardias.sort((a, b) => {
        if (a._week !== b._week) return a._week - b._week;
        const da = dayOrder[normalizeDay(a.day)] !== undefined ? dayOrder[normalizeDay(a.day)] : 9;
        const db = dayOrder[normalizeDay(b.day)] !== undefined ? dayOrder[normalizeDay(b.day)] : 9;
        return da - db;
    });

    const semanaSet = [...new Set(guardias.map(g => g._week))].sort((x, y) => x - y);

    function card(g) {
        const t = stores[g.tiendaId] || {};
        const tl = t.name || g.tiendaId;
        const c = countries[t.country] || {};
        const p = personaById[g.personaId] || {};
        const avatar = p.photo
            ? `<img class="guard-avatar" src="${p.photo}" alt="">`
            : `<span class="guard-avatar guard-avatar-fallback">${initials(p.name || "?")}</span>`;
        return `
            <div class="guard-card" data-tip-id="${g.personaId}" data-tip-store="${tl}">
                ${avatar}
                <div class="guard-info">
                    <div class="guard-name">${p.name || "?"}</div>
                    <div class="guard-meta">📧 ${p.email || "—"}</div>
                    <div class="guard-meta">📱 ${p.phone || "—"}</div>
                </div>
                <div class="guard-when">
                    <span class="guard-badge">📆 ${normalizeDay(g.day) || ""} ${g._dayNum}</span>
                    <span class="guard-badge guard-store">🏪 ${tl}</span>
                    ${c.flag ? `<span class="guard-badge guard-country">${c.flag} ${c.name}</span>` : ""}
                </div>
            </div>`;
    }

    list.innerHTML = semanaSet.map(w => `
        <div class="guard-week">📅 Semana ${w}</div>
        ${guardias.filter(g => g._week === w).map(card).join("")}
    `).join("");
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 7: TOOLTIP CON FOTO + INFO DEL TÉCNICO (HOVER)
// ═══════════════════════════════════════════════════════════

function getTechTip() {
    let tip = document.getElementById("techTooltip");
    if (!tip) {
        tip = document.createElement("div");
        tip.id = "techTooltip";
        tip.className = "tech-tooltip";
        document.body.appendChild(tip);
    }
    return tip;
}

function positionTip(event) {
    const tip = getTechTip();
    const pad = 14;
    let x = event.clientX + pad;
    let y = event.clientY + pad;
    const r = tip.getBoundingClientRect();
    if (x + r.width > window.innerWidth) x = event.clientX - r.width - pad;
    if (y + r.height > window.innerHeight) y = event.clientY - r.height - pad;
    tip.style.left = Math.max(0, x) + "px";
    tip.style.top = Math.max(0, y) + "px";
}

document.addEventListener("mouseover", (event) => {
    const el = event.target.closest ? event.target.closest("[data-tip-id]") : null;
    const tip = getTechTip();
    if (!el) {
        tip.style.display = "none";
        return;
    }
    const p = personas.find(x => x.id === el.dataset.tipId) || {};
    const store = el.dataset.tipStore || "";
    tip.innerHTML =
        (p.photo
            ? `<img class="tip-photo" src="${p.photo}" alt="">`
            : `<span class="tip-photo tip-photo-fallback">${initials(p.name || "?")}</span>`) +
        `<div class="tip-name">${p.name || "?"}</div>` +
        (p.email ? `<div class="tip-meta">📧 ${p.email}</div>` : "") +
        (p.phone ? `<div class="tip-meta">📱 ${p.phone}</div>` : "") +
        (store ? `<div class="tip-meta">🏪 ${store}</div>` : "");
    tip.style.display = "block";
    positionTip(event);
});

document.addEventListener("mousemove", (event) => {
    const tip = getTechTip();
    if (tip.style.display === "block") positionTip(event);
});

document.addEventListener("mouseout", (event) => {
    const el = event.target.closest ? event.target.closest("[data-tip-id]") : null;
    if (!el) getTechTip().style.display = "none";
});
