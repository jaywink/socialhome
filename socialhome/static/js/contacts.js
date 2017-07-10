$(document).ready(function() {
    window.SocialhomeContacts = {
        addFollowUnfollowTriggers: function() {
            $(".follower-button").off("click", SocialhomeContacts.followUnfollow)
                .click(SocialhomeContacts.followUnfollow);
        },

        followUnfollow: function(ev) {
            var $elem = $(ev.currentTarget);
            var targetGuid = $elem.data("target");
            $.post({
                url: "/api/profiles/" +$elem.data("profileid") + "/" + $elem.data("action") + "/",
                data: { guid: targetGuid },
                success: function () {
                    $(".follower-button[data-target='" + targetGuid + "']").toggleClass("hidden");
                },
                headers: { "X-CSRFToken": Cookies.get('csrftoken') },
            });
        },
    };

    if (typeof socialhomeStream === "undefined") {
        SocialhomeContacts.addFollowUnfollowTriggers();
    }
});
