import type { CSSProperties } from "react";

// Same honey layer as backend/app/routes/admin.py's _HONEY. Copied rather than
// shared for the same reason its logo is: the admin page has no build step.

// x vw, y px, strand width, bulb radius, drop length, cycle s, delay s. Each x
// sits under a lobe of POOL; negative delays desync the loops on first paint.
const DRIPS = [
  [13, 78, 18, 14, 360, 15, -6],
  [31, 72, 12, 9, 200, 12, -2],
  [50, 84, 22, 17, 440, 18, -11],
  [70, 64, 11, 8, 150, 11, -5],
  [88, 80, 15, 12, 300, 14, -9],
] as const;

// Pool edge in a 1000x100 box stretched to the viewport (preserveAspectRatio
// none), so the lobes land at the same vw fractions as DRIPS' x values. Lobe
// spacing, depth and handle lengths are deliberately uneven — evenly spaced
// equal sags read as a scallop border, not poured honey.
const POOL =
  "M0 0H1000V56C985 56 975 68 960 68C948 68 940 46 925 46C905 46 900 94 880 94" +
  "C850 94 838 60 812 60C792 60 785 40 770 40C738 40 728 78 700 78" +
  "C675 78 668 48 655 48C640 48 632 54 620 54C606 54 600 50 590 50" +
  "C570 50 562 66 545 66C530 66 520 98 500 98C470 98 462 42 445 42" +
  "C428 42 420 58 405 58C392 58 386 46 375 46C350 46 332 86 310 86" +
  "C288 86 278 40 262 40C250 40 240 42 230 42C216 42 210 64 200 64" +
  "C175 64 155 92 130 92C110 92 100 44 85 44C68 44 60 72 45 72" +
  "C22 72 12 52 0 52Z";

// ponytail: the goo filter covers the whole viewport, so every frame blurs a
// full-screen layer. If it ever janks, shrink the filter region to the pool
// band and move the falling bulb out of the filtered group.
export default function HoneyBackdrop() {
  return (
    <svg className="honey" aria-hidden="true">
      <defs>
        <linearGradient id="honey-grad" x2="0" y2="1">
          <stop offset="0" stopColor="#f7cf5c" />
          <stop offset="1" stopColor="#e1932a" />
        </linearGradient>
        {/* Classic goo: blur, then crush the alpha so blobs fuse into one skin.
            The same blur, offset and tinted terracotta, doubles as the shadow. */}
        <filter
          id="honey-goo"
          filterUnits="userSpaceOnUse"
          x="0"
          y="-10%"
          width="100%"
          height="120%"
          colorInterpolationFilters="sRGB"
        >
          {/* 6/18/-7 rather than the usual 7/19/-9: the alpha crush eats anything
              thinner than ~7px, and a necking strand has to stay visible at 70% width. */}
          <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="b" />
          <feColorMatrix in="b" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 18 -7" result="goo" />
          <feOffset in="b" dy="5" result="o" />
          <feFlood floodColor="#8c491a" floodOpacity="0.35" />
          <feComposite in2="o" operator="in" result="sh" />
          <feMerge>
            <feMergeNode in="sh" />
            <feMergeNode in="goo" />
          </feMerge>
        </filter>
      </defs>
      <g filter="url(#honey-goo)" fill="url(#honey-grad)">
        <svg width="100%" height="100" viewBox="0 0 1000 100" preserveAspectRatio="none">
          <path d={POOL} />
        </svg>
        {DRIPS.map(([x, y, w, r, length, cycle, delay]) => (
          // x in vw and y in px put the group inside a pool lobe; the bulb rests
          // there at half size, merged into the pool by the goo until it emerges.
          <g
            key={x}
            style={
              {
                transform: `translate(${x}vw, ${y}px)`,
                "--l": `${length}px`,
                "--t": `${cycle}s`,
                "--d": `${delay}s`,
              } as CSSProperties
            }
          >
            <rect className="strand" x={-w / 2} width={w} height={length} />
            <circle className="bulb" r={r} />
          </g>
        ))}
      </g>
    </svg>
  );
}
