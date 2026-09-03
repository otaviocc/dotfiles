-- init.lua for NeoVim
--
-- A single-file config on Neovim's built-in `vim.pack` manager. Requires
-- Neovim >= 0.12 for `vim.pack`, `vim.lsp.enable` + the `lsp/` directory,
-- `vim.lsp.completion` and `vim.opt.winborder`.

-- Leader must be set before any mapping is created: <leader> is expanded when
-- the mapping is defined, not when it fires.
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- Environment settings
vim.opt.compatible = false
vim.opt.encoding = "utf-8"
vim.cmd("filetype plugin indent on")
vim.cmd("syntax enable")

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
vim.opt.backspace = { "indent", "eol", "start" }
vim.opt.complete:append("kspell")
vim.opt.wrap = true

-- Persistent undo across sessions.
vim.opt.undofile = true

-- Always reserve the sign column so LSP diagnostics don't shift text as you
-- type, and give floats (hover, signature help) a visible edge.
vim.opt.signcolumn = "yes"
vim.opt.winborder = "rounded"

-- Bare `nvim` in a directory holding a Session.vim restores that layout.
local function source_local_session()
    if vim.g.local_session_loaded or vim.fn.argc() ~= 0 then
        return
    end

    local cwd = vim.uv.cwd()
    if not cwd then
        return
    end

    local session = vim.fs.joinpath(cwd, "Session.vim")
    if vim.fn.filereadable(session) == 1 then
        vim.g.local_session_loaded = true
        vim.cmd.source(vim.fn.fnameescape(session))
    end
end

vim.api.nvim_create_autocmd("VimEnter", {
    group = vim.api.nvim_create_augroup("local_session_auto_source", { clear = true }),
    once = true,
    callback = source_local_session,
})

-- Plugins ------------------------------------------------------------------
-- `vim.pack` records revisions in nvim-pack-lock.json, which is tracked in
-- this repo. Never hand-edit that file; see `:h vim.pack-lockfile`.
vim.pack.add({
    { src = "https://github.com/rebelot/kanagawa.nvim" },
    { src = "https://github.com/nvim-lua/plenary.nvim" },
    { src = "https://github.com/echasnovski/mini.nvim" },
    -- Deliberately unpinned: the 0.1.8 tag predates Neovim 0.12 and calls
    -- vim.treesitter.language.ft_to_lang (removed) plus nvim-treesitter's
    -- master-branch `configs` module, so its file previewer throws. Master
    -- uses vim.treesitter.language.get_lang and needs no nvim-treesitter at
    -- all. nvim-pack-lock.json pins the revision, so a `version` here would
    -- buy staleness rather than reproducibility.
    { src = "https://github.com/nvim-telescope/telescope.nvim" },
    { src = "https://github.com/nvim-treesitter/nvim-treesitter", version = "main" },
    { src = "https://github.com/neovim/nvim-lspconfig" },
    { src = "https://github.com/mason-org/mason.nvim" },
    { src = "https://github.com/stevearc/oil.nvim" },
    { src = "https://github.com/stevearc/conform.nvim" },
})

-- Color scheme -------------------------------------------------------------
-- Dragon is the warm, near-monochrome variant; see docs/palette.md, the
-- source of truth for every colour in this repo. Deliberately opaque, like
-- every other tool here, rather than transparent.
vim.o.background = "dark"
require("kanagawa").setup({
    theme = "dragon",
    background = { dark = "dragon" },
})
vim.cmd.colorscheme("kanagawa-dragon")

-- mini.nvim ----------------------------------------------------------------
-- One plugin, several independent modules. Set up before oil and telescope so
-- the nvim-web-devicons mock is in place before anything renders an icon.

-- Icons: replaces nvim-web-devicons outright. The mock keeps plugins that
-- still `require("nvim-web-devicons")` working.
require("mini.icons").setup()
MiniIcons.mock_nvim_web_devicons()

-- Extended a/i textobjects: arguments (a), balanced brackets (b), quotes (q),
-- function calls (f), tags (t). Deliberately no gen_spec.treesitter specs for
-- function *definitions* -- nvim-treesitter's main branch ships no textobjects
-- queries, so those would silently never match.
require("mini.ai").setup({ n_lines = 500 })

