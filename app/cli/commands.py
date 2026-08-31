from __future__ import annotations

import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.config.settings import get_settings, LifeOSSettings

# Fix Windows encoding for Rich output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console()


def _ensure_config() -> LifeOSSettings:
    settings = get_settings()
    if not settings.root_directory:
        console.print(
            "[red]Root directory not set.[/red]\n"
            "Run [bold]lifeos init[/bold] first."
        )
        raise SystemExit(1)
    return settings


def _init_database(settings: LifeOSSettings) -> None:
    from app.database.sqlite import init_db
    init_db(settings.db_path)


@click.group()
def cli() -> None:
    """LifeOS — Personal Second Brain"""
    pass


# ── init ───────────────────────────────────────────────────

@cli.command()
@click.option("--root", "-r", type=str, help="Root directory path (non-interactive)")
def init(root: str | None) -> None:
    """Initialize LifeOS — set root directory and create database."""
    settings = get_settings()

    if settings.root_directory and not root:
        console.print(
            f"LifeOS already initialized.\n"
            f"Root: [bold]{settings.root_directory}[/bold]\n\n"
            "To change root, use: lifeos init --root <new_path>"
        )
        return

    console.print(Panel.fit(
        "[bold cyan]Welcome to LifeOS[/bold cyan]\n\n"
        "Let's build your second brain.\n"
        "Choose a folder where your notes, projects,\n"
        "and documents live. LifeOS will only index\n"
        "what's inside this folder.",
        title="LifeOS Init",
        border_style="cyan",
    ))

    if root:
        root_input = root
    else:
        root_input = input("\nRoot directory to index:\n> ").strip()

    if not root_input:
        console.print("[red]No path provided. Aborting.[/red]")
        return

    root_path = Path(root_input).resolve()
    if not root_path.exists():
        create = input(f"Directory does not exist. Create it? [y/N]: ").strip().lower()
        if create == "y":
            root_path.mkdir(parents=True, exist_ok=True)
        else:
            console.print("[red]Aborted.[/red]")
            return

    # Write to .env
    env_path = Path(".env")
    env_lines: list[str] = []
    if env_path.exists():
        env_lines = env_path.read_text(encoding="utf-8").splitlines()

    # Remove old LIFEOS_ROOT_DIRECTORY if exists
    env_lines = [l for l in env_lines if not l.startswith("LIFEOS_ROOT_DIRECTORY")]
    env_lines.append(f"LIFEOS_ROOT_DIRECTORY={root_path}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")

    console.print(f"\n[green]Root directory set to:[/green] {root_path}")

    # Initialize database
    settings.root_directory = str(root_path)
    _init_database(settings)

    console.print(f"[green]Database created at:[/green] {settings.db_path}")
    console.print(
        "\n[bold green]LifeOS initialized successfully![/bold green]\n\n"
        "Next steps:\n"
        "  lifeos index    — Scan and index your files\n"
        "  lifeos search   — Search your knowledge\n"
        "  lifeos ask      — Ask a question with AI"
    )


# ── index ──────────────────────────────────────────────────

@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--force", "-f", is_flag=True, help="Force re-index all files")
def index(verbose: bool, force: bool) -> None:
    """Scan and index files in the root directory."""
    settings = _ensure_config()
    _init_database(settings)

    if force:
        from app.database.sqlite import get_connection
        with get_connection() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM documents")
            conn.execute("DELETE FROM index_metadata")
        console.print("[yellow]Forced: cleared all indexed data.[/yellow]\n")

    root = settings.root_path
    if not root or not root.exists():
        console.print(f"[red]Root directory not found:[/red] {root}")
        return

    console.print(f"[cyan]Scanning:[/cyan] {root}\n")

    from app.ingestion.scanner import scan_directory
    from app.ingestion.registry import record_index_complete

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        stats = scan_directory(root, settings)
        progress.update(task, description="Done!")

    # Record index completion
    record_index_complete(root)

    # Display results
    table = Table(title="Index Results")
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")

    table.add_row("[green]New[/green]", str(stats.new))
    table.add_row("[yellow]Changed[/yellow]", str(stats.changed))
    table.add_row("[dim]Skipped[/dim]", str(stats.skipped))
    table.add_row("[red]Deleted[/red]", str(stats.deleted))
    if stats.secret_filtered > 0:
        table.add_row("[magenta]Secret (filtered)[/magenta]", str(stats.secret_filtered))
    if stats.error > 0:
        table.add_row("[red]Errors[/red]", str(stats.error))
    table.add_row("[bold]Total scanned[/bold]", str(stats.total))

    console.print(table)
    console.print("\n[bold green]Done.[/bold green]")


