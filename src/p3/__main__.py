"""Start logging before loading scientific dependencies."""
from pathlib import Path
import sys
from .logging import logged_main, member_log_folder


def main():
    from .cli import main as command
    command()


if __name__ == "__main__":
    folder = Path(__file__).resolve().parents[2] / 'results/p3/logs'
    logged_main(main, member_log_folder(folder, sys.argv[1:]))
