"""Public command for the single-CSV PCA-order workflow."""
import subprocess
from .pca_order_csv import main

if __name__ == '__main__':
    try:
        main()
    except (ValueError, FileNotFoundError, FileExistsError, AssertionError, subprocess.SubprocessError) as error:
        raise SystemExit(f'PCA-order experiment stopped: {error}') from error
