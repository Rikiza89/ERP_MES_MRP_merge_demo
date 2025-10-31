"""
Dashboard App Views
KPI calculations and analytics endpoints
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from erp.models import Product, SalesOrder, PurchaseOrder, Invoice
from mes.models import WorkOrder, ProductionLog, QualityCheck, ProductionLine
from mrp.models import Inventory, StockMovement, Material


@staff_member_required
def dashboard_index(request):
    """Main dashboard view"""
    context = {
        'kpis': get_kpis(),
        'production_data': get_production_data(),
        'inventory_alerts': get_inventory_alerts(),
        'recent_activities': get_recent_activities(),
    }
    return render(request, 'dashboard/index.html', context)


def get_kpis():
    """Calculate key performance indicators"""
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Production KPIs
    wo_this_month = WorkOrder.objects.filter(planned_start__gte=month_start)
    completed_wo = wo_this_month.filter(status='completed')
    
    total_produced = completed_wo.aggregate(total=Sum('produced_quantity'))['total'] or 0
    total_rejected = completed_wo.aggregate(total=Sum('rejected_quantity'))['total'] or 0
    
    # OEE calculation (simplified)
    oee = 0
    if completed_wo.exists():
        efficiency_avg = 0
        count = 0
        for wo in completed_wo:
            if wo.efficiency:
                efficiency_avg += wo.efficiency
                count += 1
        oee = (efficiency_avg / count) if count > 0 else 0
    
    # Financial KPIs
    invoices_this_month = Invoice.objects.filter(invoice_date__gte=month_start, invoice_type='sales')
    revenue = invoices_this_month.aggregate(total=Sum('total'))['total'] or 0
    
    # Inventory value
    inventory_value = 0
    for inv in Inventory.objects.all():
        if inv.product:
            inventory_value += inv.quantity_on_hand * inv.product.cost
        elif inv.material:
            inventory_value += inv.quantity_on_hand * inv.material.unit_cost
    
    # Low stock items
    low_stock_count = Inventory.objects.filter(
        Q(product__isnull=False, quantity_available__lt=F('product__min_stock')) |
        Q(material__isnull=False, quantity_available__lt=0)
    ).count()
    
    return {
        'oee': round(oee, 1),
        'total_produced': int(total_produced),
        'total_rejected': int(total_rejected),
        'rejection_rate': round((total_rejected / total_produced * 100) if total_produced > 0 else 0, 2),
        'revenue': float(revenue),
        'inventory_value': float(inventory_value),
        'active_work_orders': WorkOrder.objects.filter(status='in_progress').count(),
        'pending_work_orders': WorkOrder.objects.filter(status__in=['pending', 'ready']).count(),
        'low_stock_items': low_stock_count,
    }


def get_production_data():
    """Get production performance data for charts"""
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    
    # Daily production
    daily_production = []
    for i in range(7):
        date = last_7_days + timedelta(days=i)
        produced = WorkOrder.objects.filter(
            actual_start__date=date,
            status='completed'
        ).aggregate(total=Sum('produced_quantity'))['total'] or 0
        
        daily_production.append({
            'date': date.strftime('%m/%d'),
            'quantity': int(produced)
        })
    
    # Production by line
    line_production = []
    for line in ProductionLine.objects.filter(active=True):
        produced = WorkOrder.objects.filter(
            production_line=line,
            actual_start__gte=last_7_days,
            status='completed'
        ).aggregate(total=Sum('produced_quantity'))['total'] or 0
        
        line_production.append({
            'line': line.line_code,
            'quantity': int(produced)
        })
    
    return {
        'daily': daily_production,
        'by_line': line_production
    }


def get_inventory_alerts():
    """Get low stock and critical inventory items"""
    alerts = []
    
    # Low stock products
    low_stock = Inventory.objects.filter(
        product__isnull=False,
        quantity_available__lt=F('product__min_stock')
    ).select_related('product')[:10]
    
    for inv in low_stock:
        alerts.append({
            'type': 'low_stock',
            'item': inv.product.name,
            'current': float(inv.quantity_available),
            'minimum': float(inv.product.min_stock),
            'severity': 'high' if inv.quantity_available <= 0 else 'medium'
        })
    
    # Low stock materials
    low_materials = Inventory.objects.filter(
        material__isnull=False,
        quantity_available__lt=10
    ).select_related('material')[:10]
    
    for inv in low_materials:
        alerts.append({
            'type': 'low_material',
            'item': inv.material.name,
            'current': float(inv.quantity_available),
            'severity': 'high' if inv.quantity_available <= 0 else 'medium'
        })
    
    return alerts


def get_recent_activities():
    """Get recent system activities"""
    from core.models import LogData
    
    recent_logs = LogData.objects.select_related('user', 'employee').order_by('-timestamp')[:20]
    
    activities = []
    for log in recent_logs:
        activities.append({
            'timestamp': log.timestamp,
            'user': log.user.username if log.user else 'System',
            'action': log.get_action_type_display(),
            'description': log.description
        })
    
    return activities


@staff_member_required
def api_production_chart(request):
    """API endpoint for production chart data"""
    data = get_production_data()
    return JsonResponse(data)


@staff_member_required
def api_inventory_status(request):
    """API endpoint for inventory status"""
    alerts = get_inventory_alerts()
    return JsonResponse({'alerts': alerts})


@staff_member_required
def api_kpis(request):
    """API endpoint for KPI data"""
    kpis = get_kpis()
    return JsonResponse(kpis)