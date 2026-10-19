import * as React from 'react';

export const AadharCardIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={2}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect x={3} y={5} width={18} height={14} rx={2} ry={2} />
    <path d="M7 12h4" />
    <path d="M13 12h4" />
    <path d="M7 16h10" />
    <path d="M9 8h6" />
  </svg>
);
