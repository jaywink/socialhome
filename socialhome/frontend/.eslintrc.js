module.exports = {
    rules: {
        "arrow-parens": ["error", "as-needed"],
        indent: ["error", 4, {SwitchCase: 1}],
        "max-len": ["error", 120],
        "no-plusplus": ["error", {allowForLoopAfterthoughts: true}],
        "object-curly-spacing": ["error", "never"],
        "object-curly-newline": ["error", {
            ObjectExpression: {
                multiline: true, minProperties: 2,
            },
            ObjectPattern: {multiline: true},
            ImportDeclaration: {
                multiline: true, minProperties: 6,
            },
            ExportDeclaration: {
                multiline: true, minProperties: 6,
            },
        }],
        quotes: ["error", "double", {avoidEscape: true}],
        semi: ["error", "never"],
        "vue/max-attributes-per-line": ["error", {
            singleline: 5,
            multiline: {
                max: 1, allowFirstLine: false,
            },
        }],
        "vue/html-indent": ["error", 4],
    },
    globals: {
        gettext: true,
        interpolate: true,
        ngettext: true,
        Urls: true,
    },
}
