from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from a4service.models import db, Invoice, InvoiceItem, Product, Client
from datetime import datetime

facturas_bp = Blueprint("facturas", __name__, url_prefix="/facturas")


# ============================
# LISTAR FACTURAS
# ============================
@facturas_bp.route("/")
@login_required
def lista():
    facturas = Invoice.query.order_by(Invoice.id.desc()).all()
    return render_template("facturas.html", facturas=facturas)


# ============================
# NUEVA FACTURA
# ============================
@facturas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    clientes = Client.query.all()
    productos = Product.query.all()

    if request.method == "POST":
        cliente_id = request.form["client_id"]
        fecha = datetime.now()

        fac = Invoice(
            client_id=cliente_id,
            date=fecha,
            status="Pendiente",
            subtotal=0,
            tax=0,
            total=0
        )

        db.session.add(fac)
        db.session.commit()

        items = request.form.getlist("producto")
        cantidades = request.form.getlist("cantidad")
        precios = request.form.getlist("precio")

        subtotal = 0

        for i in range(len(items)):
            if not items[i]:
                continue

            item = InvoiceItem(
                invoice_id=fac.id,
                product_id=items[i],
                quantity=int(cantidades[i]),
                price=int(precios[i])
            )

            subtotal += item.quantity * item.price
            db.session.add(item)

        fac.subtotal = subtotal
        fac.tax = int(subtotal * 0.19)
        fac.total = fac.subtotal + fac.tax

        db.session.commit()

        flash("Factura creada correctamente")
        return redirect(url_for("facturas.lista"))

    return render_template("factura_nueva.html", clientes=clientes, productos=productos)


# ============================
# CAMBIAR ESTADO
# ============================
@facturas_bp.route("/estado/<int:id>/<string:nuevo_estado>")
@login_required
def cambiar_estado(id, nuevo_estado):
    fac = Invoice.query.get_or_404(id)

    if nuevo_estado not in ["Pagada", "Anulada", "Pendiente"]:
        flash("Estado inválido")
        return redirect(url_for("facturas.lista"))

    fac.status = nuevo_estado
    db.session.commit()

    flash(f"Estado cambiado a {nuevo_estado}")
    return redirect(url_for("facturas.lista"))


# ============================
# PDF DE FACTURA
# ============================
@facturas_bp.route("/pdf/<int:id>")
@login_required
def pdf(id):
    fac = Invoice.query.get_or_404(id)
    cliente = fac.client
    items = fac.items

    return render_template("factura_pdf.html", factura=fac, cliente=cliente, items=items)


# ============================
# ELIMINAR FACTURA
# ============================
@facturas_bp.route("/eliminar/<int:id>")
@login_required
def eliminar(id):
    fac = Invoice.query.get_or_404(id)

    for item in fac.items:
        db.session.delete(item)

    db.session.delete(fac)
    db.session.commit()

    flash("Factura eliminada correctamente")
    return redirect(url_for("facturas.lista"))
