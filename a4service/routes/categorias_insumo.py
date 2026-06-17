from flask import Blueprint, render_template, request, redirect, url_for, flash
from a4service.models import db, CategoriaInsumo

categorias_insumo_bp = Blueprint(
    "categorias_insumo",
    __name__,
    url_prefix="/categorias_insumo"
)

# LISTA
@categorias_insumo_bp.route("/")
def lista():
    categorias = CategoriaInsumo.query.order_by(CategoriaInsumo.nombre.asc()).all()
    return render_template("categorias_insumo/lista.html", categorias=categorias)

# NUEVA
@categorias_insumo_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form.get("descripcion")

        if CategoriaInsumo.query.filter_by(nombre=nombre).first():
            flash("Ya existe una categoría con ese nombre", "danger")
            return redirect(url_for("categorias_insumo.nuevo"))

        nueva_cat = CategoriaInsumo(nombre=nombre, descripcion=descripcion)
        db.session.add(nueva_cat)
        db.session.commit()

        flash("Categoría creada correctamente", "success")
        return redirect(url_for("categorias_insumo.lista"))

    return render_template("categorias_insumo/nuevo.html")

# EDITAR
@categorias_insumo_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    cat = CategoriaInsumo.query.get_or_404(id)

    if request.method == "POST":
        cat.nombre = request.form["nombre"]
        cat.descripcion = request.form.get("descripcion")
        db.session.commit()

        flash("Categoría actualizada correctamente", "success")
        return redirect(url_for("categorias_insumo.lista"))

    return render_template("categorias_insumo/editar.html", cat=cat)

# ELIMINAR
@categorias_insumo_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    cat = CategoriaInsumo.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()

    flash("Categoría eliminada correctamente", "success")
    return redirect(url_for("categorias_insumo.lista"))
