'use client'
import {useEffect,useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function Admin(){
 const [o,setO]=useState<any>(null),[rounds,setRounds]=useState<any[]>([])
 const load=async()=>{const t=localStorage.getItem('squash_token');const h={Authorization:`Bearer ${t}`};
  const [a,r]=await Promise.all([fetch(API+'/admin/overview',{headers:h}),fetch(API+'/rounds?season_id=1')]);
  setO(a.ok?await a.json():null);setRounds(await r.json())}
 useEffect(()=>{load()},[])
 async function schedule(id:number){const t=localStorage.getItem('squash_token');await fetch(API+`/rounds/${id}/schedule`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({date:'2026-09-20',time:'18:00',court:'Pista 1',deadline:'2026-09-27'})});load()}
 return <div className="wrap"><h1>Administración</h1>
 {o&&<div className="cards"><div><small>JUGADORES</small><b>{o.players}</b></div><div><small>PARTIDOS</small><b>{o.matches}</b></div><div><small>PENDIENTES</small><b>{o.pending}</b></div></div>}
 <section className="panel"><h2>Jornadas</h2>{rounds.map(r=><div className="row" key={r.id}><b>Jornada {r.number}</b><span>{r.scheduled_date||'Sin fecha'} <button onClick={()=>schedule(r.id)}>Programar</button></span></div>)}</section>
 </div>
}
