"""Shared tree utilities for parsed ability structures."""


def walk_nodes(value, visit):
    """Depth-first walk over dict/list nodes and call visit for each dict."""
    if isinstance(value, dict):
        visit(value)
        for item in value.values():
            walk_nodes(item, visit)
    elif isinstance(value, list):
        for item in value:
            walk_nodes(item, visit)


def annotate_tree(value, text):
    """Attach source text to every parsed dict in a tree."""
    if not text or value is None:
        return value
    if isinstance(value, dict):
        value.setdefault('text', text)
        for item in value.values():
            annotate_tree(item, text)
    elif isinstance(value, list):
        for item in value:
            annotate_tree(item, text)
    return value


def prune_empty_raw_nodes(value):
    """Remove nodes that only carry an empty raw_text placeholder."""
    if isinstance(value, dict):
        keys_to_delete = []
        for key, item in value.items():
            if isinstance(item, dict) and item.get('raw_text') == '':
                keys_to_delete.append(key)
            else:
                prune_empty_raw_nodes(item)
        for key in keys_to_delete:
            del value[key]
    elif isinstance(value, list):
        items = []
        for item in value:
            if isinstance(item, dict) and item.get('raw_text') == '':
                continue
            prune_empty_raw_nodes(item)
            items.append(item)
        value[:] = items
    return value


def apply_tree_field(data, field_name, value_factory, *, tree_key='effect'):
    """Copy a computed field onto every dict node in each parsed tree."""
    for item in data.get('unique_abilities', []):
        tree = item.get(tree_key)
        if not tree:
            continue

        value = value_factory(item)
        if value is None:
            continue

        def visit(node):
            if field_name not in node:
                node[field_name] = value

        walk_nodes(tree, visit)

    return data
