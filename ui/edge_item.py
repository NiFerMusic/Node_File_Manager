from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from PyQt6.QtWidgets import QGraphicsPathItem, QStyleOptionGraphicsItem


class EdgeItem(QGraphicsPathItem):
    def __init__(self, source_point: QPointF, target_point: QPointF, parent=None):
        super().__init__(parent)
        self._source = source_point
        self._target = target_point
        self._highlighted = False
        self._build_path()
        self.setAcceptHoverEvents(True)
        self.setZValue(1)

    def _build_path(self):
        path = QPainterPath()
        path.moveTo(self._source)

        dx = abs(self._target.x() - self._source.x())
        ctrl_dist = max(dx * 0.5, 50)

        c1 = QPointF(self._source.x() + ctrl_dist, self._source.y())
        c2 = QPointF(self._target.x() - ctrl_dist, self._target.y())
        path.cubicTo(c1, c2, self._target)
        self.setPath(path)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._highlighted:
            color = QColor("#93f4ff")
            width = 1.8
        else:
            color = QColor("#afc7c7")
            width = 1.2
        pen = QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

        self._draw_arrow(painter, color)

    def _draw_arrow(self, painter: QPainter, color: QColor):
        path = self.path()
        if path.isEmpty():
            return
        percent = 0.98
        p1 = path.pointAtPercent(percent)
        p2 = self._target
        if p2 == p1:
            return
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        arrow_len = 8
        arrow_angle = math.radians(22)

        tip = p2
        left = QPointF(
            tip.x() - arrow_len * math.cos(angle - arrow_angle),
            tip.y() - arrow_len * math.sin(angle - arrow_angle),
        )
        right = QPointF(
            tip.x() - arrow_len * math.cos(angle + arrow_angle),
            tip.y() - arrow_len * math.sin(angle + arrow_angle),
        )

        arrow = QPolygonF([tip, left, right])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(arrow)

    def update_endpoints(self, source_point: QPointF, target_point: QPointF):
        self._source = source_point
        self._target = target_point
        self._build_path()
        self.update()

    def set_highlighted(self, on: bool):
        self._highlighted = on
        self.update()

    def hoverEnterEvent(self, event):
        self._highlighted = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._highlighted = False
        self.update()
