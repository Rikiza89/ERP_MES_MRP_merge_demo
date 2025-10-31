"""
MES App Admin Configuration
Enhanced with action buttons, status indicators, and NFC integration
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import (
    ProductionLine, Shift, Machine, WorkOrder,
    ProductionLog, QualityCheck, Downtime
)
from import_export.admin import ImportExportModelAdmin


@admin.register(ProductionLine)
class ProductionLineAdmin(ImportExportModelAdmin):
    list_display = ['line_code', 'name', 'department', 'capacity', 'active_wo_count', 'active']
    list_filter = ['active', 'department']
    search_fields = ['line_code', 'name']
    autocomplete_fields = ['department']
    
    def active_wo_count(self, obj):
        count = obj.work_orders.filter(status='in_progress').count()
        if count > 0:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', count)
        return count
    active_wo_count.short_description = _('Active WOs')


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['shift_code', 'name', 'start_time', 'end_time', 'active']
    list_filter = ['active']
    search_fields = ['shift_code', 'name']


@admin.register(Machine)
class MachineAdmin(ImportExportModelAdmin):
    list_display = ['machine_code', 'name', 'production_line', 'status_badge', 
                   'last_maintenance', 'next_maintenance', 'active']
    list_filter = ['status', 'active', 'production_line']
    search_fields = ['machine_code', 'name', 'serial_number']
    autocomplete_fields = ['production_line']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Machine Information'), {
            'fields': ('machine_code', 'name', 'production_line', 'status', 'active')
        }),
        (_('Technical Details'), {
            'fields': ('manufacturer', 'model_number', 'serial_number', 'purchase_date')
        }),
        (_('Maintenance'), {
            'fields': ('last_maintenance', 'next_maintenance')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'operational': 'green',
            'maintenance': 'orange',
            'breakdown': 'red',
            'idle': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')


class ProductionLogInline(admin.TabularInline):
    model = ProductionLog
    extra = 0
    can_delete = False
    readonly_fields = ['timestamp', 'operator', 'shift', 'action_type', 
                      'quantity', 'rejects', 'downtime_minutes', 'nfc_uid']
    fields = ['timestamp', 'operator', 'action_type', 'quantity', 'rejects', 'downtime_minutes']


class QualityCheckInline(admin.TabularInline):
    model = QualityCheck
    extra = 0
    readonly_fields = ['check_number', 'check_date', 'inspector', 'result']
    fields = ['check_number', 'inspector', 'sample_size', 'passed', 'failed', 'result']


@admin.register(WorkOrder)
class WorkOrderAdmin(ImportExportModelAdmin):
    list_display = ['wo_number', 'product', 'production_line', 'status_indicator', 
                   'progress_bar', 'priority_badge', 'delay_indicator', 'action_buttons']
    list_filter = ['status', 'priority', 'production_line', 'planned_start']
    search_fields = ['wo_number', 'product__name', 'product__product_number']
    autocomplete_fields = ['sales_order', 'product', 'production_line', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'completion_rate', 'efficiency', 'is_delayed']
    date_hierarchy = 'planned_start'
    inlines = [ProductionLogInline, QualityCheckInline]
    
    fieldsets = (
        (_('Work Order Information'), {
            'fields': ('wo_number', 'sales_order', 'product', 'production_line', 'status', 'priority')
        }),
        (_('Quantities'), {
            'fields': ('planned_quantity', 'produced_quantity', 'rejected_quantity', 'completion_rate')
        }),
        (_('Schedule'), {
            'fields': ('planned_start', 'planned_end', 'actual_start', 'actual_end', 'efficiency', 'is_delayed')
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_list_display_links(self, request, list_display):
        return ['wo_number']
    
    def status_indicator(self, obj):
        colors = {
            'pending': 'gray',
            'ready': 'blue',
            'in_progress': 'green',
            'paused': 'orange',
            'completed': 'darkgreen',
            'cancelled': 'red',
        }
        icons = {
            'pending': '○',
            'ready': '◐',
            'in_progress': '⚙',
            'paused': '⏸',
            'completed': '✓',
            'cancelled': '✗',
        }
        color = colors.get(obj.status, 'gray')
        icon = icons.get(obj.status, '○')
        
        # Add red background if delayed
        bg_style = ''
        if obj.is_delayed and obj.status in ['pending', 'in_progress']:
            bg_style = 'background-color: #ffcccc; '
        
        return format_html(
            '<span style="{}color: {}; font-weight: bold; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            bg_style, color, icon, obj.get_status_display()
        )
    status_indicator.short_description = _('Status')
    
    def progress_bar(self, obj):
        percentage = obj.completion_rate
        color = 'green' if percentage >= 100 else 'orange' if percentage >= 75 else 'blue'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; '
            'padding: 2px 0; font-size: 10px; font-weight: bold;">{}%</div></div>',
            min(percentage, 100), color, percentage
        )
    progress_bar.short_description = _('Progress')
    
    def priority_badge(self, obj):
        color = 'red' if obj.priority <= 3 else 'orange' if obj.priority <= 6 else 'gray'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.priority
        )
    priority_badge.short_description = _('Priority')
    
    def delay_indicator(self, obj):
        if obj.is_delayed:
            return format_html('<span style="color: red; font-weight: bold;">⚠ DELAYED</span>')
        return format_html('<span style="color: green;">✓ On Time</span>')
    delay_indicator.short_description = _('Schedule')
    
    def action_buttons(self, obj):
        buttons = []
        
        if obj.status == 'ready':
            buttons.append(
                f'<a href="/admin/mes/workorder/{obj.id}/start/" '
                f'class="button" style="background-color: green; color: white; '
                f'padding: 3px 10px; border-radius: 3px; text-decoration: none;">▶ Start</a>'
            )
        
        if obj.status == 'in_progress':
            buttons.append(
                f'<a href="/admin/mes/workorder/{obj.id}/pause/" '
                f'class="button" style="background-color: orange; color: white; '
                f'padding: 3px 10px; border-radius: 3px; text-decoration: none;">⏸ Pause</a>'
            )
            buttons.append(
                f'<a href="/admin/mes/workorder/{obj.id}/stop/" '
                f'class="button" style="background-color: darkred; color: white; '
                f'padding: 3px 10px; border-radius: 3px; text-decoration: none;">⏹ Stop</a>'
            )
        
        if obj.status == 'paused':
            buttons.append(
                f'<a href="/admin/mes/workorder/{obj.id}/resume/" '
                f'class="button" style="background-color: blue; color: white; '
                f'padding: 3px 10px; border-radius: 3px; text-decoration: none;">▶ Resume</a>'
            )
        
        return format_html(' '.join(buttons))
    action_buttons.short_description = _('Actions')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/start/', self.admin_site.admin_view(self.start_work_order), name='mes_workorder_start'),
            path('<int:object_id>/stop/', self.admin_site.admin_view(self.stop_work_order), name='mes_workorder_stop'),
            path('<int:object_id>/pause/', self.admin_site.admin_view(self.pause_work_order), name='mes_workorder_pause'),
            path('<int:object_id>/resume/', self.admin_site.admin_view(self.resume_work_order), name='mes_workorder_resume'),
        ]
        return custom_urls + urls
    
    def start_work_order(self, request, object_id):
        work_order = WorkOrder.objects.get(pk=object_id)
        work_order.status = 'in_progress'
        work_order.actual_start = timezone.now()
        work_order.save()
        
        # Create production log
        ProductionLog.objects.create(
            work_order=work_order,
            operator=request.user.profile.employee if hasattr(request.user, 'profile') else None,
            action_type='start',
            timestamp=timezone.now()
        )
        
        messages.success(request, _(f'Work Order {work_order.wo_number} started.'))
        return redirect('admin:mes_workorder_change', object_id)
    
    def stop_work_order(self, request, object_id):
        work_order = WorkOrder.objects.get(pk=object_id)
        work_order.status = 'completed'
        work_order.actual_end = timezone.now()
        work_order.save()
        
        # Create production log
        ProductionLog.objects.create(
            work_order=work_order,
            operator=request.user.profile.employee if hasattr(request.user, 'profile') else None,
            action_type='stop',
            timestamp=timezone.now()
        )
        
        messages.success(request, _(f'Work Order {work_order.wo_number} completed.'))
        return redirect('admin:mes_workorder_change', object_id)
    
    def pause_work_order(self, request, object_id):
        work_order = WorkOrder.objects.get(pk=object_id)
        work_order.status = 'paused'
        work_order.save()
        
        ProductionLog.objects.create(
            work_order=work_order,
            operator=request.user.profile.employee if hasattr(request.user, 'profile') else None,
            action_type='pause',
            timestamp=timezone.now()
        )
        
        messages.warning(request, _(f'Work Order {work_order.wo_number} paused.'))
        return redirect('admin:mes_workorder_change', object_id)
    
    def resume_work_order(self, request, object_id):
        work_order = WorkOrder.objects.get(pk=object_id)
        work_order.status = 'in_progress'
        work_order.save()
        
        ProductionLog.objects.create(
            work_order=work_order,
            operator=request.user.profile.employee if hasattr(request.user, 'profile') else None,
            action_type='resume',
            timestamp=timezone.now()
        )
        
        messages.success(request, _(f'Work Order {work_order.wo_number} resumed.'))
        return redirect('admin:mes_workorder_change', object_id)


@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'work_order', 'operator', 'shift', 'action_type', 
                   'quantity', 'rejects', 'downtime_minutes']
    list_filter = ['action_type', 'shift', 'timestamp']
    search_fields = ['work_order__wo_number', 'operator__employee_id', 'nfc_uid']
    autocomplete_fields = ['work_order', 'operator', 'shift']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False


@admin.register(QualityCheck)
class QualityCheckAdmin(ImportExportModelAdmin):
    list_display = ['check_number', 'work_order', 'inspector', 'check_date', 
                   'result_badge', 'pass_rate_display', 'photo_indicator']
    list_filter = ['result', 'check_date']
    search_fields = ['check_number', 'work_order__wo_number']
    autocomplete_fields = ['work_order', 'inspector']
    readonly_fields = ['created_at', 'pass_rate']
    date_hierarchy = 'check_date'
    
    fieldsets = (
        (_('Check Information'), {
            'fields': ('check_number', 'work_order', 'inspector', 'check_date')
        }),
        (_('Results'), {
            'fields': ('sample_size', 'passed', 'failed', 'result', 'pass_rate')
        }),
        (_('Details'), {
            'fields': ('defect_description', 'corrective_action', 'photo', 'notes')
        }),
        (_('Timestamp'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def result_badge(self, obj):
        colors = {
            'pass': 'green',
            'fail': 'red',
            'conditional': 'orange',
        }
        color = colors.get(obj.result, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_result_display()
        )
    result_badge.short_description = _('Result')
    
    def pass_rate_display(self, obj):
        rate = obj.pass_rate
        color = 'green' if rate >= 95 else 'orange' if rate >= 85 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, rate
        )
    pass_rate_display.short_description = _('Pass Rate')
    
    def photo_indicator(self, obj):
        if obj.photo:
            return format_html('<span style="color: green;">✓ Photo</span>')
        return format_html('<span style="color: gray;">-</span>')
    photo_indicator.short_description = _('Photo')


@admin.register(Downtime)
class DowntimeAdmin(admin.ModelAdmin):
    list_display = ['production_line', 'machine', 'start_time', 'end_time', 
                   'reason_badge', 'duration_display', 'reported_by']
    list_filter = ['reason', 'production_line', 'start_time']
    search_fields = ['production_line__line_code', 'machine__machine_code', 'description']
    autocomplete_fields = ['production_line', 'machine', 'work_order', 'reported_by']
    readonly_fields = ['created_at', 'duration_minutes']
    date_hierarchy = 'start_time'
    
    def reason_badge(self, obj):
        colors = {
            'breakdown': 'red',
            'maintenance': 'blue',
            'material_shortage': 'orange',
            'tool_change': 'purple',
            'quality_issue': 'darkred',
            'power_outage': 'black',
            'other': 'gray',
        }
        color = colors.get(obj.reason, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_reason_display()
        )
    reason_badge.short_description = _('Reason')
    
    def duration_display(self, obj):
        duration = obj.duration_minutes
        if duration >= 60:
            hours = duration / 60
            return format_html('<span style="font-weight: bold;">{} hrs</span>', hours)
        return format_html('<span>{} min</span>', duration)
    duration_display.short_description = _('Duration')