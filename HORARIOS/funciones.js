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

const cities = {
    bogota: { name: "Bogotá", country: "colombia" },
    chia: { name: "Chía", country: "colombia" }
};

const stores = {
    tienda1: { name: "C.C Colina", address: "Centro Comercial Parque la colina", country: "colombia", city: "bogota" },
    tienda2: { name: "Zona Calle 82", address: "Zona Comercial Calle 82", country: "colombia", city: "bogota" },
    tienda3: { name: "C.C Felicidad", address: "Centro Comercial La Felicidad", country: "colombia", city: "bogota" },
    tienda4: { name: "C.C Plaza Central", address: "Centro Comercial Plaza Central", country: "colombia", city: "bogota" },
    tienda5: { name: "C.C Unicentro", address: "Centro Comercial Unicentro", country: "colombia", city: "bogota" },
    tienda6: { name: "Oficina Colina", address: "Oficinas Corporativas Colina", country: "colombia", city: "bogota" },
    tienda7: { name: "C.C Titan", address: "Centro Comercial Titan Plaza", country: "colombia", city: "bogota" },
    tienda8: { name: "C.C Fontanar", address: "Centro Comercial Fontanar", country: "colombia", city: "chia" },
    tienda9: { name: "Bima", address: "Bodega Bima", country: "colombia", city: "chia" }
};

// Datos cargados desde los JSON separados
let personas = [];
let horarios = {};   // { tiendaId: [ { personaId, month, week, day, start, end, type } ] }
let currentStore = "";
let currentCity = "";

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

function resetStoreSelection() {
    currentStore = "";
    const storeSelect = document.getElementById("storeSelect");
    if (storeSelect) storeSelect.value = "";
    document.getElementById("storeInfo").classList.add("hidden");
    document.getElementById("staffSection").classList.add("hidden");
    document.getElementById("emptyState").classList.remove("hidden");
    if (document.getElementById("staffList")) document.getElementById("staffList").innerHTML = "";
}

function updateCityGuardsButton() {
    const btn = document.getElementById("btnCityGuards");
    if (!btn) return;
    if (currentCity && cities[currentCity]) {
        btn.classList.remove("hidden");
        btn.textContent = `🛡️ Guardias en ${cities[currentCity].name}`;
    } else {
        btn.classList.add("hidden");
    }
}

function filterStoresByCountry() {
    const countrySelect = document.getElementById("countrySelect");
    const citySelect = document.getElementById("citySelect");
    const selectedCountry = countrySelect.value;

    currentCity = "";
    resetStoreSelection();
    updateCityGuardsButton();

    citySelect.value = "";
    citySelect.disabled = true;
    citySelect.innerHTML = '<option value="">-- Elegir --</option>';

    if (!selectedCountry) {
        const storeSelect = document.getElementById("storeSelect");
        storeSelect.innerHTML = '<option value="">-- Elegir --</option>';
        storeSelect.disabled = true;
        return;
    }

    const citySet = new Set();
    for (const storeData of Object.values(stores)) {
        if (storeData.country === selectedCountry && storeData.city) {
            citySet.add(storeData.city);
        }
    }

    if (citySet.size === 0) {
        // País sin ciudades definidas: listar tiendas directamente
        populateStoreOptions(selectedCountry, "");
        return;
    }

    let options = '<option value="">-- Elegir --</option>';
    for (const cityId of citySet) {
        const c = cities[cityId];
        options += `<option value="${cityId}">${c ? c.name : cityId}</option>`;
    }
    citySelect.innerHTML = options;
    citySelect.disabled = false;

    const storeSelect = document.getElementById("storeSelect");
    storeSelect.innerHTML = '<option value="">-- Elegir --</option>';
    storeSelect.disabled = true;
}

function filterStoresByCity() {
    const citySelect = document.getElementById("citySelect");
    const selectedCity = citySelect.value;

    currentCity = selectedCity;
    resetStoreSelection();
    updateCityGuardsButton();

    const countrySelect = document.getElementById("countrySelect");
    const selectedCountry = countrySelect.value;
    populateStoreOptions(selectedCountry, selectedCity);
}

