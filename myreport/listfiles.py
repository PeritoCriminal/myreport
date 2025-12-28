from pathlib import Path
import sys


def list_tree(base: Path, ext: str, prefix: str = "") -> list[str]:
    lines = []

    entries = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    for i, entry in enumerate(entries):
        last = i == len(entries) - 1
        connector = "└── " if last else "├── "

        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            extension = "    " if last else "│   "
            lines.extend(list_tree(entry, ext, prefix + extension))

        elif entry.is_file() and entry.suffix.lower() == ext:
            lines.append(f"{prefix}{connector}{entry.name}")

    return lines


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python listfiles.py <extensão> [caminho]")
        sys.exit(1)

    extension = sys.argv[1].lower()
    if not extension.startswith("."):
        extension = "." + extension

    root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path.cwd()

    if not root.exists() or not root.is_dir():
        print(f"Caminho inválido: {root}")
        sys.exit(1)

    output = [root.name + "/"]
    output.extend(list_tree(root, extension))

    result = "\n".join(output)

    print(result)

    output_file = root / f"list_{extension[1:]}.txt"
    output_file.write_text(result, encoding="utf-8")
