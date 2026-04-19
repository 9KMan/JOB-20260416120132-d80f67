"""Goods Receiving module for managing incoming materials."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import GoodsReceipt, GoodsReceiptItem, PurchaseOrder, PurchaseOrderItem, Material, Stock, Warehouse
from datetime import datetime
import uuid

goods_receiving_bp = Blueprint('goods_receiving', __name__)


def generate_gr_number():
    """Generate unique goods receipt number."""
    return f'GR-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


@goods_receiving_bp.route('/goods-receipts', methods=['GET'])
@login_required
def get_goods_receipts():
    """Get all goods receipts."""
    receipts = GoodsReceipt.query.order_by(GoodsReceipt.created_at.desc()).all()
    return jsonify({
        'goods_receipts': [{
            'id': gr.id,
            'receipt_number': gr.receipt_number,
            'supplier_id': gr.supplier_id,
            'supplier_name': gr.supplier.name,
            'receipt_date': gr.receipt_date.isoformat() if gr.receipt_date else None,
            'warehouse_id': gr.warehouse_id,
            'warehouse_name': gr.warehouse.name,
            'status': gr.status,
            'created_at': gr.created_at.isoformat()
        } for gr in receipts]
    }), 200


@goods_receiving_bp.route('/goods-receipts', methods=['POST'])
@login_required
def create_goods_receipt():
    """Create a new goods receipt."""
    data = request.get_json()

    required = ['supplier_id', 'receipt_date', 'warehouse_id', 'items']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    receipt = GoodsReceipt(
        receipt_number=generate_gr_number(),
        supplier_id=data['supplier_id'],
        purchase_order_id=data.get('purchase_order_id'),
        receipt_date=datetime.strptime(data['receipt_date'], '%Y-%m-%d').date(),
        warehouse_id=data['warehouse_id'],
        status='draft',
        notes=data.get('notes')
    )

    db.session.add(receipt)
    db.session.flush()

    for item_data in data['items']:
        material = Material.query.get(item_data['material_id'])
        if not material:
            return jsonify({'error': f"Material {item_data['material_id']} not found"}), 404

        quantity = float(item_data['quantity'])
        unit_cost = float(item_data.get('unit_cost', material.unit_cost))

        item = GoodsReceiptItem(
            goods_receipt_id=receipt.id,
            material_id=item_data['material_id'],
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=quantity * unit_cost,
            quality_check_passed=item_data.get('quality_check_passed', False),
            notes=item_data.get('notes')
        )
        db.session.add(item)

    db.session.commit()

    return jsonify({
        'message': 'Goods receipt created successfully',
        'goods_receipt': {
            'id': receipt.id,
            'receipt_number': receipt.receipt_number
        }
    }), 201


@goods_receiving_bp.route('/goods-receipts/<int:gr_id>', methods=['GET'])
@login_required
def get_goods_receipt(gr_id):
    """Get goods receipt by ID."""
    receipt = GoodsReceipt.query.get_or_404(gr_id)

    items = [{
        'id': item.id,
        'material_id': item.material_id,
        'material_code': item.material.code,
        'material_name': item.material.name,
        'quantity': float(item.quantity),
        'unit_cost': float(item.unit_cost),
        'total_cost': float(item.total_cost),
        'quality_check_passed': item.quality_check_passed,
        'notes': item.notes
    } for item in receipt.items]

    return jsonify({
        'goods_receipt': {
            'id': receipt.id,
            'receipt_number': receipt.receipt_number,
            'supplier_id': receipt.supplier_id,
            'supplier_name': receipt.supplier.name,
            'purchase_order_id': receipt.purchase_order_id,
            'receipt_date': receipt.receipt_date.isoformat() if receipt.receipt_date else None,
            'warehouse_id': receipt.warehouse_id,
            'warehouse_name': receipt.warehouse.name,
            'status': receipt.status,
            'notes': receipt.notes,
            'items': items
        }
    }), 200


@goods_receiving_bp.route('/goods-receipts/<int:gr_id>/complete', methods=['POST'])
@login_required
def complete_goods_receipt(gr_id):
    """Complete goods receipt and update stock."""
    receipt = GoodsReceipt.query.get_or_404(gr_id)

    if receipt.status == 'completed':
        return jsonify({'error': 'Goods receipt already completed'}), 400

    # Update stock for each item
    for item in receipt.items:
        if not item.quality_check_passed:
            continue

        # Find or create stock record
        stock = Stock.query.filter_by(
            item_type='material',
            item_id=item.material_id,
            warehouse_id=receipt.warehouse_id
        ).first()

        if stock:
            stock.quantity += item.quantity
            stock.update_available()
        else:
            stock = Stock(
                item_type='material',
                item_id=item.material_id,
                warehouse_id=receipt.warehouse_id,
                quantity=item.quantity,
                unit_cost=item.unit_cost
            )
            stock.update_available()
            db.session.add(stock)

        # Update purchase order item received quantity
        if receipt.purchase_order_id:
            po_item = PurchaseOrderItem.query.filter_by(
                purchase_order_id=receipt.purchase_order_id,
                material_id=item.material_id
            ).first()
            if po_item:
                po_item.received_quantity += item.quantity

    receipt.status = 'completed'
    db.session.commit()

    return jsonify({'message': 'Goods receipt completed and stock updated'}), 200


@goods_receiving_bp.route('/goods-receipts/<int:gr_id>/quality-check', methods=['POST'])
@login_required
def quality_check_item(gr_id):
    """Update quality check status for items."""
    receipt = GoodsReceipt.query.get_or_404(gr_id)
    data = request.get_json()

    item_id = data.get('item_id')
    passed = data.get('passed', False)

    item = GoodsReceiptItem.query.filter_by(
        id=item_id,
        goods_receipt_id=gr_id
    ).first_or_404()

    item.quality_check_passed = passed
    db.session.commit()

    return jsonify({'message': f"Quality check {'passed' if passed else 'failed'} for item"}), 200


@goods_receiving_bp.route('/warehouses', methods=['GET'])
@login_required
def get_warehouses():
    """Get all warehouses."""
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return jsonify({
        'warehouses': [{
            'id': w.id,
            'code': w.code,
            'name': w.name,
            'address': w.address
        } for w in warehouses]
    }), 200


@goods_receiving_bp.route('/warehouses', methods=['POST'])
@login_required
def create_warehouse():
    """Create a new warehouse."""
    data = request.get_json()

    required = ['code', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Code and name are required'}), 400

    if Warehouse.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Warehouse code already exists'}), 409

    warehouse = Warehouse(
        code=data['code'],
        name=data['name'],
        address=data.get('address')
    )

    db.session.add(warehouse)
    db.session.commit()

    return jsonify({
        'message': 'Warehouse created successfully',
        'warehouse': {
            'id': warehouse.id,
            'code': warehouse.code,
            'name': warehouse.name
        }
    }), 201
