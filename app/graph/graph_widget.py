from __future__ import annotations

import math
import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSplitter, QTextBrowser,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QRadialGradient, QConicalGradient, QPainterPath, QPolygonF,
)

import networkx as nx

from app.graph.graph_builder import build_document_graph, get_graph_stats

import logging

logger = logging.getLogger(__name__)


# ── Color Palettes ──────────────────────────────────────────────────────────

NODE_COLORS = {
    ".pdf": {"main": (78, 130, 250), "glow": (78, 130, 250, 60)},      # Blue
    ".docx": {"main": (78, 130, 250), "glow": (78, 130, 250, 60)},
    ".doc": {"main": (78, 130, 250), "glow": (78, 130, 250, 60)},
    ".txt": {"main": (120, 200, 120), "glow": (120, 200, 120, 60)},    # Green
    ".md": {"main": (120, 200, 120), "glow": (120, 200, 120, 60)},
    ".py": {"main": (100, 220, 100), "glow": (100, 220, 100, 60)},     # Bright green
    ".js": {"main": (250, 210, 80), "glow": (250, 210, 80, 60)},       # Yellow
    ".ts": {"main": (100, 180, 250), "glow": (100, 180, 250, 60)},     # Light blue
    ".json": {"main": (230, 160, 80), "glow": (230, 160, 80, 60)},     # Orange
    ".yaml": {"main": (230, 160, 80), "glow": (230, 160, 80, 60)},
    ".yml": {"main": (230, 160, 80), "glow": (230, 160, 80, 60)},
    ".png": {"main": (230, 110, 150), "glow": (230, 110, 150, 60)},    # Pink
    ".jpg": {"main": (230, 110, 150), "glow": (230, 110, 150, 60)},
    ".jpeg": {"main": (230, 110, 150), "glow": (230, 110, 150, 60)},
    "entity": {"main": (180, 130, 220), "glow": (180, 130, 220, 60)},  # Purple
}
DEFAULT_NODE_COLOR = {"main": (140, 140, 160), "glow": (140, 140, 160, 60)}

EDGE_COLORS = {
    "entity": QColor(180, 130, 220, 120),      # Purple
    "shared_entities": QColor(78, 130, 250, 140),  # Blue
    "similarity": QColor(100, 200, 180, 120),   # Teal
    "folder": QColor(200, 180, 100, 100),       # Gold
}
DEFAULT_EDGE_COLOR = QColor(100, 100, 120, 80)


