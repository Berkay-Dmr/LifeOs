from __future__ import annotations

import re
import math
from collections import Counter

import networkx as nx

from app.database.sqlite import get_connection
from app.config.settings import get_settings

import logging

logger = logging.getLogger(__name__)

# ── File type colors (RGB, 0-255) ────────────────────────────────────────────

FILE_TYPE_COLORS = {
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
    ".jpeg": (230, 110, 150),
    ".csv": (200, 180, 100),
    ".xlsx": (200, 180, 100),
    ".pptx": (230, 160, 100),
}
DEFAULT_COLOR = (140, 140, 160)


# ── Turkish-aware stop words ─────────────────────────────────────────────────

STOP_WORDS_TR = set([
    "bir", "bu", "da", "de", "ve", "ile", "için", "olan", "olarak",
    "den", "dan", "ne", "ya", "ki", "mi", "mı", "mu", "mü",
    "çok", "az", "daha", "en", "bile", "sadece", "gibi", "kadar",
    "sonra", "önce", "arasında", "üzerinde", "altında", "içinde",
    "ama", "fakat", "ancak", "hem", "ya", "veya", "ya da",
    "olan", "olduğu", "olduğunu", "olup", "olarak",
    "var", "yok", "bunu", "bunun", "şu", "şey", "her",
    "kendi", "benim", "senin", "onun", "bizim", "sizin", "onların",
    "ben", "sen", "o", "biz", "siz", "onlar",
    "göre", "tarafından", "neden", "nasıl", "nere", "nerede", "ne zaman",
    "ise", "değil", "dahi", "bile",
    "tüm", "tümü", "bazı", "birçok", "bir kaç", "hepsi",
    "önceki", "sonraki", "mevcut", "yeni", "eski",
])

# ── Keywords to extract as entities ───────────────────────────────────────────

ENTITY_KEYWORDS = {
    # Education
    "üniversite": "education", "fakülte": "education", "bölüm": "education",
    "öğrenci": "education", "transkript": "education", "diploma": "education",
    "mezun": "education", "noter": "education", "ders": "education",
    "gano": "education", "öğrenci no": "education", "yök": "education",
    # Official docs
    "sgk": "official", "sigorta": "official", "prim": "official",
    "borç": "official", "emekli": "official", "kimlik": "official",
    "adli": "official", "sicil": "official", "nüfus": "official",
    "sağlık": "official", "gss": "official", "(tc)": "official",
    # Finance
    "burs": "finance", "kredi": "finance", "kyk": "finance",
    "maaş": "finance", "vergi": "finance", "bütçe": "finance",
    "ödeme": "finance", "hesap": "finance",
    # Housing
    "yurt": "housing", "konut": "housing", "kira": "housing",
    "barınma": "housing", "yatak": "housing", "oda": "housing",
    # Tech
    "python": "tech", "javascript": "tech", "java": "tech",
    "react": "tech", "django": "tech", "flask": "tech",
    "git": "tech", "docker": "tech", "linux": "tech",
    "api": "tech", "veritabanı": "tech", "veritabani": "tech",
    "sql": "tech", "html": "tech", "css": "tech",
}


