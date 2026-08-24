local mcqueen = [[



                         ______
                    ,---'  o  o `---.
              _____/      95        \_____
        ,----'                           `----.
     __/                                       \__
    |___________________________________________|
       (O)                             (O)
        -                               -

]]

return {
  { import = "lazyvim.plugins.extras.ui.dashboard-nvim" },
  {
    "nvimdev/dashboard-nvim",
    opts = {
      config = {
        header = vim.split(mcqueen, "\n"),
      },
    },
  },
}
