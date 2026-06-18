from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from a4service.models import Quotation, QuotationItem, Client, Product, Invoice, InvoiceItem, db
from datetime import datetime
import pandas as pd
from weasyprint import HTML
import tempfile
import os
import platform

from a4service import mail
from flask_mail import Message

cotizaciones_bp = Blueprint("cotizaciones", __name__, url_prefix="/cotizaciones")


# ============================================================
# LISTA DE COTIZACIONES
# ============================================================
@cotizaciones_bp.route("/")
def lista():
    cotizaciones = Quotation.query.order_by(Quotation.date.desc()).all()
    return render_template("cotizaciones.html", cotizaciones=cotizaciones)


# ============================================================
# NUEVA COTIZACIÓN
# ============================================================
@cotizaciones_bp.route("/nueva", methods=["GET", "POST"])
def nueva():
    clientes = Client.query.all()
    productos = Product.query.all()

    if request.method == "POST":
        ultimo = Quotation.query.order_by(Quotation.number.desc()).first()
        nuevo_numero = 1 if not ultimo else ultimo.number + 1

        cot = Quotation(
            number=nuevo_numero,
            client_id=request.form["client_id"],
            date=datetime.utcnow(),
            status="Pendiente",
            notes=request.form.get("notes")
        )
        db.session.add(cot)
        db.session.commit()

        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        subtotal = 0

        for pid, qty, price in zip(product_ids, quantities, prices):
            pid = pid.strip()
            qty = qty.strip()
            price = price.strip()

            if not pid or not qty or not price:
                continue

            try:
                pid_int = int(pid)
                qty_int = int(qty)
                price_float = float(price)
            except:
                continue

            item = QuotationItem(
                quotation_id=cot.id,
                product_id=pid_int,
                quantity=qty_int,
                price=price_float
            )
            db.session.add(item)
            subtotal += item.subtotal()

        cot.subtotal = subtotal
        cot.tax = subtotal * 0.19
        cot.total = subtotal + cot.tax

        db.session.commit()

        flash("Cotización creada correctamente", "success")
        return redirect(url_for("cotizaciones.lista"))

    return render_template("cotizacion_nueva.html", clientes=clientes, productos=productos)


# ============================================================
# EDITAR COTIZACIÓN
# ============================================================
@cotizaciones_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    cot = Quotation.query.get_or_404(id)
    clientes = Client.query.all()
    productos = Product.query.all()
    items = QuotationItem.query.filter_by(quotation_id=id).all()

    if request.method == "POST":

        cot.client_id = request.form["client_id"]
        cot.status = request.form.get("status", cot.status)
        cot.notes = request.form.get("notes")

        for item in items:
            db.session.delete(item)
        db.session.commit()

        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        subtotal = 0

        for pid, qty, price in zip(product_ids, quantities, prices):
            pid = pid.strip()
            qty = qty.strip()
            price = price.strip()

            if not pid or not qty or not price:
                continue

            try:
                pid_int = int(pid)
                qty_int = int(qty)
                price_float = float(price)
            except:
                continue

            item = QuotationItem(
                quotation_id=cot.id,
                product_id=pid_int,
                quantity=qty_int,
                price=price_float
            )
            db.session.add(item)
            subtotal += item.subtotal()

        cot.subtotal = subtotal
        cot.tax = subtotal * 0.19
        cot.total = subtotal + cot.tax

        db.session.commit()

        flash("Cotización actualizada correctamente", "success")
        return redirect(url_for("cotizaciones.lista"))

    return render_template(
        "cotizacion_editar.html",
        cot=cot,
        clientes=clientes,
        productos=productos,
        items=items
    )


# ============================================================
# FACTURAR COTIZACIÓN (placeholder)
# ============================================================
@cotizaciones_bp.route("/facturar/<int:id>")
def facturar(id):
    return redirect(url_for("cotizaciones.editar", id=id))


# ============================================================
# GENERAR PDF (CORREGIDO)
# ============================================================
def generar_pdf_cotizacion(cot, items):
    # Ruta absoluta local del logo
    logo_path = os.path.join(current_app.static_folder, "img", "logo.png")

    # Render HTML
    html = render_template(
        "cotizacion_pdf.html",
        cot=cot,
        items=items,
        logo_path=logo_path
    )

    # Carpeta de salida
    es_windows = platform.system() == "Windows"
    if es_windows:
        carpeta = os.path.join(current_app.root_path, "static", "uploads", "facturas")
    else:
        carpeta = "/data/facturas"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta, exist_ok=True)

    output_path = os.path.join(carpeta, f"cotizacion_{cot.id}.pdf")

    # Generar PDF
    HTML(string=html, base_url=current_app.static_folder).write_pdf(output_path)

    return output_path


# ============================================================
# DESCARGAR PDF
# ============================================================
@cotizaciones_bp.route("/pdf/<int:id>")
def cotizacion_pdf(id):
    cot = Quotation.query.get_or_404(id)
    items = QuotationItem.query.filter_by(quotation_id=id).all()

    ruta_pdf = generar_pdf_cotizacion(cot, items)

    if ruta_pdf and os.path.exists(ruta_pdf):
        return send_file(ruta_pdf, as_attachment=True, download_name=f"cotizacion_{cot.number}.pdf")

    flash("Error al generar PDF", "danger")
    return redirect(url_for("cotizaciones.lista"))


