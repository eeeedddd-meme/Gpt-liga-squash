'use client'
import {useEffect,useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function Matches(){const[m,setM]=useState<any[]>([]);const load=()=>fetch(API+'/matches').then(r=>r.json()).then(setM);useEffect(()=>{load()},[])
async function gen(){const t=localStorage.getItem('squash_token');const r=await fetch(API+'/seasons/1/generate',{method:'POST',headers:{Authorization:`Bearer ${t}`}});const x=await r.json();alert(r.ok?`Calendario: ${x.rounds} jornadas, ${x.matches} partidos`:x.detail);load()}
return <div className="wrap"><div className="title"><h1>Partidos</h1><button onClick={gen}>Generar calendario</button></div><section className="panel">{m.map(x=><div className="match" key={x.id}><span>J{x.round}</span><b>{x.player_a_name} vs {x.player_b_name}</b><span>{x.status==='played'?`${x.a_sets}-${x.b_sets}`:'Pendiente'}</span></div>)}</section></div>}