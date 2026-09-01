from __future__ import annotations

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

from app.config.settings import get_settings
from app.database.sqlite import init_db

import logging

logger = logging.getLogger(__name__)


class LifeOSAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for LifeOS API."""

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Route requests
        if path == "/api/health":
            self._send_json({"status": "ok", "version": "0.4.0"})

        elif path == "/api/search":
            query = params.get("query", [""])[0]
            limit = int(params.get("limit", ["10"])[0])
            self._handle_search(query, limit)

        elif path == "/api/stats":
            self._handle_stats()

        elif path == "/api/graph":
            self._handle_graph()

        elif path.startswith("/api/documents/"):
            doc_id = path.split("/")[-1]
            self._handle_document(doc_id)

        elif path == "/api/memory":
            self._handle_memory()

        elif path == "/api/decisions":
            self._handle_decisions()

        elif path == "/api/bugs":
            self._handle_bugs()

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            data = {}

        if path == "/api/ask":
            self._handle_ask(data)
        elif path == "/api/memory":
            self._handle_create_memory(data)
        elif path == "/api/decisions":
            self._handle_create_decision(data)
        elif path == "/api/bugs":
            self._handle_create_bug(data)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _handle_search(self, query: str, limit: int):
        """Handle search request."""
        try:
            from app.search.global_search import global_search
            results = global_search(query, limit=limit)

            # Convert to JSON-serializable format
            serialized = {}
            for key, items in results.items():
                serialized[key] = [
                    {
                        "type": r.type,
                        "title": r.title,
                        "snippet": r.snippet,
                        "source": r.source,
                    }
                    for r in items
                ]

            self._send_json({"query": query, "results": serialized})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_stats(self):
        """Handle stats request."""
        try:
            from app.search.global_search import get_search_stats
            stats = get_search_stats()
            self._send_json(stats)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_graph(self):
        """Handle graph request."""
        try:
            from app.graph.graph_builder import build_document_graph, get_graph_stats

            G = build_document_graph()
            stats = get_graph_stats(G)

            # Get nodes and edges for visualization
            nodes = []
            for node_id, data in G.nodes(data=True):
                nodes.append({
                    "id": node_id,
                    "label": data.get("label", node_id),
                    "type": data.get("node_type", "unknown"),
                })

            edges = []
            for u, v, data in G.edges(data=True):
                edges.append({
                    "source": u,
                    "target": v,
                    "type": data.get("edge_type", "unknown"),
                })

            self._send_json({"stats": stats, "nodes": nodes[:100], "edges": edges[:200]})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_document(self, doc_id: str):
        """Handle document request."""
        try:
            from app.database.sqlite import get_connection

            with get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM documents WHERE id = ?", (doc_id,)
                ).fetchone()

                if row:
                    self._send_json(dict(row))
                else:
                    self._send_json({"error": "Document not found"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_memory(self):
        """Handle memory request."""
        try:
            from app.memory.advanced import get_important_memories
            memories = get_important_memories(limit=20)
            self._send_json({"memories": memories})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_decisions(self):
        """Handle decisions request."""
        try:
            from app.database.sqlite import get_connection

            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM decisions ORDER BY created_at DESC LIMIT 20"
                ).fetchall()
                self._send_json({"decisions": [dict(r) for r in rows]})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_bugs(self):
        """Handle bugs request."""
        try:
            from app.database.sqlite import get_connection

            with get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM bugs ORDER BY created_at DESC LIMIT 20"
                ).fetchall()
                self._send_json({"bugs": [dict(r) for r in rows]})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_ask(self, data: dict):
        """Handle AI ask request."""
        question = data.get("question", "")
        if not question:
            self._send_json({"error": "Question required"}, 400)
            return

        try:
            from app.ai.smart_context import build_smart_context, build_answer_with_sources
            from app.ai.gemini_provider import GeminiProvider

            # Build context
            context = build_smart_context(question)

            # Get AI response
            settings = get_settings()
            provider = GeminiProvider(settings.gemini_api_key)
            answer = provider.generate(question, context=context)

            # Build structured response
            result = build_answer_with_sources(question, answer)

            self._send_json(result)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_create_memory(self, data: dict):
        """Handle create memory request."""
        title = data.get("title", "")
        description = data.get("description", "")
        memory_type = data.get("type", "note")

        if not title:
            self._send_json({"error": "Title required"}, 400)
            return

        try:
            from app.projects.manager import ProjectManager
            manager = ProjectManager()
            memory_id = manager.create_memory_event(title, description, memory_type)
            self._send_json({"id": memory_id, "message": "Memory created"})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_create_decision(self, data: dict):
        """Handle create decision request."""
        title = data.get("title", "")
        reason = data.get("reason", "")

        if not title:
            self._send_json({"error": "Title required"}, 400)
            return

        try:
            from app.projects.manager import ProjectManager
            manager = ProjectManager()
            decision_id = manager.create_decision(title, reason)
            self._send_json({"id": decision_id, "message": "Decision created"})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _handle_create_bug(self, data: dict):
        """Handle create bug request."""
        title = data.get("title", "")
        error_message = data.get("error_message", "")
        cause = data.get("cause", "")

        if not title:
            self._send_json({"error": "Title required"}, 400)
            return

        try:
            from app.projects.manager import ProjectManager
            manager = ProjectManager()
            bug_id = manager.create_bug(title, error_message, cause)
            self._send_json({"id": bug_id, "message": "Bug created"})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def _send_json(self, data: dict, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def log_message(self, format, *args):
        """Log HTTP requests."""
        logger.info(format % args)


class LifeOSServer:
    """LifeOS REST API server."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the server in background."""
        settings = get_settings()
        init_db(settings.database_path)

        self.server = HTTPServer((self.host, self.port), LifeOSAPIHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        logger.info("LifeOS API server started on http://%s:%d", self.host, self.port)

    def stop(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
            logger.info("LifeOS API server stopped")

    def is_running(self) -> bool:
        """Check if server is running."""
        return self.server is not None and self.thread is not None and self.thread.is_alive()
