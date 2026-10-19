import typer
from rich.columns import Columns
from rich.console import Console, ConsoleRenderable, Group
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax
from rich.tree import Tree

from tools.sources import (
    CPYTHON_MAIN_VERSION,
    SourceBlock,
    branch_range,
    build_link,
    check_hash,
    extract_struct,
    fetch_git,
    hash_source,
)
from tools.struct_meta import StructMetadata

console = Console()
cp = console.print
app = typer.Typer()

PANEL_STYLE = Style(color="grey0")


def make_struct_tree(title: str, panel: Panel) -> Tree:
    """Create a tree with a panel as a leaf."""
    tree = Tree(title)
    tree.add(panel)
    return tree


def make_panel_code(heading: str, body: dict[str, str], code: Syntax | str) -> Panel:
    """Create a panel with a heading and a table of field titles."""
    body_entries = (f"[bold]{title}[/bold]: {value}" for title, value in body.items())
    column = Columns(body_entries, equal=True)
    return Panel(
        Group(column, code), title=heading, title_align="left", border_style=PANEL_STYLE
    )


def make_panel_msg(heading: str, msg: str | ConsoleRenderable) -> Panel:
    """Create a panel with a heading and a message."""
    return Panel(
        msg,
        title=heading,
    )


@app.command()
def compare_src(path: str, struct: str, min_tag: str = "3.8", max_tag: str = "main"):
    for branch in branch_range(min_tag, max_tag):
        text = fetch_git(path, branch)
        st = extract_struct(struct, text)
        cp(f"[bold blue]{branch}[/bold blue]")
        cp(f"[gray]{st.code_hash()}[/gray]")
        cp(st.as_syntax())


@app.command()
def compare_meta(struct_name: str, min_tag: str = "3.8", max_tag: str = "main"):
    """Compare an einspect Struct with CPython source. Requires docstring metadata."""
    metadata = StructMetadata.from_struct_name(struct_name)

    # Title
    cls_name = metadata.source_cls.__qualname__
    module_name = metadata.source_cls.__module__
    title = f"[grey0]{module_name}.[/grey0][bold cyan]{cls_name}[/bold cyan]"
    cp(title)

    last_hash: str | None = None
    last_code: SourceBlock | None = None
    for branch in branch_range(min_tag, max_tag):
        if branch == "main":
            version = CPYTHON_MAIN_VERSION
        else:
            version = tuple(int(v) for v in branch.split("."))

        # Build panel
        title = f"[bold blue]{branch}[/bold blue]"
        body: dict[str, str] = {}

        try:
            entry = metadata.get_version(version)
        except KeyError as e:
            cp(make_panel_msg(title, f"[bold red]{e}[/bold red]"))
            continue

        git_text = fetch_git(entry.file, branch)
        if entry.def_kind == "struct":
            try:
                st = extract_struct(entry.def_name, git_text)
            except ValueError as e:
                link = build_link(entry.file, branch)
                raise ValueError(
                    f"Struct {entry.def_name!r} not found in {branch!r} branch {link}"
                ) from e

            # Hashes
            remote_hash = st.code_hash()
            body["hash"] = f"[plum4]{remote_hash}[/plum4]"
            if local_hash := entry.hash:
                if not check_hash(local_hash):
                    body["hash (local)"] = (
                        f"[bold red]{local_hash}[/bold red] [red](invalid)[/red]"
                    )
                elif remote_hash != local_hash:
                    body["hash (local)"] = (
                        f"[bold yellow]{local_hash}[/bold yellow] [red](does not match)[/red]"
                    )
                else:
                    body["hash (local)"] = f"[green]{local_hash}[/green]"

            if last_hash == remote_hash:
                code = "[grey0]No changes[/grey0]"
            else:
                last_hash = remote_hash
                st = st.normalize()
                code = st.as_syntax(line_numbers=True)

                # Add diff
                if last_code:
                    code = st.diff(last_code).as_syntax(line_numbers=True)

                last_code = st

            panel = make_panel_code(title, body, code)
            cp(panel)

        else:
            raise ValueError(f"Unsupported definition kind: {entry.def_kind}")
