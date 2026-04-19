const UPDATE_INTERVAL = 10 * 60 * 1000;

let dayOffset = 1;

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

const BAR_THRESHOLDS = [
    { max: 30, varName: '--bar-low',    label: '< 30'    },
    { max: 50, varName: '--bar-medium', label: '30 – 49' },
    { max: 80, varName: '--bar-high',   label: '50 – 79' },
    { max: Infinity, varName: '--bar-full', label: '≥ 80' },
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
    chart.options.scales.x.ticks.color = axisColor;
    chart.options.scales.y.ticks.color = axisColor;
    chart.options.scales.x.title.color = axisColor;
    chart.options.scales.y.title.color = axisColor;
    chart.options.scales.x.grid.color  = gridColor;
    chart.options.scales.y.grid.color  = gridColor;
    chart.update('none');
}

function barColorFn() {
    return (context) => {
        if (!context.parsed || context.parsed.y == null) return 'transparent';

        const value = context.parsed.y;
        const threshold = BAR_THRESHOLDS.find(t => value < t.max);
        return getCssVar(threshold.varName);
    };
}

document.getElementById('btn-theme').addEventListener('click', () => {
    applyTheme(getTheme() === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK);
});

// --- Legend ---

function renderLegend() {
    document.getElementById('chart-legend').innerHTML = BAR_THRESHOLDS.map(t => {
        const color = getCssVar(t.varName);
        return `<span style="display:inline-flex;align-items:center;gap:5px;font-size:13px;color:var(--text);">
            <span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:${color};flex-shrink:0;"></span>
            ${t.label}
        </span>`;
    }).join('');
}

// --- Day navigation ---

function getDateForOffset(offset) {
    const d = new Date();
    d.setDate(d.getDate() + offset);
    return d;
}

function isDailyRolloutSelected() {
    return dayOffset === 1;
}

function toLocalISODate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function updateDateLabel() {
    const d = getDateForOffset(dayOffset);
    document.getElementById('date-label').textContent = isDailyRolloutSelected()
        ? 'Denní Přehled'
        : d.toLocaleDateString('cs-CZ', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    document.getElementById('btn-next').disabled = isDailyRolloutSelected();
}

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
    document.getElementById('no-data-msg').style.display = visible ? 'flex' : 'none';
    document.getElementById('chart').style.visibility   = visible ? 'hidden' : 'visible';
}

async function loadData() {
    try {
        const date  = getDateForOffset(dayOffset);
        const start = toLocalISODate(date) + 'T00:00:00';
        const end   = toLocalISODate(date) + 'T23:59:59';

        const url = isDailyRolloutSelected()
            ? '/rollout/kravi_hora'
            : `/data/kravi_hora?start=${start}&end=${end}`;

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
            ...(isDailyRolloutSelected() && { weekday: 'short' }),
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

// --- Navigation ---

document.getElementById('btn-prev').addEventListener('click', () => {
    dayOffset--;
    updateDateLabel();
    loadData();
});

document.getElementById('btn-next').addEventListener('click', () => {
    if (dayOffset >= 1) return;
    dayOffset++;
    updateDateLabel();
    loadData();
});

// --- Version ---

async function loadVersion() {
    try {
        const res  = await fetch('/version');
        const data = await res.json();
        document.getElementById('version').textContent = `v${data.version}`;
    } catch(error) {
        console.error('Chyba při načítání verze:', error);
    }
}

// --- Init ---

const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || THEMES.DARK;
applyTheme(savedTheme);
updateDateLabel();
loadData();
loadVersion();

setInterval(() => {
    if (dayOffset >= 0) loadData();
}, UPDATE_INTERVAL);