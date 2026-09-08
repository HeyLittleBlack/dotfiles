def draw_title(data):
    from kitty.fast_data_types import get_boss

    tab = get_boss().tab_for_id(data["tab_id"])
    title = tab.name if tab else ""
    if not title:
        path = data["tab"].active_wd.rstrip("/")
        title = path.rsplit("/", 1)[-1] or "/"
    return f'{data["index"]}: {title}'
