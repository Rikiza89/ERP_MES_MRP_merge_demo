"""
MES App Models
Production Lines, Shifts, Work Orders, Machines, Production Logs, Quality Checks
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import timedelta


class ProductionLine(models.Model):
    """Production line/work center"""
    line_code = models.CharField(_("Line Code"), max_length=100, unique=True)
    name = models.CharField(_("Line Name"), max_length=200)
    department = models.ForeignKey(
        'core.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_lines',
        verbose_name=_("Department")
    )
    capacity = models.DecimalField(_("Capacity (units/hour)"), max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Production Line")
        verbose_name_plural = _("Production Lines")
        ordering = ['line_code']

    def __str__(self):
        return f"{self.line_code} - {self.name}"


class Shift(models.Model):
    """Work shift definition"""
    shift_code = models.CharField(_("Shift Code"), max_length=50, unique=True)
    name = models.CharField(_("Shift Name"), max_length=100)
    start_time = models.TimeField(_("Start Time"))
    end_time = models.TimeField(_("End Time"))
    active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Shift")
        verbose_name_plural = _("Shifts")
        ordering = ['start_time']

    def __str__(self):
        return f"{self.shift_code} - {self.name}"


class Machine(models.Model):
    """Machine/Equipment master"""
    STATUS_CHOICES = [
        ('operational', _('Operational')),
        ('maintenance', _('Under Maintenance')),
        ('breakdown', _('Breakdown')),
        ('idle', _('Idle')),
    ]

    machine_code = models.CharField(_("Machine Code"), max_length=100, unique=True)
    name = models.CharField(_("Machine Name"), max_length=200)
    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='machines',
        verbose_name=_("Production Line")
    )
    manufacturer = models.CharField(_("Manufacturer"), max_length=200, blank=True, null=True)
    model_number = models.CharField(_("Model Number"), max_length=100, blank=True, null=True)
    serial_number = models.CharField(_("Serial Number"), max_length=100, blank=True, null=True)
    purchase_date = models.DateField(_("Purchase Date"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='operational')
    last_maintenance = models.DateField(_("Last Maintenance"), blank=True, null=True)
    next_maintenance = models.DateField(_("Next Maintenance"), blank=True, null=True)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Machine")
        verbose_name_plural = _("Machines")
        ordering = ['machine_code']

    def __str__(self):
        return f"{self.machine_code} - {self.name}"


class WorkOrder(models.Model):
    """Manufacturing work order"""
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('ready', _('Ready to Start')),
        ('in_progress', _('In Progress')),
        ('paused', _('Paused')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    wo_number = models.CharField(_("WO Number"), max_length=100, unique=True)
    sales_order = models.ForeignKey(
        'erp.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        verbose_name=_("Sales Order")
    )
    product = models.ForeignKey(
        'erp.Product',
        on_delete=models.PROTECT,
        related_name='work_orders',
        verbose_name=_("Product")
    )
    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        verbose_name=_("Production Line")
    )
    planned_quantity = models.DecimalField(_("Planned Quantity"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    produced_quantity = models.DecimalField(_("Produced Quantity"), max_digits=12, decimal_places=2, default=0)
    rejected_quantity = models.DecimalField(_("Rejected Quantity"), max_digits=12, decimal_places=2, default=0)
    planned_start = models.DateTimeField(_("Planned Start"), default=timezone.now)
    planned_end = models.DateTimeField(_("Planned End"), blank=True, null=True)
    actual_start = models.DateTimeField(_("Actual Start"), blank=True, null=True)
    actual_end = models.DateTimeField(_("Actual End"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.IntegerField(_("Priority"), default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_work_orders',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Work Order")
        verbose_name_plural = _("Work Orders")
        ordering = ['-priority', '-planned_start']
        indexes = [
            models.Index(fields=['status', '-planned_start']),
            models.Index(fields=['production_line', 'status']),
        ]

    def __str__(self):
        return f"{self.wo_number} - {self.product.name}"

    @property
    def completion_rate(self):
        """Calculate completion percentage"""
        if self.planned_quantity > 0:
            return (self.produced_quantity / self.planned_quantity) * 100
        return 0

    @property
    def efficiency(self):
        """Calculate production efficiency"""
        if self.actual_start and self.actual_end and self.planned_end and self.planned_start:
            planned_duration = (self.planned_end - self.planned_start).total_seconds()
            actual_duration = (self.actual_end - self.actual_start).total_seconds()
            if actual_duration > 0:
                return (planned_duration / actual_duration) * 100
        return None

    @property
    def is_delayed(self):
        """Check if work order is delayed"""
        if self.status in ['in_progress', 'pending'] and self.planned_end:
            return timezone.now() > self.planned_end
        return False


class ProductionLog(models.Model):
    """Detailed production activity log"""
    ACTION_TYPES = [
        ('start', _('Start')),
        ('stop', _('Stop')),
        ('pause', _('Pause')),
        ('resume', _('Resume')),
        ('record_output', _('Record Output')),
        ('record_reject', _('Record Reject')),
    ]

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='production_logs',
        verbose_name=_("Work Order")
    )
    operator = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_logs',
        verbose_name=_("Operator")
    )
    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='production_logs',
        verbose_name=_("Shift")
    )
    action_type = models.CharField(_("Action Type"), max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(_("Timestamp"), default=timezone.now)
    quantity = models.DecimalField(_("Quantity"), max_digits=12, decimal_places=2, default=0)
    rejects = models.DecimalField(_("Rejects"), max_digits=12, decimal_places=2, default=0)
    downtime_minutes = models.DecimalField(_("Downtime (minutes)"), max_digits=8, decimal_places=2, default=0)
    downtime_reason = models.CharField(_("Downtime Reason"), max_length=300, blank=True, null=True)
    nfc_uid = models.CharField(_("NFC UID"), max_length=100, blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)

    class Meta:
        verbose_name = _("Production Log")
        verbose_name_plural = _("Production Logs")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['work_order', '-timestamp']),
            models.Index(fields=['operator', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.action_type} at {self.timestamp}"


class QualityCheck(models.Model):
    """Quality inspection records"""
    RESULT_CHOICES = [
        ('pass', _('Pass')),
        ('fail', _('Fail')),
        ('conditional', _('Conditional')),
    ]

    check_number = models.CharField(_("Check Number"), max_length=100, unique=True)
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='quality_checks',
        verbose_name=_("Work Order")
    )
    inspector = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_checks',
        verbose_name=_("Inspector")
    )
    check_date = models.DateTimeField(_("Check Date"), default=timezone.now)
    sample_size = models.IntegerField(_("Sample Size"), default=1)
    passed = models.IntegerField(_("Passed"), default=0)
    failed = models.IntegerField(_("Failed"), default=0)
    result = models.CharField(_("Result"), max_length=20, choices=RESULT_CHOICES, default='pass')
    defect_description = models.TextField(_("Defect Description"), blank=True, null=True)
    corrective_action = models.TextField(_("Corrective Action"), blank=True, null=True)
    photo = models.ImageField(_("Photo"), upload_to='quality_checks/', blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Quality Check")
        verbose_name_plural = _("Quality Checks")
        ordering = ['-check_date']

    def __str__(self):
        return f"{self.check_number} - {self.result}"

    @property
    def pass_rate(self):
        """Calculate pass rate percentage"""
        if self.sample_size > 0:
            return (self.passed / self.sample_size) * 100
        return 0


class Downtime(models.Model):
    """Machine/Line downtime tracking"""
    REASON_CHOICES = [
        ('breakdown', _('Equipment Breakdown')),
        ('maintenance', _('Scheduled Maintenance')),
        ('material_shortage', _('Material Shortage')),
        ('tool_change', _('Tool Change')),
        ('quality_issue', _('Quality Issue')),
        ('power_outage', _('Power Outage')),
        ('other', _('Other')),
    ]

    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.CASCADE,
        related_name='downtimes',
        verbose_name=_("Production Line")
    )
    machine = models.ForeignKey(
        Machine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='downtimes',
        verbose_name=_("Machine")
    )
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='downtimes',
        verbose_name=_("Work Order")
    )
    start_time = models.DateTimeField(_("Start Time"), default=timezone.now)
    end_time = models.DateTimeField(_("End Time"), blank=True, null=True)
    reason = models.CharField(_("Reason"), max_length=30, choices=REASON_CHOICES)
    description = models.TextField(_("Description"))
    reported_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_downtimes',
        verbose_name=_("Reported By")
    )
    resolution = models.TextField(_("Resolution"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Downtime")
        verbose_name_plural = _("Downtimes")
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.production_line.line_code} - {self.reason}"

    @property
    def duration_minutes(self):
        """Calculate downtime duration in minutes"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 60
        return (timezone.now() - self.start_time).total_seconds() / 60