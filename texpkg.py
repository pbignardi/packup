import os, sys, typer

TEXMFHOME = "~/Library/texmf/"
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

@app.command()
def update(pkg: str):
    pass

@app.command()
def install(input_file: str):
    print(f"Installing at {input_file}")
    pass

def main(command, input=None, output=None):
    # dispatch command
    return

if __name__ == "__main__":
    app()