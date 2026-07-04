import uuid

from flask import Flask, render_template, request, redirect, url_for, jsonify

from app.core.config import Config
from app.repositories.system_repository import SystemRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.court_repository import CourtRepository
from app.repositories.event_repository import EventRepository
from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService
from app.services.camera_monitor_service import CameraMonitorService
from app.modules.discovery.discovery_service import DiscoveryService

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["SECRET_KEY"] = Config.SECRET_KEY


@app.route("/")
def dashboard():
    system = SystemRepository()
    edge = system.bootstrap()

    court_repo = CourtRepository()
    camera_repo = CameraRepository()
    event_repo = EventRepository()
    health_repo = HealthRepository()

    events = event_repo.all(10)
    health = health_repo.latest()

    stats = {
        "court_total": court_repo.count(),
        "camera_total": camera_repo.count(),
        "camera_assigned": camera_repo.count_by_status("ASSIGNED"),
        "camera_new": camera_repo.count_by_status("NEW"),
        "camera_ping_up": camera_repo.count_by_ping_status("UP"),
        "camera_ping_down": camera_repo.count_by_ping_status("DOWN"),
        "camera_ping_unknown": camera_repo.count_by_ping_status("UNKNOWN"),
        "event_total": event_repo.count(),
    }

    if health is None:
        health = HealthService().collect()

    return render_template(
        "index.html",
        app_name=Config.APP_NAME,
        site_id=Config.SITE_ID,
        edge_id=Config.EDGE_ID,
        edge=edge,
        events=events,
        stats=stats,
        health=health
    )


@app.route("/health/collect")
def health_collect():
    HealthService().collect()
    return redirect(url_for("dashboard"))


@app.route("/api/camera/ping")
def api_camera_ping():
    results = CameraMonitorService().check_all()

    return jsonify({
        "cameras": results
    })


@app.route("/api/health")
def api_health():
    HealthService().collect()

    latest = HealthRepository().latest()
    history_rows = HealthRepository().history(30)

    history = []
    for row in reversed(history_rows):
        history.append({
            "cpu": row["cpu"],
            "ram": row["ram"],
            "disk": row["disk"],
            "created_at": row["created_at"]
        })

    return jsonify({
        "cpu": latest["cpu"],
        "ram": latest["ram"],
        "disk": latest["disk"],
        "temperature": latest["temperature"],
        "created_at": latest["created_at"],
        "history": history
    })


@app.route("/court")
def court():
    repo = CourtRepository()
    courts = repo.all()

    return render_template("court/list.html", courts=courts)


@app.route("/court/create", methods=["GET", "POST"])
def court_create():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")

        repo = CourtRepository()
        repo.create(name, description)

        event_repo = EventRepository()
        event_repo.create(
            "COURT_CREATED",
            "INFO",
            f"Court baru dibuat: {name}"
        )

        return redirect(url_for("court"))

    return render_template("court/create.html")


@app.route("/camera/bulk-rtsp", methods=["GET", "POST"])
def camera_bulk_rtsp():
    camera_repo = CameraRepository()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        rtsp_path = request.form.get("rtsp_path")
        vendor_filter = request.form.get("vendor_filter")

        cameras = camera_repo.all()
        updated = 0

        for camera in cameras:
            if vendor_filter and vendor_filter != "ALL":
                if camera["vendor"] != vendor_filter:
                    continue

            rtsp_url = f"rtsp://{username}:{password}@{camera['ip_address']}:554{rtsp_path}"

            camera_repo.update(
                camera_id=camera["id"],
                name=camera["name"],
                ip_address=camera["ip_address"],
                rtsp_url=rtsp_url,
                vendor=camera["vendor"],
                model=camera["model"],
                court_uuid=camera["court_uuid"]
            )

            updated += 1

        EventRepository().create(
            "CAMERA_BULK_RTSP_UPDATED",
            "INFO",
            f"Bulk update RTSP selesai. Total kamera diupdate: {updated}"
        )

        return redirect(url_for("camera"))

    vendors = []
    for camera in camera_repo.all():
        vendor = camera["vendor"] or "Unknown"
        if vendor not in vendors:
            vendors.append(vendor)

    return render_template(
        "camera/bulk_rtsp.html",
        vendors=vendors
    )


@app.route("/camera")
def camera():
    repo = CameraRepository()
    cameras = repo.all()

    return render_template("camera/list.html", cameras=cameras)


