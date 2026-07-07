from flask import jsonify, redirect, url_for

from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService


def register_health_routes(app):

    @app.route("/health/collect")
    def health_collect():
        HealthService().collect()
        return redirect(url_for("dashboard"))


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
