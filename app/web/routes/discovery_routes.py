from flask import render_template, request, redirect, url_for, jsonify

from app.modules.discovery.discovery_service import DiscoveryService
from app.repositories.discovery_repository import DiscoveryRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.event_repository import EventRepository


def register_discovery_routes(app):

    @app.route("/discovery", methods=["GET", "POST"])
    def discovery():
        repo = DiscoveryRepository()

        if request.method == "POST":
            subnet = request.form.get("subnet")
            method = request.form.get("method")

            job_id = DiscoveryService().run(subnet, method)

            return redirect(url_for("discovery"))

        jobs = repo.all()

        return render_template(
            "discovery/index.html",
            jobs=jobs
        )


    @app.route("/api/discovery/<int:job_id>")
    def api_discovery(job_id):
        repo = DiscoveryRepository()

        job = repo.find(job_id)
        devices = repo.devices(job_id)

        return jsonify({
            "job": dict(job) if job else None,
            "devices": [dict(device) for device in devices]
        })


    @app.route("/discovery/import", methods=["POST"])
    def discovery_import():
        selected = request.form.getlist("device_id")

        discovery_repo = DiscoveryRepository()
        device_repo = DeviceRepository()

        imported = 0

        for device_id in selected:
            device = discovery_repo.device_find(device_id)

            if not device:
                continue

            device_repo.upsert_from_discovery(device)
            imported += 1

        EventRepository().create(
            "DISCOVERY_IMPORT",
            "INFO",
            f"Import discovery selesai. Total device: {imported}"
        )

        return redirect(url_for("inventory"))
