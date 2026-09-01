from __future__ import annotations

DARK_THEME = """
/* ── Global ─────────────────────────────────────────────────────────────── */
QMainWindow, QWidget {
    background-color: #0f0f1a;
    color: #e0e0f0;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Sidebar ────────────────────────────────────────────────────────────── */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #12122a, stop:0.5 #151530, stop:1 #0d0d1f);
    border-right: 1px solid #2a2a4a;
    min-width: 220px;
    max-width: 220px;
}

#sidebar QPushButton {
    background: transparent;
    color: #8888aa;
    border: none;
    border-radius: 12px;
    padding: 12px 18px;
    text-align: left;
    font-size: 13px;
    margin: 2px 8px;
}

#sidebar QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(122,162,247,0.15), stop:1 rgba(122,162,247,0.05));
    color: #c0c0e0;
}

#sidebar QPushButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7aa2f7, stop:1 #5a8af7);
    color: #ffffff;
    font-weight: bold;
    border-radius: 12px;
}

/* ── Search Input ───────────────────────────────────────────────────────── */
QLineEdit#searchInput {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a1a35, stop:1 #1e1e3a);
    border: 2px solid #2a2a50;
    border-radius: 14px;
    padding: 14px 20px;
    font-size: 15px;
    color: #e0e0f0;
    selection-background-color: #7aa2f7;
}

QLineEdit#searchInput:focus {
    border-color: #7aa2f7;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1e1e40, stop:1 #22224a);
}

/* ── Ask Input ──────────────────────────────────────────────────────────── */
QLineEdit#askInput {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a1a35, stop:1 #1e1e3a);
    border: 2px solid #2a2a50;
    border-radius: 14px;
    padding: 16px 22px;
    font-size: 15px;
    color: #e0e0f0;
}

QLineEdit#askInput:focus {
    border-color: #bb9af7;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1e1e40, stop:1 #22224a);
}

/* ── Primary Button ─────────────────────────────────────────────────────── */
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7aa2f7, stop:1 #5a8af7);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #89b4fa, stop:1 #6a9af7);
}

QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6a9af7, stop:1 #4a7af7);
}

QPushButton#primaryBtn:disabled {
    background: #333355;
    color: #666688;
}

/* ── Danger Button ──────────────────────────────────────────────────────── */
QPushButton#dangerBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f7768e, stop:1 #e05575);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#dangerBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff8aa0, stop:1 #f06585);
}

/* ── Warning Button ─────────────────────────────────────────────────────── */
QPushButton#warningBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ff9e64, stop:1 #e08850);
    color: #1a1b26;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#warningBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ffaa75, stop:1 #e09560);
}

/* ── Success Button ─────────────────────────────────────────────────────── */
QPushButton#successBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9ece6a, stop:1 #80b855);
    color: #1a1b26;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: bold;
}

QPushButton#successBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #aed07a, stop:1 #90c865);
}

/* ── Result Cards ───────────────────────────────────────────────────────── */
QFrame#resultCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a35, stop:1 #1e1e3a);
    border: 1px solid #2a2a50;
    border-radius: 14px;
    padding: 18px;
}

QFrame#resultCard:hover {
    border-color: #7aa2f7;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e1e40, stop:1 #22224a);
}

/* ── Answer Card ────────────────────────────────────────────────────────── */
QFrame#answerCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1535, stop:1 #1e1840);
    border: 1px solid #bb9af7;
    border-radius: 14px;
    padding: 22px;
}

/* ── Labels ─────────────────────────────────────────────────────────────── */
QLabel#titleLabel {
    font-size: 24px;
    font-weight: bold;
    color: #7aa2f7;
}

QLabel#subtitleLabel {
    font-size: 13px;
    color: #8888aa;
}

QLabel#sourceLabel {
    font-size: 11px;
    color: #9ece6a;
    background: rgba(158, 206, 106, 0.15);
    border-radius: 6px;
    padding: 3px 8px;
}

QLabel#scoreLabel {
    font-size: 12px;
    color: #e0af68;
    font-weight: bold;
}

/* ── Scroll Area ────────────────────────────────────────────────────────── */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: #0f0f1a;
    width: 10px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a3a5a, stop:1 #2a2a4a);
    border-radius: 5px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #5a5a7a, stop:1 #4a4a6a);
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ── Text Browser ───────────────────────────────────────────────────────── */
QTextBrowser {
    background-color: #12122a;
    color: #e0e0f0;
    border: none;
    padding: 18px;
    font-size: 14px;
    line-height: 1.6;
}

/* ── Combo Box ──────────────────────────────────────────────────────────── */
QComboBox {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a1a35, stop:1 #1e1e3a);
    border: 1px solid #2a2a50;
    border-radius: 8px;
    padding: 8px 14px;
    color: #e0e0f0;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #7aa2f7;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a35;
    color: #e0e0f0;
    selection-background-color: #7aa2f7;
    border: 1px solid #2a2a50;
    border-radius: 8px;
    padding: 4px;
}

/* ── Spin Box ───────────────────────────────────────────────────────────── */
QSpinBox {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a1a35, stop:1 #1e1e3a);
    border: 1px solid #2a2a50;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e0e0f0;
}

QSpinBox:hover {
    border-color: #7aa2f7;
}

/* ── Date Edit ──────────────────────────────────────────────────────────── */
QDateEdit {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1a1a35, stop:1 #1e1e3a);
    border: 1px solid #2a2a50;
    border-radius: 8px;
    padding: 6px 10px;
    color: #e0e0f0;
}

QDateEdit:hover {
    border-color: #7aa2f7;
}

/* ── Tab Widget ─────────────────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    background-color: #0f0f1a;
}

QTabBar::tab {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a35, stop:1 #151530);
    color: #8888aa;
    padding: 10px 24px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    margin-right: 2px;
    border: 1px solid #2a2a4a;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e1e40, stop:1 #0f0f1a);
    color: #7aa2f7;
    border-bottom: 2px solid #7aa2f7;
    font-weight: bold;
}

/* ── Status Bar ─────────────────────────────────────────────────────────── */
QStatusBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #12122a, stop:1 #0d0d1f);
    color: #8888aa;
    border-top: 1px solid #2a2a4a;
}

/* ── Progress Bar ───────────────────────────────────────────────────────── */
QProgressBar {
    background: #1a1a35;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7aa2f7, stop:0.5 #bb9af7, stop:1 #9ece6a);
    border-radius: 6px;
}

/* ── Tables ─────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #12122a;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    gridline-color: #1a1a35;
    color: #e0e0f0;
    selection-background-color: rgba(122,162,247,0.3);
}

QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #1a1a35;
}

QTableWidget::item:selected {
    background-color: rgba(122,162,247,0.2);
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a35, stop:1 #151530);
    color: #8888aa;
    border: none;
    border-bottom: 1px solid #2a2a4a;
    padding: 8px;
    font-weight: bold;
}

/* ── Tool Tips ──────────────────────────────────────────────────────────── */
QToolTip {
    background-color: #1e1e40;
    color: #e0e0f0;
    border: 1px solid #7aa2f7;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

/* ── Message Box ────────────────────────────────────────────────────────── */
QMessageBox {
    background-color: #0f0f1a;
}

QMessageBox QLabel {
    color: #e0e0f0;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7aa2f7, stop:1 #5a8af7);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    min-width: 80px;
}

QMessageBox QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #89b4fa, stop:1 #6a9af7);
}
"""
