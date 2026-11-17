from pathlib import Path


def print_tree(directory, prefix=""):
  path = Path(directory)
  if not path.exists():
    print(f"Directory not found: {path}")
    return

  try:
    # Sort entries: directories first, then files alphabetically
    entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
  except PermissionError:
    return

  # Exclude .venv, __pycache__, and hidden files/folders (starting with '.')
  exclude_dirs = {".venv", "__pycache__", ".git", ".idea", ".vscode"}
  entries = [
      e
      for e in entries
      if e.name not in exclude_dirs and not e.name.startswith(".")
  ]

  pointers = ["├── "] * (len(entries) - 1) + ["└── "] if entries else []

  for pointer, entry in zip(pointers, entries):
    print(prefix + pointer + entry.name)
    if entry.is_dir():
      extension = "│   " if pointer == "├── " else "    "
      print_tree(entry, prefix + extension)


if __name__ == "__main__":
  target_dir = r"D:\AI\Projects\ai_incident_agent"
  root_path = Path(target_dir)
  print(f"{root_path.name}/")
  print_tree(target_dir)