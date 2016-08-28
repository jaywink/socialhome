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
