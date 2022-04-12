from csv import excel
import os, sys, typer, sqlite3, json
from typing import Optional
from rich.console import Console
from rich.theme import Theme

theme = Theme(
    {
        "error": "bold red",
        "warning": "bold yellow",
        "success": "green",
        "info": "italic blue"
        })

TEXMFHOME = "~/Library/texmf/"

console = Console(theme=theme)
app = typer.Typer()

def config(
    texmfhome: str, 
    pkg_db: Optional[str] = typer.Argument(None),
    mktree: bool = typer.Option(False, help="Create the local packages dir tree"), 
    force: bool = typer.Option(False, help="Overwrite current setting file")):
    """
    Set local packages path.

    Optionally: set packages database file
    """
    configs = {
        "texmfhome": texmfhome
    }
    
    if pkg_db:
        config["pkg_db"] = pkg_db
    else:
        config["pkg_db"] = ".pkg.db"

    if mktree:
        # TODO: implement mktree
        pass

    try:
        if not os.path.isfile(".config.json") or force:
            with open(".config.json","w") as file:
                json.dump(configs, file)
    except:
        console.print("[error]Error:[/] cannot write settings to JSON file!")

def help():
    print("TeXPKG: deploy and maintain your TeX packages")

def remove(pkg: str):
    pass

def update(pkg: str):
    pass

def install(input_file: str):
    print(f"Installing at {input_file}")
    pass

if __name__ == "__main__":
    app()