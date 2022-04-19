import os, sys, typer, sqlite3, json, shutil

from rich.console import Console
from rich.theme import Theme
from rich.prompt import Confirm

theme = Theme(
    {
        "error": "bold red",
        "warning": "bold yellow",
        "success": "green",
        "info": "italic blue",
        "command": "orange_red1"
        })
    
DEBUG = True    

console = Console(theme=theme)
app = typer.Typer()

def _unpack_name_opt(file, isclass=False):
    provide_cmd = "ProvidesClass" if isclass else "ProvidesPackage" 
    with open(file,"r") as f:
        line = f.readline()
        while line:
            if provide_cmd in line:
                pkg_matches = re.findall("\{[a-zA-Z0-9]*\}", line)
                ver_matches = re.findall("\[.*?\]", line)
                if pkg_matches:
                    package_string = pkg_matches[0][1:-1]
                    version_string = ver_matches[0][1:-1] if ver_matches else ""
                    return package_string, version_string

def _extract_ver_desc(opt: str):
    version = re.search("[0-9]{1,4}[./-]?[0-9]{1,4}[./-]?[0-9]{1,4}", opt)
    return version.group(), (opt[0:version.start()] + opt[version.end():]).lstrip()

def _rm_pkg(pkg_name: str, db_conn: sqlite3.Connection):
    c = db_conn.cursor()
    c.execute("DELETE FROM packages WHERE name=?",(pkg_name,))
    db_conn.commit()
    c.close()
    
def _pkg_exists(pkg_name: str, db_conn: sqlite3.Connection):
    c = db_conn.cursor()
    c.execute("SELECT * FROM packages WHERE name=?",(pkg_name,))
    out = c.fetchall()
    c.close()
    return len(out) > 0

def _add_pkg(pkg_name: str, pkg_type: str, db_conn: sqlite3.Connection):
    c = db_conn.cursor()
    c.execute("INSERT INTO packages VALUES (:name, 1, :type)",{
        "name": pkg_name,
        "type": pkg_type
    })
    db_conn.commit()
    c.close()


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

def _mktree(localdirname, verbose=False):
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
        if not os.path.isdir(d):
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
    """
    DElete current TEXMFHOME tree, and create a new one.
    """
    if not no_confirm:
        msg = "This will [warning]delete the current tree and its packages[/], confirm?"
        if not Confirm.ask(msg, console=console):
            return
    shutil.rmtree(_get_texmfhome())
    _mktree(_get_texmfhome())

@app.command()
def wipe_db(no_confirm: bool = typer.Option(default=False)):
    """
    Delete package database and initialize a new (empty) one
    """
    if not no_confirm:
        msg = "This will [warning]delete the whole package database[/], confirm?"
        if not Confirm.ask(msg, console=console):
            return
    os.remove(".pkg.db")
    conn = sqlite3.connect(".pkg.db")
    _create_db(conn)
    

def remove(pkg: str):
    pass

@app.command()
def view():
    """
    Print the list of installed packages and all the informations in the database
    """
    con = sqlite3.connect(".pkg.db")
    
    pkg_list = _get_all_pkgs(con) # this could throw exception if packages table doesnt exists
    t = Table("Package", "Version", "Type", "Path", box=box.HORIZONTALS, header_style="blue bold")
    for entry in pkg_list:
        name, ver, typ, path = map(str,entry)
        t.add_row(name, ver, typ)

    console.print(t)
    return
    

def update(pkg: str):
    pass

@app.command()
def install(
    pkg_path: str = typer.Argument(help="Path to package directory"),
    verbose: bool = typer.Option(True)):
    """
    Install command, to install specified pkg.
    Package must be a path to a directory, where the package files are contained.


    To install we need:
    - check if package is already installed (if it is abort)
    - understand the destination folder
    - copy the packages in the install folder into the tree_path
    """
    # check if path exists
    if not os.path.isdir(pkg_path) or len(os.listdir(pkg_path)) == 0:
        console.print("Package directory [error]does not exists[/] or [error]is empty[/]")
    # get pkg name - remove whitespaces in pkg_name
    pkg_name = os.path.basename(os.path.abspath(pkg_path))
    if " " in pkg_name:
        console.print("Package directory name [error]must not contain whitespaces[/].")
        return

    conn = sqlite3.connect(".pkg.db")
    c = conn.cursor()

    pass

if __name__ == "__main__":
    if DEBUG:
        os.environ["TEXMFHOME"] = os.path.abspath(".")
    app()