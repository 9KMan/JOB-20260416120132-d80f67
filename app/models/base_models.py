"""Base business models for the ERP system."""

from app import db
from datetime import datetime


class Supplier(db.Model):
    """Supplier/Vendor model."""

    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))
    payment_terms = db.Column(db.String(50))  # e.g., 'NET30', 'NET60'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    purchase_orders = db.relationship('PurchaseOrder', backref='supplier', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.code}: {self.name}>'


class Customer(db.Model):
    """Customer model."""

    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))
    credit_limit = db.Column(db.Numeric(12, 2), default=0)
    payment_terms = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sales_orders = db.relationship('SalesOrder', backref='customer', lazy='dynamic')

    def __repr__(self):
        return f'<Customer {self.code}: {self.name}>'


class Material(db.Model):
    """Raw material model."""

    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20), default='UNIT')  # kg, liter, piece, etc.
    unit_cost = db.Column(db.Numeric(10, 2), default=0)
    reorder_level = db.Column(db.Numeric(10, 2), default=0)
    safety_stock = db.Column(db.Numeric(10, 2), default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Material {self.code}: {self.name}>'


class Product(db.Model):
    """Finished product model."""

    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20), default='UNIT')
    unit_price = db.Column(db.Numeric(10, 2), default=0)
    quantity_per_unit = db.Column(db.Numeric(10, 2), default=1)
    weight = db.Column(db.Numeric(10, 2))
    dimensions = db.Column(db.String(50))  # LxWxH
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bill_of_materials = db.relationship('BillOfMaterials', backref='product', lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.code}: {self.name}>'


class Warehouse(db.Model):
    """Warehouse model."""

    __tablename__ = 'warehouses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Warehouse {self.code}: {self.name}>'


