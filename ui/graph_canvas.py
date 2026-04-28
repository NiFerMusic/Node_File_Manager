from __future__ import annotations

from PyQt6.QtCore import QPointF, Qt, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QMouseEvent,
    QPainter,
    QPen,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsScene,
    QGraphicsView,
    QMenu,
)

from core.graph_layout import compute_layout
from ui.edge_item import EdgeItem
from ui.node_item import NodeItem


class GraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self._grid_pen = QPen(QColor("#2a2a2a"), 0.5)
        self._draw_grid()

    def _draw_grid(self):
        size = 6000
        spacing = 50
        for i in range(-size, size + 1, spacing):
            self.addLine(i, -size, i, size, self._grid_pen)
            self.addLine(-size, i, size, i, self._grid_pen)


class GraphCanvas(QGraphicsView):
    node_clicked = pyqtSignal(str)
    node_double_clicked = pyqtSignal(str)
    node_dropped = pyqtSignal(str, str)
    file_dropped_on_canvas = pyqtSignal(str)
    merge_requested = pyqtSignal(list)
    delete_node_requested = pyqtSignal(str)
    edit_description_requested = pyqtSignal(str)

    MIN_ZOOM = 0.1
    MAX_ZOOM = 3.0
    ZOOM_FACTOR = 1.15

    def __init__(self, parent=None):
        self._scene = GraphScene()
        super().__init__(self._scene, parent)

        self._panning = False
        self._last_pan_pos = QPoint()
        self._zoom_level = 1.0
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: list[EdgeItem] = []
        self._selected_ids: set[str] = set()

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setAcceptDrops(True)

    def rebuild(self, nodes: list, edges: list):
        self._scene.clearSelection()
        self._selected_ids.clear()
        for ei in self._edge_items:
            self._scene.removeItem(ei)
        self._edge_items.clear()
        for ni in self._node_items.values():
            self._scene.removeItem(ni)
        self._node_items.clear()

        self._scene._draw_grid()

        positions = compute_layout(nodes, edges)

        for n in nodes:
            item = NodeItem(n)
            pos = positions.get(n.id, (0, 0))
            item.setPos(QPointF(pos[0], pos[1]))
            item.node_clicked.connect(self._on_node_clicked)
            item.node_double_clicked.connect(self.node_double_clicked.emit)
            item.node_context_menu.connect(self._on_node_context_menu)
            self._scene.addItem(item)
            self._node_items[n.id] = item

        for e in edges:
            src_item = self._node_items.get(e.source_id)
            tgt_item = self._node_items.get(e.target_id)
            if src_item and tgt_item:
                sp = src_item.connection_point_right()
                tp = tgt_item.connection_point_left()
                ei = EdgeItem(sp, tp)
                self._scene.addItem(ei)
                self._edge_items.append(ei)

    # ---- drag & drop ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            scene_pos = self.mapToScene(event.position().toPoint())
            item = self._scene.itemAt(scene_pos, self.transform())
            if isinstance(item, NodeItem):
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    if file_path:
                        self.node_dropped.emit(item.node_id, file_path)
            else:
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    if file_path:
                        self.file_dropped_on_canvas.emit(file_path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ---- selection ----
    def _on_node_clicked(self, node_id: str):
        if node_id in self._selected_ids:
            self._selected_ids.discard(node_id)
        else:
            self._selected_ids.add(node_id)
        self._sync_item_visuals()
        self.node_clicked.emit(node_id)

    def _sync_item_visuals(self):
        for nid, item in self._node_items.items():
            item.setHighlighted(nid in self._selected_ids)

    def selected_node_ids(self) -> list[str]:
        return list(self._selected_ids)

    def clear_node_selection(self):
        self._selected_ids.clear()
        self._sync_item_visuals()

    def select_node(self, node_id: str):
        self._selected_ids.add(node_id)
        self._sync_item_visuals()

    # ---- interactions ----
    def _on_node_context_menu(self, node_id: str, scene_pos: QPointF):
        selected_ids = self.selected_node_ids()

        menu = QMenu(self)

        if len(selected_ids) >= 2:
            merge_action = menu.addAction(f"合并选中节点 ({len(selected_ids)})")
            merge_action.triggered.connect(lambda: self.merge_requested.emit(list(selected_ids)))

        edit_action = menu.addAction("编辑描述")
        edit_action.triggered.connect(lambda: self.edit_description_requested.emit(node_id))

        menu.addSeparator()

        delete_action = menu.addAction("删除节点")
        delete_action.triggered.connect(lambda: self.delete_node_requested.emit(node_id))

        menu.exec(self.mapToGlobal(self.mapFromScene(scene_pos)))

    def get_node_item(self, node_id: str) -> NodeItem | None:
        return self._node_items.get(node_id)

    # ---- view-level mouse for click-on-empty ----
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._last_pan_pos = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            item = self._scene.itemAt(scene_pos, self.transform())
            if not isinstance(item, NodeItem):
                self.clear_node_selection()
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning:
            delta = event.position().toPoint() - self._last_pan_pos
            self._last_pan_pos = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton and self._panning:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # ---- zoom ----
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            factor = self.ZOOM_FACTOR if delta > 0 else 1 / self.ZOOM_FACTOR
            new_zoom = self._zoom_level * factor
            if self.MIN_ZOOM <= new_zoom <= self.MAX_ZOOM:
                self._zoom_level = new_zoom
                self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        if self._zoom_level < self.MAX_ZOOM:
            self._zoom_level *= self.ZOOM_FACTOR
            self.scale(self.ZOOM_FACTOR, self.ZOOM_FACTOR)

    def zoom_out(self):
        if self._zoom_level > self.MIN_ZOOM:
            self._zoom_level /= self.ZOOM_FACTOR
            self.scale(1 / self.ZOOM_FACTOR, 1 / self.ZOOM_FACTOR)

    def fit_all(self):
        self.fitInView(
            self._scene.itemsBoundingRect().adjusted(-100, -100, 100, 100),
            Qt.AspectRatioMode.KeepAspectRatio,
        )
        self._zoom_level = self.transform().m11()
