-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here

local opt = vim.opt

-- 4-space indentation (LazyVim defaults to 2)
opt.shiftwidth = 4
opt.tabstop = 4
opt.softtabstop = 4

-- No backup or swap files
opt.backup = false
opt.writebackup = false
opt.swapfile = false
