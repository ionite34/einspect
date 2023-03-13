import typer
from rich import Console
from rich.syntax import Syntax

from tools.sources import branch_range, extract_struct, fetch_git

console = Console()
app = typer.Typer()


@app.command()
def compare_src(path: str, struct: str, min_tag: str = "3.8", max_tag: str = "main"):
    for branch in branch_range(min_tag, max_tag):
        text = fetch_git(path, branch)
        struct_text = extract_struct(struct, text)
        struct_fmt = Syntax(struct_text, "c", line_numbers=True)
        console.print(f"[bold blue]{branch}[/bold blue]")
        console.print(struct_fmt)


@app.command()
def compare_meta(struct_name: str, min_tag: str = "3.8", max_tag: str = "main"):
    """Compare an einspect Struct with CPython source. Requires docstring metadata."""

    for branch in branch_range(min_tag, max_tag):
        text = fetch_git(path, branch)
        console.print(f"[bold blue]{branch}[/bold blue]")
        console.print(text)