class GraphCanvas(QWidget):
    """Custom canvas for drawing the knowledge graph with visual effects."""

    node_clicked = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[nx.Graph] = None
        self.pos: dict = {}
        self._node_rects: dict[str, QRectF] = {}
        self._hovered_node: str | None = None
        self._selected_node: str | None = None
        self._dragging = False
        self._drag_node: str | None = None
        self._offset = QPointF(0.0, 0.0)
        self._zoom = 1.0
        self._pan_start: QPointF | None = None
        self._anim_tick = 0

        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    def set_graph(self, graph: nx.Graph):
        self.graph = graph
        self._calculate_layout()
        self._hovered_node = None
        self._selected_node = None
        self.update()

    def _calculate_layout(self):
        """Calculate node positions using Kamada-Kawai layout for better spacing."""
        if self.graph is None or self.graph.number_of_nodes() == 0:
            self.pos = {}
            return

        try:
            if self.graph.number_of_nodes() > 1:
                self.pos = nx.kamada_kawai_layout(self.graph, scale=2.0)
            else:
                self.pos = {list(self.graph.nodes())[0]: (0.0, 0.0)}
        except Exception:
            self.pos = nx.spring_layout(self.graph, k=2.0, iterations=50, seed=42)

    def _to_screen(self, pos, w, h):
        """Convert graph coordinates to screen coordinates."""
        cx, cy = w / 2, h / 2
        scale = min(w, h) * 0.35 * self._zoom
        x = cx + pos[0] * scale + self._offset.x()
        y = cy + pos[1] * scale + self._offset.y()
        return x, y

    def paintEvent(self, event):
        if self.graph is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # ── Background with grid pattern ────────────────────────────────────
        bg = QColor(18, 18, 32)
        painter.fillRect(0, 0, w, h, bg)

        # Draw subtle grid
        grid_pen = QPen(QColor(30, 30, 50), 1)
        painter.setPen(grid_pen)
        grid_size = 40
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)

        # Draw radial gradient background
        grad = QRadialGradient(w / 2, h / 2, min(w, h) * 0.6)
        grad.setColorAt(0, QColor(25, 25, 45, 40))
        grad.setColorAt(1, QColor(18, 18, 32, 0))
        painter.fillRect(0, 0, w, h, QBrush(grad))

        # ── Draw edges with glow ────────────────────────────────────────────
        for u, v, data in self.graph.edges(data=True):
            if u in self.pos and v in self.pos:
                x1, y1 = self._to_screen(self.pos[u], w, h)
                x2, y2 = self._to_screen(self.pos[v], w, h)

                edge_type = data.get("edge_type", "")
                base_color = EDGE_COLORS.get(edge_type, DEFAULT_EDGE_COLOR)

                # Edge glow (wider, transparent)
                glow_pen = QPen(QColor(base_color.red(), base_color.green(),
                                       base_color.blue(), 40), 6)
                painter.setPen(glow_pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

                # Main edge
                painter.setPen(QPen(base_color, 1.5))
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # ── Draw nodes ──────────────────────────────────────────────────────
        self._node_rects.clear()
        for node_id, data in self.graph.nodes(data=True):
            if node_id not in self.pos:
                continue

            x, y = self._to_screen(self.pos[node_id], w, h)
            base_size = data.get("size", 10) * self._zoom
            ext = data.get("extension", "")
            node_type = data.get("node_type", "")

            # Get colors
            if node_type == "entity":
                colors = NODE_COLORS["entity"]
            else:
                colors = NODE_COLORS.get(ext, DEFAULT_NODE_COLOR)

            main_r, main_g, main_b = colors["main"]
            glow_r, glow_g, glow_b, glow_a = colors["glow"]

            # Highlight effects
            if node_id == self._selected_node:
                size = base_size * 1.4
                glow_a = 120
            elif node_id == self._hovered_node:
                size = base_size * 1.25
                glow_a = 100
            else:
                size = base_size

            # ── Glow effect (outer ring) ────────────────────────────────────
            glow_size = size * 2.2
            glow_grad = QRadialGradient(x, y, glow_size)
            glow_grad.setColorAt(0.0, QColor(glow_r, glow_g, glow_b, glow_a))
            glow_grad.setColorAt(0.4, QColor(glow_r, glow_g, glow_b, int(glow_a * 0.4)))
            glow_grad.setColorAt(1.0, QColor(glow_r, glow_g, glow_b, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(glow_grad))
            glow_rect = QRectF(x - glow_size, y - glow_size, glow_size * 2, glow_size * 2)
            painter.drawEllipse(glow_rect)

            # ── Main node (gradient fill) ───────────────────────────────────
            node_grad = QRadialGradient(x - size * 0.3, y - size * 0.3, size * 1.5)
            node_grad.setColorAt(0.0, QColor(min(main_r + 60, 255),
                                             min(main_g + 60, 255),
                                             min(main_b + 60, 255)))
            node_grad.setColorAt(0.6, QColor(main_r, main_g, main_b))
            node_grad.setColorAt(1.0, QColor(max(main_r - 40, 0),
                                             max(main_g - 40, 0),
                                             max(main_b - 40, 0)))

            painter.setPen(QPen(QColor(255, 255, 255, 50), 1))
            painter.setBrush(QBrush(node_grad))
            node_rect = QRectF(x - size, y - size, size * 2, size * 2)
            self._node_rects[node_id] = node_rect
            painter.drawEllipse(node_rect)

            # ── Inner highlight (shine) ─────────────────────────────────────
            shine_grad = QRadialGradient(x - size * 0.25, y - size * 0.35, size * 0.6)
            shine_grad.setColorAt(0.0, QColor(255, 255, 255, 70))
            shine_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(shine_grad))
            shine_rect = QRectF(x - size * 0.6, y - size * 0.7, size * 1.2, size * 1.2)
            painter.drawEllipse(shine_rect)

            # ── Label ───────────────────────────────────────────────────────
            label = data.get("label", "")
            if label and self._zoom > 0.4:
                font = QFont("Segoe UI", max(7, int(9 * self._zoom)))
                if node_id == self._selected_node:
                    font.setBold(True)
                painter.setFont(font)
                painter.setPen(QColor(220, 220, 230))
                text_rect = QRectF(x - 80, y + size + 4, 160, 20)
                painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, label)

        painter.end()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_node:
            pos = self.pos[self._drag_node]
            w, h = self.width(), self.height()
            new_x = (event.position().x() - w / 2 - self._offset.x()) / (min(w, h) * 0.35 * self._zoom)
            new_y = (event.position().y() - h / 2 - self._offset.y()) / (min(w, h) * 0.35 * self._zoom)
            self.pos[self._drag_node] = (new_x, new_y)
            self.update()
        elif self._pan_start:
            dx = event.position().x() - self._pan_start.x()
            dy = event.position().y() - self._pan_start.y()
            self._offset += QPointF(dx, dy)
            self._pan_start = event.position()
            self.update()
        else:
            node = self._get_node_at(event.position().x(), event.position().y())
            if node != self._hovered_node:
                self._hovered_node = node
                self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            node = self._get_node_at(event.position().x(), event.position().y())
            if node:
                self._dragging = True
                self._drag_node = node
                self._selected_node = node
                self.node_clicked.emit(node, self.graph.nodes[node])
                self.update()
            else:
                self._pan_start = event.position()
        elif event.button() == Qt.RightButton:
            self._selected_node = None
            self.update()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._drag_node = None
        self._pan_start = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom = min(3.0, self._zoom * 1.1)
        else:
            self._zoom = max(0.2, self._zoom / 1.1)
        self.update()

    def _get_node_at(self, x: float, y: float) -> str | None:
        for node_id, rect in self._node_rects.items():
            if rect.contains(x, y):
                return node_id
        return None

    def get_node_details(self, node_id: str) -> dict:
        if self.graph is None or node_id not in self.graph.nodes:
            return {}

        data = self.graph.nodes[node_id]
        details = {"id": node_id, **data}

        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.edges[node_id, neighbor]
            neighbor_data = self.graph.nodes[neighbor]
            neighbors.append({
                "id": neighbor,
                "label": neighbor_data.get("label", ""),
                "type": neighbor_data.get("node_type", ""),
                "edge_type": edge_data.get("edge_type", ""),
            })
        details["neighbors"] = neighbors

        if data.get("node_type") == "document":
            from app.database.sqlite import get_connection
            with get_connection() as conn:
                chunks = conn.execute(
                    "SELECT text, page, section FROM chunks WHERE document_id = ? LIMIT 5",
                    (node_id,)
                ).fetchall()
                details["chunks"] = [
                    {"text": c["text"][:200], "page": c["page"], "section": c["section"]}
                    for c in chunks
                ]

        return details


