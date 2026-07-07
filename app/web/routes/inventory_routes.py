from flask import render_template

from app.repositories.device_repository import DeviceRepository


def register_inventory_routes(app):

    @app.route("/inventory")
    def inventory():
        devices = DeviceRepository().all()
        return render_template("inventory/index.html", devices=devices)
