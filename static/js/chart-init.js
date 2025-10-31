// Chart.js Dashboard Initialization

document.addEventListener('DOMContentLoaded', function() {
    // Load KPI data
    loadKPIs();
    
    // Load charts
    loadProductionChart();
    loadLineChart();
    
    // Load inventory alerts
    loadInventoryAlerts();
    
    // Load recent activities (from LogData)
    loadRecentActivities();
    
    // Refresh every 30 seconds
    setInterval(() => {
        loadKPIs();
        loadInventoryAlerts();
    }, 30000);
});

function loadKPIs() {
    fetch('/dashboard/api/kpis/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('kpi-oee').textContent = data.oee + '%';
            document.getElementById('kpi-produced').textContent = data.total_produced.toLocaleString();
            document.getElementById('kpi-rejection').textContent = data.rejection_rate + '%';
            document.getElementById('kpi-revenue').textContent = '$' + data.revenue.toLocaleString(undefined, {minimumFractionDigits: 2});
            document.getElementById('kpi-lowstock').textContent = data.low_stock_items;
            document.getElementById('kpi-active-wo').textContent = data.active_work_orders;
        })
        .catch(error => console.error('Error loading KPIs:', error));
}

function loadProductionChart() {
    const ctx = document.getElementById('productionChart');
    if (!ctx) return;
    
    fetch('/dashboard/api/production-chart/')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.daily.map(d => d.date),
                    datasets: [{
                        label: 'Units Produced',
                        data: data.daily.map(d => d.quantity),
                        backgroundColor: 'rgba(76, 175, 80, 0.6)',
                        borderColor: 'rgba(76, 175, 80, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error loading production chart:', error));
}

function loadLineChart() {
    const ctx = document.getElementById('lineChart');
    if (!ctx) return;
    
    fetch('/dashboard/api/production-chart/')
        .then(response => response.json())
        .then(data => {
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.by_line.map(d => d.line),
                    datasets: [{
                        label: 'Production by Line',
                        data: data.by_line.map(d => d.quantity),
                        backgroundColor: [
                            'rgba(76, 175, 80, 0.6)',
                            'rgba(33, 150, 243, 0.6)',
                            'rgba(255, 152, 0, 0.6)',
                            'rgba(156, 39, 176, 0.6)',
                            'rgba(244, 67, 54, 0.6)',
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error loading line chart:', error));
}

function loadInventoryAlerts() {
    fetch('/dashboard/api/inventory-status/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('inventory-alerts');
            if (!container) return;
            
            if (data.alerts.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: green;">✓ All inventory levels OK</p>';
                return;
            }
            
            container.innerHTML = data.alerts.map(alert => `
                <div class="alert-item severity-${alert.severity}">
                    <div class="alert-item-title">${alert.item}</div>
                    <div class="alert-item-detail">
                        Current: ${alert.current} | 
                        ${alert.minimum ? 'Min: ' + alert.minimum : 'Critical'}
                    </div>
                </div>
            `).join('');
        })
        .catch(error => {
            console.error('Error loading inventory alerts:', error);
            document.getElementById('inventory-alerts').innerHTML = 
                '<p style="color: red;">Error loading alerts</p>';
        });
}

function loadRecentActivities() {
    // This would connect to the LogData via an API endpoint
    // For now, we'll show a placeholder
    const container = document.getElementById('recent-activities');
    if (!container) return;
    
    // Simulated activity data - in production, this would fetch from backend
    const activities = [
        { time: '2 min ago', user: 'operator1', action: 'Started', desc: 'Work Order WO-2024-001' },
        { time: '15 min ago', user: 'manager', action: 'Approved', desc: 'Purchase Request PR-2024-123' },
        { time: '1 hour ago', user: 'admin', action: 'Created', desc: 'Sales Order SO-2024-456' },
    ];
    
    container.innerHTML = activities.map(act => `
        <div class="activity-item">
            <div class="activity-time">${act.time}</div>
            <div>
                <span class="activity-user">${act.user}</span>
                <span class="activity-desc">${act.action} ${act.desc}</span>
            </div>
        </div>
    `).join('');
}