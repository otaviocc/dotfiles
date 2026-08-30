-- Vesper colorscheme (matches ghostty/tig/lazygit/hunk/vigia/opencode/zsh)

vim.cmd("hi clear")
if vim.fn.exists("syntax_on") == 1 then
    vim.cmd("syntax reset")
end
vim.o.termguicolors = true
vim.o.background = "dark"
vim.g.colors_name = "vesper"

local c = {
    bg = "#101010",
    bg_panel = "#161616",
    bg_selection = "#232323",
    fg = "#FFFFFF",
    muted = "#505050",
    muted_text = "#7E7E7E",
    subtle = "#1C1C1C",
    red = "#FF8080",
    green = "#90B99F",
    yellow = "#FFC799",
    blue = "#F591B2",
    magenta = "#ECAAD6",
    cyan = "#B9AEDA",
}

local function hi(group, opts)
    vim.api.nvim_set_hl(0, group, opts)
end

-- Editor
hi("Normal", { fg = c.fg, bg = c.bg })
hi("NormalFloat", { fg = c.fg, bg = c.bg_panel })
hi("FloatBorder", { fg = c.muted, bg = c.bg_panel })
hi("Cursor", { fg = c.bg, bg = c.fg })
hi("CursorLine", { bg = c.subtle })
hi("CursorLineNr", { fg = c.yellow, bold = true })
hi("LineNr", { fg = c.muted })
hi("Visual", { bg = c.bg_selection })
hi("Search", { fg = c.bg, bg = c.yellow })
hi("IncSearch", { fg = c.bg, bg = c.magenta })
hi("StatusLine", { fg = c.fg, bg = c.subtle })
hi("StatusLineNC", { fg = c.muted, bg = c.subtle })
hi("WinSeparator", { fg = c.muted })
hi("VertSplit", { fg = c.muted })
hi("Pmenu", { fg = c.fg, bg = c.bg_panel })
hi("PmenuSel", { fg = c.bg, bg = c.blue })
hi("PmenuSbar", { bg = c.subtle })
hi("PmenuThumb", { bg = c.muted })
hi("SignColumn", { bg = c.bg })
hi("ColorColumn", { bg = c.subtle })
hi("MatchParen", { fg = c.yellow, bold = true })
hi("NonText", { fg = c.muted })
hi("Whitespace", { fg = c.muted })
hi("Folded", { fg = c.muted_text, bg = c.subtle })
hi("Directory", { fg = c.blue })
hi("Title", { fg = c.blue, bold = true })

-- Diagnostics
hi("DiagnosticError", { fg = c.red })
hi("DiagnosticWarn", { fg = c.yellow })
hi("DiagnosticInfo", { fg = c.blue })
hi("DiagnosticHint", { fg = c.cyan })

-- Diff
hi("DiffAdd", { fg = c.green, bg = c.bg })
hi("DiffChange", { fg = c.yellow, bg = c.bg })
hi("DiffDelete", { fg = c.red, bg = c.bg })
hi("DiffText", { fg = c.blue, bg = c.bg })

-- Syntax
hi("Comment", { fg = c.muted_text, italic = true })
hi("Constant", { fg = c.yellow })
hi("String", { fg = c.green })
hi("Character", { fg = c.green })
hi("Number", { fg = c.yellow })
hi("Boolean", { fg = c.magenta })
hi("Float", { fg = c.yellow })
hi("Identifier", { fg = c.fg })
hi("Function", { fg = c.blue })
hi("Statement", { fg = c.magenta })
hi("Conditional", { fg = c.magenta })
hi("Repeat", { fg = c.magenta })
hi("Label", { fg = c.magenta })
hi("Operator", { fg = c.red })
hi("Keyword", { fg = c.magenta })
hi("Exception", { fg = c.red })
hi("PreProc", { fg = c.cyan })
hi("Include", { fg = c.cyan })
hi("Define", { fg = c.cyan })
hi("Macro", { fg = c.cyan })
hi("Type", { fg = c.cyan })
hi("StorageClass", { fg = c.cyan })
hi("Structure", { fg = c.cyan })
hi("Typedef", { fg = c.cyan })
hi("Special", { fg = c.magenta })
hi("SpecialChar", { fg = c.magenta })
hi("Tag", { fg = c.blue })
hi("Delimiter", { fg = c.muted_text })
hi("SpecialComment", { fg = c.muted_text })
hi("Underlined", { fg = c.blue, underline = true })
hi("Error", { fg = c.red })
hi("Todo", { fg = c.bg, bg = c.yellow, bold = true })

-- Treesitter
hi("@variable", { link = "Identifier" })
hi("@function", { link = "Function" })
hi("@keyword", { link = "Keyword" })
hi("@string", { link = "String" })
hi("@comment", { link = "Comment" })
hi("@type", { link = "Type" })
hi("@constant", { link = "Constant" })
hi("@number", { link = "Number" })
hi("@boolean", { link = "Boolean" })
hi("@operator", { link = "Operator" })
hi("@punctuation", { fg = c.muted_text })

-- Gitsigns
hi("GitSignsAdd", { fg = c.green })
hi("GitSignsChange", { fg = c.yellow })
hi("GitSignsDelete", { fg = c.red })

-- Telescope
hi("TelescopeBorder", { fg = c.muted, bg = c.bg_panel })
hi("TelescopeSelection", { bg = c.bg_selection })
hi("TelescopeMatching", { fg = c.yellow, bold = true })

-- Dashboard
hi("Dashboard", { fg = c.fg, bg = c.bg })
hi("DashboardHeader", { fg = c.yellow })
hi("DashboardCenter", { fg = c.fg })
hi("DashboardDesc", { fg = c.fg })
hi("DashboardIcon", { fg = c.yellow })
hi("DashboardShortCut", { fg = c.yellow })
hi("DashboardShortCutIcon", { fg = c.yellow })
hi("DashboardKey", { fg = c.yellow })
hi("DashboardFooter", { fg = c.muted_text, italic = true })