function populateStoreOptions(countryId, cityId) {
    const storeSelect = document.getElementById("storeSelect");
    let options = '<option value="">-- Elige una tienda --</option>';
    for (const [storeId, storeData] of Object.entries(stores)) {
        const countryOk = !countryId || storeData.country === countryId;
        const cityOk = !cityId || storeData.city === cityId;
        if (countryOk && cityOk) {
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
    const city = cities[store.city];

    document.getElementById("storeName").textContent = store.name;
    document.getElementById("storeAddress").textContent = store.address;
    const countryCity = city ? `${city.name} · ${country.flag} ${country.name}` : `${country.flag} ${country.name}`;
    document.getElementById("countryDisplay").textContent = countryCity;
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

function renderCalendarHTML(storeId, monthSel) {
    const store = stores[storeId] || {};
    const storeName = store.name || storeId;
    const records = (horarios[storeId] || []).filter(r =>
        !monthSel || String(r.month) === monthSel
    );

    if (records.length === 0) {
        return `
            <div class="empty-box">
                <div style="font-size: 36px; margin-bottom: 8px;">&#x1F4ED;</div>
                <p style="margin: 0; font-size: 15px;">No hay horarios para esta tienda.</p>
            </div>`;
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
    const monthIndex = MONTH_NAMES.indexOf(monthSel);
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
            inner += `
                <div class="cal-event ${turnoColor(sch)}" data-tip-id="${sch.personaId}" data-tip-store="${storeName}">
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

    return `
        <div class="cal-wrapper">
            <div class="cal-month-title">${monthSel} ${yearNum}</div>
            <div class="cal-grid">
                ${buildHeader()}
                ${rows}
            </div>
        </div>`;
}

function renderCalendar() {
    const container = document.getElementById("staffList");
    if (container) container.innerHTML = renderCalendarHTML(currentStore, currentMonth);
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

function guardsCity() {
    const sel = document.getElementById("guardsCitySelect");
    return sel ? sel.value : "";
}

function guardsCountryChanged() {
    const countrySel = guardsCountry();
    const citySel = document.getElementById("guardsCitySelect");
    if (citySel) {
        const citiesInCountry = new Set();
        for (const t of Object.values(stores)) {
            if (!t.country || !t.city) continue;
            if (countrySel && t.country !== countrySel) continue;
            citiesInCountry.add(t.city);
        }
        citySel.innerHTML = '<option value="">🏙️ Todas las ciudades</option>' +
            [...citiesInCountry].sort().map(cc => {
                const c = cities[cc];
                return `<option value="${cc}">${c ? c.name : cc}</option>`;
            }).join("");
    }
    selectGuardsFilters();
}

function updateGuardsCountryOptions() {
    const monthVal = guardsMonth() || currentMonth || MONTH_NAMES[new Date().getMonth()];
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
}

function closeGuards() {
    guardsMode = false;
    const panel = document.getElementById("allGuardsPanel");
    if (panel) panel.classList.add("hidden");
    document.querySelector(".filter-bar").classList.remove("hidden");
    if (currentStore) {
        renderStore();
    } else {
        document.getElementById("storeInfo").classList.add("hidden");
        document.getElementById("staffSection").classList.add("hidden");
        document.getElementById("emptyState").classList.remove("hidden");
    }
}

function selectGuardsFilters() {
    const list = document.getElementById("allGuardsList");
    if (list) list.innerHTML = "";
    renderAllGuards();
}

function showCityGuards() {
    if (!currentCity) return;
    guardsMode = true;
    const panel = document.getElementById("allGuardsPanel");
    if (!panel) return;

    document.querySelector(".filter-bar").classList.add("hidden");
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
    updateGuardsCountryOptions();

    const citySel = document.getElementById("guardsCitySelect");
    if (citySel) {
        const citiesInMonth = new Set();
        for (const [tid, recs] of Object.entries(horarios)) {
            recs.forEach(r => {
                if (r.type !== "guardia") return;
                if (monthVal && String(r.month) !== monthVal) return;
                const t = stores[tid];
                if (t && t.city) citiesInMonth.add(t.city);
            });
        }
        citySel.innerHTML = '<option value="">🏙️ Todas las ciudades</option>' +
            [...citiesInMonth].sort().map(cc => {
                const c = cities[cc];
                return `<option value="${cc}">${c ? c.name : cc}</option>`;
            }).join("");
        citySel.value = currentCity;
    }

    // Ajustar el título del panel
    const headTitle = panel.querySelector("h3");
    if (headTitle && cities[currentCity]) {
        headTitle.textContent = `🧾 Guardias en ${cities[currentCity].name}`;
    }

    panel.classList.remove("hidden");
    renderAllGuards();
}

// Lista de guardias de todos los técnicos (con los datos de cada uno)
function buildGuardCards(guardias, personaById, monthSel) {
    if (!guardias || guardias.length === 0) return "";

    const dayOrder = { "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3, "Viernes": 4, "Sábado": 5, "Domingo": 6 };
    const monthIndex = MONTH_NAMES.indexOf(monthSel);
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
        const city = cities[t.city] || {};
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
                    ${city.name ? `<span class="guard-badge guard-city">🏙️ ${city.name}</span>` : ""}
                    ${c.flag ? `<span class="guard-badge guard-country">${c.flag} ${c.name}</span>` : ""}
                </div>
            </div>`;
    }

    return semanaSet.map(w => `
        <div class="guard-week">📅 Semana ${w}</div>
        ${guardias.filter(g => g._week === w).map(card).join("")}
    `).join("");
}

function renderAllGuards() {
    const list = document.getElementById("allGuardsList");
    if (!list) return;

    const monthSel = guardsMonth();
    const countrySel = guardsCountry();
    const citySel = guardsCity();
    const personaById = {};
    personas.forEach(p => { personaById[p.id] = p; });

    const guardias = [];
    for (const [tiendaId, recs] of Object.entries(horarios)) {
        recs.forEach(r => {
            if (r.type !== "guardia") return;
            if (monthSel && String(r.month) !== monthSel) return;
            const t = stores[tiendaId] || {};
            if (countrySel && t.country !== countrySel) return;
            if (citySel && t.city !== citySel) return;
            guardias.push({ tiendaId: tiendaId, ...r });
        });
    }

    if (guardias.length === 0) {
        list.innerHTML = '<p class="tech-empty">No hay guardias en este mes/país/ciudad.</p>';
        return;
    }

    list.innerHTML = buildGuardCards(guardias, personaById, monthSel);
}


// ═══════════════════════════════════════════════════════════
//  BLOQUE 6.5: FILTRO LIBRE (VARIOS PAÍSES / CIUDADES)
// ═══════════════════════════════════════════════════════════

let freeMode = false;

function freeMonth() {
    const sel = document.getElementById("freeMonthSelect");
    return sel ? sel.value : (currentMonth || MONTH_NAMES[new Date().getMonth()]);
}

function buildFreeCheckboxes() {
    const box = document.getElementById("freeCheckboxes");
    if (!box) return;

    const countrySet = new Set();
    Object.values(stores).forEach(s => { if (s.country) countrySet.add(s.country); });

    let html = `<div class="free-tools-row">
        <button type="button" class="free-select-btn" onclick="setAllFreeCities(true)">✓ Seleccionar todas</button>
        <button type="button" class="free-select-btn" onclick="setAllFreeCities(false)">✗ Quitar todas</button>
    </div>`;

    for (const cc of [...countrySet].sort()) {
        const c = countries[cc] || {};
        const citySet = new Set();
        Object.values(stores).forEach(s => {
            if (s.country === cc && s.city) citySet.add(s.city);
        });
        html += `<div class="free-country">
                    <label>
                        <input type="checkbox" class="free-country-check" data-cc="${cc}"
                               onchange="toggleFreeCountry('${cc}')">
                        ${c.flag || ""} ${c.name || cc}
                    </label>
                </div>
                <div class="free-country-children">`;
        for (const cityId of [...citySet].sort()) {
            const city = cities[cityId];
            html += `<label class="free-city">
                        <input type="checkbox" class="free-city-check" data-cc="${cc}" data-city="${cityId}"
                               onchange="toggleFreeCity('${cityId}')">
                        🏙️ ${city ? city.name : cityId}
                    </label>`;
        }
        html += `</div>`;
    }

    box.innerHTML = html;
}

function toggleFreeCountry(cc) {
    const countryCheck = document.querySelector(`.free-country-check[data-cc="${cc}"]`);
    const checked = countryCheck ? countryCheck.checked : false;
    document.querySelectorAll(`.free-city-check[data-cc="${cc}"]`).forEach(cb => { cb.checked = checked; });
    renderFreeFilter();
}

function toggleFreeCity(cityId) {
    const cb = document.querySelector(`.free-city-check[data-city="${cityId}"]`);
    if (!cb) return;
    const cc = cb.dataset.cc;
    const cityChecks = [...document.querySelectorAll(`.free-city-check[data-cc="${cc}"]`)];
    const anyChecked = cityChecks.some(x => x.checked);
    const allChecked = cityChecks.every(x => x.checked);
    const countryCheck = document.querySelector(`.free-country-check[data-cc="${cc}"]`);
    if (countryCheck) {
        countryCheck.checked = allChecked;
        countryCheck.indeterminate = anyChecked && !allChecked;
    }
    renderFreeFilter();
}

function setAllFreeCities(on) {
    document.querySelectorAll(".free-city-check").forEach(cb => { cb.checked = on; });
    document.querySelectorAll(".free-country-check").forEach(cb => {
        cb.checked = on;
        cb.indeterminate = false;
    });
    renderFreeFilter();
}

function selectedFreeCities() {
    return [...document.querySelectorAll(".free-city-check:checked")].map(cb => cb.dataset.city);
}

function toggleFreeFilter() {
    freeMode = !freeMode;
    const btn = document.getElementById("btnFreeFilter");
    const panel = document.getElementById("freeFilterPanel");
    if (!panel) return;

    if (btn) btn.textContent = freeMode ? "✖ Salir del filtro libre" : "🎛️ Filtro libre";

    if (!freeMode) {
        closeFreeFilter();
        return;
    }

    // Entrando: ocultar el esquema principal
    document.querySelector(".filter-bar").classList.add("hidden");
    document.getElementById("allGuardsPanel").classList.add("hidden");
    document.getElementById("storeInfo").classList.add("hidden");
    document.getElementById("staffSection").classList.add("hidden");
    document.getElementById("emptyState").classList.add("hidden");

    const ms = document.getElementById("freeMonthSelect");
    if (ms) {
        ms.innerHTML = '<option value="">-- Mes --</option>' +
            MONTH_NAMES.map(m => `<option value="${m}">${m}</option>`).join("");
        ms.value = currentMonth || MONTH_NAMES[new Date().getMonth()];
    }

    buildFreeCheckboxes();
    setAllFreeCities(true);
    panel.classList.remove("hidden");
    renderFreeFilter();
}

function closeFreeFilter() {
    freeMode = false;
    const btn = document.getElementById("btnFreeFilter");
    if (btn) btn.textContent = "🎛️ Filtro libre";
    const panel = document.getElementById("freeFilterPanel");
    if (panel) panel.classList.add("hidden");

    document.querySelector(".filter-bar").classList.remove("hidden");
    if (currentStore) {
        renderStore();
    } else {
        document.getElementById("storeInfo").classList.add("hidden");
        document.getElementById("staffSection").classList.add("hidden");
        document.getElementById("emptyState").classList.remove("hidden");
    }
}

function renderFreeFilter() {
    const res = document.getElementById("freeResults");
    if (!res) return;

    const monthSel = freeMonth();
    const citiesSel = selectedFreeCities();
    const personaById = {};
    personas.forEach(p => { personaById[p.id] = p; });

    if (citiesSel.length === 0) {
        res.innerHTML = '<p class="tech-empty">Selecciona al menos un país o ciudad.</p>';
        return;
    }

    // Agrupar ciudades por país
    const byCountry = {};
    for (const cityId of citiesSel) {
        const city = cities[cityId];
        if (!city) continue;
        (byCountry[city.country] = byCountry[city.country] || []).push(cityId);
    }

    let html = "";
    for (const cc of Object.keys(byCountry).sort()) {
        const c = countries[cc] || {};
        html += `<div class="free-results-section">
            <h4 class="free-results-country">${c.flag || ""} ${c.name || cc}</h4>`;

        for (const cityId of byCountry[cc].sort()) {
            const city = cities[cityId] || {};
            const cityStores = Object.entries(stores).filter(([, s]) =>
                s.country === cc && s.city === cityId
            );
            html += `<div class="free-results-city">🏙️ ${city.name || cityId}</div>`;

            // Guardias de la ciudad
            const guardias = [];
            for (const [tid, recs] of Object.entries(horarios)) {
                if (!cityStores.some(([sid]) => sid === tid)) continue;
                recs.forEach(r => {
                    if (r.type !== "guardia") return;
                    if (monthSel && String(r.month) !== monthSel) return;
                    guardias.push({ tiendaId: tid, ...r });
                });
            }
            html += `<div class="free-subtitle">🛡️ Guardias</div>`;
            if (guardias.length === 0) {
                html += '<p class="tech-empty">Sin guardias en este mes.</p>';
            } else {
                html += buildGuardCards(guardias, personaById, monthSel);
            }

            // Calendarios de cada tienda de la ciudad
            html += `<div class="free-subtitle">📅 Calendarios</div>`;
            let anyCal = false;
            for (const [tid, storeData] of cityStores) {
                const hasRecords = (horarios[tid] || []).some(r =>
                    !monthSel || String(r.month) === monthSel
                );
                if (!hasRecords) continue;
                anyCal = true;
                html += `<div class="free-results-store">🏪 ${storeData.name}</div>`;
                html += renderCalendarHTML(tid, monthSel);
            }
            if (!anyCal) {
                html += '<p class="tech-empty">Sin horarios para este mes.</p>';
            }
        }
        html += `</div>`;
    }

    res.innerHTML = html;
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
