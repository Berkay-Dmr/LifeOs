from __future__ import annotations

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1a1b26;
    color: #c0caf5;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* Sidebar */
#sidebar {
    background-color: #16161e;
    border-right: 1px solid #292e42;
    min-width: 200px;
    max-width: 200px;
}

#sidebar QPushButton {
    background: transparent;
    color: #787c99;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
}

#sidebar QPushButton:hover {
    background-color: #292e42;
    color: #c0caf5;
}

#sidebar QPushButton:checked {
    background-color: #7aa2f7;
    color: #1a1b26;
    font-weight: bold;
}

/* Search Input */
QLineEdit#searchInput {
    background-color: #24283b;
    border: 2px solid #292e42;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 15px;
    color: #c0caf5;
    selection-background-color: #7aa2f7;
}

QLineEdit#searchInput:focus {
    border-color: #7aa2f7;
}

/* Ask Input */
QLineEdit#askInput {
    background-color: #24283b;
    border: 2px solid #292e42;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 15px;
    color: #c0caf5;
}

QLineEdit#askInput:focus {
    border-color: #bb9af7;
}

/* Buttons */
QPushButton#primaryBtn {
    background-color: #7aa2f7;
    color: #1a1b26;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton#primaryBtn:hover {
    background-color: #89b4fa;
}

QPushButton#primaryBtn:pressed {
    background-color: #6c8be6;
}

QPushButton#dangerBtn {
    background-color: #f7768e;
    color: #1a1b26;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background-color: #ff899e;
}

/* Result Cards */
QFrame#resultCard {
    background-color: #24283b;
    border: 1px solid #292e42;
    border-radius: 10px;
    padding: 16px;
}

QFrame#resultCard:hover {
    border-color: #7aa2f7;
}

QFrame#answerCard {
    background-color: #1e2030;
    border: 1px solid #bb9af7;
    border-radius: 12px;
    padding: 20px;
}

/* Labels */
QLabel#titleLabel {
    font-size: 22px;
    font-weight: bold;
    color: #7aa2f7;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #787c99;
}

QLabel#sourceLabel {
    font-size: 12px;
    color: #9ece6a;
    background-color: #1a2232;
    border-radius: 4px;
    padding: 2px 6px;
}

QLabel#scoreLabel {
    font-size: 12px;
    color: #e0af68;
    font-weight: bold;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #1a1b26;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #292e42;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #787c99;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Text Browser (for answers) */
QTextBrowser {
    background-color: #1e2030;
    color: #c0caf5;
    border: none;
    padding: 16px;
    font-size: 14px;
    line-height: 1.6;
}

/* Combo Box */
QComboBox {
    background-color: #24283b;
    border: 1px solid #292e42;
    border-radius: 6px;
    padding: 6px 12px;
    color: #c0caf5;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #24283b;
    color: #c0caf5;
    selection-background-color: #7aa2f7;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #292e42;
    border-radius: 8px;
    background-color: #1a1b26;
}

QTabBar::tab {
    background-color: #24283b;
    color: #787c99;
    padding: 8px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #1a1b26;
    color: #7aa2f7;
    border-bottom: 2px solid #7aa2f7;
}

/* Status Bar */
QStatusBar {
    background-color: #16161e;
    color: #787c99;
    border-top: 1px solid #292e42;
}
"""
