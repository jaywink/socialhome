(function($){
    $(document).ready(function() {
        // Init masonry grid
        var $grid = $('.grid').masonry({
            itemSelector: '.grid-item',
            columnWidth: '.grid-sizer',
            percentPosition: true,
        });
        // Layout Masonry after each image loads
        $grid.imagesLoaded().progress(function() {
            $grid.masonry('layout');
        });
    });
})(jQuery);
