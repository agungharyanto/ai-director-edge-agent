from flask import render_template, request, redirect, url_for

from app.repositories.credential_repository import CredentialRepository
from app.repositories.event_repository import EventRepository


def register_credential_routes(app):

    @app.route("/credential")
    def credential():
        credentials = CredentialRepository().all()
        return render_template("credential/list.html", credentials=credentials)


    @app.route("/credential/create", methods=["GET", "POST"])
    def credential_create():
        if request.method == "POST":
            vendor = request.form.get("vendor")
            username = request.form.get("username")
            password = request.form.get("password")

            CredentialRepository().create(
                vendor=vendor,
                username=username,
                password=password
            )

            EventRepository().create(
                "CREDENTIAL_CREATED",
                "INFO",
                f"Credential baru dibuat untuk vendor {vendor}"
            )

            return redirect(url_for("credential"))

        return render_template("credential/create.html")
