-- bootstrap lazy.nvim, LazyVim and your plugins
require("config.lazy")
--
-- 将这段代码加入你的 init.lua
local original_set_extmark = vim.api.nvim_buf_set_extmark
vim.api.nvim_buf_set_extmark = function(buffer, ns_id, line, col, opts)
  if opts and type(opts.hl_group) == "table" then
    -- 打印一下是谁在捣乱（可选）
    -- print("Fixed invalid hl_group table: ", vim.inspect(opts.hl_group))

    -- 强制取数组中的第一个高亮组，确保不报错
    opts.hl_group = opts.hl_group[0]
  end
  return original_set_extmark(buffer, ns_id, line, col, opts)
end
