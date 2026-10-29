"""Start logging before loading scientific dependencies."""
from pathlib import Path
from .logging import logged_main


def main():
    from .cli import main as command
    command()


if __name__ == "__main__":
    logged_main(main, Path(__file__).resolve().parents[2] / 'results/p3/logs')
