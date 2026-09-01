from __future__ import annotations

import math
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSplitter, QTextBrowser,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF, QTimer
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QPaintEvent,
)

import networkx as nx

from app.graph.graph_builder import build_document_graph, get_graph_stats

import logging

logger = logging.getLogger(__name__)


# ── Colors ────────────────────────────────────────────────────────────────────

NODE_COLORS = {
    ".pdf": (78, 130, 250),
    ".docx": (78, 130, 250),
    ".doc": (78, 130, 250),
    ".txt": (120, 200, 120),
    ".md": (120, 200, 120),
    ".py": (100, 220, 100),
    ".js": (250, 210, 80),
    ".ts": (100, 180, 250),
    ".json": (230, 160, 80),
    ".yaml": (230, 160, 80),
    ".yml": (230, 160, 80),
    ".png": (230, 110, 150),
    ".jpg": (230, 110, 150),
    "entity": (180, 130, 220),
}
DEFAULT_COLOR = (140, 140, 160)

EDGE_COLORS = {
    "entity": QColor(180, 130, 220, 80),
    "shared_entities": QColor(78, 130, 250, 100),
}
DEFAULT_EDGE_COLOR = QColor(100, 100, 120, 50)


class GraphCanvas(QWidget):
    """Optimized graph canvas with cached rendering."""

    node_clicked = Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[nx.Graph] = None
        self.pos: dict = {}
        self._node_screen: dict[str, tuple[float, float, float]] = {}  # id -> (x, y, radius)

        self._hovered_node: str | None = None
        self._selected_node: str | None = None
        self._dragging = False
        self._drag_node: str | None = None
        self._offset = QPointF(0.0, 0.0)
        self._zoom = 1.0
        self._pan_start: QPointF | None = None

        # Caching
        self._bg_cache: QPixmap | None = None
        self._bg_cache_size: tuple = (0, 0)
        self._needs_redraw = True

        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

        # Update timer for smooth rendering
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(16)  # ~60fps
        self._update_timer.timeout.connect(self.update)

    def set_graph(self, graph: nx.Graph):
        self.graph = graph
        self._calculate_layout()
        self._hovered_node = None
        self._selected_node = None
        self._needs_redraw = True
        self._bg_cache = None
        self.update()

    def _calculate_layout(self):
        if self.graph is None or self.graph.number_of_nodes() == 0:
            self.pos = {}
            return
        try:
            if self.graph.number_of_nodes() > 1:
                self.pos = nx.kamada_kawai_layout(self.graph, scale=2.0)
            else:
                self.pos = {list(self.graph.nodes())[0]: (0.0, 0.0)}
        except Exception:
            self.pos = nx.spring_layout(self.graph, k=2.0, iterations=30, seed=42)

    def _to_screen(self, pos, w, h):
        cx, cy = w / 2, h / 2
        scale = min(w, h) * 0.35 * self._zoom
        x = cx + pos[0] * scale + self._offset.x()
        y = cy + pos[1] * scale + self._offset.y()
        return x, y

    def _update_node_positions(self):
        """Pre-calculate all node screen positions."""
        w, h = self.width(), self.height()
        self._node_screen.clear()

        if self.graph is None:
            return

        for node_id, data in self.graph.nodes(data=True):
            if node_id not in self.pos:
                continue
            x, y = self._to_screen(self.pos[node_id], w, h)
            base_size = data.get("size", 10) * self._zoom
            if node_id == self._selected_node:
                size = base_size * 1.3
            elif node_id == self._hovered_node:
                size = base_size * 1.2
            else:
                size = base_size
            self._node_screen[node_id] = (x, y, size)

    def _draw_background(self, w: int, h: int) -> QPixmap:
        """Cache background drawing."""
        if self._bg_cache and self._bg_cache_size == (w, h):
            return self._bg_cache

        pixmap = QPixmap(w, h)
        pixmap.fill(QColor(15, 15, 26))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Simple grid
        painter.setPen(QPen(QColor(25, 25, 45), 1))
        grid_size = 50
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)

        painter.end()

        self._bg_cache = pixmap
        self._bg_cache_size = (w, h)
        return pixmap

    def paintEvent(self, event: QPaintEvent):
        if self.graph is None:
            return

        w, h = self.width(), self.height()

        # Update node positions if needed
        if self._needs_redraw or not self._node_screen:
            self._update_node_positions()
            self._needs_redraw = False

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Draw cached background
        bg = self._draw_background(w, h)
        painter.drawPixmap(0, 0, bg)

        # ── Draw edges (simple lines, no gradients) ────────────────────────
        for u, v, data in self.graph.edges(data=True):
            if u not in self._node_screen or v not in self._node_screen:
                continue

            x1, y1, _ = self._node_screen[u]
            x2, y2, _ = self._node_screen[v]

            edge_type = data.get("edge_type", "")
            color = EDGE_COLORS.get(edge_type, DEFAULT_EDGE_COLOR)

            painter.setPen(QPen(color, 1))
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # ── Draw nodes (solid circles, no gradients) ───────────────────────
        for node_id, (x, y, size) in self._node_screen.items():
            data = self.graph.nodes[node_id]
            ext = data.get("extension", "")
            node_type = data.get("node_type", "")

            # Get color
            if node_type == "entity":
                rgb = NODE_COLORS.get("entity", DEFAULT_COLOR)
            else:
                rgb = NODE_COLORS.get(ext, DEFAULT_COLOR)

            # Highlight
            if node_id == self._selected_node:
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            elif node_id == self._hovered_node:
                painter.setPen(QPen(QColor(200, 200, 200), 1.5))
            else:
                painter.setPen(QPen(QColor(40, 40, 60), 1))

            r, g, b = rgb
            painter.setBrush(QBrush(QColor(r, g, b)))

            rect = QRectF(x - size, y - size, size * 2, size * 2)
            painter.drawEllipse(rect)

            # Label (only if zoomed enough)
            if self._zoom > 0.5:
                label = data.get("label", "")
                if label:
                    font = QFont("Segoe UI", max(6, int(8 * self._zoom)))
                    if node_id == self._selected_node:
                        font.setBold(True)
                    painter.setFont(font)
                    painter.setPen(QColor(200, 200, 210))
                    text_rect = QRectF(x - 60, y + size + 3, 120, 16)
                    painter.drawText(text_rect, Qt.AlignHCenter | Qt.AlignTop, label)

        painter.end()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_node:
            w, h = self.width(), self.height()
            scale = min(w, h) * 0.35 * self._zoom
            new_x = (event.position().x() - w / 2 - self._offset.x()) / scale
            new_y = (event.position().y() - h / 2 - self._offset.y()) / scale
            self.pos[self._drag_node] = (new_x, new_y)
            self._needs_redraw = True
            self._schedule_update()
        elif self._pan_start:
            dx = event.position().x() - self._pan_start.x()
            dy = event.position().y() - self._pan_start.y()
            self._offset += QPointF(dx, dy)
            self._pan_start = event.position()
            self._needs_redraw = True
            self._bg_cache = None  # Background moved
            self._schedule_update()
        else:
            node = self._get_node_at(event.position().x(), event.position().y())
            if node != self._hovered_node:
                self._hovered_node = node
                self._needs_redraw = True
                self._schedule_update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            node = self._get_node_at(event.position().x(), event.position().y())
            if node:
                self._dragging = True
                self._drag_node = node
                self._selected_node = node
                self.node_clicked.emit(node, self.graph.nodes[node])
                self._needs_redraw = True
                self._schedule_update()
            else:
                self._pan_start = event.position()
        elif event.button() == Qt.RightButton:
            self._selected_node = None
            self._needs_redraw = True
            self._schedule_update()

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
        self._needs_redraw = True
        self._bg_cache = None
        self._schedule_update()

    def _schedule_update(self):
        if not self._update_timer.isActive():
            self._update_timer.start()

    def _get_node_at(self, x: float, y: float) -> str | None:
        for node_id, (nx, ny, nr) in self._node_screen.items():
            dx = x - nx
            dy = y - ny
            if dx * dx + dy * dy <= (nr + 4) ** 2:  # Small tolerance
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
        self.setFixedWidth(280)
        self.setStyleSheet("""
            QFrame {
                background: rgba(18,18,42,0.9);
                border-left: 1px solid #2a2a4a;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.title_label = QLabel("Node Details")
        self.title_label.setStyleSheet("""
            font-weight: bold;
            color: #7aa2f7;
            font-size: 14px;
            padding-bottom: 6px;
            border-bottom: 1px solid #2a2a4a;
        """)
        layout.addWidget(self.title_label)

        self.info_label = QLabel("Click a node")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #8888aa; font-size: 12px;")
        layout.addWidget(self.info_label)

        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        self.details_browser.setStyleSheet("""
            QTextBrowser {
                background: transparent;
                border: none;
                color: #e0e0f0;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.details_browser)

    def show_node(self, details: dict):
        if not details:
            self.info_label.setText("No node selected")
            self.details_browser.setHtml("")
            return

        node_type = details.get("node_type", "")
        label = details.get("label", "")
        ext = details.get("extension", "")

        info_parts = [f"<b style='color:#7aa2f7; font-size:13px;'>{label}</b>"]
        if node_type == "document":
            info_parts.append(f"<span style='color:#888;'>Type: File ({ext})</span>")
        elif node_type == "entity":
            info_parts.append("<span style='color:#bb9af7;'>Type: Entity</span>")

        neighbors = details.get("neighbors", [])
        info_parts.append(f"<span style='color:#888;'>Connections: {len(neighbors)}</span>")

        self.info_label.setText("<br>".join(info_parts))

        html_parts = []

        if neighbors:
            html_parts.append("<b style='color:#7aa2f7;'>Connected Nodes:</b><br><br>")
            for n in neighbors[:12]:
                ntype = "Entity" if n["type"] == "entity" else "File"
                color = "#bb9af7" if n["type"] == "entity" else "#9ece6a"
                html_parts.append(
                    f"<span style='color:{color};'>●</span> "
                    f"{n['label']} <span style='color:#666;'>({ntype})</span><br>"
                )

        chunks = details.get("chunks", [])
        if chunks:
            html_parts.append("<br><b style='color:#7aa2f7;'>Content:</b><br><br>")
            for i, chunk in enumerate(chunks, 1):
                page = f" (p.{chunk['page']})" if chunk.get("page") else ""
                html_parts.append(
                    f"<div style='background:rgba(122,162,247,0.1); padding:8px; "
                    f"margin:4px 0; border-radius:6px; border-left:3px solid #7aa2f7;'>"
                    f"<b style='color:#7aa2f7;'>[{i}]{page}</b><br>"
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
        self.stats_label.setStyleSheet("color: #8888aa; font-size: 12px;")
        header.addWidget(self.stats_label)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("primaryBtn")
        refresh_btn.setCursor(Qt.PointingHandCursor)
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
                f"{stats['documents']} files | {stats['entities']} entities | "
                f"{stats['edges']} edges"
            )
        except Exception as e:
            logger.error("Failed to load graph: %s", e)
            self.stats_label.setText(f"Error: {e}")

    def _on_node_clicked(self, node_id: str, node_data: dict):
        details = self.canvas.get_node_details(node_id)
        self.detail_panel.show_node(details)
