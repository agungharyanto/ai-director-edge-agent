from flask import render_template, redirect, url_for

from app.repositories.event_repository import EventRepository


def register_event_routes(app):

    @app.route("/event")
    def event():
        events = EventRepository().all(100)
        return render_template("event/list.html", events=events)


    @app.route("/event/reset", methods=["POST"])
    def event_reset():
        EventRepository().clear()
        return redirect(url_for("event"))
