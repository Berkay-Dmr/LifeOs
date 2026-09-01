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

    # Log notification
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Index completed: %d new, %d changed, %d skipped",
                stats.new, stats.changed, stats.skipped)


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
def git_index(max_commits: int):
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


# ── projects ──────────────────────────────────────────────────

@cli.command()
def projects():
    """List all projects."""
    settings = _ensure_config()
    _init_database(settings)

    from app.projects.manager import list_projects

    all_projects = list_projects()
    if not all_projects:
        console.print("[dim]No projects found.[/dim]")
        console.print("Run: lifeos project-discover")
        return

    table = Table(title="Projects")
    table.add_column("Name", style="bold")
    table.add_column("Language")
    table.add_column("Framework")
    table.add_column("Status")
    table.add_column("Path")

    for p in all_projects:
        table.add_row(
            p.name,
            p.language or "-",
            p.framework or "-",
            p.status,
            p.path[:40],
        )

    console.print(table)


@cli.command(name="project-discover")
@click.option("--path", "-p", type=str, help="Path to scan for projects")
def project_discover(path: str | None):
    """Auto-discover projects in a directory."""
    settings = _ensure_config()
    _init_database(settings)

    scan_path = Path(path) if path else settings.root_path
    if not scan_path or not scan_path.exists():
        console.print(f"[red]Path not found:[/red] {scan_path}")
        return

    console.print(f"[cyan]Scanning for projects in:[/cyan] {scan_path}\n")

    from app.projects.manager import discover_projects

    discovered = discover_projects(scan_path)

    if not discovered:
        console.print("[dim]No projects found.[/dim]")
        return

    table = Table(title="Discovered Projects")
    table.add_column("Name", style="bold green")
    table.add_column("Language")
    table.add_column("Framework")
    table.add_column("Path")

    for p in discovered:
        table.add_row(
            p.name,
            p.language or "-",
            p.framework or "-",
            p.path[:50],
        )

    console.print(table)
    console.print(f"\n[green]{len(discovered)} project(s) found.[/green]")


@cli.command(name="project-add")
@click.argument("name")
@click.option("--path", "-p", required=True, help="Project path")
@click.option("--language", "-l", help="Programming language")
@click.option("--framework", "-f", help="Framework")
def project_add(name: str, path: str, language: str | None, framework: str | None):
    """Manually add a project."""
    settings = _ensure_config()
    _init_database(settings)

    from app.projects.manager import create_project

    project = create_project(
        name=name,
        path=path,
        language=language,
        framework=framework,
    )

    console.print(f"[green]Project created:[/green] {project.name} ({project.id})")


# ── decisions ─────────────────────────────────────────────────

@cli.command()
@click.argument("title")
@click.option("--reason", "-r", help="Reason for the decision")
@click.option("--project", "-p", help="Project ID")
@click.option("--alternatives", "-a", help="Alternatives (comma-separated)")
def decision_add(title: str, reason: str | None, project: str | None, alternatives: str | None):
    """Add a decision record."""
    settings = _ensure_config()
    _init_database(settings)

    from app.projects.manager import create_decision

    alt_list = [a.strip() for a in alternatives.split(",")] if alternatives else []

    dec = create_decision(
        title=title,
        reason=reason,
        alternatives=alt_list,
        project_id=project,
    )

    console.print(f"[green]Decision recorded:[/green] {dec.title} ({dec.id})")


