module.exports = {
    rules: {
        "arrow-parens": ["error", "as-needed"],
        indent: ["error", 4, {SwitchCase: 1}],
        "import/extensions": "off",
        "import/no-extraneous-dependencies": "off",
        "import/no-unresolved": "off",
        "max-len": ["error", 120],
        "no-plusplus": ["error", {allowForLoopAfterthoughts: true}],
        "no-return-assign": "off",
        "no-unused-expressions": "off",
        "object-curly-spacing": ["error", "never"],
        "object-curly-newline": ["error", {
            ObjectExpression: {multiline: true},
            ObjectPattern: {multiline: true},
            ImportDeclaration: {multiline: true, minProperties: 6},
            ExportDeclaration: {multiline: true, minProperties: 6},
        }],
        quotes: ["error", "double"],
        semi: ["error", "never"],
        "vue/max-attributes-per-line": ["error", {
            singleline: 5,
            multiline: {max: 1, allowFirstLine: false},
        }],
    },
    globals: {
        gettext: true,
        interpolate: true,
        ngettext: true,
        Urls: true,
        Cookies: true,
    },
}
