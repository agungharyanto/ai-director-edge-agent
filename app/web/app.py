import uuid

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

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config["SECRET_KEY"] = Config.SECRET_KEY


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

@app.route("/health/collect")
def health_collect():
    HealthService().collect()
    return redirect(url_for("dashboard"))


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
    vm = VideoManager()
    vm.stop_camera(camera_id)

    return jsonify({
        "success": True,
        "camera_id": camera_id
    })


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
