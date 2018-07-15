(function ($) {
    $(".markdownx-editor").markdown({
        resize: "vertical",
        autofocus: true,
        iconlibrary: "fa",
        hiddenButtons: ["cmdPreview"],
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
                var $textArea = $("#id_text");
                var text = $textArea.val();
                var position = document.getElementById("id_text").selectionStart;
                if (data.code !== undefined) {
                    var newText = text.substring(0, position) + "\n" + data.code + " " + text.substring(position);
                    $textArea.val(newText);
                    document.getElementById("id_text").selectionEnd = position + data.code.length + 2;

                    // Placing new text doesn't trigger the textarea in a way that MarkdownX picks it up and does
                    // a preview fetch - and have tried all posssible events to make it trigger to no benefit.
                    // So, let's do it manually.
                    $.post({
                        url: "/markdownx/markdownify/",
                        data: { content: newText },
                        headers: { "X-CSRFToken": Cookies.get("csrftoken") },
                        success: function(data) {
                            $(".markdownx-preview").html(data);
                        },
                    });
                }
            },
        });
    });

    /* Show limited visibility related fields based on visibility selection */
    $('#id_visibility').change(function(ev) {
        var val = $(ev.currentTarget).val();
        if (val == '1') {  // Magic numbers <3 .. This is for "Visibility.LIMITED"
            $('#id_recipients').parent().removeClass('hidden');
            $('#id_include_following').parent().removeClass('hidden');
        } else {
            $('#id_recipients').parent().addClass('hidden');
            $('#id_include_following').parent().addClass('hidden');
        }
    })
})(jQuery);

function publisherUploadImage() {
  $("#image-upload-input").click();
}
