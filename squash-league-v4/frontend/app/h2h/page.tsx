'use client';

import { useState } from 'react';
import { apiCall, API_ENDPOINTS } from '../utils/api';

interface H2HResult {
  matches: number;
  player_a_wins: number;
  player_b_wins: number;
}

export default function H2HPage() {
  const [playerA, setPlayerA] = useState('1');
  const [playerB, setPlayerB] = useState('2');
  const [result, setResult] = useState<H2HResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleQuery() {
    setIsLoading(true);
    setError('');

    const queryResult = await apiCall<H2HResult>(`${API_ENDPOINTS.H2H}/${playerA}/${playerB}`);

    if (queryResult.data) {
      setResult(queryResult.data);
    } else {
      setError(queryResult.error || 'Error al consultar H2H');
    }

    setIsLoading(false);
  }

  return (
    <div className="wrap narrow">
      <section className="panel">
        <h1>Head-to-Head</h1>
        <div className="h2hinputs">
          <input
            type="number"
            value={playerA}
            onChange={(e) => setPlayerA(e.target.value)}
            placeholder="Jugador A ID"
            disabled={isLoading}
          />
          <input
            type="number"
            value={playerB}
            onChange={(e) => setPlayerB(e.target.value)}
            placeholder="Jugador B ID"
            disabled={isLoading}
          />
        </div>
        <button onClick={handleQuery} disabled={isLoading}>
          {isLoading ? 'Consultando...' : 'Consultar'}
        </button>

        {error && <p style={{ color: 'red' }}>{error}</p>}

        {result && (
          <div className="hero">
            <b>Partidos: {result.matches}</b>
            <p>Jugador A: {result.player_a_wins} victorias</p>
            <p>Jugador B: {result.player_b_wins} victorias</p>
          </div>
        )}
      </section>
    </div>
  );
}
