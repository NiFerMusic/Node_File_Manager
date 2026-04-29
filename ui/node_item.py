from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import (
    QPointF, QRectF, Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty,
)
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
CORNER_RADIUS = 14
MISSING_FILE_COLOR = QColor("#f44747")


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
        if not node_data.file_exists:
            self._accent = MISSING_FILE_COLOR

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
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
        cr = CORNER_RADIUS

        # --- multi-layer shadow ---
        # Far shadow
        far_path = QPainterPath()
        far_rect = r.translated(4, 7)
        far_path.addRoundedRect(far_rect, cr, cr)
        painter.fillPath(far_path, QColor(0, 0, 0, 45))
        # Near shadow
        near_path = QPainterPath()
        near_rect = r.translated(1, 3)
        near_path.addRoundedRect(near_rect, cr, cr)
        painter.fillPath(near_path, QColor(0, 0, 0, 70))

        # --- glass background ---
        body_path = QPainterPath()
        body_path.addRoundedRect(r, cr, cr)
        bg_grad = QLinearGradient(r.topLeft(), r.bottomLeft())
        if self._hovered:
            bg_grad.setColorAt(0, QColor(255, 255, 255, 22))
            bg_grad.setColorAt(0.35, QColor(52, 52, 58, 225))
            bg_grad.setColorAt(1, QColor(38, 38, 44, 238))
        else:
            bg_grad.setColorAt(0, QColor(255, 255, 255, 10))
            bg_grad.setColorAt(0.35, QColor(42, 42, 48, 215))
            bg_grad.setColorAt(1, QColor(28, 28, 34, 232))
        painter.fillPath(body_path, QBrush(bg_grad))

        # --- glass border ---
        border_pen = QPen()
        border_pen.setWidthF(1.0)
        if self._drop_mode == "append":
            border_pen.setColor(QColor("#4ec9b0"))
            border_pen.setWidthF(2.5)
        elif self._drop_mode == "branch":
            border_pen.setColor(QColor("#dcdcaa"))
            border_pen.setWidthF(2.5)
        elif self._highlighted:
            border_pen.setColor(QColor("#007acc"))
            border_pen.setWidthF(2.0)
        elif self._hovered:
            border_pen.setColor(QColor(255, 255, 255, 35))
        else:
            border_pen.setColor(QColor(255, 255, 255, 12))
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(r, cr, cr)

        # --- accent bar with gradient glow ---
        bar_path = QPainterPath()
        bar_rect = QRectF(r.left() + 1.5, r.top() + 6, 4, r.height() - 12)
        bar_path.addRoundedRect(bar_rect, 3, 3)
        bar_grad = QLinearGradient(bar_rect.topLeft(), bar_rect.bottomLeft())
        lighter = QColor(self._accent).lighter(150)
        bar_grad.setColorAt(0, lighter)
        bar_grad.setColorAt(0.6, self._accent)
        bar_grad.setColorAt(1, QColor(self._accent).darker(120))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.fillPath(bar_path, QBrush(bar_grad))

        # --- drop mode label ---
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
            label_rect = QRectF(r.left() + 16, r.bottom() - 24, r.width() - 32, 18)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label)

        # --- main text: description or filename ---
        name_font = QFont("Segoe UI", 11)
        name_font.setBold(True)
        painter.setFont(name_font)
        painter.setPen(QColor("#e8e8e8"))
        name_rect = QRectF(r.left() + 16, r.top() + 10, r.width() - 32, 22)
        main_text = self._data.description if self._data.description else self._data.filename
        elided = QFontMetrics(name_font).elidedText(
            main_text, Qt.TextElideMode.ElideRight, int(name_rect.width())
        )
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided)

        # --- secondary: filename ---
        file_font = QFont("Segoe UI", 9)
        painter.setFont(file_font)
        painter.setPen(QColor("#999"))
        file_rect = QRectF(r.left() + 16, r.top() + 32, r.width() - 32, 18)
        elided_fn = QFontMetrics(file_font).elidedText(
            self._data.filename, Qt.TextElideMode.ElideMiddle, int(file_rect.width())
        )
        painter.drawText(file_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, elided_fn)

        # --- date ---
        date_font = QFont("Segoe UI", 9)
        painter.setFont(date_font)
        painter.setPen(QColor("#707070"))
        date_rect = QRectF(r.left() + 16, r.top() + 48, r.width() - 32, 18)
        dt = datetime.fromtimestamp(self._data.last_modified)
        painter.drawText(date_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         dt.strftime("%Y-%m-%d %H:%M"))

        # --- merge badge ---
        if self._data.node_type == "merge":
            badge_size = 18
            badge_rect = QRectF(r.right() - badge_size - 4, r.top() + 4, badge_size, badge_size)
            badge_grad = QLinearGradient(badge_rect.topLeft(), badge_rect.bottomRight())
            badge_grad.setColorAt(0, QColor("#c586c0"))
            badge_grad.setColorAt(1, QColor("#a05da0"))
            painter.setBrush(QBrush(badge_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(badge_rect)
            painter.setPen(QColor("#fff"))
            badge_font = QFont("Segoe UI", 9)
            badge_font.setBold(True)
            painter.setFont(badge_font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "M")

        # --- connection dots with glow ---
        for cx in (r.left(), r.right()):
            center = QPointF(cx, r.center().y())
            # Outer glow
            glow_r = 5.5
            glow_color = QColor(self._accent)
            glow_color.setAlpha(45)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(glow_color, 2.5))
            painter.drawEllipse(center, glow_r, glow_r)
            # Inner dot
            dot_r = 3.5
            painter.setBrush(self._accent)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, dot_r, dot_r)

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
        if not data.file_exists:
            self._accent = MISSING_FILE_COLOR
        self._compute_height()
        self.prepareGeometryChange()
        self.update()

    def connection_point_right(self) -> QPointF:
        return self.mapToScene(self.boundingRect().right(), 0)

    def connection_point_left(self) -> QPointF:
        return self.mapToScene(self.boundingRect().left(), 0)

    def scene_center(self) -> QPointF:
        return self.mapToScene(0, 0)

    # ---- scale property for animation ----
    def _get_item_scale(self) -> float:
        return self.scale()

    def _set_item_scale(self, s: float):
        self.setScale(s)

    itemScale = pyqtProperty(float, _get_item_scale, _set_item_scale)

    def animate_appear(self):
        self.setScale(0.3)
        anim = QPropertyAnimation(self, b"itemScale")
        anim.setDuration(350)
        anim.setStartValue(0.3)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        return anim

    def animate_disappear(self):
        anim = QPropertyAnimation(self, b"itemScale")
        anim.setDuration(220)
        anim.setStartValue(self.scale())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InBack)
        return anim

    # ---- position property for movement animation ----
    def _get_node_pos(self) -> QPointF:
        return self.pos()

    def _set_node_pos(self, p: QPointF):
        self.setPos(p)

    nodePos = pyqtProperty(QPointF, _get_node_pos, _set_node_pos)
