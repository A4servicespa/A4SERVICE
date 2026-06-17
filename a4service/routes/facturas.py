from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, current_app
from flask_login import login_required
from a4service.models import db, Invoice, InvoiceItem, Product, Client
from datetime import datetime
from weasyprint import HTML
import os
import platform

from a4service import mail
from flask_mail import Message

facturas_bp = Blueprint("facturas", __name__, url_prefix="/facturas")


# LISTAR FACTURAS
@facturas_bp.route("/")
@login_required
def lista():
    facturas = Invoice.query.order_by(Invoice.id.desc()).all()
    return render_template("facturas.html", facturas=facturas)


# VER FACTURA
@facturas_bp.route("/ver/<int:id>")
@login_required
def ver(id):
    fac = Invoice.query.get_or_404(id)
    # asumimos relación: fac.client y fac.items (InvoiceItem)
    items = InvoiceItem.query.filter_by(invoice_id=fac.id).all()
    return render_template("factura_ver.html", factura=fac, cliente=fac.client, items=items)


# NUEVA FACTURA MANUAL
@facturas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    clientes = Client.query.all()
    productos = Product.query.all()

    if request.method == "POST":
        cliente_id = request.form["client_id"]
        fecha = datetime.utcnow()

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

        # IMPORTANTE: que coincida con los name del formulario
        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        subtotal = 0

        for i in range(len(product_ids)):
            if not product_ids[i]:
                continue

            item = InvoiceItem(
                invoice_id=fac.id,
                product_id=int(product_ids[i]),
                quantity=int(quantities[i]),
                price=float(prices[i])
            )
            db.session.add(item)
            subtotal += item.quantity * item.price

        fac.subtotal = subtotal
        fac.tax = subtotal * 0.19
        fac.total = fac.subtotal + fac.tax

        db.session.commit()

        flash("Factura creada correctamente", "success")
        return redirect(url_for("facturas.lista"))

    return render_template("factura_nueva.html", clientes=clientes, productos=productos)


# CAMBIAR ESTADO
@facturas_bp.route("/estado/<int:id>/<string:nuevo_estado>")
@login_required
def cambiar_estado(id, nuevo_estado):
    fac = Invoice.query.get_or_404(id)

    if nuevo_estado not in ["Pagada", "Anulada", "Pendiente"]:
        flash("Estado inválido", "danger")
        return redirect(url_for("facturas.lista"))

    fac.status = nuevo_estado
    db.session.commit()

    flash(f"Estado cambiado a {nuevo_estado}", "success")
    return redirect(url_for("facturas.lista"))


# GENERAR PDF FACTURA
def generar_pdf_factura(fac):
    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    items = InvoiceItem.query.filter_by(invoice_id=fac.id).all()

    html = render_template(
        "factura_pdf.html",
        factura=fac,
        cliente=fac.client,
        items=items,
        logo_path=logo_path
    )

    es_windows = platform.system() == "Windows"

    if es_windows:
        carpeta = os.path.join(current_app.root_path, "static", "uploads", "facturas")
    else:
        carpeta = "/data/facturas"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta, exist_ok=True)

    output_path = os.path.join(carpeta, f"factura_{fac.id}.pdf")

    HTML(string=html, base_url=current_app.root_path).write_pdf(output_path)
    return output_path


# DESCARGAR PDF
@facturas_bp.route("/pdf/<int:id>")
@login_required
def pdf(id):
    fac = Invoice.query.get_or_404(id)

    ruta_pdf = generar_pdf_factura(fac)

    if ruta_pdf and os.path.exists(ruta_pdf):
        return send_file(ruta_pdf, as_attachment=True, download_name=f"factura_{fac.id}.pdf")

    flash("Error al generar PDF", "danger")
    return redirect(url_for("facturas.ver", id=id))


# ENVIAR FACTURA POR CORREO
@facturas_bp.route("/enviar/<int:id>")
@login_required
def enviar_factura(id):
    fac = Invoice.query.get_or_404(id)
    items = InvoiceItem.query.filter_by(invoice_id=fac.id).all()

    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    html = render_template(
        "factura_pdf.html",
        factura=fac,
        cliente=fac.client,
        items=items,
        logo_path=logo_path
    )

    pdf_bytes = HTML(string=html, base_url=current_app.root_path).write_pdf()

    msg = Message(
        subject=f"Factura #{fac.id} - A4 Service",
        recipients=[fac.client.email],
        body=f"Estimado {fac.client.name}, adjuntamos su factura en formato PDF."
    )

    msg.attach(
        f"Factura_{fac.id}.pdf",
        "application/pdf",
        pdf_bytes
    )

    try:
        mail.send(msg)
        flash("Factura enviada correctamente", "success")
    except Exception:
        flash("No se pudo enviar la factura. Revise la configuración de correo.", "danger")

    return redirect(url_for("facturas.ver", id=id))


# ELIMINAR FACTURA
@facturas_bp.route("/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar(id):
    fac = Invoice.query.get_or_404(id)
    items = InvoiceItem.query.filter_by(invoice_id=id).all()

    for it in items:
        db.session.delete(it)

    db.session.delete(fac)
    db.session.commit()

    flash("Factura eliminada correctamente", "success")
    return redirect(url_for("facturas.lista"))
