"""Sales module for managing customers and sales orders."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import Customer, SalesOrder, SalesOrderItem, Product, Stock, Invoice
from datetime import datetime
import uuid

sales_bp = Blueprint('sales', __name__)


def generate_so_number():
    """Generate unique sales order number."""
    return f'SO-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


def generate_invoice_number():
    """Generate unique invoice number."""
    return f'INV-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


# Customer endpoints
@sales_bp.route('/customers', methods=['GET'])
@login_required
def get_customers():
    """Get all customers."""
    customers = Customer.query.filter_by(is_active=True).all()
    return jsonify({
        'customers': [{
            'id': c.id,
            'code': c.code,
            'name': c.name,
            'contact_person': c.contact_person,
            'email': c.email,
            'phone': c.phone,
            'address': c.address,
            'city': c.city,
            'country': c.country,
            'credit_limit': float(c.credit_limit),
            'payment_terms': c.payment_terms
        } for c in customers]
    }), 200


@sales_bp.route('/customers', methods=['POST'])
@login_required
def create_customer():
    """Create a new customer."""
    data = request.get_json()

    required = ['code', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Code and name are required'}), 400

    if Customer.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Customer code already exists'}), 409

    customer = Customer(
        code=data['code'],
        name=data['name'],
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        city=data.get('city'),
        country=data.get('country'),
        tax_id=data.get('tax_id'),
        credit_limit=data.get('credit_limit', 0),
        payment_terms=data.get('payment_terms')
    )

    db.session.add(customer)
    db.session.commit()

    return jsonify({
        'message': 'Customer created successfully',
        'customer': {
            'id': customer.id,
            'code': customer.code,
            'name': customer.name
        }
    }), 201


@sales_bp.route('/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    """Get customer by ID."""
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({
        'customer': {
            'id': customer.id,
            'code': customer.code,
            'name': customer.name,
            'contact_person': customer.contact_person,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'city': customer.city,
            'country': customer.country,
            'tax_id': customer.tax_id,
            'credit_limit': float(customer.credit_limit),
            'payment_terms': customer.payment_terms
        }
    }), 200


# Sales Order endpoints
@sales_bp.route('/sales-orders', methods=['GET'])
@login_required
def get_sales_orders():
    """Get all sales orders."""
    orders = SalesOrder.query.order_by(SalesOrder.created_at.desc()).all()
    return jsonify({
        'sales_orders': [{
            'id': so.id,
            'order_number': so.order_number,
            'customer_id': so.customer_id,
            'customer_name': so.customer.name,
            'order_date': so.order_date.isoformat() if so.order_date else None,
            'delivery_date': so.delivery_date.isoformat() if so.delivery_date else None,
            'status': so.status,
            'payment_status': so.payment_status,
            'total_amount': float(so.total_amount),
            'created_at': so.created_at.isoformat()
        } for so in orders]
    }), 200


@sales_bp.route('/sales-orders', methods=['POST'])
@login_required
def create_sales_order():
    """Create a new sales order."""
    data = request.get_json()

    required = ['customer_id', 'order_date', 'items']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    order = SalesOrder(
        order_number=generate_so_number(),
        customer_id=data['customer_id'],
        order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date(),
        delivery_date=datetime.strptime(data['delivery_date'], '%Y-%m-%d').date() if data.get('delivery_date') else None,
        warehouse_id=data.get('warehouse_id'),
        status='draft',
        notes=data.get('notes')
    )

    db.session.add(order)
    db.session.flush()

    for item_data in data['items']:
        product = Product.query.get(item_data['product_id'])
        if not product:
            return jsonify({'error': f"Product {item_data['product_id']} not found"}), 404

        quantity = float(item_data['quantity'])
        unit_price = float(item_data['unit_price'])

        item = SalesOrderItem(
            sales_order_id=order.id,
            product_id=item_data['product_id'],
            quantity=quantity,
            unit_price=unit_price,
            total=quantity * unit_price
        )
        db.session.add(item)

    order.calculate_totals()
    db.session.commit()

    return jsonify({
        'message': 'Sales order created successfully',
        'sales_order': {
            'id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount)
        }
    }), 201


@sales_bp.route('/sales-orders/<int:so_id>', methods=['GET'])
@login_required
def get_sales_order(so_id):
    """Get sales order by ID."""
    order = SalesOrder.query.get_or_404(so_id)

    items = [{
        'id': item.id,
        'product_id': item.product_id,
        'product_code': item.product.code,
        'product_name': item.product.name,
        'quantity': float(item.quantity),
        'unit_price': float(item.unit_price),
        'total': float(item.total),
        'quantity_shipped': float(item.quantity_shipped)
    } for item in order.items]

    return jsonify({
        'sales_order': {
            'id': order.id,
            'order_number': order.order_number,
            'customer_id': order.customer_id,
            'customer_name': order.customer.name,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'delivery_date': order.delivery_date.isoformat() if order.delivery_date else None,
            'warehouse_id': order.warehouse_id,
            'status': order.status,
            'payment_status': order.payment_status,
            'subtotal': float(order.subtotal),
            'tax_amount': float(order.tax_amount),
            'total_amount': float(order.total_amount),
            'notes': order.notes,
            'items': items
        }
    }), 200


@sales_bp.route('/sales-orders/<int:so_id>/status', methods=['PUT'])
@login_required
def update_sales_order_status(so_id):
    """Update sales order status."""
    order = SalesOrder.query.get_or_404(so_id)
    data = request.get_json()

    new_status = data.get('status')
    valid_statuses = ['draft', 'confirmed', 'shipped', 'delivered', 'cancelled']

    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    order.status = new_status
    db.session.commit()

    return jsonify({'message': f'Sales order status updated to {new_status}'}), 200


@sales_bp.route('/sales-orders/<int:so_id>/ship', methods=['POST'])
@login_required
def ship_sales_order(so_id):
    """Ship sales order and deduct from stock."""
    order = SalesOrder.query.get_or_404(so_id)
    data = request.get_json()

    if order.status not in ['draft', 'confirmed']:
        return jsonify({'error': 'Cannot ship order in current status'}), 400

    warehouse_id = data.get('warehouse_id', order.warehouse_id or 1)

    for item_data in data.get('items', []):
        item = SalesOrderItem.query.filter_by(
            id=item_data['id'],
            sales_order_id=so_id
        ).first()

        if not item:
            continue

        quantity_to_ship = float(item_data['quantity'])

        # Check and deduct from stock
        stock = Stock.query.filter_by(
            item_type='product',
            item_id=item.product_id,
            warehouse_id=warehouse_id
        ).first()

        if not stock or stock.available_quantity < quantity_to_ship:
            return jsonify({
                'error': f"Insufficient stock for product {item.product.name}"
            }), 400

        stock.quantity -= quantity_to_ship
        stock.update_available()

        item.quantity_shipped += quantity_to_ship

    order.status = 'shipped'
    db.session.commit()

    return jsonify({'message': 'Sales order shipped successfully'}), 200


@sales_bp.route('/sales-orders/<int:so_id>/invoice', methods=['POST'])
@login_required
def create_invoice(so_id):
    """Create invoice from sales order."""
    order = SalesOrder.query.get_or_404(so_id)

    if order.status not in ['shipped', 'delivered']:
        return jsonify({'error': 'Can only invoice shipped/delivered orders'}), 400

    # Check if invoice already exists
    existing = Invoice.query.filter_by(sales_order_id=so_id).first()
    if existing:
        return jsonify({'error': 'Invoice already exists for this order'}), 409

    invoice = Invoice(
        invoice_number=generate_invoice_number(),
        invoice_type='sales',
        sales_order_id=so_id,
        customer_id=order.customer_id,
        invoice_date=datetime.now().date(),
        due_date=datetime.strptime(request.get_json().get('due_date', ''), '%Y-%m-%d').date() if request.get_json().get('due_date') else None,
        status='issued',
        subtotal=order.subtotal,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount
    )

    db.session.add(invoice)

    order.payment_status = 'pending'
    db.session.commit()

    return jsonify({
        'message': 'Invoice created successfully',
        'invoice': {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'total_amount': float(invoice.total_amount)
        }
    }), 201
