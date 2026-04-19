"""Financial module for managing invoices, payments, and journal entries."""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.base_models import Invoice, Payment, JournalEntry, JournalEntryLine, Supplier, Customer
from datetime import datetime
import uuid

financial_bp = Blueprint('financial', __name__)


def generate_payment_number():
    """Generate unique payment number."""
    return f'PAY-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


def generate_journal_number():
    """Generate unique journal entry number."""
    return f'JE-{datetime.now().strftime("%Y%m%d")}-{str(uuid.uuid4())[:4].upper()}'


# Invoice endpoints
@financial_bp.route('/invoices', methods=['GET'])
@login_required
def get_invoices():
    """Get all invoices."""
    invoice_type = request.args.get('type')  # 'sales' or 'purchase'

    query = Invoice.query
    if invoice_type:
        query = query.filter_by(invoice_type=invoice_type)

    invoices = query.order_by(Invoice.created_at.desc()).all()

    return jsonify({
        'invoices': [{
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'invoice_type': inv.invoice_type,
            'customer_id': inv.customer_id,
            'customer_name': inv.customer.name if inv.customer else None,
            'supplier_id': inv.supplier_id,
            'supplier_name': inv.supplier.name if inv.supplier else None,
            'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
            'due_date': inv.due_date.isoformat() if inv.due_date else None,
            'status': inv.status,
            'total_amount': float(inv.total_amount),
            'amount_paid': float(inv.amount_paid),
            'balance': float(inv.total_amount - inv.amount_paid)
        } for inv in invoices]
    }), 200


@financial_bp.route('/invoices/<int:inv_id>', methods=['GET'])
@login_required
def get_invoice(inv_id):
    """Get invoice by ID."""
    invoice = Invoice.query.get_or_404(inv_id)

    payments = [{
        'id': p.id,
        'payment_number': p.payment_number,
        'payment_date': p.payment_date.isoformat() if p.payment_date else None,
        'amount': float(p.amount),
        'payment_method': p.payment_method,
        'reference_number': p.reference_number
    } for p in invoice.payments]

    return jsonify({
        'invoice': {
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_type': invoice.invoice_type,
            'customer_id': invoice.customer_id,
            'customer_name': invoice.customer.name if invoice.customer else None,
            'supplier_id': invoice.supplier_id,
            'supplier_name': invoice.supplier.name if invoice.supplier else None,
            'sales_order_id': invoice.sales_order_id,
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
            'status': invoice.status,
            'subtotal': float(invoice.subtotal),
            'tax_amount': float(invoice.tax_amount),
            'total_amount': float(invoice.total_amount),
            'amount_paid': float(invoice.amount_paid),
            'payments': payments,
            'notes': invoice.notes
        }
    }), 200


@financial_bp.route('/invoices/<int:inv_id>/status', methods=['PUT'])
@login_required
def update_invoice_status(inv_id):
    """Update invoice status."""
    invoice = Invoice.query.get_or_404(inv_id)
    data = request.get_json()

    new_status = data.get('status')
    valid_statuses = ['draft', 'issued', 'paid', 'overdue', 'cancelled']

    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400

    invoice.status = new_status
    db.session.commit()

    return jsonify({'message': f'Invoice status updated to {new_status}'}), 200


# Payment endpoints
@financial_bp.route('/payments', methods=['GET'])
@login_required
def get_payments():
    """Get all payments."""
    payments = Payment.query.order_by(Payment.created_at.desc()).all()
    return jsonify({
        'payments': [{
            'id': p.id,
            'payment_number': p.payment_number,
            'invoice_id': p.invoice_id,
            'invoice_number': p.invoice.invoice_number if p.invoice else None,
            'payment_date': p.payment_date.isoformat() if p.payment_date else None,
            'amount': float(p.amount),
            'payment_method': p.payment_method,
            'reference_number': p.reference_number
        } for p in payments]
    }), 200


@financial_bp.route('/payments', methods=['POST'])
@login_required
def create_payment():
    """Record a new payment."""
    data = request.get_json()

    required = ['invoice_id', 'payment_date', 'amount']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    invoice = Invoice.query.get(data['invoice_id'])
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404

    amount = float(data['amount'])

    payment = Payment(
        payment_number=generate_payment_number(),
        invoice_id=data['invoice_id'],
        payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d').date(),
        amount=amount,
        payment_method=data.get('payment_method'),
        reference_number=data.get('reference_number'),
        notes=data.get('notes')
    )

    db.session.add(payment)

    # Update invoice
    invoice.amount_paid += amount
    if invoice.amount_paid >= invoice.total_amount:
        invoice.status = 'paid'

    # Create journal entry for payment
    create_payment_journal_entry(payment, invoice)

    db.session.commit()

    return jsonify({
        'message': 'Payment recorded successfully',
        'payment': {
            'id': payment.id,
            'payment_number': payment.payment_number,
            'amount': float(payment.amount)
        }
    }), 201


def create_payment_journal_entry(payment, invoice):
    """Create journal entry for payment."""
    je = JournalEntry(
        entry_number=generate_journal_number(),
        entry_date=payment.payment_date,
        description=f'Payment received: {payment.payment_number}',
        debit_total=payment.amount,
        credit_total=payment.amount,
        is_posted=True,
        posted_by=1  # System user
    )

    db.session.add(je)
    db.session.flush()

    # Debit: Cash/Bank
    cash_line = JournalEntryLine(
        journal_entry_id=je.id,
        account_code='1001',
        account_name='Cash',
        debit=payment.amount,
        credit=0,
        description=f'Cash received for invoice {invoice.invoice_number}'
    )
    db.session.add(cash_line)

    # Credit: Accounts Receivable
    ar_line = JournalEntryLine(
        journal_entry_id=je.id,
        account_code='1101',
        account_name='Accounts Receivable',
        debit=0,
        credit=payment.amount,
        description=f'AR reduced for invoice {invoice.invoice_number}'
    )
    db.session.add(ar_line)


