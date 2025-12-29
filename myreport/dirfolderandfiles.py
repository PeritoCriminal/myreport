from pathlib import Path
import sys


def list_folders_one_level(base: Path) -> list[str]:
    lines: list[str] = []

    folders = sorted(p for p in base.iterdir() if p.is_dir())

    for folder in folders:
        subdirs = sorted(d for d in folder.iterdir() if d.is_dir())
        files = sorted(f for f in folder.iterdir() if f.is_file())

        if not subdirs and not files:
            continue

        lines.append(folder.name)

        items = [(d.name, "dir") for d in subdirs] + [(f.name, f.suffix or "(sem extensão)") for f in files]

        for i, (name, info) in enumerate(items):
            last = i == len(items) - 1
            connector = "└── " if last else "├── "

            if info == "dir":
                lines.append(f"  {connector}{name} (dir)")
            else:
                ext = info
                lines.append(f"  {connector}{name} [{ext}]")

    return lines


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

    if not root.exists() or not root.is_dir():
        print(f"Caminho inválido: {root}")
        sys.exit(1)

    output = [root.name]
    output.extend(list_folders_one_level(root))

    result = "\n".join(output)

    print(result)

    (root / "folders_and_files.txt").write_text(result, encoding="utf-8")