# ============================================================
# EXPORTAR A EXCEL (CORPORATIVO)
# ============================================================
@cotizaciones_bp.route("/excel/<int:id>")
def cotizacion_excel(id):
    cot = Quotation.query.get_or_404(id)
    items = QuotationItem.query.filter_by(quotation_id=id).all()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        ruta_excel = tmp.name

    writer = pd.ExcelWriter(ruta_excel, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet("Cotización")
    writer.sheets["Cotización"] = worksheet

    # FORMATO CORPORATIVO
    bold = workbook.add_format({'bold': True})
    title = workbook.add_format({'bold': True, 'font_size': 14})
    header = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9', 'border': 1})
    cell = workbook.add_format({'border': 1})
    money = workbook.add_format({'num_format': '$#,##0', 'border': 1})
    separator = workbook.add_format({'bottom': 2})

    # Ajuste de columnas
    worksheet.set_column("A:A", 35)
    worksheet.set_column("B:D", 15)

    # LOGO
    logo_path = os.path.join(current_app.static_folder, "img", "logo.png")
    if os.path.exists(logo_path):
        worksheet.insert_image("A1", logo_path, {"x_scale": 0.5, "y_scale": 0.5})

    # DATOS DE LA EMPRESA
    worksheet.write("C1", "A4 SERVICE SPA", title)
    worksheet.write("C2", "RUT: 77.472.704-3")
    worksheet.write("C3", "Calle Río Toltén N° 32, Población La Unión")
    worksheet.write("C4", "El Melón, Nogales")
    worksheet.write("C5", "Tel: +56 9 5424 5660 / +56 9 3881 2474")
    worksheet.write("C6", "Email: A4servicespa@outlook.com")

    worksheet.write("A8", "", separator)

    # ENCABEZADO DE COTIZACIÓN
    worksheet.write("A10", f"Cotización #{cot.number}", title)
    worksheet.write("A11", f"Fecha: {cot.date.strftime('%d-%m-%Y')}")
    worksheet.write("A12", f"Estado: {cot.status}")

    # DATOS DEL CLIENTE
    worksheet.write("A14", "Datos del Cliente", bold)
    worksheet.write("A15", "Nombre:")
    worksheet.write("B15", cot.client.name)

    worksheet.write("A16", "Empresa:")
    worksheet.write("B16", cot.client.company or "")

    worksheet.write("A17", "RUT:")
    worksheet.write("B17", cot.client.rut or "")

    worksheet.write("A18", "Email:")
    worksheet.write("B18", cot.client.email or "")

    worksheet.write("A19", "Teléfono:")
    worksheet.write("B19", cot.client.phone or "")

    # TABLA DE ITEMS
    start_row = 22
    worksheet.write(start_row, 0, "Producto / Servicio", header)
    worksheet.write(start_row, 1, "Cantidad", header)
    worksheet.write(start_row, 2, "Precio Unitario", header)
    worksheet.write(start_row, 3, "Subtotal", header)

    row = start_row + 1

    for item in items:
        worksheet.write(row, 0, item.product.name, cell)
        worksheet.write(row, 1, item.quantity, cell)
        worksheet.write(row, 2, item.price, money)
        worksheet.write(row, 3, item.quantity * item.price, money)
        row += 1

    # TOTALES
    worksheet.write(row + 1, 2, "Subtotal:", bold)
    worksheet.write(row + 1, 3, cot.subtotal, money)

    worksheet.write(row + 2, 2, "IVA (19%):", bold)
    worksheet.write(row + 2, 3, cot.tax, money)

    worksheet.write(row + 3, 2, "TOTAL:", title)
    worksheet.write(row + 3, 3, cot.total, money)

    # NOTAS
    if cot.notes:
        worksheet.write(row + 5, 0, "Notas:", bold)
        worksheet.write(row + 6, 0, cot.notes)

    writer.close()

    return send_file(ruta_excel, as_attachment=True, download_name=f"cotizacion_{cot.number}.xlsx")


# ============================================================
# ENVIAR EXCEL POR CORREO
# ============================================================
@cotizaciones_bp.route("/enviar_excel/<int:id>")
def enviar_excel(id):
    cot = Quotation.query.get_or_404(id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        ruta_excel = tmp.name

    writer = pd.ExcelWriter(ruta_excel, engine="xlsxwriter")
    workbook = writer.book
    worksheet = workbook.add_worksheet("Cotización")
    writer.sheets["Cotización"] = worksheet

    worksheet.write("A1", f"Cotización #{cot.number}")
    writer.close()

    with open(ruta_excel, "rb") as f:
        excel_bytes = f.read()

    msg = Message(
        subject=f"Cotización #{cot.number} - A4 Service",
        recipients=[cot.client.email],
        body=f"Estimado {cot.client.name}, adjuntamos su cotización en formato Excel."
    )

    msg.attach(
        f"Cotizacion_{cot.number}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        excel_bytes
    )

    mail.send(msg)

    flash("Cotización enviada en Excel correctamente", "success")
    return redirect(url_for("cotizaciones.lista"))


# ============================================================
# ELIMINAR COTIZACIÓN
# ============================================================
@cotizaciones_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    cot = Quotation.query.get_or_404(id)

    items = QuotationItem.query.filter_by(quotation_id=id).all()
    for item in items:
        db.session.delete(item)

    db.session.delete(cot)
    db.session.commit()

    flash("Cotización eliminada correctamente", "success")
    return redirect(url_for("cotizaciones.lista"))
