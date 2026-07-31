-- init.lua for NeoVim

require("config.lazy")

-- Environment settings
vim.opt.compatible = false
vim.opt.encoding = 'utf-8'
vim.cmd('filetype plugin indent on')
vim.cmd('syntax enable')

-- Terminal settings
vim.opt.termguicolors = true
vim.opt.errorbells = false
vim.opt.hlsearch = true
vim.opt.incsearch = true
vim.opt.number = true
vim.opt.showmatch = true
vim.opt.backup = false
vim.opt.writebackup = false
vim.opt.swapfile = false
vim.opt.autoindent = true
vim.opt.smartindent = true
vim.opt.expandtab = true
vim.opt.shiftwidth = 4
vim.opt.tabstop = 4
vim.opt.softtabstop = 4
vim.opt.backspace = { 'indent', 'eol', 'start' }
vim.opt.complete:append('kspell')
vim.opt.wrap = true

-- Paste toggle (F12)
vim.keymap.set('n', '<F12>', ':set invpaste<CR>', { silent = true })
vim.keymap.set('i', '<F12>', '<C-O>:set invpaste<CR>', { silent = true })

-- Git commit messages
vim.api.nvim_create_autocmd("FileType", {
    pattern = "gitcommit",
    callback = function()
        vim.opt_local.textwidth = 72
        vim.opt_local.colorcolumn = "+1"
        vim.opt_local.spell = true
    end,
})

-- Markdown
vim.api.nvim_create_autocmd("FileType", {
    pattern = "markdown",
    callback = function()
        vim.opt_local.wrap = true
        vim.opt_local.spell = true
    end,
})

-- Telescope configuration (modern alternative to ctrlp)
local telescope = require('telescope')
telescope.setup({
    defaults = {
        file_ignore_patterns = {
            "node_modules/.*",
            "_site/.*", 
            "%.git/.*",
            "tmp/.*",
            "%.build/.*",
            "%.o$",
            "%.so$", 
            "%.dat$",
            "%.DS_Store$"
        }
    }
})

-- Telescope keymaps
vim.keymap.set('n', '<C-p>', '<cmd>Telescope find_files<cr>', { desc = 'Find files' })
vim.keymap.set('n', '<leader>fg', '<cmd>Telescope live_grep<cr>', { desc = 'Live grep' })
vim.keymap.set('n', '<leader>fb', '<cmd>Telescope buffers<cr>', { desc = 'Find buffers' })

-- Color scheme
require('themes.default_plus').setup()

