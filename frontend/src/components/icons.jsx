const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round",
  strokeLinejoin: "round",
};

export function IconHome({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 10v9a1 1 0 0 0 1 1H9a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1h2.5a1 1 0 0 0 1-1v-9" />
    </svg>
  );
}

export function IconArrowDown({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M12 4v16" />
      <path d="m6 14 6 6 6-6" />
    </svg>
  );
}

export function IconArrowUp({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M12 20V4" />
      <path d="m6 10 6-6 6 6" />
    </svg>
  );
}

export function IconSwap({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M7 8h11l-3.5-3.5" />
      <path d="M17 16H6l3.5 3.5" />
    </svg>
  );
}

export function IconList({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M8 6h12" />
      <path d="M8 12h12" />
      <path d="M8 18h12" />
      <path d="M4 6h.01" />
      <path d="M4 12h.01" />
      <path d="M4 18h.01" />
    </svg>
  );
}

export function IconGauge({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M4.5 19a8.5 8.5 0 1 1 15 0" />
      <path d="M12 13 15.5 9" />
      <circle cx="12" cy="13" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function IconLogout({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" />
      <path d="M10 17l5-5-5-5" />
      <path d="M15 12H3" />
    </svg>
  );
}

export function IconEye({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function IconEyeOff({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M3 3l18 18" />
      <path d="M10.6 5.2A10.6 10.6 0 0 1 12 5c6.5 0 10 7 10 7a15.6 15.6 0 0 1-3.9 4.6" />
      <path d="M6.6 6.6C4 8.3 2 12 2 12s3.5 7 10 7a9.7 9.7 0 0 0 3.4-.6" />
      <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
    </svg>
  );
}

export function IconBank({ className, ...props }) {
  return (
    <svg viewBox="0 0 24 24" className={className} {...base} {...props}>
      <path d="M3 21h18" />
      <path d="M4 21V10" />
      <path d="M20 21V10" />
      <path d="M2 10 12 3l10 7" />
      <path d="M8 21v-6" />
      <path d="M12 21v-6" />
      <path d="M16 21v-6" />
    </svg>
  );
}
