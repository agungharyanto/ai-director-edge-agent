from flask import render_template, jsonify, Response

from app.core.config import Config
from app.repositories.system_repository import SystemRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.court_repository import CourtRepository
from app.repositories.event_repository import EventRepository
from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService


def register_dashboard_routes(app):

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


    @app.route("/robots.txt")
    def robots_txt():
        return Response(
            "User-agent: *\nDisallow:\n",
            mimetype="text/plain"
        )
