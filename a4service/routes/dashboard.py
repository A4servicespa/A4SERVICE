from flask import Blueprint, render_template
from a4service.models import Invoice, Quotation, Product, Client, db

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
def dashboard():
    total_cotizaciones = Quotation.query.count()
    total_facturas = Invoice.query.count()
    total_productos = Product.query.count()
    total_clientes = Client.query.count()

    ventas_mes = {"labels": [], "data": []}
    cotizaciones_mes = {"labels": [], "data": []}
    estados_cotizaciones = {"labels": ["Aprobada", "Rechazada", "Pendiente"], "data": []}

    for mes in range(1, 13):
        ventas_mes["labels"].append(f"Mes {mes}")
        cotizaciones_mes["labels"].append(f"Mes {mes}")

        ventas_mes["data"].append(
            db.session.query(db.func.sum(Invoice.total))
            .filter(db.extract("month", Invoice.date) == mes)
            .scalar() or 0
        )

        cotizaciones_mes["data"].append(
            Quotation.query.filter(db.extract("month", Quotation.date) == mes).count()
        )

    for estado in estados_cotizaciones["labels"]:
        estados_cotizaciones["data"].append(
            Quotation.query.filter_by(status=estado).count()
        )

    return render_template(
        "dashboard.html",
        total_cotizaciones=total_cotizaciones,
        total_facturas=total_facturas,
        total_productos=total_productos,
        total_clientes=total_clientes,
        ventas_mes=ventas_mes,
        cotizaciones_mes=cotizaciones_mes,
        estados_cotizaciones=estados_cotizaciones
    )
