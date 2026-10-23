// Chart.js utility helpers for USTA Dashboard
const ChartManager = {
    instances: {},

    colors: {
        navy: "#0B2545",
        navyLight: "#133E87",
        gold: "#FDB813",
        blue: "#2563EB",
        lightBlue: "#60A5FA",
        teal: "#0D9488",
        green: "#10B981",
        amber: "#F59E0B",
        red: "#EF4444",
        purple: "#8B5CF6",
        slate: "#64748B",
        palette: [
            "#0B2545", "#2563EB", "#0D9488", "#FDB813", "#F59E0B",
            "#10B981", "#8B5CF6", "#EC4899", "#6366F1", "#14B8A6"
        ]
    },

    destroy(canvasId) {
        if (this.instances[canvasId]) {
            this.instances[canvasId].destroy();
            delete this.instances[canvasId];
        }
    },

    renderDoughnut(canvasId, labels, data, customColors = null) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const bgColors = customColors || [this.colors.blue, "#CBD5E1", this.colors.gold];

        this.instances[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: bgColors,
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 12,
                            font: { size: 11, family: 'Segoe UI' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${val} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    },

    renderBar(canvasId, labels, data, labelName = "Estudiantes", color = null, horizontal = false) {
        this.destroy(canvasId);
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        const barColor = color || this.colors.navy;

        this.instances[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: labelName,
                    data: data,
                    backgroundColor: barColor,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: horizontal ? 'y' : 'x',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${labelName}: ${ctx.raw}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: horizontal, color: '#F1F5F9' },
                        ticks: { font: { size: 10 } }
                    },
                    y: {
                        grid: { display: !horizontal, color: '#F1F5F9' },
                        ticks: { font: { size: 10 }, precision: 0 }
                    }
                }
            }
        });
    }
};
