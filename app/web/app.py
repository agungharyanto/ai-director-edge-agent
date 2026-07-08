import uuid

from flask import Flask, render_template, request, redirect, url_for, jsonify
from app.modules.provisioning.profile_engine import ProfileEngine
from app.modules.provisioning.verify_engine import VerifyEngine
from app.modules.overlay.overlay_engine import OverlayEngine
from app.modules.video.video_manager import VideoManager

from app.core.config import Config
from app.web.bootstrap import register_routes
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

register_routes(app)