@cli.command(name="decision-list")
@click.option("--project", "-p", help="Filter by project")
def decision_list(project: str | None):
    """List decisions."""
    settings = _ensure_config()
    _init_database(settings)

    from app.database.sqlite import get_connection

    with get_connection() as conn:
        if project:
            rows = conn.execute(
                "SELECT * FROM decisions WHERE project_id = ? ORDER BY date DESC",
                (project,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM decisions ORDER BY date DESC LIMIT 20"
            ).fetchall()

    if not rows:
        console.print("[dim]No decisions found.[/dim]")
        return

    table = Table(title="Decisions")
    table.add_column("Title", style="bold")
    table.add_column("Date")
    table.add_column("Status")
    table.add_column("Reason")

    for r in rows:
        status_color = "green" if r["status"] == "active" else "yellow"
        table.add_row(
            r["title"][:50],
            r["date"],
            f"[{status_color}]{r['status']}",
            (r["reason"] or "-")[:40],
        )

    console.print(table)


# ── bugs ──────────────────────────────────────────────────────

@cli.command()
@click.argument("title")
@click.option("--error", "-e", help="Error message")
@click.option("--project", "-p", help="Project ID")
@click.option("--cause", "-c", help="Root cause")
@click.option("--solution", "-s", help="Solution")
def bug_add(title: str, error: str | None, project: str | None, cause: str | None, solution: str | None):
    """Add a bug record."""
    settings = _ensure_config()
    _init_database(settings)

    from app.projects.manager import create_bug

    bug = create_bug(
        title=title,
        error_message=error,
        project_id=project,
        cause=cause,
        solution=solution,
    )

    console.print(f"[green]Bug recorded:[/green] {bug.title} ({bug.id})")


@cli.command(name="bug-list")
@click.option("--project", "-p", help="Filter by project")
@click.option("--resolved", "-r", is_flag=True, help="Show only resolved bugs")
def bug_list(project: str | None, resolved: bool):
    """List bugs."""
    settings = _ensure_config()
    _init_database(settings)

    from app.database.sqlite import get_connection

    with get_connection() as conn:
        query = "SELECT * FROM bugs WHERE 1=1"
        params = []

        if project:
            query += " AND project_id = ?"
            params.append(project)

        if resolved:
            query += " AND resolved = 1"
        else:
            query += " AND resolved = 0"

        query += " ORDER BY first_seen DESC LIMIT 20"
        rows = conn.execute(query, params).fetchall()

    if not rows:
        console.print("[dim]No bugs found.[/dim]")
        return

    table = Table(title="Bugs")
    table.add_column("Title", style="bold")
    table.add_column("Error")
    table.add_column("Status")
    table.add_column("First Seen")

    for r in rows:
        status = "[green]Resolved" if r["resolved"] else "[red]Open"
        table.add_row(
            r["title"][:40],
            (r["error_message"] or "-")[:30],
            status,
            r["first_seen"][:10],
        )

    console.print(table)


# ── git-link ─────────────────────────────────────────────────

@cli.command(name="git-link")
@click.argument("commit_hash")
@click.option("--bug", "-b", help="Link to bug ID")
@click.option("--decision", "-d", help="Link to decision ID")
@click.option("--memory", "-m", help="Link to memory event ID")
@click.option("--type", "-t", "link_type", default="relates_to", help="Link type")
def git_link(commit_hash: str, bug: str | None, decision: str | None, memory: str | None, link_type: str):
    """Link a git commit to a bug, decision, or memory."""
    settings = _ensure_config()
    _init_database(settings)

    from app.git.memory_linker import link_commit_to_memory

    if not bug and not decision and not memory:
        console.print("[red]Specify at least one: --bug, --decision, or --memory[/red]")
        return

    link_commit_to_memory(
        commit_hash=commit_hash,
        memory_event_id=memory,
        decision_id=decision,
        bug_id=bug,
        link_type=link_type,
    )

    console.print(f"[green]Commit {commit_hash[:8]} linked.[/green]")


@cli.command(name="git-links")
@click.argument("commit_hash")
def git_links(commit_hash: str):
    """Show all memory links for a commit."""
    settings = _ensure_config()
    _init_database(settings)

    from app.git.memory_linker import get_commit_links

    links = get_commit_links(commit_hash)

    if not links:
        console.print("[dim]No links found for this commit.[/dim]")
        return

    for link in links:
        console.print(f"\n[bold]{link['link_type']}[/bold]")

        if link["memory"]:
            console.print(f"  Memory: {link['memory']['title']} ({link['memory']['type']})")
        if link["decision"]:
            console.print(f"  Decision: {link['decision']['title']} [{link['decision']['status']}]")
        if link["bug"]:
            status = "resolved" if link["bug"]["resolved"] else "open"
            console.print(f"  Bug: {link['bug']['title']} ({status})")


# ── code-deps ────────────────────────────────────────────────

@cli.command(name="code-deps")
@click.argument("file_path")
def code_deps(file_path: str):
    """Show dependencies for a code file."""
    settings = _ensure_config()
    _init_database(settings)

    from app.code_intelligence.dependencies import get_file_dependencies

    deps = get_file_dependencies(file_path)

    if not deps:
        console.print("[dim]No dependencies found.[/dim]")
        return

    table = Table(title=f"Dependencies: {file_path}")
    table.add_column("Type", style="cyan")
    table.add_column("Target", style="bold")

    for dep in deps:
        target = dep["calls_function"] or dep["calls_file"] or "-"
        table.add_row(dep["dependency_type"], target)

    console.print(table)


@cli.command(name="code-index")
@click.argument("path", required=False)
def code_index(path: str | None):
    """Index code dependencies in a directory."""
    settings = _ensure_config()
    _init_database(settings)

    scan_path = path or str(settings.root_path)
    if not scan_path:
        console.print("[red]Path not set.[/red]")
        return

    from app.code_intelligence.dependencies import index_directory_dependencies

    console.print(f"[cyan]Indexing dependencies in:[/cyan] {scan_path}")
    count = index_directory_dependencies(scan_path)
    console.print(f"[green]Indexed {count} dependencies.[/green]")


# ── todo ─────────────────────────────────────────────────────

@cli.command(name="todo-extract")
@click.argument("path", required=False)
@click.option("--store", "-s", is_flag=True, help="Store in database")
def todo_extract(path: str | None, store: bool):
    """Extract TODOs from code files."""
    settings = _ensure_config()
    _init_database(settings)

    from app.ai.smart_systems import extract_todos_from_directory, extract_todos_from_file, store_todos

    scan_path = path or str(settings.root_path)
    if not scan_path:
        console.print("[red]Path not set.[/red]")
        return

    console.print(f"[cyan]Extracting TODOs from:[/cyan] {scan_path}")

    if path:
        todos = extract_todos_from_file(scan_path)
    else:
        todos = extract_todos_from_directory(scan_path)

    if not todos:
        console.print("[dim]No TODOs found.[/dim]")
        return

    if store:
        count = store_todos(todos)
        console.print(f"[green]Stored {count} new tasks.[/green]")

    table = Table(title="TODOs Found")
    table.add_column("Priority", style="bold")
    table.add_column("Task")
    table.add_column("Source")

    priority_colors = {"high": "red", "medium": "yellow", "low": "green"}

    for todo in todos[:20]:
        color = priority_colors.get(todo["priority"], "white")
        source = todo.get("source", "-")
        if source and len(source) > 30:
            source = "..." + source[-27:]
        table.add_row(
            f"[{color}]{todo['priority']}",
            todo["text"][:50],
            source,
        )

    console.print(table)


@cli.command(name="todo-list")
def todo_list():
    """List open tasks."""
    settings = _ensure_config()
    _init_database(settings)

    from app.ai.smart_systems import get_open_tasks

    tasks = get_open_tasks()

    if not tasks:
        console.print("[dim]No open tasks.[/dim]")
        return

    table = Table(title="Open Tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Priority")
    table.add_column("Task")
    table.add_column("Source")

    priority_colors = {"high": "red", "medium": "yellow", "low": "green"}

    for task in tasks:
        color = priority_colors.get(task["priority"], "white")
        source = task.get("source", "-")
        if source and len(source) > 30:
            source = "..." + source[-27:]
        table.add_row(
            task["id"],
            f"[{color}]{task['priority']}",
            task["text"][:50],
            source,
        )

    console.print(table)


# ── dedup ────────────────────────────────────────────────────

@cli.command(name="memory-dedup")
def memory_dedup():
    """Check for duplicate memories."""
    settings = _ensure_config()
    _init_database(settings)

    from app.database.sqlite import get_connection
    from app.ai.smart_systems import check_duplicate

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, content, type FROM memories WHERE active = 1 LIMIT 50"
        ).fetchall()

    duplicates = 0
    for row in rows:
        result = check_duplicate(row["content"], row["type"])
        if result:
            duplicates += 1
            console.print(
                f"\n[bold yellow]Duplicate found:[/bold yellow]\n"
                f"  Existing: {result['existing_content'][:60]}\n"
                f"  Similarity: {result['similarity']:.0%}\n"
                f"  ID: {result['existing_id']}"
            )

    if duplicates == 0:
        console.print("[green]No duplicates found.[/green]")
    else:
        console.print(f"\n[yellow]{duplicates} potential duplicate(s) found.[/yellow]")


