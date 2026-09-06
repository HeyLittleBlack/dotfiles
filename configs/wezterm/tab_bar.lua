local wezterm = require("wezterm")

local M = {}
local right_arrow = utf8.char(0xe0b0)

local colors = {
	bar = "#151821",
	active = "#2878d0",
	inactive = "#343b4c",
	hover = "#465168",
	text = "#f2f4f8",
}

function M.apply(config)
	config.use_fancy_tab_bar = false
	config.tab_max_width = 48
	config.colors = config.colors or {}
	config.colors.tab_bar = {
		background = colors.bar,
		new_tab = { bg_color = colors.bar, fg_color = colors.text },
		new_tab_hover = { bg_color = colors.hover, fg_color = colors.text },
	}

	wezterm.on("format-tab-title", function(tab, tabs, _, _, hover, max_width)
		local background = tab.is_active and colors.active or (hover and colors.hover or colors.inactive)
		local title = tab.tab_title
		if title == "" then
			local cwd = tab.active_pane.current_working_dir
			local path = cwd and cwd.file_path or tab.active_pane.title
			title = path:gsub("[/\\]+$", ""):match("([^/\\]+)$") or path
		end
		title = string.format("%d: %s", tab.tab_index + 1, title)
		title = wezterm.truncate_right(title, max_width - 3)

		local next_tab = tabs[tab.tab_index + 2]
		local next_background = next_tab and (next_tab.is_active and colors.active or colors.inactive) or colors.bar

		return {
			{ Background = { Color = background } },
			{ Foreground = { Color = colors.text } },
			{ Text = " " .. title .. " " },
			{ Background = { Color = next_background } },
			{ Foreground = { Color = background } },
			{ Text = right_arrow },
		}
	end)
end

return M
