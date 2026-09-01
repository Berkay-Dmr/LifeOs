from __future__ import annotations


# ── DARK THEME ───────────────────────────────────────────────────────────────

DARK_THEME = """
/* ── Global ─────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #161b22, stop:0.5 #0d1117, stop:1 #010409);
    border-right: 1px solid #21262d;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background: transparent;
    color: #8b949e;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    text-align: left;
    font-size: 13px;
    margin: 3px 8px;
}

#sidebar QPushButton:hover {
    background: rgba(56,139,253,0.15);
    color: #c9d1d9;
}

#sidebar QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    color: #ffffff;
    font-weight: bold;
}

/* ── Search Input ───────────────────────────────────────────────────────── */
QLineEdit#searchInput {
    background: #0d1117;
    border: 2px solid #30363d;
    border-radius: 12px;
    padding: 14px 20px;
    font-size: 15px;
    color: #e6edf3;
    selection-background-color: #388bfd;
}

QLineEdit#searchInput:focus {
    border-color: #58a6ff;
    background: #161b22;
}

/* ── Ask Input ──────────────────────────────────────────────────────────── */
QLineEdit#askInput {
    background: #0d1117;
    border: 2px solid #30363d;
    border-radius: 12px;
    padding: 16px 22px;
    font-size: 15px;
    color: #e6edf3;
}

QLineEdit#askInput:focus {
    border-color: #a371f7;
    background: #161b22;
}

/* ── Primary Button ─────────────────────────────────────────────────────── */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ea043, stop:1 #3fb950);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a7f37, stop:1 #238636);
}

QPushButton#primaryBtn:disabled {
    background: #21262d;
    color: #484f58;
}

/* ── Danger Button ──────────────────────────────────────────────────────── */
QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #da3633, stop:1 #f85149);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f85149, stop:1 #ff7b72);
}

/* ── Warning Button ─────────────────────────────────────────────────────── */
QPushButton#warningBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d29922, stop:1 #e3b341);
    color: #0d1117;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#warningBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e3b341, stop:1 #f0c75e);
}

/* ── Result Cards ───────────────────────────────────────────────────────── */
QFrame#resultCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #161b22, stop:1 #0d1117);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 18px;
}

QFrame#resultCard:hover {
    border-color: #58a6ff;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1c2333, stop:1 #161b22);
}

/* ── Answer Card ────────────────────────────────────────────────────────── */
QFrame#answerCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1040, stop:1 #150d35);
    border: 1px solid #a371f7;
    border-radius: 12px;
    padding: 22px;
}

/* ── Labels ─────────────────────────────────────────────────────────────── */
QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #58a6ff;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #8b949e;
}

QLabel#sourceLabel {
    font-size: 11px;
    color: #3fb950;
    background: rgba(46,160,67,0.15);
    border-radius: 6px;
    padding: 3px 8px;
}

QLabel#scoreLabel {
    font-size: 12px;
    color: #e3b341;
    font-weight: bold;
}

/* ── Scroll Area ────────────────────────────────────────────────────────── */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #0d1117;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #30363d;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── Text Browser ───────────────────────────────────────────────────────── */
QTextBrowser {
    background-color: #0d1117;
    color: #e6edf3;
    border: none;
    padding: 18px;
    font-size: 14px;
    line-height: 1.6;
}

/* ── Combo Box ──────────────────────────────────────────────────────────── */
QComboBox {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 14px;
    color: #e6edf3;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    color: #e6edf3;
    selection-background-color: #388bfd;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 4px;
}

/* ── Spin Box ───────────────────────────────────────────────────────────── */
QSpinBox {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e6edf3;
}

QSpinBox:hover {
    border-color: #58a6ff;
}

/* ── Date Edit ──────────────────────────────────────────────────────────── */
QDateEdit {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e6edf3;
}

QDateEdit:hover {
    border-color: #58a6ff;
}

/* ── Tab Widget ─────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #21262d;
    border-radius: 10px;
    background-color: #0d1117;
}

QTabBar::tab {
    background: #161b22;
    color: #8b949e;
    padding: 10px 24px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 2px;
    border: 1px solid #21262d;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: #0d1117;
    color: #58a6ff;
    border-bottom: 2px solid #58a6ff;
    font-weight: bold;
}

/* ── Status Bar ─────────────────────────────────────────────────────────── */
QStatusBar {
    background: #010409;
    color: #8b949e;
    border-top: 1px solid #21262d;
}

/* ── Progress Bar ───────────────────────────────────────────────────────── */
QProgressBar {
    background: #21262d;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:0.5 #58a6ff, stop:1 #a371f7);
    border-radius: 6px;
}

/* ── Tables ─────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    gridline-color: #161b22;
    color: #e6edf3;
    selection-background-color: rgba(56,139,253,0.3);
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #161b22;
}

QTableWidget::item:selected {
    background-color: rgba(56,139,253,0.2);
}

QHeaderView::section {
    background: #161b22;
    color: #8b949e;
    border: none;
    border-bottom: 1px solid #21262d;
    padding: 8px;
    font-weight: bold;
}

/* ── Tool Tips ──────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1c2333;
    color: #e6edf3;
    border: 1px solid #58a6ff;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

/* ── Message Box ────────────────────────────────────────────────────────── */
QMessageBox {
    background-color: #0d1117;
}

QMessageBox QLabel {
    color: #e6edf3;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #238636, stop:1 #2ea043);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2ea043, stop:1 #3fb950);
}
"""


# ── LIGHT THEME ──────────────────────────────────────────────────────────────

