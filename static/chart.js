const UPDATE_INTERVAL = 10 * 60 * 1000;

const URL_PARAM_POOL = 'pool';
const URL_PARAM_DAY  = 'day';

const ROLLOUT_DATE = null;

// --- State ---

let selectedPoolId   = null;
let selectedDate     = ROLLOUT_DATE; // Date | null; null = rollout view
let currentThresholds = [];

// --- Theme ---

const THEMES = {
    DARK:  'dark',
    LIGHT: 'light',
};

const THEME_ICONS = {
    [THEMES.DARK]:  '☀️',
    [THEMES.LIGHT]: '🌙',
};

const THEME_STORAGE_KEY = 'theme';

const BAR_COLORS = [
    { varName: '--bar-low'    },
    { varName: '--bar-medium' },
    { varName: '--bar-high'   },
    { varName: '--bar-full'   },
];

function getCssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function getTheme() {
    return document.documentElement.getAttribute('data-theme') || THEMES.DARK;
}

function getAxisColor() {
    return getCssVar('--text');
}

function getGridColor() {
    return getCssVar('--border');
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
    document.getElementById('btn-theme').textContent = THEME_ICONS[theme];
    renderLegend();
    updateChartTheme();
}

function updateChartTheme() {
    const chart = Chart.getChart(document.getElementById('chart'));
    if (!chart) return;

    const axisColor = getAxisColor();
    const gridColor = getGridColor();

    chart.data.datasets[0].backgroundColor = barColorFn();
    chart.options.scales.x.ticks.color     = axisColor;
    chart.options.scales.y.ticks.color     = axisColor;
    chart.options.scales.x.title.color     = axisColor;
    chart.options.scales.y.title.color     = axisColor;
    chart.options.scales.x.grid.color      = gridColor;
    chart.options.scales.y.grid.color      = gridColor;
    chart.update('none');
}

function barColorFn() {
    return (context) => {
        if (!context.parsed || context.parsed.y == null) return 'transparent';

        const value = context.parsed.y;
        const index = currentThresholds.findIndex(t => value < t);
        const colorIndex = index === -1 ? BAR_COLORS.length - 1 : index;
        return getCssVar(BAR_COLORS[colorIndex].varName);
    };
}

