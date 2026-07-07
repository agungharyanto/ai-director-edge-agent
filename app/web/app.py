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
from app.web.routes.inventory_routes import register_inventory_routes
from app.web.routes.health_routes import register_health_routes
from app.web.routes.discovery_routes import register_discovery_routes
from app.web.routes.credential_routes import register_credential_routes
from app.web.routes.event_routes import register_event_routes

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["SECRET_KEY"] = Config.SECRET_KEY

app.register_blueprint(dataset_bp)
register_camera_routes(app)
register_court_routes(app)
register_inventory_routes(app)
register_health_routes(app)
register_discovery_routes(app)
register_credential_routes(app)
register_event_routes(app)



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


@app.route("/robots.txt")
def robots_txt():
    return Response(
        "User-agent: *\nDisallow:\n",
        mimetype="text/plain"
    )



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





