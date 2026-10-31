// Shared YouTube facade: thumbnails and click-to-play for the whole site.
//
// There were two copies of this, inlined in build_videos.py and
// build_announcements.py, and only one of them drew a thumbnail -- which is why
// the archived meeting stream rendered as an empty panel. One module now, used
// by every page that embeds video.
//
// Thumbnails need no API key: YouTube serves them at a URL derived from the
// video id, so any element carrying data-yt gets art automatically.
//
// Nothing is requested from YouTube until a visitor clicks, so a page of videos
// costs nothing to load and sets no cookies for someone who only reads. The
// player itself comes from youtube-nocookie.com.
(function () {
  'use strict';

  function thumb(id, quality) {
    return 'https://i.ytimg.com/vi/' + id + '/' + quality + '.jpg';
  }

  // ---- thumbnails -------------------------------------------------------
  // maxresdefault is a true 16:9 frame but is missing for plenty of videos;
  // hqdefault always exists but is 4:3 with letterbox bars, which object-fit
  // crops off. Try the good one, fall back on error.
  document.querySelectorAll('[data-yt]').forEach(function (el) {
    if (el.querySelector('img')) return;           // markup supplied its own
    var id = el.getAttribute('data-yt');
    if (!id) return;

    var img = document.createElement('img');
    img.alt = '';
    img.loading = 'lazy';
    img.decoding = 'async';
    img.addEventListener('error', function () {
      if (img.getAttribute('data-fallback')) {
        img.remove();                              // neither size resolved
        return;
      }
      img.setAttribute('data-fallback', '1');
      img.src = thumb(id, 'hqdefault');
    });
    img.src = thumb(id, 'maxresdefault');
    el.insertBefore(img, el.firstChild);
  });

  // ---- click to play ----------------------------------------------------
  function player(src, title) {
    var f = document.createElement('iframe');
    f.src = src;
    f.title = title || 'Video player';
    f.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture';
    f.allowFullscreen = true;
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    return f;
  }

  var NOCOOKIE = 'https://www.youtube-nocookie.com/embed/';

  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-yt], [data-list], [data-live]');
    if (!el) return;

    var label = el.getAttribute('aria-label') || '';
    var src;

    if (el.hasAttribute('data-yt')) {
      // data-t is an optional start offset in seconds.
      var t = el.getAttribute('data-t');
      src = NOCOOKIE + el.getAttribute('data-yt') + '?autoplay=1&rel=0'
          + (t ? '&start=' + t : '');
    } else if (el.hasAttribute('data-list')) {
      src = NOCOOKIE + 'videoseries?list=' + el.getAttribute('data-list')
          + '&autoplay=1&rel=0';
    } else {
      // Channel-level live embed: whatever is streaming now, no per-stream id
      // to maintain. Deliberately www.youtube.com -- live_stream?channel= is
      // documented there and unverified on the nocookie host. When nothing is
      // live it renders "Video Play Configuration Error", which the panel's own
      // copy explains.
      src = 'https://www.youtube.com/embed/live_stream?channel='
          + el.getAttribute('data-live') + '&autoplay=1';
      label = label || 'Live meeting stream';
    }

    // The facade is a real link to YouTube, so it still works without this
    // script. Once the player is in, let the link alone.
    e.preventDefault();
    el.replaceChildren(player(src, label));
    el.classList.add('is-playing');
  });
})();
