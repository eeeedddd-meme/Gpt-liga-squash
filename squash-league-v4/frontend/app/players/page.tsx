'use client';

import { useEffect, useState } from 'react';
import { apiCall, apiCallWithAuth, API_ENDPOINTS } from '../utils/api';

interface Player {
  id: number;
  name: string;
  email?: string;
  level: string;
  elo: number;
}

export default function PlayersPage() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadPlayers();
  }, []);

  async function loadPlayers() {
    const result = await apiCall<Player[]>(API_ENDPOINTS.PLAYERS);
    if (result.data) {
      setPlayers(result.data);
    }
  }

  async function handleAddPlayer(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    const result = await apiCallWithAuth<Player>(API_ENDPOINTS.PLAYERS, {
      method: 'POST',
      body: JSON.stringify({ name }),
    });

    if (result.data) {
      setName('');
      await loadPlayers();
    } else {
      setError(result.error || 'Error al añadir jugador');
    }

    setIsLoading(false);
  }

  return (
    <div className="wrap">
      <h1>Jugadores</h1>
      <section className="panel">
        <form onSubmit={handleAddPlayer}>
          <input
            type="text"
            placeholder="Nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Añadiendo...' : 'Añadir'}
          </button>
        </form>
        {error && <p style={{ color: 'red' }}>{error}</p>}

        <div>
          {players.map((player) => (
            <div className="row" key={player.id}>
              <b>{player.name}</b>
              <span>
                {player.level} · ELO {player.elo}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}