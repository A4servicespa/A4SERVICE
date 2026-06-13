from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from a4service.models import db, Insumo, CategoriaInsumo

insumos_bp = Blueprint("insumos", __name__, url_prefix="/insumos")


# ============================
# LISTAR INSUMOS
# ============================
@insumos_bp.route("/")
@login_required
def lista():
    insumos = Insumo.query.order_by(Insumo.nombre.asc()).all()
    return render_template("insumos/lista.html", insumos=insumos)


# ============================
# NUEVO INSUMO
# ============================
@insumos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    categorias = CategoriaInsumo.query.order_by(CategoriaInsumo.nombre.asc()).all()

    if request.method == "POST":
        nombre = request.form["nombre"]
        unidad = request.form["unidad"]
        costo_unitario = float(request.form["costo_unitario"])
        categoria_id = request.form.get("categoria_id") or None

        insumo = Insumo(
            nombre=nombre,
            unidad=unidad,
            costo_unitario=costo_unitario,
            categoria_id=categoria_id
        )

        db.session.add(insumo)
        db.session.commit()

        flash("Insumo creado correctamente", "success")
        return redirect(url_for("insumos.lista"))

    return render_template("insumos/nuevo.html", categorias=categorias)


# ============================
# EDITAR INSUMO
# ============================
@insumos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    insumo = Insumo.query.get_or_404(id)
    categorias = CategoriaInsumo.query.order_by(CategoriaInsumo.nombre.asc()).all()

    if request.method == "POST":
        insumo.nombre = request.form["nombre"]
        insumo.unidad = request.form["unidad"]
        insumo.costo_unitario = float(request.form["costo_unitario"])
        insumo.categoria_id = request.form.get("categoria_id") or None

        db.session.commit()

        flash("Insumo actualizado correctamente", "success")
        return redirect(url_for("insumos.lista"))

    return render_template("insumos/editar.html", insumo=insumo, categorias=categorias)


# ============================
# ELIMINAR INSUMO
# ============================
@insumos_bp.route("/eliminar/<int:id>")
@login_required
def eliminar(id):
    insumo = Insumo.query.get_or_404(id)

    db.session.delete(insumo)
    db.session.commit()

    flash("Insumo eliminado correctamente", "success")
    return redirect(url_for("insumos.lista"))
