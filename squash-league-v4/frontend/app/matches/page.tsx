'use client';

import { useEffect, useState } from 'react';
import { apiCall, apiCallWithAuth, API_ENDPOINTS } from '../utils/api';

interface Match {
  id: number;
  round: number;
  player_a_name: string;
  player_b_name: string;
  status: string;
  a_sets?: number;
  b_sets?: number;
}

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadMatches();
  }, []);

  async function loadMatches() {
    const result = await apiCall<Match[]>(API_ENDPOINTS.MATCHES);
    if (result.data) {
      setMatches(result.data);
    }
  }

  async function handleGenerateSchedule() {
    setIsLoading(true);
    setMessage('Generando calendario...');

    const result = await apiCallWithAuth<{ rounds: number; matches: number }>(
      '/seasons/1/generate',
      { method: 'POST' }
    );

    if (result.data) {
      setMessage(`✓ Calendario: ${result.data.rounds} jornadas, ${result.data.matches} partidos`);
      await loadMatches();
    } else {
      setMessage(`✗ ${result.error || 'Error al generar calendario'}`);
    }

    setIsLoading(false);
  }

  return (
    <div className="wrap">
      <div className="title">
        <h1>Partidos</h1>
        <button onClick={handleGenerateSchedule} disabled={isLoading}>
          {isLoading ? 'Generando...' : 'Generar calendario'}
        </button>
      </div>
      {message && <p>{message}</p>}

      <section className="panel">
        {matches.map((match) => (
          <div className="match" key={match.id}>
            <span>J{match.round}</span>
            <b>
              {match.player_a_name} vs {match.player_b_name}
            </b>
            <span>
              {match.status === 'played' ? `${match.a_sets}-${match.b_sets}` : 'Pendiente'}
            </span>
          </div>
        ))}
      </section>
    </div>
  );
}