# ── contradict ───────────────────────────────────────────────

@cli.command(name="decision-check")
@click.argument("title")
def decision_check(title: str):
    """Check if a decision contradicts existing ones."""
    settings = _ensure_config()
    _init_database(settings)

    from app.ai.smart_systems import detect_contradiction

    contradictions = detect_contradiction(title)

    if not contradictions:
        console.print("[green]No contradictions detected.[/green]")
        return

    console.print(f"[bold yellow]⚠ {len(contradictions)} potential contradiction(s):[/bold yellow]\n")

    for c in contradictions:
        console.print(
            f"  [bold]Existing:[/bold] {c['existing_title']}\n"
            f"  [bold]New:[/bold] {c['new_title']}\n"
            f"  [bold]Type:[/bold] {c['type']}\n"
            f"  [bold]Confidence:[/bold] {c['confidence']:.0%}\n"
        )


# ── find (global search) ─────────────────────────────────────

@cli.command()
@click.argument("query")
def find(query: str):
    """Find anything across your knowledge base."""
    settings = _ensure_config()
    _init_database(settings)

    from app.search.global_search import global_search, get_search_stats

    console.print(f'[cyan]Finding:[/cyan] "{query}"\n')

    results = global_search(query)

    total = sum(len(v) for v in results.values())
    if total == 0:
        console.print("[dim]No results found.[/dim]")
        return

    # Stats
    stats = get_search_stats()
    console.print(f"[dim]Searching across: {stats.get('files', 0)} files, "
                  f"{stats.get('bugs', 0)} bugs, "
                  f"{stats.get('decisions', 0)} decisions[/dim]\n")

    # Files
    if results["files"]:
        console.print("[bold cyan]Files:[/bold cyan]")
        for r in results["files"][:5]:
            console.print(f"  {r.title} — {r.snippet[:50]}")
        console.print()

    # Bugs
    if results["bugs"]:
        console.print("[bold red]Bugs:[/bold red]")
        for r in results["bugs"][:3]:
            status = r.metadata.get("status", "?")
            console.print(f"  [{status}] {r.title}")
        console.print()

    # Decisions
    if results["decisions"]:
        console.print("[bold yellow]Decisions:[/bold yellow]")
        for r in results["decisions"][:3]:
            console.print(f"  {r.title} ({r.metadata.get('date', '')})")
        console.print()

    # Memory
    if results["memory"]:
        console.print("[bold green]Memory:[/bold green]")
        for r in results["memory"][:3]:
            console.print(f"  {r.title}")
        console.print()

    # Commits
    if results["commits"]:
        console.print("[bold blue]Commits:[/bold blue]")
        for r in results["commits"][:3]:
            console.print(f"  {r.title}: {r.snippet[:50]}")
        console.print()

    # Tasks
    if results["tasks"]:
        console.print("[bold magenta]Tasks:[/bold magenta]")
        for r in results["tasks"][:3]:
            console.print(f"  {r.title}")
        console.print()


