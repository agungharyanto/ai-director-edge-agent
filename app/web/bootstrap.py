from app.web.routes.camera_routes import register_camera_routes
from app.web.routes.court_routes import register_court_routes
from app.web.routes.discovery_routes import register_discovery_routes
from app.web.routes.dataset_routes import dataset_bp
from app.web.routes.event_routes import register_event_routes
from app.web.routes.credential_routes import register_credential_routes
from app.web.routes.inventory_routes import register_inventory_routes
from app.web.routes.health_routes import register_health_routes
from app.web.routes.dashboard_routes import register_dashboard_routes


def register_routes(app):

    register_dashboard_routes(app)

    app.register_blueprint(dataset_bp)

    register_camera_routes(app)
    register_court_routes(app)
    register_discovery_routes(app)
    register_event_routes(app)
    register_credential_routes(app)
    register_inventory_routes(app)
    register_health_routes(app)
