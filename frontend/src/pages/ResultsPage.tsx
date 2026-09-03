import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getVideoResults, outputVideoUrl } from '../api/client';
import { ResultsResponse } from '../api/types';
import StatCard from '../components/StatCard';
import AnalyticsCharts from '../components/AnalyticsCharts';
import './ResultsPage.css';

export default function ResultsPage() {
  const { videoId = '' } = useParams();
  const [results, setResults] = useState<ResultsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getVideoResults(videoId)
      .then(setResults)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load results'));
  }, [videoId]);

  if (error) {
    return (
      <div className="results-page">
        <h2>Results</h2>
        <p className="error-text">{error}</p>
        <Link className="btn" to={`/process/${videoId}`}>Check processing status</Link>
      </div>
    );
  }

  if (!results) return <p className="loading">Loading results…</p>;

  return (
    <div className="results-page">
      <h2>Results</h2>
      <div className="stats-grid">
        <StatCard label="Total Vehicles" value={results.total} accent="#4f8ef7" />
        <StatCard label="Cars" value={results.by_type.car} accent="#57c26b" />
        <StatCard label="Motorcycles" value={results.by_type.motorcycle} accent="#e0b341" />
        <StatCard label="Buses" value={results.by_type.bus} accent="#b07ae8" />
        <StatCard label="Trucks" value={results.by_type.truck} accent="#e0703a" />
        <StatCard label="Entering" value={results.entering} accent="#3ac8c8" />
        <StatCard label="Exiting" value={results.exiting} accent="#e05a7a" />
      </div>

      <section className="panel">
        <h3>Annotated Video</h3>
        <video className="player" controls preload="metadata" src={outputVideoUrl(videoId)} />
        <div className="player-meta">
          <a className="btn" href={outputVideoUrl(videoId)} download={`annotated-${videoId}.mp4`}>
            Download Video
          </a>
          <span>Processed in {results.processing_time_s.toFixed(1)} s</span>
          <span>Processed at {results.processing_fps.toFixed(1)} FPS</span>
        </div>
      </section>

      <AnalyticsCharts results={results} />
    </div>
  );
}
