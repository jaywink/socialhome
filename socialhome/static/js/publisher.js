(function ($) {
    $(".markdownx-editor").markdown({
        resize: "vertical",
        autofocus: true,
        iconlibrary: "fa",
        hiddenButtons: ["cmdPreview"],
        onChange: function(e) {
            e.$textarea.trigger("input");
        }.bind(this),
        additionalButtons: [[{
            name: "groupCustom",
            data: [{
                name: "cmdUploadImage",
                title: "Upload image",
                icon: "fa fa-camera",
                callback: publisherUploadImage,
            }]
        }]],
    });

    var uploadProgessTemplate =_.template(
        '<div class="progress">' +
            '<div id="<%= imageId %>" class="progress-bar progress-bar-striped bg-success" role="progressbar" ' +
                'aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>' +
        '</div>'
    );

    $("#image-upload-input").on("change", function() {
        // Adapted from https://stackoverflow.com/a/8758614/1489738
        var imageFormData = new FormData($("#image-upload-form")[0]);
        var imageId = imageFormData.get("image").lastModified;
        $.ajax({
            url: "/api/image-upload/",
            type: "POST",
            data: imageFormData,
            cache: false,
            contentType: false,
            processData: false,
            headers: { "X-CSRFToken": Cookies.get("csrftoken") },
            xhr: function() {
                var myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    myXhr.upload.addEventListener("progress", function(e) {
                        if (e.lengthComputable) {
                            var percentage = (e.loaded / e.total)*100;
                            $("#" + imageId).css("width", percentage + "%").attr("aria-valuenow", percentage);
                        }
                    }, false);
                }
                return myXhr;
            },
            beforeSend: function() {
                $("#image-upload-progress-container").append(uploadProgessTemplate({imageId: imageId}));
            },
            complete: function() {
                $("#" + imageId).hide();
            },
            success: function(data) {
                if (data.code !== undefined) {
                    $('#id_text').val(function(_, val) {
                        return val + "\n" + data.code + "\n";
                    });
                    // TODO: how do we make the preview trigger??
                }
            },
        });
    });
})(jQuery);

function publisherUploadImage() {
  $("#image-upload-input").click();
}
