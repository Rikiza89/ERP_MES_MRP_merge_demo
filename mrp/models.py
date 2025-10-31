"""
MRP App Models
Materials, BOM, Inventory, Stock Movements, Purchase Requests, Reorder Rules
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Material(models.Model):
    """Material master data (extends Product for raw materials)"""
    MATERIAL_TYPES = [
        ('raw', _('Raw Material')),
        ('component', _('Component')),
        ('consumable', _('Consumable')),
        ('packaging', _('Packaging')),
    ]

    material_code = models.CharField(_("Material Code"), max_length=100, unique=True)
    name = models.CharField(_("Material Name"), max_length=300)
    material_type = models.CharField(_("Material Type"), max_length=20, choices=MATERIAL_TYPES, default='raw')
    product = models.OneToOneField(
        'erp.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='material_detail',
        verbose_name=_("Linked Product")
    )
    unit = models.CharField(_("Unit"), max_length=50, default='kg')
    unit_cost = models.DecimalField(_("Unit Cost"), max_digits=12, decimal_places=2, default=0)
    lead_time_days = models.IntegerField(_("Lead Time (days)"), default=7)
    min_order_quantity = models.DecimalField(_("Min Order Quantity"), max_digits=12, decimal_places=2, default=1)
    supplier = models.ForeignKey(
        'erp.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials',
        verbose_name=_("Primary Supplier")
    )
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Material")
        verbose_name_plural = _("Materials")
        ordering = ['material_code']

    def __str__(self):
        return f"{self.material_code} - {self.name}"


class BOM(models.Model):
    """Bill of Materials - product composition"""
    bom_number = models.CharField(_("BOM Number"), max_length=100, unique=True)
    product = models.ForeignKey(
        'erp.Product',
        on_delete=models.CASCADE,
        related_name='boms',
        verbose_name=_("Product")
    )
    version = models.CharField(_("Version"), max_length=50, default='1.0')
    active = models.BooleanField(_("Active"), default=True)
    effective_date = models.DateField(_("Effective Date"), default=timezone.now)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("BOM")
        verbose_name_plural = _("BOMs")
        ordering = ['bom_number']
        unique_together = ['product', 'version']

    def __str__(self):
        return f"{self.bom_number} - {self.product.name} v{self.version}"

    @property
    def total_cost(self):
        """Calculate total material cost for this BOM"""
        total = Decimal(0)
        for line in self.lines.all():
            if line.material:
                total += line.quantity * line.material.unit_cost
            elif line.component:
                total += line.quantity * line.component.cost
        return total


class BOMLine(models.Model):
    """BOM line items"""
    bom = models.ForeignKey(
        BOM,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_("BOM")
    )
    line_number = models.IntegerField(_("Line Number"))
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='bom_lines',
        verbose_name=_("Material")
    )
    component = models.ForeignKey(
        'erp.Product',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='component_bom_lines',
        verbose_name=_("Component Product")
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=12, decimal_places=4, validators=[MinValueValidator(0)])
    unit = models.CharField(_("Unit"), max_length=50, default='pcs')
    scrap_factor = models.DecimalField(
        _("Scrap Factor (%)"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Expected waste percentage")
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)

    class Meta:
        verbose_name = _("BOM Line")
        verbose_name_plural = _("BOM Lines")
        ordering = ['bom', 'line_number']
        unique_together = ['bom', 'line_number']

    def __str__(self):
        item = self.material or self.component
        return f"{self.bom.bom_number} - Line {self.line_number}: {item}"

    @property
    def adjusted_quantity(self):
        """Quantity including scrap factor"""
        return self.quantity * (1 + self.scrap_factor / 100)


class Inventory(models.Model):
    """Inventory/Stock levels"""
    product = models.ForeignKey(
        'erp.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory',
        verbose_name=_("Product")
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='inventory',
        verbose_name=_("Material")
    )
    warehouse = models.CharField(_("Warehouse"), max_length=100, default='Main')
    location = models.CharField(_("Location"), max_length=200, blank=True, null=True)
    quantity_on_hand = models.DecimalField(_("Quantity On Hand"), max_digits=15, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(_("Quantity Reserved"), max_digits=15, decimal_places=2, default=0)
    quantity_available = models.DecimalField(_("Quantity Available"), max_digits=15, decimal_places=2, default=0)
    last_count_date = models.DateField(_("Last Count Date"), blank=True, null=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Inventory")
        verbose_name_plural = _("Inventory")
        unique_together = ['product', 'material', 'warehouse', 'location']
        indexes = [
            models.Index(fields=['warehouse']),
            models.Index(fields=['quantity_on_hand']),
        ]

    def __str__(self):
        item = self.product or self.material
        return f"{item} - {self.warehouse}: {self.quantity_on_hand}"

    def save(self, *args, **kwargs):
        """Auto-calculate available quantity"""
        self.quantity_available = self.quantity_on_hand - self.quantity_reserved
        super().save(*args, **kwargs)

    @property
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        if self.product and self.product.min_stock:
            return self.quantity_available < self.product.min_stock
        return False


class StockMovement(models.Model):
    """Stock movement transactions"""
    MOVEMENT_TYPES = [
        ('in', _('Inbound')),
        ('out', _('Outbound')),
        ('transfer', _('Transfer')),
        ('adjustment', _('Adjustment')),
        ('production', _('Production')),
        ('consumption', _('Consumption')),
    ]

    movement_number = models.CharField(_("Movement Number"), max_length=100, unique=True)
    movement_type = models.CharField(_("Movement Type"), max_length=20, choices=MOVEMENT_TYPES)
    product = models.ForeignKey(
        'erp.Product',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Product")
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Material")
    )
    from_warehouse = models.CharField(_("From Warehouse"), max_length=100, blank=True, null=True)
    to_warehouse = models.CharField(_("To Warehouse"), max_length=100, blank=True, null=True)
    quantity = models.DecimalField(_("Quantity"), max_digits=12, decimal_places=2)
    unit = models.CharField(_("Unit"), max_length=50, default='pcs')
    reference = models.CharField(_("Reference"), max_length=200, blank=True, null=True)
    work_order = models.ForeignKey(
        'mes.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Work Order")
    )
    purchase_order = models.ForeignKey(
        'erp.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Purchase Order")
    )
    sales_order = models.ForeignKey(
        'erp.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Sales Order")
    )
    movement_date = models.DateTimeField(_("Movement Date"), default=timezone.now)
    performed_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Performed By")
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Stock Movement")
        verbose_name_plural = _("Stock Movements")
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['-movement_date']),
            models.Index(fields=['movement_type', '-movement_date']),
        ]

    def __str__(self):
        item = self.product or self.material
        return f"{self.movement_number} - {item}: {self.quantity}"


class PurchaseRequest(models.Model):
    """Material purchase request (MRP generated)"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('ordered', _('PO Created')),
        ('received', _('Received')),
        ('cancelled', _('Cancelled')),
    ]

    pr_number = models.CharField(_("PR Number"), max_length=100, unique=True)
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='purchase_requests',
        verbose_name=_("Material")
    )
    requested_quantity = models.DecimalField(_("Requested Quantity"), max_digits=12, decimal_places=2)
    required_date = models.DateField(_("Required Date"))
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    purchase_order = models.ForeignKey(
        'erp.PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requests',
        verbose_name=_("Purchase Order")
    )
    work_order = models.ForeignKey(
        'mes.WorkOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requests',
        verbose_name=_("Related Work Order")
    )
    requested_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_requests',
        verbose_name=_("Requested By")
    )
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Purchase Request")
        verbose_name_plural = _("Purchase Requests")
        ordering = ['-required_date', '-pr_number']

    def __str__(self):
        return f"{self.pr_number} - {self.material.name}"


