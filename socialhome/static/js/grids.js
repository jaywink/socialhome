(function($){
    $(document).ready(function() {
        $('.grid').masonry({
            itemSelector: '.grid-item',
            columnWidth: 200,
            fitWidth: true,
        });
    });
})(jQuery);
