"""Production module for managing production orders and bill of materials."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import ProductionOrder, ProductionOrderItem, Product, Material, BillOfMaterials, Stock
from datetime import datetime
import uuid

production_bp = Blueprint('production', __name__)


def generate_production_number():
    """Generate unique production order number."""
    return f'PROD-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


@production_bp.route('/production-orders', methods=['GET'])
@login_required
def get_production_orders():
    """Get all production orders."""
    orders = ProductionOrder.query.order_by(ProductionOrder.created_at.desc()).all()
    return jsonify({
        'production_orders': [{
            'id': po.id,
            'order_number': po.order_number,
            'product_id': po.product_id,
            'product_name': po.product.name,
            'quantity': float(po.quantity),
            'order_date': po.order_date.isoformat() if po.order_date else None,
            'scheduled_start_date': po.scheduled_start_date.isoformat() if po.scheduled_start_date else None,
            'scheduled_end_date': po.scheduled_end_date.isoformat() if po.scheduled_end_date else None,
            'status': po.status,
            'created_at': po.created_at.isoformat()
        } for po in orders]
    }), 200


@production_bp.route('/production-orders', methods=['POST'])
@login_required
def create_production_order():
    """Create a new production order."""
    data = request.get_json()

    required = ['product_id', 'quantity', 'order_date']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    order = ProductionOrder(
        order_number=generate_production_number(),
        product_id=data['product_id'],
        quantity=float(data['quantity']),
        order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date(),
        scheduled_start_date=datetime.strptime(data['scheduled_start_date'], '%Y-%m-%d').date() if data.get('scheduled_start_date') else None,
        scheduled_end_date=datetime.strptime(data['scheduled_end_date'], '%Y-%m-%d').date() if data.get('scheduled_end_date') else None,
        status='planned',
        notes=data.get('notes')
    )

    db.session.add(order)
    db.session.flush()

    # Auto-create items from bill of materials
    bom_items = BillOfMaterials.query.filter_by(product_id=data['product_id'], is_active=True).all()
    for bom_item in bom_items:
        item = ProductionOrderItem(
            production_order_id=order.id,
            material_id=bom_item.material_id,
            quantity_required=bom_item.quantity_required * float(data['quantity'])
        )
        db.session.add(item)

    db.session.commit()

    return jsonify({
        'message': 'Production order created successfully',
        'production_order': {
            'id': order.id,
            'order_number': order.order_number
        }
    }), 201


@production_bp.route('/production-orders/<int:po_id>', methods=['GET'])
@login_required
def get_production_order(po_id):
    """Get production order by ID."""
    order = ProductionOrder.query.get_or_404(po_id)

    items = [{
        'id': item.id,
        'material_id': item.material_id,
        'material_code': item.material.code,
        'material_name': item.material.name,
        'quantity_required': float(item.quantity_required),
        'quantity_used': float(item.quantity_used),
        'is_issued': item.is_issued
    } for item in order.items]

    return jsonify({
        'production_order': {
            'id': order.id,
            'order_number': order.order_number,
            'product_id': order.product_id,
            'product_name': order.product.name,
            'quantity': float(order.quantity),
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'scheduled_start_date': order.scheduled_start_date.isoformat() if order.scheduled_start_date else None,
            'scheduled_end_date': order.scheduled_end_date.isoformat() if order.scheduled_end_date else None,
            'actual_start_date': order.actual_start_date.isoformat() if order.actual_start_date else None,
            'actual_end_date': order.actual_end_date.isoformat() if order.actual_end_date else None,
            'status': order.status,
            'notes': order.notes,
            'items': items
        }
    }), 200


@production_bp.route('/production-orders/<int:po_id>/status', methods=['PUT'])
@login_required
def update_production_order_status(po_id):
    """Update production order status."""
    order = ProductionOrder.query.get_or_404(po_id)
    data = request.get_json()

    new_status = data.get('status')
    valid_statuses = ['planned', 'in_progress', 'completed', 'cancelled']

    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    # Update dates based on status
    if new_status == 'in_progress' and not order.actual_start_date:
        order.actual_start_date = datetime.now().date()
    elif new_status == 'completed' and not order.actual_end_date:
        order.actual_end_date = datetime.now().date()

    order.status = new_status
    db.session.commit()

    return jsonify({'message': f'Production order status updated to {new_status}'}), 200


@production_bp.route('/production-orders/<int:po_id>/issue-materials', methods=['POST'])
@login_required
def issue_materials(po_id):
    """Issue materials for production."""
    order = ProductionOrder.query.get_or_404(po_id)
    data = request.get_json()

    if order.status not in ['planned', 'in_progress']:
        return jsonify({'error': 'Cannot issue materials for this order status'}), 400

    warehouse_id = data.get('warehouse_id', 1)  # Default warehouse

    for item_data in data.get('items', []):
        item = ProductionOrderItem.query.filter_by(
            id=item_data['id'],
            production_order_id=po_id
        ).first()

        if not item:
            continue

        quantity_to_issue = float(item_data['quantity'])

        # Check stock availability
        stock = Stock.query.filter_by(
            item_type='material',
            item_id=item.material_id,
            warehouse_id=warehouse_id
        ).first()

        if not stock or stock.available_quantity < quantity_to_issue:
            return jsonify({
                'error': f"Insufficient stock for material {item.material.name}"
            }), 400

        # Deduct from stock
        stock.quantity -= quantity_to_issue
        stock.update_available()

        # Update production order item
        item.quantity_used += quantity_to_issue
        item.is_issued = True

    db.session.commit()

    return jsonify({'message': 'Materials issued successfully'}), 200


@production_bp.route('/production-orders/<int:po_id>/complete', methods=['POST'])
@login_required
def complete_production_order(po_id):
    """Complete production order and add finished goods to stock."""
    order = ProductionOrder.query.get_or_404(po_id)
    data = request.get_json()

    if order.status == 'completed':
        return jsonify({'error': 'Production order already completed'}), 400

    warehouse_id = data.get('warehouse_id', 1)
    actual_quantity = float(data.get('quantity', order.quantity))

    # Add finished goods to stock
    stock = Stock.query.filter_by(
        item_type='product',
        item_id=order.product_id,
        warehouse_id=warehouse_id
    ).first()

    if stock:
        stock.quantity += actual_quantity
        stock.update_available()
    else:
        stock = Stock(
            item_type='product',
            item_id=order.product_id,
            warehouse_id=warehouse_id,
            quantity=actual_quantity,
            unit_cost=0
        )
        stock.update_available()
        db.session.add(stock)

    order.status = 'completed'
    order.actual_end_date = datetime.now().date()
    db.session.commit()

    return jsonify({'message': 'Production order completed'}), 200


# Bill of Materials endpoints
@production_bp.route('/bill-of-materials', methods=['GET'])
@login_required
def get_bill_of_materials():
    """Get all bill of materials."""
    product_id = request.args.get('product_id')

    if product_id:
        bom_items = BillOfMaterials.query.filter_by(product_id=product_id, is_active=True).all()
    else:
        bom_items = BillOfMaterials.query.filter_by(is_active=True).all()

    return jsonify({
        'bill_of_materials': [{
            'id': bom.id,
            'product_id': bom.product_id,
            'product_name': bom.product.name,
            'material_id': bom.material_id,
            'material_name': bom.material.name,
            'material_code': bom.material.code,
            'quantity_required': float(bom.quantity_required)
        } for bom in bom_items]
    }), 200


@production_bp.route('/bill-of-materials', methods=['POST'])
@login_required
def create_bom_item():
    """Add item to bill of materials."""
    data = request.get_json()

    required = ['product_id', 'material_id', 'quantity_required']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    # Check if BOM item already exists
    existing = BillOfMaterials.query.filter_by(
        product_id=data['product_id'],
        material_id=data['material_id']
    ).first()

    if existing:
        existing.quantity_required = float(data['quantity_required'])
        db.session.commit()
        return jsonify({'message': 'BOM item updated'}), 200

    bom = BillOfMaterials(
        product_id=data['product_id'],
        material_id=data['material_id'],
        quantity_required=float(data['quantity_required'])
    )

    db.session.add(bom)
    db.session.commit()

    return jsonify({
        'message': 'BOM item created successfully',
        'bill_of_materials': {
            'id': bom.id,
            'product_id': bom.product_id,
            'material_id': bom.material_id
        }
    }), 201


@production_bp.route('/products', methods=['GET'])
@login_required
def get_products():
    """Get all products."""
    products = Product.query.filter_by(is_active=True).all()
    return jsonify({
        'products': [{
            'id': p.id,
            'code': p.code,
            'name': p.name,
            'description': p.description,
            'unit': p.unit,
            'unit_price': float(p.unit_price)
        } for p in products]
    }), 200


@production_bp.route('/products', methods=['POST'])
@login_required
def create_product():
    """Create a new product."""
    data = request.get_json()

    required = ['code', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Code and name are required'}), 400

    if Product.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Product code already exists'}), 409

    product = Product(
        code=data['code'],
        name=data['name'],
        description=data.get('description'),
        unit=data.get('unit', 'UNIT'),
        unit_price=data.get('unit_price', 0),
        quantity_per_unit=data.get('quantity_per_unit', 1),
        weight=data.get('weight'),
        dimensions=data.get('dimensions')
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        'message': 'Product created successfully',
        'product': {
            'id': product.id,
            'code': product.code,
            'name': product.name
        }
    }), 201
