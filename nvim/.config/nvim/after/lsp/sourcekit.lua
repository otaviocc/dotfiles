-- Overrides nvim-lspconfig's sourcekit config. This must live in `after/lsp/`,
-- not `lsp/`: all `lsp/<name>.lua` files on the runtimepath are merged first
-- and nvim-lspconfig's would win, whereas `after/lsp/` is applied on top of
-- them. See `:h lsp-config-merge`.
--
-- Pin to the sourcekit-lsp of the *selected Xcode* rather than whatever PATH
-- resolves first. swiftly prepends ~/.swiftly/bin (from ~/.zprofile), so the
-- winner otherwise differs between a login shell, a GUI launch and a
-- subshell -- and a toolchain that disagrees with the Xcode SDK indexes
-- badly. `xcrun` always follows `xcode-select -p`.
return {
    cmd = { "xcrun", "sourcekit-lsp" },
}
