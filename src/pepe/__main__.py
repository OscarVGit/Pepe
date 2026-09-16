"""Allow `python -m pepe` to invoke the Typer app."""
from .cli import app

if __name__ == "__main__":
    app()
