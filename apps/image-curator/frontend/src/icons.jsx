import React from "react";

// Bits & Flames glyphs use a 16px grid, matching Gluma's compact interface.
// Keep these local so installed Curate does not require another repository.
function pixelIcon(path) {
  return function PixelIcon({ className = "", size = 16, ...props }) {
    return (
      <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor"
        stroke="none" shapeRendering="crispEdges" aria-hidden="true" focusable="false"
        className={`bf-pixel-icon ${className}`} {...props}>
        <path d={path} fillRule="evenodd" />
      </svg>
    );
  };
}

export const AlertCircle = pixelIcon("M7 1h2v2h2v3h2v3h2v6H1V9h2V6h2V3h2zM7 4V7H5v3H3v3h10v-3h-2V7H9V4zM7 6h2v4H7zM7 11h2v2H7z");
export const Check = pixelIcon("M1 7h2v2h2v2h2V9h2V7h2V5h2V3h2v4h-2v2h-2v2H9v2H7v2H5v-2H3v-2H1z");
export const CheckCircle2 = pixelIcon("M1 7h2v2h2v2h2V9h2V7h2V5h2V3h2v4h-2v2h-2v2H9v2H7v2H5v-2H3v-2H1z");
export const ChevronDown = pixelIcon("M2 5h2v2h2v2h4V7h2V5h2v4h-2v2h-2v2H6v-2H4V9H2z");
export const Copy = pixelIcon("M1 1h9v2H3v8H1zM5 5h10v10H5zM7 7v6h6V7z");
export const Download = pixelIcon("M7 1h2v7h3v2h-2v2H6v-2H4V8h3zM1 12h2v2h10v-2h2v4H1z");
export const FolderUp = pixelIcon("M1 3h5v2h9v9H1zM3 7v5h10V7zM8 1h2v2h2v2h-2V3H8v2H6V3h2z");
export const ImageIcon = pixelIcon("M1 1h14v14H1zM3 3v10h10V3zM4 4h3v3H4zM8 7h2v2h2v3H4v-2h2V8h2z");
export const Info = pixelIcon("M4 1h8v2H4zM2 3h2v10H2zM12 3h2v10h-2zM4 13h8v2H4zM7 4h2v2H7zM7 8h2v4H7z");
export const Keyboard = pixelIcon("M0 3h16v10H0zM2 5v6h12V5zM3 6h1v1H3zM6 6h1v1H6zM9 6h1v1H9zM12 6h1v1h-1zM4 9h8v1H4z");
export const LayoutDashboard = pixelIcon("M1 1h14v14H1zM3 3v10h6V3zM11 3v10h2V3z");
export const Loader2 = pixelIcon("M5 1h6v2h2V1h2v6H9V5h2V3H5v2H3v6h2v2h6v-2h2v2h-2v2H5v-2H3v-2H1V5h2V3h2z");
export const Maximize2 = pixelIcon("M1 1h6v2H3v4H1zM9 1h6v6h-2V3H9zM1 9h2v4h4v2H1zM13 9h2v6H9v-2h4z");
export const Menu = pixelIcon("M1 2h14v2H1zM1 7h14v2H1zM1 12h14v2H1z");
export const Plus = pixelIcon("M7 2h2v5h5v2H9v5H7V9H2V7h5z");
export const RotateCcw = pixelIcon("M5 1h6v2h2V1h2v6H9V5h2V3H5v2H3v6h2v2h6v-2h2v2h-2v2H5v-2H3v-2H1V5h2V3h2z");
export const Search = pixelIcon("M3 1h6v2H3zM1 3h2v6H1zM9 3h2v6H9zM3 9h6v2H3zM10 10h2v2h2v2h2v2h-3v-2h-2v-2h-1z");
export const SlidersHorizontal = pixelIcon("M4 1h2v4H4zM0 6h10v2H0zM4 9h2v6H4zM11 1h2v8h-2zM7 10h9v2H7zM11 13h2v2h-2z");
export const X = pixelIcon("M2 2h2v2h2v2h4V4h2V2h2v2h-2v2h-2v4h2v2h2v2h-2v-2h-2v-2H6v2H4v2H2v-2h2v-2h2V6H4V4H2z");
export const ArrowLeft = pixelIcon("M14 7H5V5h2V3H5v2H3v2H1v2h2v2h2v2h2v-2H5V9h9z");
export const ArrowRight = pixelIcon("M2 7h9V5H9V3h2v2h2v2h2v2h-2v2h-2v2H9v-2h2V9H2z");