LIGHT_THEME = """
/* ── Global ─────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #ffffff;
    color: #1f2328;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #f6f8fa, stop:0.5 #ffffff, stop:1 #f6f8fa);
    border-right: 1px solid #d0d7de;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background: transparent;
    color: #656d76;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    text-align: left;
    font-size: 13px;
    margin: 3px 8px;
}

#sidebar QPushButton:hover {
    background: rgba(56,139,253,0.1);
    color: #1f2328;
}

#sidebar QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a7f37, stop:1 #2da44e);
    color: #ffffff;
    font-weight: bold;
}

/* ── Search Input ───────────────────────────────────────────────────────── */
QLineEdit#searchInput {
    background: #ffffff;
    border: 2px solid #d0d7de;
    border-radius: 12px;
    padding: 14px 20px;
    font-size: 15px;
    color: #1f2328;
    selection-background-color: #0969da;
}

QLineEdit#searchInput:focus {
    border-color: #0969da;
    background: #ffffff;
}

/* ── Ask Input ──────────────────────────────────────────────────────────── */
QLineEdit#askInput {
    background: #ffffff;
    border: 2px solid #d0d7de;
    border-radius: 12px;
    padding: 16px 22px;
    font-size: 15px;
    color: #1f2328;
}

QLineEdit#askInput:focus {
    border-color: #8250df;
    background: #ffffff;
}

/* ── Primary Button ─────────────────────────────────────────────────────── */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a7f37, stop:1 #2da44e);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2da44e, stop:1 #3fb950);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #116329, stop:1 #1a7f37);
}

QPushButton#primaryBtn:disabled {
    background: #d0d7de;
    color: #8c959f;
}

/* ── Danger Button ──────────────────────────────────────────────────────── */
QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #cf222e, stop:1 #d1242f);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #d1242f, stop:1 #e5534b);
}

/* ── Warning Button ─────────────────────────────────────────────────────── */
QPushButton#warningBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9a6700, stop:1 #bf8700);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#warningBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #bf8700, stop:1 #d4a72c);
}

/* ── Result Cards ───────────────────────────────────────────────────────── */
QFrame#resultCard {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 12px;
    padding: 18px;
}

QFrame#resultCard:hover {
    border-color: #0969da;
    background: #f6f8fa;
}

/* ── Answer Card ────────────────────────────────────────────────────────── */
QFrame#answerCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #f5f0ff, stop:1 #faf5ff);
    border: 1px solid #8250df;
    border-radius: 12px;
    padding: 22px;
}

/* ── Labels ─────────────────────────────────────────────────────────────── */
QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #0969da;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #656d76;
}

QLabel#sourceLabel {
    font-size: 11px;
    color: #1a7f37;
    background: rgba(26,127,55,0.1);
    border-radius: 6px;
    padding: 3px 8px;
}

QLabel#scoreLabel {
    font-size: 12px;
    color: #9a6700;
    font-weight: bold;
}

/* ── Scroll Area ────────────────────────────────────────────────────────── */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #ffffff;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #d0d7de;
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #8c959f;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── Text Browser ───────────────────────────────────────────────────────── */
QTextBrowser {
    background-color: #ffffff;
    color: #1f2328;
    border: none;
    padding: 18px;
    font-size: 14px;
    line-height: 1.6;
}

/* ── Combo Box ──────────────────────────────────────────────────────────── */
QComboBox {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 8px 14px;
    color: #1f2328;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #0969da;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1f2328;
    selection-background-color: #0969da;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 4px;
}

/* ── Spin Box ───────────────────────────────────────────────────────────── */
QSpinBox {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1f2328;
}

QSpinBox:hover {
    border-color: #0969da;
}

/* ── Date Edit ──────────────────────────────────────────────────────────── */
QDateEdit {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 6px 10px;
    color: #1f2328;
}

QDateEdit:hover {
    border-color: #0969da;
}

/* ── Tab Widget ─────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #d0d7de;
    border-radius: 10px;
    background-color: #ffffff;
}

QTabBar::tab {
    background: #f6f8fa;
    color: #656d76;
    padding: 10px 24px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 2px;
    border: 1px solid #d0d7de;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #0969da;
    border-bottom: 2px solid #0969da;
    font-weight: bold;
}

/* ── Status Bar ─────────────────────────────────────────────────────────── */
QStatusBar {
    background: #f6f8fa;
    color: #656d76;
    border-top: 1px solid #d0d7de;
}

/* ── Progress Bar ───────────────────────────────────────────────────────── */
QProgressBar {
    background: #d0d7de;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a7f37, stop:0.5 #0969da, stop:1 #8250df);
    border-radius: 6px;
}

/* ── Tables ─────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    gridline-color: #f6f8fa;
    color: #1f2328;
    selection-background-color: rgba(9,105,218,0.2);
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #f6f8fa;
}

QTableWidget::item:selected {
    background-color: rgba(9,105,218,0.15);
}

QHeaderView::section {
    background: #f6f8fa;
    color: #656d76;
    border: none;
    border-bottom: 1px solid #d0d7de;
    padding: 8px;
    font-weight: bold;
}

/* ── Tool Tips ──────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1f2328;
    color: #ffffff;
    border: 1px solid #0969da;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

/* ── Message Box ────────────────────────────────────────────────────────── */
QMessageBox {
    background-color: #ffffff;
}

QMessageBox QLabel {
    color: #1f2328;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a7f37, stop:1 #2da44e);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2da44e, stop:1 #3fb950);
}
"""
