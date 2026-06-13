from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required
from a4service.models import db, Insumo, Calculo, CalculoItem, CategoriaInsumo
from datetime import datetime
from weasyprint import HTML

costos_bp = Blueprint("costos", __name__, url_prefix="/costos")


# ============================
# LISTAR CÁLCULOS
# ============================
@costos_bp.route("/")
@login_required
def lista():
    calculos = Calculo.query.order_by(Calculo.id.desc()).all()
    return render_template("costos/lista.html", calculos=calculos)


# ============================
# NUEVO CÁLCULO
# ============================
@costos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    categorias = CategoriaInsumo.query.order_by(CategoriaInsumo.nombre.asc()).all()
    insumos = Insumo.query.order_by(Insumo.nombre.asc()).all()

    if request.method == "POST":
        nombre = request.form["nombre"]
        margen = float(request.form["margen"])

        costo_total = 0
        items = []

        for insumo in insumos:
            campo = f"insumo_{insumo.id}"
            cantidad_str = request.form.get(campo, "0")

            try:
                cantidad = float(cantidad_str) if cantidad_str else 0
            except ValueError:
                cantidad = 0

            if cantidad > 0:
                subtotal = cantidad * insumo.costo_unitario
                costo_total += subtotal

                items.append(
                    CalculoItem(
                        insumo_id=insumo.id,
                        cantidad=cantidad,
                        subtotal=subtotal
                    )
                )

        precio_final = costo_total + (costo_total * margen / 100)

        calc = Calculo(
            nombre=nombre,
            costo_total=costo_total,
            margen=margen,
            precio_final=precio_final,
            fecha=datetime.utcnow()
        )

        db.session.add(calc)
        db.session.flush()

        for item in items:
            item.calculo_id = calc.id
            db.session.add(item)

        db.session.commit()

        flash("Cálculo guardado correctamente", "success")
        return redirect(url_for("costos.lista"))

    return render_template("costos/nuevo.html", categorias=categorias, insumos=insumos)


# ============================
# ELIMINAR CÁLCULO
# ============================
@costos_bp.route("/eliminar/<int:id>")
@login_required
def eliminar(id):
    calc = Calculo.query.get_or_404(id)
    db.session.delete(calc)
    db.session.commit()
    flash("Cálculo eliminado correctamente", "success")
    return redirect(url_for("costos.lista"))


# ============================
# EXPORTAR PDF
# ============================
@costos_bp.route("/pdf/<int:id>")
@login_required
def pdf(id):
    calc = Calculo.query.get_or_404(id)

    html = render_template("costos/pdf.html", calc=calc)
    pdf = HTML(string=html).write_pdf()

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=calculo_{id}.pdf"

    return response


# ============================
# DUPLICAR CÁLCULO
# ============================
@costos_bp.route("/duplicar/<int:id>")
@login_required
def duplicar(id):
    original = Calculo.query.get_or_404(id)

    copia = Calculo(
        nombre=f"{original.nombre} (copia)",
        costo_total=original.costo_total,
        margen=original.margen,
        precio_final=original.precio_final,
        fecha=datetime.utcnow()
    )

    db.session.add(copia)
    db.session.flush()

    for item in original.items:
        nuevo_item = CalculoItem(
            calculo_id=copia.id,
            insumo_id=item.insumo_id,
            cantidad=item.cantidad,
            subtotal=item.subtotal
        )
        db.session.add(nuevo_item)

    db.session.commit()

    flash("Cálculo duplicado correctamente", "success")
    return redirect(url_for("costos.lista"))
