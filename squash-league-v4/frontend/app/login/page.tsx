'use client';

import { useState } from 'react';
import { apiCall, API_ENDPOINTS } from '../utils/api';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@squash.local');
  const [password, setPassword] = useState('admin123');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');

    try {
      const result = await apiCall<{ access_token: string; role: string }>(
        API_ENDPOINTS.LOGIN,
        {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        }
      );

      if (result.data) {
        localStorage.setItem('squash_token', result.data.access_token);
        localStorage.setItem('user_role', result.data.role);
        setMessage('✓ Login correcto. Redirigiendo...');
        setTimeout(() => router.push('/'), 1000);
      } else {
        setMessage(`✗ ${result.error || 'Error de autenticación'}`);
      }
    } catch (error) {
      setMessage('✗ Error de conexión');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="wrap narrow">
      <section className="panel">
        <h1>Acceso</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </label>
          <label>
            Contraseña
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        {message && <p className={message.startsWith('✓') ? 'success' : 'error'}>{message}</p>}
      </section>
    </div>
  );
}