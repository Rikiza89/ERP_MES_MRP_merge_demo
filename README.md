# ERP+MES+MRP Django System

Complete Django-based manufacturing management system integrating Enterprise Resource Planning (ERP), Manufacturing Execution System (MES), and Material Requirements Planning (MRP).

## Features

### Core System
- Multi-company/department management
- Employee management with role-based access
- Optional NFC card integration for operator login
- Comprehensive audit logging
- Multi-language support (EN/JP)

### ERP Module
- Product catalog management
- Supplier and customer management
- Purchase orders and sales orders
- Invoice and payment tracking
- Inventory value calculation
- Import/export capabilities

### MES Module
- Production line and shift management
- Work order tracking with real-time status
- Machine/equipment management
- Production logging with operator tracking
- Quality inspection records
- Downtime tracking
- Interactive action buttons (Start/Stop/Pause)

### MRP Module
- Material master data
- Bill of Materials (BOM) with multi-level support
- Inventory management
- Stock movement tracking
- Automatic purchase request generation
- Reorder rules
- MRP calculation engine

### Dashboard
- Real-time KPI cards (OEE, production, revenue, etc.)
- Production performance charts
- Inventory alerts
- Recent activity feed
- Quick access links

## Installation

### Requirements
- Python 3.9+
- PostgreSQL 12+
- Django 5.1

### Setup Steps

1. **Clone and navigate to project**
```bash
mkdir erp_mes_mrp_nfc
cd erp_mes_mrp_nfc
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure database**
Edit `config/settings.py` and update DATABASES section with your PostgreSQL credentials.

Create database:
```bash
createdb erp_mes_mrp_db
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Load sample data (optional)**
```bash
python manage.py seed_data
```

8. **Collect static files**
```bash
python manage.py collectstatic --noinput
```

9. **Run development server**
```bash
python manage.py runserver
```

Access admin at: http://localhost:8000/admin/

## Project Structure

```
erp_mes_mrp_nfc/
├── core/              # Core system (Company, Employee, Logging)
├── erp/               # ERP module (Products, Orders, Invoices)
├── mes/               # MES module (Production, Quality, Machines)
├── mrp/               # MRP module (Materials, BOM, Inventory)
├── dashboard/         # Analytics and KPI dashboard
├── templates/admin/   # Custom admin templates
├── static/            # CSS, JavaScript, images
└── config/            # Django settings and URLs
```

## Usage Guide

### Creating a Work Order

1. Navigate to **Sales Orders** → Create new sales order
2. Go to **Work Orders** → Add new work order
3. Select product, production line, and quantities
4. Set status to "Ready"
5. Use action buttons to Start/Stop/Pause

### Running MRP Calculation

```python
from mrp.utils import MRPCalculator

calculator = MRPCalculator(run_by=employee)
success, calculation = calculator.run_calculation()
```

Or create a management command:
```bash
python manage.py run_mrp_calculation
```

### NFC Integration (Optional)

Enable NFC in settings:
```python
NFC_ENABLED = True
```

Register employee NFC UIDs in employee records. When operators scan their card:
- System logs them in automatically
- Can start/stop work orders with NFC scan
- All actions are logged

### Admin Customization

All admin interfaces include:
- Color-coded status indicators
- Progress bars for work orders
- Inline action buttons
- Custom filters and search
- Export functionality

## API Endpoints

Dashboard APIs:
- `/dashboard/api/kpis/` - KPI data
- `/dashboard/api/production-chart/` - Production charts
- `/dashboard/api/inventory-status/` - Inventory alerts

## Configuration

### Environment Variables

Create `.env` file:
```
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
NFC_ENABLED=False
```

### Localization

Add translations:
```bash
python manage.py makemessages -l ja
python manage.py compilemessages
```

## Testing

Run tests:
```bash
python manage.py test
```

## Production Deployment

1. Set `DEBUG = False`
2. Configure proper SECRET_KEY
3. Set up PostgreSQL with proper credentials
4. Use gunicorn/uwsgi for WSGI server
5. Set up nginx for static files
6. Configure SSL certificates
7. Set up regular backups

Example with gunicorn:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Key Models

### Core
- `Company`, `Department`, `Employee`
- `UserProfile` (with NFC UID)
- `LogData` (universal logger)

### ERP
- `Product`, `ProductCategory`
- `Supplier`, `Customer`
- `PurchaseOrder`, `SalesOrder`
- `Invoice`, `Payment`

### MES
- `ProductionLine`, `Shift`, `Machine`
- `WorkOrder`, `ProductionLog`
- `QualityCheck`, `Downtime`

### MRP
- `Material`, `BOM`, `BOMLine`
- `Inventory`, `StockMovement`
- `PurchaseRequest`, `ReorderRule`

## Default Credentials

After running `seed_data`:
- Username: `admin`
- Password: `admin123`

**Change immediately in production!**

## License

Proprietary - Internal Use Only

## Support

For issues or questions, contact the development team.