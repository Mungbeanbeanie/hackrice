export default function HoneyDrop({ size = 64 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 11 13"
      style={{ imageRendering: "pixelated" }}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* tip top */}
      <rect x="5" y="0" width="1" height="1" fill="#E87D00" />
      {/* row 1 */}
      <rect x="4" y="1" width="3" height="1" fill="#F5A623" />
      {/* row 2 */}
      <rect x="3" y="2" width="5" height="1" fill="#F5A623" />
      {/* row 3 */}
      <rect x="2" y="3" width="7" height="1" fill="#FFCC02" />
      {/* row 4 */}
      <rect x="1" y="4" width="9" height="1" fill="#FFCC02" />
      {/* row 5 */}
      <rect x="1" y="5" width="9" height="1" fill="#FFD740" />
      {/* eyes row */}
      <rect x="1" y="6" width="9" height="1" fill="#FFD740" />
      <rect x="3" y="6" width="2" height="2" fill="#1a0800" />
      <rect x="6" y="6" width="2" height="2" fill="#1a0800" />
      {/* row 7 */}
      <rect x="1" y="7" width="9" height="1" fill="#FFD740" />
      {/* row 8 */}
      <rect x="1" y="8" width="9" height="1" fill="#FFCC02" />
      {/* row 9 */}
      <rect x="2" y="9" width="7" height="1" fill="#F5A623" />
      {/* row 10 */}
      <rect x="3" y="10" width="5" height="1" fill="#F5A623" />
      {/* row 11 */}
      <rect x="4" y="11" width="3" height="1" fill="#E87D00" />
      {/* bottom tip */}
      <rect x="5" y="12" width="1" height="1" fill="#D06800" />
      {/* highlight sheen */}
      <rect x="2" y="3" width="2" height="2" fill="#FFF176" fillOpacity="0.5" />
    </svg>
  );
}