# ── search ─────────────────────────────────────────────────

@cli.command()
@click.argument("query")
@click.option("--top-k", "-k", default=10, help="Number of results")
def search(query: str, top_k: int) -> None:
    """Search indexed files."""
    settings = _ensure_config()
    _init_database(settings)

    console.print(f'[cyan]Searching:[/cyan] "{query}"\n')

    from app.search.hybrid import hybrid_search
    from app.models.search import SearchQuery

    sq = SearchQuery(text=query, top_k=top_k)
    results = hybrid_search(sq, settings)

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    for i, r in enumerate(results, 1):
        console.print(
            f"[bold]{i}.[/bold] {r.path}\n"
            f"   Score: [cyan]{r.score:.2f}[/cyan]  "
            f"Snippet: [dim]{r.snippet[:80]}...[/dim]\n"
        )


# ── ask ────────────────────────────────────────────────────

@cli.command()
@click.argument("question")
@click.option("--provider", "-p", default=None, help="AI provider (openai, gemini, auto)")
@click.option("--model", "-m", default=None, help="Model name")
def ask(question: str, provider: str | None, model: str | None) -> None:
    """Ask a question — AI searches your knowledge and answers."""
    settings = _ensure_config()
    _init_database(settings)

    console.print(f'[cyan]Question:[/cyan] "{question}"\n')

    from app.search.hybrid import hybrid_search
    from app.models.search import SearchQuery
    from app.ai.context_builder import build_context, extract_source_references
    from app.ai.answer_validator import validate_answer
    from app.ai.base import AIRequest
    from app.ai.factory import get_ai_provider

    # Step 1: Search
    sq = SearchQuery(text=question, top_k=settings.max_context_chunks)
    results = hybrid_search(sq, settings)

    if not results:
        console.print(
            "[dim]No relevant sources found in your indexed files.[/dim]"
        )
        return

    # Step 2: Build context
    context = build_context(results, max_chunks=settings.max_context_chunks)

    # Step 3: Generate AI answer
    console.print("[dim]Generating answer...[/dim]\n")

    try:
        ai_provider = get_ai_provider(provider=provider, model=model)
        console.print(f"[dim]Using: {ai_provider.name} ({model or 'default'})[/dim]\n")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        return

    request = AIRequest(
        question=question,
        context=context,
    )
    response = ai_provider.generate(request)

    # Step 4: Validate
    response = validate_answer(response, results)

    # Step 5: Display answer
    console.print(Panel(
        response.answer,
        title="Answer",
        border_style="cyan",
    ))

    # Step 6: Show sources
    source_refs = extract_source_references(results)
    if source_refs:
        console.print("\n[bold]Kaynaklar:[/bold]")
        for ref in source_refs:
            console.print(f"  {ref}")


# ── status ─────────────────────────────────────────────────

