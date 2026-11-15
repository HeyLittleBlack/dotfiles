return {
  "keaising/im-select.nvim",
  enabled = vim.fn.has("macunix") == 1,
  main = "im_select",
  opts = {
    default_command = "macism",
    default_im_select = "com.apple.keylayout.UnicodeHexInput",
    set_default_events = { "InsertLeave", "CmdlineLeave", "FocusGained" },
    set_previous_events = {},
    async_switch_im = false,
  },
  config = function(_, opts)
    -- The plugin does not reset its completion flag between synchronous switches.
    vim.api.nvim_create_autocmd(opts.set_default_events, {
      group = vim.api.nvim_create_augroup("im_select_completion", { clear = true }),
      callback = function()
        require("im_select").closed = false
      end,
    })
    require("im_select").setup(opts)

    -- Always select WeChat instead of restoring the previous input source.
    vim.api.nvim_create_autocmd({ "InsertEnter", "FocusLost", "VimLeavePre", "CmdlineEnter" }, {
      group = vim.api.nvim_create_augroup("wechat_input_source", { clear = true }),
      callback = function(event)
        if event.event == "CmdlineEnter" and event.match ~= "/" and event.match ~= "?" then
          return
        end
        -- shortcut: disable macism's focus workaround to avoid FocusGained switching back to English; revisit if WeChat fails to activate.
        vim.fn.system({ "macism", "com.tencent.inputmethod.wetype.pinyin", "0" })
        if vim.v.shell_error ~= 0 then
          vim.notify("Failed to switch to WeChat Input with macism", vim.log.levels.WARN)
        end
      end,
    })
  end,
}
