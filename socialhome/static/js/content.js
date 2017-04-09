(function($){
    window.Content = {};
    // TODO: add edit / delete functionality since we need that for comments now
    var contentTemplate =
        '<div class="<% if (content.parent) { %>comment<% } else { %>grid-item<% } %>" data-content-id="<%= content.id %>"><%= content.rendered %>' +
        '<% if (content.parent || stream !== "profile") { %>' +
            '<div class="grid-item-author-bar">' +
                '<img src="<%= content.author_image %>" class="grid-item-author-bar-pic"> <%= content.author_name %>' +
            '</div>' +
        '<% } %>' +
        '<div class="grid-item-bar">' +
            '<div class="row">' +
                '<div class="col-xs-6">' +
                    '<span class="grid-item-open-action" data-content-guid="<%= content.guid %>" ' +
                        'title="<%= content.formatted_timestamp %>"><%= content.humanized_timestamp %>' +
                    '</span>' +
                '</div>' +
                '<div class="col-xs-6 text-xs-right grid-item-reactions">' +
                    '<% if (!content.parent) { %>' +
                        '<div class="item-reaction">' +
                            '<span class="item-open-comments-action" data-content-id="<%= content.id %>">' +
                                '<i class="fa fa-envelope"></i>' +
                            '</span>&nbsp;' +
                            '<span class="item-reaction-counter"><%= content.child_count %></span>' +
                        '</div>' +
                    '<% } %>' +
                '</div>' +
            '</div>';
    window.Content.template = _.template(contentTemplate);
})(jQuery);
