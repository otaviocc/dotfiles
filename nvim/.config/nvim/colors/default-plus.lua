-- Default+ colorscheme
--
-- Ported from the Xcode Font & Color Theme of the same name.
-- Canonical palette: https://github.com/otaviocc/default-plus (palette.yaml)
--
-- Roles follow Xcode, which is NOT the usual terminal convention:
--   comments are GREEN and strings are RED. That inversion is the theme's
--   signature; "fixing" it makes this stop looking like Default+.
--
-- Xcode also unifies the identifiers you declare — types, classes, functions,
-- variables, constants — onto one teal, and puts SDK members on purple. That
-- distinction is project-vs-system, not kind-of-thing, so it is reproduced via
-- the `.builtin` treesitter captures and the LSP `defaultLibrary` modifier.

vim.cmd("hi clear")
if vim.fn.exists("syntax_on") == 1 then
    vim.cmd("syntax reset")
end
vim.o.termguicolors = true
vim.o.background = "dark"
vim.g.colors_name = "default-plus"

local c = {
    bg = "#171717",
    bg_panel = "#111111",
    bg_subtle = "#242424",
    cursor_line = "#26262C",
    selection = "#515B70",
    fg = "#FFFFFF",
    muted = "#4C4C4C",
    muted_text = "#8E8E8E",

    comment = "#2EA85B",
    string = "#FC4651",
    keyword = "#F2248C",
    number = "#FFE76D",
    macro = "#FD8F3F",
    attribute = "#E09D65",
    url = "#4FA5FF",
    declaration = "#35B0D8",
    declaration_type = "#66DAFF",
    project = "#56D0B3",
    system_member = "#AB64FF",
    system_type = "#D0A8FF",

    error = "#F74A4A",
    warning = "#EFB759",
    success = "#41B645",

    diff_add_bg = "#1C3425",
    diff_del_bg = "#452023",
    diff_text_bg = "#1F4A2F",
    muted_green = "#226039",
    muted_red = "#8A2E34",
}

local function hi(group, opts)
    vim.api.nvim_set_hl(0, group, opts)
end

-- ── Editor ──────────────────────────────────────────────────────────────
hi("Normal", { fg = c.fg, bg = c.bg })
hi("NormalFloat", { fg = c.fg, bg = c.bg_panel })
hi("FloatBorder", { fg = c.muted, bg = c.bg_panel })
hi("FloatTitle", { fg = c.declaration, bg = c.bg_panel, bold = true })
hi("Cursor", { fg = c.bg, bg = c.fg })
hi("CursorLine", { bg = c.cursor_line })
hi("CursorColumn", { bg = c.cursor_line })
hi("CursorLineNr", { fg = c.number, bold = true })
hi("LineNr", { fg = c.muted })
hi("Visual", { bg = c.selection })
hi("VisualNOS", { bg = c.selection })
hi("Search", { fg = c.bg, bg = c.number })
hi("IncSearch", { fg = c.bg, bg = c.keyword })
hi("CurSearch", { fg = c.bg, bg = c.keyword })
hi("StatusLine", { fg = c.fg, bg = c.bg_subtle })
hi("StatusLineNC", { fg = c.muted_text, bg = c.bg_panel })
hi("WinSeparator", { fg = c.muted })
hi("VertSplit", { fg = c.muted })
hi("Pmenu", { fg = c.fg, bg = c.bg_panel })
hi("PmenuSel", { fg = c.bg, bg = c.declaration })
hi("PmenuSbar", { bg = c.bg_subtle })
hi("PmenuThumb", { bg = c.muted })
hi("PmenuMatch", { fg = c.number, bold = true })
hi("PmenuMatchSel", { fg = c.bg, bg = c.declaration, bold = true })
hi("SignColumn", { bg = c.bg })
hi("ColorColumn", { bg = c.bg_subtle })
hi("MatchParen", { fg = c.number, bold = true })
hi("NonText", { fg = c.muted })
hi("Whitespace", { fg = c.muted })
hi("SpecialKey", { fg = c.muted })
hi("Folded", { fg = c.muted_text, bg = c.bg_subtle })
hi("FoldColumn", { fg = c.muted, bg = c.bg })
hi("Directory", { fg = c.declaration })
hi("Title", { fg = c.declaration, bold = true })
hi("Question", { fg = c.comment })
hi("MoreMsg", { fg = c.comment })
hi("ModeMsg", { fg = c.fg, bold = true })
hi("WarningMsg", { fg = c.warning })
hi("ErrorMsg", { fg = c.error })
hi("WinBar", { fg = c.fg, bg = c.bg })
hi("WinBarNC", { fg = c.muted_text, bg = c.bg })
hi("QuickFixLine", { bg = c.selection })
hi("Conceal", { fg = c.muted })
hi("TabLine", { fg = c.muted_text, bg = c.bg_panel })
hi("TabLineSel", { fg = c.fg, bg = c.bg })
hi("TabLineFill", { bg = c.bg_panel })

