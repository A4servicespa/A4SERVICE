from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from a4service.models import Quotation, QuotationItem, Client, Product, db
from datetime import datetime
import pandas as pd
import pdfkit
import tempfile
import os
import platform

cotizaciones_bp = Blueprint("cotizaciones", __name__, url_prefix="/cotizaciones")


# ---------------------------------------------------------
# LISTA DE COTIZACIONES
# ---------------------------------------------------------
@cotizaciones_bp.route("/")
def lista():
    cotizaciones = Quotation.query.order_by(Quotation.date.desc()).all()
    return render_template("cotizaciones.html", cotizaciones=cotizaciones)


# ---------------------------------------------------------
# CREAR COTIZACIÓN
# ---------------------------------------------------------
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

        for i in range(len(product_ids)):
            if not product_ids[i]:
                continue

            item = QuotationItem(
                quotation_id=cot.id,
                product_id=int(product_ids[i]),
                quantity=int(quantities[i]),
                price=float(prices[i])
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


# ---------------------------------------------------------
# EDITAR COTIZACIÓN
# ---------------------------------------------------------
@cotizaciones_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    cot = Quotation.query.get_or_404(id)
    clientes = Client.query.all()
    productos = Product.query.all()
    items = QuotationItem.query.filter_by(quotation_id=id).all()

    if request.method == "POST":
        cot.client_id = request.form["client_id"]
        cot.status = request.form["status"]
        cot.notes = request.form.get("notes")

        for item in items:
            db.session.delete(item)
        db.session.commit()

        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        subtotal = 0

        for i in range(len(product_ids)):
            if not product_ids[i]:
                continue

            item = QuotationItem(
                quotation_id=cot.id,
                product_id=int(product_ids[i]),
                quantity=int(quantities[i]),
                price=float(prices[i])
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


# ---------------------------------------------------------
# GENERAR PDF
# ---------------------------------------------------------
def generar_pdf_cotizacion(cot, items):
    html = render_template("cotizacion_pdf.html", cot=cot, items=items)

    es_windows = platform.system() == "Windows"

    if es_windows:
        carpeta = os.path.join(current_app.root_path, "static", "uploads", "facturas")
    else:
        carpeta = "/data/facturas"

    if not os.path.exists(carpeta):
        os.makedirs(carpeta, exist_ok=True)

    output_path = os.path.join(carpeta, f"cotizacion_{cot.id}.pdf")

    if es_windows:
        config = pdfkit.configuration(
            wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        )
    else:
        config = pdfkit.configuration()

    opciones = {
        "page-size": "A4",
        "encoding": "UTF-8",
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
        "enable-local-file-access": None
    }

    try:
        pdfkit.from_string(html, output_path, configuration=config, options=opciones)
        return output_path
    except Exception as e:
        print("ERROR PDF:", e)
        return None


# ---------------------------------------------------------
# DESCARGAR PDF
# ---------------------------------------------------------
@cotizaciones_bp.route("/pdf/<int:id>")
def cotizacion_pdf(id):
    cot = Quotation.query.get_or_404(id)
    items = QuotationItem.query.filter_by(quotation_id=id).all()

    ruta_pdf = generar_pdf_cotizacion(cot, items)

    if ruta_pdf and os.path.exists(ruta_pdf):
        return send_file(ruta_pdf, as_attachment=True, download_name=f"cotizacion_{cot.number}.pdf")

    flash("Error al generar PDF", "danger")
    return redirect(url_for("cotizaciones.lista"))


# ---------------------------------------------------------
# EXPORTAR A EXCEL — ENCABEZADO PROFESIONAL (Opción 1)
# ---------------------------------------------------------
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

    # -----------------------------
    # ESTILOS
    # -----------------------------
    titulo = workbook.add_format({
        "bold": True,
        "font_size": 18,
        "font_color": "#0A4A7A"
    })

    negrita = workbook.add_format({"bold": True})

    texto = workbook.add_format({
        "align": "left",
        "valign": "vcenter"
    })

    derecha = workbook.add_format({
        "align": "right",
        "valign": "vcenter"
    })

    borde = workbook.add_format({
        "border": 1,
        "border_color": "#CCCCCC",
        "align": "center",
        "valign": "vcenter"
    })

    header = workbook.add_format({
        "bold": True,
        "bg_color": "#0A4A7A",
        "font_color": "white",
        "border": 1,
        "align": "center",
        "valign": "vcenter"
    })

    moneda = workbook.add_format({
        "num_format": "$#,##0",
        "border": 1,
        "align": "right"
    })

    # Ajuste de columnas
    worksheet.set_column("A:A", 25)
    worksheet.set_column("B:B", 40)
    worksheet.set_column("C:D", 15)
    worksheet.set_column("E:F", 25)

    # -----------------------------
    # LOGO + DATOS EMPRESA + COTIZACIÓN (ALINEADOS)
    # -----------------------------
    logo_path = os.path.join(current_app.root_path, "static", "img", "logo.png")
    if os.path.exists(logo_path):
        worksheet.insert_image("A1", logo_path, {"x_scale": 0.25, "y_scale": 0.25})

    # Datos empresa (al lado del logo)
    worksheet.write("B1", "A4 SERVICE SPA", titulo)
    worksheet.write("B2", "RUT: 77.472.704-3", texto)
    worksheet.write("B3", "Dirección: Calle Río Toltén Nº32, El Melón, Nogales", texto)
    worksheet.write("B4", "Teléfonos: +56 9 5424 5660 / +56 9 3881 2474", texto)
    worksheet.write("B5", "Correo: A4servicespa@outlook.com", texto)

    # Número de cotización alineado con la columna de totales (columna D)
    worksheet.write("D1", f"COTIZACIÓN #{cot.number}", titulo)
    worksheet.write("D2", f"Fecha: {cot.date.strftime('%d-%m-%Y')}", derecha)
    worksheet.write("D3", f"Estado: {cot.status}", derecha)

    # -----------------------------
    # DATOS DEL CLIENTE
    # -----------------------------
    fila = 7
    worksheet.write(f"A{fila}", "Datos del Cliente", titulo)
    fila += 2

    worksheet.write(f"A{fila}", "Nombre:", negrita)
    worksheet.write(f"B{fila}", cot.client.name)
    fila += 1

    if cot.client.rut:
        worksheet.write(f"A{fila}", "RUT:", negrita)
        worksheet.write(f"B{fila}", cot.client.rut)
        fila += 1

    if cot.client.email:
        worksheet.write(f"A{fila}", "Correo:", negrita)
        worksheet.write(f"B{fila}", cot.client.email)
        fila += 1

    if cot.client.phone:
        worksheet.write(f"A{fila}", "Teléfono:", negrita)
        worksheet.write(f"B{fila}", cot.client.phone)
        fila += 1

    if cot.client.company:
        worksheet.write(f"A{fila}", "Empresa:", negrita)
        worksheet.write(f"B{fila}", cot.client.company)
        fila += 2

    # -----------------------------
    # TABLA DE PRODUCTOS
    # -----------------------------
    worksheet.write(f"A{fila}", "Producto", header)
    worksheet.write(f"B{fila}", "Cant.", header)
    worksheet.write(f"C{fila}", "Precio", header)
    worksheet.write(f"D{fila}", "Subtotal", header)

    fila += 1

    for item in items:
        worksheet.write(f"A{fila}", item.product.name, borde)
        worksheet.write(f"B{fila}", item.quantity, borde)
        worksheet.write(f"C{fila}", item.price, moneda)
        worksheet.write(f"D{fila}", item.subtotal(), moneda)
        fila += 1

    # -----------------------------
    # TOTALES
    # -----------------------------
    fila += 1
    worksheet.write(f"C{fila}", "Subtotal:", negrita)
    worksheet.write(f"D{fila}", cot.subtotal, moneda)

    fila += 1
    worksheet.write(f"C{fila}", "IVA (19%):", negrita)
    worksheet.write(f"D{fila}", cot.tax, moneda)

    fila += 1
    worksheet.write(f"C{fila}", "TOTAL:", titulo)
    worksheet.write(f"D{fila}", cot.total, moneda)

    # -----------------------------
    # NOTAS
    # -----------------------------
    fila += 3
    worksheet.write(f"A{fila}", "Notas / Condiciones:", titulo)
    fila += 1
    worksheet.write(f"A{fila}", cot.notes if cot.notes else "", texto)

    writer.close()

    return send_file(ruta_excel, as_attachment=True, download_name=f"cotizacion_{cot.number}.xlsx")


# ---------------------------------------------------------
# ELIMINAR COTIZACIÓN
# ---------------------------------------------------------
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
