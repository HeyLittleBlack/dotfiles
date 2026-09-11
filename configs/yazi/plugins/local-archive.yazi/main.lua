local function parent(path)
	if path == "/" then
		return "/"
	end
	local result = path:match("^(.*)/[^/]+$")
	return result ~= "" and result or "/"
end

local function common_dir(items)
	local common = items[1].is_dir and items[1].path or parent(items[1].path)
	for i = 2, #items do
		local path = items[i].is_dir and items[i].path or parent(items[i].path)
		while common ~= "/" and path ~= common and path:sub(1, #common + 1) ~= common .. "/" do
			common = parent(common)
		end
	end
	return common
end

local function layout(items)
	local root = common_dir(items)
	if root == "/" then
		return nil
	end

	local base = parent(root)
	local paths = {}
	for _, item in ipairs(items) do
		paths[#paths + 1] = item.path:sub(#base + (base == "/" and 1 or 2))
	end
	table.sort(paths)

	local filtered = {}
	for _, path in ipairs(paths) do
		local covered = false
		for _, parent_path in ipairs(filtered) do
			if path == parent_path or path:sub(1, #parent_path + 1) == parent_path .. "/" then
				covered = true
				break
			end
		end
		if not covered then
			filtered[#filtered + 1] = path
		end
	end

	return base, filtered, root:match("([^/]+)$")
end

if os.getenv("YAZI_ARCHIVE_SELF_TEST") then
	local base, paths, name = layout({
		{ path = "/work/project/src/a.lua", is_dir = false },
		{ path = "/work/project/tests/a_test.lua", is_dir = false },
	})
	assert(base == "/work" and name == "project")
	assert(paths[1] == "project/src/a.lua" and paths[2] == "project/tests/a_test.lua")
	assert(layout({ { path = "/a", is_dir = false }, { path = "/b", is_dir = false } }) == nil)
	local _, nested = layout({
		{ path = "/work/project/a", is_dir = true },
		{ path = "/work/project/a-file", is_dir = false },
		{ path = "/work/project/a/x", is_dir = false },
	})
	assert(#nested == 2 and nested[1] == "project/a" and nested[2] == "project/a-file")
	print("local-archive self-test passed")
	return
end

local selected_or_hovered = ya.sync(function()
	local tab = cx.active
	local items = {}
	for _, file in pairs(tab.selected) do
		items[#items + 1] = { path = tostring(file.url), is_dir = file.cha.is_dir }
	end
	if #items == 0 and tab.current.hovered then
		local file = tab.current.hovered
		items[1] = { path = tostring(file.url), is_dir = file.cha.is_dir }
	end
	return items, tostring(tab.current.cwd)
end)

local function notify(content, level)
	ya.notify({ title = "Archive", content = content, level = level, timeout = 5 })
end

local function command_exists(command)
	local ok = os.execute("command -v " .. command .. " >/dev/null 2>&1")
	return ok == true or ok == 0
end

return {
	entry = function()
		local items, output_dir = selected_or_hovered()
		if #items == 0 then
			return notify("No files selected", "warn")
		end

		local base, paths, root_name = layout(items)
		if not base then
			return notify("Selected files have no safe common directory", "error")
		end

		local output_name, event = ya.input({
			title = "Create ZIP:",
			value = root_name .. ".zip",
			pos = { "top-center", y = 3, w = 50 },
		})
		if event ~= 1 then
			return
		end
		if output_name == "" or output_name == "." or output_name == ".." or output_name:find("/", 1, true) then
			return notify("Invalid archive name", "error")
		end
		if not output_name:lower():match("%.zip$") then
			output_name = output_name .. ".zip"
		end

		local temporary_dir, temporary_err = fs.unique(
			"dir",
			Url(os.getenv("TMPDIR") or "/tmp"):join("yazi-local-archive")
		)
		if not temporary_dir then
			return notify("Failed to create temporary directory: " .. tostring(temporary_err), "error")
		end
		local temporary = temporary_dir:join(output_name)
		local command, arguments
		-- ponytail: argv is enough for normal selections; use a list file if ARG_MAX becomes a real limit.
		if command_exists("zip") then
			command = "zip"
			arguments = { "-r", tostring(temporary), "--", table.unpack(paths) }
		else
			command = command_exists("7zz") and "7zz" or command_exists("7z") and "7z"
			if not command then
				fs.remove("dir_all", temporary_dir)
				return notify("zip or 7zz is required", "error")
			end
			arguments = { "a", "-tzip", "--", tostring(temporary), table.unpack(paths) }
		end

		local output, err = Command(command)
			:arg(arguments)
			:cwd(base)
			:stdout(Command.PIPED)
			:stderr(Command.PIPED)
			:output()
		if not output or output.status.code ~= 0 then
			fs.remove("dir_all", temporary_dir)
			return notify(output and (output.stderr ~= "" and output.stderr or output.stdout) or tostring(err), "error")
		end

		local final, unique_err = fs.unique("file", Url(output_dir):join(output_name))
		if not final then
			fs.remove("dir_all", temporary_dir)
			return notify("Failed to reserve archive name: " .. tostring(unique_err), "error")
		end

		local moved, move_err = fs.rename(temporary, final)
		if not moved and move_err and move_err.kind == "CrossesDevices" then
			moved, move_err = fs.copy(temporary, final)
		end
		fs.remove("dir_all", temporary_dir)
		if not moved then
			fs.remove("file", final)
			return notify("Failed to save archive: " .. tostring(move_err), "error")
		end

		ya.emit("escape", { visual = true })
		notify("Created " .. final.name, "info")
	end,
}
