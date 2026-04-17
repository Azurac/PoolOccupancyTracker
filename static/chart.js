const UPDATE_INTERVAL = 10 * 60 * 1000;

let dayOffset = 1;

// --- Theme ---

function getTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    document.getElementById('btn-theme').textContent = theme === 'dark' ? '☀️' : '🌙';
    renderLegend();
    updateChartTheme();
}

function updateChartTheme() {
    const chart = Chart.getChart(document.getElementById('chart'));
    if (!chart) return;

    const theme = getTheme();
    const axisColor = theme === 'dark' ? '#ccc' : '#333';
    const gridColor = theme === 'dark' ? '#333' : '#ddd';

    chart.data.datasets[0].backgroundColor = barColorFn();
    chart.options.scales.x.ticks = { color: axisColor };
    chart.options.scales.y.ticks = { color: axisColor };
    chart.options.scales.x.title.color = axisColor;
    chart.options.scales.y.title.color = axisColor;
    chart.options.scales.x.grid = { color: gridColor };
    chart.options.scales.y.grid = { color: gridColor };
    chart.update('none');
}

function barColorFn() {
    return (context) => {
        // Guard: no data point during empty update
        if (!context.parsed || context.parsed.y == null) return 'transparent';

        const value = context.parsed.y;
        const style = getComputedStyle(document.documentElement);
        if (value < 30) return style.getPropertyValue('--bar-low').trim();
        if (value < 50) return style.getPropertyValue('--bar-medium').trim();
        if (value < 80) return style.getPropertyValue('--bar-high').trim();
        return style.getPropertyValue('--bar-full').trim();
    };
}

document.getElementById('btn-theme').addEventListener('click', () => {
    applyTheme(getTheme() === 'dark' ? 'light' : 'dark');
});

// --- Legend ---

function renderLegend() {
    const thresholds = [
        { label: '< 30',   varName: '--bar-low' },
        { label: '30 – 49', varName: '--bar-medium' },
        { label: '50 – 79', varName: '--bar-high' },
        { label: '≥ 80',   varName: '--bar-full' },
    ];

    const style = getComputedStyle(document.documentElement);
    document.getElementById('chart-legend').innerHTML = thresholds.map(t => {
        const color = style.getPropertyValue(t.varName).trim();
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
    return dayOffset === 1
}

function toLocalISODate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function updateDateLabel() {
    const d = getDateForOffset(dayOffset);
    document.getElementById('date-label').textContent = isDailyRolloutSelected() ? "Daily Rollout" : d.toLocaleDateString('cs-CZ', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
    document.getElementById('btn-next').disabled = isDailyRolloutSelected();
}

// --- Chart ---

function setNoData(visible) {
    document.getElementById('no-data-msg').style.display = visible ? 'flex' : 'none';
    document.getElementById('chart').style.visibility = visible ? 'hidden' : 'visible';
}

async function loadData() {
    try {
        const date = getDateForOffset(dayOffset);
        const start = toLocalISODate(date) + 'T00:00:00';
        const end   = toLocalISODate(date) + 'T23:59:59';

        const url = isDailyRolloutSelected()
            ? '/rollout'
            : `/data?start=${start}&end=${end}`;

        const res = await fetch(url);
        const data = await res.json();

        const ctx = document.getElementById('chart');
        const existingChart = Chart.getChart(ctx);

        if (data.length === 0) {
            setNoData(true);
            // Clear chart data without triggering barColorFn on empty rows
            if (existingChart) {
                existingChart.data.labels = [];
                existingChart.data.datasets[0].data = [];
                existingChart.update('none');
            }
            updateStatus();
            return;
        }

        setNoData(false);

        const options = {
            hour: '2-digit',
            minute: '2-digit',
            ...(isDailyRolloutSelected() && { weekday: 'short' })
        };
        const labels = data.map(d =>
            new Date(d.time * 1000)
                .toLocaleTimeString('cs-CZ', options)
        );
        const values = data.map(d => d.val);

        const theme = getTheme();
        const axisColor = theme === 'dark' ? '#ccc' : '#333';
        const gridColor = theme === 'dark' ? '#333' : '#ddd';

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
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: barColorFn(),
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    plugins: {
                        legend: { display: false }
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { color: axisColor },
                            title: { display: true, text: 'Obsazenost', color: axisColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: axisColor },
                            title: { display: true, text: 'Čas', color: axisColor },
                            grid: { color: gridColor }
                        }
                    },
                    animation: false
                }
            });
        }

        updateStatus();
    } catch (error) {
        console.error('Chyba při načítání dat:', error);
    }
}

function updateStatus() {
    document.getElementById('timestamp').textContent =
        new Date().toLocaleTimeString('cs-CZ');
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

// --- Init ---

const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);
updateDateLabel();
loadData();

setInterval(() => {
    if (dayOffset >= 0) loadData();
}, UPDATE_INTERVAL);