'use client';

import { useEffect, useState } from 'react';
import { apiCallWithAuth, API_ENDPOINTS } from '../../utils/api';

interface SetScore {
  player_a: number;
  player_b: number;
}

export default function MatchDetailPage({ params }: { params: { id: string } }) {
  const [sets, setSets] = useState<[string, string][]>([
    ['11', '8'],
    ['11', '9'],
    ['11', '7'],
  ]);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSaveAvailability(status: string) {
    setIsLoading(true);
    setMessage('');

    const result = await apiCallWithAuth(`/matches/${params.id}/availability`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    });

    if (result.status === 200) {
      setMessage('✓ Disponibilidad guardada');
    } else {
      setMessage(`✗ ${result.error || 'Error al guardar disponibilidad'}`);
    }

    setIsLoading(false);
  }

  async function handleSaveResult() {
    setIsLoading(true);
    setMessage('');

    const result = await apiCallWithAuth(`/matches/${params.id}/result`, {
      method: 'POST',
      body: JSON.stringify({ sets }),
    });

    if (result.status === 200) {
      setMessage('✓ Resultado guardado y ELO actualizado');
    } else {
      setMessage(`✗ ${result.error || 'Error al guardar resultado'}`);
    }

    setIsLoading(false);
  }

  function handleSetScoreChange(index: number, playerIndex: 0 | 1, value: string) {
    const newSets = [...sets];
    const set = [...newSets[index]];
    set[playerIndex] = value;
    newSets[index] = [set[0], set[1]];
    setSets(newSets);
  }

  return (
    <div className="wrap narrow">
      <section className="panel">
        <h1>Gestionar partido</h1>

        <h2>Disponibilidad</h2>
        <div className="actions">
          <button
            onClick={() => handleSaveAvailability('available')}
            disabled={isLoading}
          >
            Puedo jugar
          </button>
          <button
            onClick={() => handleSaveAvailability('unavailable')}
            disabled={isLoading}
          >
            No puedo
          </button>
        </div>

        <h2>Resultado</h2>
        {sets.map((score, index) => (
          <div className="set" key={index}>
            <b>Set {index + 1}</b>
            <input
              type="number"
              value={score[0]}
              onChange={(e) => handleSetScoreChange(index, 0, e.target.value)}
              placeholder="Puntos A"
              min="0"
              disabled={isLoading}
            />
            <span>-</span>
            <input
              type="number"
              value={score[1]}
              onChange={(e) => handleSetScoreChange(index, 1, e.target.value)}
              placeholder="Puntos B"
              min="0"
              disabled={isLoading}
            />
          </div>
        ))}

        <button onClick={handleSaveResult} disabled={isLoading}>
          {isLoading ? 'Guardando...' : 'Guardar resultado'}
        </button>

        {message && (
          <p style={{ color: message.startsWith('✓') ? 'green' : 'red' }}>
            {message}
          </p>
        )}
      </section>
    </div>
  );
}