-- Surroundings: sa add, sd delete, sr replace, sf/sF find, sh highlight.
-- Note this takes over `s` in normal mode (was substitute-character; use `cl`).
require("mini.surround").setup()

-- Autopairs.
require("mini.pairs").setup()

-- Git diff: signs in the gutter, plus a toggleable inline overlay. The
-- default style is "number" (it tints the line number) whenever 'number' is
-- set; force signs instead, since 'signcolumn' is already reserved above.
require("mini.diff").setup({
    view = {
        style = "sign",
        signs = { add = "+", change = "~", delete = "_" },
    },
})

-- [b/]b between buffers, plus the same pattern for diagnostics, quickfix,
-- comments, conflicts, undo states, oldfiles and more. [B/]B for first/last.
require("mini.bracketed").setup()

-- Close a buffer without collapsing the window layout, which :bdelete does.
require("mini.bufremove").setup()

-- Highlight TODO/FIXME/HACK/NOTE, and render hex colours as inline swatches.
local hipatterns = require("mini.hipatterns")
hipatterns.setup({
    highlighters = {
        fixme = { pattern = "%f[%w]()FIXME()%f[%W]", group = "MiniHipatternsFixme" },
        hack = { pattern = "%f[%w]()HACK()%f[%W]", group = "MiniHipatternsHack" },
        todo = { pattern = "%f[%w]()TODO()%f[%W]", group = "MiniHipatternsTodo" },
        note = { pattern = "%f[%w]()NOTE()%f[%W]", group = "MiniHipatternsNote" },
        hex_color = hipatterns.gen_highlighter.hex_color(),
    },
})

-- Show the available next keys after a prefix, like which-key.
local clue = require("mini.clue")
clue.setup({
    triggers = {
        { mode = "n", keys = "<Leader>" },
        { mode = "x", keys = "<Leader>" },
        { mode = "n", keys = "g" },
        { mode = "x", keys = "g" },
        { mode = "n", keys = "z" },
        { mode = "x", keys = "z" },
        -- mini.surround lives under `s`; without this its verbs are invisible.
        { mode = "n", keys = "s" },
        { mode = "x", keys = "s" },
        { mode = "n", keys = "[" },
        { mode = "n", keys = "]" },
        { mode = "n", keys = "'" },
        { mode = "n", keys = "`" },
        { mode = "n", keys = '"' },
        { mode = "n", keys = "<C-w>" },
        { mode = "i", keys = "<C-r>" },
    },
    clues = {
        -- Group labels for the <Leader> submenus.
        { mode = "n", keys = "<Leader>b", desc = "+buffer" },
        { mode = "n", keys = "<Leader>f", desc = "+find" },
        { mode = "n", keys = "<Leader>g", desc = "+git" },
        { mode = "n", keys = "<Leader>l", desc = "+lsp" },
        clue.gen_clues.builtin_completion(),
        clue.gen_clues.g(),
        clue.gen_clues.marks(),
        clue.gen_clues.registers(),
        clue.gen_clues.windows(),
        clue.gen_clues.z(),
    },
    window = { config = { border = "rounded" } },
})

-- Treesitter ---------------------------------------------------------------
-- The `main` branch has no `ensure_installed` and does not enable
-- highlighting on its own: parsers are installed explicitly and
-- `vim.treesitter.start()` is called per buffer.
local parsers = {
    "bash",
    "dockerfile",
    "javascript",
    "json",
    "kotlin",
    "lua",
    "markdown",
    "markdown_inline",
    "python",
    "ruby",
    "rust",
    "swift",
    "toml",
    "tsx",
    "typescript",
    "yaml",
}

require("nvim-treesitter").install(parsers)

vim.api.nvim_create_autocmd("FileType", {
    group = vim.api.nvim_create_augroup("treesitter_start", { clear = true }),
    pattern = {
        "bash",
        "dockerfile",
        "javascript",
        "json",
        "kotlin",
        "lua",
        "markdown",
        "python",
        "ruby",
        "rust",
        "sh",
        "swift",
        "toml",
        "typescript",
        "typescriptreact",
        "yaml",
    },
    callback = function()
        -- pcall: a filetype whose parser has not finished installing yet
        -- should not abort the autocmd with an error.
        pcall(vim.treesitter.start)
    end,
})

