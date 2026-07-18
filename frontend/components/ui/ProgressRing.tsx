/**
 * Circular progress indicator (Apple Fitness "activity ring" style) -
 * an alternative to ProgressBar for contexts where a glanceable ring
 * reads better than a linear bar, currently used by GoalCard. Pure SVG,
 * no dependencies: a silver track circle plus an accent-colored arc
 * whose `stroke-dashoffset` is driven by `value`, rotated so progress
 * starts at 12 o'clock and sweeps clockwise like a watch face.
 */
export default function ProgressRing({
  value,
  size = 56,
  strokeWidth = 5,
}: {
  value: number;
  size?: number;
  strokeWidth?: number;
}) {
  const clamped = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - clamped / 100);

  return (
    <div
      className="relative inline-flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--silver)"
          strokeOpacity={0.25}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]"
        />
      </svg>
      <span className="text-foreground absolute text-xs font-semibold">{clamped}%</span>
    </div>
  );
}
