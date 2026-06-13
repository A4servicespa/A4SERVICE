from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from a4service.models import db, CategoriaInsumo

categorias_insumo_bp = Blueprint("categorias_insumo", __name__, url_prefix="/categorias_insumo")


# ============================
# LISTAR CATEGORÍAS
# ============================
@categorias_insumo_bp.route("/")
@login_required
def lista():
    categorias = CategoriaInsumo.query.order_by(CategoriaInsumo.nombre.asc()).all()
    return render_template("categorias_insumo/lista.html", categorias=categorias)


# ============================
# NUEVA CATEGORÍA
# ============================
@categorias_insumo_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if request.method == "POST":
        nombre = request.form["nombre"]

        categoria = CategoriaInsumo(nombre=nombre)
        db.session.add(categoria)
        db.session.commit()

        flash("Categoría creada correctamente", "success")
        return redirect(url_for("categorias_insumo.lista"))

    return render_template("categorias_insumo/nuevo.html")


# ============================
# EDITAR CATEGORÍA
# ============================
@categorias_insumo_bp.route("/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar(id):
    categoria = CategoriaInsumo.query.get_or_404(id)

    if request.method == "POST":
        categoria.nombre = request.form["nombre"]
        db.session.commit()

        flash("Categoría actualizada correctamente", "success")
        return redirect(url_for("categorias_insumo.lista"))

    return render_template("categorias_insumo/editar.html", categoria=categoria)


# ============================
# ELIMINAR CATEGORÍA
# ============================
@categorias_insumo_bp.route("/eliminar/<int:id>")
@login_required
def eliminar(id):
    categoria = CategoriaInsumo.query.get_or_404(id)

    db.session.delete(categoria)
    db.session.commit()

    flash("Categoría eliminada correctamente", "success")
    return redirect(url_for("categorias_insumo.lista"))
