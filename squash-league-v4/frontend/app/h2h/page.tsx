'use client'
import {useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function H2H(){const[a,setA]=useState('1'),[b,setB]=useState('2'),[x,setX]=useState<any>(null)
 async function go(){setX(await fetch(API+`/h2h/${a}/${b}`).then(r=>r.json()))}
 return <div className="wrap narrow"><section className="panel"><h1>Head-to-Head</h1>
 <div className="h2hinputs"><input value={a} onChange={e=>setA(e.target.value)} placeholder="Jugador A ID"/><input value={b} onChange={e=>setB(e.target.value)} placeholder="Jugador B ID"/></div>
 <button onClick={go}>Consultar</button>{x&&<div className="hero"><b>Partidos: {x.matches}</b><p>Jugador A: {x.player_a_wins} victorias</p><p>Jugador B: {x.player_b_wins} victorias</p></div>}</section></div>}
