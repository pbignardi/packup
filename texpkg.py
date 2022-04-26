from ensurepip import version
from importlib.metadata import packages_distributions
import os, sys, typer, sqlite3, json, shutil,re
from xml.etree.ElementInclude import include

from rich.console import Console
from rich.theme import Theme
from rich.prompt import Confirm
from rich.table import Table
from rich import box

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
conn = sqlite3.connect(".pkg.db")

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

def _rm_pkg(pkg_name: str):
    c = conn.cursor()
    c.execute("DELETE FROM packages WHERE name=?",(pkg_name,))
    conn.commit()
    c.close()

def _pkg_exists(pkg_name: str):
    c = conn.cursor()
    c.execute("SELECT * FROM packages WHERE name=?",(pkg_name,))
    out = c.fetchall()
    c.close()
    return len(out) > 0

def _add_pkg(pkg_name: str, pkg_type: str, pkg_path: str):
    c = conn.cursor()
    c.execute("INSERT INTO packages VALUES (:name, 1, :type, :path)",{
        "name": pkg_name,
        "type": pkg_type,
        "path": pkg_path
    })
    conn.commit()
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
            if verbose:
                console.print(f"Creating directory [info]{d}[/]")
            os.makedirs(d)
        else:
            console.print(f"Directory [info]{d}[/] aready exists")
    
    console.print(f"Local TeX Directory Structure [success]succesfully created[/]")

def _get_texmfhome():
    path = os.popen("kpsewhich -var-value TEXMFHOME").read().replace("\n","")
    return path

def _check_update(pkg: str):
    pass

def _get_all_pkgs():
    c = conn.cursor()
    c.execute("SELECT * FROM packages")
    return c.fetchall()

def _create_db():
    c = conn.cursor()
    c.execute("""CREATE TABLE packages (
            name text,
            version integer,
            type text,
            path text
        )""")
    conn.commit()

def _type_folder(pkg_type: str):
    """
    Get the installation folder based on the package type
    """
    if pkg_type in ["sty", "cls"]:
        return "latex"

def _get_type(pkg_name: str):
    pass

def _find_type(pkg_path):
    """
    Find type of package by looking at the extensions in the path
    """
    exts = map(lambda x: os.path.splitext(x)[1],os.listdir(pkg_path))
    if ".sty" in exts:
        return "sty"
    if ".cls" in exts:
        return "cls"
    

@app.command()
def init(force: bool = typer.Option(False, help="Overwrite current setting file",
    confirmation_prompt="Are you sure? This will erase the database as well")):
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
        _create_db(conn)
        console.print("Database [success]succesfully created[/]")
    except sqlite3.OperationalError as e:
        console.print(str(e),style="error")


@app.command()
def wipe_tree(no_confirm: bool = typer.Option(default=False)):
    """
    Delete current TEXMFHOME tree, and create a new one.
    """
    if not no_confirm:
        msg = "[warning]Deleting the current tree and its packages[/], confirm?"
        if not Confirm.ask(msg, console=console):
            return
    try:            
        shutil.rmtree(_get_texmfhome())
    except FileNotFoundError as e:
        pass

@app.command()
def wipe_db(no_confirm: bool = typer.Option(default=False)):
    """
    Delete package database and initialize a new (empty) one
    """
    if not no_confirm:
        msg = "[warning]Deleting the package database[/], confirm?"
        if not Confirm.ask(msg, console=console):
            return
    try:            
        os.remove(".pkg.db")
    except FileNotFoundError as e:
        pass
    conn = sqlite3.connect(".pkg.db")

@app.command()    
def reset(no_confirm: bool = typer.Option(default=False)):
    """
    Nuke database and tree. Equivalent to using wipe_db and wipe_tree commands
    """
    wipe_db(no_confirm)
    wipe_tree(no_confirm)


def remove(pkg: str):
    pass

@app.command()
def view():
    """
    Print the list of installed packages and all the informations in the database
    """

    
    pkg_list = _get_all_pkgs(con) # this could throw exception if packages table doesnt exists
    t = Table("Package", "Version", "Type", box=box.HORIZONTALS, header_style="blue bold")
    for entry in pkg_list:
        name, ver, typ, path = map(str,entry)
        t.add_row(name, ver, typ)

    console.print(t)
    return
    

def update(pkg: str):
    """
    Update all the packages installed by copying the
    """

@app.command()
def install(
    pkg_path: str,
    verbose: bool = typer.Option(False)):
    """
    Install command, to install specified pkg.
    Package must be a path to a directory, where the package files are contained, and dirname must not contain whitespaces.
    

    To install we need:
    - check if package is already installed (if it is abort)
    - understand the destination folder
    - copy the packages in the install folder into the tree_path
    """
    isdir = os.path.isdir(pkg_path)
    isfile = os.path.isfile(pkg_path)
    if not isdir and not isfile:
        console.print("Package file [error]does not exists[/] or directory [error]is empty[/]")
    
    source_files = [pkg_path] if isfile else map(os.path.abspath, os.listdir(pkg_path))
    pkg_dir = os.path.basename(pkg_path) if isdir else os.path.splitext(os.path.basename(pkg_path))[0]

    # get pkg name - remove whitespaces in pkg_name
    if " " in pkg_dir:
        console.print("Package name [error]must not contain whitespaces[/]")
        console.print("[info]Removing whitespaces[/] from package name")
        pkg_dir = pkg_dir.replace(" ","")

    if verbose:
        console.print(f"Installing package [info]{pkg_name}[/]")
    # connect to db
    con = sqlite3.connect(".pkg.db")
    if verbose:
        console.print("Connected to database")

    ispkg = _pkg_exists(pkg_name, con)

    # define installation destination
    texmfhome = _get_texmfhome()
    pkg_type = _find_type(os.path.abspath(pkg_path)) #if not ispkg else _get_type(pkg_name,con)
    tex_folder = _type_folder(pkg_type)
    dest = os.path.join(texmfhome,tex_folder)
    
    # actual installation
    try:
        console.print(f"Copying files for package [info]{pkg_name}[/]")
        shutil.copytree(pkg_path, os.path.join(dest,pkg_name)) 
    except FileExistsError as e:
        console.print(str(e), style="error")
        return

    # add entry into database - maybe if it doesnt work we should abort the whole thing
    if verbose:
        console.print("[info]Adding entry[/] in the package database")
    _add_pkg(pkg_name, pkg_type, os.path.abspath(pkg_path), con)

    console.print(f"Package [info]{pkg_name}[/] has been [success]succesfully installed[/]")

    if _pkg_exists(pkg_name, con):
        console.print("Package [info]already installed[/]. Updating")


if __name__ == "__main__":
    if DEBUG:
        os.environ["TEXMFHOME"] = os.path.abspath("./texmf/")
    app()