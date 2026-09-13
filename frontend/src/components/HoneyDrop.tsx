export default function HoneyDrop({ size = 64 }: { size?: number }) {
  // The art lives in public/favicon.svg — one file, pointed at from here and
  // from routes/admin.py, instead of three inline copies that drifted apart.
  // `size` is the width; the art is 11x13 cells, so a square box letterboxed it
  // at a fractional scale and the rows sheared apart. Snap to whole-pixel cells.
  const cell = Math.max(1, Math.round(size / 11));
  return <img src="/favicon.svg" width={cell * 11} height={cell * 13} alt="" />;
}
