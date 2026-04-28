from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt6.QtWidgets import (
    QGraphicsItem,
    QGraphicsObject,
    QStyleOptionGraphicsItem,
)

EXTENSION_COLORS = {
    ".blend": QColor("#f5793a"),
    ".psd": QColor("#31a8ff"),
    ".ai": QColor("#ff9a00"),
    ".prproj": QColor("#9b59b6"),
    ".aep": QColor("#c586c0"),
    ".flp": QColor("#4ec9b0"),
    ".als": QColor("#4ec9b0"),
    ".logic": QColor("#4ec9b0"),
    ".ptx": QColor("#dcdcaa"),
    ".c4d": QColor("#ce9178"),
    ".ma": QColor("#569cd6"),
    ".mb": QColor("#569cd6"),
    ".max": QColor("#d16969"),
    ".fbx": QColor("#608b4e"),
    ".obj": QColor("#608b4e"),
    ".spp": QColor("#c586c0"),
    ".clip": QColor("#dcdcaa"),
    ".kra": QColor("#f5793a"),
    ".xcf": QColor("#f5793a"),
    ".fcpxml": QColor("#9b59b6"),
    ".davinci": QColor("#9b59b6"),
}

NODE_WIDTH = 200
NODE_MIN_HEIGHT = 80
DESC_MAX_WIDTH = 190


class NodeItem(QGraphicsObject):
    node_clicked = pyqtSignal(str)
    node_double_clicked = pyqtSignal(str)
    node_context_menu = pyqtSignal(str, QPointF)

    def __init__(self, node_data, parent=None):
        super().__init__(parent)
        self._data = node_data
        self._width = NODE_WIDTH
        self._height = NODE_MIN_HEIGHT
        self._highlighted = False
        self._drop_mode = None
        self._hovered = False
        self._accent = self._color_for_ext(node_data.ext)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton)

        self._compute_height()

    def _compute_height(self):
        self._height = NODE_MIN_HEIGHT

    def _wrap_text(self, text: str, max_w: int, font: QFont) -> list[str]:
        fm = QFontMetrics(font)
        lines = []
        current = ""
        for ch in text:
            if fm.horizontalAdvance(current + ch) > max_w:
                lines.append(current)
                current = ch
            else:
                current += ch
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _color_for_ext(ext: str) -> QColor:
        return EXTENSION_COLORS.get(ext.lower(), QColor("#6a9955"))

    def boundingRect(self) -> QRectF:
        return QRectF(-self._width / 2, -self._height / 2, self._width, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.boundingRect()
        r = rect.adjusted(2, 2, -2, -2)
        corner = 10

        # Shadow
        shadow_path = QPainterPath()
        shadow_rect = r.translated(3, 3)
        shadow_path.addRoundedRect(shadow_rect, corner, corner)
        painter.fillPath(shadow_path, QColor(0, 0, 0, 60))

        # Background
        grad = QLinearGradient(r.topLeft(), r.bottomRight())
        if self._hovered:
            grad.setColorAt(0, QColor("#3c3c3c"))
            grad.setColorAt(1, QColor("#333333"))
        else:
            grad.setColorAt(0, QColor("#2d2d2d"))
            grad.setColorAt(1, QColor("#252526"))
        body_path = QPainterPath()
        body_path.addRoundedRect(r, corner, corner)
        painter.fillPath(body_path, QBrush(grad))

        # Accent bar
        bar_path = QPainterPath()
        bar_rect = QRectF(r.left(), r.top(), 5, r.height())
        bar_path.addRoundedRect(bar_rect, 2, 2)
        painter.fillPath(bar_path, self._accent)

        # Border
        if self._drop_mode == "append":
            pen = QPen(QColor("#4ec9b0"), 3)
        elif self._drop_mode == "branch":
            pen = QPen(QColor("#dcdcaa"), 3)
        elif self._highlighted:
            pen = QPen(QColor("#007acc"), 2)
        elif self._hovered:
            pen = QPen(QColor("#555"), 1.5)
        else:
            pen = QPen(QColor("#3c3c3c"), 1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(r, corner, corner)

        # Drop mode label
        if self._drop_mode:
            label_font = QFont("Segoe UI", 8)
            label_font.setBold(True)
            painter.setFont(label_font)
            if self._drop_mode == "append":
                painter.setPen(QColor("#4ec9b0"))
                label = "+ 追加到末尾"
            else:
                painter.setPen(QColor("#dcdcaa"))
                label = "↳ 从此分支"
            label_rect = QRectF(r.left() + 14, r.bottom() - 24, r.width() - 28, 18)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # Main: description (or filename if no description)
        name_font = QFont("Segoe UI", 11)
        name_font.setBold(True)
        painter.setFont(name_font)
        painter.setPen(QColor("#e0e0e0"))
        name_rect = QRectF(r.left() + 14, r.top() + 10, r.width() - 28, 22)
        main_text = self._data.description if self._data.description else self._data.filename
        elided = QFontMetrics(name_font).elidedText(
            main_text, Qt.TextElideMode.ElideRight, int(name_rect.width())
        )
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

        # Secondary: filename
        file_font = QFont("Segoe UI", 9)
        painter.setFont(file_font)
        painter.setPen(QColor("#888"))
        file_rect = QRectF(r.left() + 14, r.top() + 32, r.width() - 28, 18)
        elided_fn = QFontMetrics(file_font).elidedText(
            self._data.filename, Qt.TextElideMode.ElideMiddle, int(file_rect.width())
        )
        painter.drawText(file_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_fn)

        # Date
        date_font = QFont("Segoe UI", 9)
        painter.setFont(date_font)
        painter.setPen(QColor("#666"))
        date_rect = QRectF(r.left() + 14, r.top() + 48, r.width() - 28, 18)
        dt = datetime.fromtimestamp(self._data.last_modified)
        painter.drawText(date_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         dt.strftime("%Y-%m-%d %H:%M"))

        # Merge badge
        if self._data.node_type == "merge":
            badge_size = 18
            badge_rect = QRectF(r.right() - badge_size - 4, r.top() + 4, badge_size, badge_size)
            painter.setBrush(QColor("#c586c0"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(badge_rect)
            painter.setPen(QColor("#fff"))
            badge_font = QFont("Segoe UI", 9)
            badge_font.setBold(True)
            painter.setFont(badge_font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "M")

        # Connection dots
        dot_r = 3
        painter.setBrush(self._accent)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(r.right(), r.center().y()), dot_r, dot_r)
        painter.drawEllipse(QPointF(r.left(), r.center().y()), dot_r, dot_r)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.node_clicked.emit(self._data.id)
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.node_context_menu.emit(self._data.id, event.scenePos())
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.node_double_clicked.emit(self._data.id)
            event.accept()

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update()

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    def setHighlighted(self, on: bool):
        self._highlighted = on
        self.update()

    def setDropHighlight(self, mode: str | None):
        self._drop_mode = mode
        self.update()

    @property
    def node_id(self) -> str:
        return self._data.id

    @property
    def node_data(self):
        return self._data

    def set_node_data(self, data):
        self._data = data
        self._accent = self._color_for_ext(data.ext)
        self._compute_height()
        self.prepareGeometryChange()
        self.update()

    def connection_point_right(self) -> QPointF:
        return self.mapToScene(self.boundingRect().right(), 0)

    def connection_point_left(self) -> QPointF:
        return self.mapToScene(self.boundingRect().left(), 0)

    def scene_center(self) -> QPointF:
        return self.mapToScene(0, 0)
