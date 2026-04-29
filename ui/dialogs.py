from __future__ import annotations

import os
import subprocess
from datetime import datetime

from PyQt6.QtCore import Qt, QSize, QUrl, pyqtSignal

from core.models import Node
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
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
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

PREVIEW_TYPE = {
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".gif": "image",
    ".bmp": "image", ".webp": "image",
    ".mp4": "video", ".mov": "video", ".avi": "video", ".webm": "video",
    ".mkv": "video", ".wmv": "video", ".flv": "video",
    ".mp3": "audio", ".wav": "audio", ".flac": "audio", ".ogg": "audio",
    ".aac": "audio", ".wma": "audio", ".m4a": "audio",
    ".txt": "text", ".md": "text", ".py": "text", ".json": "text",
    ".xml": "text", ".html": "text", ".css": "text", ".js": "text",
    ".yaml": "text", ".yml": "text", ".cfg": "text", ".ini": "text",
    ".log": "text", ".csv": "text", ".toml": "text", ".rst": "text",
    ".bat": "text", ".sh": "text", ".ps1": "text",
}

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
    node_relocated = pyqtSignal(str)

    PG_EMPTY, PG_IMAGE, PG_VIDEO, PG_AUDIO, PG_TEXT = range(5)

    def __init__(self, node, storage, parent=None, untracked_files: list[str] | None = None):
        super().__init__(parent)
        self._node = node
        self._storage = storage
        self._untracked_files = untracked_files or []
        self._current_preview_type = None
        self._video_player: QMediaPlayer | None = None
        self._audio_player: QMediaPlayer | None = None

        self.setWindowTitle(f"节点详情 - {node.filename}")
        self.setMinimumSize(550, 520)
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
        preview_layout.setSpacing(8)

        self._preview_stack = QStackedWidget()
        self._preview_stack.setMinimumHeight(200)
        self._preview_stack.setMaximumHeight(340)
        self._preview_stack.setStyleSheet("QStackedWidget { background-color: #1e1e1e; border-radius: 6px; }")

        # Page 0: Empty
        empty_w = QWidget()
        empty_l = QVBoxLayout(empty_w)
        self._empty_label = QLabel("无预览")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("color: #666; font-size: 14px;")
        empty_l.addWidget(self._empty_label)
        self._preview_stack.addWidget(empty_w)

        # Page 1: Image
        self._image_scroll = QScrollArea()
        self._image_scroll.setWidgetResizable(True)
        self._image_scroll.setStyleSheet("QScrollArea { background-color: #1e1e1e; border: none; }")
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_scroll.setWidget(self._image_label)
        self._preview_stack.addWidget(self._image_scroll)

        # Page 2: Video
        video_w = QWidget()
        video_l = QVBoxLayout(video_w)
        video_l.setContentsMargins(0, 0, 0, 0)
        video_l.setSpacing(6)
        self._video_widget = QVideoWidget()
        self._video_widget.setMinimumHeight(180)
        self._video_widget.setMaximumHeight(260)
        video_l.addWidget(self._video_widget, 1)
        vctrl = QHBoxLayout()
        self._v_play_btn = QPushButton("播放")
        self._v_play_btn.clicked.connect(self._toggle_video)
        vctrl.addWidget(self._v_play_btn)
        self._v_seek = QSlider(Qt.Orientation.Horizontal)
        self._v_seek.setRange(0, 0)
        self._v_seek.sliderMoved.connect(self._seek_video)
        vctrl.addWidget(self._v_seek, 1)
        self._v_time = QLabel("00:00 / 00:00")
        self._v_time.setStyleSheet("color: #aaa; font-size: 11px;")
        self._v_time.setFixedWidth(110)
        vctrl.addWidget(self._v_time)
        video_l.addLayout(vctrl)
        self._preview_stack.addWidget(video_w)

        # Page 3: Audio
        audio_w = QWidget()
        audio_l = QVBoxLayout(audio_w)
        audio_l.setContentsMargins(16, 16, 16, 16)
        audio_l.setSpacing(10)
        self._audio_visual = QLabel("🎵 音频预览")
        self._audio_visual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._audio_visual.setMinimumHeight(100)
        self._audio_visual.setStyleSheet(
            "background-color: #2d2d2d; border-radius: 8px; color: #888; font-size: 20px;"
        )
        audio_l.addWidget(self._audio_visual)
        actrl = QHBoxLayout()
        self._a_play_btn = QPushButton("播放")
        self._a_play_btn.clicked.connect(self._toggle_audio)
        actrl.addWidget(self._a_play_btn)
        self._a_seek = QSlider(Qt.Orientation.Horizontal)
        self._a_seek.setRange(0, 0)
        self._a_seek.sliderMoved.connect(self._seek_audio)
        actrl.addWidget(self._a_seek, 1)
        self._a_time = QLabel("00:00 / 00:00")
        self._a_time.setStyleSheet("color: #aaa; font-size: 11px;")
        self._a_time.setFixedWidth(110)
        actrl.addWidget(self._a_time)
        audio_l.addLayout(actrl)
        self._preview_stack.addWidget(audio_w)

        # Page 4: Text
        self._text_view = QPlainTextEdit()
        self._text_view.setReadOnly(True)
        self._text_view.setStyleSheet(
            "QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4;"
            " font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;"
            " border: none; }"
        )
        self._preview_stack.addWidget(self._text_view)

        preview_layout.addWidget(self._preview_stack)

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

        self._relocate_btn = QPushButton("重新定位")
        self._relocate_btn.setVisible(False)
        self._relocate_btn.clicked.connect(self._relocate_file)
        btn_row.addWidget(self._relocate_btn)

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

        self._relocate_btn.setVisible(not self._node.file_exists)

        preview_path = self._storage.get_preview_path(self._node.id)
        if preview_path and os.path.isfile(preview_path):
            self._show_preview(preview_path)
        else:
            self._preview_stack.setCurrentIndex(self.PG_EMPTY)

    def _detect_type(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        return PREVIEW_TYPE.get(ext, "")

    def _show_preview(self, path: str):
        ptype = self._detect_type(path)
        self._stop_media()
        self._current_preview_type = ptype

        if ptype == "image":
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self._image_label.setPixmap(pixmap.scaled(
                    QSize(400, 280),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
                self._preview_stack.setCurrentIndex(self.PG_IMAGE)
                return
        elif ptype == "video":
            self._video_player = QMediaPlayer()
            self._v_audio = QAudioOutput()
            self._video_player.setAudioOutput(self._v_audio)
            self._video_player.setVideoOutput(self._video_widget)
            self._video_player.setSource(QUrl.fromLocalFile(path))
            self._video_player.positionChanged.connect(self._v_position_changed)
            self._video_player.durationChanged.connect(self._v_duration_changed)
            self._video_player.playbackStateChanged.connect(self._v_state_changed)
            self._v_seek.setRange(0, 0)
            self._v_time.setText("00:00 / 00:00")
            self._preview_stack.setCurrentIndex(self.PG_VIDEO)
            return
        elif ptype == "audio":
            self._audio_player = QMediaPlayer()
            self._a_output = QAudioOutput()
            self._audio_player.setAudioOutput(self._a_output)
            self._audio_player.setSource(QUrl.fromLocalFile(path))
            self._audio_player.positionChanged.connect(self._a_position_changed)
            self._audio_player.durationChanged.connect(self._a_duration_changed)
            self._audio_player.playbackStateChanged.connect(self._a_state_changed)
            self._a_seek.setRange(0, 0)
            self._a_time.setText("00:00 / 00:00")
            self._preview_stack.setCurrentIndex(self.PG_AUDIO)
            return
        elif ptype == "text":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read(100000)  # limit 100KB
                self._text_view.setPlainText(content)
                self._preview_stack.setCurrentIndex(self.PG_TEXT)
                return
            except (OSError, UnicodeDecodeError):
                pass

        # Fallback
        self._preview_stack.setCurrentIndex(self.PG_EMPTY)

    def _upload_preview(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择预览文件", "",
            "所有支持格式 (*.png *.jpg *.jpeg *.gif *.bmp *.webp"
            " *.mp4 *.mov *.avi *.webm *.mkv *.wmv *.flv"
            " *.mp3 *.wav *.flac *.ogg *.aac *.wma *.m4a"
            " *.txt *.md *.py *.json *.xml *.html *.css"
            " *.js *.yaml *.yml *.cfg *.ini *.log *.csv"
            " *.toml *.rst *.bat *.sh *.ps1);;"
            "图片 (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;"
            "视频 (*.mp4 *.mov *.avi *.webm *.mkv *.wmv);;"
            "音频 (*.mp3 *.wav *.flac *.ogg *.aac *.wma);;"
            "文本 (*.txt *.md *.py *.json *.xml *.html *.css *.js *.yaml *.yml *.csv *.log);;"
            "所有文件 (*)"
        )
        if file_path:
            preview_path = self._storage.import_preview(self._node.id, file_path)
            self._node.preview_path = preview_path
            self._storage.update_node(self._node)
            self._show_preview(preview_path)

    def _delete_preview(self):
        # Switch away from media pages FIRST so widgets stop painting
        self._preview_stack.setCurrentIndex(self.PG_EMPTY)
        # Release file handles before deleting files on disk
        self._release_media()
        self._storage.remove_preview(self._node.id)
        self._node.preview_path = ""
        self._storage.update_node(self._node)
        self._current_preview_type = None
        # Now safe to destroy players
        self._destroy_players()

    # ---- media controls ----
    def _release_media(self):
        """Stop playback and release file handles, keep players alive."""
        if self._video_player:
            self._video_player.blockSignals(True)
            self._video_player.stop()
            self._video_player.setSource(QUrl())
            self._video_player.setVideoOutput(None)
        if self._audio_player:
            self._audio_player.blockSignals(True)
            self._audio_player.stop()
            self._audio_player.setSource(QUrl())

    def _destroy_players(self):
        if self._video_player:
            try:
                self._video_player.positionChanged.disconnect()
                self._video_player.durationChanged.disconnect()
                self._video_player.playbackStateChanged.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._video_player.deleteLater()
            self._video_player = None
        if self._audio_player:
            try:
                self._audio_player.positionChanged.disconnect()
                self._audio_player.durationChanged.disconnect()
                self._audio_player.playbackStateChanged.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._audio_player.deleteLater()
            self._audio_player = None
        self._v_play_btn.setText("播放")
        self._a_play_btn.setText("播放")

    def _stop_media(self):
        self._release_media()
        self._destroy_players()

    def _toggle_video(self):
        if not self._video_player:
            return
        if self._video_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._video_player.pause()
        else:
            self._video_player.play()

    def _seek_video(self, pos: int):
        if self._video_player:
            self._video_player.setPosition(pos)

    def _v_position_changed(self, pos: int):
        self._v_seek.blockSignals(True)
        self._v_seek.setValue(pos)
        self._v_seek.blockSignals(False)
        dur = self._video_player.duration() if self._video_player else 0
        self._v_time.setText(f"{self._fmt_time(pos)} / {self._fmt_time(dur)}")

    def _v_duration_changed(self, dur: int):
        self._v_seek.setRange(0, dur)
        self._v_time.setText(f"00:00 / {self._fmt_time(dur)}")

    def _v_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._v_play_btn.setText("暂停")
        else:
            self._v_play_btn.setText("播放")

    def _toggle_audio(self):
        if not self._audio_player:
            return
        if self._audio_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._audio_player.pause()
        else:
            self._audio_player.play()

    def _seek_audio(self, pos: int):
        if self._audio_player:
            self._audio_player.setPosition(pos)

    def _a_position_changed(self, pos: int):
        self._a_seek.blockSignals(True)
        self._a_seek.setValue(pos)
        self._a_seek.blockSignals(False)
        dur = self._audio_player.duration() if self._audio_player else 0
        self._a_time.setText(f"{self._fmt_time(pos)} / {self._fmt_time(dur)}")

    def _a_duration_changed(self, dur: int):
        self._a_seek.setRange(0, dur)
        self._a_time.setText(f"00:00 / {self._fmt_time(dur)}")

    def _a_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._a_play_btn.setText("暂停")
        else:
            self._a_play_btn.setText("播放")

    @staticmethod
    def _fmt_time(ms: int) -> str:
        s = ms // 1000
        m, s = divmod(s, 60)
        return f"{m:02d}:{s:02d}"

    def closeEvent(self, event):
        self._preview_stack.setCurrentIndex(self.PG_EMPTY)
        self._stop_media()
        super().closeEvent(event)

    def _save_description(self):
        self._node.description = self._desc_edit.toPlainText().strip()
        self._storage.update_node(self._node)

    def _open_file_location(self):
        if self._node.file_path and os.path.isfile(self._node.file_path):
            folder = os.path.dirname(self._node.file_path)
            if os.path.isdir(folder):
                subprocess.Popen(["explorer", "/select,", self._node.file_path])

    def _relocate_file(self):
        if not self._untracked_files:
            QMessageBox.warning(self, "提示", "没有可用的未追踪文件。")
            return

        dlg = MergeFileDialog(self._untracked_files, self, title="选择重新定位的文件")
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_path = dlg.selected_file()
        if not new_path:
            return

        try:
            new_info = Node.from_file(new_path)
        except OSError as e:
            QMessageBox.warning(self, "错误", f"无法读取文件: {e}")
            return

        self._node.file_path = new_info.file_path
        self._node.filename = new_info.filename
        self._node.last_modified = new_info.last_modified
        self._node.created_at = new_info.created_at

        self._storage.update_node(self._node)

        self._load_data()
        self.setWindowTitle(f"节点详情 - {self._node.filename}")

        self.node_relocated.emit(self._node.id)


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
    def __init__(self, untracked_files: list[str], parent=None, title: str = "选择合并结果文件"):
        super().__init__(parent)
        self.setWindowTitle(title)
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
