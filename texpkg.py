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

def _check_tds(localdirname):
    """
    Check if the TDS is populated correctly
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
    return all(os.path.isdir(d) for d in dirs)

def _mktree(localdirname, force=False):
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
        if force or not os.path.isdir(d):
            console.print(f"Creating directory [info]{d}[/]")
            os.makedirs(d)
        else:
            console.print(f"Directory [info]{d}[/] aready exists")
    
    console.print(f"Local TeX Directory Structure [success]succesfully created[/]")

def _get_texmfhome():
    path = os.popen("kpsewhich -var-value TEXMFHOME").read().replace("\n","")
    return path

def _create_db(conn:sqlite3.Connection):
    c = conn.cursor()
    c.execute("""CREATE TABLE packages (
            name text,
            version integer,
            type text
        )""")
    conn.commit()

@app.command()
def init(
    #tree_path: str = typer.Option(default="~/.texmf/",prompt="Enter TEXMF path", help="Path of the TEXMF tree"),
    #src_path: str = typer.Option(...,prompt="Packages source path", help="Path of the sources"), 
    #pkg_db: str = typer.Option(default=".pkg.db",prompt="Packages database path", help="Path of the packages DB"),
    force: bool = typer.Option(False, help="Overwrite current setting file",confirmation_prompt="Are you sure? This will erase the database as well")):
    """
    Create the tree path and set up the package database.
    """

    # get TEXMFHOME variable and confirm is ok
    texmf = _get_texmfhome()    
    if not Confirm.ask(f"TEXMFHOME env variable is set at [info]{texmf}[/], continue?",console=console,default=False):
        console.print(f"[info]Change the TEXMFHOME environment variable and re-run the [command]init[/] command[/]")
        return
    
    # Create the tree if it's not ok
    if not _check_tds(texmf) or force:
        _mktree(texmf) 
    
    # Create the database and package table
    conn = sqlite3.connect(".pkg.db")
    c = conn.cursor()
    try:
        _create_db()
    except sqlite3.OperationalError as e:
        console.print(str(e),style="error")


@app.command()
def wipe_tree(no_confirm: bool = typer.Option(default=False)):
    if not no_confirm:
        msg = "This will [warning]delete the current tree and its packages[/], confirm?"
        if not Confirm.ask(msg, console=console):
            return
    _mktree(_get_texmfhome(),force=True)

@app.command()
def wipe_db(no_confirm: bool = typer.Option(default=False)):
    if not no_confirm:
        msg = "This will [warning]delete the whole package database[/], confirm?"
        if not Confirm.ask(msg, console=console):
            return
    os.remove(".pkg.db")
    conn = sqlite3.connect(".pkg.db")
    _create_db(conn)
    

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