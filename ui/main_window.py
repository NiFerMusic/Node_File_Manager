from __future__ import annotations

import os
import time

from PyQt6.QtCore import QSettings, Qt, QTimer, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from core.models import Edge, Node, Project
from core.storage import ProjectStorage
from ui.dialogs import DescriptionDialog, MergeFileDialog, NewProjectDialog, NodeDetailDialog
from ui.file_panel import FilePanel
from ui.graph_canvas import GraphCanvas
from ui.theme import DARK_STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._project: Project | None = None
        self._storage: ProjectStorage | None = None
        self._nodes: list[Node] = []
        self._edges: list[Edge] = []

        self.setWindowTitle("Visual Version Tree")
        self.setMinimumSize(1000, 650)
        self.resize(1400, 900)

        self._setup_menu()
        self._setup_toolbar()
        self._setup_central()
        self._setup_status()
        self._restore_geometry()

    def _setup_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("文件(&F)")

        new_action = QAction("新建项目...", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_action = QAction("打开项目...", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        close_action = QAction("关闭项目", self)
        close_action.triggered.connect(self._close_project)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menu_bar.addMenu("视图(&V)")

        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl+="))
        zoom_in_action.triggered.connect(lambda: self._canvas.zoom_in())
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(lambda: self._canvas.zoom_out())
        view_menu.addAction(zoom_out_action)

        fit_action = QAction("适应窗口", self)
        fit_action.setShortcut(QKeySequence("Ctrl+0"))
        fit_action.triggered.connect(lambda: self._canvas.fit_all())
        view_menu.addAction(fit_action)

    def _setup_toolbar(self):
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self._project_label = QLabel("未打开项目")
        self._project_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        toolbar.addWidget(self._project_label)

        toolbar.addSeparator()

        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("放大")
        zoom_in_btn.clicked.connect(lambda: self._canvas.zoom_in())
        toolbar.addWidget(zoom_in_btn)

        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("缩小")
        zoom_out_btn.clicked.connect(lambda: self._canvas.zoom_out())
        toolbar.addWidget(zoom_out_btn)

        fit_btn = QToolButton()
        fit_btn.setText("适应")
        fit_btn.clicked.connect(lambda: self._canvas.fit_all())
        toolbar.addWidget(fit_btn)

        toolbar.addSeparator()

        add_root_btn = QToolButton()
        add_root_btn.setText("添加根节点")
        add_root_btn.clicked.connect(self._add_root_node)
        toolbar.addWidget(add_root_btn)

    def _setup_central(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self._canvas = GraphCanvas()
        self._canvas.node_clicked.connect(self._on_node_clicked)
        self._canvas.node_double_clicked.connect(self._on_node_double_clicked)
        self._canvas.node_dropped.connect(self._on_node_dropped)
        self._canvas.file_dropped_on_canvas.connect(self._on_file_dropped_on_canvas)
        self._canvas.merge_requested.connect(self._on_merge_requested)
        self._canvas.delete_node_requested.connect(self._on_delete_node)
        self._canvas.edit_description_requested.connect(self._on_edit_description)
        splitter.addWidget(self._canvas)

        self._file_panel = FilePanel()
        self._file_panel.file_double_clicked.connect(self._on_file_double_clicked)
        splitter.addWidget(self._file_panel)

        splitter.setSizes([600, 300])
        layout.addWidget(splitter)

    def _setup_status(self):
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._node_count_label = QLabel("节点: 0")
        self._edge_count_label = QLabel("边: 0")
        self._status_bar.addWidget(self._node_count_label)
        self._status_bar.addWidget(self._edge_count_label)

    # ---- project management ----
    def _new_project(self):
        dlg = NewProjectDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        name, root_path, exts = dlg.get_project_info()

        project = Project(
            name=name,
            root_path=root_path,
            allowed_extensions=exts,
            created_at=time.time(),
        )

        self._storage = ProjectStorage(root_path)
        self._storage.init_project(project)
        self._project = project
        self._nodes = []
        self._edges = []

        self._update_title()
        self._file_panel.set_project(root_path, exts)
        self._rebuild_graph()
        self._update_status()

    def _open_project(self):
        path = QFileDialog.getExistingDirectory(self, "选择项目根目录")
        if not path:
            return
        vmtree = os.path.join(path, ".vmtree")
        if not os.path.isdir(vmtree):
            QMessageBox.warning(self, "警告", "所选目录不是有效的 VVT 项目（缺少 .vmtree）。")
            return

        self._storage = ProjectStorage(path)
        project = self._storage.load_project()
        if not project:
            QMessageBox.warning(self, "警告", "无法加载项目数据。")
            return

        self._project = project
        self._nodes = self._storage.load_nodes()
        self._edges = self._storage.load_edges()

        self._update_title()
        tracked_paths = {n.file_path for n in self._nodes if n.file_path}
        self._file_panel.set_project(project.root_path, project.allowed_extensions)
        self._file_panel.set_tracked_paths(tracked_paths)
        self._file_panel.refresh()
        self._rebuild_graph()
        self._update_status()

    def _close_project(self):
        self._project = None
        self._storage = None
        self._nodes = []
        self._edges = []
        self._canvas.rebuild([], [])
        self._file_panel.set_project("", [])
        self.setWindowTitle("Visual Version Tree")
        self._project_label.setText("未打开项目")
        self._update_status()

    # ---- graph operations ----
    def _on_node_dropped(self, target_id: str, file_path: str):
        if not self._storage:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if self._project and ext not in self._project.allowed_extensions:
            QMessageBox.warning(self, "警告", f"不支持的文件格式: {ext}")
            return

        filename = os.path.basename(file_path)
        desc_dlg = DescriptionDialog(filename, self)
        if desc_dlg.exec() != QDialog.DialogCode.Accepted:
            return
        description = desc_dlg.description()

        new_node = Node.from_file(file_path)
        new_node.description = description
        self._storage.add_node(new_node)

        edge = Edge(source_id=target_id, target_id=new_node.id)
        self._storage.add_edge(edge)

        self._refresh_from_storage()

    def _on_file_dropped_on_canvas(self, file_path: str):
        if not self._storage:
            QMessageBox.warning(self, "提示", "请先创建或打开项目。")
            return

        ext = os.path.splitext(file_path)[1].lower()
        if self._project and ext not in self._project.allowed_extensions:
            QMessageBox.warning(self, "警告", f"不支持的文件格式: {ext}")
            return

        filename = os.path.basename(file_path)
        desc_dlg = DescriptionDialog(filename, self)
        if desc_dlg.exec() != QDialog.DialogCode.Accepted:
            return
        description = desc_dlg.description()

        new_node = Node.from_file(file_path)
        new_node.description = description
        self._storage.add_node(new_node)
        self._refresh_from_storage()

    def _on_merge_requested(self, selected_ids: list[str]):
        if not self._storage or len(selected_ids) < 2:
            return

        untracked = self._file_panel.untracked_files()
        if not untracked:
            QMessageBox.warning(self, "提示", "没有可用的未追踪文件作为合并结果。")
            return

        file_dlg = MergeFileDialog(untracked, self)
        if file_dlg.exec() != QDialog.DialogCode.Accepted:
            return
        file_path = file_dlg.selected_file()
        if not file_path:
            return

        desc, ok = QInputDialog.getText(self, "合并描述", "描述合并内容:")
        if not ok:
            return

        merge_node = Node.from_file(file_path)
        merge_node.description = desc
        merge_node.node_type = "merge"
        self._storage.add_node(merge_node)

        for sid in selected_ids:
            edge = Edge(source_id=sid, target_id=merge_node.id)
            self._storage.add_edge(edge)

        self._refresh_from_storage()

    def _on_delete_node(self, node_id: str):
        if not self._storage:
            return
        reply = QMessageBox.question(self, "确认删除", "确定要删除此节点吗？此操作不可撤销。")
        if reply == QMessageBox.StandardButton.Yes:
            self._storage.remove_node(node_id)
            self._refresh_from_storage()

    def _on_edit_description(self, node_id: str):
        if not self._storage:
            return
        node = self._storage.get_node(node_id)
        if not node:
            return
        desc, ok = QInputDialog.getMultiLineText(self, "编辑描述", "修改描述:", node.description)
        if ok:
            node.description = desc.strip()
            self._storage.update_node(node)
            self._refresh_from_storage()

    def _add_root_node(self):
        if not self._storage or not self._project:
            QMessageBox.warning(self, "提示", "请先创建或打开项目。")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择工程文件", self._project.root_path,
            "所有支持的格式 (*.blend *.psd *.ai *.aep *.prproj *.c4d *.ma *.mb *.max *.fbx *.obj)"
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self._project.allowed_extensions:
            QMessageBox.warning(self, "警告", f"不支持的文件格式: {ext}")
            return

        filename = os.path.basename(file_path)
        desc_dlg = DescriptionDialog(filename, self)
        if desc_dlg.exec() != QDialog.DialogCode.Accepted:
            return

        new_node = Node.from_file(file_path)
        new_node.description = desc_dlg.description()
        self._storage.add_node(new_node)
        self._refresh_from_storage()

    # ---- node interactions ----
    def _on_node_clicked(self, node_id: str):
        self._update_status()

    def _on_node_double_clicked(self, node_id: str):
        if not self._storage:
            return
        node = self._storage.get_node(node_id)
        if node:
            dlg = NodeDetailDialog(node, self._storage, self)
            dlg.finished.connect(lambda: self._refresh_from_storage())
            dlg.show()

    def _on_file_double_clicked(self, file_path: str):
        if os.path.isfile(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(file_path)))

    # ---- helpers ----
    def _refresh_from_storage(self):
        if not self._storage:
            return
        self._nodes = self._storage.load_nodes()
        self._edges = self._storage.load_edges()
        tracked_paths = {n.file_path for n in self._nodes if n.file_path}
        self._file_panel.set_tracked_paths(tracked_paths)
        self._file_panel.refresh()
        self._rebuild_graph()
        self._update_status()

    def _rebuild_graph(self):
        self._canvas.rebuild(self._nodes, self._edges)

    def _update_title(self):
        if self._project:
            self.setWindowTitle(f"Visual Version Tree — {self._project.name}")
            self._project_label.setText(self._project.name)

    def _update_status(self):
        self._node_count_label.setText(f"节点: {len(self._nodes)}")
        self._edge_count_label.setText(f"边: {len(self._edges)}")

    def _restore_geometry(self):
        settings = QSettings("VVT", "VisualVersionTree")
        geo = settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        else:
            self.resize(1400, 900)

    def closeEvent(self, event):
        settings = QSettings("VVT", "VisualVersionTree")
        settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
