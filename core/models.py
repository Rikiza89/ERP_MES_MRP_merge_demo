"""
Core App Models
Base system entities: Company, Department, Employee, UserProfile, LogData
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Company(models.Model):
    """Company/Factory information"""
    name = models.CharField(_("Company Name"), max_length=200)
    code = models.CharField(_("Company Code"), max_length=50, unique=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ['name']

    def __str__(self):
        return self.name


class Department(models.Model):
    """Department/Work Center"""
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name=_("Company")
    )
    name = models.CharField(_("Department Name"), max_length=200)
    code = models.CharField(_("Department Code"), max_length=50)
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_("Manager")
    )
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Department")
        verbose_name_plural = _("Departments")
        ordering = ['company', 'name']
        unique_together = ['company', 'code']

    def __str__(self):
        return f"{self.company.code} - {self.name}"


class Employee(models.Model):
    """Employee information"""
    ROLE_CHOICES = [
        ('admin', _('Administrator')),
        ('manager', _('Manager')),
        ('operator', _('Operator')),
        ('viewer', _('Viewer')),
    ]

    employee_id = models.CharField(_("Employee ID"), max_length=50, unique=True)
    first_name = models.CharField(_("First Name"), max_length=100)
    last_name = models.CharField(_("Last Name"), max_length=100)
    email = models.EmailField(_("Email"), unique=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_("Department")
    )
    role = models.CharField(_("Role"), max_length=20, choices=ROLE_CHOICES, default='operator')
    nfc_uid = models.CharField(
        _("NFC UID"),
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text=_("NFC card unique identifier for quick login")
    )
    hire_date = models.DateField(_("Hire Date"), default=timezone.now)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        ordering = ['employee_id']

    def __str__(self):
        return f"{self.employee_id} - {self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class UserProfile(models.Model):
    """Extended user profile linked to Django User"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("User")
    )
    employee = models.OneToOneField(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profile',
        verbose_name=_("Employee")
    )
    nfc_uid = models.CharField(
        _("NFC UID"),
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text=_("NFC card UID for automatic login")
    )
    language = models.CharField(
        _("Preferred Language"),
        max_length=10,
        choices=[('en', 'English'), ('ja', '日本語')],
        default='en'
    )
    theme = models.CharField(
        _("Theme"),
        max_length=20,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    last_login_device = models.CharField(
        _("Last Login Device"),
        max_length=200,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self):
        return f"{self.user.username} Profile"


class LogData(models.Model):
    """Universal operation logger for all system actions"""
    ACTION_TYPES = [
        ('create', _('Create')),
        ('update', _('Update')),
        ('delete', _('Delete')),
        ('login', _('Login')),
        ('logout', _('Logout')),
        ('start', _('Start Operation')),
        ('stop', _('Stop Operation')),
        ('pause', _('Pause')),
        ('complete', _('Complete')),
        ('nfc_scan', _('NFC Scan')),
        ('other', _('Other')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name=_("User")
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name=_("Employee")
    )
    action_type = models.CharField(_("Action Type"), max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(_("Model Name"), max_length=100, blank=True, null=True)
    object_id = models.IntegerField(_("Object ID"), blank=True, null=True)
    description = models.TextField(_("Description"))
    ip_address = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    device_info = models.CharField(_("Device Info"), max_length=200, blank=True, null=True)
    nfc_uid = models.CharField(_("NFC UID"), max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True)

    class Meta:
        verbose_name = _("Log Entry")
        verbose_name_plural = _("Log Entries")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{self.timestamp} - {user_str} - {self.action_type}: {self.description}"