'use client'
import {useEffect,useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function Players(){const[p,setP]=useState<any[]>([]);const[name,setName]=useState('');const load=()=>fetch(API+'/players').then(r=>r.json()).then(setP);useEffect(()=>{load()},[])
async function add(e:React.FormEvent){e.preventDefault();const t=localStorage.getItem('squash_token');await fetch(API+'/players',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({name})});setName('');load()}
return <div className="wrap"><h1>Jugadores</h1><section className="panel"><form onSubmit={add}><input placeholder="Nombre" value={name} onChange={e=>setName(e.target.value)} required/><button>Añadir</button></form>{p.map(x=><div className="row" key={x.id}><b>{x.name}</b><span>{x.level} · ELO {x.elo}</span></div>)}</section></div>}