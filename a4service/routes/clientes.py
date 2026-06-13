from flask import Blueprint, render_template, request, redirect, url_for, flash
from a4service.models import Client, db

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

@clientes_bp.route("/")
def lista():
    search = request.args.get("search", "")
    clientes = Client.query

    if search:
        clientes = clientes.filter(Client.name.ilike(f"%{search}%"))

    clientes = clientes.all()

    return render_template("clientes.html", clientes=clientes, search=search)


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    if request.method == "POST":
        c = Client(
            name=request.form["name"],
            email=request.form.get("email"),
            phone=request.form.get("phone"),
            company=request.form.get("company"),
            rut=request.form.get("rut")
        )
        db.session.add(c)
        db.session.commit()
        flash("Cliente creado correctamente", "success")
        return redirect(url_for("clientes.lista"))

    return render_template("cliente_nuevo.html")


@clientes_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    cliente = Client.query.get_or_404(id)

    if request.method == "POST":
        cliente.name = request.form["name"]
        cliente.email = request.form.get("email")
        cliente.phone = request.form.get("phone")
        cliente.company = request.form.get("company")
        cliente.rut = request.form.get("rut")

        db.session.commit()
        flash("Cliente actualizado", "success")
        return redirect(url_for("clientes.lista"))

    return render_template("cliente_editar.html", cliente=cliente)


@clientes_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    cliente = Client.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminado", "success")
    return redirect(url_for("clientes.lista"))