@cli.command()
def status() -> None:
    """Show LifeOS status."""
    settings = _ensure_config()
    _init_database(settings)

    from app.database.repositories import (
        count_documents,
        count_chunks,
        count_memories,
        get_index_meta,
    )

    doc_count = count_documents()
    chunk_count = count_chunks()
    memory_count = count_memories()
    last_index = get_index_meta("last_index_time")

    table = Table(title="LifeOS Status", show_header=False)
    table.add_column("Key", style="bold")
    table.add_column("Value")

    table.add_row("Root", settings.root_directory or "Not set")
    table.add_row("Documents", str(doc_count))
    table.add_row("Chunks", str(chunk_count))
    table.add_row("Memories", str(memory_count))
    table.add_row("Last index", last_index or "Never")
    table.add_row("DB Path", str(settings.db_path))

    console.print(table)


# ── doctor ─────────────────────────────────────────────────

@cli.command()
def doctor() -> None:
    """Check system health."""
    console.print("[bold]LifeOS Doctor[/bold]\n")

    checks = []

    # Python version
    import sys
    py_ok = sys.version_info >= (3, 11)
    checks.append(("Python 3.11+", py_ok, sys.version.split()[0]))

    # SQLite
    try:
        import sqlite3
        sqlite_ok = True
        sqlite_ver = sqlite3.sqlite_version
    except Exception:
        sqlite_ok = False
        sqlite_ver = "N/A"
    checks.append(("SQLite", sqlite_ok, sqlite_ver))

    # FAISS
    try:
        import faiss
        faiss_ok = True
        faiss_ver = getattr(faiss, "__version__", "installed")
    except ImportError:
        faiss_ok = False
        faiss_ver = "not installed"
    checks.append(("FAISS", faiss_ok, faiss_ver))

    # sentence-transformers
    try:
        import sentence_transformers
        st_ok = True
        st_ver = sentence_transformers.__version__
    except ImportError:
        st_ok = False
        st_ver = "not installed"
    checks.append(("sentence-transformers", st_ok, st_ver))

    # OpenAI
    try:
        import openai
        oai_ok = True
        oai_ver = openai.__version__
    except ImportError:
        oai_ok = False
        oai_ver = "not installed"
    checks.append(("OpenAI", oai_ok, oai_ver))

    # Config
    settings = get_settings()
    config_ok = bool(settings.root_directory)
    checks.append(("Config (root dir set)", config_ok, settings.root_directory or "not set"))

    # API key
    api_ok = bool(settings.openai_api_key)
    checks.append(("OpenAI API key", api_ok, "set" if api_ok else "not set"))

    # Root directory exists
    if settings.root_path:
        root_ok = settings.root_path.exists()
    else:
        root_ok = False
    checks.append(("Root directory exists", root_ok, str(settings.root_path) if settings.root_path else "not set"))

    # Print results
    table = Table(show_header=True)
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Version / Info")

    for name, ok, info in checks:
        status_str = "[green]OK[/green]" if ok else "[red]MISSING[/red]"
        table.add_row(name, status_str, info)

    console.print(table)

    all_ok = all(ok for _, ok, _ in checks)
    if all_ok:
        console.print("\n[bold green]All checks passed![/bold green]")
    else:
        console.print(
            "\n[bold yellow]Some components are missing.[/bold yellow]\n"
            "Run: pip install -r requirements.txt"
        )


# ── rebuild-index ──────────────────────────────────────────

@cli.command(name="rebuild-index")
def rebuild_index() -> None:
    """Rebuild the vector index from database metadata."""
    settings = _ensure_config()
    _init_database(settings)

    console.print("[cyan]Rebuilding vector index...[/cyan]")
    # Will be implemented in Phase 6
    console.print("[yellow]Vector rebuild will be available after Phase 6.[/yellow]")


# ── forget ─────────────────────────────────────────────────

