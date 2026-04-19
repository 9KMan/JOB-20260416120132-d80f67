# Boston AI Life Sciences ERP System

A comprehensive Flask-based Enterprise Resource Planning (ERP) system designed for manufacturing and distribution businesses. Built for Boston AI Life Sciences Startup.

## Features

### Modules

1. **Procurement Module**
   - Supplier management
   - Purchase order creation and tracking
   - Material inventory management

2. **Goods Receiving Module**
   - Inbound shipment processing
   - Quality control checks
   - Warehouse receipt management
   - Automatic stock updates

3. **Production Module**
   - Production order management
   - Bill of Materials (BOM)
   - Material requirements planning
   - Work order tracking

4. **Packaging Module**
   - Packaging order management
   - Packaging material tracking
   - Batch processing

5. **Sales Module**
   - Customer management
   - Sales order processing
   - Inventory allocation
   - Invoice generation

6. **Financial Module**
   - Accounts payable/receivable
   - Payment processing
   - Journal entries
   - Basic accounting (balance sheet, income statement)

7. **Reporting Module**
   - Dashboard with KPIs
   - Inventory reports
   - Sales analytics
   - Financial reports

## Tech Stack

- **Backend**: Flask 2.3, Python 3.11
- **Database**: PostgreSQL 15 with SQLAlchemy ORM
- **Authentication**: Flask-Login, Flask-Bcrypt
- **API**: RESTful JSON API
- **Container**: Docker, Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Docker & Docker Compose (optional)

### Installation

1. **Clone and setup:**
   ```bash
   cd erp-system
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   export DATABASE_URL="postgresql://erp_user:erp_password@localhost:5432/erp_database"
   export SECRET_KEY="your-secret-key-here"
   ```

3. **Initialize database:**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

### Using Docker

```bash
docker-compose up -d
```

The application will be available at http://localhost:5000

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user

### Procurement
- `GET /procurement/suppliers` - List suppliers
- `POST /procurement/suppliers` - Create supplier
- `GET /procurement/purchase-orders` - List purchase orders
- `POST /procurement/purchase-orders` - Create purchase order
- `GET /procurement/materials` - List materials

### Goods Receiving
- `GET /goods-receiving/goods-receipts` - List receipts
- `POST /goods-receiving/goods-receipts` - Create receipt
- `POST /goods-receiving/goods-receipts/<id>/complete` - Complete receipt

### Production
- `GET /production/production-orders` - List orders
- `POST /production/production-orders` - Create order
- `POST /production/production-orders/<id>/issue-materials` - Issue materials

### Packaging
- `GET /packaging/packaging-orders` - List orders
- `POST /packaging/packaging-orders` - Create order

### Sales
- `GET /sales/customers` - List customers
- `POST /sales/customers` - Create customer
- `GET /sales/sales-orders` - List orders
- `POST /sales/sales-orders` - Create order
- `POST /sales/sales-orders/<id>/ship` - Ship order

### Financial
- `GET /financial/invoices` - List invoices
- `POST /financial/payments` - Record payment
- `GET /financial/journal-entries` - List journal entries
- `POST /financial/journal-entries` - Create journal entry
- `GET /financial/accounts/balance-sheet` - Balance sheet

### Reporting
- `GET /reporting/dashboard` - Dashboard KPIs
- `GET /reporting/reports/inventory` - Inventory report
- `GET /reporting/reports/sales` - Sales report
- `GET /reporting/reports/financial/income-statement` - Income statement

## Database Schema

The system uses the following main tables:
- `users` - User authentication
- `suppliers` - Vendor/supplier information
- `customers` - Customer information
- `materials` - Raw material inventory
- `products` - Finished product catalog
- `warehouses` - Warehouse locations
- `stocks` - Current inventory levels
- `purchase_orders` - PO header information
- `purchase_order_items` - PO line items
- `goods_receipts` - Inbound receipts
- `production_orders` - Manufacturing orders
- `sales_orders` - Sales order headers
- `invoices` - Financial invoices
- `payments` - Payment records
- `journal_entries` - Accounting entries

## Testing

```bash
pytest tests/ -v
```

## Development

The project uses:
- Black for code formatting
- Flake8 for linting

```bash
black app/
flake8 app/
```

## License

Proprietary - Boston AI Life Sciences Startup
