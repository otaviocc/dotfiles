-- Unlike tokyonight and catppuccin, LazyVim does not bundle kanagawa, so the
-- plugin has to be declared here rather than just selected by name. `priority`
-- and `lazy = false` are what a colorscheme plugin needs to load before the
-- first buffer is drawn.
return {
  {
    "rebelot/kanagawa.nvim",
    lazy = false,
    priority = 1000,
    opts = {
      -- Dragon is the warm, near-monochrome variant; see docs/palette.md.
      theme = "dragon",
      background = { dark = "dragon" },
    },
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "kanagawa-dragon",
    },
  },
}