@cli.command()
@click.argument("memory_id")
def forget(memory_id: str) -> None:
    """Forget a memory by ID."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.memory_engine import MemoryEngine
    engine = MemoryEngine()
    if engine.forget(memory_id):
        console.print(f"[green]Memory {memory_id} deactivated.[/green]")
    else:
        console.print(f"[red]Memory {memory_id} not found.[/red]")


# ── memories ───────────────────────────────────────────────

@cli.command()
@click.option("--type", "-t", "mem_type", help="Filter by memory type")
def memories(mem_type: str | None) -> None:
    """List all memories."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.memory_engine import MemoryEngine
    engine = MemoryEngine()

    all_memories = engine.list_all(active_only=True)
    if mem_type:
        all_memories = [m for m in all_memories if m.type == mem_type]

    if not all_memories:
        console.print("[dim]No memories found.[/dim]")
        return

    table = Table(title="Memories")
    table.add_column("ID", style="bold cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Content")
    table.add_column("Confidence", justify="right")
    table.add_column("Sources", justify="right")

    for mem in all_memories:
        table.add_row(
            mem.id,
            mem.type,
            mem.content[:80] + ("..." if len(mem.content) > 80 else ""),
            f"{mem.confidence:.0%}",
            str(mem.source_count),
        )

    console.print(table)


# ── remember ───────────────────────────────────────────────

@cli.command()
@click.argument("content")
@click.option("--type", "-t", "mem_type", default="fact", help="Memory type")
@click.option("--confidence", "-c", default=1.0, type=float, help="Confidence 0-1")
def remember(content: str, mem_type: str, confidence: float) -> None:
    """Manually save a memory."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.memory_engine import MemoryEngine
    engine = MemoryEngine()
    mem = engine.create_memory(content, memory_type=mem_type, confidence=confidence)
    console.print(f"[green]Memory saved:[/green] {mem.id} — {content[:60]}")


# ── timeline ───────────────────────────────────────────────

@cli.command()
@click.option("--days", "-d", default=30, help="Number of days to look back")
def timeline(days: int) -> None:
    """Show recent activity timeline."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.timeline import build_timeline
    events = build_timeline(days=days)

    if not events:
        console.print("[dim]No events found.[/dim]")
        return

    console.print(f"[bold]Timeline (last {days} days)[/bold]\n")

    current_date = ""
    for event in events:
        if event.date != current_date:
            current_date = event.date
            console.print(f"\n[cyan]{current_date}[/cyan]")

        icon = "📄" if event.event_type == "document" else "💡"
        console.print(f"  {icon} {event.title}")


# ── entities ───────────────────────────────────────────────

@cli.command()
@click.option("--type", "-t", "entity_type", help="Filter by entity type")
def entities(entity_type: str | None) -> None:
    """List extracted entities."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.entities import list_entities, count_entities

    all_entities = list_entities(entity_type=entity_type)

    if not all_entities:
        console.print("[dim]No entities found.[/dim]")
        return

    table = Table(title="Entities")
    table.add_column("Name", style="bold")
    table.add_column("Type", style="yellow")

    for ent in all_entities:
        table.add_row(ent.name, ent.type)

    console.print(table)
    console.print(f"\nTotal: {count_entities()}")


# ── git ────────────────────────────────────────────────────

@cli.command()
@click.option("--max-count", "-n", default=20, help="Number of recent commits to show")
def git(max_count: int) -> None:
    """Show git repository status and recent commits."""
    settings = _ensure_config()
    _init_database(settings)

    from app.git.repo import get_repo_info, get_commits, find_git_root
    from app.git.indexer import get_git_stats

    root = settings.root_path
    if not root:
        console.print("[red]Root directory not set.[/red]")
        return

    stats = get_git_stats(root)
    if not stats["is_git"]:
        console.print("[yellow]Root directory is not inside a git repository.[/yellow]")
        return

    # Repo info panel
    repo = get_repo_info(root)
    if repo:
        info = f"""[bold]Branch:[/bold] {repo.branch}
