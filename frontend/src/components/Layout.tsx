import { ReactNode, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getHealth } from '../api/client';
import './Layout.css';

export default function Layout({ children }: { children: ReactNode }) {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    const check = () =>
      getHealth()
        .then(() => setBackendOk(true))
        .catch(() => setBackendOk(false));
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="layout">
      <header className="header">
        <Link to="/upload" className="logo">
          Traffic<span>Vision</span>
        </Link>
        <nav className="nav">
          <Link to="/upload">Upload</Link>
          <span
            className={`health ${backendOk === null ? '' : backendOk ? 'ok' : 'down'}`}
            title={backendOk ? 'Backend online' : 'Backend offline'}
          />
        </nav>
      </header>
      <main className="main">{children}</main>
      <footer className="footer">TrafficVision — Vehicle Counting Dashboard</footer>
    </div>
  );
}
