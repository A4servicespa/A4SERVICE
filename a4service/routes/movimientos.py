from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from a4service.models import db, Movement, Product
from datetime import datetime

movimientos_bp = Blueprint("movimientos", __name__, url_prefix="/movimientos")


@movimientos_bp.route("/")
@login_required
def lista():
    movimientos = Movement.query.order_by(Movement.id.desc()).all()
    return render_template("movimientos.html", movimientos=movimientos)


@movimientos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    productos = Product.query.all()

    if request.method == "POST":
        tipo = request.form["type"]              # Entrada / Salida
        producto_id = request.form["product_id"]
        cantidad = int(request.form["quantity"])
        motivo = request.form.get("reason", "")
        fecha = datetime.now()

        mov = Movement(
            type=tipo,
            product_id=producto_id,
            quantity=cantidad,
            reason=motivo,
            date=fecha
        )

        producto = Product.query.get(producto_id)

        if tipo == "Entrada":
            producto.stock += cantidad
        elif tipo == "Salida":
            if producto.stock < cantidad:
                flash("Stock insuficiente")
                return redirect(url_for("movimientos.nuevo"))
            producto.stock -= cantidad

        db.session.add(mov)
        db.session.commit()

        flash("Movimiento registrado correctamente")
        return redirect(url_for("movimientos.lista"))

    return render_template("movimiento_nuevo.html", productos=productos)


@movimientos_bp.route("/eliminar/<int:id>")
@login_required
def eliminar(id):
    mov = Movement.query.get_or_404(id)
    producto = mov.product

    if mov.type == "Entrada":
        producto.stock -= mov.quantity
    elif mov.type == "Salida":
        producto.stock += mov.quantity

    db.session.delete(mov)
    db.session.commit()

    flash("Movimiento eliminado correctamente")
    return redirect(url_for("movimientos.lista"))
