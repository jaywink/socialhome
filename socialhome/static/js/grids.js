(function($){
    $(document).ready(function() {
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
