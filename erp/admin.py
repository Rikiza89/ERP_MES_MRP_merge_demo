"""
ERP App Admin Configuration
Enhanced with inline forms, modals, and custom actions
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from .models import (
    ProductCategory, Product, Supplier, Customer,
    PurchaseOrder, PurchaseOrderLine,
    SalesOrder, SalesOrderLine,
    Invoice, Payment
)
from import_export.admin import ImportExportModelAdmin


@admin.register(ProductCategory)
class ProductCategoryAdmin(ImportExportModelAdmin):
    list_display = ['code', 'name', 'parent', 'active', 'product_count']
    list_filter = ['active', 'parent']
    search_fields = ['code', 'name']
    autocomplete_fields = ['parent']
    
    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<b>{}</b>', count)
    product_count.short_description = _('Products')


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    list_display = ['product_number', 'name', 'category', 'product_type', 'price', 'cost', 
                   'margin_display', 'stock_status', 'active']
    list_filter = ['product_type', 'active', 'category']
    search_fields = ['product_number', 'name', 'sku', 'barcode']
    autocomplete_fields = ['category']
    readonly_fields = ['created_at', 'updated_at', 'margin_display']
    
    fieldsets = (
        (_('Product Information'), {
            'fields': ('product_number', 'name', 'sku', 'barcode', 'category', 
                      'product_type', 'description', 'specifications', 'image')
        }),
        (_('Pricing'), {
            'fields': ('price', 'cost', 'margin_display')
        }),
        (_('Inventory Settings'), {
            'fields': ('unit', 'min_stock', 'max_stock')
        }),
        (_('Status'), {
            'fields': ('active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def margin_display(self, obj):
        margin = obj.margin
        color = 'green' if margin > 20 else 'orange' if margin > 10 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, margin
        )
    margin_display.short_description = _('Margin')
    
    def stock_status(self, obj):
        # Will be implemented with inventory integration
        return format_html('<span style="color: gray;">-</span>')
    stock_status.short_description = _('Stock')
    
    actions = ['activate_products', 'deactivate_products', 'export_products']
    
    def activate_products(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, _(f'{updated} products activated.'))
    activate_products.short_description = _('Activate selected products')
    
    def deactivate_products(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, _(f'{updated} products deactivated.'))
    deactivate_products.short_description = _('Deactivate selected products')


@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    list_display = ['supplier_code', 'name', 'contact_person', 'email', 'phone', 'active', 'po_count']
    list_filter = ['active', 'created_at']
    search_fields = ['supplier_code', 'name', 'email', 'contact_person']
    
    def po_count(self, obj):
        count = obj.purchase_orders.count()
        url = reverse('admin:erp_purchaseorder_changelist') + f'?supplier__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    po_count.short_description = _('POs')


@admin.register(Customer)
class CustomerAdmin(ImportExportModelAdmin):
    list_display = ['customer_code', 'name', 'contact_person', 'email', 'phone', 
                   'credit_limit', 'active', 'so_count']
    list_filter = ['active', 'created_at']
    search_fields = ['customer_code', 'name', 'email', 'contact_person']
    
    def so_count(self, obj):
        count = obj.sales_orders.count()
        url = reverse('admin:erp_salesorder_changelist') + f'?customer__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    so_count.short_description = _('SOs')


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1
    autocomplete_fields = ['product']
    fields = ['product', 'quantity', 'unit_price', 'total_price', 'received_quantity']
    readonly_fields = ['total_price']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ImportExportModelAdmin):
    list_display = ['po_number', 'supplier', 'order_date', 'expected_date', 
                   'status_badge', 'total_amount', 'created_by']
    list_filter = ['status', 'order_date', 'expected_date']
    search_fields = ['po_number', 'supplier__name']
    autocomplete_fields = ['supplier', 'created_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderLineInline]
    
    fieldsets = (
        (_('Purchase Order Information'), {
            'fields': ('po_number', 'supplier', 'order_date', 'expected_date', 'status')
        }),
        (_('Financial'), {
            'fields': ('total_amount',)
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'sent': 'blue',
            'confirmed': 'orange',
            'received': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    actions = ['mark_as_sent', 'mark_as_confirmed']
    
    def mark_as_sent(self, request, queryset):
        updated = queryset.filter(status='draft').update(status='sent')
        self.message_user(request, _(f'{updated} orders marked as sent.'))
    mark_as_sent.short_description = _('Mark as Sent')
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.filter(status='sent').update(status='confirmed')
        self.message_user(request, _(f'{updated} orders confirmed.'))
    mark_as_confirmed.short_description = _('Mark as Confirmed')


class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 1
    autocomplete_fields = ['product']
    fields = ['product', 'quantity', 'unit_price', 'total_price', 'shipped_quantity']
    readonly_fields = ['total_price']


@admin.register(SalesOrder)
class SalesOrderAdmin(ImportExportModelAdmin):
    list_display = ['so_number', 'customer', 'order_date', 'delivery_date', 
                   'status_badge', 'total_amount', 'created_by']
    list_filter = ['status', 'order_date', 'delivery_date']
    search_fields = ['so_number', 'customer__name']
    autocomplete_fields = ['customer', 'created_by']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'order_date'
    inlines = [SalesOrderLineInline]
    
    fieldsets = (
        (_('Sales Order Information'), {
            'fields': ('so_number', 'customer', 'order_date', 'delivery_date', 'status')
        }),
        (_('Financial'), {
            'fields': ('total_amount',)
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'confirmed': 'blue',
            'in_production': 'orange',
            'ready': 'purple',
            'shipped': 'teal',
            'delivered': 'green',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    actions = ['confirm_orders', 'create_work_orders']
    
    def confirm_orders(self, request, queryset):
        updated = queryset.filter(status='draft').update(status='confirmed')
        self.message_user(request, _(f'{updated} orders confirmed.'))
    confirm_orders.short_description = _('Confirm Selected Orders')
    
    def create_work_orders(self, request, queryset):
        # Will be implemented with MES integration
        self.message_user(request, _('Work order creation will be available after MES integration.'))
    create_work_orders.short_description = _('Create Work Orders')


@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    list_display = ['invoice_number', 'invoice_type', 'invoice_date', 'due_date', 
                   'status_badge', 'total', 'paid_amount', 'balance_display']
    list_filter = ['invoice_type', 'status', 'invoice_date', 'due_date']
    search_fields = ['invoice_number']
    autocomplete_fields = ['sales_order', 'purchase_order']
    readonly_fields = ['created_at', 'updated_at', 'balance_display']
    date_hierarchy = 'invoice_date'
    
    fieldsets = (
        (_('Invoice Information'), {
            'fields': ('invoice_number', 'invoice_type', 'sales_order', 'purchase_order',
                      'invoice_date', 'due_date', 'status')
        }),
        (_('Amounts'), {
            'fields': ('subtotal', 'tax', 'total', 'paid_amount', 'balance_display')
        }),
        (_('Additional Information'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'sent': 'blue',
            'paid': 'green',
            'overdue': 'red',
            'cancelled': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def balance_display(self, obj):
        balance = obj.balance
        if balance > 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', balance)
        return format_html('<span style="color: green;">Paid</span>')
    balance_display.short_description = _('Balance')


@admin.register(Payment)
class PaymentAdmin(ImportExportModelAdmin):
    list_display = ['payment_number', 'invoice', 'payment_date', 'amount', 
                   'payment_method', 'created_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['payment_number', 'invoice__invoice_number', 'reference']
    autocomplete_fields = ['invoice', 'created_by']
    readonly_fields = ['created_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        (_('Payment Information'), {
            'fields': ('payment_number', 'invoice', 'payment_date', 'amount', 'payment_method')
        }),
        (_('Additional Details'), {
            'fields': ('reference', 'notes', 'created_by')
        }),
        (_('Timestamp'), {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )