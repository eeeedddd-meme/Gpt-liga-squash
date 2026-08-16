'use client';

import { useEffect, useState } from 'react';
import { apiCallWithAuth, API_ENDPOINTS } from '../utils/api';
import Link from 'next/link';

interface UserMatch {
  id: number;
  round: number;
  opponent: string;
  home: boolean;
  status: string;
  score?: string;
}

export default function MyLeaguePage() {
  const [matches, setMatches] = useState<UserMatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadUserMatches();
  }, []);

  async function loadUserMatches() {
    const result = await apiCallWithAuth<UserMatch[]>(API_ENDPOINTS.MY_MATCHES);

    if (result.data) {
      setMatches(result.data);
    }

    setIsLoading(false);
  }

  if (isLoading) {
    return (
      <div className="wrap">
        <p>Cargando...</p>
      </div>
    );
  }

  const nextMatch = matches.find((m) => m.status === 'pending');

  return (
    <div className="wrap">
      <section className="hero">
        <small>MI LIGA</small>
        <h1>Tu competición</h1>

        {nextMatch ? (
          <>
            <p>Próximo partido · Jornada {nextMatch.round}</p>
            <div className="next">
              <b>VS {nextMatch.opponent}</b>
              <Link href={`/matches/${nextMatch.id}`}>
                <button>Gestionar disponibilidad</button>
              </Link>
            </div>
          </>
        ) : (
          <p>No tienes partidos pendientes.</p>
        )}
      </section>

      <section className="panel">
        <h2>Mis partidos</h2>
        {matches.map((match) => (
          <div className="match" key={match.id}>
            <span>J{match.round}</span>
            <b>vs {match.opponent}</b>
            <span>{match.status === 'played' ? match.score : 'Pendiente'}</span>
          </div>
        ))}
      </section>
    </div>
  );
}