@app.route("/camera/create", methods=["GET", "POST"])
def camera_create():
    court_repo = CourtRepository()
    courts = court_repo.all()

    if request.method == "POST":
        name = request.form.get("name")

        camera_repo = CameraRepository()
        camera_repo.create(
            name=name,
            ip_address=request.form.get("ip_address"),
            rtsp_url=request.form.get("rtsp_url"),
            vendor=request.form.get("vendor"),
            model=request.form.get("model"),
            court_uuid=request.form.get("court_uuid") or None
        )

        event_repo = EventRepository()
        event_repo.create(
            "CAMERA_CREATED",
            "INFO",
            f"Camera baru dibuat: {name}"
        )

        return redirect(url_for("camera"))

    return render_template("camera/create.html", courts=courts)


@app.route("/camera/<int:camera_id>/edit", methods=["GET", "POST"])
def camera_edit(camera_id):
    camera_repo = CameraRepository()
    court_repo = CourtRepository()

    camera_data = camera_repo.find(camera_id)
    courts = court_repo.all()

    if request.method == "POST":
        name = request.form.get("name")

        camera_repo.update(
            camera_id=camera_id,
            name=name,
            ip_address=request.form.get("ip_address"),
            rtsp_url=request.form.get("rtsp_url"),
            vendor=request.form.get("vendor"),
            model=request.form.get("model"),
            court_uuid=request.form.get("court_uuid") or None
        )

        event_repo = EventRepository()
        event_repo.create(
            "CAMERA_UPDATED",
            "INFO",
            f"Camera diupdate: {name}"
        )

        return redirect(url_for("camera"))

    return render_template(
        "camera/edit.html",
        camera=camera_data,
        courts=courts
    )


@app.route("/camera/<int:camera_id>/delete", methods=["POST"])
def camera_delete(camera_id):
    repo = CameraRepository()
    camera_data = repo.find(camera_id)

    camera_name = camera_data["name"] if camera_data else f"ID {camera_id}"

    repo.delete(camera_id)

    event_repo = EventRepository()
    event_repo.create(
        "CAMERA_DELETED",
        "WARNING",
        f"Camera dihapus: {camera_name}"
    )

    return redirect(url_for("camera"))


@app.route("/api/dashboard/stats")
def api_dashboard_stats():
    camera_repo = CameraRepository()
    event_repo = EventRepository()

    return jsonify({
        "camera_ping_up": camera_repo.count_by_ping_status("UP"),
        "camera_ping_down": camera_repo.count_by_ping_status("DOWN"),
        "camera_ping_unknown": camera_repo.count_by_ping_status("UNKNOWN"),
        "event_total": event_repo.count()
    })


@app.route("/event/reset", methods=["POST"])
def event_reset():
    EventRepository().reset()
    return redirect(url_for("event"))


@app.route("/discovery", methods=["GET", "POST"])
def discovery():
    results = []
    network = request.form.get("network", "192.168.1.0/24")

    if request.method == "POST":
        results = DiscoveryService().scan_network(network)

    return render_template(
        "discovery/index.html",
        results=results,
        network=network
    )


@app.route("/discovery/import", methods=["POST"])
def discovery_import():
    ip_address = request.form.get("ip_address")
    ports = request.form.get("ports", "")
    vendor = request.form.get("vendor", "Unknown")
    model = request.form.get("model", "-")

    rtsp_url = ""

    if "554" in ports:
        rtsp_url = f"rtsp://username:password@{ip_address}:554/Streaming/Channels/101"

    camera_repo = CameraRepository()

    existing = None
    for camera in camera_repo.all():
        if camera["ip_address"] == ip_address:
            existing = camera
            break

    if existing is None:
        camera_repo.create(
            name=f"Camera {ip_address}",
            ip_address=ip_address,
            rtsp_url=rtsp_url,
            vendor=vendor,
            model=model,
            court_uuid=None
        )

        EventRepository().create(
            "CAMERA_IMPORTED",
            "INFO",
            f"Camera hasil discovery diimport: {ip_address}"
        )

    return redirect(url_for("camera"))


@app.route("/event")
def event():
    repo = EventRepository()

    event_type = request.args.get("type") or None
    level = request.args.get("level") or None
    message = request.args.get("message") or None
    start_time = request.args.get("start_time") or None
    end_time = request.args.get("end_time") or None

    if start_time:
        start_time = start_time.replace("T", " ")

    if end_time:
        end_time = end_time.replace("T", " ")

    events = repo.all(
        limit=100,
        event_type=event_type,
        level=level,
        message=message,
        start_time=start_time,
        end_time=end_time
    )

    return render_template(
        "event/list.html",
        events=events,
        types=repo.distinct_types(),
        levels=repo.distinct_levels(),
        selected_type=event_type,
        selected_level=level,
        selected_message=message or "",
        selected_start_time=start_time or "",
        selected_end_time=end_time or ""
    )


if __name__ == "__main__":
    app.run(
        host=Config.WEB_HOST,
        port=Config.WEB_PORT,
        debug=True
    )
