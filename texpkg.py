from dataclasses import dataclass, asdict
import os, sys, typer, sqlite3, json

from rich.console import Console
from rich.theme import Theme

theme = Theme(
    {
        "error": "bold red",
        "warning": "bold yellow",
        "success": "green",
        "info": "italic blue",
        "command": "orange_red1"
        })

@dataclass
class Config:
    """
    Configuration dataclass, used to capture all the options 
    """
    tree_path: str
    source_path: str
    pkg_db: str
    def __post_init__(self):
        self.pkg_db = self.pkg_db if self.pkg_db else ".pkg.db"
    

console = Console(theme=theme)
app = typer.Typer()

def _retrieve_config():
    """
    Fetch the config file and return a Config object
    """
    try:
        with open(".config.json","r") as file:
            return Config(**json.load(file))
    except FileNotFoundError:
        console.print("[error]Error:[/] [info].config.json[/] file not found. Use [command]config[/] and try to re-run.")

def _mktree(localdirname):
    """
    Create the local Tex Directory Structure, necessary to install local packages.
    Each user should have its own TDS tree. Do not mess with the root TDS of TeX
    """
    dirs =[
        f"{localdirname}/bibtex/bib",
        f"{localdirname}/bibtex/bst",
        f"{localdirname}/doc",
        f"{localdirname}/fonts/afm",
        f"{localdirname}/fonts/map",
        f"{localdirname}/fonts/misc",
        f"{localdirname}/fonts/pk",
        f"{localdirname}/fonts/source",
        f"{localdirname}/fonts/tfm",
        f"{localdirname}/fonts/type1",
        f"{localdirname}/fonts/opentype",
        f"{localdirname}/fonts/truetype",
        f"{localdirname}/generic",
        f"{localdirname}/scripts",
        f"{localdirname}/source",
        f"{localdirname}/tex/context",
        f"{localdirname}/tex/generic",
        f"{localdirname}/tex/latex",
        f"{localdirname}/tex/plain",
        f"{localdirname}/tex/xelatex",
        f"{localdirname}/tex/xetex",
        f"{localdirname}/tex/luatex",
        f"{localdirname}/tex/lualatex"
        ]
    if os.path.isdir(localdirname):
        console.print("Local TEXMF directory [info]already exists[/]")
    for d in dirs:
        console.print(f"Creating directory [info]{d}[/]")
        os.makedirs(d)
    
    console.print(f"Local TeX Directory Structure [success]succesfully created[/]")


@app.command()
def config(
    tree_path: str,
    source_path: str, 
    pkg_db: str = typer.Argument(default=None),
    mktree: bool = typer.Option(False, help="Create the local packages dir tree"), 
    force: bool = typer.Option(False, help="Overwrite current setting file")):
    """
    Set local packages path.

    Optionally: set packages database file
    """
    cfg = Config(tree_path,source_path, pkg_db)

    if mktree:
        # TODO: implement mktree
        pass

    try:
        if not os.path.isfile(".config.json") or force:
            with open(".config.json","w") as file:
                json.dump(asdict(cfg), file)
        else:
            console.print("[warning]Warning:[/] [info].config.json[/] file already exists. Skipping configuration.")
    except:
        console.print("[error]Error:[/] cannot write settings to JSON file!")    

def remove(pkg: str):
    pass

def update(pkg: str):
    pass

@app.command()
def install(pkg: str):
    """
    Install command, to install specified pkg

    To install we need:
    - check if package is already installed (if it is abort)
    - understand the destination folder
    - copy the packages in the install folder into the tree_path
    """
    cfg = _retrieve_config()
    conn = sqlite3.connect(cfg.pkg_db)
    c = conn.cursor()

    pass

if __name__ == "__main__":
    app()