-- ── Syntax (legacy groups) ──────────────────────────────────────────────
hi("Comment", { fg = c.comment, italic = true })
hi("String", { fg = c.string })
hi("Character", { fg = c.number })
hi("Number", { fg = c.number })
hi("Float", { fg = c.number })
hi("Boolean", { fg = c.keyword })
hi("Constant", { fg = c.number })
hi("Identifier", { fg = c.project })
hi("Function", { fg = c.project })
hi("Statement", { fg = c.keyword })
hi("Conditional", { fg = c.keyword })
hi("Repeat", { fg = c.keyword })
hi("Label", { fg = c.keyword })
hi("Keyword", { fg = c.keyword })
hi("Exception", { fg = c.keyword })
hi("Operator", { fg = c.fg })
hi("PreProc", { fg = c.macro })
hi("Include", { fg = c.macro })
hi("Define", { fg = c.macro })
hi("Macro", { fg = c.macro })
hi("PreCondit", { fg = c.macro })
hi("Type", { fg = c.project })
hi("StorageClass", { fg = c.keyword })
hi("Structure", { fg = c.project })
hi("Typedef", { fg = c.project })
hi("Special", { fg = c.macro })
hi("SpecialChar", { fg = c.macro })
hi("Tag", { fg = c.declaration })
hi("Delimiter", { fg = c.muted_text })
hi("SpecialComment", { fg = c.comment, bold = true })
hi("Debug", { fg = c.warning })
hi("Underlined", { fg = c.url, underline = true })
hi("Error", { fg = c.error })
hi("Todo", { fg = c.bg, bg = c.number, bold = true })

-- ── Treesitter ──────────────────────────────────────────────────────────
hi("@comment", { link = "Comment" })
hi("@comment.documentation", { fg = c.comment, italic = true })
hi("@comment.error", { fg = c.error })
hi("@comment.warning", { fg = c.warning })
hi("@comment.todo", { link = "Todo" })
hi("@comment.note", { fg = c.comment, bold = true })

hi("@string", { link = "String" })
hi("@string.documentation", { fg = c.string })
hi("@string.regexp", { fg = c.string })
hi("@string.escape", { fg = c.macro })
hi("@string.special", { fg = c.macro })
hi("@string.special.url", { fg = c.url, underline = true })
hi("@character", { fg = c.number })
hi("@character.special", { fg = c.macro })

hi("@number", { link = "Number" })
hi("@number.float", { link = "Number" })
hi("@boolean", { link = "Boolean" })

hi("@keyword", { link = "Keyword" })
hi("@keyword.function", { link = "Keyword" })
hi("@keyword.operator", { fg = c.keyword })
hi("@keyword.return", { link = "Keyword" })
hi("@keyword.import", { fg = c.macro })
hi("@keyword.directive", { fg = c.macro })
hi("@keyword.exception", { link = "Keyword" })
hi("@keyword.conditional", { link = "Keyword" })
hi("@keyword.repeat", { link = "Keyword" })
hi("@conditional", { link = "Keyword" })
hi("@repeat", { link = "Keyword" })
hi("@exception", { link = "Keyword" })

