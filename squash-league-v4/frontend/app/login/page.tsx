'use client'
import {useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function Login(){const[email,setEmail]=useState('admin@squash.local');const[pw,setPw]=useState('admin123');const[msg,setMsg]=useState('')
async function go(e:React.FormEvent){e.preventDefault();const r=await fetch(API+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pw})});const x=await r.json();if(r.ok){localStorage.setItem('squash_token',x.access_token);setMsg('Login correcto')}else setMsg(x.detail||'Error')}
return <div className="wrap narrow"><section className="panel"><h1>Acceso</h1><form onSubmit={go}><label>Email<input value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Password<input type="password" value={pw} onChange={e=>setPw(e.target.value)}/></label><button>Entrar</button></form><p>{msg}</p></section></div>}