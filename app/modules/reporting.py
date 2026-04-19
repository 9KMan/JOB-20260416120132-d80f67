"""Reporting module for generating various business reports."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import (
    PurchaseOrder, SalesOrder, ProductionOrder, Stock,
    Invoice, Payment, JournalEntry, JournalEntryLine,
    Supplier, Customer, Product, Material, Warehouse
)
from datetime import datetime, timedelta
from sqlalchemy import func

reporting_bp = Blueprint('reporting', __name__)


# Dashboard / KPI endpoints
@reporting_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """Get dashboard overview with KPIs."""
    today = datetime.now().date()

    # Count queries
    pending_suppliers = Supplier.query.filter_by(is_active=True).count()
    active_customers = Customer.query.filter_by(is_active=True).count()

    # Order counts
    pending_po = PurchaseOrder.query.filter(PurchaseOrder.status.in_(['draft', 'submitted', 'approved'])).count()
    pending_so = SalesOrder.query.filter(SalesOrder.status.in_(['draft', 'confirmed'])).count()
    active_production = ProductionOrder.query.filter_by(status='in_progress').count()

    # Financial summary (posted invoices)
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.invoice_type == 'sales',
        Invoice.status == 'paid'
    ).scalar() or 0

    total_receivable = db.session.query(func.sum(Invoice.total_amount - Invoice.amount_paid)).filter(
        Invoice.invoice_type == 'sales',
        Invoice.status.in_(['issued', 'overdue'])
    ).scalar() or 0

    # Low stock alerts
    low_stock = db.session.query(Stock).filter(
        Stock.quantity < Stock.item_type  # Simplified check
    ).limit(10).all()

    low_stock_alerts = [{
        'item_type': s.item_type,
        'item_id': s.item_id,
        'quantity': float(s.quantity),
        'warehouse': s.warehouse.name if s.warehouse else None
    } for s in low_stock]

    return jsonify({
        'dashboard': {
            'pending_suppliers': pending_suppliers,
            'active_customers': active_customers,
            'pending_purchase_orders': pending_po,
            'pending_sales_orders': pending_so,
            'active_production_orders': active_production,
            'total_revenue': float(total_revenue),
            'total_receivable': float(total_receivable),
            'low_stock_alerts': low_stock_alerts
        }
    }), 200


# Inventory reports
@reporting_bp.route('/reports/inventory', methods=['GET'])
@login_required
def get_inventory_report():
    """Get inventory status report."""
    warehouse_id = request.args.get('warehouse_id')

    query = Stock.query
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)

    stocks = query.all()

    inventory = []
    for stock in stocks:
        item_name = stock.material.name if stock.item_type == 'material' else stock.product.name
        item_code = stock.material.code if stock.item_type == 'material' else stock.product.code

        inventory.append({
            'item_type': stock.item_type,
            'item_id': stock.item_id,
            'item_code': item_code,
            'item_name': item_name,
            'warehouse': stock.warehouse.name if stock.warehouse else None,
            'quantity': float(stock.quantity),
            'reserved': float(stock.reserved_quantity),
            'available': float(stock.available_quantity),
            'unit_cost': float(stock.unit_cost),
            'total_value': float(stock.total_value)
        })

    return jsonify({'inventory': inventory}), 200


@reporting_bp.route('/reports/inventory/valuation', methods=['GET'])
@login_required
def get_inventory_valuation():
    """Get inventory valuation report."""
    stocks = Stock.query.all()

    total_value = 0
    materials_value = 0
    products_value = 0

    material_items = []
    product_items = []

    for stock in stocks:
        value = float(stock.total_value)
        total_value += value

        if stock.item_type == 'material':
            materials_value += value
            material_items.append({
                'item_code': stock.material.code,
                'item_name': stock.material.name,
                'quantity': float(stock.quantity),
                'unit_cost': float(stock.unit_cost),
                'total_value': value
            })
        else:
            products_value += value
            product_items.append({
                'item_code': stock.product.code,
                'item_name': stock.product.name,
                'quantity': float(stock.quantity),
                'unit_cost': float(stock.unit_cost),
                'total_value': value
            })

    return jsonify({
        'inventory_valuation': {
            'total_value': total_value,
            'materials_value': materials_value,
            'products_value': products_value,
            'materials': material_items,
            'products': product_items
        }
    }), 200


# Sales reports
@reporting_bp.route('/reports/sales', methods=['GET'])
@login_required
def get_sales_report():
    """Get sales report."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = SalesOrder.query
    if start_date:
        query = query.filter(SalesOrder.order_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(SalesOrder.order_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    orders = query.order_by(SalesOrder.order_date.desc()).all()

    total_amount = sum(float(o.total_amount) for o in orders)
    total_paid = sum(float(o.total_amount) for o in orders if o.payment_status == 'paid')

    return jsonify({
        'sales_report': {
            'period_start': start_date,
            'period_end': end_date,
            'total_orders': len(orders),
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_outstanding': total_amount - total_paid,
            'orders': [{
                'order_number': o.order_number,
                'customer': o.customer.name,
                'order_date': o.order_date.isoformat() if o.order_date else None,
                'total_amount': float(o.total_amount),
                'status': o.status,
                'payment_status': o.payment_status
            } for o in orders]
        }
    }), 200


@reporting_bp.route('/reports/sales/by-customer', methods=['GET'])
@login_required
def get_sales_by_customer():
    """Get sales breakdown by customer."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = db.session.query(
        Customer.id,
        Customer.code,
        Customer.name,
        func.count(SalesOrder.id).label('order_count'),
        func.sum(SalesOrder.total_amount).label('total_amount')
    ).join(SalesOrder).group_by(Customer.id)

    if start_date:
        query = query.filter(SalesOrder.order_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(SalesOrder.order_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    results = query.all()

    return jsonify({
        'sales_by_customer': [{
            'customer_id': r.id,
            'customer_code': r.code,
            'customer_name': r.name,
            'order_count': r.order_count,
            'total_amount': float(r.total_amount or 0)
        } for r in results]
    }), 200


@reporting_bp.route('/reports/sales/by-product', methods=['GET'])
@login_required
def get_sales_by_product():
    """Get sales breakdown by product."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = db.session.query(
        Product.id,
        Product.code,
        Product.name,
        func.sum(SalesOrderItem.quantity).label('quantity_sold'),
        func.sum(SalesOrderItem.total).label('total_revenue')
    ).join(SalesOrderItem).join(SalesOrder)

    if start_date:
        query = query.filter(SalesOrder.order_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(SalesOrder.order_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    query = query.group_by(Product.id)

    results = query.all()

    return jsonify({
        'sales_by_product': [{
            'product_id': r.id,
            'product_code': r.code,
            'product_name': r.name,
            'quantity_sold': float(r.quantity_sold or 0),
            'total_revenue': float(r.total_revenue or 0)
        } for r in results]
    }), 200


# Purchase reports
@reporting_bp.route('/reports/purchases', methods=['GET'])
@login_required
def get_purchase_report():
    """Get purchase report."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = PurchaseOrder.query
    if start_date:
        query = query.filter(PurchaseOrder.order_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(PurchaseOrder.order_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

    orders = query.order_by(PurchaseOrder.order_date.desc()).all()

    total_amount = sum(float(o.total_amount) for o in orders)

    return jsonify({
        'purchase_report': {
            'period_start': start_date,
            'period_end': end_date,
            'total_orders': len(orders),
            'total_amount': total_amount,
            'orders': [{
                'order_number': o.order_number,
                'supplier': o.supplier.name,
                'order_date': o.order_date.isoformat() if o.order_date else None,
                'total_amount': float(o.total_amount),
                'status': o.status
            } for o in orders]
        }
    }), 200


# Production reports
@reporting_bp.route('/reports/production', methods=['GET'])
@login_required
def get_production_report():
    """Get production report."""
    status = request.args.get('status')

    query = ProductionOrder.query
    if status:
        query = query.filter_by(status=status)

    orders = query.order_by(ProductionOrder.created_at.desc()).all()

    return jsonify({
        'production_report': {
            'total_orders': len(orders),
            'orders': [{
                'order_number': o.order_number,
                'product': o.product.name,
                'quantity': float(o.quantity),
                'order_date': o.order_date.isoformat() if o.order_date else None,
                'scheduled_start': o.scheduled_start_date.isoformat() if o.scheduled_start_date else None,
                'scheduled_end': o.scheduled_end_date.isoformat() if o.scheduled_end_date else None,
                'actual_start': o.actual_start_date.isoformat() if o.actual_start_date else None,
                'actual_end': o.actual_end_date.isoformat() if o.actual_end_date else None,
                'status': o.status
            } for o in orders]
        }
    }), 200


# Financial reports
@reporting_bp.route('/reports/financial/income-statement', methods=['GET'])
@login_required
def get_income_statement():
    """Get income statement."""
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).date().isoformat())
    end_date = request.args.get('end_date', datetime.now().date().isoformat())

    # Calculate revenue from paid invoices
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.invoice_type == 'sales',
        Invoice.status == 'paid',
        Invoice.invoice_date >= datetime.strptime(start_date, '%Y-%m-%d').date(),
        Invoice.invoice_date <= datetime.strptime(end_date, '%Y-%m-%d').date()
    ).scalar() or 0

    # Simplified cost - in real system would track COGS
    cost_of_goods_sold = total_revenue * 0.6  # Assume 60% COGS

    gross_profit = total_revenue - cost_of_goods_sold
    operating_expenses = gross_profit * 0.2  # Assume 20% for expenses
    net_income = gross_profit - operating_expenses

    return jsonify({
        'income_statement': {
            'period_start': start_date,
            'period_end': end_date,
            'revenue': float(total_revenue),
            'cost_of_goods_sold': float(cost_of_goods_sold),
            'gross_profit': float(gross_profit),
            'operating_expenses': float(operating_expenses),
            'net_income': float(net_income)
        }
    }), 200


@reporting_bp.route('/reports/financial/accounts-receivable', methods=['GET'])
@login_required
def get_accounts_receivable():
    """Get aging accounts receivable report."""
    invoices = Invoice.query.filter(
        Invoice.invoice_type == 'sales',
        Invoice.status.in_(['issued', 'overdue']),
        Invoice.amount_paid < Invoice.total_amount
    ).all()

    today = datetime.now().date()
    aging = {'current': 0, '30_days': 0, '60_days': 0, '90+_days': 0}

    receivable_list = []
    for inv in invoices:
        balance = float(inv.total_amount - inv.amount_paid)
        days_old = (today - inv.invoice_date).days if inv.invoice_date else 0

        if days_old <= 30:
            aging['current'] += balance
        elif days_old <= 60:
            aging['30_days'] += balance
        elif days_old <= 90:
            aging['60_days'] += balance
        else:
            aging['90+_days'] += balance

        receivable_list.append({
            'invoice_number': inv.invoice_number,
            'customer': inv.customer.name if inv.customer else None,
            'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
            'due_date': inv.due_date.isoformat() if inv.due_date else None,
            'total_amount': float(inv.total_amount),
            'balance': balance,
            'days_old': days_old
        })

    return jsonify({
        'accounts_receivable': {
            'aging': aging,
            'total_receivable': sum(aging.values()),
            'invoices': receivable_list
        }
    }), 200


@reporting_bp.route('/reports/financial/trial-balance', methods=['GET'])
@login_required
def get_trial_balance():
    """Get trial balance report."""
    accounts = {}

    entries = JournalEntry.query.filter_by(is_posted=True).all()
    for entry in entries:
        for line in entry.lines:
            code = line.account_code
            if code not in accounts:
                accounts[code] = {
                    'account_code': code,
                    'account_name': line.account_name,
                    'debit': 0,
                    'credit': 0
                }

            accounts[code]['debit'] += float(line.debit)
            accounts[code]['credit'] += float(line.credit)

    # Calculate balances
    account_list = []
    for code, acc in sorted(accounts.items()):
        balance = acc['debit'] - acc['credit']
        account_list.append({
            'account_code': code,
            'account_name': acc['account_name'],
            'debit': acc['debit'],
            'credit': acc['credit'],
            'balance': balance
        })

    total_debits = sum(a['debit'] for a in account_list)
    total_credits = sum(a['credit'] for a in account_list)

    return jsonify({
        'trial_balance': {
            'accounts': account_list,
            'total_debits': total_debits,
            'total_credits': total_credits,
            'is_balanced': abs(total_debits - total_credits) < 0.01
        }
    }), 200
