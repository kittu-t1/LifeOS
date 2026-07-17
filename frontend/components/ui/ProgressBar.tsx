export default function ProgressBar({ value }: { value: number }) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div className="bg-surface-hover h-1.5 w-full overflow-hidden rounded-full">
      <div
        className="bg-accent h-full rounded-full transition-[width]"
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
