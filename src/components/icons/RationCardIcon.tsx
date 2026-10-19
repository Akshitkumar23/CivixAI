import * as React from 'react';

export const RationCardIcon = (props: React.SVGProps<SVGSVGElement>) => (
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
    <path d="M2 9.5h20" />
    <path d="M2 14.5h20" />
    <path d="M7 9.5v5" />
    <path d="M12 9.5v5" />
    <path d="M17 9.5v5" />
    <rect x={2} y={4} width={20} height={16} rx={2} />
  </svg>
);
