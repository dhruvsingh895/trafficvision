import './StatCard.css';

interface Props {
  label: string;
  value: number | string;
  accent?: string;
}

export default function StatCard({ label, value, accent }: Props) {
  return (
    <div className="stat-card" style={accent ? { borderTopColor: accent } : undefined}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
