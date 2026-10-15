// Teal rounded-square logo with a white heartbeat/pulse line, matching the
// reference app's brand mark.
export default function PulseLogo({ size = 40 }) {
  return (
    <span
      className="pulse-logo"
      style={{ width: size, height: size, borderRadius: size * 0.28 }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 24 24" width={size * 0.62} height={size * 0.62} fill="none">
        <path
          d="M2 12h3.5l2-5 3 10 2.5-7 1.8 2H22"
          stroke="#ffffff"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}
