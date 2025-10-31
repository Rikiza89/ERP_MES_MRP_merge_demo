"""
Core App Admin Configuration
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Company, Department, Employee, UserProfile, LogData
from import_export.admin import ImportExportModelAdmin


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = _('Profile')
    fields = ['employee', 'nfc_uid', 'language', 'theme', 'last_login_device']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_nfc_uid']
    
    def get_nfc_uid(self, obj):
        if hasattr(obj, 'profile') and obj.profile.nfc_uid:
            return obj.profile.nfc_uid
        return '-'
    get_nfc_uid.short_description = _('NFC UID')


# Unregister default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Company)
class CompanyAdmin(ImportExportModelAdmin):
    list_display = ['code', 'name', 'phone', 'email', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['code', 'name', 'email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('code', 'name', 'active')
        }),
        (_('Contact Details'), {
            'fields': ('address', 'phone', 'email')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    list_display = ['code', 'name', 'company', 'manager', 'active', 'created_at']
    list_filter = ['company', 'active', 'created_at']
    search_fields = ['code', 'name', 'company__name']
    autocomplete_fields = ['company', 'manager']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'code', 'name', 'manager', 'active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    list_display = ['employee_id', 'full_name', 'email', 'department', 'role', 'nfc_status', 'active']
    list_filter = ['role', 'active', 'department', 'hire_date']
    search_fields = ['employee_id', 'first_name', 'last_name', 'email', 'nfc_uid']
    autocomplete_fields = ['department']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('employee_id', 'first_name', 'last_name', 'email', 'phone')
        }),
        (_('Employment Details'), {
            'fields': ('department', 'role', 'hire_date', 'active')
        }),
        (_('NFC Configuration'), {
            'fields': ('nfc_uid',),
            'classes': ('collapse',),
            'description': _('Configure NFC card for quick login and operation tracking')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def nfc_status(self, obj):
        if obj.nfc_uid:
            return format_html(
                '<span style="color: green;">✓ {}</span>',
                _('Configured')
            )
        return format_html(
            '<span style="color: gray;">○ {}</span>',
            _('Not Set')
        )
    nfc_status.short_description = _('NFC Status')
    
    actions = ['export_employees']
    
    def export_employees(self, request, queryset):
        # Custom export action
        pass
    export_employees.short_description = _('Export selected employees')


@admin.register(LogData)
class LogDataAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'employee', 'action_type', 'model_name', 'short_description', 'ip_address']
    list_filter = ['action_type', 'model_name', 'timestamp']
    search_fields = ['user__username', 'employee__employee_id', 'description', 'ip_address', 'nfc_uid']
    readonly_fields = ['timestamp', 'user', 'employee', 'action_type', 'model_name', 
                      'object_id', 'description', 'ip_address', 'device_info', 'nfc_uid']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def short_description(self, obj):
        if len(obj.description) > 50:
            return obj.description[:50] + '...'
        return obj.description
    short_description.short_description = _('Description')
    
    fieldsets = (
        (_('Who'), {
            'fields': ('user', 'employee', 'nfc_uid')
        }),
        (_('What'), {
            'fields': ('action_type', 'model_name', 'object_id', 'description')
        }),
        (_('When & Where'), {
            'fields': ('timestamp', 'ip_address', 'device_info')
        }),
    )
    
    
# At the very end of core/admin.py
from dashboard.views import get_kpis, get_production_data, get_inventory_alerts, get_recent_activities
import json

def add_dashboard_context(request, extra_context=None):
    """Add dashboard data to admin index context"""
    if extra_context is None:
        extra_context = {}
    extra_context.update({
        'kpis': get_kpis(),
        'production_data': json.dumps(get_production_data()),
        'inventory_alerts': get_inventory_alerts(),
        'recent_activities': get_recent_activities(),
    })
    return extra_context

# Add this at the END of core/admin.py (COMPLETE VERSION)
import json
from django.contrib import admin
from dashboard.views import get_kpis, get_production_data, get_inventory_alerts, get_recent_activities

# Monkey-patch admin site index to add dashboard data
_original_index = admin.site.index

def custom_admin_index(request, extra_context=None):
    """Override admin index to inject dashboard data"""
    if extra_context is None:
        extra_context = {}
    
    # Get the data
    kpis = get_kpis()
    production_data = get_production_data()
    
    # Debug: Print to console
    print("=" * 60)
    print("DASHBOARD DATA DEBUG")
    print("=" * 60)
    print(f"KPIs: {kpis}")
    print(f"Production Data: {production_data}")
    print(f"Daily Production Items: {len(production_data.get('daily', []))}")
    print(f"Production Lines: {len(production_data.get('by_line', []))}")
    print("=" * 60)
    
    # Add dashboard data to context
    extra_context.update({
        'kpis': kpis,
        'production_data': json.dumps(production_data),
        'inventory_alerts': get_inventory_alerts(),
        'recent_activities': get_recent_activities(),
    })
    
    return _original_index(request, extra_context)

# Replace the admin index method
admin.site.index = custom_admin_index