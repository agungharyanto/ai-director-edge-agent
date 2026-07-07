import cv2
from pathlib import Path
from datetime import datetime


class DatasetManager:

    BASE_PATH = Path("storage/datasets")
    ALLOWED_CATEGORIES = {
        "player",
        "ball",
        "court",
        "racket",
        "custom"
    }

    def ensure_dirs(self):
        for category in self.ALLOWED_CATEGORIES:
            (self.BASE_PATH / category / "raw").mkdir(parents=True, exist_ok=True)
            (self.BASE_PATH / category / "labeled").mkdir(parents=True, exist_ok=True)

    def count(self, category):
        if category not in self.ALLOWED_CATEGORIES:
            return 0

        path = self.BASE_PATH / category / "raw"
        path.mkdir(parents=True, exist_ok=True)

        return len(list(path.glob("*.jpg")))

    def stats(self):
        self.ensure_dirs()

        return {
            category: self.count(category)
            for category in sorted(self.ALLOWED_CATEGORIES)
        }

    def capture(self, camera_id, frame, category):
        if category not in self.ALLOWED_CATEGORIES:
            return {
                "success": False,
                "error": f"Invalid category: {category}"
            }

        if frame is None:
            return {
                "success": False,
                "error": "Frame tidak tersedia"
            }

        self.ensure_dirs()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"camera{camera_id}_{category}_{timestamp}.jpg"
        filepath = self.BASE_PATH / category / "raw" / filename

        ok = cv2.imwrite(str(filepath), frame)

        if not ok:
            return {
                "success": False,
                "error": "Gagal menyimpan frame"
            }

        return {
            "success": True,
            "category": category,
            "filename": filename,
            "path": str(filepath),
            "total": self.count(category)
        }
