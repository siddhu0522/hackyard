import React from 'react';

interface LogoProps {
  className?: string;
  size?: number;
}

export const APIVerseLogo: React.FC<LogoProps> = ({ className = "h-7 w-7", size = 28 }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M14 3.5L23.5 9V20L14 25.5L4.5 20V9L14 3.5Z"
        stroke="#8B5CF6"
        strokeWidth="1.75"
        strokeLinejoin="round"
      />
      <path
        d="M14 3.5V14.5L23.5 20"
        stroke="#A78BFA"
        strokeWidth="1.25"
        strokeLinecap="round"
      />
      <path
        d="M14 14.5L4.5 20"
        stroke="#6366F1"
        strokeWidth="1.25"
        strokeLinecap="round"
      />
      <circle cx="14" cy="14.5" r="2.25" fill="#DDD6FE" />
    </svg>
  );
};
