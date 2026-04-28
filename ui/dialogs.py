from __future__ import annotations

import os
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

EXTENSION_OPTIONS = [
    (".blend", "Blender"),
    (".psd", "Photoshop"),
    (".ai", "Illustrator"),
    (".prproj", "Premiere Pro"),
    (".aep", "After Effects"),
    (".flp", "FL Studio"),
    (".als", "Ableton Live"),
    (".ptx", "Pro Tools"),
    (".c4d", "Cinema 4D"),
    (".ma", "Maya ASCII"),
    (".mb", "Maya Binary"),
    (".max", "3ds Max"),
    (".fbx", "FBX"),
    (".obj", "OBJ"),
    (".spp", "Substance Painter"),
    (".clip", "Clip Studio"),
    (".kra", "Krita"),
    (".xcf", "GIMP"),
    (".fcpxml", "Final Cut Pro"),
    (".hip", "Houdini"),
    (".sbs", "Substance Designer"),
    (".nk", "Nuke"),
    (".hipnc", "Houdini NC"),
]


class NewProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建项目")
        self.setMinimumSize(550, 500)
        self.setModal(True)
        self._ext_checks: dict[str, QCheckBox] = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("创建新版本管理项目")
        title_font = QFont("Segoe UI", 16)
        title_font.setBold(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("输入项目名称...")
        form.addRow("项目名称:", self._name_edit)

        path_layout = QHBoxLayout()
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText("选择项目根目录...")
        self._path_edit.setReadOnly(True)
        path_layout.addWidget(self._path_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(browse_btn)
        form.addRow("项目目录:", path_layout)

        layout.addLayout(form)

        ext_group = QGroupBox("支持的工程文件格式")
        ext_layout = QVBoxLayout(ext_group)
        ext_layout.setSpacing(4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(2)

        for ext, name in EXTENSION_OPTIONS:
            cb = QCheckBox(f"{name}  ({ext})")
            cb.setChecked(True)
            scroll_layout.addWidget(cb)
            self._ext_checks[ext] = cb

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        ext_layout.addWidget(scroll)
        layout.addWidget(ext_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择项目根目录")
        if path:
            self._path_edit.setText(path)

    def _validate_and_accept(self):
        if not self._name_edit.text().strip():
            QMessageBox.warning(self, "警告", "请输入项目名称。")
            return
        if not self._path_edit.text().strip():
            QMessageBox.warning(self, "警告", "请选择项目目录。")
            return
        selected = [ext for ext, cb in self._ext_checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "警告", "请至少选择一种文件格式。")
            return
        self.accept()

    def get_project_info(self) -> tuple[str, str, list[str]]:
        name = self._name_edit.text().strip()
        path = self._path_edit.text().strip()
        exts = [ext for ext, cb in self._ext_checks.items() if cb.isChecked()]
        return name, path, exts


class NodeDetailDialog(QDialog):
    preview_changed = pyqtSignal(str)

    def __init__(self, node, storage, parent=None):
        super().__init__(parent)
        self._node = node
        self._storage = storage
        self.setWindowTitle(f"节点详情 - {node.filename}")
        self.setMinimumSize(500, 460)
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        info_group = QGroupBox("文件信息")
        info_form = QFormLayout(info_group)
        info_form.setSpacing(8)

        self._filename_label = QLabel()
        self._filename_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        info_form.addRow("文件名:", self._filename_label)

        self._path_label = QLabel()
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_form.addRow("路径:", self._path_label)

        self._date_label = QLabel()
        info_form.addRow("修改时间:", self._date_label)

        self._type_label = QLabel()
        info_form.addRow("节点类型:", self._type_label)

        layout.addWidget(info_group)

        desc_group = QGroupBox("修改描述")
        desc_layout = QVBoxLayout(desc_group)
        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("描述此次修改...")
        self._desc_edit.setMaximumHeight(80)
        desc_layout.addWidget(self._desc_edit)

        save_desc_btn = QPushButton("保存描述")
        save_desc_btn.clicked.connect(self._save_description)
        desc_layout.addWidget(save_desc_btn)
        layout.addWidget(desc_group)

        preview_group = QGroupBox("预览")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_label = QLabel()
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumHeight(120)
        self._preview_label.setStyleSheet("background-color: #1e1e1e; border-radius: 6px;")
        preview_layout.addWidget(self._preview_label)

        preview_btns = QHBoxLayout()
        upload_btn = QPushButton("上传预览")
        upload_btn.clicked.connect(self._upload_preview)
        preview_btns.addWidget(upload_btn)
        replace_btn = QPushButton("替换预览")
        replace_btn.clicked.connect(self._upload_preview)
        preview_btns.addWidget(replace_btn)
        delete_btn = QPushButton("删除预览")
        delete_btn.clicked.connect(self._delete_preview)
        preview_btns.addWidget(delete_btn)
        preview_layout.addLayout(preview_btns)

        layout.addWidget(preview_group)

        btn_row = QHBoxLayout()

        open_btn = QPushButton("打开文件所在位置")
        open_btn.clicked.connect(self._open_file_location)
        btn_row.addWidget(open_btn)

        btn_row.addStretch()

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _load_data(self):
        self._filename_label.setText(self._node.filename)
        self._path_label.setText(self._node.file_path)
        dt = datetime.fromtimestamp(self._node.last_modified)
        self._date_label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
        self._type_label.setText("合并节点" if self._node.node_type == "merge" else "文件节点")
        self._desc_edit.setPlainText(self._node.description)

        preview_path = self._storage.get_preview_path(self._node.id)
        if preview_path:
            self._show_preview(preview_path)

    def _show_preview(self, path: str):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                QSize(320, 200),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._preview_label.setPixmap(scaled)

    def _save_description(self):
        self._node.description = self._desc_edit.toPlainText().strip()
        self._storage.update_node(self._node)

    def _upload_preview(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择预览文件", "",
            "图片/视频 (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.mp4 *.mov *.avi)"
        )
        if file_path:
            preview_path = self._storage.import_preview(self._node.id, file_path)
            self._node.preview_path = preview_path
            self._storage.update_node(self._node)
            self._show_preview(preview_path)

    def _open_file_location(self):
        if self._node.file_path and os.path.isfile(self._node.file_path):
            folder = os.path.dirname(self._node.file_path)
            if os.path.isdir(folder):
                subprocess.Popen(["explorer", "/select,", self._node.file_path])

    def _delete_preview(self):
        self._storage.remove_preview(self._node.id)
        self._node.preview_path = ""
        self._storage.update_node(self._node)
        self._preview_label.clear()
        self._preview_label.setText("无预览")


class DescriptionDialog(QDialog):
    def __init__(self, filename: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加修改描述")
        self.setMinimumSize(400, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel(f"为 <b>{filename}</b> 添加描述:")
        label.setWordWrap(True)
        layout.addWidget(label)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("例如：添加角色模型、调整色调、修复UV...")
        layout.addWidget(self._desc_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def description(self) -> str:
        return self._desc_edit.toPlainText().strip()


class MergeFileDialog(QDialog):
    def __init__(self, untracked_files: list[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择合并结果文件")
        self.setMinimumSize(500, 350)
        self.setModal(True)
        self._files = untracked_files
        self._selected_file = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("选择未追踪的文件作为合并结果:")
        label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(label)

        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        self._list = QListWidget()
        self._list.setStyleSheet("QListWidget { font-size: 13px; }")
        for fp in self._files:
            item = QListWidgetItem(os.path.basename(fp))
            item.setData(Qt.ItemDataRole.UserRole, fp)
            item.setToolTip(fp)
            self._list.addItem(item)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self):
        item = self._list.currentItem()
        if item:
            self._selected_file = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def selected_file(self) -> str:
        return self._selected_file
