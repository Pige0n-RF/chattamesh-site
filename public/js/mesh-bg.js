(function () {
    "use strict";

    // Ambient mesh texture behind the whole site: drifting nodes, links drawn
    // between any two that are close enough to "hear" each other, and the
    // occasional packet crossing one of those links.
    //
    // No network calls. Nothing here reflects real node positions or real
    // traffic -- it is decoration, and deliberately doesn't pretend otherwise.

    var canvas = document.getElementById("mesh-bg");
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext("2d");

    var reduceMotion = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var LINK_DIST = 170;      // px; beyond this two nodes don't draw a link
    var LINK_ALPHA = 0.48;    // peak opacity of a link at zero distance
    var NODE_SPACING = 90;    // roughly one node per NODE_SPACING^2 of area
    var MAX_NODES = 130;
    var PULSE_CHANCE_PER_SEC = 0.6;

    // Palette is read from the stylesheet so the canvas tracks the site tokens.
    // Canvas needs numeric channels to interpolate alpha per frame, which
    // var() can't express, so the hexes are parsed to "r, g, b" once at load.
    function rgbOf(name, fallback) {
        var raw = getComputedStyle(document.documentElement)
            .getPropertyValue(name).trim() || fallback;
        var hex = raw.replace("#", "");
        if (hex.length === 3) hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
        if (!/^[0-9a-f]{6}$/i.test(hex)) hex = fallback.replace("#", "");
        return parseInt(hex.slice(0, 2), 16) + ", " +
               parseInt(hex.slice(2, 4), 16) + ", " +
               parseInt(hex.slice(4, 6), 16);
    }
    var LINK = rgbOf("--mesh-link", "#3a5f9e");
    var NODE = rgbOf("--mesh-node", "#6e70e6");

    var width = 0, height = 0, dpr = 1;
    var nodes = [];
    var pulses = [];
    var lastTime = 0;

    function rand(min, max) { return min + Math.random() * (max - min); }

    function build() {
        var target = Math.min(MAX_NODES,
            Math.round((width * height) / (NODE_SPACING * NODE_SPACING)));
        nodes = [];
        for (var i = 0; i < target; i++) {
            nodes.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: rand(-0.012, 0.012),
                vy: rand(-0.012, 0.012),
                r: rand(1.1, 2.2),
                pulse: Math.random() * Math.PI * 2
            });
        }
    }

    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = Math.round(width * dpr);
        canvas.height = Math.round(height * dpr);
        canvas.style.width = width + "px";
        canvas.style.height = height + "px";
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        build();
    }

    function spawnPulse() {
        if (nodes.length < 2) return;
        var a = nodes[Math.floor(Math.random() * nodes.length)];
        var candidates = [];
        for (var i = 0; i < nodes.length; i++) {
            if (nodes[i] === a) continue;
            var dx = nodes[i].x - a.x, dy = nodes[i].y - a.y;
            if (Math.sqrt(dx * dx + dy * dy) < LINK_DIST) candidates.push(nodes[i]);
        }
        if (!candidates.length) return;
        pulses.push({
            a: a,
            b: candidates[Math.floor(Math.random() * candidates.length)],
            t: 0,
            duration: rand(500, 1000)
        });
    }

    function step(dt) {
        var i;
        for (i = 0; i < nodes.length; i++) {
            var n = nodes[i];
            n.x += n.vx * dt;
            n.y += n.vy * dt;
            if (n.x < -20) n.x = width + 20;
            if (n.x > width + 20) n.x = -20;
            if (n.y < -20) n.y = height + 20;
            if (n.y > height + 20) n.y = -20;
            n.pulse += dt * 0.002;
        }
        if (Math.random() < (PULSE_CHANCE_PER_SEC * dt) / 1000) spawnPulse();
        for (i = pulses.length - 1; i >= 0; i--) {
            pulses[i].t += dt / pulses[i].duration;
            if (pulses[i].t >= 1) pulses.splice(i, 1);
        }
    }

    function draw() {
        ctx.clearRect(0, 0, width, height);

        ctx.lineWidth = 1;
        for (var i = 0; i < nodes.length; i++) {
            for (var j = i + 1; j < nodes.length; j++) {
                var dx = nodes[i].x - nodes[j].x;
                var dy = nodes[i].y - nodes[j].y;
                var dist = Math.sqrt(dx * dx + dy * dy);
                if (dist >= LINK_DIST) continue;
                var alpha = (1 - dist / LINK_DIST) * LINK_ALPHA;
                ctx.strokeStyle = "rgba(" + LINK + ", " + alpha.toFixed(3) + ")";
                ctx.beginPath();
                ctx.moveTo(nodes[i].x, nodes[i].y);
                ctx.lineTo(nodes[j].x, nodes[j].y);
                ctx.stroke();
            }
        }

        for (var p = 0; p < pulses.length; p++) {
            var pu = pulses[p];
            var fade = Math.sin(Math.PI * pu.t);
            ctx.beginPath();
            ctx.arc(pu.a.x + (pu.b.x - pu.a.x) * pu.t,
                    pu.a.y + (pu.b.y - pu.a.y) * pu.t,
                    2.4, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(" + NODE + ", " + (0.6 * fade).toFixed(3) + ")";
            ctx.fill();
        }

        for (var n = 0; n < nodes.length; n++) {
            var node = nodes[n];
            var glow = 0.34 + 0.18 * Math.sin(node.pulse);
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(" + NODE + ", " + glow.toFixed(3) + ")";
            ctx.fill();
        }
    }

    var rafId = null;

    function frame(time) {
        var dt = lastTime ? time - lastTime : 16;
        lastTime = time;
        step(Math.min(dt, 48));
        draw();
        rafId = requestAnimationFrame(frame);
    }

    function startLoop() {
        if (reduceMotion || rafId) return;
        lastTime = 0;
        rafId = requestAnimationFrame(frame);
    }

    function stopLoop() {
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    }

    // A backgrounded tab keeps firing timers while rAF is paused, so animation
    // state quietly queues up and refocusing dumps it all into one frame.
    // Going fully quiet while hidden avoids that.
    document.addEventListener("visibilitychange", function () {
        if (document.hidden) stopLoop(); else startLoop();
    });

    var resizeTimer = null;
    window.addEventListener("resize", function () {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(resize, 150);
    });

    resize();

    if (reduceMotion) {
        draw();   // one static frame, no motion
    } else {
        startLoop();
    }
})();
