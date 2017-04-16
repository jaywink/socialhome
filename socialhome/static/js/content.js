(function($){
    window.Content = {};
    var contentTemplate =
        '<div class="<% if (content.parent) { %>reply<% } else { %>grid-item<% } %>" ' +
                'data-content-id="<%= content.id %>">' +
            '<%= content.rendered %>' +
            '<% if (content.parent || stream !== "profile") { %>' +
                '<div class="grid-item-author-bar">' +
                    '<img src="<%= content.author_image %>" class="grid-item-author-bar-pic"> <%= content.author_name %>' +
                '</div>' +
            '<% } %>' +
            '<div class="grid-item-bar">' +
                '<div class="row">' +
                    '<div class="col-xs-6">' +
                        '<span class="grid-item-open-action" data-content-id="<%= content.id %>" ' +
                            'title="<%= content.formatted_timestamp %>"><%= content.humanized_timestamp %>' +
                        '</span>' +
                        '<% if (content.is_author) { %>' +
                            '<span id="content-bar-actions"> ' +
                                '&nbsp;' +
                                '<a id="content-update-link" href="<%= content.update_url %>"><i class="fa fa-pencil" title="' + gettext("Update") + '" aria-label="' + gettext("Update") + '"></i></a> ' +
                                '<a id="content-delete-link" href="<%= content.delete_url %>"><i class="fa fa-remove" title="' + gettext("Delete") + '" aria-label="' + gettext("Delete") + '"></i></a>' +
                            '</span>' +
                        '<% } %>' +
                    '</div>' +
                    '<div class="col-xs-6 text-xs-right grid-item-reactions">' +
                        '<% if (! content.parent && (content.is_authenticated || content.child_count)) { %>' +
                            '<div class="item-reaction">' +
                                '<span class="item-open-replies-action" data-content-id="<%= content.id %>">' +
                                    '<i class="fa fa-envelope" title="' + gettext("Replies") +'" aria-label="' + gettext("Replies") +'"></i>' +
                                '</span>&nbsp;' +
                                '<span class="item-reaction-counter"><%= content.child_count %></span>' +
                            '</div>' +
                        '<% } %>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>';
    window.Content.template = _.template(contentTemplate);
})(jQuery);
