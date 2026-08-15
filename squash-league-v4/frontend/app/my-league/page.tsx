'use client'
import {useEffect,useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function MyLeague(){
 const [matches,setMatches]=useState<any[]>([]),[loading,setLoading]=useState(true)
 useEffect(()=>{const t=localStorage.getItem('squash_token');fetch(API+'/me/matches',{headers:{Authorization:`Bearer ${t}`}})
 .then(r=>r.ok?r.json():[]).then(x=>{setMatches(x);setLoading(false)})},[])
 if(loading)return <div className="wrap"><p>Cargando...</p></div>
 const next=matches.find(x=>x.status==='pending')
 return <div className="wrap">
  <section className="hero"><small>MI LIGA</small><h1>Tu competición</h1>
  {next?<><p>Próximo partido · Jornada {next.round}</p><div className="next"><b>VS {next.opponent}</b>
  <button onClick={()=>location.href=`/matches/${next.id}`}>Gestionar disponibilidad</button></div></>:<p>No tienes partidos pendientes.</p>}</section>
  <section className="panel"><h2>Mis partidos</h2>{matches.map(m=><div className="match" key={m.id}>
   <span>J{m.round}</span><b>vs {m.opponent}</b><span>{m.status==='played'?m.score:'Pendiente'}</span>
  </div>)}</section>
 </div>
}