@cli.command(name="find-stats")
def find_stats():
    """Show statistics about searchable content."""
    settings = _ensure_config()
    _init_database(settings)

    from app.search.global_search import get_search_stats

    stats = get_search_stats()

    table = Table(title="Knowledge Base Stats")
    table.add_column("Type", style="bold")
    table.add_column("Count", justify="right")

    for key, value in stats.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)


# ── memory score ────────────────────────────────────────────────

@cli.command(name="memory-score")
@click.option("--decay", is_flag=True, help="Apply temporal decay")
def memory_score(decay: bool):
    """Show memory importance scores."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.advanced import get_memory_stats, apply_temporal_decay, get_important_memories

    if decay:
        affected = apply_temporal_decay()
        console.print(f"[yellow]Applied decay to {affected} records[/yellow]\n")

    stats = get_memory_stats()

    table = Table(title="Memory Stats")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Memories", str(stats["total_memories"]))
    table.add_row("Average Score", f"{stats['avg_score']:.2f}")
    table.add_row("High Importance (>0.7)", str(stats["high_importance"]))
    table.add_row("Low Importance (<0.3)", str(stats["low_importance"]))
    table.add_row("Stale (>30 days)", str(stats["stale_memories"]))

    console.print(table)

    # Top memories
    memories = get_important_memories(limit=5)
    if memories:
        console.print("\n[bold]Top Important Memories:[/bold]")
        for m in memories:
            score = m.get("score", 0) or 0
            console.print(f"  [{score:.2f}] {m['title'][:50]}")


@cli.command(name="memory-consolidate")
def memory_consolidate():
    """Merge duplicate memories."""
    settings = _ensure_config()
    _init_database(settings)

    from app.memory.advanced import consolidate_memories

    result = consolidate_memories()

    console.print(f"[green]Merged: {result['merged']} duplicates[/green]")
    console.print(f"[green]Kept: {result['kept']} unique memories[/green]")


# ── graph analysis ────────────────────────────────────────────────

@cli.command(name="graph-centrality")
@click.option("--top", default=10, help="Show top N nodes")
def graph_centrality(top: int):
    """Show most important nodes in the knowledge graph."""
    settings = _ensure_config()
    _init_database(settings)

    from app.graph.graph_builder import build_document_graph, get_centrality

    G = build_document_graph()
    centrality = get_centrality(G, top=top)

    table = Table(title=f"Top {top} Central Nodes")
    table.add_column("Node", style="bold")
    table.add_column("Type")
    table.add_column("Centrality", justify="right")
    table.add_column("Connections", justify="right")

    for node in centrality:
        table.add_row(
            node["label"][:40],
            node["type"],
            f"{node['centrality']:.3f}",
            str(node["degree"]),
        )

    console.print(table)


@cli.command(name="graph-communities")
def graph_communities():
    """Detect communities in the knowledge graph."""
    settings = _ensure_config()
    _init_database(settings)

    from app.graph.graph_builder import build_document_graph, find_communities

    G = build_document_graph()
    communities = find_communities(G)

    console.print(f"[bold]Found {len(communities)} communities[/bold]\n")

    for i, community in enumerate(communities[:5], 1):
        docs = [G.nodes[n].get("label", n) for n in community
                if G.nodes[n].get("node_type") == "document"][:5]
        if docs:
            console.print(f"[bold cyan]Community {i}:[/bold cyan]")
            for doc in docs:
                console.print(f"  - {doc}")
            console.print()


@cli.command(name="graph-path")
@click.argument("source")
@click.argument("target")
def graph_path(source: str, target: str):
    """Find path between two nodes."""
    settings = _ensure_config()
    _init_database(settings)

    from app.graph.graph_builder import build_document_graph, find_path

    G = build_document_graph()

    # Find nodes by label
    source_id = None
    target_id = None

    for node_id, data in G.nodes(data=True):
        label = data.get("label", "").lower()
        if source.lower() in label and source_id is None:
            source_id = node_id
        if target.lower() in label and target_id is None:
            target_id = node_id

    if not source_id:
        console.print(f"[red]Source '{source}' not found[/red]")
        return
    if not target_id:
        console.print(f"[red]Target '{target}' not found[/red]")
        return

    path = find_path(G, source_id, target_id)

    if not path:
        console.print("[yellow]No path found[/yellow]")
        return

    console.print(f"[bold]Path ({len(path)} steps):[/bold]")
    for i, node_id in enumerate(path):
        label = G.nodes[node_id].get("label", node_id)
        if i < len(path) - 1:
            console.print(f"  {label} →")
        else:
            console.print(f"  {label}")


# ── API server ────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=8000, help="Port to bind")
def api(host: str, port: int):
    """Start REST API server for mobile access."""
    settings = _ensure_config()
    _init_database(settings)

    from app.api.server import LifeOSServer

    server = LifeOSServer(host=host, port=port)
    server.start()

    console.print(f"[bold green]LifeOS API server started![/bold green]")
    console.print(f"[dim]Endpoint: http://{host}:{port}[/dim]")
    console.print(f"[dim]Health: http://{host}:{port}/api/health[/dim]")
    console.print(f"\nPress Ctrl+C to stop\n")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
        console.print("[yellow]Server stopped[/yellow]")


# ── bulk-delete ──────────────────────────────────────────

@cli.command(name="bulk-delete")
@click.option("--ext", "-e", help="Delete by extension (e.g., .pdf)")
@click.option("--pattern", "-p", help="Delete by name pattern")
@click.option("--older-than", "-d", type=int, help="Delete files older than N days")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted")
def bulk_delete(ext: str | None, pattern: str | None, older_than: int | None, dry_run: bool):
    """Bulk delete documents from index."""
    settings = _ensure_config()
    _init_database(settings)

    from app.database.repositories import (
        delete_documents_by_extension,
        delete_documents_by_pattern,
        delete_old_documents,
        count_documents,
    )

    if not ext and not pattern and not older_than:
        console.print("[red]Specify at least one filter: --ext, --pattern, or --older-than[/red]")
        return

    if ext:
        before = count_documents()
        if dry_run:
            with get_connection() as conn:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE extension = ?", (ext,)
                ).fetchone()[0]
            console.print(f"[yellow]Dry run:[/yellow] Would delete {cnt} documents with extension '{ext}'")
        else:
            deleted = delete_documents_by_extension(ext)
            console.print(f"[green]Deleted {deleted} documents with extension '{ext}'[/green]")

    if pattern:
        if dry_run:
            with get_connection() as conn:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE name LIKE ?", (f"%{pattern}%",)
                ).fetchone()[0]
            console.print(f"[yellow]Dry run:[/yellow] Would delete {cnt} documents matching '{pattern}'")
        else:
            deleted = delete_documents_by_pattern(pattern)
            console.print(f"[green]Deleted {deleted} documents matching '{pattern}'[/green]")

    if older_than:
        if dry_run:
            from datetime import datetime, timedelta
            cutoff = (datetime.utcnow() - timedelta(days=older_than)).isoformat()
            with get_connection() as conn:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM documents WHERE modified_at < ?", (cutoff,)
                ).fetchone()[0]
            console.print(f"[yellow]Dry run:[/yellow] Would delete {cnt} documents older than {older_than} days")
        else:
            deleted = delete_old_documents(older_than)
            console.print(f"[green]Deleted {deleted} documents older than {older_than} days[/green]")


# ── bulk-reindex ──────────────────────────────────────────

@cli.command(name="bulk-reindex")
@click.option("--ext", "-e", help="Re-index by extension (e.g., .pdf)")
@click.option("--all", "reindex_all", is_flag=True, help="Re-index all files")
def bulk_reindex(ext: str | None, reindex_all: bool):
    """Bulk re-index documents."""
    settings = _ensure_config()
    _init_database(settings)

    if not ext and not reindex_all:
        console.print("[red]Specify --ext or --all[/red]")
        return

    root = settings.root_path
    if not root or not root.exists():
        console.print(f"[red]Root directory not found:[/red] {root}")
        return

    from app.database.sqlite import get_connection
    from app.ingestion.scanner import scan_directory

    if reindex_all:
        console.print("[cyan]Re-indexing all files...[/cyan]")
        with get_connection() as conn:
            conn.execute("DELETE FROM chunks")
            conn.execute("DELETE FROM documents")
        stats = scan_directory(root, settings)
        console.print(f"[green]Done: {stats.new} indexed, {stats.skipped} skipped[/green]")
    elif ext:
        console.print(f"[cyan]Re-indexing files with extension '{ext}'...[/cyan]")
        with get_connection() as conn:
            doc_ids = [r["id"] for r in conn.execute(
                "SELECT id FROM documents WHERE extension = ?", (ext,)
            ).fetchall()]
            if doc_ids:
                placeholders = ",".join("?" * len(doc_ids))
                conn.execute(f"DELETE FROM chunks WHERE document_id IN ({placeholders})", doc_ids)
                conn.execute(f"DELETE FROM documents WHERE id IN ({placeholders})", doc_ids)
        stats = scan_directory(root, settings)
        console.print(f"[green]Done: {stats.new} indexed, {stats.skipped} skipped[/green]")


# ── stats ──────────────────────────────────────────────────

@cli.command()
def stats():
    """Show detailed index statistics."""
    settings = _ensure_config()
    _init_database(settings)

    from app.database.repositories import get_extension_stats, count_chunks, count_documents

    ext_stats = get_extension_stats()
    doc_count = count_documents()
    chunk_count = count_chunks()

    table = Table(title="Index Statistics")
    table.add_column("Extension", style="bold")
    table.add_column("Count", justify="right")

    for ext, cnt in ext_stats.items():
        table.add_row(ext, str(cnt))

    table.add_row("─" * 10, "─" * 5)
    table.add_row("TOTAL", str(doc_count))

    console.print(table)
    console.print(f"Total chunks: {chunk_count}")


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
        # Log for notification system
        logger.info("Auto-index: %s", msg)

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
