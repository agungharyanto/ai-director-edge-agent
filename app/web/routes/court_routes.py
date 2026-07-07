from flask import render_template, request, redirect, url_for

from app.repositories.court_repository import CourtRepository
from app.repositories.camera_repository import CameraRepository
from app.repositories.event_repository import EventRepository


def register_court_routes(app):

    @app.route("/court")
    def court():
        repo = CourtRepository()
        courts = repo.all()

        return render_template("court/list.html", courts=courts)


    @app.route("/court/<int:court_id>")
    def court_detail(court_id):
        court_repo = CourtRepository()
        camera_repo = CameraRepository()

        court_data = court_repo.find(court_id)
        cameras = camera_repo.by_court(court_data["uuid"])
        all_cameras = camera_repo.all()

        return render_template(
            "court/detail.html",
            court=court_data,
            cameras=cameras,
            all_cameras=all_cameras
        )


    @app.route("/court/<int:court_id>/assign-camera", methods=["POST"])
    def court_assign_camera(court_id):
        court_repo = CourtRepository()
        camera_repo = CameraRepository()

        court_data = court_repo.find(court_id)

        camera_repo.assign_position(
            camera_id=request.form.get("camera_id"),
            court_uuid=court_data["uuid"],
            position=request.form.get("position")
        )

        EventRepository().create(
            "COURT_CAMERA_ASSIGNED",
            "INFO",
            f"Camera ID {request.form.get('camera_id')} di-assign ke {court_data['name']} posisi {request.form.get('position')}"
        )

        return redirect(url_for("court_detail", court_id=court_id))


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