class NodeDetailPanel(QFrame):
    """Panel showing details of a selected node."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(300)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a2e, stop:1 #16162a);
                border-left: 1px solid #333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.title_label = QLabel("Düğüm Detayları")
        self.title_label.setStyleSheet("""
            font-weight: bold;
            color: #7aa2f7;
            font-size: 14px;
            padding-bottom: 6px;
            border-bottom: 1px solid #333;
        """)
        layout.addWidget(self.title_label)

        self.info_label = QLabel("Bir düğüme tıklayın")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(self.info_label)

        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        self.details_browser.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                color: #ccc;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.details_browser)

    def show_node(self, details: dict):
        if not details:
            self.info_label.setText("Düğüm seçilmedi")
            self.details_browser.setHtml("")
            return

        node_type = details.get("node_type", "")
        label = details.get("label", "")
        ext = details.get("extension", "")

        info_parts = [f"<b style='color:#7aa2f7; font-size:13px;'>{label}</b>"]
        if node_type == "document":
            info_parts.append(f"<span style='color:#888;'>Tur: Dosya ({ext})</span>")
            if "size" in details:
                info_parts.append(f"<span style='color:#888;'>Boyut: {details['size']:,} byte</span>")
        elif node_type == "entity":
            info_parts.append("<span style='color:#b482dc;'>Tur: Entity</span>")

        neighbors = details.get("neighbors", [])
        info_parts.append(f"<span style='color:#888;'>Baglanti: {len(neighbors)}</span>")

        self.info_label.setText("<br>".join(info_parts))

        html_parts = ["<style>body{margin:0;padding:0;}</style>"]

        if neighbors:
            html_parts.append("<b style='color:#7aa2f7;'>Bagli Dugumler:</b><br><br>")
            for n in neighbors[:12]:
                ntype = "Entity" if n["type"] == "entity" else "Dosya"
                color = "#b482dc" if n["type"] == "entity" else "#78c878"
                html_parts.append(
                    f"<span style='color:{color};'>●</span> "
                    f"{n['label']} <span style='color:#666;'>({ntype})</span><br>"
                )

        chunks = details.get("chunks", [])
        if chunks:
            html_parts.append("<br><b style='color:#7aa2f7;'>Icerik (Chunk'lari):</b><br><br>")
            for i, chunk in enumerate(chunks, 1):
                page = f" (sayfa {chunk['page']})" if chunk.get("page") else ""
                section = f" — {chunk['section']}" if chunk.get("section") else ""
                html_parts.append(
                    f"<div style='background:#252540; padding:8px; margin:4px 0; border-radius:6px; "
                    f"border-left:3px solid #7aa2f7;'>"
                    f"<b style='color:#7aa2f7;'>[{i}]{page}{section}</b><br>"
                    f"<span style='color:#aaa;'>{chunk['text']}</span></div>"
                )

        self.details_browser.setHtml("".join(html_parts))


class GraphWidget(QWidget):
    """Graph view widget showing knowledge graph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_graph()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 8)

        title = QLabel("Knowledge Graph")
        title.setObjectName("titleLabel")
        header.addWidget(title)

        header.addStretch()

        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: #787c99; font-size: 12px;")
        header.addWidget(self.stats_label)

        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self._load_graph)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # Main content
        splitter = QSplitter(Qt.Horizontal)

        self.canvas = GraphCanvas()
        self.canvas.node_clicked.connect(self._on_node_clicked)
        splitter.addWidget(self.canvas)

        self.detail_panel = NodeDetailPanel()
        splitter.addWidget(self.detail_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter)

    def _load_graph(self):
        try:
            graph = build_document_graph()
            self.canvas.set_graph(graph)

            stats = get_graph_stats(graph)
            self.stats_label.setText(
                f"{stats['documents']} dosya | {stats['entities']} entity | "
                f"{stats['edges']} baglanti"
            )
        except Exception as e:
            logger.error("Failed to load graph: %s", e)
            self.stats_label.setText(f"Hata: {e}")

    def _on_node_clicked(self, node_id: str, node_data: dict):
        details = self.canvas.get_node_details(node_id)
        self.detail_panel.show_node(details)
