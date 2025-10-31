"""
ERP App Models
Products, Suppliers, Customers, Orders, Invoices, Payments
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class ProductCategory(models.Model):
    """Product category/classification"""
    name = models.CharField(_("Category Name"), max_length=200)
    code = models.CharField(_("Category Code"), max_length=50, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Parent Category")
    )
    description = models.TextField(_("Description"), blank=True, null=True)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Product(models.Model):
    """Product master data"""
    PRODUCT_TYPES = [
        ('finished', _('Finished Good')),
        ('semi', _('Semi-Finished')),
        ('raw', _('Raw Material')),
        ('component', _('Component')),
        ('consumable', _('Consumable')),
    ]

    product_number = models.CharField(_("Product Number"), max_length=100, unique=True)
    name = models.CharField(_("Product Name"), max_length=300)
    sku = models.CharField(_("SKU"), max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(_("Barcode"), max_length=100, unique=True, blank=True, null=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name=_("Category")
    )
    product_type = models.CharField(_("Product Type"), max_length=20, choices=PRODUCT_TYPES, default='finished')
    description = models.TextField(_("Description"), blank=True, null=True)
    specifications = models.TextField(_("Specifications"), blank=True, null=True)
    
    # Pricing
    price = models.DecimalField(_("Selling Price"), max_digits=15, decimal_places=2, default=0)
    cost = models.DecimalField(_("Cost"), max_digits=15, decimal_places=2, default=0)
    
    # Inventory
    unit = models.CharField(_("Unit"), max_length=50, default='pcs')
    min_stock = models.DecimalField(_("Min Stock"), max_digits=12, decimal_places=2, default=0)
    max_stock = models.DecimalField(_("Max Stock"), max_digits=12, decimal_places=2, default=0)
    
    # Media
    image = models.ImageField(_("Product Image"), upload_to='products/', blank=True, null=True)
    
    # Status
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['product_number']
        indexes = [
            models.Index(fields=['product_number']),
            models.Index(fields=['sku']),
            models.Index(fields=['barcode']),
        ]

    def __str__(self):
        return f"{self.product_number} - {self.name}"

    @property
    def margin(self):
        """Calculate profit margin"""
        if self.price > 0:
            return ((self.price - self.cost) / self.price) * 100
        return 0

    def save(self, *args, **kwargs):
        """Auto-generate SKU if not provided"""
        if not self.sku:
            self.sku = f"SKU-{self.product_number}"
        super().save(*args, **kwargs)


class Supplier(models.Model):
    """Supplier/Vendor master data"""
    supplier_code = models.CharField(_("Supplier Code"), max_length=100, unique=True)
    name = models.CharField(_("Supplier Name"), max_length=300)
    contact_person = models.CharField(_("Contact Person"), max_length=200, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    payment_terms = models.CharField(_("Payment Terms"), max_length=200, blank=True, null=True)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['supplier_code']

    def __str__(self):
        return f"{self.supplier_code} - {self.name}"


class Customer(models.Model):
    """Customer master data"""
    customer_code = models.CharField(_("Customer Code"), max_length=100, unique=True)
    name = models.CharField(_("Customer Name"), max_length=300)
    contact_person = models.CharField(_("Contact Person"), max_length=200, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=50, blank=True, null=True)
    address = models.TextField(_("Address"), blank=True, null=True)
    payment_terms = models.CharField(_("Payment Terms"), max_length=200, blank=True, null=True)
    credit_limit = models.DecimalField(_("Credit Limit"), max_digits=15, decimal_places=2, default=0)
    active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ['customer_code']

    def __str__(self):
        return f"{self.customer_code} - {self.name}"


class PurchaseOrder(models.Model):
    """Purchase order from supplier"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('confirmed', _('Confirmed')),
        ('received', _('Received')),
        ('cancelled', _('Cancelled')),
    ]

    po_number = models.CharField(_("PO Number"), max_length=100, unique=True)
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name=_("Supplier")
    )
    order_date = models.DateField(_("Order Date"), default=timezone.now)
    expected_date = models.DateField(_("Expected Delivery Date"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(_("Total Amount"), max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_pos',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")
        ordering = ['-order_date', '-po_number']

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"


class PurchaseOrderLine(models.Model):
    """Purchase order line items"""
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_("Purchase Order")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='po_lines',
        verbose_name=_("Product")
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(_("Unit Price"), max_digits=15, decimal_places=2)
    total_price = models.DecimalField(_("Total Price"), max_digits=15, decimal_places=2, editable=False)
    received_quantity = models.DecimalField(_("Received Quantity"), max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Purchase Order Line")
        verbose_name_plural = _("Purchase Order Lines")

    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SalesOrder(models.Model):
    """Sales order from customer"""
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('confirmed', _('Confirmed')),
        ('in_production', _('In Production')),
        ('ready', _('Ready to Ship')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
    ]

    so_number = models.CharField(_("SO Number"), max_length=100, unique=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='sales_orders',
        verbose_name=_("Customer")
    )
    order_date = models.DateField(_("Order Date"), default=timezone.now)
    delivery_date = models.DateField(_("Requested Delivery Date"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(_("Total Amount"), max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sos',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Sales Order")
        verbose_name_plural = _("Sales Orders")
        ordering = ['-order_date', '-so_number']

    def __str__(self):
        return f"{self.so_number} - {self.customer.name}"


class SalesOrderLine(models.Model):
    """Sales order line items"""
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_("Sales Order")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='so_lines',
        verbose_name=_("Product")
    )
    quantity = models.DecimalField(_("Quantity"), max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(_("Unit Price"), max_digits=15, decimal_places=2)
    total_price = models.DecimalField(_("Total Price"), max_digits=15, decimal_places=2, editable=False)
    shipped_quantity = models.DecimalField(_("Shipped Quantity"), max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Sales Order Line")
        verbose_name_plural = _("Sales Order Lines")

    def __str__(self):
        return f"{self.sales_order.so_number} - {self.product.name}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """Invoice for sales orders"""
    INVOICE_TYPES = [
        ('sales', _('Sales Invoice')),
        ('purchase', _('Purchase Invoice')),
    ]

    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('sent', _('Sent')),
        ('paid', _('Paid')),
        ('overdue', _('Overdue')),
        ('cancelled', _('Cancelled')),
    ]

    invoice_number = models.CharField(_("Invoice Number"), max_length=100, unique=True)
    invoice_type = models.CharField(_("Invoice Type"), max_length=20, choices=INVOICE_TYPES)
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_("Sales Order")
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        verbose_name=_("Purchase Order")
    )
    invoice_date = models.DateField(_("Invoice Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(_("Subtotal"), max_digits=15, decimal_places=2, default=0)
    tax = models.DecimalField(_("Tax"), max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(_("Total"), max_digits=15, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)

    class Meta:
        verbose_name = _("Invoice")
        verbose_name_plural = _("Invoices")
        ordering = ['-invoice_date', '-invoice_number']

    def __str__(self):
        return f"{self.invoice_number} - {self.get_invoice_type_display()}"

    @property
    def balance(self):
        return self.total - self.paid_amount


class Payment(models.Model):
    """Payment records"""
    PAYMENT_METHODS = [
        ('cash', _('Cash')),
        ('bank_transfer', _('Bank Transfer')),
        ('credit_card', _('Credit Card')),
        ('check', _('Check')),
        ('other', _('Other')),
    ]

    payment_number = models.CharField(_("Payment Number"), max_length=100, unique=True)
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_("Invoice")
    )
    payment_date = models.DateField(_("Payment Date"), default=timezone.now)
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2, validators=[MinValueValidator(0)])
    payment_method = models.CharField(_("Payment Method"), max_length=20, choices=PAYMENT_METHODS)
    reference = models.CharField(_("Reference"), max_length=200, blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    created_by = models.ForeignKey(
        'core.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_("Created By")
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-payment_date', '-payment_number']

    def __str__(self):
        return f"{self.payment_number} - {self.amount}"