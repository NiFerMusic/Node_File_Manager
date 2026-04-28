DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}
QMenuBar {
    background-color: #252526;
    color: #cccccc;
    border-bottom: 1px solid #3c3c3c;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #094771;
}
QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3c3c3c;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #094771;
}
QMenu::separator {
    height: 1px;
    background: #3c3c3c;
    margin: 4px 8px;
}
QToolBar {
    background-color: #252526;
    border-bottom: 1px solid #3c3c3c;
    spacing: 6px;
    padding: 3px;
}
QToolBar QLabel {
    color: #cccccc;
    font-size: 13px;
    padding: 0 4px;
}
QToolButton {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
}
QToolButton:hover {
    background-color: #2a2d2e;
    border-color: #555;
}
QToolButton:pressed {
    background-color: #094771;
}
QSplitter::handle {
    background-color: #3c3c3c;
    height: 2px;
}
QStatusBar {
    background-color: #252526;
    color: #888;
    border-top: 1px solid #3c3c3c;
    font-size: 12px;
}
QScrollBar:horizontal, QScrollBar:vertical {
    background-color: #1e1e1e;
    border: none;
}
QScrollBar:horizontal {
    height: 10px;
}
QScrollBar:vertical {
    width: 10px;
}
QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background-color: #424242;
    border-radius: 4px;
    min-width: 20px;
    min-height: 20px;
}
QScrollBar::handle:horizontal:hover, QScrollBar::handle:vertical:hover {
    background-color: #555;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
    width: 0;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: none;
}
QTreeView {
    background-color: #1e1e1e;
    color: #cccccc;
    border: none;
    outline: none;
}
QTreeView::item {
    padding: 6px 8px;
    border-radius: 4px;
}
QTreeView::item:hover {
    background-color: #2a2d2e;
}
QTreeView::item:selected {
    background-color: #094771;
}
QHeaderView::section {
    background-color: #252526;
    color: #888;
    border: none;
    border-bottom: 1px solid #3c3c3c;
    padding: 6px 8px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
}
QLabel {
    color: #cccccc;
}
QDialog {
    background-color: #252526;
    color: #cccccc;
}
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #007acc;
}
QPushButton {
    background-color: #0e639c;
    color: #fff;
    border: none;
    border-radius: 4px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #094771;
}
QPushButton[flat="true"] {
    background-color: transparent;
    color: #cccccc;
    border: 1px solid #555;
}
QPushButton[flat="true"]:hover {
    background-color: #2a2d2e;
}
QComboBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}
QComboBox:hover {
    border-color: #888;
}
QComboBox QAbstractItemView {
    background-color: #252526;
    color: #cccccc;
    selection-background-color: #094771;
    border: 1px solid #3c3c3c;
}
QCheckBox {
    color: #cccccc;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555;
    border-radius: 3px;
    background-color: #3c3c3c;
}
QCheckBox::indicator:checked {
    background-color: #007acc;
    border-color: #007acc;
}
QGroupBox {
    color: #cccccc;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px;
    font-size: 13px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
"""
