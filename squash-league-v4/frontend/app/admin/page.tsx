'use client';

import { useEffect, useState } from 'react';
import { apiCallWithAuth, API_ENDPOINTS } from '../utils/api';

interface AdminOverview {
  seasons: number;
  players: number;
  matches: number;
  played: number;
  pending: number;
}

interface Round {
  id: number;
  number: number;
  scheduled_date?: string;
}

export default function AdminPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [rounds, setRounds] = useState<Round[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadAdminData();
  }, []);

  async function loadAdminData() {
    const [overviewRes, roundsRes] = await Promise.all([
      apiCallWithAuth<AdminOverview>(API_ENDPOINTS.ADMIN_OVERVIEW),
      apiCallWithAuth<Round[]>(API_ENDPOINTS.ROUNDS),
    ]);

    if (overviewRes.data) setOverview(overviewRes.data);
    if (roundsRes.data) setRounds(roundsRes.data);
  }

  async function handleScheduleRound(roundId: number) {
    setIsLoading(true);

    await apiCallWithAuth(`/rounds/${roundId}/schedule`, {
      method: 'POST',
      body: JSON.stringify({
        date: '2026-09-20',
        time: '18:00',
        court: 'Pista 1',
        deadline: '2026-09-27',
      }),
    });

    setIsLoading(false);
    await loadAdminData();
  }

  return (
    <div className="wrap">
      <h1>Administración</h1>

      {overview && (
        <div className="cards">
          <div>
            <small>JUGADORES</small>
            <b>{overview.players}</b>
          </div>
          <div>
            <small>PARTIDOS</small>
            <b>{overview.matches}</b>
          </div>
          <div>
            <small>JUGADOS</small>
            <b>{overview.played}</b>
          </div>
          <div>
            <small>PENDIENTES</small>
            <b>{overview.pending}</b>
          </div>
        </div>
      )}

      <section className="panel">
        <h2>Jornadas</h2>
        {rounds.map((round) => (
          <div className="row" key={round.id}>
            <b>Jornada {round.number}</b>
            <span>
              {round.scheduled_date || 'Sin fecha'}{' '}
              <button onClick={() => handleScheduleRound(round.id)} disabled={isLoading}>
                Programar
              </button>
            </span>
          </div>
        ))}
      </section>
    </div>
  );
}