-- LSP ----------------------------------------------------------------------
-- Neovim's built-in completion, driven straight off the LSP client: no
-- completion plugin. Widening triggerCharacters to every printable ASCII
-- character is what makes it fire as you type rather than only after `.`.
vim.api.nvim_create_autocmd("LspAttach", {
    group = vim.api.nvim_create_augroup("lsp_native_completion", { clear = true }),
    callback = function(args)
        local client = assert(vim.lsp.get_client_by_id(args.data.client_id))
        if client:supports_method("textDocument/completion") then
            local chars = {}
            for i = 32, 126 do
                table.insert(chars, string.char(i))
            end
            client.server_capabilities.completionProvider.triggerCharacters = chars
            vim.lsp.completion.enable(true, client.id, args.buf, { autotrigger = true })
        end
    end,
})

vim.opt.completeopt:append({ "menuone", "noselect", "popup" })

require("mason").setup()

-- Servers resolve from nvim-lspconfig unless overridden by a file in `lsp/`.
-- Install them with `:Mason`; sourcekit ships with the Xcode toolchain.
-- No kotlin_language_server (needs a JVM) and no ruby_lsp (needs Ruby >= 3.0;
-- this machine has the 2.6 system Ruby). Treesitter still highlights both.
vim.lsp.enable({
    "bashls",
    "lua_ls",
    "pyright",
    "ruff",
    "rust_analyzer",
    "sourcekit",
    "ts_ls",
})

-- Formatting ---------------------------------------------------------------
require("conform").setup({
    format_on_save = {
        timeout_ms = 1000,
        lsp_format = "fallback",
    },
    formatters_by_ft = {
        json = { "prettier" },
        lua = { "stylua" },
        markdown = { "prettier" },
        python = { "ruff_format" },
        rust = { "rustfmt" },
        sh = { "shfmt" },
        yaml = { "prettier" },
    },
})

-- File explorer ------------------------------------------------------------
require("oil").setup({
    lsp_file_methods = {
        enabled = true,
        timeout_ms = 1000,
        autosave_changes = true,
    },
    columns = {
        "icon",
    },
    float = {
        max_width = 0.3,
        max_height = 0.6,
        border = "rounded",
    },
})

-- Telescope ----------------------------------------------------------------
-- `hidden` belongs under `pickers.find_files`, not `defaults` -- it is a
-- picker option, and putting it in the wrong place is a mistake this config
-- has already made once.
local telescope = require("telescope")
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
            "%.DS_Store$",
        },
    },
    pickers = {
        find_files = {
            hidden = true,
        },
    },
})

-- Keymaps ------------------------------------------------------------------
local map = vim.keymap.set

-- Paste toggle (F12)
map("n", "<F12>", ":set invpaste<CR>", { silent = true })
map("i", "<F12>", "<C-O>:set invpaste<CR>", { silent = true })

-- Telescope
map("n", "<C-p>", "<cmd>Telescope find_files<cr>", { desc = "Find files" })
map("n", "<leader>fg", "<cmd>Telescope live_grep<cr>", { desc = "Live grep" })
map("n", "<leader>fb", "<cmd>Telescope buffers<cr>", { desc = "Find buffers" })

-- File explorer and formatting
map("n", "<leader>e", "<cmd>Oil<cr>", { desc = "Open parent directory" })
map("n", "<leader>lf", function()
    require("conform").format({ async = true, lsp_format = "fallback" })
end, { desc = "Format current buffer" })
map("n", "<leader>gd", function()
    require("mini.diff").toggle_overlay()
end, { desc = "Toggle git diff overlay" })
map("n", "<leader>a", "<cmd>edit #<cr>", { desc = "Alternate buffer" })
map("n", "<leader>bd", function()
    require("mini.bufremove").delete()
end, { desc = "Delete buffer, keep layout" })

-- Keep the cursor centred when jumping, and the selection when indenting.
map("n", "n", "nzzzv")
map("n", "N", "Nzzzv")
map("n", "<C-d>", "<C-d>zz")
map("n", "<C-u>", "<C-u>zz")
map("n", "<Esc>", "<cmd>nohlsearch<CR>", { silent = true })
map("v", "<", "<gv", { noremap = true, silent = true })
map("v", ">", ">gv", { noremap = true, silent = true })

-- Autocmds -----------------------------------------------------------------

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
