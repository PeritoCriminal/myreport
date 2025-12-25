from pathlib import Path
import sys


def print_tree(base: Path, prefix: str = "", lines: list[str] | None = None):
    if lines is None:
        lines = []

    dirs = sorted(p for p in base.iterdir() if p.is_dir())

    for i, d in enumerate(dirs):
        last = i == len(dirs) - 1
        connector = "└── " if last else "├── "
        lines.append(f"{prefix}{connector}{d.name}")

        extension = "    " if last else "│   "
        print_tree(d, prefix + extension, lines)

    return lines


if __name__ == "__main__":
    # Se caminho for informado, usa-o; senão, usa o diretório atual
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        root = Path.cwd()

    if not root.exists() or not root.is_dir():
        print(f"Caminho inválido: {root}")
        sys.exit(1)

    output = [root.name]
    output.extend(print_tree(root))

    tree = "\n".join(output)

    print(tree)

    (root / "tree_dirs.txt").write_text(tree, encoding="utf-8")
    