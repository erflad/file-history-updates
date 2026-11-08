def detect_changes(previous_inventory, current_inventory):
    """Compare two folder inventories."""

    changes = []

    previous_paths = set(previous_inventory)
    current_paths = set(current_inventory)

    # Newly added files
    for path in current_paths - previous_paths:
        changes.append({
            "type": "added",
            "path": path,
            "name": current_inventory[path]["name"]
        })

    # Deleted files
    for path in previous_paths - current_paths:
        changes.append({
            "type": "deleted",
            "path": path,
            "name": previous_inventory[path]["name"]
        })

    # Modified files
    for path in previous_paths & current_paths:
        old_file = previous_inventory[path]
        new_file = current_inventory[path]

        if old_file["hash"] != new_file["hash"]:
            changes.append({
                "type": "modified",
                "path": path,
                "name": new_file["name"]
            })

    return sorted(changes, key=lambda change: (change["type"], change["path"]))
