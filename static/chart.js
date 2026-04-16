const UPDATE_INTERVAL = 10 * 60 * 1000;

let dayOffset = 0;

// --- Theme ---

function getTheme() {
    return document.documentElement.getAttribute('data-theme') || 'dark';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    document.getElementById('btn-theme').textContent = theme === 'dark' ? '☀️' : '🌙';
    updateChartTheme();
}

function updateChartTheme() {
    const chart = Chart.getChart(document.getElementById('chart'));
    if (!chart) return;

    const theme = getTheme();
    const axisColor = theme === 'dark' ? '#ccc' : '#333';

    chart.data.datasets[0].backgroundColor = barColorFn();
    chart.options.scales.x.ticks = { color: axisColor };
    chart.options.scales.y.ticks = { color: axisColor };
    chart.options.scales.x.title.color = axisColor;
    chart.options.scales.y.title.color = axisColor;
    chart.options.scales.x.grid = { color: theme === 'dark' ? '#333' : '#ddd' };
    chart.options.scales.y.grid = { color: theme === 'dark' ? '#333' : '#ddd' };
    chart.update('none');
}

function barColorFn() {
    // Returns a function that reads CSS variables at render time
    return (context) => {
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

// Apply saved preference on load (before chart renders)
const savedTheme = localStorage.getItem('theme') || 'dark';
applyTheme(savedTheme);

// --- Day navigation ---

function getDateForOffset(offset) {
    const d = new Date();
    d.setDate(d.getDate() + offset);
    return d;
}

function toLocalISODate(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function updateDateLabel() {
    const d = getDateForOffset(dayOffset);
    document.getElementById('date-label').textContent = d.toLocaleDateString('cs-CZ', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });
    document.getElementById('btn-next').disabled = dayOffset === 0;
}

// --- Chart ---

async function loadData() {
    try {
        const date = getDateForOffset(dayOffset);
        const start = toLocalISODate(date) + 'T00:00:00';
        const end   = toLocalISODate(date) + 'T23:59:59';

        const url = dayOffset === 0
            ? '/data?limit=100'
            : `/data?start=${start}&end=${end}`;

        const res = await fetch(url);
        const data = await res.json();

        const labels = data.map(d =>
            new Date(d.timestamp * 1000)
                .toLocaleTimeString('cs-CZ', { weekday: 'short', hour: '2-digit', minute: '2-digit' })
        );
        const values = data.map(d => d.value);

        const ctx = document.getElementById('chart');
        const existingChart = Chart.getChart(ctx);
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
                        label: 'Obsazenost',
                        data: values,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: barColorFn(),
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
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

document.getElementById('btn-prev').addEventListener('click', () => {
    dayOffset--;
    updateDateLabel();
    loadData();
});

document.getElementById('btn-next').addEventListener('click', () => {
    if (dayOffset >= 0) return;
    dayOffset++;
    updateDateLabel();
    loadData();
});

updateDateLabel();
loadData();

setInterval(() => {
    if (dayOffset === 0) loadData();
}, UPDATE_INTERVAL);