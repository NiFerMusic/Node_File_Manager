DARK_STYLESHEET = """
QMainWindow {
    background-color: #161616;
}
QMenuBar {
    background-color: #1e1e20;
    color: #cccccc;
    border-bottom: 1px solid #2a2a2d;
    padding: 3px 4px;
    font-size: 13px;
}
QMenuBar::item:selected {
    background-color: rgba(0, 122, 204, 0.25);
    border-radius: 5px;
}
QMenu {
    background-color: #222224;
    color: #d0d0d0;
    border: 1px solid #333338;
    border-radius: 8px;
    padding: 5px;
}
QMenu::item {
    border-radius: 5px;
    padding: 6px 28px 6px 12px;
    margin: 1px 4px;
}
QMenu::item:selected {
    background-color: rgba(0, 122, 204, 0.30);
}
QMenu::separator {
    height: 1px;
    background: #333338;
    margin: 5px 10px;
}
QToolBar {
    background-color: #1e1e20;
    border-bottom: 1px solid #2a2a2d;
    spacing: 8px;
    padding: 4px 6px;
}
QToolBar QLabel {
    color: #d0d0d0;
    font-size: 13px;
    padding: 0 6px;
}
QToolButton {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
}
QToolButton:hover {
    background-color: #2a2a2e;
    border-color: #3e3e44;
}
QToolButton:pressed {
    background-color: rgba(0, 122, 204, 0.25);
}
QSplitter::handle {
    background-color: #2a2a2d;
    height: 2px;
}
QStatusBar {
    background-color: #1e1e20;
    color: #888;
    border-top: 1px solid #2a2a2d;
    font-size: 12px;
    padding: 2px 6px;
}
QScrollBar:horizontal, QScrollBar:vertical {
    background-color: #161616;
    border: none;
}
QScrollBar:horizontal {
    height: 8px;
}
QScrollBar:vertical {
    width: 8px;
}
QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background-color: #3a3a3e;
    border-radius: 4px;
    min-width: 24px;
    min-height: 24px;
}
QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {
    background-color: #505056;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: none;
}
QTreeView {
    background-color: #161616;
    color: #d0d0d0;
    border: none;
    outline: none;
}
QTreeView::item {
    padding: 7px 10px;
    border-radius: 6px;
}
QTreeView::item:hover {
    background-color: #222226;
}
QTreeView::item:selected {
    background-color: rgba(0, 122, 204, 0.28);
}
QHeaderView::section {
    background-color: #1e1e20;
    color: #888;
    border: none;
    border-bottom: 1px solid #2a2a2d;
    padding: 7px 10px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
}
QLabel {
    color: #cccccc;
}
QDialog {
    background-color: #1e1e20;
    color: #cccccc;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #26262a;
    color: #d0d0d0;
    border: 1px solid #3a3a3e;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #007acc;
}
QPushButton {
    background-color: #0066aa;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #007acc;
}
QPushButton:pressed {
    background-color: #005588;
}
QPushButton[flat="true"] {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid #44444a;
    border-radius: 6px;
}
QPushButton[flat="true"]:hover {
    background-color: #2a2a2e;
    border-color: #55555c;
}
QComboBox {
    background-color: #26262a;
    color: #d0d0d0;
    border: 1px solid #3a3a3e;
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #505056;
}
QComboBox QAbstractItemView {
    background-color: #222224;
    color: #d0d0d0;
    selection-background-color: rgba(0, 122, 204, 0.30);
    border: 1px solid #333338;
    border-radius: 6px;
    outline: none;
}
QCheckBox {
    color: #cccccc;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border: 1px solid #4a4a50;
    border-radius: 4px;
    background-color: #26262a;
}
QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}
QGroupBox {
    color: #cccccc;
    border: 1px solid #2a2a2d;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px;
    font-size: 13px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
}
QSlider::groove:horizontal {
    background: #2a2a2e;
    border-radius: 3px;
    height: 6px;
}
QSlider::handle:horizontal {
    background: #007acc;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background: #007acc;
    border-radius: 3px;
}
QListWidget {
    background-color: #161616;
    color: #d0d0d0;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 7px 10px;
    border-radius: 5px;
}
QListWidget::item:hover {
    background-color: #222226;
}
QListWidget::item:selected {
    background-color: rgba(0, 122, 204, 0.28);
}
"""
