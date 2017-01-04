(function($){
    $(document).ready(function() {
        // Init masonry grid
        var $grid = $('.grid').masonry({
            itemSelector: '.grid-item',
            columnWidth: '.grid-sizer',
            percentPosition: true,
            stamp: ".stamped",
        });

        // Layout Masonry after each image loads
        $grid.imagesLoaded().progress(function() {
            $grid.masonry('layout');
        });

        var layoutAfterIFramesCounter = 0;
        function layoutAfterIFrames() {
            // Check for new iframes and layout the grid if we find some
            // Stop after X iterations - we're assuming things have loaded by then
            var $unprocessedIframes = $("iframe:not(.grid-layout-done)");
            if ($unprocessedIframes.length) {
                setTimeout(function() {
                    $grid.masonry('layout');
                }, 300);
                $unprocessedIframes.addClass("grid-layout-done");
            }
            if (layoutAfterIFramesCounter < 20) {
                layoutAfterIFramesCounter += 1;
                setTimeout(layoutAfterIFrames, 500);
            }
        }
        layoutAfterIFrames();

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
