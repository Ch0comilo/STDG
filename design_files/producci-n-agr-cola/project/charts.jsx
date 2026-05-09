// charts.jsx — shared chart components

// ─── COLOR SCALE ─────────────────────────────────────────────────────────────
function getChoroColor(t) {
  // cream → yellow-green → deep forest green
  if (t < 0.2)  return `oklch(${90 - t*20}% ${0.04 + t*0.12} 115)`;
  if (t < 0.45) return `oklch(${80 - t*18}% ${0.14 + t*0.08} 135)`;
  if (t < 0.70) return `oklch(${62 - t*14}% 0.20 145)`;
  return `oklch(${46 - t*8}% 0.22 150)`;
}

// ─── INTERACTIVE COLOMBIA MAP ─────────────────────────────────────────────────
function ColombiaMap({ data, colorKey, year, selectedId, onSelect, colorMode = 'choro', lisaColors }) {
  const [tooltip, setTooltip] = React.useState(null);
  const [hoverId, setHoverId] = React.useState(null);

  const filtered = React.useMemo(() =>
    data.filter(d => d.year === year), [data, year]);

  const vals = filtered.map(d => d[colorKey] ?? 0);
  const mn = Math.min(...vals), mx = Math.max(...vals);
  const norm = v => (v - mn) / (mx - mn + 0.001);

  const LISA_FILL = { HH:'#22c55e', LL:'#ef4444', HL:'#3b82f6', LH:'#f59e0b', NS:'#334155' };

  const W = 400, H = 340;
  const toX = lon => ((lon - (-79.5)) / ((-66) - (-79.5))) * (W - 40) + 20;
  const toY = lat => H - ((lat - (-5)) / (14 - (-5))) * (H - 40) - 20;

  return (
    <div style={{ position: 'relative', userSelect: 'none' }}>
      <svg width={W} height={H} style={{ display: 'block', overflow: 'visible' }}
        onMouseLeave={() => { setTooltip(null); setHoverId(null); }}>

        {/* Colombia silhouette */}
        <polygon
          points="82,22 130,10 190,8 240,14 285,30 318,60 338,95 348,138 340,178 322,210 298,248 265,278 228,304 188,318 148,316 108,298 70,268 40,228 22,185 18,140 28,98 50,62 82,22"
          fill="oklch(20% 0.035 145)"
          stroke="oklch(33% 0.07 145)"
          strokeWidth="1.5"
        />

        {/* Region highlight zones — subtle */}
        {filtered.map((d, i) => {
          const cx = toX(d.lon), cy = toY(d.lat);
          if (cx < 15 || cx > W - 15 || cy < 15 || cy > H - 15) return null;

          const isSelected = d.id === selectedId;
          const isHovered  = d.id === hoverId;

          let fill;
          if (colorMode === 'lisa' && lisaColors) {
            fill = LISA_FILL[lisaColors[i]?.lisa ?? 'NS'] ?? '#334155';
          } else {
            fill = getChoroColor(norm(d[colorKey] ?? 0));
          }

          return (
            <g key={d.id}>
              {(isSelected || isHovered) && (
                <circle cx={cx} cy={cy} r={isSelected ? 11 : 9}
                  fill="none" stroke={isSelected ? '#fff' : 'rgba(255,255,255,0.5)'}
                  strokeWidth={isSelected ? 2 : 1} />
              )}
              <circle
                cx={cx} cy={cy}
                r={isSelected ? 7 : isHovered ? 6 : 5}
                fill={fill}
                stroke={isSelected ? '#fff' : 'rgba(0,0,0,0.3)'}
                strokeWidth={isSelected ? 1.5 : 0.5}
                style={{ cursor: 'pointer', transition: 'r 0.1s' }}
                onMouseEnter={e => {
                  setHoverId(d.id);
                  setTooltip({ x: e.clientX, y: e.clientY, d });
                }}
                onMouseMove={e => setTooltip(t => t ? { ...t, x: e.clientX, y: e.clientY } : null)}
                onMouseLeave={() => { setHoverId(null); setTooltip(null); }}
                onClick={() => onSelect && onSelect(d.id === selectedId ? null : d.id)}
              />
            </g>
          );
        })}

        {/* Selected label */}
        {selectedId != null && (() => {
          const sel = filtered.find(d => d.id === selectedId);
          if (!sel) return null;
          const cx = toX(sel.lon), cy = toY(sel.lat);
          return (
            <g>
              <rect x={cx + 9} y={cy - 14} width={sel.nombre.length * 5.8 + 8} height={16}
                fill="oklch(14% 0.03 145)" rx={3} opacity={0.85}/>
              <text x={cx + 13} y={cy - 3} fill="#fff" fontSize={10} fontFamily="'IBM Plex Sans', sans-serif">
                {sel.nombre}
              </text>
            </g>
          );
        })()}
      </svg>

      {/* Floating tooltip */}
      {tooltip && (
        <div style={{
          position: 'fixed', left: tooltip.x + 14, top: tooltip.y - 10,
          background: 'oklch(18% 0.04 145)', border: '1px solid oklch(35% 0.07 145)',
          borderRadius: 8, padding: '8px 12px', pointerEvents: 'none', zIndex: 9999,
          minWidth: 160, boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}>
          <div style={{ fontWeight: 700, fontSize: 12, color: '#fff', marginBottom: 4 }}>
            {tooltip.d.nombre}
          </div>
          <div style={{ fontSize: 11, color: 'oklch(65% 0.04 145)', lineHeight: 1.8 }}>
            <span style={{ color: 'oklch(72% 0.16 145)' }}>Rendimiento: </span>
            <strong style={{ fontFamily: 'monospace', color: '#fff' }}>
              {tooltip.d.rendimiento?.toFixed(2)} ton/ha
            </strong><br/>
            <span style={{ color: 'oklch(65% 0.04 145)' }}>Región: </span>{tooltip.d.region}<br/>
            <span style={{ color: 'oklch(65% 0.04 145)' }}>Precip: </span>{tooltip.d.precipitacion} mm<br/>
            <span style={{ color: 'oklch(65% 0.04 145)' }}>Altitud: </span>{tooltip.d.altitud} msnm
          </div>
        </div>
      )}

      {/* Legend bar */}
      {colorMode !== 'lisa' && (
        <div style={{ display:'flex', alignItems:'center', gap:8, justifyContent:'center', marginTop:6 }}>
          <span style={{ color:'oklch(60% 0.04 145)', fontSize:11, fontFamily:'monospace' }}>
            {mn.toFixed(1)}
          </span>
          <div style={{ width:140, height:10, borderRadius:5,
            background:'linear-gradient(to right, oklch(88% 0.04 115), oklch(72% 0.18 135), oklch(38% 0.22 150))' }}/>
          <span style={{ color:'oklch(60% 0.04 145)', fontSize:11, fontFamily:'monospace' }}>
            {mx.toFixed(1)}
          </span>
          <span style={{ fontSize:10, color:'oklch(50% 0.04 145)' }}>ton/ha</span>
        </div>
      )}
      {colorMode === 'lisa' && (
        <div style={{ display:'flex', gap:10, justifyContent:'center', flexWrap:'wrap', marginTop:6 }}>
          {Object.entries(LISA_FILL).map(([k,v]) => (
            <div key={k} style={{ display:'flex', alignItems:'center', gap:4 }}>
              <div style={{ width:9, height:9, borderRadius:'50%', background:v }}></div>
              <span style={{ fontSize:10, color:'oklch(60% 0.04 145)' }}>{k}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── TIME SERIES ──────────────────────────────────────────────────────────────
function TimeSeriesChart({ data, years, regions, highlight, selectedId }) {
  const W = 480, H = 220, PAD = { t:20, r:20, b:36, l:48 };
  const iW = W - PAD.l - PAD.r, iH = H - PAD.t - PAD.b;

  // National trend
  const national = years.map(y => {
    const yd = data.filter(d => d.year === y);
    return { year: y, avg: yd.reduce((s,d)=>s+d.rendimiento,0)/yd.length };
  });

  // By region
  const byRegion = regions.map(r => ({
    region: r,
    series: years.map(y => {
      const yd = data.filter(d => d.year === y && d.region === r);
      return { year: y, avg: yd.length ? yd.reduce((s,d)=>s+d.rendimiento,0)/yd.length : null };
    })
  }));

  // Selected municipality series
  const selSeries = selectedId != null
    ? years.map(y => data.find(d => d.id === selectedId && d.year === y)).filter(Boolean)
    : null;

  const allVals = national.map(d => d.avg);
  byRegion.forEach(r => r.series.forEach(p => p.avg && allVals.push(p.avg)));
  const minV = Math.min(...allVals) * 0.9;
  const maxV = Math.max(...allVals) * 1.05;

  const tx = (y) => PAD.l + ((y - years[0]) / (years[years.length-1] - years[0])) * iW;
  const ty = (v) => PAD.t + iH - ((v - minV) / (maxV - minV)) * iH;

  const RCOLORS = { 'Andina':'#4ade80','Caribe':'#f59e0b','Pacífica':'#3b82f6','Orinoquía':'#a78bfa','Amazonía':'#34d399' };

  return (
    <svg width={W} height={H}>
      {/* Grid lines */}
      {[0,0.25,0.5,0.75,1].map(t => {
        const v = minV + t*(maxV-minV);
        const y = ty(v);
        return (
          <g key={t}>
            <line x1={PAD.l} y1={y} x2={W-PAD.r} y2={y}
              stroke="oklch(28% 0.03 145)" strokeWidth={1}/>
            <text x={PAD.l-6} y={y+4} textAnchor="end"
              fill="oklch(55% 0.04 145)" fontSize={9} fontFamily="monospace">
              {v.toFixed(1)}
            </text>
          </g>
        );
      })}

      {/* Area under national */}
      <path
        d={national.map((p,i) => `${i===0?'M':'L'}${tx(p.year)},${ty(p.avg)}`).join(' ')
           + ` L${tx(years[years.length-1])},${H-PAD.b} L${tx(years[0])},${H-PAD.b} Z`}
        fill="oklch(52% 0.18 148)" opacity={0.10}/>

      {/* Region lines */}
      {byRegion.map(r => {
        const pts = r.series.filter(p => p.avg != null);
        if (pts.length < 2) return null;
        const col = RCOLORS[r.region] ?? '#888';
        return (
          <polyline key={r.region}
            points={pts.map(p => `${tx(p.year)},${ty(p.avg)}`).join(' ')}
            fill="none" stroke={col} strokeWidth={1.5} opacity={0.65} strokeDasharray="4 2"/>
        );
      })}

      {/* National line */}
      <polyline
        points={national.map(p => `${tx(p.year)},${ty(p.avg)}`).join(' ')}
        fill="none" stroke="oklch(72% 0.16 145)" strokeWidth={2.5}/>
      {national.map((p,i) => (
        <circle key={i} cx={tx(p.year)} cy={ty(p.avg)} r={4}
          fill="oklch(72% 0.16 145)" stroke="oklch(14% 0.03 145)" strokeWidth={1.5}/>
      ))}

      {/* Selected municipality */}
      {selSeries && (
        <>
          <polyline
            points={selSeries.map(d => `${tx(d.year)},${ty(d.rendimiento)}`).join(' ')}
            fill="none" stroke="#fff" strokeWidth={2} strokeDasharray="6 2"/>
          {selSeries.map((d,i) => (
            <circle key={i} cx={tx(d.year)} cy={ty(d.rendimiento)} r={4}
              fill="#fff" stroke="oklch(14% 0.03 145)" strokeWidth={1.5}>
              <title>{d.nombre} {d.year}: {d.rendimiento} ton/ha</title>
            </circle>
          ))}
        </>
      )}

      {/* X axis */}
      <line x1={PAD.l} y1={H-PAD.b} x2={W-PAD.r} y2={H-PAD.b}
        stroke="oklch(33% 0.05 145)" strokeWidth={1}/>
      {years.map(y => (
        <text key={y} x={tx(y)} y={H-PAD.b+14} textAnchor="middle"
          fill="oklch(55% 0.04 145)" fontSize={10} fontFamily="monospace">{y}</text>
      ))}

      {/* Legend */}
      <line x1={PAD.l} y1={H-8} x2={PAD.l+18} y2={H-8} stroke="oklch(72% 0.16 145)" strokeWidth={2.5}/>
      <text x={PAD.l+22} y={H-4} fill="oklch(65% 0.04 145)" fontSize={9}>Nacional</text>
      {selSeries && (
        <>
          <line x1={PAD.l+75} y1={H-8} x2={PAD.l+93} y2={H-8} stroke="#fff" strokeWidth={2} strokeDasharray="5 2"/>
          <text x={PAD.l+97} y={H-4} fill="oklch(80% 0.04 145)" fontSize={9}>
            {data.find(d=>d.id===selectedId)?.nombre}
          </text>
        </>
      )}
    </svg>
  );
}

// ─── HEATMAP ──────────────────────────────────────────────────────────────────
function HeatmapChart({ data, years, selectedId, onSelect }) {
  // Show top 20 municipalities by average rendimiento
  const muns = [...new Set(data.map(d => d.id))];
  const avgByMun = muns.map(id => ({
    id,
    nombre: data.find(d => d.id === id)?.nombre,
    avg: data.filter(d => d.id === id).reduce((s,d) => s+d.rendimiento,0) /
         data.filter(d => d.id === id).length
  })).sort((a,b) => b.avg - a.avg).slice(0,22);

  const allVals = avgByMun.flatMap(m =>
    years.map(y => data.find(d => d.id === m.id && d.year === y)?.rendimiento ?? 0)
  );
  const mn = Math.min(...allVals), mx = Math.max(...allVals);
  const norm = v => (v - mn) / (mx - mn + 0.001);

  const cellW = 44, cellH = 22, labelW = 130;
  const W = labelW + years.length * cellW + 20;
  const H = avgByMun.length * cellH + 40;

  return (
    <svg width={W} height={H} style={{ display:'block' }}>
      {/* Year headers */}
      {years.map((y,j) => (
        <text key={y} x={labelW + j*cellW + cellW/2} y={16}
          textAnchor="middle" fill="oklch(60% 0.04 145)" fontSize={10} fontFamily="monospace">{y}</text>
      ))}

      {avgByMun.map((m, i) => {
        const isSelected = m.id === selectedId;
        return (
          <g key={m.id} style={{ cursor:'pointer' }}
            onClick={() => onSelect && onSelect(m.id === selectedId ? null : m.id)}>
            {/* Label */}
            <text x={labelW - 6} y={24 + i*cellH + cellH*0.65}
              textAnchor="end" fill={isSelected ? '#fff' : 'oklch(65% 0.04 145)'}
              fontSize={10} fontFamily="'IBM Plex Sans',sans-serif"
              fontWeight={isSelected ? 700 : 400}>
              {m.nombre?.length > 16 ? m.nombre.slice(0,15)+'…' : m.nombre}
            </text>
            {/* Cells */}
            {years.map((y, j) => {
              const d = data.find(dd => dd.id === m.id && dd.year === y);
              const v = d?.rendimiento ?? 0;
              const t = norm(v);
              const fill = getChoroColor(t);
              return (
                <g key={y}>
                  <rect
                    x={labelW + j*cellW + 2}
                    y={24 + i*cellH + 2}
                    width={cellW - 4}
                    height={cellH - 4}
                    fill={fill}
                    rx={2}
                    stroke={isSelected ? '#fff' : 'none'}
                    strokeWidth={isSelected ? 1 : 0}
                  >
                    <title>{m.nombre} {y}: {v.toFixed(2)} ton/ha</title>
                  </rect>
                  <text
                    x={labelW + j*cellW + cellW/2}
                    y={24 + i*cellH + cellH*0.68}
                    textAnchor="middle"
                    fill={t > 0.5 ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.7)'}
                    fontSize={8.5}
                    fontFamily="monospace"
                  >
                    {v.toFixed(1)}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

// ─── RANKING ──────────────────────────────────────────────────────────────────
function RankingChart({ data, year, n=8, mode='top' }) {
  const yd = data.filter(d => d.year === year);
  const sorted = [...yd].sort((a,b) =>
    mode === 'top' ? b.rendimiento - a.rendimiento : a.rendimiento - b.rendimiento
  ).slice(0, n);
  const maxVal = sorted[0]?.rendimiento ?? 1;
  const W = 340, ROW = 30;
  const H = sorted.length * ROW + 20;

  return (
    <svg width={W} height={H}>
      {sorted.map((d, i) => {
        const barW = (d.rendimiento / maxVal) * (W - 165);
        const col = mode === 'top' ? getChoroColor(1 - i/n) : getChoroColor(i/n * 0.3);
        return (
          <g key={d.id}>
            <text x={8} y={14 + i*ROW + ROW*0.5}
              fill="oklch(65% 0.04 145)" fontSize={10} fontFamily="'IBM Plex Sans',sans-serif">
              {i+1}. {d.nombre.length > 16 ? d.nombre.slice(0,15)+'…' : d.nombre}
            </text>
            <rect x={155} y={6 + i*ROW} width={barW} height={ROW-8} fill={col} rx={3} opacity={0.9}/>
            <text x={159+barW} y={14 + i*ROW + ROW*0.5}
              fill="oklch(65% 0.04 145)" fontSize={9} fontFamily="monospace">
              {d.rendimiento.toFixed(2)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── HORIZONTAL BAR (SHAP) ───────────────────────────────────────────────────
function ShapBar({ features, values, color='oklch(52% 0.18 148)' }) {
  const W = 340, H = features.length * 32 + 20;
  const max = Math.max(...values);
  return (
    <svg width={W} height={H}>
      {features.map((f, i) => {
        const barW = (values[i] / max) * (W - 132);
        return (
          <g key={i}>
            <text x={118} y={i*32+22} textAnchor="end"
              fill="oklch(78% 0.04 145)" fontSize={12} fontFamily="'IBM Plex Sans',sans-serif">{f}</text>
            <rect x={122} y={i*32+9} width={barW} height={18} fill={color} rx={3} opacity={0.85}/>
            <text x={126+barW} y={i*32+22} fill="oklch(55% 0.04 145)" fontSize={10} fontFamily="monospace">
              {(values[i]*100).toFixed(0)}%
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── SCATTER ─────────────────────────────────────────────────────────────────
function ScatterChart({ data }) {
  const W = 300, H = 240, PAD = { t:16, r:16, b:32, l:40 };
  const iW = W-PAD.l-PAD.r, iH = H-PAD.t-PAD.b;
  const allV = data.flatMap(d => [d.obs, d.pred]);
  const maxV = Math.max(...allV) + 0.4;
  const tx = v => PAD.l + (v/maxV)*iW;
  const ty = v => PAD.t + iH - (v/maxV)*iH;
  return (
    <svg width={W} height={H}>
      <line x1={tx(0)} y1={ty(0)} x2={tx(maxV)} y2={ty(maxV)}
        stroke="oklch(68% 0.16 72)" strokeWidth={1.2} strokeDasharray="5 3" opacity={0.6}/>
      {data.filter((_,i)=>i%3===0).map((d,i) => (
        <circle key={i} cx={tx(d.obs)} cy={ty(d.pred)} r={3.5}
          fill="oklch(52% 0.18 148)" opacity={0.55}/>
      ))}
      <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={H-PAD.b} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
      <line x1={PAD.l} y1={H-PAD.b} x2={W-PAD.r} y2={H-PAD.b} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
      <text x={W/2} y={H-6} textAnchor="middle" fill="oklch(55% 0.04 145)" fontSize={10}>Observado (ton/ha)</text>
      <text x={12} y={H/2} textAnchor="middle" fill="oklch(55% 0.04 145)" fontSize={10}
        transform={`rotate(-90,12,${H/2})`}>Predicho</text>
    </svg>
  );
}

// ─── VARIOGRAM ───────────────────────────────────────────────────────────────
function VariogramChart({ data }) {
  const W = 380, H = 210, PAD = { t:20, r:20, b:36, l:46 };
  const iW = W-PAD.l-PAD.r, iH = H-PAD.t-PAD.b;
  const maxH = 160, maxG = 0.38;
  const tx = h => PAD.l + (h/maxH)*iW;
  const ty = g => PAD.t + iH - (g/maxG)*iH;
  return (
    <svg width={W} height={H}>
      <line x1={PAD.l} y1={ty(0.30)} x2={W-PAD.r} y2={ty(0.30)}
        stroke="oklch(68% 0.16 72)" strokeWidth={1} strokeDasharray="5 3" opacity={0.5}/>
      <text x={PAD.l+4} y={ty(0.30)-4} fill="oklch(68% 0.16 72)" fontSize={9} opacity={0.8}>Sill ≈ 0.30</text>
      <line x1={tx(58)} y1={PAD.t} x2={tx(58)} y2={H-PAD.b}
        stroke="oklch(68% 0.16 72)" strokeWidth={1} strokeDasharray="5 3" opacity={0.5}/>
      <text x={tx(58)+3} y={PAD.t+12} fill="oklch(68% 0.16 72)" fontSize={9} opacity={0.8}>Range≈58km</text>
      <polyline
        points={data.map(d => `${tx(d.h)},${ty(d.theoretical)}`).join(' ')}
        fill="none" stroke="oklch(72% 0.16 145)" strokeWidth={2}/>
      {data.map((d,i) => (
        <circle key={i} cx={tx(d.h)} cy={ty(d.gamma)} r={4}
          fill="oklch(52% 0.18 148)" stroke="oklch(14% 0.03 145)" strokeWidth={1.5}>
          <title>h={d.h}km γ={d.gamma}</title>
        </circle>
      ))}
      <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={H-PAD.b} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
      <line x1={PAD.l} y1={H-PAD.b} x2={W-PAD.r} y2={H-PAD.b} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
      <text x={W/2} y={H-6} textAnchor="middle" fill="oklch(55% 0.04 145)" fontSize={10}>Distancia (km)</text>
      <text x={12} y={H/2} textAnchor="middle" fill="oklch(55% 0.04 145)" fontSize={10}
        transform={`rotate(-90,12,${H/2})`}>γ(h)</text>
      {[50,100,150].map(v => (
        <text key={v} x={tx(v)} y={H-PAD.b+14} textAnchor="middle"
          fill="oklch(55% 0.04 145)" fontSize={9} fontFamily="monospace">{v}</text>
      ))}
      <circle cx={W-120} cy={16} r={4} fill="oklch(52% 0.18 148)"/>
      <text x={W-113} y={20} fill="oklch(55% 0.04 145)" fontSize={9}>Empírico</text>
      <line x1={W-60} y1={16} x2={W-46} y2={16} stroke="oklch(72% 0.16 145)" strokeWidth={2}/>
      <text x={W-42} y={20} fill="oklch(55% 0.04 145)" fontSize={9}>Teórico</text>
    </svg>
  );
}

// ─── PDP ─────────────────────────────────────────────────────────────────────
function PDPChart({ feature }) {
  const W = 300, H = 160, PAD = { t:10, r:10, b:28, l:36 };
  const iW = W-PAD.l-PAD.r, iH = H-PAD.t-PAD.b;
  const pts = Array.from({length:20}, (_,i) => {
    const x = i/19;
    let y;
    if (feature === 'Precipitación') y = 0.6 + 1.4*(1-Math.exp(-x*3)) + Math.sin(x*6)*0.1;
    else if (feature === 'Temperatura') y = 2.5 - Math.pow((x-0.4)*2,2)*0.9;
    else y = 2.0 - x*0.9 + Math.sin(x*4)*0.15;
    return { x, y: Math.max(0.4, y) };
  });
  const maxY = Math.max(...pts.map(p=>p.y)), minY = Math.min(...pts.map(p=>p.y));
  const tx = x => PAD.l + x*iW;
  const ty = y => PAD.t + iH - ((y-minY)/(maxY-minY+0.01))*iH;
  const path = pts.map((p,i) => `${i===0?'M':'L'}${tx(p.x)},${ty(p.y)}`).join(' ');
  return (
    <svg width={W} height={H}>
      <path d={path+` L${tx(1)},${H-PAD.b} L${tx(0)},${H-PAD.b} Z`}
        fill="oklch(68% 0.16 72)" opacity={0.12}/>
      <path d={path} fill="none" stroke="oklch(68% 0.16 72)" strokeWidth={2.5}/>
      <line x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={H-PAD.b} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
      <line x1={PAD.l} y1={H-PAD.b} x2={W-PAD.r} y2={H-PAD.b} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
      <text x={W/2} y={H-6} textAnchor="middle" fill="oklch(55% 0.04 145)" fontSize={10}>{feature}</text>
    </svg>
  );
}

// Export all
Object.assign(window, {
  getChoroColor,
  ColombiaMap, TimeSeriesChart, HeatmapChart, RankingChart,
  ShapBar, ScatterChart, VariogramChart, PDPChart,
});
