import uuid
import cv2

from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
from app.modules.provisioning.profile_engine import ProfileEngine
from app.modules.provisioning.verify_engine import VerifyEngine
from app.modules.overlay.overlay_engine import OverlayEngine
from flask import Response
from app.modules.video.video_manager import VideoManager

from app.core.config import Config
from app.repositories.system_repository import SystemRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.court_repository import CourtRepository
from app.repositories.event_repository import EventRepository
from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService
from app.services.camera_monitor_service import CameraMonitorService
from app.modules.discovery.discovery_service import DiscoveryService
from app.repositories.discovery_repository import DiscoveryRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.credential_repository import CredentialRepository
from app.modules.drivers.hikvision_driver import HikvisionDriver
from app.web.routes.dataset_routes import dataset_bp
from app.web.routes.camera_routes import register_camera_routes
from app.web.routes.court_routes import register_court_routes

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["SECRET_KEY"] = Config.SECRET_KEY

app.register_blueprint(dataset_bp)
register_camera_routes(app)
register_court_routes(app)



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


@app.route("/robots.txt")
def robots_txt():
    return Response(
        "User-agent: *\nDisallow:\n",
        mimetype="text/plain"
    )


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
    network = request.form.get("network", "192.168.1.0/24")
    job = DiscoveryRepository().latest_job()

    if request.method == "POST":
        job_id = DiscoveryService().start_scan(network)
        return redirect(url_for("discovery", job_id=job_id))

    job_id = request.args.get("job_id")

    if job_id:
        job = DiscoveryRepository().get_job(job_id)

    return render_template(
        "discovery/index.html",
        network=network,
        job=job
    )


@app.route("/api/discovery/<int:job_id>")
def api_discovery_job(job_id):
    repo = DiscoveryRepository()
    job = repo.get_job(job_id)
    results = repo.results(job_id)

    return jsonify({
        "job": {
            "id": job["id"],
            "network": job["network"],
            "status": job["status"],
            "total_hosts": job["total_hosts"],
            "scanned_hosts": job["scanned_hosts"],
            "found_hosts": job["found_hosts"],
            "started_at": job["started_at"],
            "finished_at": job["finished_at"]
        },
        "results": [
            {
                "ip_address": row["ip_address"],
                "ping_status": row["ping_status"],
                "open_ports": row["open_ports"],
                "vendor": row["vendor"],
                "model": row["model"],
                "confidence": row["confidence"]
            }
            for row in results
        ]
    })


@app.route("/discovery/import", methods=["POST"])
def discovery_import():
    ip_address = request.form.get("ip_address")
    ports = request.form.get("ports", "")
    vendor = request.form.get("vendor", "Unknown")
    model = request.form.get("model", "-")

    rtsp_url = ""
    provision_status = "UNKNOWN"
    provision_message = ""

    if vendor == "Hikvision":
        creds = CredentialRepository().active_by_vendor("Hikvision")

        if creds:
            cred = creds[0]
            driver = HikvisionDriver()

            profile_result = ProfileEngine().provision(
                vendor=vendor,
                driver=driver,
                ip=ip_address,
                username=cred["username"],
                password=cred["password"]
            )

            rtsp_url = profile_result.get("rtsp_url", "")
            provision_status = "AI_READY" if profile_result.get("success") else "FAILED"
            provision_message = str(profile_result)

            EventRepository().create(
                "CAMERA_PROFILE_APPLIED" if provision_status == "AI_READY" else "CAMERA_PROFILE_FAILED",
                "INFO" if provision_status == "AI_READY" else "WARNING",
                f"Profile AI Director untuk {ip_address}: {profile_result}"
            )

        else:
            provision_status = "AUTH_REQUIRED"
            provision_message = "Credential Hikvision belum tersedia"

    if not rtsp_url and "554" in ports:
        rtsp_url = f"rtsp://username:password@{ip_address}:554/Streaming/Channels/101"

    camera_repo = CameraRepository()
    existing = camera_repo.find_by_ip(ip_address)

    if existing is None:
        camera_repo.create(
            name=f"{vendor} {model}" if model and model != "-" else f"Camera {ip_address}",
            ip_address=ip_address,
            rtsp_url=rtsp_url,
            vendor=vendor,
            model=model,
            court_uuid=None
        )

        camera_data = camera_repo.find_by_ip(ip_address)

        if camera_data:
            camera_repo.set_provision_status(
                camera_data["id"],
                provision_status,
                provision_message
            )

        EventRepository().create(
            "CAMERA_IMPORTED",
            "INFO",
            f"Camera hasil discovery diimport: {ip_address}"
        )

    else:
        camera_repo.set_provision_status(
            existing["id"],
            provision_status,
            provision_message
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

@app.route("/credential")
def credential():
    repo = CredentialRepository()
    credentials = repo.all()

    return render_template(
        "credential/list.html",
        credentials=credentials
    )


@app.route("/credential/create", methods=["GET", "POST"])
def credential_create():
    if request.method == "POST":
        CredentialRepository().create(
            vendor=request.form.get("vendor"),
            name=request.form.get("name"),
            username=request.form.get("username"),
            password=request.form.get("password"),
            priority=int(request.form.get("priority") or 100),
            enabled=1 if request.form.get("enabled") == "on" else 0
        )

        EventRepository().create(
            "CREDENTIAL_CREATED",
            "INFO",
            f"Credential profile dibuat untuk vendor {request.form.get('vendor')}"
        )

        return redirect(url_for("credential"))

    return render_template("credential/create.html")


@app.route("/inventory")
def inventory():
    repo = DeviceRepository()
    devices = repo.all()

    return render_template(
        "inventory/index.html",
        devices=devices
    )


if __name__ == "__main__":
    app.run(
        host=Config.WEB_HOST,
        port=Config.WEB_PORT,
        debug=True
    )
