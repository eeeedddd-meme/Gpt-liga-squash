import './globals.css';
import Link from 'next/link';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <header>
          <b>
            SQUASH <span>LEAGUE</span>
          </b>
          <nav>
            <Link href="/">Dashboard</Link>
            <Link href="/standings">Clasificación</Link>
            <Link href="/matches">Partidos</Link>
            <Link href="/players">Jugadores</Link>
            <Link href="/my-league">Mi liga</Link>
            <Link href="/h2h">H2H</Link>
            <Link href="/admin">Admin</Link>
            <Link href="/login">Login</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}