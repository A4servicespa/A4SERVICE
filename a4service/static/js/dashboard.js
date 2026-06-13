document.addEventListener("DOMContentLoaded", () => {

    const raw = document.getElementById("dashboard-data").textContent;
    const data = JSON.parse(raw);

    const { labels, stockData, entradas, salidas } = data;

    const ctxMov = document.getElementById('movChart');
    if (ctxMov) {
        new Chart(ctxMov, {
            type: 'pie',
            data: {
                labels: ['Entradas', 'Salidas'],
                datasets: [{
                    data: [entradas, salidas],
                    backgroundColor: ['#16a34a', '#dc2626']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }
});