document.getElementById('btn-theme').addEventListener('click', () => {
    applyTheme(getTheme() === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
});

// --- Legend ---

function renderLegend() {
    if (currentThresholds.length === 0) return;

    const [t1, t2, t3] = currentThresholds;
    const labels = [`< ${t1}`, `${t1} – ${t2 - 1}`, `${t2} – ${t3 - 1}`, `≥ ${t3}`];

    document.getElementById('chart-legend').innerHTML = BAR_COLORS.map((bar, i) => {
        const color = getCssVar(bar.varName);
        return `<span style="display:inline-flex;align-items:center;gap:5px;font-size:13px;color:var(--text);">
            <span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${color};flex-shrink:0;"></span>
            ${labels[i]}
        </span>`;
    }).join('');
}

// --- Pool selection ---

async function loadPools() {
    const res   = await fetch('/pools');
    const pools = await res.json();

    const select = document.getElementById('pool-select');
    select.innerHTML = pools.map(p =>
        `<option value="${p.id}">${p.name}</option>`
    ).join('');

    const urlPool = new URLSearchParams(location.search).get(URL_PARAM_POOL);
    const initialPool = pools.find(p => p.id === urlPool) ?? pools[0];

    applyPoolSelection(initialPool);
}

function applyPoolSelection(pool) {
    selectedPoolId    = pool.id;
    currentThresholds = pool.thresholds;

    document.getElementById('pool-select').value = pool.id;
    renderLegend();
}

document.getElementById('pool-select').addEventListener('change', async (e) => {
    const res   = await fetch('/pools');
    const pools = await res.json();
    const pool  = pools.find(p => p.id === e.target.value);
    if (!pool) return;

    applyPoolSelection(pool);
    pushUrlState();
    loadData();
});

// --- Day navigation ---

function isRolloutActive() {
    return selectedDate === ROLLOUT_DATE;
}

function toLocalISODate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function updateDateLabel() {
    const rollout = isRolloutActive();
    document.getElementById('date-label').textContent = rollout
        ? 'Denní Přehled'
        : selectedDate.toLocaleDateString('cs-CZ', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

    document.getElementById('btn-next').disabled = rollout;
    document.getElementById('btn-rollout').style.display = rollout ? 'none' : '';
}

function shiftDate(days) {
    const base = isRolloutActive() ? new Date() : new Date(selectedDate);
    base.setDate(base.getDate() + days);

    // Clamp to today – navigating forward past today switches to rollout
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    base.setHours(0, 0, 0, 0);

    selectedDate = base >= today ? ROLLOUT_DATE : base;
}

document.getElementById('btn-prev').addEventListener('click', () => {
    shiftDate(-1);
    updateDateLabel();
    pushUrlState();
    loadData();
});

document.getElementById('btn-next').addEventListener('click', () => {
    if (isRolloutActive()) return;
    shiftDate(1);
    updateDateLabel();
    pushUrlState();
    loadData();
});

document.getElementById('btn-rollout').addEventListener('click', () => {
    selectedDate = ROLLOUT_DATE;
    updateDateLabel();
    pushUrlState();
    loadData();
});

// --- URL state ---

function pushUrlState() {
    const params = new URLSearchParams();
    if (selectedPoolId) params.set(URL_PARAM_POOL, selectedPoolId);
    if (!isRolloutActive()) params.set(URL_PARAM_DAY, toLocalISODate(selectedDate));

    const newUrl = `${location.pathname}?${params.toString()}`;
    history.pushState({ poolId: selectedPoolId, day: isRolloutActive() ? null : toLocalISODate(selectedDate) }, '', newUrl);
}

function readUrlState() {
    const params = new URLSearchParams(location.search);
    const dayParam = params.get(URL_PARAM_DAY);

    if (dayParam) {
        const parsed = new Date(dayParam);
        selectedDate = isNaN(parsed.getTime()) ? ROLLOUT_DATE : parsed;
    } else {
        selectedDate = ROLLOUT_DATE;
    }
}

window.addEventListener('popstate', () => {
    readUrlState();
    updateDateLabel();
    loadData();
});

// --- Chart ---

function buildScaleAxis(label) {
    const axisColor = getAxisColor();
    const gridColor = getGridColor();
    return {
        ticks: { color: axisColor },
        title: { display: true, text: label, color: axisColor },
        grid:  { color: gridColor },
    };
}

function setNoData(visible) {
    document.getElementById('no-data-msg').style.visibility = visible ? 'visible' : 'hidden';
    document.getElementById('chart').style.visibility       = visible ? 'hidden' : 'visible';
}

async function loadData() {
    if (!selectedPoolId) return;

    try {
        let url;
        if (isRolloutActive()) {
            url = `/rollout/${selectedPoolId}`;
        } else {
            const dateStr = toLocalISODate(selectedDate);
            url = `/data/${selectedPoolId}?start=${dateStr}T00:00:00&end=${dateStr}T23:59:59`;
        }

        const res  = await fetch(url);
        const data = await res.json();

        const ctx           = document.getElementById('chart');
        const existingChart = Chart.getChart(ctx);

        if (data.length === 0) {
            setNoData(true);
            if (existingChart) {
                existingChart.data.labels = [];
                existingChart.data.datasets[0].data = [];
                existingChart.update('none');
            }
            updateStatus();
            return;
        }

        setNoData(false);

        const timeOptions = {
            hour:   '2-digit',
            minute: '2-digit',
            ...(isRolloutActive() && { weekday: 'short' }),
        };
        const labels = data.map(d => new Date(d.time * 1000).toLocaleTimeString('cs-CZ', timeOptions));
        const values = data.map(d => d.val);

        if (existingChart) {
            existingChart.data.labels = labels;
            existingChart.data.datasets[0].data = values;
            existingChart.update('none');
        } else {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        data: values,
                        backgroundColor: barColorFn(),
                        fill: true,
                        tension: 0.4,
                    }],
                },
                options: {
                    plugins:  { legend: { display: false } },
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true, ...buildScaleAxis('Obsazenost') },
                        x: { ...buildScaleAxis('Čas') },
                    },
                    animation: false,
                },
            });
        }

        updateStatus();
    } catch (error) {
        console.error('Chyba při načítání dat:', error);
    }
}

function updateStatus() {
    document.getElementById('timestamp').textContent = new Date().toLocaleTimeString('cs-CZ');
}

// --- Version ---

async function loadVersion() {
    try {
        const res  = await fetch('/version');
        const data = await res.json();
        document.getElementById('version').textContent = `v${data.version}`;
    } catch (error) {
        console.error('Chyba při načítání verze:', error);
    }
}

// --- Init ---

const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || THEMES.DARK;
applyTheme(savedTheme);
readUrlState();
updateDateLabel();
loadPools().then(() => loadData());
loadVersion();

setInterval(() => {
    if (isRolloutActive()) loadData();
}, UPDATE_INTERVAL);