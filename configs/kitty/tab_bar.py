def draw_title(data):
    from kitty.fast_data_types import get_boss, truncate_point_for_length, wcswidth

    boss = get_boss()
    tab = boss.tab_for_id(data["tab_id"])
    title = tab.name if tab else ""
    if not title:
        path = data["tab"].active_wd.rstrip("/")
        title = path.rsplit("/", 1)[-1] or "/"
    marker = "Z " if data["layout_name"] == "stack" and data["num_windows"] > 1 else ""
    title = f'{data["index"]}: {marker}{title}'
    window = tab.active_window if tab is not None and tab is boss.active_tab else None
    if window is None:
        return title

    pane_id = f"#{window.id}"
    suffix = f" · {pane_id}"
    limit = data["max_title_length"]
    if limit > 0:
        available = limit - wcswidth(suffix)
        if available <= 0:
            return pane_id
        if wcswidth(title) > available:
            title = title[:truncate_point_for_length(title, available - 1)] + "…"
    return title + suffix
