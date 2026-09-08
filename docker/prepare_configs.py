"""Fill each missing configuration without overwriting existing user settings."""
from pathlib import Path
import shutil


def prepare_configs(directory=Path("configs")):
    for source in directory.glob("*.py.example"):
        target = source.with_suffix("")
        if not target.exists():
            shutil.copyfile(source, target)


if __name__ == "__main__":
    prepare_configs()
