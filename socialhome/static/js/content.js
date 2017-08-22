(function($){
    window.Content = {};
    var contentTemplate =
        '<div class="<% if (content.parent) { %>reply<% } else { %>grid-item<% } %>" ' +
                'data-content-id="<%= content.id %>">' +
            '<%= content.rendered %>' +
            '<% if (content.parent || stream !== "profile") { %>' +
                '<div class="grid-item-author-bar mt-1">' +
                    '<div class="profile-box-trigger">' +
                        '<img src="<%= content.author_image %>" class="grid-item-author-bar-pic"> <%= content.author_name %>' +
                    '</div>' +
                    '<div class="profile-box hidden">' +
                        '<%= content.author_handle %>' +
                        '<div class="pull-right">' +
                            '<a href="<%= content.author_profile_url %>" class="btn btn-secondary" title="' + gettext("Profile") + '" aria-label="' + gettext("Profile") + '"><i class="fa fa-user"></i></a>' +
                            '<% if (! content.author_is_local) { %>' +
                                '<a href="<%= content.author_home_url %>" class="btn btn-secondary" title="' + gettext("Home") + '" aria-label="' + gettext("Home") + '"><i class="fa fa-home"></i></a>' +
                            '<% } %>' +
                            '<% if (content.is_authenticated && ! content.is_author) { %>' +
                                '<button class="follower-button btn btn-secondary <% if (! content.is_following_author) { %>hidden<% } %>" data-action="remove_follower" data-profileid="<%= content.profile_id %>" data-target="<%= content.author_guid %>" title="' + gettext("Unfollow") + '" aria-label="' + gettext("Unfollow") + '"><i class="fa fa-minus"></i></button>' +
                                '<button class="follower-button btn btn-secondary <% if (content.is_following_author) { %>hidden<% } %>" data-action="add_follower" data-profileid="<%= content.profile_id %>" data-target="<%= content.author_guid %>" title="' + gettext("Follow") + '" aria-label="' + gettext("Follow") + '"><i class="fa fa-plus"></i></button>' +
                            '<% } %>' +
                        '</div>' +
                        '<div class="clearfix"></div>' +
                    '</div>' +
                '</div>' +
            '<% } %>' +
            '<div class="grid-item-bar d-flex justify-content-start">' +
                '<div class="mt-1">' +
                    '<a class="unstyled-link" href="<%= content.detail_url %>" title="<%= content.formatted_timestamp %>">' +
                        '<%= content.humanized_timestamp %>' +
                    '</a>' +
                    '<% if (content.is_author) { %>' +
                        '<span id="content-bar-actions"> ' +
                            '&nbsp;' +
                            '<a id="content-update-link" href="<%= content.update_url %>"><i class="fa fa-pencil" title="' + gettext("Update") + '" aria-label="' + gettext("Update") + '"></i></a> ' +
                            '<a id="content-delete-link" href="<%= content.delete_url %>?next='+ window.location.pathname +'"><i class="fa fa-remove" title="' + gettext("Delete") + '" aria-label="' + gettext("Delete") + '"></i></a>' +
                        '</span>' +
                    '<% } %>' +
                '</div>' +
                '<div class="ml-auto grid-item-reactions mt-1">' +
                    '<% if (! content.parent && (content.is_authenticated || content.shares_count)) { %>' +
                        '<div class="item-reaction <% if (content.shares_count) { %>item-reaction-counter-positive<% } %>">' +
                            '<i class="fa fa-refresh" title="' + gettext("Shares") + '" aria-label="' + gettext("Shares") + '"></i>&nbsp;' +
                            '<span class="item-reaction-counter"><%= content.shares_count %></span>' +
                        '</div>' +
                    '<% } %>' +
                    '<% if (! content.parent && (content.is_authenticated || content.child_count)) { %>' +
                        '<div class="item-reaction ml-1 <% if (content.child_count) { %>item-reaction-counter-positive<% } %>">' +
                            '<span class="item-open-replies-action" data-content-id="<%= content.id %>">' +
                                '<i class="fa fa-envelope" title="' + gettext("Replies") +'" aria-label="' + gettext("Replies") +'"></i>' +
                            '</span>&nbsp;' +
                            '<span class="item-reaction-counter"><%= content.child_count %></span>' +
                        '</div>' +
                    '<% } %>' +
                '</div>' +
            '</div>' +
            '<div class="replies-container" data-content-id="<%= content.id %>"></div>' +
            '<% if (content.is_authenticated && content.content_type === "content") { %>' +
                '<div class="content-actions hidden" data-content-id="<%= content.id %>">' +
                    '<a class="btn btn-secondary" href="<%= content.reply_url %>" aria-label="' + gettext("Reply") + '">' + gettext("Reply") +'</a>' +
                '</div>' +
            '<% } %>' +
        '</div>';
    window.Content.template = _.template(contentTemplate);
})(jQuery);
