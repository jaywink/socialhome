/* Source: Diaspora project (https://github.com/diaspora/diaspora) */

var bookmarklet = function(e, n, t, o) {
    var r = 1900,
        i = 128,
        c = function() {
            var e = window,
                o = e.screenTop ? e.screenTop : e.screenY,
                r = e.screenLeft ? e.screenLeft : e.screenX;
            return "width=" + n + ",height=" + t + ",top=" + (o + e.innerHeight / 2 - t / 2) + ",left=" + (r + e.innerWidth / 2 - n / 2)
        },
        l = function() {
            var e = window,
                n = document,
                t = e.location.href,
                o = n.title,
                c = e.getSelection ? e.getSelection() : n.getSelection ? n.getSelection() : n.selection.createRange().text,
                l = c.toString(),
                s = r - t.length;
            return (o + l).length > s && (o.length > i && (o = o.substr(0, i) + " ..."), l.length > s - i && (l = l.substr(0, s - i) + " ...")), "url=" + encodeURIComponent(t) + "&title=" + encodeURIComponent(o) + "&notes=" + encodeURIComponent(l)
        },
        s = function() {
            var n = o || "location=yes,links=no,scrollbars=yes,toolbar=no",
                t = e + "?jump=yes";
            window.open(e + "?" + l(), "socialhome_bookmarklet", n + "," + c()) || (window.location.href = t + "&" + l())
        };
    /Firefox/.test(navigator.userAgent) ? setTimeout(s, 0) : s()
};

bookmarklet("https://{{ request.site.domain }}/bookmarklet", 620, 400);
