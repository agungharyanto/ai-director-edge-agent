import time
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Box:
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class CropState:
    cx: float
    cy: float
    zoom: float


class SmoothDirector:
    def __init__(
        self,
        frame_w: int,
        frame_h: int,
        min_zoom: float = 1.0,
        max_zoom: float = 2.6,
        target_fill: float = 0.68,
        deadzone_px: float = 55,
        zoom_deadzone: float = 0.07,
        pan_speed: float = 0.065,
        zoom_speed: float = 0.018,
        prediction_strength: float = 0.45,
    ):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.target_fill = target_fill
        self.deadzone_px = deadzone_px
        self.zoom_deadzone = zoom_deadzone
        self.pan_speed = pan_speed
        self.zoom_speed = zoom_speed
        self.prediction_strength = prediction_strength

        self.state = CropState(frame_w / 2, frame_h / 2, 1.0)
        self.last_target_cx = self.state.cx
        self.last_target_cy = self.state.cy
        self.last_time = time.time()

    def update(self, boxes: List[Box]) -> Tuple[int, int, int, int]:
        if not boxes:
            return self._crop_from_state()

        now = time.time()
        dt = max(now - self.last_time, 0.001)
        self.last_time = now

        b = self._combine_boxes(boxes)

        raw_cx = (b.x1 + b.x2) / 2
        raw_cy = (b.y1 + b.y2) / 2

        vx = (raw_cx - self.last_target_cx) / dt
        vy = (raw_cy - self.last_target_cy) / dt

        self.last_target_cx = raw_cx
        self.last_target_cy = raw_cy

        speed = (vx * vx + vy * vy) ** 0.5

        prediction_px = min(speed * self.prediction_strength * dt, 160)

        if speed > 1:
            pred_cx = raw_cx + (vx / speed) * prediction_px
            pred_cy = raw_cy + (vy / speed) * prediction_px
        else:
            pred_cx = raw_cx
            pred_cy = raw_cy

        margin = self._adaptive_margin(speed)

        box_w = (b.x2 - b.x1) + margin * 2
        box_h = (b.y2 - b.y1) + margin * 2

        zoom_x = self.frame_w * self.target_fill / max(box_w, 1)
        zoom_y = self.frame_h * self.target_fill / max(box_h, 1)

        target_zoom = min(zoom_x, zoom_y)
        target_zoom = max(self.min_zoom, min(self.max_zoom, target_zoom))

        self._smooth_pan(pred_cx, pred_cy)
        self._smooth_zoom(target_zoom)

        return self._crop_from_state()

    def _combine_boxes(self, boxes: List[Box]) -> Box:
        return Box(
            min(b.x1 for b in boxes),
            min(b.y1 for b in boxes),
            max(b.x2 for b in boxes),
            max(b.y2 for b in boxes),
        )

    def _adaptive_margin(self, speed: float) -> float:
        return 90 + min(speed * 0.035, 170)

    def _smooth_pan(self, target_cx: float, target_cy: float):
        dx = target_cx - self.state.cx
        dy = target_cy - self.state.cy

        if abs(dx) > self.deadzone_px:
            self.state.cx += dx * self.pan_speed

        if abs(dy) > self.deadzone_px:
            self.state.cy += dy * self.pan_speed

    def _smooth_zoom(self, target_zoom: float):
        diff = target_zoom - self.state.zoom

        if abs(diff) < self.zoom_deadzone:
            return

        step = max(-self.zoom_speed, min(self.zoom_speed, diff))
        self.state.zoom += step
        self.state.zoom = max(self.min_zoom, min(self.max_zoom, self.state.zoom))

    def _crop_from_state(self) -> Tuple[int, int, int, int]:
        crop_w = self.frame_w / self.state.zoom
        crop_h = self.frame_h / self.state.zoom

        x1 = self.state.cx - crop_w / 2
        y1 = self.state.cy - crop_h / 2
        x2 = self.state.cx + crop_w / 2
        y2 = self.state.cy + crop_h / 2

        if x1 < 0:
            x2 -= x1
            x1 = 0

        if y1 < 0:
            y2 -= y1
            y1 = 0

        if x2 > self.frame_w:
            shift = x2 - self.frame_w
            x1 -= shift
            x2 = self.frame_w

        if y2 > self.frame_h:
            shift = y2 - self.frame_h
            y1 -= shift
            y2 = self.frame_h

        return (
            max(0, int(x1)),
            max(0, int(y1)),
            min(self.frame_w, int(x2)),
            min(self.frame_h, int(y2)),
        )
