import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ResultsResponse } from '../api/types';
import './AnalyticsCharts.css';

const COLORS = ['#57c26b', '#e0b341', '#b07ae8', '#e0703a'];

export default function AnalyticsCharts({ results }: { results: ResultsResponse }) {
  const pieData = [
    { name: 'Cars', value: results.by_type.car },
    { name: 'Motorcycles', value: results.by_type.motorcycle },
    { name: 'Buses', value: results.by_type.bus },
    { name: 'Trucks', value: results.by_type.truck },
  ].filter((d) => d.value > 0);

  const flowData = [
    { name: 'Entering', count: results.entering },
    { name: 'Exiting', count: results.exiting },
  ];

  return (
    <div className="charts-grid">
      <section className="panel chart">
        <h3>Vehicle Type Distribution</h3>
        <ResponsiveContainer width="100%" height={280}>
          <PieChart>
            <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={100} label>
              {pieData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </section>

      <section className="panel chart">
        <h3>Entering vs Exiting</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={flowData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3140" />
            <XAxis dataKey="name" stroke="#9aa4b5" />
            <YAxis allowDecimals={false} stroke="#9aa4b5" />
            <Tooltip />
            <Bar dataKey="count" fill="#4f8ef7" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="panel chart wide">
        <h3>Cumulative Vehicles Over Time</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={results.timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a3140" />
            <XAxis dataKey="t" stroke="#9aa4b5" tickFormatter={(t: number) => `${t}s`} />
            <YAxis allowDecimals={false} stroke="#9aa4b5" />
            <Tooltip formatter={(v: number) => [v, 'Count']} labelFormatter={(t) => `${t} s`} />
            <Line type="monotone" dataKey="count" stroke="#3ac8c8" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </section>
    </div>
  );
}
