"""
Core App Signals
Automatic logging for all system operations
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import LogData, Employee, UserProfile
import threading

# Thread-local storage for request context
_thread_locals = threading.local()


def get_current_request():
    """Get current request from thread local"""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request):
    """Store request in thread local"""
    _thread_locals.request = request


class RequestMiddleware:
    """Middleware to capture request in thread local"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        set_current_request(None)
        return response


def create_log(action_type, description, user=None, employee=None, model_name=None, 
               object_id=None, nfc_uid=None):
    """Helper function to create log entries"""
    request = get_current_request()
    
    ip_address = None
    device_info = None
    
    if request:
        ip_address = request.META.get('REMOTE_ADDR')
        device_info = request.META.get('HTTP_USER_AGENT', '')[:200]
        
        if not user and request.user.is_authenticated:
            user = request.user
        
        if not employee and hasattr(request.user, 'profile') and request.user.profile.employee:
            employee = request.user.profile.employee
    
    LogData.objects.create(
        user=user,
        employee=employee,
        action_type=action_type,
        model_name=model_name,
        object_id=object_id,
        description=description,
        ip_address=ip_address,
        device_info=device_info,
        nfc_uid=nfc_uid
    )


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login"""
    nfc_uid = None
    if hasattr(user, 'profile'):
        nfc_uid = user.profile.nfc_uid
    
    create_log(
        action_type='login',
        description=f'User {user.username} logged in',
        user=user,
        nfc_uid=nfc_uid
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logout"""
    if user:
        create_log(
            action_type='logout',
            description=f'User {user.username} logged out',
            user=user
        )


@receiver(post_save, sender=Employee)
def log_employee_save(sender, instance, created, **kwargs):
    """Log employee create/update"""
    action = 'create' if created else 'update'
    description = f'Employee {instance.employee_id} - {instance.full_name} {"created" if created else "updated"}'
    
    create_log(
        action_type=action,
        description=description,
        model_name='Employee',
        object_id=instance.id
    )


@receiver(post_save, sender=UserProfile)
def log_profile_save(sender, instance, created, **kwargs):
    """Log user profile changes"""
    if not created:
        create_log(
            action_type='update',
            description=f'User profile updated for {instance.user.username}',
            model_name='UserProfile',
            object_id=instance.id,
            user=instance.user
        )


# Generic logging for key models
def create_generic_log_signal(model_class, model_name):
    """Factory function to create logging signals for any model"""
    
    @receiver(post_save, sender=model_class)
    def log_model_save(sender, instance, created, **kwargs):
        action = 'create' if created else 'update'
        description = f'{model_name} {instance} {"created" if created else "updated"}'
        
        create_log(
            action_type=action,
            description=description,
            model_name=model_name,
            object_id=instance.id
        )
    
    @receiver(post_delete, sender=model_class)
    def log_model_delete(sender, instance, **kwargs):
        description = f'{model_name} {instance} deleted'
        
        create_log(
            action_type='delete',
            description=description,
            model_name=model_name,
            object_id=instance.id
        )


# Register signals for key models (will be imported in apps.py)
def register_model_signals():
    """Register signals for all tracked models"""
    from erp.models import Product, PurchaseOrder, SalesOrder, Invoice
    from mes.models import WorkOrder, ProductionLog, QualityCheck
    from mrp.models import Material, BOM, Inventory, StockMovement, PurchaseRequest
    
    models_to_track = [
        (Product, 'Product'),
        (PurchaseOrder, 'PurchaseOrder'),
        (SalesOrder, 'SalesOrder'),
        (Invoice, 'Invoice'),
        (WorkOrder, 'WorkOrder'),
        (ProductionLog, 'ProductionLog'),
        (QualityCheck, 'QualityCheck'),
        (Material, 'Material'),
        (BOM, 'BOM'),
        (Inventory, 'Inventory'),
        (StockMovement, 'StockMovement'),
        (PurchaseRequest, 'PurchaseRequest'),
    ]
    
    for model_class, model_name in models_to_track:
        create_generic_log_signal(model_class, model_name)