from pathlib import Path
import json
from flask import request, jsonify, Response
from app.modules.streaming.director_mjpeg_stream import generate_director_mjpeg
from flask import render_template, request, redirect, url_for, jsonify, Response

from app.modules.provisioning.profile_engine import ProfileEngine
from app.modules.provisioning.verify_engine import VerifyEngine
from app.modules.overlay.overlay_engine import OverlayEngine
from app.modules.video.video_manager import VideoManager
from app.repositories.camera_repository import CameraRepository
from app.repositories.court_repository import CourtRepository
from app.repositories.event_repository import EventRepository
from app.repositories.credential_repository import CredentialRepository
from app.services.camera_monitor_service import CameraMonitorService
from app.modules.drivers.hikvision_driver import HikvisionDriver


def register_camera_routes(app):

    @app.route("/camera/<int:camera_id>/director-settings", methods=["GET", "POST"])
    def camera_director_settings(camera_id):
        settings_file = Path("storage/config/director_tuning.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)

        default = {
            "pan_speed": 0.055,
            "deadzone_x": 45,
            "deadzone_y": 80,
            "fixed_zoom": 1.35,
            "center_x": 0.50,
            "center_y": 0.50
        }

        try:
            if settings_file.exists():
                data = json.loads(settings_file.read_text())
            else:
                data = {}
        except Exception:
            data = {}

        cam_key = str(camera_id)

        if request.method == "GET":
            current = default.copy()
            current.update(data.get(cam_key, {}))
            return jsonify({"success": True, "settings": current})

        payload = request.get_json(silent=True) or {}

        current = default.copy()
        current.update(data.get(cam_key, {}))

        for key in ["pan_speed", "deadzone_x", "deadzone_y", "fixed_zoom", "center_x", "center_y"]:
            if key in payload:
                current[key] = payload[key]

        current["pan_speed"] = max(0.005, min(0.30, float(current["pan_speed"])))
        current["deadzone_x"] = max(0, min(300, int(float(current["deadzone_x"]))))
        current["deadzone_y"] = max(0, min(300, int(float(current["deadzone_y"]))))
        current["fixed_zoom"] = max(1.0, min(2.5, float(current["fixed_zoom"])))
        current["center_x"] = max(0.0, min(1.0, float(current["center_x"])))
        current["center_y"] = max(0.0, min(1.0, float(current["center_y"])))

        data[cam_key] = current
        settings_file.write_text(json.dumps(data, indent=2))

        return jsonify({"success": True, "settings": current})



    @app.route("/camera/<int:camera_id>/director-stream")
    def camera_director_stream(camera_id):
        camera_repo = CameraRepository()
        camera = camera_repo.find(camera_id)

        if camera is None:
            return "Camera tidak ditemukan", 404

        vm = VideoManager()
        vm.start_camera(camera)

        return Response(
            vm.director_mjpeg_generator(camera_id),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )



    @app.route("/camera/<int:camera_id>/virtual-ptz")
    def camera_virtual_ptz(camera_id):
        vm = VideoManager()

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "window": vm.get_virtual_ptz_window(camera_id)
        })



    @app.route("/camera/<int:camera_id>/director")
    def camera_director(camera_id):
        vm = VideoManager()

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "director": vm.get_director_decision(camera_id)
        })



    @app.route("/camera/<int:camera_id>/rally")
    def camera_rally(camera_id):
        vm = VideoManager()

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "rally": vm.get_rally(camera_id)
        })



    @app.route("/camera/<int:camera_id>/ball-trajectory")
    def camera_ball_trajectory(camera_id):
        vm = VideoManager()

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "trajectory": vm.get_ball_trajectory(camera_id)
        })



    @app.route("/camera/<int:camera_id>/object-history")
    def camera_object_history(camera_id):
        vm = VideoManager()

        return jsonify(
            vm.get_object_history(camera_id)
        )


    @app.route("/camera/<int:camera_id>/verify", methods=["POST"])
    def verify_camera(camera_id):
        camera_repo = CameraRepository()
        camera = camera_repo.find(camera_id)

        verify = VerifyEngine().verify(camera)

        if verify["overall"]:
            camera_repo.set_provision_status(
                camera_id,
                "AI_READY",
                str(verify)
            )
        else:
            camera_repo.set_provision_status(
                camera_id,
                "FAILED",
                str(verify)
            )

        EventRepository().create(
            "CAMERA_VERIFY",
            "INFO" if verify["overall"] else "WARNING",
            str(verify)
        )

        return redirect(url_for(
            "camera_detail",
            camera_id=camera_id
        ))


    @app.route("/api/camera/ping")
    def api_camera_ping():
        results = CameraMonitorService().check_all()

        return jsonify({
            "cameras": results
        })


    @app.route("/camera/<int:camera_id>/stream")
    def camera_stream(camera_id):
        repo = CameraRepository()
        camera = repo.find(camera_id)

        if camera is None:
            return "Camera tidak ditemukan", 404

        vm = VideoManager()
        vm.start_camera(camera)

        return Response(
            vm.mjpeg_generator(camera_id),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )



    @app.route("/camera/<int:camera_id>/stream-status")
    def camera_stream_status(camera_id):
        vm = VideoManager()
        return jsonify(vm.get_status(camera_id))



    @app.route("/camera/<int:camera_id>/stream-stop", methods=["POST"])
    def camera_stream_stop(camera_id):
        # Sprint 39 safety:
        # Jangan stop worker RTSP otomatis dari browser.
        # Stop mendadak saat MJPEG generator masih berjalan bisa memicu native crash FFmpeg/OpenCV.
        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "stopped": False,
            "message": "Stream worker kept alive"
        })





    @app.route("/camera/<int:camera_id>/player-detection/toggle", methods=["POST"])
    def camera_player_detection_toggle(camera_id):
        vm = VideoManager()
        enabled = vm.toggle_player_detection(camera_id)

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "enabled": enabled
        })



    @app.route("/camera/<int:camera_id>/player-detection/status")
    def camera_player_detection_status(camera_id):
        vm = VideoManager()

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "enabled": vm.is_player_detection_enabled(camera_id)
        })




    @app.route("/camera/<int:camera_id>/ball-detection/toggle", methods=["POST"])
    def camera_ball_detection_toggle(camera_id):
        vm = VideoManager()
        enabled = vm.toggle_ball_detection(camera_id)

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "enabled": enabled
        })



    @app.route("/camera/<int:camera_id>/ball-detection/status")
    def camera_ball_detection_status(camera_id):
        vm = VideoManager()

        return jsonify({
            "success": True,
            "camera_id": camera_id,
            "enabled": vm.is_ball_detection_enabled(camera_id)
        })






    @app.route("/camera/provision-all", methods=["POST"])
    def camera_provision_all():
        camera_repo = CameraRepository()
        cameras = camera_repo.all()

        total = 0
        success = 0
        failed = 0

        for camera in cameras:
            vendor = camera["vendor"]

            if vendor != "Hikvision":
                continue

            total += 1

            creds = CredentialRepository().active_by_vendor("Hikvision")

            if not creds:
                camera_repo.set_provision_status(
                    camera["id"],
                    "AUTH_REQUIRED",
                    "Credential Hikvision belum tersedia"
                )
                failed += 1
                continue

            cred = creds[0]
            driver = HikvisionDriver()

            profile_result = ProfileEngine().provision(
                vendor=vendor,
                driver=driver,
                ip=camera["ip_address"],
                username=cred["username"],
                password=cred["password"]
            )

            rtsp_url = profile_result.get("rtsp_url", camera["rtsp_url"])

            camera_repo.update(
                camera_id=camera["id"],
                name=camera["name"],
                ip_address=camera["ip_address"],
                rtsp_url=rtsp_url,
                vendor=camera["vendor"],
                model=camera["model"],
                court_uuid=camera["court_uuid"]
            )

            if profile_result.get("success"):
                camera_repo.set_provision_status(
                    camera["id"],
                    "AI_READY",
                    str(profile_result)
                )
                success += 1
            else:
                camera_repo.set_provision_status(
                    camera["id"],
                    "FAILED",
                    str(profile_result)
                )
                failed += 1

        EventRepository().create(
            "CAMERA_PROVISION_ALL",
            "INFO" if failed == 0 else "WARNING",
            f"Provision All selesai. Total={total}, Success={success}, Failed={failed}"
        )

        return redirect(url_for("camera"))



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



    @app.route("/camera/<int:camera_id>")
    def camera_detail(camera_id):
        camera_repo = CameraRepository()
        camera_data = camera_repo.find(camera_id)

        snapshot_url = f"/camera/{camera_id}/snapshot?ts=init"
        overlay = OverlayEngine.build(camera_data)

        return render_template(
            "camera/detail.html",
            camera=camera_data,
            snapshot_url=snapshot_url,
            overlay=overlay
        )


    @app.route("/camera/<int:camera_id>/calibration")
    def camera_calibration(camera_id):

        repo = CourtRepository()

        data = repo.get_camera_calibration(camera_id)

        if data is None:
            return jsonify({
                "success": False
            })

        return jsonify({
            "success": True,
            "top_left": [
                data["top_left_x"],
                data["top_left_y"]
            ],
            "top_right": [
                data["top_right_x"],
                data["top_right_y"]
            ],
            "bottom_right": [
                data["bottom_right_x"],
                data["bottom_right_y"]
            ],
            "bottom_left": [
                data["bottom_left_x"],
                data["bottom_left_y"]
            ]
        })


    @app.route(
        "/camera/<int:camera_id>/calibration",
        methods=["POST"]
    )
    def camera_calibration_save(camera_id):

        payload = request.get_json()

        CourtRepository().save_camera_calibration(
            camera_id,
            payload
        )

        return jsonify({
            "success": True
        })



    @app.route("/camera/<int:camera_id>/snapshot")
    def camera_snapshot(camera_id):
        camera_repo = CameraRepository()
        camera_data = camera_repo.find(camera_id)

        # Sementara Sprint 30 v1 pakai credential pertama Hikvision
        creds = CredentialRepository().active_by_vendor("Hikvision")

        if not creds:
            return Response("Credential Hikvision belum tersedia", status=401)

        cred = creds[0]

        driver = HikvisionDriver()

        url = driver.snapshot(camera_data["ip_address"])

        import requests

        auth = requests.auth.HTTPDigestAuth(
            cred["username"],
            cred["password"]
        )

        try:
            r = requests.get(
                url,
                auth=auth,
                timeout=5,
                verify=False
            )

            if r.status_code != 200:
                return Response(
                    f"Snapshot gagal. HTTP {r.status_code}",
                    status=500
                )

            return Response(
                r.content,
                mimetype="image/jpeg"
            )

        except Exception as error:
            return Response(
                f"Snapshot error: {error}",
                status=500
            )



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



    @app.route("/camera/<int:camera_id>/hide-osd", methods=["POST"])
    def camera_hide_osd(camera_id):
        camera_repo = CameraRepository()
        camera_data = camera_repo.find(camera_id)

        creds = CredentialRepository().active_by_vendor("Hikvision")
        if not creds:
            EventRepository().create("CAMERA_OSD_FAILED", "WARNING", "Credential Hikvision belum tersedia")
            return redirect(url_for("camera_detail", camera_id=camera_id))

        cred = creds[0]

        result = HikvisionDriver().hide_osd(
            camera_data["ip_address"],
            cred["username"],
            cred["password"]
        )

        if result.get("success"):
            EventRepository().create(
                "CAMERA_OSD_DISABLED",
                "INFO",
                f"OSD dimatikan untuk {camera_data['name']} ({camera_data['ip_address']})"
            )
        else:
            EventRepository().create(
                "CAMERA_OSD_FAILED",
                "WARNING",
                f"Gagal mematikan OSD untuk {camera_data['name']}: {result}"
            )

        return redirect(url_for("camera_detail", camera_id=camera_id))



    @app.route("/camera/<int:camera_id>/show-osd", methods=["POST"])
    def camera_show_osd(camera_id):
        camera_repo = CameraRepository()
        camera_data = camera_repo.find(camera_id)

        creds = CredentialRepository().active_by_vendor("Hikvision")
        if not creds:
            EventRepository().create("CAMERA_OSD_SHOW_FAILED", "WARNING", "Credential Hikvision belum tersedia")
            return redirect(url_for("camera_detail", camera_id=camera_id))

        cred = creds[0]

        result = HikvisionDriver().show_osd(
            camera_data["ip_address"],
            cred["username"],
            cred["password"]
        )

        EventRepository().create(
            "CAMERA_OSD_SHOW" if result.get("success") else "CAMERA_OSD_SHOW_FAILED",
            "INFO" if result.get("success") else "WARNING",
            f"Show OSD untuk {camera_data['name']}: {result}"
        )

        return redirect(url_for("camera_detail", camera_id=camera_id))



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



