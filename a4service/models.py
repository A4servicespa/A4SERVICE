from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from a4service import db

# ============================
# USUARIO (LOGIN)
# ============================
class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password_plain):
        self.password = generate_password_hash(password_plain)

    def check_password(self, password_plain):
        return check_password_hash(self.password, password_plain)

    def __repr__(self):
        return f"<Usuario {self.email}>"


# ============================
# CLIENTES
# ============================
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(120))
    rut = db.Column(db.String(50))

    quotations = db.relationship("Quotation", backref="client", lazy=True)
    invoices = db.relationship("Invoice", backref="client", lazy=True)

    def __repr__(self):
        return f"<Client {self.name}>"


# ============================
# PRODUCTOS
# ============================
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_min = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)

    quotation_items = db.relationship("QuotationItem", backref="product", lazy=True)
    invoice_items = db.relationship("InvoiceItem", backref="product", lazy=True)
    movements = db.relationship("Movement", backref="product", lazy=True)

    def __repr__(self):
        return f"<Product {self.name}>"


# ============================
# COTIZACIONES
# ============================
class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Pendiente")

    subtotal = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)

    notes = db.Column(db.Text)

    items = db.relationship(
        "QuotationItem",
        backref="quotation",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Quotation {self.number or self.id}>"


class QuotationItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey("quotation.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def subtotal(self):
        return self.quantity * self.price


# ============================
# FACTURAS
# ============================
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Pendiente")

    subtotal = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)

    items = db.relationship(
        "InvoiceItem",
        backref="invoice",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Invoice {self.id}>"


class InvoiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def subtotal(self):
        return self.quantity * self.price


# ============================
# MOVIMIENTOS DE INVENTARIO
# ============================
class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False)

    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Movement {self.type} {self.quantity}>"


# ============================
# FACTURAS PDF (ARCHIVOS)
# ============================
class InvoiceFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))
    fecha = db.Column(db.Date)
    proveedor = db.Column(db.String(120))
    total = db.Column(db.Float)
    archivo = db.Column(db.String(200))


# ============================
# CATEGORÍAS DE INSUMOS
# ============================
class CategoriaInsumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)


# ============================
# INSUMOS (CORRECTO Y ÚNICO)
# ============================
class Insumo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    unidad = db.Column(db.String(50), nullable=False)
    costo_unitario = db.Column(db.Float, nullable=False)

    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_insumo.id'))
    categoria = db.relationship('CategoriaInsumo', backref='insumos')


# ============================
# CÁLCULOS DE COSTOS
# ============================
class Calculo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    costo_total = db.Column(db.Float, nullable=False)
    margen = db.Column(db.Float, nullable=False)
    precio_final = db.Column(db.Float, nullable=False)
    items = db.relationship("CalculoItem", backref="calculo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Calculo {self.nombre}>"

class CalculoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    calculo_id = db.Column(db.Integer, db.ForeignKey('calculo.id'), nullable=False)
    insumo_id = db.Column(db.Integer, db.ForeignKey('insumo.id'), nullable=False)

    cantidad = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    insumo = db.relationship("Insumo")
