-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

local opts = {
  noremap = true,
  silent = true,
}
--vim.keymap.set({ "n", "i", "c" }, "<C-a>", "<Home>", opts)
--vim.keymap.set({ "n", "i", "c" }, "<C-e>", "<End>", opts)
vim.keymap.set("n", "<S-j>", "<cmd>BufferLineCyclePrev<cr>", opts)
vim.keymap.set("n", "<S-k>", "<cmd>BufferLineCycleNext<cr>", opts)
vim.keymap.set("n", "<CR>", "o<ESC>", opts)
vim.keymap.set("n", "<S-CR>", "O<ESC>", opts)
vim.keymap.set({ "n" }, "<D-Left>", "^", opts)
vim.keymap.set({ "n" }, "<D-Right>", "$", opts)
vim.keymap.set({ "i", "c" }, "<D-Left>", "<Home>", opts)
vim.keymap.set({ "i", "c" }, "<D-Right>", "<End>", opts)
vim.keymap.set({ "n", "i", "v" }, "<D-s>", "<cmd>write<cr>", { desc = "Save file", silent = true })
vim.keymap.del({ "n", "t" }, "<C-/>", opts)

-- local toggle_term = function()
--   local current_file_dir = vim.fn.expand("%:p:h")
--   local cwd = (current_file_dir and current_file_dir ~= "" and current_file_dir ~= ".") and current_file_dir
--     or LazyVim.root() -- 或者使用 vim.loop.cwd() 来获取当前 Neovim 的工作目录
--   Snacks.terminal(nil, { cwd = cwd })
-- end

local toggle_term = function()
  -- 1. 获取用户输入的数字前缀 (例如 2<C-`> 中的 2)
  -- 如果没有输入数字，count 为 0，我们默认给它 ID "1"
  local count = vim.v.count
  local id = (count > 0) and tostring(count) or "1"

  -- 2. 判断当前 buffer 是否是终端
  local is_term = vim.bo.buftype == "terminal"

  -- 3. 如果当前已经在终端里，且我们想切换/关闭它
  if is_term then
    vim.api.nvim_win_close(0, true)
    return
  end

  -- for _, term in pairs(Snacks.terminal.list()) do
  --   local print_string = string.format("term.buf = %d, term.id = %d", term.buf, term.id)
  --   local meta = vim.b[term.buf].snacks_terminal
  --   print_string = print_string .. " meta.id = " .. meta.id
  --   vim.notify(print_string, "debug")
  -- end
  local find_term_by_id = function(target_id)
    for _, term in pairs(Snacks.terminal.list()) do
      local meta = vim.b[term.buf].snacks_terminal
      -- vim.notify(vim.inspect(meta), "debug")
      if tostring(meta.id) == target_id then
        return term
      end
    end
    return nil
  end

  local existing_term = find_term_by_id(id)
  if existing_term then
    existing_term:toggle()
    return
  end
  -- 4. 确定工作目录
  local current_file_dir = vim.fn.expand("%:p:h")
  local cwd = (current_file_dir and current_file_dir ~= "" and current_file_dir ~= ".") and current_file_dir
    or LazyVim.root()

  -- 5. 调用 Snacks 终端，并在 title 中显示 ID
  Snacks.terminal.toggle(nil, {
    id = id,
    cwd = cwd,
    win = {
      position = "float",
      border = "rounded",
      -- 动态显示标题：例如 " Terminal #1 " 或 " Terminal #2 "
      title = " 󰆍 Terminal #" .. id .. " ",
      title_pos = "center",
      -- 可选：给不同 ID 的窗口设置不同的透明度或样式
      -- winblend = 100,
    },
  })
end

vim.keymap.set({ "n", "t" }, "<C-`>", toggle_term, { desc = "Terminal (Root Dir)" })
-- vim.keymap.set("t", "<C-`>", "<cmd>close<cr>", opts)

local function open_typora()
  -- 获取当前文件的完整路径
  local filepath = vim.fn.expand("%")
  -- 构建外部命令。使用 'typora' 和文件的完整路径。
  -- ' & ' 用于在后台运行命令 (适用于 Unix/Linux/macOS)
  local command = "Typora " .. filepath .. "&"
  if vim.fn.has("mac") == 1 or vim.fn.has("darwin") == 1 then
    command = "open -a Typora " .. filepath
  end
  -- 在 shell 中执行命令
  vim.fn.system(command)
end

vim.keymap.set("n", "<leader>ot", open_typora, { desc = "Open current file in Typora" })
--
-- 映射为 <leader>ir (Insert Read)
vim.keymap.set("n", "<leader>ir", function()
  -- 获取用户输入的命令
  local cmd = vim.fn.input("Run command: ")
  if cmd ~= "" then
    -- 执行命令并去除末尾换行符
    local result = vim.fn.system(cmd):gsub("%\n$", "")
    -- 在光标处插入内容
    vim.api.nvim_put({ result }, "c", true, true)
  end
end, { desc = "Run command and insert at cursor" })

vim.keymap.set("n", "<F2>", "@@", { desc = "执行上一次宏" })

vim.keymap.set("n", "<leader>of", function()
  local s = string.format("%s\n%s", vim.fn.expand("%:p"), vim.fn.expand("%:t"))
  vim.notify(s)
  vim.fn.setreg("+", vim.fn.expand("%:p"))
end, { desc = "显示当前文件路径" })

vim.keymap.set("n", "<leader>da", function()
  local result = tostring(os.date("%Y-%m-%d"))
  vim.api.nvim_put({ result }, "c", true, true)
end)

-- 插入当前文件名（带后缀）
vim.keymap.set("n", "<leader>if", function()
  local filename = vim.fn.expand("%:t")
  vim.api.nvim_put({ filename }, "c", true, true)
end, { desc = "Insert current filename" })
