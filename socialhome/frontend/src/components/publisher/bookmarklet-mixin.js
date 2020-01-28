const controlChars = [
    " ",
    "\f",
    "\r",
    "\t",
    "\v",
    "\\u00a0",
    "\\u1680",
    "\\u2000",
    "\\u200a",
    "\\u2028",
    "\\u2029",
    "\\u202f",
    "\\u205f",
    "\\u3000",
    "\\ufeff",
]

function trimMargin(string) {
    return string
        // eslint-disable-next-line no-useless-escape
        .replace(RegExp(`^[${controlChars.join()}]+\\|`, "gm"), "")
        .replace(/^\n*/g, "")
        .replace(/\n*$/g, "")
}

const bookmarkletMixin = {
    props: {
        shareUrl: {
            type: String, default: "",
        },
        shareTitle: {
            type: String, default: "",
        },
        shareNotes: {
            type: String, default: "",
        },
    },
    beforeMount() {
        if (this.shareUrl.length > 0 && this.shareUrl.length > 0) {
            this.baseModel.text = trimMargin(`
                |## ${decodeURIComponent(this.shareTitle)}

                |${decodeURIComponent(this.shareUrl)}

                |${decodeURIComponent(this.shareNotes)}`)
        }
    },
}

export default bookmarkletMixin
export {bookmarkletMixin}
