local wezterm = require("wezterm")
local key_binding = require("key_binding")
local keys = key_binding.Keys()
local mouse_bindings = require("mouse_binding").MouseBindings()
local config = wezterm.config_builder()
require("tab_bar").apply(config)
config.font_size = 16
config.font = wezterm.font("Maple Mono Normal NF CN")
config.leader = { key = "`", mods = "ALT", timeout_milliseconds = 1000 }

config.keys = keys
config.mouse_bindings = mouse_bindings

-- config.color_scheme = "Catppuccin Mocha"
-- config.color_scheme = "Dracula (Gogh)"
-- config.color_scheme = "Catppuccin Latte"
config.color_scheme = "Sakura"
config.color_scheme = "Google Dark (Gogh)"
-- config.color_scheme = "SynthwaveAlpha"
config.tab_bar_at_bottom = true
config.default_cursor_style = "SteadyBar"
config.enable_scroll_bar = true
-- config.window_background_image = "/Users/homantix/Pictures/wallpaper/wallhaven-j3dgmy.jpg"
--
-- config.background = {
-- 	{
-- 		source = {
-- 			-- File = "/Users/homantix/Pictures/wallpaper/wallhaven-6dr5rl.jpg",
-- 			-- File = "/Users/homantix/Pictures/wallpaper/wallhaven-zpxzrj.png",
-- 		},
-- 		-- width = "100%",
-- 		height = "100%",
-- 		-- opacity = 0.9,
-- 		hsb = {
-- 			hue = 1.0,
-- 			saturation = 1.0,
-- 			brightness = 0.2,
-- 		},
-- 	},
-- }
--
-- https://github.com/wez/wezterm/discussions/4728
local is_darwin = wezterm.target_triple:find("darwin") ~= nil
local is_linux = wezterm.target_triple:find("linux") ~= nil
local is_windows = wezterm.target_triple:find("windows") ~= nil
if is_darwin then
	local macos_keys = key_binding.MacOSKeys()
	for i = 1, #macos_keys do
		config.keys[#config.keys + 1] = macos_keys[i]
	end
end

if is_windows then
	config.default_domain = "WSL:Ubuntu-20.04"
end
if is_linux then
	wezterm.on("gui-startup", key_binding.work_workspace)
end

if is_darwin then
	wezterm.on("gui-startup", key_binding.work_workspace)
end

wezterm.on("augment-command-palette", function(window, pane)
	return {
		{
			brief = "Broadcast command to all panes",
			action = require("custom_event").BroadcastCommand(),
		},
	}
end)

return config
