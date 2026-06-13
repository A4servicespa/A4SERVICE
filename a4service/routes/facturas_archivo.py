from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from a4service.models import InvoiceFile, db
import os
from datetime import datetime

facturas_archivo_bp = Blueprint("facturas_archivo", __name__, url_prefix="/facturas-archivo")

UPLOAD_FOLDER = "a4service/static/uploads/facturas"

@facturas_archivo_bp.route("/")
def lista():
    facturas = InvoiceFile.query.order_by(InvoiceFile.fecha.desc()).all()
    return render_template("facturas_archivo/lista.html", facturas=facturas)

@facturas_archivo_bp.route("/subir", methods=["GET", "POST"])
def subir():
    if request.method == "POST":
        tipo = request.form["tipo"]
        proveedor = request.form["proveedor"]
        total = float(request.form["total"])
        fecha = datetime.strptime(request.form["fecha"], "%Y-%m-%d")

        archivo = request.files["archivo"]

        if archivo.filename == "":
            flash("Debe seleccionar un archivo PDF", "danger")
            return redirect(url_for("facturas_archivo.subir"))

        filename = secure_filename(archivo.filename)
        ruta = os.path.join(UPLOAD_FOLDER, filename)
        archivo.save(ruta)

        factura = InvoiceFile(
            tipo=tipo,
            proveedor=proveedor,
            total=total,
            fecha=fecha,
            archivo=ruta.replace("a4service/", "")
        )

        db.session.add(factura)
        db.session.commit()

        flash("Factura cargada correctamente", "success")
        return redirect(url_for("facturas_archivo.lista"))

    return render_template("facturas_archivo/subir.html")
