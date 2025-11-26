import React from 'react'

export default function Leaderboard(){
  return (
    <main style={{padding:28}}>
      <h1 style={{textAlign:'center',color:'var(--purple)'}}>Leaderboard</h1>
      <div className="card" style={{marginTop:24}}>
        <div className="leaderboard-hero">
          <div className="podium">Luana<br/><small>7 h 02 m</small></div>
          <div className="podium" style={{transform:'scale(1.1)'}}>Marcelo<br/><small>6 h 18 m</small></div>
          <div className="podium">Sofia<br/><small>8 h 05 m</small></div>
        </div>

        <div style={{background:'#f3f4fb',padding:18,borderRadius:12}}>
          <ol>
            <li>Paul — 8 h 35 m</li>
            <li>Robert — 8 h 53 m</li>
            <li>Gwen — 9 h 16 m</li>
            <li>You — 10 h 23 m</li>
            <li>Emma — 12 h 04 m</li>
          </ol>
        </div>
      </div>
    </main>
  )
}