class Stock(db.Model):
    """Stock/Inventory model."""

    __tablename__ = 'stocks'

    id = db.Column(db.Integer, primary_key=True)
    item_type = db.Column(db.String(20), nullable=False)  # 'material' or 'product'
    item_id = db.Column(db.Integer, nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    quantity = db.Column(db.Numeric(10, 2), default=0)
    reserved_quantity = db.Column(db.Numeric(10, 2), default=0)
    available_quantity = db.Column(db.Numeric(10, 2), default=0)
    unit_cost = db.Column(db.Numeric(10, 2), default=0)
    total_value = db.Column(db.Numeric(12, 2), default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = db.relationship('Warehouse', backref='stocks')

    def update_available(self):
        """Update available quantity."""
        self.available_quantity = self.quantity - self.reserved_quantity
        self.total_value = self.available_quantity * self.unit_cost

    def __repr__(self):
        return f'<Stock {self.item_type}:{self.item_id} Qty:{self.quantity}>'


class PurchaseOrder(db.Model):
    """Purchase Order model."""

    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    expected_delivery_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')  # draft, submitted, approved, received, cancelled
    notes = db.Column(db.Text)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('PurchaseOrderItem', backref='purchase_order', lazy='dynamic', cascade='all, delete-orphan')

    def calculate_totals(self):
        """Calculate order totals."""
        self.subtotal = sum(item.total for item in self.items)
        self.tax_amount = self.subtotal * 0.1  # 10% tax
        self.total_amount = self.subtotal + self.tax_amount

    def __repr__(self):
        return f'<PurchaseOrder {self.order_number}>'


class PurchaseOrderItem(db.Model):
    """Purchase Order Item model."""

    __tablename__ = 'purchase_order_items'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    received_quantity = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material')

    def __repr__(self):
        return f'<PurchaseOrderItem PO:{self.purchase_order_id} Mat:{self.material_id}>'


class GoodsReceipt(db.Model):
    """Goods Receipt model."""

    __tablename__ = 'goods_receipts'

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(20), unique=True, nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    receipt_date = db.Column(db.Date, nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = db.relationship('Supplier')
    warehouse = db.relationship('Warehouse')
    items = db.relationship('GoodsReceiptItem', backref='goods_receipt', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<GoodsReceipt {self.receipt_number}>'


class GoodsReceiptItem(db.Model):
    """Goods Receipt Item model."""

    __tablename__ = 'goods_receipt_items'

    id = db.Column(db.Integer, primary_key=True)
    goods_receipt_id = db.Column(db.Integer, db.ForeignKey('goods_receipts.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    total_cost = db.Column(db.Numeric(12, 2), nullable=False)
    quality_check_passed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material')

    def __repr__(self):
        return f'<GoodsReceiptItem GR:{self.goods_receipt_id} Mat:{self.material_id}>'


class ProductionOrder(db.Model):
    """Production Order model."""

    __tablename__ = 'production_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    scheduled_start_date = db.Column(db.Date)
    scheduled_end_date = db.Column(db.Date)
    actual_start_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product')
    items = db.relationship('ProductionOrderItem', backref='production_order', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ProductionOrder {self.order_number}>'


class ProductionOrderItem(db.Model):
    """Production Order Item (Bill of Materials) model."""

    __tablename__ = 'production_order_items'

    id = db.Column(db.Integer, primary_key=True)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity_required = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_used = db.Column(db.Numeric(10, 2), default=0)
    is_issued = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material')

    def __repr__(self):
        return f'<ProductionOrderItem PO:{self.production_order_id} Mat:{self.material_id}>'


class BillOfMaterials(db.Model):
    """Bill of Materials - defines product components."""

    __tablename__ = 'bill_of_materials'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity_required = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    material = db.relationship('Material')

    def __repr__(self):
        return f'<BillOfMaterials Prod:{self.product_id} Mat:{self.material_id}>'


class PackagingOrder(db.Model):
    """Packaging Order model."""

    __tablename__ = 'packaging_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    packaging_type = db.Column(db.String(50))  # box, pallet, etc.
    order_date = db.Column(db.Date, nullable=False)
    scheduled_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship('Product')
    items = db.relationship('PackagingOrderItem', backref='packaging_order', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PackagingOrder {self.order_number}>'


class PackagingOrderItem(db.Model):
    """Packaging Order Item model."""

    __tablename__ = 'packaging_order_items'

    id = db.Column(db.Integer, primary_key=True)
    packaging_order_id = db.Column(db.Integer, db.ForeignKey('packaging_orders.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), default=0)
    total_cost = db.Column(db.Numeric(12, 2), default=0)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material')

    def __repr__(self):
        return f'<PackagingOrderItem PKG:{self.packaging_order_id} Mat:{self.material_id}>'


class SalesOrder(db.Model):
    """Sales Order model."""

    __tablename__ = 'sales_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    order_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'))
    status = db.Column(db.String(20), default='draft')  # draft, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, paid
    notes = db.Column(db.Text)
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = db.relationship('Warehouse')
    items = db.relationship('SalesOrderItem', backref='sales_order', lazy='dynamic', cascade='all, delete-orphan')

    def calculate_totals(self):
        """Calculate order totals."""
        self.subtotal = sum(item.total for item in self.items)
        self.tax_amount = self.subtotal * 0.1  # 10% tax
        self.total_amount = self.subtotal + self.tax_amount

    def __repr__(self):
        return f'<SalesOrder {self.order_number}>'


class SalesOrderItem(db.Model):
    """Sales Order Item model."""

    __tablename__ = 'sales_order_items'

    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    quantity_shipped = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')

    def __repr__(self):
        return f'<SalesOrderItem SO:{self.sales_order_id} Prod:{self.product_id}>'


class Invoice(db.Model):
    """Invoice model."""

    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    invoice_type = db.Column(db.String(20), default='sales')  # sales, purchase
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    invoice_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')  # draft, issued, paid, overdue, cancelled
    subtotal = db.Column(db.Numeric(12, 2), default=0)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), default=0)
    amount_paid = db.Column(db.Numeric(12, 2), default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship('Customer')
    supplier = db.relationship('Supplier')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')

    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class Payment(db.Model):
    """Payment model."""

    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(20), unique=True, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_method = db.Column(db.String(20))  # cash, bank_transfer, check, credit_card
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.payment_number}>'


class JournalEntry(db.Model):
    """Accounting Journal Entry model."""

    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    entry_number = db.Column(db.String(20), unique=True, nullable=False)
    entry_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    debit_total = db.Column(db.Numeric(12, 2), default=0)
    credit_total = db.Column(db.Numeric(12, 2), default=0)
    is_posted = db.Column(db.Boolean, default=False)
    posted_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    posted_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = db.relationship('JournalEntryLine', backref='journal_entry', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<JournalEntry {self.entry_number}>'


class JournalEntryLine(db.Model):
    """Journal Entry Line model."""

    __tablename__ = 'journal_entry_lines'

    id = db.Column(db.Integer, primary_key=True)
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=False)
    account_code = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(100), nullable=False)
    debit = db.Column(db.Numeric(12, 2), default=0)
    credit = db.Column(db.Numeric(12, 2), default=0)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<JournalEntryLine {self.account_code} Dr:{self.debit} Cr:{self.credit}>'
