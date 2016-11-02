(function ($) {
    $(".markdownx-editor").markdown({
         resize: "none",
         iconlibrary: "fa",
         fullscreen: {enable: false, icons: {}},
         hiddenButtons: ["cmdPreview"],
         onChange: function(e){ e.$textarea.trigger("input"); }.bind(this)
    });
})(jQuery);