hi("@operator", { fg = c.fg })
hi("@punctuation", { fg = c.muted_text })
hi("@punctuation.delimiter", { fg = c.muted_text })
hi("@punctuation.bracket", { fg = c.muted_text })
hi("@punctuation.special", { fg = c.macro })

-- Project identifiers -> teal; system/SDK identifiers -> purple.
hi("@function", { fg = c.project })
hi("@function.call", { fg = c.project })
hi("@function.method", { fg = c.project })
hi("@function.method.call", { fg = c.project })
hi("@function.builtin", { fg = c.system_member })
hi("@function.macro", { fg = c.macro })
hi("@constructor", { fg = c.project })

hi("@variable", { fg = c.project })
hi("@variable.parameter", { fg = c.project })
hi("@variable.member", { fg = c.project })
hi("@variable.builtin", { fg = c.system_member })
hi("@property", { fg = c.project })
hi("@field", { fg = c.project })

hi("@constant", { fg = c.number })
hi("@constant.builtin", { fg = c.system_member })
hi("@constant.macro", { fg = c.macro })

hi("@type", { fg = c.project })
hi("@type.definition", { fg = c.declaration_type })
hi("@type.builtin", { fg = c.system_type })
hi("@type.qualifier", { fg = c.keyword })
hi("@attribute", { fg = c.attribute })
hi("@attribute.builtin", { fg = c.attribute })
hi("@module", { fg = c.system_type })
hi("@namespace", { fg = c.system_type })
hi("@label", { fg = c.keyword })
hi("@tag", { fg = c.declaration })
hi("@tag.attribute", { fg = c.attribute })
hi("@tag.delimiter", { fg = c.muted_text })

-- Markup (markdown, doc comments)
hi("@markup.heading", { fg = c.declaration, bold = true })
hi("@markup.strong", { fg = c.fg, bold = true })
hi("@markup.italic", { fg = c.fg, italic = true })
hi("@markup.strikethrough", { fg = c.muted_text, strikethrough = true })
hi("@markup.underline", { underline = true })
hi("@markup.link", { fg = c.url, underline = true })
hi("@markup.link.label", { fg = c.declaration })
hi("@markup.link.url", { fg = c.url, underline = true })
hi("@markup.raw", { fg = c.keyword })
hi("@markup.raw.block", { fg = c.fg })
hi("@markup.list", { fg = c.project })
hi("@markup.quote", { fg = c.muted_text, italic = true })
hi("@diff.plus", { fg = c.success })
hi("@diff.minus", { fg = c.error })
hi("@diff.delta", { fg = c.declaration })

-- ── LSP semantic tokens ─────────────────────────────────────────────────
-- sourcekit marks SDK symbols with the `defaultLibrary` modifier, which is how
-- Xcode's project-vs-system split is reproduced here.
hi("@lsp.type.class", { fg = c.project })
hi("@lsp.type.struct", { fg = c.project })
hi("@lsp.type.enum", { fg = c.project })
hi("@lsp.type.interface", { fg = c.project })
hi("@lsp.type.type", { fg = c.project })
hi("@lsp.type.typeParameter", { fg = c.project })
hi("@lsp.type.function", { fg = c.project })
hi("@lsp.type.method", { fg = c.project })
hi("@lsp.type.property", { fg = c.project })
hi("@lsp.type.variable", { fg = c.project })
hi("@lsp.type.parameter", { fg = c.project })
hi("@lsp.type.enumMember", { fg = c.number })
hi("@lsp.type.macro", { fg = c.macro })
hi("@lsp.type.namespace", { fg = c.system_type })
hi("@lsp.type.comment", {})
hi("@lsp.mod.defaultLibrary", { fg = c.system_member })
hi("@lsp.typemod.class.defaultLibrary", { fg = c.system_type })
hi("@lsp.typemod.struct.defaultLibrary", { fg = c.system_type })
hi("@lsp.typemod.enum.defaultLibrary", { fg = c.system_type })
hi("@lsp.typemod.type.defaultLibrary", { fg = c.system_type })
hi("@lsp.typemod.interface.defaultLibrary", { fg = c.system_type })
hi("@lsp.typemod.function.defaultLibrary", { fg = c.system_member })
hi("@lsp.typemod.method.defaultLibrary", { fg = c.system_member })
hi("@lsp.typemod.variable.defaultLibrary", { fg = c.system_member })
hi("@lsp.typemod.property.defaultLibrary", { fg = c.system_member })

