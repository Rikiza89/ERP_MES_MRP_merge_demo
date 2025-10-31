"""
Management command to seed sample data for testing
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from core.models import Company, Department, Employee, UserProfile
from erp.models import (ProductCategory, Product, Supplier, Customer, 
                        PurchaseOrder, PurchaseOrderLine, SalesOrder, SalesOrderLine,
                        Invoice, Payment)
from mes.models import ProductionLine, Shift, Machine, WorkOrder, ProductionLog, QualityCheck, Downtime
from mrp.models import Material, BOM, BOMLine, Inventory, ReorderRule, StockMovement, PurchaseRequest


class Command(BaseCommand):
    help = 'Seed database with sample data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data seeding...')
        
        # Create superuser
        self.create_users()
        
        # Core data
        self.create_core_data()
        
        # ERP data
        self.create_erp_data()
        
        # MES data
        self.create_mes_data()
        
        # MRP data
        self.create_mrp_data()
        
        self.stdout.write(self.style.SUCCESS('Data seeding completed!'))
    
    def create_users(self):
        self.stdout.write('Creating users...')
        
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@factory.com',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user'))
    
    def create_core_data(self):
        self.stdout.write('Creating core data...')
        
        # Company
        company = Company.objects.create(
            name='Smart Factory Inc.',
            code='SF001',
            address='123 Industrial Ave, Tokyo, Japan',
            phone='+81-3-1234-5678',
            email='info@smartfactory.jp'
        )
        
        # Departments
        production_dept = Department.objects.create(
            company=company,
            name='Production',
            code='PROD'
        )
        
        quality_dept = Department.objects.create(
            company=company,
            name='Quality Control',
            code='QC'
        )
        
        # Employees
        employees = [
            ('EMP001', 'John', 'Tanaka', 'john.tanaka@factory.com', 'manager', production_dept, '04001A2B3C4D'),
            ('EMP002', 'Sarah', 'Yamamoto', 'sarah.yamamoto@factory.com', 'operator', production_dept, '04005E6F7G8H'),
            ('EMP003', 'Mike', 'Suzuki', 'mike.suzuki@factory.com', 'operator', production_dept, '0400123456AB'),
            ('EMP004', 'Emily', 'Nakamura', 'emily.nakamura@factory.com', 'manager', quality_dept, None),
        ]
        
        for emp_id, fname, lname, email, role, dept, nfc in employees:
            Employee.objects.create(
                employee_id=emp_id,
                first_name=fname,
                last_name=lname,
                email=email,
                role=role,
                department=dept,
                nfc_uid=nfc,
                hire_date=timezone.now().date() - timedelta(days=random.randint(30, 365))
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(employees)} employees'))
    
    def create_erp_data(self):
        self.stdout.write('Creating ERP data...')
        
        # Product Categories
        categories = [
            ('CAT001', 'Electronics'),
            ('CAT002', 'Mechanical Parts'),
            ('CAT003', 'Packaging Materials'),
        ]
        
        for code, name in categories:
            ProductCategory.objects.create(code=code, name=name)
        
        # Products
        products = [
            ('PRD001', 'Smart Widget A', 'finished', 150.00, 80.00, 'pcs'),
            ('PRD002', 'Smart Widget B', 'finished', 200.00, 120.00, 'pcs'),
            ('PRD003', 'Component X', 'component', 25.00, 15.00, 'pcs'),
            ('PRD004', 'Component Y', 'component', 30.00, 18.00, 'pcs'),
            ('PRD005', 'Premium Widget C', 'finished', 300.00, 180.00, 'pcs'),
        ]
        
        cat = ProductCategory.objects.first()
        for prd_num, name, prd_type, price, cost, unit in products:
            Product.objects.create(
                product_number=prd_num,
                name=name,
                category=cat,
                product_type=prd_type,
                price=Decimal(str(price)),
                cost=Decimal(str(cost)),
                unit=unit,
                min_stock=Decimal('10'),
                max_stock=Decimal('100')
            )
        
        # Suppliers
        suppliers = [
            ('SUP001', 'Tokyo Electronics Co.'),
            ('SUP002', 'Osaka Parts Ltd.'),
            ('SUP003', 'Kyoto Materials Inc.'),
        ]
        
        for code, name in suppliers:
            Supplier.objects.create(
                supplier_code=code,
                name=name,
                email=f'{code.lower()}@supplier.com',
                phone='+81-3-9999-0000'
            )
        
        # Customers
        customers = [
            ('CUST001', 'ABC Corporation', 100000),
            ('CUST002', 'XYZ Industries', 150000),
            ('CUST003', 'Global Manufacturing Ltd.', 200000),
        ]
        
        for code, name, credit in customers:
            Customer.objects.create(
                customer_code=code,
                name=name,
                email=f'{code.lower()}@customer.com',
                phone='+81-3-8888-0000',
                credit_limit=Decimal(str(credit))
            )
        
        # Create Sales Orders for this month
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        customers_list = list(Customer.objects.all())
        products_list = list(Product.objects.filter(product_type='finished'))
        employee = Employee.objects.first()
        
        # Create 5-10 sales orders this month
        for i in range(random.randint(5, 10)):
            customer = random.choice(customers_list)
            order_date = month_start + timedelta(days=random.randint(0, today.day - 1))
            
            so = SalesOrder.objects.create(
                so_number=f'SO-{today.strftime("%Y%m")}-{str(i+1).zfill(3)}',
                customer=customer,
                order_date=order_date,
                delivery_date=order_date + timedelta(days=random.randint(7, 30)),
                status=random.choice(['confirmed', 'in_production', 'ready', 'shipped']),
                total_amount=Decimal('0'),
                created_by=employee
            )
            
            # Add line items
            total = Decimal('0')
            num_lines = random.randint(1, 3)
            for j in range(num_lines):
                product = random.choice(products_list)
                qty = Decimal(str(random.randint(10, 100)))
                unit_price = product.price
                
                SalesOrderLine.objects.create(
                    sales_order=so,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    shipped_quantity=Decimal('0')
                )
                total += qty * unit_price
            
            so.total_amount = total
            so.save()
            
            # Create invoices for confirmed/shipped orders
            if so.status in ['shipped', 'ready']:
                invoice = Invoice.objects.create(
                    invoice_number=f'INV-{today.strftime("%Y%m")}-{str(i+1).zfill(3)}',
                    invoice_type='sales',
                    sales_order=so,
                    invoice_date=so.order_date + timedelta(days=random.randint(1, 5)),
                    due_date=so.order_date + timedelta(days=30),
                    status=random.choice(['sent', 'paid']),
                    subtotal=total,
                    tax=total * Decimal('0.1'),
                    total=total * Decimal('1.1'),
                    paid_amount=total * Decimal('1.1') if random.choice([True, False]) else Decimal('0')
                )
                
                # Create payment for paid invoices
                if invoice.status == 'paid':
                    Payment.objects.create(
                        payment_number=f'PAY-{today.strftime("%Y%m")}-{str(i+1).zfill(3)}',
                        invoice=invoice,
                        payment_date=invoice.invoice_date + timedelta(days=random.randint(1, 14)),
                        amount=invoice.total,
                        payment_method=random.choice(['bank_transfer', 'credit_card', 'check']),
                        created_by=employee
                    )
        
        # Create Purchase Orders
        supplier = Supplier.objects.first()
        for i in range(random.randint(3, 6)):
            po_date = month_start + timedelta(days=random.randint(0, today.day - 1))
            
            po = PurchaseOrder.objects.create(
                po_number=f'PO-{today.strftime("%Y%m")}-{str(i+1).zfill(3)}',
                supplier=supplier,
                order_date=po_date,
                expected_date=po_date + timedelta(days=random.randint(7, 14)),
                status=random.choice(['sent', 'confirmed', 'received']),
                total_amount=Decimal('0'),
                created_by=employee
            )
            
            # Add line items (components/materials)
            total = Decimal('0')
            components = Product.objects.filter(product_type='component')
            for product in random.sample(list(components), min(2, len(components))):
                qty = Decimal(str(random.randint(50, 200)))
                unit_price = product.cost
                
                PurchaseOrderLine.objects.create(
                    purchase_order=po,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    received_quantity=qty if po.status == 'received' else Decimal('0')
                )
                total += qty * unit_price
            
            po.total_amount = total
            po.save()
        
        self.stdout.write(self.style.SUCCESS('Created ERP master data with orders and invoices'))

    
    def create_mes_data(self):
        self.stdout.write('Creating MES data...')
        
        dept = Department.objects.first()
        
        # Production Lines
        lines = ['LINE-A', 'LINE-B', 'LINE-C']
        for line_code in lines:
            ProductionLine.objects.create(
                line_code=line_code,
                name=f'Production {line_code}',
                department=dept,
                capacity=Decimal('50')
            )
        
        # Shifts
        shifts = [
            ('SHIFT-1', 'Morning Shift', '08:00', '16:00'),
            ('SHIFT-2', 'Evening Shift', '16:00', '00:00'),
            ('SHIFT-3', 'Night Shift', '00:00', '08:00'),
        ]
        
        for code, name, start, end in shifts:
            Shift.objects.create(
                shift_code=code,
                name=name,
                start_time=start,
                end_time=end
            )
        
        # Machines
        all_lines = ProductionLine.objects.all()
        machine_counter = 1
        for line in all_lines:
            for i in range(2):  # 2 machines per line
                Machine.objects.create(
                    machine_code=f'MCH{str(machine_counter).zfill(3)}',
                    name=f'Machine {machine_counter} - {line.line_code}',
                    production_line=line,
                    status='operational',
                    last_maintenance=timezone.now().date() - timedelta(days=random.randint(1, 30))
                )
                machine_counter += 1
        
        # Get products and sales orders
        products = list(Product.objects.filter(product_type='finished'))
        sales_orders = list(SalesOrder.objects.all())
        employees = list(Employee.objects.filter(role='operator'))
        shifts_list = list(Shift.objects.all())
        all_lines_list = list(ProductionLine.objects.all())
        
        # Create work orders with COMPLETED status for last 7 days
        wo_counter = 1
        for i in range(7):
            days_ago = 6 - i  # 6, 5, 4, 3, 2, 1, 0 (today)
            work_date = timezone.now() - timedelta(days=days_ago)
            
            # Create 2-4 work orders per day
            for j in range(random.randint(2, 4)):
                line = random.choice(all_lines_list)
                product = random.choice(products)
                so = random.choice(sales_orders) if sales_orders else None
                
                planned_qty = random.randint(50, 200)
                produced_qty = random.randint(int(planned_qty * 0.85), planned_qty)
                rejected_qty = random.randint(0, int(produced_qty * 0.05))
                
                wo = WorkOrder.objects.create(
                    wo_number=f'WO-2024-{str(wo_counter).zfill(4)}',
                    sales_order=so,
                    product=product,
                    production_line=line,
                    planned_quantity=Decimal(str(planned_qty)),
                    produced_quantity=Decimal(str(produced_qty)),
                    rejected_quantity=Decimal(str(rejected_qty)),
                    planned_start=work_date.replace(hour=8, minute=0, second=0, microsecond=0),
                    planned_end=work_date.replace(hour=16, minute=0, second=0, microsecond=0),
                    actual_start=work_date.replace(hour=8, minute=15, second=0, microsecond=0),
                    actual_end=work_date.replace(hour=15, minute=45, second=0, microsecond=0),
                    status='completed',
                    priority=random.randint(1, 10)
                )
                wo_counter += 1
                
                # Create production logs
                if employees and shifts_list:
                    operator = random.choice(employees)
                    shift = random.choice(shifts_list)
                    
                    ProductionLog.objects.create(
                        work_order=wo,
                        operator=operator,
                        shift=shift,
                        action_type='start',
                        timestamp=wo.actual_start,
                        quantity=Decimal('0')
                    )
                    
                    ProductionLog.objects.create(
                        work_order=wo,
                        operator=operator,
                        shift=shift,
                        action_type='stop',
                        timestamp=wo.actual_end,
                        quantity=wo.produced_quantity,
                        rejects=wo.rejected_quantity
                    )
                
                # Create quality checks for some work orders
                if random.choice([True, False]):
                    inspector = Employee.objects.filter(role='manager').first()
                    sample_size = random.randint(10, 30)
                    passed = random.randint(int(sample_size * 0.9), sample_size)
                    failed = sample_size - passed
                    
                    QualityCheck.objects.create(
                        check_number=f'QC-2024-{str(wo_counter).zfill(4)}',
                        work_order=wo,
                        inspector=inspector,
                        check_date=wo.actual_end,
                        sample_size=sample_size,
                        passed=passed,
                        failed=failed,
                        result='pass' if passed >= sample_size * 0.95 else 'conditional'
                    )
        
        # Create some pending/in-progress work orders for future
        for i in range(5):
            line = random.choice(all_lines_list)
            product = random.choice(products)
            so = random.choice(sales_orders) if sales_orders else None
            
            status_choice = ['ready', 'ready', 'in_progress', 'pending', 'pending']
            status = status_choice[i]
            
            wo = WorkOrder.objects.create(
                wo_number=f'WO-2024-{str(wo_counter).zfill(4)}',
                sales_order=so,
                product=product,
                production_line=line,
                planned_quantity=Decimal(str(random.randint(100, 300))),
                produced_quantity=Decimal('50') if status == 'in_progress' else Decimal('0'),
                rejected_quantity=Decimal('0'),
                planned_start=timezone.now() + timedelta(days=i),
                planned_end=timezone.now() + timedelta(days=i+1),
                actual_start=timezone.now() if status == 'in_progress' else None,
                status=status,
                priority=10 - i
            )
            wo_counter += 1
        
        # Create some downtime records
        for i in range(3):
            line = random.choice(all_lines_list)
            machines = list(line.machines.all())
            machine = random.choice(machines) if machines else None
            
            downtime_start = timezone.now() - timedelta(days=random.randint(1, 7), hours=random.randint(1, 8))
            downtime_end = downtime_start + timedelta(minutes=random.randint(30, 240))
            
            Downtime.objects.create(
                production_line=line,
                machine=machine,
                start_time=downtime_start,
                end_time=downtime_end,
                reason=random.choice(['breakdown', 'maintenance', 'material_shortage', 'tool_change']),
                description=f'Sample downtime event {i+1}',
                reported_by=Employee.objects.first()
            )
        
        self.stdout.write(self.style.SUCCESS(f'Created MES data with {wo_counter-1} work orders'))
    
    def create_mrp_data(self):
        self.stdout.write('Creating MRP data...')
        
        supplier = Supplier.objects.first()
        
        # Materials
        materials = [
            ('MAT001', 'Steel Sheet', 'raw', 50.00, 'kg'),
            ('MAT002', 'Plastic Resin', 'raw', 30.00, 'kg'),
            ('MAT003', 'Electronic Board', 'component', 80.00, 'pcs'),
            ('MAT004', 'Cardboard Box', 'packaging', 2.00, 'pcs'),
            ('MAT005', 'Copper Wire', 'raw', 15.00, 'meter'),
        ]
        
        for code, name, mat_type, cost, unit in materials:
            Material.objects.create(
                material_code=code,
                name=name,
                material_type=mat_type,
                unit=unit,
                unit_cost=Decimal(str(cost)),
                lead_time_days=7,
                min_order_quantity=Decimal('10'),
                supplier=supplier
            )
        
        # BOM for each finished product
        products = Product.objects.filter(product_type='finished')
        materials_list = list(Material.objects.all())
        
        for idx, product in enumerate(products):
            bom = BOM.objects.create(
                bom_number=f'BOM-{product.product_number}',
                product=product,
                version='1.0',
                effective_date=timezone.now().date()
            )
            
            # Add 3-4 materials per product
            selected_materials = random.sample(materials_list, min(random.randint(3, 4), len(materials_list)))
            for i, material in enumerate(selected_materials, 1):
                BOMLine.objects.create(
                    bom=bom,
                    line_number=i * 10,
                    material=material,
                    quantity=Decimal(str(random.uniform(1.5, 5.0))),
                    unit=material.unit,
                    scrap_factor=Decimal(str(random.uniform(2, 8)))
                )
        
        # Inventory - Create realistic stock levels
        # Products inventory
        for product in Product.objects.all():
            on_hand = Decimal(str(random.randint(20, 150)))
            reserved = Decimal(str(random.randint(0, int(on_hand * Decimal('0.3')))))
            
            Inventory.objects.create(
                product=product,
                warehouse='Main',
                location=f'A-{str(random.randint(1, 20)).zfill(2)}',
                quantity_on_hand=on_hand,
                quantity_reserved=reserved,
                last_count_date=timezone.now().date() - timedelta(days=random.randint(1, 30))
            )
        
        # Materials inventory - some low stock to trigger alerts
        for idx, material in enumerate(Material.objects.all()):
            # Make some materials low stock
            if idx % 3 == 0:
                on_hand = Decimal(str(random.randint(0, 5)))  # Low stock
            else:
                on_hand = Decimal(str(random.randint(50, 200)))
            
            reserved = Decimal(str(random.randint(0, int(on_hand * Decimal('0.2'))))) if on_hand > 0 else Decimal('0')
            
            Inventory.objects.create(
                material=material,
                warehouse='Main',
                location=f'B-{str(random.randint(1, 30)).zfill(2)}',
                quantity_on_hand=on_hand,
                quantity_reserved=reserved,
                last_count_date=timezone.now().date() - timedelta(days=random.randint(1, 15))
            )
        
        # Stock movements for the past week
        today = timezone.now()
        for i in range(20):
            days_ago = random.randint(0, 7)
            movement_date = today - timedelta(days=days_ago)
            
            movement_type = random.choice(['in', 'out', 'production', 'consumption', 'adjustment'])
            
            if random.choice([True, False]):
                # Product movement
                product = random.choice(list(Product.objects.all()))
                StockMovement.objects.create(
                    movement_number=f'SM-PROD-{today.strftime("%Y%m%d")}-{str(i+1).zfill(3)}',
                    movement_type=movement_type,
                    product=product,
                    to_warehouse='Main' if movement_type == 'in' else None,
                    from_warehouse='Main' if movement_type == 'out' else None,
                    quantity=Decimal(str(random.randint(10, 50))),
                    unit=product.unit,
                    movement_date=movement_date
                )
            else:
                # Material movement
                material = random.choice(list(Material.objects.all()))
                StockMovement.objects.create(
                    movement_number=f'SM-MAT-{today.strftime("%Y%m%d")}-{str(i+1).zfill(3)}',
                    movement_type=movement_type,
                    material=material,
                    to_warehouse='Main' if movement_type == 'in' else None,
                    from_warehouse='Main' if movement_type == 'out' else None,
                    quantity=Decimal(str(random.randint(5, 30))),
                    unit=material.unit,
                    movement_date=movement_date
                )
        
        # Purchase Requests - some pending
        for i in range(random.randint(3, 7)):
            material = random.choice(list(Material.objects.all()))
            required_date = timezone.now().date() + timedelta(days=random.randint(7, 30))
            
            PurchaseRequest.objects.create(
                pr_number=f'PR-{timezone.now().strftime("%Y%m%d")}-{str(i+1).zfill(3)}',
                material=material,
                requested_quantity=Decimal(str(random.randint(50, 200))),
                required_date=required_date,
                status=random.choice(['pending', 'approved', 'draft']),
                requested_by=Employee.objects.first()
            )
        
        # Reorder Rules
        for product in Product.objects.all():
            ReorderRule.objects.create(
                product=product,
                warehouse='Main',
                rule_type='reorder_point',
                min_quantity=product.min_stock,
                max_quantity=product.max_stock,
                reorder_point=Decimal(str(int(product.min_stock) * 1.5)),
                reorder_quantity=Decimal(str(int(product.max_stock) - int(product.min_stock)))
            )
        
        for material in Material.objects.all():
            ReorderRule.objects.create(
                material=material,
                warehouse='Main',
                rule_type='min_max',
                min_quantity=Decimal('20'),
                max_quantity=Decimal('200'),
                reorder_point=Decimal('30'),
                reorder_quantity=Decimal('150')
            )
        
        self.stdout.write(self.style.SUCCESS('Created MRP data with inventory and alerts'))