[bold]Remote:[/bold] {repo.remote_url or 'none'}
[bold]Total commits:[/bold] {repo.total_commits}
[bold]Indexed commits:[/bold] {stats['indexed_commits']}
[bold]Authors:[/bold] {', '.join(stats['unique_authors'][:5])}"""
        console.print(Panel(info, title="Git Repository", border_style="green"))

    # Recent commits table
    commits = get_commits(root, max_count=max_count)
    if commits:
        table = Table(title=f"Recent Commits (last {max_count})")
        table.add_column("Hash", style="bold cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Author", style="green")
        table.add_column("Message")
        table.add_column("Files", justify="right")
        table.add_column("±", justify="right")

        for c in commits:
            delta = f"+{c.insertions}/-{c.deletions}" if c.files_changed > 0 else ""
            table.add_row(
                c.short_hash,
                c.date,
                c.author[:20],
                c.message[:60] + ("..." if len(c.message) > 60 else ""),
                str(c.files_changed) if c.files_changed > 0 else "",
                delta,
            )

        console.print(table)


@cli.command(name="git-index")
@click.option("--max-commits", "-n", default=50, help="Max commits to index")
def git_index(max_commits: int) -> None:
    """Index git commit history for search."""
    settings = _ensure_config()
    _init_database(settings)

    root = settings.root_path
    if not root:
        console.print("[red]Root directory not set.[/red]")
        return

    from app.git.indexer import index_git_history

    console.print("[cyan]Indexing git history...[/cyan]")
    count = index_git_history(root, max_commits=max_commits)
    console.print(f"[green]Indexed {count} commits.[/green]")


# ── gui ────────────────────────────────────────────────────

@cli.command()
def gui() -> None:
    """Launch the LifeOS graphical interface."""
    settings = _ensure_config()
    _init_database(settings)

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
    except ImportError:
        console.print("[red]PySide6 not installed. Run: pip install PySide6[/red]")
        return

    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("LifeOS")
    app.setStyle("Fusion")

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    from app.gui.main_window import MainWindow
    window = MainWindow()
    window.show()

    console.print("[green]LifeOS GUI launched.[/green]")
    sys.exit(app.exec())


# ── watch ──────────────────────────────────────────────────

@cli.command()
@click.option("--no-tray", is_flag=True, help="Don't show system tray icon")
def watch(no_tray: bool) -> None:
    """Watch root directory for changes and auto-index."""
    import signal
    import time

    settings = _ensure_config()
    _init_database(settings)

    root = settings.root_path
    if not root or not root.exists():
        console.print(f"[red]Root directory not found:[/red] {root}")
        return

    console.print(f"[cyan]Watching:[/cyan] {root}")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")

    from app.background.watcher import FileWatcher
    from app.background.indexer import BackgroundIndexer

    def on_file_change(path: Path, event_type: str):
        indexer.queue_file(path, event_type)

    def on_index_complete(msg: str):
        console.print(f"  [green]{msg}[/green]")

    indexer = BackgroundIndexer(root, on_complete=on_index_complete)
    indexer.start()

    watcher = FileWatcher(root, on_change=on_file_change)
    watcher.start()

    # System tray (optional)
    tray = None
    if not no_tray:
        try:
            from PySide6.QtWidgets import QApplication
            from app.background.tray import SystemTray

            app = QApplication.instance() or QApplication(sys.argv)

            def on_show():
                console.print("[cyan]GUI is running in background[/cyan]")

            def on_quit():
                watcher.stop()
                indexer.stop()

            tray = SystemTray(on_show=on_show, on_quit=on_quit)
            tray.start()
        except ImportError:
            pass
        except Exception as e:
            logger.debug("System tray unavailable: %s", e)

    # Keep alive
    def shutdown(sig, frame):
        console.print("\n[yellow]Stopping watcher...[/yellow]")
        watcher.stop()
        indexer.stop()
        if tray:
            tray.hide()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            time.sleep(1)
            if indexer.queue_size > 0:
                console.print(f"  [dim]Queue: {indexer.queue_size} files[/dim]")
    except KeyboardInterrupt:
        watcher.stop()
        indexer.stop()
        if tray:
            tray.hide()


if __name__ == "__main__":
    cli()
