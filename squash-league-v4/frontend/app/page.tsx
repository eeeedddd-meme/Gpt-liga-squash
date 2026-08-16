import { apiCall, API_ENDPOINTS } from './utils/api';

interface Standing {
  id: number;
  name: string;
  elo: number;
  played: number;
  wins: number;
  losses: number;
  points: number;
  sets_for: number;
  sets_against: number;
}

interface Match {
  id: number;
  player_a_name: string;
  player_b_name: string;
  status: string;
  a_sets: number;
  b_sets: number;
}

interface Player {
  id: number;
  name: string;
}

export default async function Home() {
  const [standingsRes, matchesRes, playersRes] = await Promise.all([
    apiCall<Standing[]>(API_ENDPOINTS.STANDINGS, { cache: 'no-store' }),
    apiCall<Match[]>(API_ENDPOINTS.MATCHES, { cache: 'no-store' }),
    apiCall<Player[]>(API_ENDPOINTS.PLAYERS, { cache: 'no-store' }),
  ]);

  const standings = standingsRes.data || [];
  const matches = matchesRes.data || [];
  const players = playersRes.data || [];

  const playedMatches = matches.filter((m) => m.status === 'played').length;

  return (
    <div className="wrap">
      <section className="hero">
        <small>TEMPORADA 2026/27</small>
        <h1>Squash League</h1>
        <p>Gestión de jugadores, jornadas, resultados, clasificación y ELO.</p>
      </section>

      <div className="cards">
        <div>
          <small>JUGADORES</small>
          <b>{players.length}</b>
        </div>
        <div>
          <small>PARTIDOS</small>
          <b>{matches.length}</b>
        </div>
        <div>
          <small>JUGADOS</small>
          <b>{playedMatches}</b>
        </div>
      </div>

      <section className="panel">
        <h2>Clasificación</h2>
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
                <td>
                  <b>{player.name}</b>
                </td>
                <td>{player.played}</td>
                <td>{player.wins}</td>
                <td>{player.losses}</td>
                <td>
                  {player.sets_for}-{player.sets_against}
                </td>
                <td>{player.elo}</td>
                <td>
                  <b>{player.points}</b>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}