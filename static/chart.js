const UPDATE_INTERVAL = 10 * 60 * 1000;

async function loadData() {
    try {
        const res = await fetch('/data?limit=200');
        const data = await res.json();

        const labels = data.map(d => {
            return new Date(d.timestamp * 1000)
                .toLocaleTimeString('cs-CZ', { hour: "2-digit", minute: "2-digit" });
        });
        const values = data.map(d => d.value);

        const ctx = document.getElementById('chart');
        const existingChart = Chart.getChart(ctx);

        if (existingChart) {
            existingChart.data.labels = labels;
            existingChart.data.datasets[0].data = values;
            existingChart.update('none');  // Fast update without animation
        } else {
            new Chart(ctx, {
                type: 'bar',  // bar, horizontalBar, pie, line, doughnut, radar, polarArea
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Obsazenost',
                        data: values,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: (context) => {
                            const value = context.parsed.y;
                            if (value < 30) return 'rgba(75, 192, 192, 0.3)';
                            if (value < 50) return '#4CAF5066';
                            if (value < 80) return '#FF980066';
                            return '#F4433666';
                        },
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
                            title: { display: true, text: 'Obsazenost' }
                        },
                        x: {
                            title: { display: true, text: 'Čas' }
                        }
                    },
                    animation: false  // Disable animation for faster update
                }
            });
        }

        updateStatus();

    } catch (error) {
        console.error('Chyba při načítání dat:', error);
    }
}

loadData();

setInterval(loadData, UPDATE_INTERVAL);

function updateStatus() {
    const now = new Date().toLocaleTimeString('cs-CZ');
    document.getElementById('timestamp').textContent = now;
}