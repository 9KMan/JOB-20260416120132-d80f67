"""Procurement module for managing suppliers and purchase orders."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import Supplier, PurchaseOrder, PurchaseOrderItem, Material
from datetime import datetime
import uuid

procurement_bp = Blueprint('procurement', __name__)


def generate_po_number():
    """Generate unique purchase order number."""
    return f'PO-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


# Supplier endpoints
@procurement_bp.route('/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    """Get all suppliers."""
    suppliers = Supplier.query.filter_by(is_active=True).all()
    return jsonify({
        'suppliers': [{
            'id': s.id,
            'code': s.code,
            'name': s.name,
            'contact_person': s.contact_person,
            'email': s.email,
            'phone': s.phone,
            'address': s.address,
            'city': s.city,
            'country': s.country,
            'payment_terms': s.payment_terms
        } for s in suppliers]
    }), 200


@procurement_bp.route('/suppliers', methods=['POST'])
@login_required
def create_supplier():
    """Create a new supplier."""
    data = request.get_json()

    required = ['code', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Code and name are required'}), 400

    if Supplier.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Supplier code already exists'}), 409

    supplier = Supplier(
        code=data['code'],
        name=data['name'],
        contact_person=data.get('contact_person'),
        email=data.get('email'),
        phone=data.get('phone'),
        address=data.get('address'),
        city=data.get('city'),
        country=data.get('country'),
        tax_id=data.get('tax_id'),
        payment_terms=data.get('payment_terms')
    )

    db.session.add(supplier)
    db.session.commit()

    return jsonify({
        'message': 'Supplier created successfully',
        'supplier': {
            'id': supplier.id,
            'code': supplier.code,
            'name': supplier.name
        }
    }), 201


@procurement_bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
@login_required
def get_supplier(supplier_id):
    """Get supplier by ID."""
    supplier = Supplier.query.get_or_404(supplier_id)
    return jsonify({
        'supplier': {
            'id': supplier.id,
            'code': supplier.code,
            'name': supplier.name,
            'contact_person': supplier.contact_person,
            'email': supplier.email,
            'phone': supplier.phone,
            'address': supplier.address,
            'city': supplier.city,
            'country': supplier.country,
            'tax_id': supplier.tax_id,
            'payment_terms': supplier.payment_terms
        }
    }), 200


@procurement_bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required
def update_supplier(supplier_id):
    """Update supplier."""
    supplier = Supplier.query.get_or_404(supplier_id)
    data = request.get_json()

    for field in ['name', 'contact_person', 'email', 'phone', 'address', 'city', 'country', 'tax_id', 'payment_terms']:
        if field in data:
            setattr(supplier, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Supplier updated successfully'}), 200


# Purchase Order endpoints
@procurement_bp.route('/purchase-orders', methods=['GET'])
@login_required
def get_purchase_orders():
    """Get all purchase orders."""
    orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    return jsonify({
        'purchase_orders': [{
            'id': po.id,
            'order_number': po.order_number,
            'supplier_id': po.supplier_id,
            'supplier_name': po.supplier.name,
            'order_date': po.order_date.isoformat() if po.order_date else None,
            'expected_delivery_date': po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            'status': po.status,
            'total_amount': float(po.total_amount),
            'created_at': po.created_at.isoformat()
        } for po in orders]
    }), 200


@procurement_bp.route('/purchase-orders', methods=['POST'])
@login_required
def create_purchase_order():
    """Create a new purchase order."""
    data = request.get_json()

    required = ['supplier_id', 'order_date', 'items']
    if not all(field in data for field in required):
        return jsonify({'error': 'Supplier ID, order date, and items are required'}), 400

    supplier = Supplier.query.get(data['supplier_id'])
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404

    order = PurchaseOrder(
        order_number=generate_po_number(),
        supplier_id=data['supplier_id'],
        order_date=datetime.strptime(data['order_date'], '%Y-%m-%d').date(),
        expected_delivery_date=datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date() if data.get('expected_delivery_date') else None,
        status='draft',
        notes=data.get('notes')
    )

    db.session.add(order)
    db.session.flush()  # Get the order ID

    for item_data in data['items']:
        material = Material.query.get(item_data['material_id'])
        if not material:
            return jsonify({'error': f"Material {item_data['material_id']} not found"}), 404

        quantity = float(item_data['quantity'])
        unit_price = float(item_data['unit_price'])

        item = PurchaseOrderItem(
            purchase_order_id=order.id,
            material_id=item_data['material_id'],
            quantity=quantity,
            unit_price=unit_price,
            total=quantity * unit_price
        )
        db.session.add(item)

    order.calculate_totals()
    db.session.commit()

    return jsonify({
        'message': 'Purchase order created successfully',
        'purchase_order': {
            'id': order.id,
            'order_number': order.order_number,
            'total_amount': float(order.total_amount)
        }
    }), 201


@procurement_bp.route('/purchase-orders/<int:po_id>', methods=['GET'])
@login_required
def get_purchase_order(po_id):
    """Get purchase order by ID."""
    order = PurchaseOrder.query.get_or_404(po_id)

    items = [{
        'id': item.id,
        'material_id': item.material_id,
        'material_code': item.material.code,
        'material_name': item.material.name,
        'quantity': float(item.quantity),
        'unit_price': float(item.unit_price),
        'total': float(item.total),
        'received_quantity': float(item.received_quantity)
    } for item in order.items]

    return jsonify({
        'purchase_order': {
            'id': order.id,
            'order_number': order.order_number,
            'supplier_id': order.supplier_id,
            'supplier_name': order.supplier.name,
            'order_date': order.order_date.isoformat() if order.order_date else None,
            'expected_delivery_date': order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
            'status': order.status,
            'subtotal': float(order.subtotal),
            'tax_amount': float(order.tax_amount),
            'total_amount': float(order.total_amount),
            'notes': order.notes,
            'items': items
        }
    }), 200


@procurement_bp.route('/purchase-orders/<int:po_id>/status', methods=['PUT'])
@login_required
def update_purchase_order_status(po_id):
    """Update purchase order status."""
    order = PurchaseOrder.query.get_or_404(po_id)
    data = request.get_json()

    new_status = data.get('status')
    valid_statuses = ['draft', 'submitted', 'approved', 'received', 'cancelled']

    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    order.status = new_status
    db.session.commit()

    return jsonify({'message': f'Purchase order status updated to {new_status}'}), 200


@procurement_bp.route('/materials', methods=['GET'])
@login_required
def get_materials():
    """Get all materials."""
    materials = Material.query.filter_by(is_active=True).all()
    return jsonify({
        'materials': [{
            'id': m.id,
            'code': m.code,
            'name': m.name,
            'description': m.description,
            'unit': m.unit,
            'unit_cost': float(m.unit_cost),
            'reorder_level': float(m.reorder_level),
            'safety_stock': float(m.safety_stock)
        } for m in materials]
    }), 200


@procurement_bp.route('/materials', methods=['POST'])
@login_required
def create_material():
    """Create a new material."""
    data = request.get_json()

    required = ['code', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Code and name are required'}), 400

    if Material.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Material code already exists'}), 409

    material = Material(
        code=data['code'],
        name=data['name'],
        description=data.get('description'),
        unit=data.get('unit', 'UNIT'),
        unit_cost=data.get('unit_cost', 0),
        reorder_level=data.get('reorder_level', 0),
        safety_stock=data.get('safety_stock', 0)
    )

    db.session.add(material)
    db.session.commit()

    return jsonify({
        'message': 'Material created successfully',
        'material': {
            'id': material.id,
            'code': material.code,
            'name': material.name
        }
    }), 201
