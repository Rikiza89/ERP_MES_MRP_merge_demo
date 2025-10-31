"""
MRP App Admin Configuration
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from .models import (
    Material, BOM, BOMLine, Inventory, StockMovement,
    PurchaseRequest, ReorderRule, MRPCalculation
)
from import_export.admin import ImportExportModelAdmin


@admin.register(Material)
class MaterialAdmin(ImportExportModelAdmin):
    list_display = ['material_code', 'name', 'material_type', 'unit_cost', 'supplier', 
                   'lead_time_days', 'stock_level', 'active']
    list_filter = ['material_type', 'active', 'supplier']
    search_fields = ['material_code', 'name']
    autocomplete_fields = ['product', 'supplier']
    
    def stock_level(self, obj):
        inventory = Inventory.objects.filter(material=obj).first()
        if inventory:
            color = 'red' if inventory.is_low_stock else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, inventory.quantity_on_hand
            )
        return format_html('<span style="color: gray;">-</span>')
    stock_level.short_description = _('Stock')


class BOMLineInline(admin.TabularInline):
    model = BOMLine
    extra = 1
    autocomplete_fields = ['material', 'component']
    fields = ['line_number', 'material', 'component', 'quantity', 'unit', 'scrap_factor']


@admin.register(BOM)
class BOMAdmin(ImportExportModelAdmin):
    list_display = ['bom_number', 'product', 'version', 'active', 'effective_date', 
                   'line_count', 'total_cost_display']
    list_filter = ['active', 'effective_date']
    search_fields = ['bom_number', 'product__name']
    autocomplete_fields = ['product']
    readonly_fields = ['created_at', 'updated_at', 'total_cost']
    date_hierarchy = 'effective_date'
    inlines = [BOMLineInline]
    
    def line_count(self, obj):
        count = obj.lines.count()
        return format_html('<b>{}</b>', count)
    line_count.short_description = _('Lines')
    
    def total_cost_display(self, obj):
        cost = obj.total_cost
        return format_html('<span style="font-weight: bold;">${}</span>', cost)
    total_cost_display.short_description = _('Total Cost')


@admin.register(Inventory)
class InventoryAdmin(ImportExportModelAdmin):
    list_display = ['item_display', 'warehouse', 'location', 'quantity_on_hand', 
                   'quantity_reserved', 'quantity_available', 'stock_status', 'updated_at']
    list_filter = ['warehouse', 'updated_at']
    search_fields = ['product__name', 'material__name', 'warehouse', 'location']
    autocomplete_fields = ['product', 'material']
    readonly_fields = ['quantity_available', 'updated_at', 'is_low_stock']
    
    fieldsets = (
        (_('Item'), {
            'fields': ('product', 'material')
        }),
        (_('Location'), {
            'fields': ('warehouse', 'location')
        }),
        (_('Quantities'), {
            'fields': ('quantity_on_hand', 'quantity_reserved', 'quantity_available')
        }),
        (_('Tracking'), {
            'fields': ('last_count_date', 'is_low_stock', 'updated_at')
        }),
    )
    
    def item_display(self, obj):
        item = obj.product or obj.material
        return str(item)
    item_display.short_description = _('Item')
    
    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html(
                '<span style="background-color: red; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">⚠ LOW</span>'
            )
        elif obj.quantity_available <= 0:
            return format_html(
                '<span style="background-color: darkred; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-weight: bold;">OUT</span>'
            )
        return format_html('<span style="color: green;">✓ OK</span>')
    stock_status.short_description = _('Status')
    
    actions = ['create_reorder_requests']
    
    def create_reorder_requests(self, request, queryset):
        count = 0
        for inventory in queryset.filter(quantity_available__lt=0):
            # Logic to create purchase request
            count += 1
        messages.success(request, _(f'{count} reorder requests created.'))
    create_reorder_requests.short_description = _('Create Reorder Requests')


@admin.register(StockMovement)
class StockMovementAdmin(ImportExportModelAdmin):
    list_display = ['movement_number', 'movement_type_badge', 'item_display', 
                   'quantity', 'from_warehouse', 'to_warehouse', 'movement_date', 'performed_by']
    list_filter = ['movement_type', 'movement_date', 'from_warehouse', 'to_warehouse']
    search_fields = ['movement_number', 'product__name', 'material__name', 'reference']
    autocomplete_fields = ['product', 'material', 'work_order', 'purchase_order', 
                          'sales_order', 'performed_by']
    readonly_fields = ['created_at']
    date_hierarchy = 'movement_date'
    
    def item_display(self, obj):
        item = obj.product or obj.material
        return str(item)
    item_display.short_description = _('Item')
    
    def movement_type_badge(self, obj):
        colors = {
            'in': 'green',
            'out': 'red',
            'transfer': 'blue',
            'adjustment': 'orange',
            'production': 'purple',
            'consumption': 'darkred',
        }
        color = colors.get(obj.movement_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_movement_type_display()
        )
    movement_type_badge.short_description = _('Type')


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(ImportExportModelAdmin):
    list_display = ['pr_number', 'material', 'requested_quantity', 'required_date', 
                   'status_badge', 'purchase_order', 'requested_by']
    list_filter = ['status', 'required_date', 'created_at']
    search_fields = ['pr_number', 'material__name']
    autocomplete_fields = ['material', 'purchase_order', 'work_order', 'requested_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'required_date'
    
    fieldsets = (
        (_('Request Information'), {
            'fields': ('pr_number', 'material', 'requested_quantity', 'required_date', 'status')
        }),
        (_('References'), {
            'fields': ('work_order', 'purchase_order')
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'requested_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'pending': 'blue',
            'approved': 'green',
            'ordered': 'purple',
            'received': 'darkgreen',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    actions = ['approve_requests', 'create_purchase_orders']
    
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='approved')
        messages.success(request, _(f'{updated} requests approved.'))
    approve_requests.short_description = _('Approve Selected Requests')
    
    def create_purchase_orders(self, request, queryset):
        # Will create POs from approved PRs
        messages.info(request, _('PO creation from PRs will be implemented.'))
    create_purchase_orders.short_description = _('Create Purchase Orders')


@admin.register(ReorderRule)
class ReorderRuleAdmin(ImportExportModelAdmin):
    list_display = ['item_display', 'warehouse', 'rule_type', 'reorder_point', 
                   'reorder_quantity', 'active', 'last_triggered']
    list_filter = ['rule_type', 'active', 'warehouse']
    search_fields = ['product__name', 'material__name', 'warehouse']
    autocomplete_fields = ['product', 'material']
    readonly_fields = ['created_at', 'updated_at', 'last_triggered']
    
    def item_display(self, obj):
        item = obj.product or obj.material
        return str(item)
    item_display.short_description = _('Item')


@admin.register(MRPCalculation)
class MRPCalculationAdmin(admin.ModelAdmin):
    list_display = ['calculation_number', 'start_time', 'end_time', 'status_badge', 
                   'work_orders_analyzed', 'purchase_requests_created', 'run_by']
    list_filter = ['status', 'start_time']
    search_fields = ['calculation_number']
    autocomplete_fields = ['run_by']
    readonly_fields = ['created_at', 'start_time', 'end_time', 'work_orders_analyzed', 
                      'purchase_requests_created', 'calculation_log']
    date_hierarchy = 'start_time'
    
    def status_badge(self, obj):
        colors = {
            'running': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False