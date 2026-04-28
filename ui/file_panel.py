from __future__ import annotations

import os
from datetime import datetime

from PyQt6.QtCore import QMimeData, QPoint, QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QDrag,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

EXTENSION_DISPLAY = {
    ".blend": "Blender",
    ".psd": "Photoshop",
    ".ai": "Illustrator",
    ".prproj": "Premiere Pro",
    ".aep": "After Effects",
    ".flp": "FL Studio",
    ".als": "Ableton Live",
    ".ptx": "Pro Tools",
    ".c4d": "Cinema 4D",
    ".ma": "Maya ASCII",
    ".mb": "Maya Binary",
    ".max": "3ds Max",
    ".fbx": "FBX",
    ".obj": "OBJ",
    ".spp": "Substance Painter",
    ".clip": "Clip Studio",
    ".kra": "Krita",
    ".xcf": "GIMP",
    ".fcpxml": "Final Cut Pro",
    ".hip": "Houdini",
}

_DOT_ICON_CACHE: dict[str, QIcon] = {}


def _get_dot_icon(color_hex: str) -> QIcon:
    if color_hex in _DOT_ICON_CACHE:
        return _DOT_ICON_CACHE[color_hex]
    pix = QPixmap(12, 12)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QBrush(QColor(color_hex)))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, 8, 8)
    p.end()
    icon = QIcon(pix)
    _DOT_ICON_CACHE[color_hex] = icon
    return icon


class DragTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setRootIsDecorated(False)
        self.setItemsExpandable(False)
        self.setIndentation(0)
        self.setSortingEnabled(False)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(
            "QTreeView { alternate-background-color: #222222; }"
        )

    def startDrag(self, supportedActions):
        indexes = self.selectedIndexes()
        if not indexes:
            return
        mime_data = QMimeData()
        urls = []
        for idx in indexes:
            file_path = idx.data(Qt.ItemDataRole.UserRole)
            if file_path and os.path.isfile(file_path):
                urls.append(QUrl.fromLocalFile(file_path))
        if not urls:
            return
        mime_data.setUrls(urls)
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction)


class FilePanel(QWidget):
    file_double_clicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project_root = ""
        self._allowed_extensions: set[str] = set()
        self._tracked_paths: set[str] = set()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()

        title = QLabel("文件管理")
        title_font = QFont("Segoe UI", 13)
        title_font.setBold(True)
        title.setFont(title_font)
        header.addWidget(title)

        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #888; font-size: 12px;")
        header.addWidget(self._summary_label)

        header.addStretch()

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.setFlat(True)
        self._refresh_btn.setFixedHeight(30)
        self._refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)

        # Unified file list
        self._file_view = DragTreeView()
        self._file_model = QStandardItemModel()
        self._file_model.setHorizontalHeaderLabels(["", "文件名", "修改时间", "类型", "状态"])
        self._file_view.setModel(self._file_model)
        self._file_view.doubleClicked.connect(
            lambda idx: self._emit_file(idx)
        )
        self._file_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._file_view.customContextMenuRequested.connect(self._on_context_menu)

        hdr = self._file_view.header()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)    # dot
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # filename
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # date
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # type
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # status
        hdr.resizeSection(0, 24)

        layout.addWidget(self._file_view)

    def _emit_file(self, idx):
        item = self._file_model.itemFromIndex(idx)
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path:
                self.file_double_clicked.emit(file_path)

    def _on_context_menu(self, pos: QPoint):
        idx = self._file_view.indexAt(pos)
        if not idx.isValid():
            return
        # Map to column 0 to get the file path
        item = self._file_model.itemFromIndex(
            self._file_model.index(idx.row(), 0)
        )
        if not item:
            return
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path:
            return
        menu = QMenu(self)
        if file_path in self._tracked_paths:
            action = menu.addAction("在图中定位此节点")
            action.triggered.connect(lambda: self._locate_in_graph(file_path))
        else:
            action = menu.addAction("添加到图中（需拖拽到节点）")
            action.setEnabled(False)
        menu.exec(self._file_view.mapToGlobal(pos))

    def _locate_in_graph(self, file_path: str):
        # Signal to main window to highlight the node
        pass

    def set_project(self, root_path: str, extensions: list[str]):
        self._project_root = root_path
        self._allowed_extensions = set(extensions)
        self.refresh()

    def set_tracked_paths(self, paths: set[str]):
        self._tracked_paths = {os.path.normpath(p) for p in paths}

    def untracked_files(self) -> list[str]:
        if not self._project_root or not os.path.isdir(self._project_root):
            return []
        result = []
        for dirpath, dirnames, filenames in os.walk(self._project_root):
            if ".vmtree" in dirpath:
                continue
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in self._allowed_extensions:
                    fp = os.path.normpath(os.path.join(dirpath, fn))
                    if fp not in self._tracked_paths:
                        result.append(fp)
        result.sort(key=lambda x: os.path.basename(x).lower())
        return result

    def refresh(self):
        if not self._project_root or not os.path.isdir(self._project_root):
            return
        self._file_model.removeRows(0, self._file_model.rowCount())

        all_files = []
        for dirpath, dirnames, filenames in os.walk(self._project_root):
            if ".vmtree" in dirpath:
                continue
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext in self._allowed_extensions:
                    full_path = os.path.normpath(os.path.join(dirpath, fn))
                    all_files.append(full_path)

        # Sort: untracked first, then tracked; within each group by filename
        untracked = []
        tracked = []
        for fp in all_files:
            if fp in self._tracked_paths:
                tracked.append(fp)
            else:
                untracked.append(fp)

        untracked.sort(key=lambda x: os.path.basename(x).lower())
        tracked.sort(key=lambda x: os.path.basename(x).lower())

        for fp in untracked:
            self._add_file_row(fp, tracked=False)
        for fp in tracked:
            self._add_file_row(fp, tracked=True)

        untracked_count = len(untracked)
        tracked_count = len(tracked)
        self._summary_label.setText(
            f"共 {len(all_files)} 个文件  |  "
            f"未追踪: {untracked_count}  |  "
            f"已追踪: {tracked_count}"
        )

    def _add_file_row(self, file_path: str, tracked: bool):
        try:
            stat = os.stat(file_path)
            filename = os.path.basename(file_path)
            ext = os.path.splitext(filename)[1].lower()

            # Dot icon column
            dot_item = QStandardItem()
            dot_item.setIcon(_get_dot_icon("#4ec9b0") if tracked else _get_dot_icon("#6e6e6e"))
            dot_item.setData(file_path, Qt.ItemDataRole.UserRole)
            dot_item.setEditable(False)
            dot_item.setSelectable(False)

            # Filename
            name_item = QStandardItem(filename)
            name_item.setData(file_path, Qt.ItemDataRole.UserRole)
            name_item.setEditable(False)
            if tracked:
                name_item.setForeground(QBrush(QColor("#4ec9b0")))

            # Date
            dt = datetime.fromtimestamp(stat.st_mtime)
            date_item = QStandardItem(dt.strftime("%m-%d %H:%M"))
            date_item.setEditable(False)

            # Type
            type_name = EXTENSION_DISPLAY.get(ext, ext.upper().lstrip("."))
            type_item = QStandardItem(type_name)
            type_item.setEditable(False)

            # Status text
            status_item = QStandardItem("已追踪" if tracked else "未追踪")
            status_item.setEditable(False)
            if tracked:
                status_item.setForeground(QBrush(QColor("#4ec9b0")))
            else:
                status_item.setForeground(QBrush(QColor("#6e6e6e")))

            self._file_model.appendRow([dot_item, name_item, date_item, type_item, status_item])
        except OSError:
            pass
