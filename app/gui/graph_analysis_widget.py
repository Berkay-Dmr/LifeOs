from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QGroupBox,
    QTextBrowser,
)
from PySide6.QtCore import Qt, QThread, Signal

import logging

logger = logging.getLogger(__name__)


class GraphAnalysisWorker(QThread):
    """Worker thread for graph analysis."""
    finished = Signal(dict)
    error = Signal(str)

    def run(self):
        try:
            from app.graph.graph_builder import build_document_graph, get_graph_stats, get_centrality, find_communities
            G = build_document_graph()
            stats = get_graph_stats(G)
            centrality = get_centrality(G, top=15)
            communities = find_communities(G)
            self.finished.emit({
                "stats": stats,
                "centrality": centrality,
                "communities": communities,
                "graph": G,
            })
        except Exception as e:
            self.error.emit(str(e))


class GraphAnalysisWidget(QWidget):
    """Graph analysis widget with centrality and communities."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._graph = None
        self._init_ui()
        self._load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Title
        title = QLabel("Graph Analysis")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.stat_cards = {}
        for name, color in [("Nodes", "88,148,253"), ("Edges", "163,113,247"),
                            ("Documents", "63,185,80"), ("Entities", "227,179,65")]:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba({color},0.1);
                    border: 1px solid rgba({color},0.3);
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)

            value = QLabel("0")
            value.setStyleSheet(f"font-size: 24px; font-weight: bold; color: rgb({color});")
            value.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(value)

            label = QLabel(name)
            label.setStyleSheet("color: #8b949e; font-size: 11px;")
            label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(label)

            self.stat_cards[name] = value
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # Path finder
        path_group = QGroupBox("Find Path")
        path_layout = QHBoxLayout(path_group)

        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Source node...")
        path_layout.addWidget(self.source_input)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Target node...")
        path_layout.addWidget(self.target_input)

        self.find_path_btn = QPushButton("Find Path")
        self.find_path_btn.clicked.connect(self._find_path)
        path_layout.addWidget(self.find_path_btn)

        layout.addWidget(path_group)

        # Path result
        self.path_result = QTextBrowser()
        self.path_result.setMaximumHeight(100)
        self.path_result.setStyleSheet("background: rgba(22,27,34,0.8); border: 1px solid #30363d; border-radius: 8px; padding: 8px;")
        layout.addWidget(self.path_result)

        # Centrality table
        centrality_group = QGroupBox("Node Centrality (Top 15)")
        centrality_layout = QVBoxLayout(centrality_group)

        self.centrality_table = QTableWidget()
        self.centrality_table.setColumnCount(4)
        self.centrality_table.setHorizontalHeaderLabels(["Node", "Type", "Centrality", "Connections"])
        self.centrality_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.centrality_table.setEditTriggers(QTableWidget.NoEditTriggers)
        centrality_layout.addWidget(self.centrality_table)

        layout.addWidget(centrality_group)

        # Communities
        communities_group = QGroupBox("Detected Communities")
        communities_layout = QVBoxLayout(communities_group)

        self.communities_text = QTextBrowser()
        self.communities_text.setStyleSheet("background: transparent; border: none;")
        communities_layout.addWidget(self.communities_text)

        layout.addWidget(communities_group)

    def _load_data(self):
        self.worker = GraphAnalysisWorker()
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_data_loaded(self, data):
        stats = data["stats"]
        centrality = data["centrality"]
        communities = data["communities"]
        self._graph = data["graph"]

        self.stat_cards["Nodes"].setText(str(stats.get("nodes", 0)))
        self.stat_cards["Edges"].setText(str(stats.get("edges", 0)))
        self.stat_cards["Documents"].setText(str(stats.get("documents", 0)))
        self.stat_cards["Entities"].setText(str(stats.get("entities", 0)))

        # Centrality table
        self.centrality_table.setRowCount(len(centrality))
        for i, node in enumerate(centrality):
            self.centrality_table.setItem(i, 0, QTableWidgetItem(node.get("label", "")[:40]))
            self.centrality_table.setItem(i, 1, QTableWidgetItem(node.get("type", "")))
            self.centrality_table.setItem(i, 2, QTableWidgetItem(f"{node.get('centrality', 0):.3f}"))
            self.centrality_table.setItem(i, 3, QTableWidgetItem(str(node.get("degree", 0))))

        # Communities
        community_html = f"<b>{len(communities)}</b> communities detected<br><br>"
        for i, community in enumerate(communities[:5], 1):
            docs = [self._graph.nodes[n].get("label", n) for n in community
                    if self._graph.nodes[n].get("node_type") == "document"][:5]
            if docs:
                community_html += f"<b>Community {i}:</b><br>"
                for doc in docs:
                    community_html += f"&nbsp;&nbsp;- {doc}<br>"
                community_html += "<br>"

        self.communities_text.setHtml(community_html)

    def _on_error(self, error):
        logger.error("Graph analysis error: %s", error)

    def _find_path(self):
        if not self._graph:
            return

        source = self.source_input.text().strip()
        target = self.target_input.text().strip()

        if not source or not target:
            self.path_result.setPlainText("Please enter both source and target.")
            return

        # Find nodes by label
        source_id = None
        target_id = None

        for node_id, data in self._graph.nodes(data=True):
            label = data.get("label", "").lower()
            if source.lower() in label and source_id is None:
                source_id = node_id
            if target.lower() in label and target_id is None:
                target_id = node_id

        if not source_id:
            self.path_result.setPlainText(f"Source '{source}' not found.")
            return
        if not target_id:
            self.path_result.setPlainText(f"Target '{target}' not found.")
            return

        try:
            import networkx as nx
            path = nx.shortest_path(self._graph, source_id, target_id)
            path_text = f"Path ({len(path)} steps):\n"
            for i, node_id in enumerate(path):
                label = self._graph.nodes[node_id].get("label", node_id)
                if i < len(path) - 1:
                    path_text += f"  {label} →\n"
                else:
                    path_text += f"  {label}"
            self.path_result.setPlainText(path_text)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            self.path_result.setPlainText("No path found between these nodes.")