# Journal Entry endpoints
@financial_bp.route('/journal-entries', methods=['GET'])
@login_required
def get_journal_entries():
    """Get all journal entries."""
    entries = JournalEntry.query.order_by(JournalEntry.created_at.desc()).all()
    return jsonify({
        'journal_entries': [{
            'id': je.id,
            'entry_number': je.entry_number,
            'entry_date': je.entry_date.isoformat() if je.entry_date else None,
            'description': je.description,
            'debit_total': float(je.debit_total),
            'credit_total': float(je.credit_total),
            'is_posted': je.is_posted,
            'created_at': je.created_at.isoformat()
        } for je in entries]
    }), 200


@financial_bp.route('/journal-entries', methods=['POST'])
@login_required
def create_journal_entry():
    """Create a new journal entry."""
    data = request.get_json()

    required = ['entry_date', 'description', 'lines']
    if not all(field in data for field in required):
        return jsonify({'error': 'Required fields missing'}), 400

    lines = data['lines']
    if len(lines) < 2:
        return jsonify({'error': 'At least 2 lines required'}), 400

    debit_total = sum(float(line.get('debit', 0)) for line in lines)
    credit_total = sum(float(line.get('credit', 0)) for line in lines)

    if abs(debit_total - credit_total) > 0.01:
        return jsonify({'error': 'Debits must equal credits'}), 400

    je = JournalEntry(
        entry_number=generate_journal_number(),
        entry_date=datetime.strptime(data['entry_date'], '%Y-%m-%d').date(),
        description=data['description'],
        debit_total=debit_total,
        credit_total=credit_total,
        is_posted=data.get('is_posted', False),
        posted_by=1
    )

    db.session.add(je)
    db.session.flush()

    for line_data in lines:
        line = JournalEntryLine(
            journal_entry_id=je.id,
            account_code=line_data['account_code'],
            account_name=line_data['account_name'],
            debit=float(line_data.get('debit', 0)),
            credit=float(line_data.get('credit', 0)),
            description=line_data.get('description')
        )
        db.session.add(line)

    db.session.commit()

    return jsonify({
        'message': 'Journal entry created successfully',
        'journal_entry': {
            'id': je.id,
            'entry_number': je.entry_number
        }
    }), 201


@financial_bp.route('/journal-entries/<int:je_id>', methods=['GET'])
@login_required
def get_journal_entry(je_id):
    """Get journal entry by ID."""
    entry = JournalEntry.query.get_or_404(je_id)

    lines = [{
        'id': line.id,
        'account_code': line.account_code,
        'account_name': line.account_name,
        'debit': float(line.debit),
        'credit': float(line.credit),
        'description': line.description
    } for line in entry.lines]

    return jsonify({
        'journal_entry': {
            'id': entry.id,
            'entry_number': entry.entry_number,
            'entry_date': entry.entry_date.isoformat() if entry.entry_date else None,
            'description': entry.description,
            'debit_total': float(entry.debit_total),
            'credit_total': float(entry.credit_total),
            'is_posted': entry.is_posted,
            'posted_by': entry.posted_by,
            'lines': lines
        }
    }), 200


@financial_bp.route('/journal-entries/<int:je_id>/post', methods=['POST'])
@login_required
def post_journal_entry(je_id):
    """Post a journal entry."""
    entry = JournalEntry.query.get_or_404(je_id)

    if entry.is_posted:
        return jsonify({'error': 'Entry already posted'}), 400

    entry.is_posted = True
    entry.posted_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': 'Journal entry posted successfully'}), 200


# Account balances (simple chart of accounts)
@financial_bp.route('/accounts/balance-sheet', methods=['GET'])
@login_required
def get_balance_sheet():
    """Get balance sheet summary."""
    # Simplified balance sheet
    assets = {
        '1001': {'name': 'Cash', 'balance': 0},
        '1101': {'name': 'Accounts Receivable', 'balance': 0},
        '1201': {'name': 'Inventory', 'balance': 0},
        '1501': {'name': 'Equipment', 'balance': 0}
    }

    liabilities = {
        '2001': {'name': 'Accounts Payable', 'balance': 0},
        '2101': {'name': 'Notes Payable', 'balance': 0}
    }

    equity = {
        '3001': {'name': 'Common Stock', 'balance': 0},
        '3101': {'name': 'Retained Earnings', 'balance': 0}
    }

    # Calculate from journal entries
    entries = JournalEntry.query.filter_by(is_posted=True).all()
    for entry in entries:
        for line in entry.lines:
            account = line.account_code[:2] if len(line.account_code) >= 2 else line.account_code[0]
            if account in assets:
                assets[account]['balance'] += float(line.debit - line.credit)
            elif account in liabilities:
                liabilities[account]['balance'] += float(line.credit - line.debit)
            elif account in equity:
                equity[account]['balance'] += float(line.credit - line.debit)

    total_assets = sum(a['balance'] for a in assets.values())
    total_liabilities = sum(l['balance'] for l in liabilities.values())
    total_equity = sum(e['balance'] for e in equity.values())

    return jsonify({
        'balance_sheet': {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'check': total_assets - (total_liabilities + total_equity)
        }
    }), 200
