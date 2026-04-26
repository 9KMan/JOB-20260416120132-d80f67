# Boston AI Life Sciences - AI Platform

A comprehensive FastAPI-based AI Platform with enterprise ERP capabilities. Built for Boston AI Life Sciences Startup - Senior Python/FastAPI Engineer position.

## Features

### AI Platform Core
- **LLM Integration**: OpenAI GPT-4, Anthropic Claude support via LangChain
- **Agent Framework**: Custom AI agents with tool access and reasoning
- **Supabase Backend**: Real-time database with PostgREST API
- **SMS Notifications**: Twilio integration for alerts and updates

### Enterprise Modules (Flask Legacy)

The system includes a complete Flask-based ERP system:

1. **Procurement Module** - Supplier management, purchase orders, material inventory
2. **Goods Receiving Module** - Inbound shipment processing, quality control
3. **Production Module** - Production orders, BOM, material requirements planning
4. **Packaging Module** - Packaging orders, material tracking, batch processing
5. **Sales Module** - Customer management, sales orders, invoice generation
6. **Financial Module** - Accounts payable/receivable, journal entries
7. **Reporting Module** - Dashboard KPIs, inventory/sales/financial reports

## Tech Stack

- **Backend**: FastAPI 0.109 + Flask 2.3 (dual stack)
- **Database**: PostgreSQL 15 with asyncpg, SQLAlchemy 2.0
- **AI/LLM**: LangChain, OpenAI, Anthropic
- **Backend-as-a-Service**: Supabase
- **SMS**: Twilio
- **Container**: Docker, Docker Compose
- **Python**: 3.11+

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or Docker)
- Docker & Docker Compose (optional)
- API keys: OpenAI, Anthropic, Supabase, Twilio (for full features)

### Installation

1. **Clone and setup:**
```bash
cd erp-system
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
export DATABASE_URL="postgresql+asyncpg://erp_user:erp_password@localhost:5432/erp_database"
export SECRET_KEY="your-secret-key-here"
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="eyJ..."
```

3. **Initialize database:**
```bash
alembic upgrade head
```

4. **Run the FastAPI application:**
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Or run the Flask application (legacy):**
```bash
python run.py
```

### Using Docker

```bash
docker-compose up -d
```

The FastAPI application will be available at http://localhost:8000
API documentation at http://localhost:8000/docs

## API Endpoints

### AI Platform (FastAPI)

#### LLM Integration
- `POST /api/llm/chat` - Chat completion with OpenAI/Anthropic
- `POST /api/llm/agent` - Create AI agent with tools
- `GET /api/llm/models` - List available models

#### AI Agents
- `POST /api/agents` - Create new agent
- `GET /api/agents/{id}` - Get agent details
- `POST /api/agents/{id}/execute` - Execute agent task
- `GET /api/agents/{id}/history` - Get conversation history

#### Supabase Integration
- `POST /api/supabase/query` - Execute Supabase query
- `GET /api/supabase/tables` - List available tables

#### SMS Notifications (Twilio)
- `POST /api/notifications/sms` - Send SMS notification
- `GET /api/notifications/sms/status/{sid}` - Check SMS delivery status

### Legacy ERP Endpoints (Flask)

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/register` - User registration
- `GET /auth/me` - Get current user

#### Procurement
- `GET /procurement/suppliers` - List suppliers
- `POST /procurement/suppliers` - Create supplier
- `GET /procurement/purchase-orders` - List purchase orders
- `POST /procurement/purchase-orders` - Create purchase order
- `GET /procurement/materials` - List materials

#### Goods Receiving
- `GET /goods-receiving/goods-receipts` - List receipts
- `POST /goods-receiving/goods-receipts` - Create receipt
- `POST /goods-receiving/goods-receipts/<id>/complete` - Complete receipt

#### Production
- `GET /production/production-orders` - List orders
- `POST /production/production-orders` - Create order
- `POST /production/production-orders/<id>/issue-materials` - Issue materials

#### Packaging
- `GET /packaging/packaging-orders` - List orders
- `POST /packaging/packaging-orders` - Create order

#### Sales
- `GET /sales/customers` - List customers
- `POST /sales/customers` - Create customer
- `GET /sales/sales-orders` - List orders
- `POST /sales/sales-orders` - Create order
- `POST /sales/sales-orders/<id>/ship` - Ship order

#### Financial
- `GET /financial/invoices` - List invoices
- `POST /financial/payments` - Record payment
- `GET /financial/journal-entries` - List journal entries
- `POST /financial/journal-entries` - Create journal entry
- `GET /financial/accounts/balance-sheet` - Balance sheet

#### Reporting
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
- `ai_agents` - AI agent configurations
- `ai_conversations` - Agent conversation history

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

## Development

The project uses:
- Black for code formatting
- Flake8 for linting
- mypy for type checking

```bash
black app/ api/
flake8 app/ api/
mypy app/ api/
```

## Project Structure

```
erp-system/
├── api/                    # FastAPI application
│   └── main.py            # FastAPI entry point
├── app/                    # Flask application (legacy)
│   ├── __init__.py        # Flask app factory
│   ├── models/            # SQLAlchemy models
│   ├── modules/           # Flask blueprints
│   ├── static/            # Static assets
│   └── templates/         # Jinja templates
├── migrations/             # Alembic migrations
├── tests/                  # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── run.py                  # Flask entry point
```

## License

Proprietary - Boston AI Life Sciences Startup