-- ── Diagnostics ─────────────────────────────────────────────────────────
hi("DiagnosticError", { fg = c.error })
hi("DiagnosticWarn", { fg = c.warning })
hi("DiagnosticInfo", { fg = c.declaration })
hi("DiagnosticHint", { fg = c.project })
hi("DiagnosticOk", { fg = c.success })
hi("DiagnosticUnderlineError", { undercurl = true, sp = c.error })
hi("DiagnosticUnderlineWarn", { undercurl = true, sp = c.warning })
hi("DiagnosticUnderlineInfo", { undercurl = true, sp = c.declaration })
hi("DiagnosticUnderlineHint", { undercurl = true, sp = c.project })
hi("DiagnosticUnderlineOk", { undercurl = true, sp = c.success })

-- ── LSP ─────────────────────────────────────────────────────────────────
hi("LspReferenceText", { bg = c.bg_subtle })
hi("LspReferenceRead", { bg = c.bg_subtle })
hi("LspReferenceWrite", { bg = c.bg_subtle, underline = true })
hi("LspInlayHint", { fg = c.muted, bg = c.bg_subtle, italic = true })
hi("LspSignatureActiveParameter", { fg = c.number, bold = true })
hi("LspCodeLens", { fg = c.muted_text, italic = true })

-- ── Diff ────────────────────────────────────────────────────────────────
hi("DiffAdd", { bg = c.diff_add_bg })
hi("DiffChange", { bg = c.bg_subtle })
hi("DiffDelete", { fg = c.muted_red, bg = c.diff_del_bg })
hi("DiffText", { bg = c.diff_text_bg })
hi("Added", { fg = c.success })
hi("Changed", { fg = c.warning })
hi("Removed", { fg = c.error })

-- ── Plugins ─────────────────────────────────────────────────────────────
hi("GitSignsAdd", { fg = c.muted_green })
hi("GitSignsChange", { fg = c.warning })
hi("GitSignsDelete", { fg = c.muted_red })

hi("MiniDiffSignAdd", { fg = c.muted_green })
hi("MiniDiffSignChange", { fg = c.warning })
hi("MiniDiffSignDelete", { fg = c.muted_red })
hi("MiniIconsAzure", { fg = c.declaration })
hi("MiniIconsBlue", { fg = c.url })
hi("MiniIconsCyan", { fg = c.project })
hi("MiniIconsGreen", { fg = c.comment })
hi("MiniIconsGrey", { fg = c.muted_text })
hi("MiniIconsOrange", { fg = c.macro })
hi("MiniIconsPurple", { fg = c.system_member })
hi("MiniIconsRed", { fg = c.string })
hi("MiniIconsYellow", { fg = c.number })
hi("MiniStatuslineModeNormal", { fg = c.bg, bg = c.declaration, bold = true })
hi("MiniStatuslineModeInsert", { fg = c.bg, bg = c.comment, bold = true })
hi("MiniStatuslineModeVisual", { fg = c.bg, bg = c.keyword, bold = true })
hi("MiniStatuslineModeReplace", { fg = c.bg, bg = c.string, bold = true })
hi("MiniStatuslineModeCommand", { fg = c.bg, bg = c.number, bold = true })

hi("TelescopeNormal", { fg = c.fg, bg = c.bg_panel })
hi("TelescopeBorder", { fg = c.muted, bg = c.bg_panel })
hi("TelescopeTitle", { fg = c.declaration, bold = true })
hi("TelescopeSelection", { bg = c.selection })
hi("TelescopeSelectionCaret", { fg = c.declaration })
hi("TelescopeMatching", { fg = c.number, bold = true })
hi("TelescopePromptPrefix", { fg = c.keyword })

hi("OilDir", { fg = c.declaration })
hi("OilFile", { fg = c.fg })
hi("OilCreate", { fg = c.success })
hi("OilDelete", { fg = c.error })
hi("OilMove", { fg = c.warning })
