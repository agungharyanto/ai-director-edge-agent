from flask import Blueprint, jsonify

from app.modules.video.video_manager import VideoManager
from app.modules.dataset.dataset_manager import DatasetManager


dataset_bp = Blueprint("dataset", __name__)


@dataset_bp.route("/camera/<int:camera_id>/dataset/<category>", methods=["POST"])
def camera_dataset_capture(camera_id, category):
    vm = VideoManager()
    frame = vm.get_frame(camera_id)

    result = DatasetManager().capture(
        camera_id=camera_id,
        frame=frame,
        category=category
    )

    status = 200 if result.get("success") else 400

    return jsonify(result), status


@dataset_bp.route("/dataset/stats")
def dataset_stats():
    return jsonify({
        "success": True,
        "stats": DatasetManager().stats()
    })
