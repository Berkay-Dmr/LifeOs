from __future__ import annotations

import math
import numpy as np
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSplitter, QTextBrowser,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

import networkx as nx

from app.graph.graph_builder import build_document_graph, get_graph_stats

import logging

logger = logging.getLogger(__name__)


class GraphCanvas(QWidget):
    """Custom canvas for drawing the knowledge graph."""

    node_clicked = Signal(str, dict)  # node_id, node_data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[nx.Graph] = None
        self.pos: dict = {}  # node_id -> (x, y)
        self._node_rects: dict[str, QRectF] = {}
        self._hovered_node: str | None = None
        self._selected_node: str | None = None
        self._dragging = False
        self._drag_node: str | None = None
        self._offset = (0.0, 0.0)
        self._zoom = 1.0
        self._pan_start = None

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
        """Calculate node positions using spring layout."""
        if self.graph is None or self.graph.number_of_nodes() == 0:
            self.pos = {}
            return

        # Use spring layout
        self.pos = nx.spring_layout(
            self.graph,
            k=2.0 / math.sqrt(self.graph.number_of_nodes()),
            iterations=50,
            seed=42,
        )

    def paintEvent(self, event):
        if self.graph is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(24, 24, 37))

        # Transform coordinates
        cx, cy = w / 2, h / 2
        scale = min(w, h) * 0.4 * self._zoom

        def to_screen(pos):
            x = cx + pos[0] * scale + self._offset[0]
            y = cy + pos[1] * scale + self._offset[1]
            return x, y

        # Draw edges
        for u, v, data in self.graph.edges(data=True):
            if u in self.pos and v in self.pos:
                x1, y1 = to_screen(self.pos[u])
                x2, y2 = to_screen(self.pos[v])

                edge_type = data.get("edge_type", "")
                if edge_type == "entity":
                    color = QColor(180, 130, 180, 80)  # Purple, semi-transparent
                    pen = QPen(color, 1, Qt.DashLine)
                else:
                    color = QColor(122, 162, 247, 100)  # Blue, semi-transparent
                    pen = QPen(color, 1.5)

                painter.setPen(pen)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw nodes
        self._node_rects.clear()
        for node_id, data in self.graph.nodes(data=True):
            if node_id not in self.pos:
                continue

            x, y = to_screen(self.pos[node_id])
            node_size = data.get("size", 10) * self._zoom
            color = data.get("color", (0.55, 0.55, 0.55))

            # Highlight selected/hovered
            if node_id == self._selected_node:
                node_size *= 1.3
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            elif node_id == self._hovered_node:
                node_size *= 1.2
                painter.setPen(QPen(QColor(200, 200, 200), 1.5))
            else:
                painter.setPen(QPen(QColor(60, 60, 80), 1))

            r, g, b = [int(c * 255) for c in color]
            painter.setBrush(QBrush(QColor(r, g, b)))

            rect = QRectF(x - node_size, y - node_size, node_size * 2, node_size * 2)
            self._node_rects[node_id] = rect
            painter.drawEllipse(rect)

            # Draw label
            label = data.get("label", "")
            if label and self._zoom > 0.5:
                font = QFont("Segoe UI", max(7, int(9 * self._zoom)))
                painter.setFont(font)
                painter.setPen(QColor(200, 200, 210))
                painter.drawText(int(x), int(y + node_size + 12), label)

        painter.end()

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_node:
            # Move node
            self.pos[self._drag_node] = (
                (event.position().x() - self.width() / 2 - self._offset[0]) /
                (self.width() / 2 * self._zoom),
                (event.position().y() - self.height() / 2 - self._offset[1]) /
                (self.height() / 2 * self._zoom),
            )
            self.update()
        elif self._pan_start:
            dx = event.position().x() - self._pan_start[0]
            dy = event.position().y() - self._pan_start[1]
            self._offset = (self._offset[0] + dx, self._offset[1] + dy)
            self._pan_start = (event.position().x(), event.position().y())
            self.update()
        else:
            # Hover detection
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
                self._pan_start = (event.position().x(), event.position().y())
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
        """Get detailed info about a node."""
        if self.graph is None or node_id not in self.graph.nodes:
            return {}

        data = self.graph.nodes[node_id]
        details = {"id": node_id, **data}

        # Get neighbors
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

        # Get chunks if it's a document
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
        self.setStyleSheet("QFrame { background: #1a1a2e; border-left: 1px solid #333; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.title_label = QLabel("Düğüm Detayları")
        self.title_label.setStyleSheet("font-weight: bold; color: #7aa2f7; font-size: 14px;")
        layout.addWidget(self.title_label)

        self.info_label = QLabel("Bir düğüme tıklayın")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(self.info_label)

        self.details_browser = QTextBrowser()
        self.details_browser.setOpenExternalLinks(True)
        self.details_browser.setStyleSheet("background: transparent; border: none; color: #ccc; font-size: 12px;")
        layout.addWidget(self.details_browser)

    def show_node(self, details: dict):
        if not details:
            self.info_label.setText("Düğüm seçilmedi")
            self.details_browser.setHtml("")
            return

        node_type = details.get("node_type", "")
        label = details.get("label", "")
        ext = details.get("extension", "")

        info_parts = [f"<b>{label}</b>"]
        if node_type == "document":
            info_parts.append(f"Tur: Dosya ({ext})")
            if "size" in details:
                info_parts.append(f"Boyut: {details['size']:,} byte")
        elif node_type == "entity":
            info_parts.append("Tur: Entity (baglanti)")

        neighbors = details.get("neighbors", [])
        info_parts.append(f"Baglanti: {len(neighbors)}")

        self.info_label.setText("<br>".join(info_parts))

        # Build details HTML
        html_parts = []

        # Neighbors
        if neighbors:
            html_parts.append("<b>Bagli Dugumler:</b><br>")
            for n in neighbors[:10]:
                ntype = "Entity" if n["type"] == "entity" else "Dosya"
                html_parts.append(f"  - {n['label']} ({ntype})<br>")

        # Chunks
        chunks = details.get("chunks", [])
        if chunks:
            html_parts.append("<br><b>Icerik (Chunk'lari):</b><br>")
            for i, chunk in enumerate(chunks, 1):
                page = f" (sayfa {chunk['page']})" if chunk.get("page") else ""
                section = f" - {chunk['section']}" if chunk.get("section") else ""
                html_parts.append(f"<b>[{i}]{page}{section}</b><br>")
                html_parts.append(f"{chunk['text']}<br><br>")

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

        # Main content: canvas + detail panel
        splitter = QSplitter(Qt.Horizontal)

        # Graph canvas
        self.canvas = GraphCanvas()
        self.canvas.node_clicked.connect(self._on_node_clicked)
        splitter.addWidget(self.canvas)

        # Detail panel
        self.detail_panel = NodeDetailPanel()
        splitter.addWidget(self.detail_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter)

    def _load_graph(self):
        """Load and display the graph."""
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
