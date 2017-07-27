$(document).ready(function() {
    var searchInput = $("#search-input");

    if (searchInput.length) {
        // Multiply by 2 to ensure the cursor always ends up at the end;
        // Opera sometimes sees a carriage return as 2 characters.
        var strLength = searchInput.val().length * 2;

        searchInput.focus();
        searchInput[0].setSelectionRange(strLength, strLength);
    }
});
