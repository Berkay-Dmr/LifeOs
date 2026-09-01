from __future__ import annotations

import networkx as nx
from datetime import datetime

from app.database.sqlite import get_connection
from app.config.settings import get_settings

import logging

logger = logging.getLogger(__name__)

# File type colors (RGB tuples, 0-1 range)
FILE_TYPE_COLORS = {
    ".pdf": (0.48, 0.63, 0.97),    # Blue
    ".docx": (0.48, 0.63, 0.97),
    ".doc": (0.48, 0.63, 0.97),
    ".txt": (0.61, 0.78, 0.61),    # Green-ish
    ".md": (0.61, 0.78, 0.61),
    ".py": (0.61, 0.80, 0.42),     # Green
    ".js": (0.97, 0.80, 0.30),     # Yellow
    ".ts": (0.40, 0.65, 0.90),     # Light blue
    ".json": (0.90, 0.60, 0.30),   # Orange
    ".yaml": (0.90, 0.60, 0.30),
    ".yml": (0.90, 0.60, 0.30),
    ".png": (0.90, 0.45, 0.60),    # Pink
    ".jpg": (0.90, 0.45, 0.60),
    ".jpeg": (0.90, 0.45, 0.60),
}
DEFAULT_COLOR = (0.55, 0.55, 0.55)  # Gray


def build_document_graph() -> nx.Graph:
    """Build a graph where nodes are documents and edges are connections."""
    G = nx.Graph()

    settings = get_settings()

    with get_connection() as conn:
        # Get all documents
        docs = conn.execute(
            "SELECT id, path, name, extension, size, modified_at FROM documents"
        ).fetchall()

        # Add document nodes
        doc_map = {}
        for doc in docs:
            doc_id = doc["id"]
            doc_map[doc_id] = {
                "path": doc["path"],
                "name": doc["name"],
                "extension": doc["extension"],
                "size": doc["size"],
                "modified_at": doc["modified_at"],
            }
            G.add_node(
                doc_id,
                label=doc["name"],
                node_type="document",
                extension=doc["extension"],
                color=FILE_TYPE_COLORS.get(doc["extension"], DEFAULT_COLOR),
            )

        # Get chunks per document for size info
        chunk_counts = {}
        rows = conn.execute(
            "SELECT document_id, COUNT(*) as cnt FROM chunks GROUP BY document_id"
        ).fetchall()
        for row in rows:
            chunk_counts[row["document_id"]] = row["cnt"]

        # Update node sizes based on chunk count
        for doc_id in G.nodes:
            count = chunk_counts.get(doc_id, 1)
            G.nodes[doc_id]["size"] = max(8, min(20, count * 2))

        # Get entities per document
        doc_entities: dict[str, set[str]] = {}
        for doc_id in doc_map:
            doc_entities[doc_id] = set()

        # Extract entities from chunks
        rows = conn.execute(
            "SELECT document_id, text FROM chunks LIMIT 500"
        ).fetchall()
        for row in rows:
            doc_id = row["document_id"]
            text = row["text"].lower()
            # Simple entity extraction
            entities = _extract_simple_entities(text)
            if doc_id in doc_entities:
                doc_entities[doc_id].update(entities)

        # Add entity nodes and edges
        all_entities: dict[str, set[str]] = {}  # entity -> set of doc_ids
        for doc_id, entities in doc_entities.items():
            for entity in entities:
                if entity not in all_entities:
                    all_entities[entity] = set()
                all_entities[entity].add(doc_id)

        # Add entity nodes (only if they connect 2+ documents)
        for entity, connected_docs in all_entities.items():
            if len(connected_docs) >= 2:
                G.add_node(
                    f"entity_{entity}",
                    label=entity,
                    node_type="entity",
                    color=(0.85, 0.50, 0.70),  # Purple-ish
                    size=10,
                )
                for doc_id in connected_docs:
                    G.add_edge(
                        f"entity_{entity}",
                        doc_id,
                        edge_type="entity",
                        weight=0.6,
                    )

        # Add document-to-document edges based on shared entities
        doc_pairs: dict[tuple, int] = {}
        for entity, connected_docs in all_entities.items():
            docs_list = list(connected_docs)
            for i in range(len(docs_list)):
                for j in range(i + 1, len(docs_list)):
                    pair = tuple(sorted([docs_list[i], docs_list[j]]))
                    doc_pairs[pair] = doc_pairs.get(pair, 0) + 1

        for (doc1, doc2), weight in doc_pairs.items():
            if weight >= 2:  # At least 2 shared entities
                G.add_edge(
                    doc1, doc2,
                    edge_type="shared_entities",
                    weight=min(weight / 5.0, 1.0),
                )

    logger.info("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def _extract_simple_entities(text: str) -> set[str]:
    """Extract simple entities from text."""
    entities = set()

    # Technology keywords
    tech_keywords = [
        "python", "javascript", "typescript", "java", "c#", "c++", "go", "rust",
        "react", "node.js", "django", "flask", "fastapi", "vue", "angular",
        "postgresql", "mysql", "redis", "mongodb", "sqlite",
        "docker", "kubernetes", "aws", "azure", "gcp",
        "git", "github", "gitlab", "linux", "windows",
        "pytorch", "tensorflow", "scikit-learn", "pandas", "numpy",
        "html", "css", "sass", "tailwind",
    ]

    # Domain keywords
    domain_keywords = [
        "sgk", "sigorta", "prim", "borc", "emekli",
        "ogrenci", "universite", "fakulte", "bolum",
        "transkript", "diploma", "mezun",
        "belge", "kimlik", "adli", "sicil",
        "burs", "kredi", "kyk", "yurt",
    ]

    text_lower = text.lower()
    for kw in tech_keywords + domain_keywords:
        if kw in text_lower:
            entities.add(kw)

    return entities


def get_graph_stats(G: nx.Graph) -> dict:
    """Get statistics about the graph."""
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "documents": sum(1 for n, d in G.nodes(data=True) if d.get("node_type") == "document"),
        "entities": sum(1 for n, d in G.nodes(data=True) if d.get("node_type") == "entity"),
        "connected_components": nx.number_connected_components(G),
    }
