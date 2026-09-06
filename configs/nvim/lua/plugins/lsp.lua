return {
  {
    "neovim/nvim-lspconfig",
    opts = function()
      local keys = require("lazyvim.plugins.lsp.keymaps").get()
      keys[#keys + 1] = { "K", false }
    end,
  },
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        pyright = {
          settings = {
            python = {
              analysis = {
                typeCheckingMode = "off",
              },
            },
          },
        },
      },
    },
  },
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        clangd = {
          cmd = {
            "clangd",
            "--fallback-style=webkit",
          },
          on_attach = function(client, bufnr)
            local util = require("lspconfig.util")
            local fname = vim.api.nvim_buf_get_name(bufnr)

            -- 再次检查标记文件
            if util.root_pattern(".stop_lsp", ".no-lsp")(fname) then
              -- 立即清空当前 buffer 的所有诊断信息（消灭红线）
              vim.diagnostic.reset(nil, bufnr)
              -- 立即断开这个 LSP 客户端的连接
              vim.schedule(function()
                client.stop()
              end)
              return false
            end
          end,
        },
      },
    },
  },
}
