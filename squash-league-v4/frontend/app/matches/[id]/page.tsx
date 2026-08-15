'use client'
import {useEffect,useState} from 'react'
const API=process.env.NEXT_PUBLIC_API_URL||'http://localhost:8000'
export default function Match({params}:{params:{id:string}}){
 const [sets,setSets]=useState([['11','8'],['11','9'],['11','7']]),[msg,setMsg]=useState('')
 const save=async(status:string)=>{const t=localStorage.getItem('squash_token');const r=await fetch(API+`/matches/${params.id}/availability`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({status})});setMsg(r.ok?'Disponibilidad guardada':(await r.json()).detail)}
 const result=async()=>{const t=localStorage.getItem('squash_token');const r=await fetch(API+`/matches/${params.id}/result`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({sets})});setMsg(r.ok?'Resultado guardado y ELO actualizado':(await r.json()).detail)}
 return <div className="wrap narrow"><section className="panel"><h1>Gestionar partido</h1>
 <h2>Disponibilidad</h2><div className="actions"><button onClick={()=>save('available')}>Puedo jugar</button><button onClick={()=>save('unavailable')}>No puedo</button></div>
 <h2>Resultado</h2>{sets.map((x,i)=><div className="set" key={i}><b>Set {i+1}</b><input value={x[0]} onChange={e=>{const a=[...sets];a[i]=[e.target.value,a[i][1]];setSets(a)}}/><input value={x[1]} onChange={e=>{const a=[...sets];a[i]=[a[i][0],e.target.value];setSets(a)}}/></div>}
 <button onClick={result}>Guardar resultado</button><p>{msg}</p></section></div>
}
