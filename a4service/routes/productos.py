from flask import Blueprint, render_template, request, redirect, url_for, flash
from a4service.models import Product, db

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")

@productos_bp.route("/")
def lista():
    search = request.args.get("search", "")
    productos = Product.query

    if search:
        productos = productos.filter(Product.name.ilike(f"%{search}%"))

    productos = productos.all()

    return render_template("productos.html", productos=productos, search=search)


@productos_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        p = Product(
            name=request.form["name"],
            price=float(request.form["price"]),
            stock=int(request.form["stock"]),
            stock_min=int(request.form["stock_min"]),
            description=request.form.get("description")
        )
        db.session.add(p)
        db.session.commit()
        flash("Producto creado correctamente", "success")
        return redirect(url_for("productos.lista"))

    return render_template("producto_nuevo.html")


@productos_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    producto = Product.query.get_or_404(id)

    if request.method == "POST":
        producto.name = request.form["name"]
        producto.price = float(request.form["price"])
        producto.stock = int(request.form["stock"])
        producto.stock_min = int(request.form["stock_min"])
        producto.description = request.form.get("description")

        db.session.commit()
        flash("Producto actualizado", "success")
        return redirect(url_for("productos.lista"))

    return render_template("producto_editar.html", producto=producto)


@productos_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    producto = Product.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash("Producto eliminado", "success")
    return redirect(url_for("productos.lista"))