def build_document_graph() -> nx.Graph:
    """Build a graph where nodes are documents and entities, edges are connections."""
    G = nx.Graph()

    with get_connection() as conn:
        # ── 1. Add document nodes ────────────────────────────────────────────
        docs = conn.execute(
            "SELECT id, path, name, extension, size FROM documents"
        ).fetchall()

        doc_map = {}
        for doc in docs:
            doc_id = doc["id"]
            doc_map[doc_id] = {
                "name": doc["name"],
                "extension": doc["extension"],
                "size": doc["size"],
            }
            G.add_node(
                doc_id,
                label=doc["name"],
                node_type="document",
                extension=doc["extension"],
                color=FILE_TYPE_COLORS.get(doc["extension"], DEFAULT_COLOR),
                size=12,
            )

        # ── 2. Get chunk counts for sizing ──────────────────────────────────
        chunk_counts = {}
        rows = conn.execute(
            "SELECT document_id, COUNT(*) as cnt FROM chunks GROUP BY document_id"
        ).fetchall()
        for row in rows:
            chunk_counts[row["document_id"]] = row["cnt"]

        for doc_id in G.nodes:
            count = chunk_counts.get(doc_id, 1)
            G.nodes[doc_id]["size"] = max(8, min(22, 6 + count))

        # ── 3. Extract entities from chunks ─────────────────────────────────
        doc_entities: dict[str, set[str]] = {doc_id: set() for doc_id in doc_map}

        rows = conn.execute("SELECT document_id, text FROM chunks").fetchall()
        for row in rows:
            doc_id = row["document_id"]
            text = row["text"]
            entities = _extract_entities(text)
            if doc_id in doc_entities:
                doc_entities[doc_id].update(entities)

        # ── 4. Build entity → docs mapping ──────────────────────────────────
        all_entities: dict[str, set[str]] = {}
        for doc_id, entities in doc_entities.items():
            for entity in entities:
                all_entities.setdefault(entity, set()).add(doc_id)

        # ── 5. Add entity nodes ──────────────────────────────────────────────
        # Only show entities connecting 3+ documents (meaningful connections)
        for entity, connected_docs in all_entities.items():
            doc_count = len(connected_docs)
            if doc_count < 3:
                continue
            node_id = f"entity_{entity}"
            etype = ENTITY_KEYWORDS.get(entity, "general")

            # Color by category
            cat_colors = {
                "education": (180, 130, 220),  # Purple
                "official": (220, 100, 100),    # Red
                "finance": (220, 180, 80),      # Gold
                "housing": (100, 180, 140),     # Teal
                "tech": (80, 180, 220),         # Cyan
                "general": (160, 140, 180),     # Light purple
            }
            color = cat_colors.get(etype, cat_colors["general"])

            # Size: more docs → bigger node
            size = 6 + doc_count * 3

            G.add_node(
                node_id,
                label=entity,
                node_type="entity",
                entity_type=etype,
                color=tuple(c / 255 for c in color),
                size=min(size, 20),
            )

            # Connect entity to its documents
            for doc_id in connected_docs:
                G.add_edge(node_id, doc_id, edge_type="entity", weight=0.6)

        # ── 6. Add document-to-document edges (shared entities) ──────────────
        doc_pairs: dict[tuple, int] = {}
        for entity, connected_docs in all_entities.items():
            docs_list = list(connected_docs)
            for i in range(len(docs_list)):
                for j in range(i + 1, len(docs_list)):
                    pair = tuple(sorted([docs_list[i], docs_list[j]]))
                    doc_pairs[pair] = doc_pairs.get(pair, 0) + 1

        for (doc1, doc2), weight in doc_pairs.items():
            if weight >= 1:
                G.add_edge(
                    doc1, doc2,
                    edge_type="shared_entities",
                    weight=min(weight / 3.0, 1.0),
                )

    logger.info("Graph built: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G


def _extract_entities(text: str) -> set[str]:
    """Extract meaningful entities from text."""
    entities = set()
    text_lower = text.lower()

    # 1. Known keyword matches
    for keyword in ENTITY_KEYWORDS:
        if keyword in text_lower:
            entities.add(keyword)

        # 2. Extract capitalized terms (potential names/places)
        words = re.findall(r'[A-ZÇĞİÖŞÜ][a-zçğıöşü]+', text)
        for word in words:
            w = word.lower()
            if w not in STOP_WORDS_TR and len(w) > 3:
                entities.add(w)

        # 3. Extract frequent meaningful words (only if 3+ occurrences)
        words_all = re.findall(r'[a-zçğıöşü]{5,}', text_lower)
        word_freq = Counter(w for w in words_all if w not in STOP_WORDS_TR)
        for word, count in word_freq.most_common(2):
            if count >= 3:
                entities.add(word)

    return entities


def get_graph_stats(G: nx.Graph) -> dict:
    """Get statistics about the graph."""
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "documents": sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "document"),
        "entities": sum(1 for _, d in G.nodes(data=True) if d.get("node_type") == "entity"),
        "connected_components": nx.number_connected_components(G),
    }
