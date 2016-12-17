(function($){
    $(document).ready(function() {
        // Init masonry grid
        var $grid = $('.grid').masonry({
            itemSelector: '.grid-item',
            columnWidth: '.grid-sizer',
            percentPosition: true,
            stamp: ".stamped",
        });

        var layoutMasonry = function() {
            // We're doing again an 'imagesLoaded' call here since some OEmbed's could have images which
            // load a while, and we might be ending here from the Ajax success trigger
            $grid.imagesLoaded().progress(function() {
                $grid.masonry('layout');
            });
        };

        // Layout Masonry after each image loads
        $grid.imagesLoaded().progress(function() {
            $grid.masonry('layout');
        });
        // Layout Masonry also a little after each successful Ajax call
        $(document).ajaxSuccess(function() {
            setTimeout(layoutMasonry, 500);
        });
        // Make profile content organize cards sortable
        $(".organize-content").sortable({
            handle: ".fa-arrows-alt"
        });
        // Submit handler for saving new profile content order
        $("form#organize-content-form").submit(function() {
            var data = $(".organize-content").sortable("toArray", {attribute: "data-id"}).toString();
            $("input[name='sort_order']").val(data);
        });
    });
})(jQuery);
