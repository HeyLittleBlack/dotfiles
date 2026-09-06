local wezterm = require("wezterm")
local M = {}

local choices = {
	{
		id = "/Users/homantix/self/notes/",
		label = "MacOS_ws",
	},
	{
		id = "/home/homantix/.config/wezterm",
		label = "Linux_ws",
	},
}

local layouts = {}

layouts[choices[1].label] = {
	{
		tabname = "configwez",
		cwd = wezterm.config_dir,
	},
	{
		tabname = "notes",
		cwd = "/Users/homantix/self/notes",
	},
	{
		tabname = "coding",
		cwd = "/Users/homantix/self/codes/",
	},
}

layouts[choices[2].label] = {
	{
		tabname = "configwez",
		cwd = wezterm.config_dir,
	},
	{
		tabname = "notes",
		cwd = "/mnt/work/Notes/MyNotes/",
	},
	{
		tabname = "carlaue5",
		cwd = "/mnt/work/CarlaOfficial/carla/",
	},
}

function M.bind()
	return wezterm.action_callback(function(window, pane)
		window:perform_action(
			wezterm.action.InputSelector({
				title = "Choose Workspace",
				choices = choices,
				action = wezterm.action_callback(function(new_window, new_pane, id, label)
					-- new_window's type is wezterm.window, not wezterm.mux_window
					-- new_pane:send_text(id .. label)
					new_window:perform_action(
						wezterm.action.SwitchToWorkspace({
							name = label,
							spawn = {
								label = label,
								cwd = id,
							},
						}),
						new_pane
					)
					-- new_window is likely not spawn window
					new_window:active_tab():set_title(layouts[label][1].tabname)
					for i = 2, #layouts[label] do
						local layout = layouts[label][i]
						local n_tab, _pane, _window = new_window:mux_window():spawn_tab({ cwd = layout.cwd })
						n_tab:set_title(layout.tabname)
					end
				end),
			}),
			pane
		)
	end)
end

function M.BroadcastCommand()
	return wezterm.action_callback(function(window, pane)
		window:perform_action(
			wezterm.action.PromptInputLine({
				description = "Broadcast command to all panes:",
				action = wezterm.action_callback(function(win, p, line)
					if line and line ~= "" then
						local active_tab = win:active_tab()
						for _, target_pane in ipairs(active_tab:panes()) do
							target_pane:send_text(line .. "\r")
						end
					end
				end),
			}),
			pane
		)
	end)
end

M.choices = choices
M.layouts = layouts
return M
