"""Packaging module for managing packaging orders."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import PackagingOrder, PackagingOrderItem, Product, Material, Stock
from datetime import datetime
import uuid

packaging_bp = Blueprint('packaging', __name__)


def generate_packaging_number():
    """Generate unique packaging order number."""
    return f'PKG-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


@packaging_bp.route('/packaging-orders', methods=['GET'])
@login_required
def get_packaging_orders():
    """Get all packaging orders."""
    orders = PackagingOrder.query.order_by(PackagingOrder.created_at.desc()).all()
    return jsonify({
        'packaging_orders': [{
            'id': po.id,
            'order_number': po.order_number,
            'product_id': po.product_id,
            'product_name': po.product.name,
            'quantity': float(po.quantity),
            'packaging_type': po.packaging_type,
            'order_date': po.order_date.isoformat() if po.order_date else None,
            'scheduled_date': po.scheduled_date.isoformat() if po.scheduled_date else None,
            'completed_date': po.completed_date.isoformat() if po.completed_date else None,
            'status': po.status,
            'created_at': po.created_at.isoformat()
        } for po in orders]
    }), 200


@packaging_bp.route('/packaging-orders', methods=['POST'])
@login_required
def create_packaging_order():
    """Create a new packaging order."""
    data = request.get_json()

    required = ['product_id', 'quantity', 'order_date']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    order = PackagingOrder(
        order_number=generate_packaging_number(),
        production_order_id=data.get('production_order_id'),
        product_id=data['product_id'],
        quantity=float(data['quantity']),
        packaging_type=data.get('packaging_type'),
        order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date(),
        scheduled_date=datetime.strptime(data['scheduled_date'], '%Y-%m-%d').date() if data.get('scheduled_date') else None,
        status='pending',
        notes=data.get('notes')
    )

    db.session.add(order)
    db.session.commit()

    return jsonify({
        'message': 'Packaging order created successfully',
        'packaging_order': {
            'id': order.id,
            'order_number': order.order_number
        }
    }), 201


@packaging_bp.route('/packaging-orders/<int:po_id>', methods=['GET'])
@login_required
def get_packaging_order(po_id):
    """Get packaging order by ID."""
    order = PackagingOrder.query.get_or_404(po_id)

    items = [{
        'id': item.id,
        'material_id': item.material_id,
        'material_code': item.material.code,
        'material_name': item.material.name,
        'quantity': float(item.quantity),
        'unit_cost': float(item.unit_cost),
        'total_cost': float(item.total_cost),
        'is_used': item.is_used
    } for item in order.items]

    return jsonify({
        'packaging_order': {
            'id': order.id,
            'order_number': order.order_number,
            'production_order_id': order.production_order_id,
            'product_id': order.product_id,
            'product_name': order.product.name,
            'quantity': float(order.quantity),
            'packaging_type': order.packaging_type,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'scheduled_date': order.scheduled_date.isoformat() if order.scheduled_date else None,
            'completed_date': order.completed_date.isoformat() if order.completed_date else None,
            'status': order.status,
            'notes': order.notes,
            'items': items
        }
    }), 200


@packaging_bp.route('/packaging-orders/<int:po_id>/status', methods=['PUT'])
@login_required
def update_packaging_order_status(po_id):
    """Update packaging order status."""
    order = PackagingOrder.query.get_or_404(po_id)
    data = request.get_json()

    new_status = data.get('status')
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']

    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    if new_status == 'completed':
        order.completed_date = datetime.now().date()

    order.status = new_status
    db.session.commit()

    return jsonify({'message': f'Packaging order status updated to {new_status}'}), 200


@packaging_bp.route('/packaging-orders/<int:po_id>/add-materials', methods=['POST'])
@login_required
def add_packaging_materials(po_id):
    """Add packaging materials to order."""
    order = PackagingOrder.query.get_or_404(po_id)
    data = request.get_json()

    if order.status == 'completed':
        return jsonify({'error': 'Cannot add materials to completed order'}), 400

    for item_data in data.get('items', []):
        material = Material.query.get(item_data['material_id'])
        if not material:
            return jsonify({'error': f"Material {item_data['material_id']} not found"}), 404

        quantity = float(item_data['quantity'])
        unit_cost = float(item_data.get('unit_cost', material.unit_cost))

        item = PackagingOrderItem(
            packaging_order_id=order.id,
            material_id=item_data['material_id'],
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost
        )
        db.session.add(item)

    db.session.commit()

    return jsonify({'message': 'Packaging materials added successfully'}), 200


@packaging_bp.route('/packaging-orders/<int:po_id>/use-materials', methods=['POST'])
@login_required
def use_packaging_materials(po_id):
    """Consume packaging materials."""
    order = PackagingOrder.query.get_or_404(po_id)
    data = request.get_json()

    warehouse_id = data.get('warehouse_id', 1)

    for item_data in data.get('items', []):
        item = PackagingOrderItem.query.filter_by(
            id=item_data['id'],
            packaging_order_id=po_id
        ).first()

        if not item or item.is_used:
            continue

        quantity_used = float(item_data['quantity'])

        # Deduct from stock
        stock = Stock.query.filter_by(
            item_type='material',
            item_id=item.material_id,
            warehouse_id=warehouse_id
        ).first()

        if stock and stock.available_quantity >= quantity_used:
            stock.quantity -= quantity_used
            stock.update_available()
            item.is_used = True

    db.session.commit()

    return jsonify({'message': 'Packaging materials consumed'}), 200


@packaging_bp.route('/packaging-orders/<int:po_id>/complete', methods=['POST'])
@login_required
def complete_packaging_order(po_id):
    """Complete packaging order."""
    order = PackagingOrder.query.get_or_404(po_id)

    if order.status == 'completed':
        return jsonify({'error': 'Packaging order already completed'}), 400

    order.status = 'completed'
    order.completed_date = datetime.now().date()
    db.session.commit()

    return jsonify({'message': 'Packaging order completed'}), 200
