import os, sys, typer

TEXMFHOME = "~/Library/texmf/"
app = typer.Typer()

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