class ReorderRule(models.Model):
    """Automatic reorder point rules"""
    RULE_TYPES = [
        ('min_max', _('Min-Max')),
        ('reorder_point', _('Reorder Point')),
        ('time_based', _('Time Based')),
    ]

    product = models.ForeignKey(
        'erp.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reorder_rules',
        verbose_name=_("Product")
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reorder_rules',
        verbose_name=_("Material")
    )
    warehouse = models.CharField(_("Warehouse"), max_length=100, default='Main')
    rule_type = models.CharField(_("Rule Type"), max_length=20, choices=RULE_TYPES, default='reorder_point')
    min_quantity = models.DecimalField(_("Min Quantity"), max_digits=12, decimal_places=2, default=0)
    max_quantity = models.DecimalField(_("Max Quantity"), max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(_("Reorder Point"), max_digits=12, decimal_places=2, default=0)
    reorder_quantity = models.DecimalField(_("Reorder Quantity"), max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(_("Active"), default=True)
    last_triggered = models.DateTimeField(_("Last Triggered"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Reorder Rule")
        verbose_name_plural = _("Reorder Rules")
        unique_together = ['product', 'material', 'warehouse']

    def __str__(self):
        item = self.product or self.material
        return f"{item} - {self.warehouse} - {self.get_rule_type_display()}"


class MRPCalculation(models.Model):
    """MRP calculation run history"""
    STATUS_CHOICES = [
        ('running', _('Running')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    calculation_number = models.CharField(_("Calculation Number"), max_length=100, unique=True)
    start_time = models.DateTimeField(_("Start Time"), default=timezone.now)
    end_time = models.DateTimeField(_("End Time"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='running')
    work_orders_analyzed = models.IntegerField(_("Work Orders Analyzed"), default=0)
    purchase_requests_created = models.IntegerField(_("Purchase Requests Created"), default=0)
    calculation_log = models.TextField(_("Calculation Log"), blank=True, null=True)
    run_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mrp_calculations',
        verbose_name=_("Run By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("MRP Calculation")
        verbose_name_plural = _("MRP Calculations")
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.calculation_number} - {self.status}"