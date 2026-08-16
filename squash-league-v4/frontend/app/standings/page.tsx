import { apiCall, API_ENDPOINTS } from '../utils/api';

interface Standing {
  id: number;
  name: string;
  played: number;
  wins: number;
  losses: number;
  sets_for: number;
  sets_against: number;
  elo: number;
  points: number;
}

export default async function StandingsPage() {
  const result = await apiCall<Standing[]>(API_ENDPOINTS.STANDINGS, {
    cache: 'no-store',
  });

  const standings = result.data || [];

  return (
    <div className="wrap">
      <h1>Clasificación</h1>
      <section className="panel">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Jugador</th>
              <th>PJ</th>
              <th>PG</th>
              <th>PP</th>
              <th>Sets</th>
              <th>ELO</th>
              <th>Pts</th>
            </tr>
          </thead>
          <tbody>
            {standings.map((player, index) => (
              <tr key={player.id}>
                <td>{index + 1}</td>
                <td>{player.name}</td>
                <td>{player.played}</td>
                <td>{player.wins}</td>
                <td>{player.losses}</td>
                <td>
                  {player.sets_for}-{player.sets_against}
                </td>
                <td>{player.elo}</td>
                <td>{player.points}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}