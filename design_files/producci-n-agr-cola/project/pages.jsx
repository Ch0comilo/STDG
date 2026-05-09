// pages.jsx — all page sections

// ─── SHARED UI ───────────────────────────────────────────────────────────────
const Card = ({ children, style={} }) => (
  <div style={{ background:'oklch(18% 0.03 145)', border:'1px solid oklch(28% 0.04 145)',
    borderRadius:10, padding:16, ...style }}>
    {children}
  </div>
);

const SectionTitle = ({ children, sub }) => (
  <div style={{ marginBottom:20 }}>
    <h2 style={{ fontSize:18, fontWeight:600, color:'oklch(92% 0.02 145)' }}>{children}</h2>
    {sub && <p style={{ fontSize:12, color:'oklch(58% 0.04 145)', marginTop:4 }}>{sub}</p>}
  </div>
);

const Metric = ({ label, value, unit='', color='oklch(52% 0.18 148)' }) => (
  <div style={{ background:'oklch(22% 0.03 145)', borderRadius:8, padding:'12px 16px',
    border:'1px solid oklch(28% 0.04 145)' }}>
    <div style={{ fontSize:11, color:'oklch(55% 0.04 145)', marginBottom:4 }}>{label}</div>
    <div style={{ fontSize:22, fontWeight:600, fontFamily:'monospace', color }}>
      {value}<span style={{ fontSize:12, marginLeft:3, color:'oklch(50% 0.04 145)' }}>{unit}</span>
    </div>
  </div>
);

const Tag = ({ children, color='oklch(52% 0.18 148)' }) => (
  <span style={{ background:`${color}22`, color, border:`1px solid ${color}55`,
    borderRadius:4, padding:'2px 8px', fontSize:11, fontFamily:'monospace' }}>
    {children}
  </span>
);

const CardTitle = ({ children }) => (
  <div style={{ fontSize:11, fontWeight:600, letterSpacing:'0.06em',
    color:'oklch(55% 0.04 145)', marginBottom:12, textTransform:'uppercase' }}>
    {children}
  </div>
);

const Alert = ({ color='oklch(52% 0.18 148)', accent, children }) => (
  <div style={{ background:'oklch(18% 0.03 145)', border:`1px solid ${color}44`,
    borderRadius:10, padding:'12px 16px', display:'flex', gap:12, alignItems:'flex-start' }}>
    <div style={{ width:4, minHeight:36, borderRadius:3, background:color, flexShrink:0, marginTop:2 }}></div>
    <div style={{ fontSize:12, color:'oklch(65% 0.04 145)', lineHeight:1.7 }}>{children}</div>
  </div>
);

// ─── MUNICIPALITY DETAIL PANEL ───────────────────────────────────────────────
function MunDetailPanel({ selectedId, data, years, onClose }) {
  if (selectedId == null) return null;
  const series = years.map(y => data.find(d => d.id === selectedId && d.year === y)).filter(Boolean);
  if (!series.length) return null;
  const last = series[series.length - 1];
  const first = series[0];
  const trend = ((last.rendimiento - first.rendimiento) / first.rendimiento * 100).toFixed(1);
  const trendPos = +trend > 0;

  return (
    <div style={{
      background:'oklch(18% 0.03 145)', border:'1px solid oklch(35% 0.08 145)',
      borderRadius:12, padding:16, minWidth:200,
    }}>
      <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', marginBottom:12 }}>
        <div>
          <div style={{ fontWeight:700, fontSize:13, color:'oklch(92% 0.02 145)' }}>{last.nombre}</div>
          <div style={{ fontSize:11, color:'oklch(55% 0.04 145)', marginTop:2 }}>{last.region}</div>
        </div>
        <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer',
          color:'oklch(55% 0.04 145)', fontSize:16, padding:'0 4px', lineHeight:1 }}>×</button>
      </div>
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginBottom:12 }}>
        <div style={{ background:'oklch(22% 0.03 145)', borderRadius:6, padding:'8px 10px' }}>
          <div style={{ fontSize:10, color:'oklch(55% 0.04 145)' }}>Rendimiento {last.year}</div>
          <div style={{ fontFamily:'monospace', fontSize:16, fontWeight:700,
            color:'oklch(72% 0.16 145)' }}>{last.rendimiento.toFixed(2)}</div>
          <div style={{ fontSize:9, color:'oklch(50% 0.04 145)' }}>ton/ha</div>
        </div>
        <div style={{ background:'oklch(22% 0.03 145)', borderRadius:6, padding:'8px 10px' }}>
          <div style={{ fontSize:10, color:'oklch(55% 0.04 145)' }}>Tendencia 6a</div>
          <div style={{ fontFamily:'monospace', fontSize:16, fontWeight:700,
            color: trendPos ? '#4ade80' : '#f87171' }}>
            {trendPos ? '+' : ''}{trend}%
          </div>
          <div style={{ fontSize:9, color:'oklch(50% 0.04 145)' }}>vs 2018</div>
        </div>
      </div>
      <div style={{ fontSize:10, color:'oklch(50% 0.04 145)', marginBottom:6 }}>
        Evolución temporal
      </div>
      <svg width="100%" height={70} viewBox="0 0 200 70">
        {series.map((d, i) => {
          const maxR = Math.max(...series.map(s=>s.rendimiento));
          const minR = Math.min(...series.map(s=>s.rendimiento));
          const x = 10 + (i/(series.length-1))*180;
          const y = 60 - ((d.rendimiento-minR)/(maxR-minR+0.01))*50;
          return (
            <g key={d.year}>
              {i > 0 && (() => {
                const prev = series[i-1];
                const px = 10 + ((i-1)/(series.length-1))*180;
                const py = 60 - ((prev.rendimiento-minR)/(maxR-minR+0.01))*50;
                return <line x1={px} y1={py} x2={x} y2={y}
                  stroke="oklch(72% 0.16 145)" strokeWidth={1.5}/>;
              })()}
              <circle cx={x} cy={y} r={3} fill="oklch(72% 0.16 145)"
                stroke="oklch(14% 0.03 145)" strokeWidth={1}/>
              <text x={x} y={68} textAnchor="middle"
                fill="oklch(50% 0.04 145)" fontSize={7} fontFamily="monospace">
                {String(d.year).slice(2)}
              </text>
            </g>
          );
        })}
      </svg>
      <div style={{ marginTop:10, fontSize:10, color:'oklch(55% 0.04 145)', lineHeight:1.8 }}>
        <div>Precip: <strong style={{color:'oklch(72% 0.16 145)'}}>{last.precipitacion} mm</strong></div>
        <div>Temp: <strong style={{color:'oklch(68% 0.16 72)'}}>{last.temperatura}°C</strong></div>
        <div>Altitud: <strong style={{color:'oklch(65% 0.04 145)'}}>{last.altitud} msnm</strong></div>
        <div>NBI: <strong style={{color:'oklch(65% 0.04 145)'}}>{last.nbi.toFixed(1)}%</strong></div>
      </div>
    </div>
  );
}

// ─── PAGE EDA ────────────────────────────────────────────────────────────────
function PageEDA({ year, region, selectedId, setSelectedId }) {
  const filtered = React.useMemo(() =>
    ALL_DATA.filter(d => d.year === year && (region === 'Todas' || d.region === region)),
    [year, region]
  );
  const avg = (filtered.reduce((s,d)=>s+d.rendimiento,0)/filtered.length).toFixed(2);
  const totalProd = (filtered.reduce((s,d)=>s+d.produccion,0)/1000).toFixed(0);
  const top = [...filtered].sort((a,b)=>b.rendimiento-a.rendimiento)[0];
  const byRegion = REGIONES.map(r => ({
    r,
    avg: +(ALL_DATA.filter(d=>d.year===year&&d.region===r)
      .reduce((s,d)=>s+d.rendimiento,0) /
      Math.max(1,ALL_DATA.filter(d=>d.year===year&&d.region===r).length)).toFixed(2)
  }));
  const maxByR = Math.max(...byRegion.map(r=>r.avg));

  return (
    <div>
      <SectionTitle sub="Exploración geoespacial del rendimiento municipal de maíz · Selecciona un municipio en el mapa">
        EDA Espacial
      </SectionTitle>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:18 }}>
        <Metric label="Rendimiento promedio" value={avg} unit="ton/ha"/>
        <Metric label="Producción total" value={totalProd} unit="×10³ ton" color="oklch(68% 0.16 72)"/>
        <Metric label="Municipio top" value={top?.rendimiento.toFixed(2)} unit="ton/ha" color="oklch(72% 0.16 145)"/>
        <Metric label="Municipios" value={filtered.length} unit="muns" color="oklch(55% 0.04 145)"/>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16 }}>
        {/* Map */}
        <Card>
          <CardTitle>Mapa Coroplético — Rendimiento (ton/ha) · {year}</CardTitle>
          <ColombiaMap data={ALL_DATA} colorKey="rendimiento" year={year}
            selectedId={selectedId} onSelect={setSelectedId}/>
        </Card>

        {/* Right column */}
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {/* Detail panel when selected */}
          {selectedId != null && (
            <MunDetailPanel selectedId={selectedId} data={ALL_DATA} years={YEARS}
              onClose={() => setSelectedId(null)}/>
          )}

          {/* Region bars */}
          <Card style={{ flex:1 }}>
            <CardTitle>Rendimiento promedio por región · {year}</CardTitle>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {byRegion.sort((a,b)=>b.avg-a.avg).map(({r, avg: a}) => (
                <div key={r}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                    <span style={{ fontSize:11, color:'oklch(72% 0.04 145)' }}>{r}</span>
                    <span style={{ fontSize:11, fontFamily:'monospace', color: REGION_COLORS[r] }}>{a.toFixed(2)}</span>
                  </div>
                  <div style={{ height:8, background:'oklch(22% 0.03 145)', borderRadius:4 }}>
                    <div style={{ height:'100%', width:`${(a/maxByR)*100}%`,
                      background: REGION_COLORS[r], borderRadius:4, opacity:0.85 }}></div>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Scatter precip vs rendimiento */}
          <Card>
            <CardTitle>Precipitación vs Rendimiento</CardTitle>
            <svg width="100%" height={120} viewBox="0 0 300 120">
              {filtered.filter((_,i)=>i%2===0).map((d,i) => {
                const maxP=2200, maxR=6;
                const cx = 30+(d.precipitacion/maxP)*255;
                const cy = 110-(d.rendimiento/maxR)*95;
                const isSelected = d.id === selectedId;
                return (
                  <circle key={i} cx={cx} cy={cy} r={isSelected ? 5 : 3}
                    fill={isSelected ? '#fff' : REGION_COLORS[d.region] ?? 'oklch(52% 0.18 148)'}
                    opacity={isSelected ? 1 : 0.55}/>
                );
              })}
              <line x1={28} y1={10} x2={28} y2={112} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
              <line x1={28} y1={112} x2={285} y2={112} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
              <text x={158} y={120} textAnchor="middle" fill="oklch(50% 0.04 145)" fontSize={9}>Precipitación (mm)</text>
              <text x={10} y={60} textAnchor="middle" fill="oklch(50% 0.04 145)" fontSize={9}
                transform="rotate(-90,10,60)">ton/ha</text>
              <text x={290} y={20} fill="oklch(60% 0.12 145)" fontSize={9} textAnchor="end">r = +0.62</text>
            </svg>
          </Card>
        </div>
      </div>

      {/* Historical trends */}
      <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:16 }}>
        <Card>
          <CardTitle>Serie Histórica — Rendimiento nacional y por región (2018–2023)</CardTitle>
          <TimeSeriesChart data={ALL_DATA} years={YEARS} regions={REGIONES} selectedId={selectedId}/>
          <div style={{ display:'flex', gap:12, flexWrap:'wrap', marginTop:8 }}>
            {REGIONES.map(r => (
              <div key={r} style={{ display:'flex', alignItems:'center', gap:4 }}>
                <div style={{ width:16, height:2, background:REGION_COLORS[r], borderRadius:1 }}></div>
                <span style={{ fontSize:9, color:'oklch(55% 0.04 145)' }}>{r}</span>
              </div>
            ))}
            <div style={{ display:'flex', alignItems:'center', gap:4 }}>
              <div style={{ width:18, height:2.5, background:'oklch(72% 0.16 145)', borderRadius:1 }}></div>
              <span style={{ fontSize:9, color:'oklch(72% 0.16 145)' }}>Nacional</span>
            </div>
          </div>
        </Card>
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          <Card>
            <CardTitle>Top 8 · {year}</CardTitle>
            <RankingChart data={ALL_DATA} year={year} n={8} mode="top"/>
          </Card>
        </div>
      </div>

      {/* Heatmap */}
      <Card style={{ marginTop:16 }}>
        <CardTitle>Heatmap — Rendimiento por municipio y año (Top 22)</CardTitle>
        <div style={{ overflowX:'auto' }}>
          <HeatmapChart data={ALL_DATA} years={YEARS} selectedId={selectedId} onSelect={setSelectedId}/>
        </div>
        <div style={{ fontSize:11, color:'oklch(50% 0.04 145)', marginTop:8 }}>
          Haz clic en una fila para seleccionar ese municipio en todos los gráficos
        </div>
      </Card>
    </div>
  );
}

// ─── PAGE MORAN ──────────────────────────────────────────────────────────────
function PageMoran({ year, selectedId, setSelectedId }) {
  const raw = React.useMemo(() => ALL_DATA.filter(d => d.year === year), [year]);
  const mData = React.useMemo(() => addMoranAttrs(raw), [raw]);
  const moranI = +(0.42 - (year - 2018) * 0.012).toFixed(3);
  const counts = { HH:0, LL:0, HL:0, LH:0, NS:0 };
  mData.forEach(d => counts[d.lisa]++);

  // Lisa colors indexed by id
  const lisaByIdx = mData;

  return (
    <div>
      <SectionTitle sub="Índice de Moran global e indicadores locales de asociación espacial (LISA)">
        Autocorrelación Espacial
      </SectionTitle>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:18 }}>
        <Metric label="Moran I global" value={moranI} color="oklch(52% 0.18 148)"/>
        <Metric label="p-valor" value="< 0.001" color="oklch(68% 0.16 72)"/>
        <Metric label="Clusters HH" value={counts.HH} unit="muns" color="#4ade80"/>
        <Metric label="Clusters LL" value={counts.LL} unit="muns" color="#f87171"/>
      </div>

      <Alert color="oklch(52% 0.18 148)">
        <strong style={{color:'oklch(72% 0.16 145)'}}>Autocorrelación positiva significativa</strong>
        {' '}(I = {moranI}, p &lt; 0.001): municipios con alto rendimiento tienden a estar
        rodeados de municipios similares. La estructura espacial explica parte importante de la varianza.
      </Alert>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>
        <Card>
          <CardTitle>Mapa LISA — Clusters Espaciales · {year}</CardTitle>
          <ColombiaMap data={mData} colorKey="rendimiento" year={year}
            colorMode="lisa" lisaColors={mData}
            selectedId={selectedId} onSelect={setSelectedId}/>
        </Card>
        <Card>
          <CardTitle>Diagrama de Moran — Rendimiento vs Lag Espacial</CardTitle>
          <svg width="340" height="280">
            <line x1={40} y1={250} x2={320} y2={50}
              stroke="oklch(68% 0.16 72)" strokeWidth={1.5} strokeDasharray="5 3" opacity={0.7}/>
            {/* Quadrant lines */}
            <line x1={180} y1={20} x2={180} y2={270} stroke="oklch(28% 0.04 145)" strokeWidth={0.8}/>
            <line x1={40} y1={145} x2={320} y2={145} stroke="oklch(28% 0.04 145)" strokeWidth={0.8}/>
            <text x={230} y={38} fill="#4ade80" fontSize={9} opacity={0.7}>I (HH)</text>
            <text x={60} y={270} fill="#ef4444" fontSize={9} opacity={0.7}>III (LL)</text>
            <text x={60} y={38} fill="#f59e0b" fontSize={9} opacity={0.7}>II (LH)</text>
            <text x={230} y={270} fill="#3b82f6" fontSize={9} opacity={0.7}>IV (HL)</text>
            {mData.filter((_,i)=>i%2===0).map((d, i) => {
              const COLS = { HH:'#4ade80', LL:'#ef4444', HL:'#3b82f6', LH:'#f59e0b', NS:'#475569' };
              const mx=6, my=5;
              return (
                <circle key={i}
                  cx={40 + (d.rendimiento/mx)*280}
                  cy={270 - (d.lag/my)*250}
                  r={d.id===selectedId ? 6 : 3.5}
                  fill={COLS[d.lisa]} opacity={0.75}/>
              );
            })}
            <line x1={38} y1={18} x2={38} y2={270} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
            <line x1={38} y1={268} x2={322} y2={268} stroke="oklch(30% 0.04 145)" strokeWidth={1}/>
            <text x={180} y={285} textAnchor="middle" fill="oklch(50% 0.04 145)" fontSize={10}>
              Rendimiento estandarizado
            </text>
            <text x={14} y={145} textAnchor="middle" fill="oklch(50% 0.04 145)" fontSize={10}
              transform="rotate(-90,14,145)">Lag espacial</text>
          </svg>
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:6, marginTop:8, fontSize:11 }}>
            {[['HH','#4ade80','Alto-Alto'],['LL','#ef4444','Bajo-Bajo'],
              ['HL','#3b82f6','Alto-Bajo'],['LH','#f59e0b','Bajo-Alto']].map(([k,c,l]) => (
              <div key={k} style={{ display:'flex', alignItems:'center', gap:6 }}>
                <div style={{ width:8, height:8, borderRadius:'50%', background:c }}></div>
                <span style={{ color:'oklch(60% 0.04 145)' }}>{k}: {l} ({counts[k]})</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'2fr 1fr', gap:16, marginTop:16 }}>
        <Card>
          <CardTitle>Tendencia del Índice de Moran I por año</CardTitle>
          <svg width="420" height="160">
            {YEARS.map((y, i) => {
              const mi = +(0.42 - (y - 2018) * 0.012).toFixed(3);
              const x = 45 + (i/(YEARS.length-1))*355;
              const h = (mi/0.5)*110;
              return (
                <g key={y}>
                  <rect x={x-18} y={140-h} width={36} height={h}
                    fill={y===year ? 'oklch(52% 0.18 148)' : 'oklch(35% 0.10 148)'}
                    rx={3} opacity={0.85}/>
                  <text x={x} y={152} textAnchor="middle"
                    fill="oklch(55% 0.04 145)" fontSize={9} fontFamily="monospace">{y}</text>
                  <text x={x} y={140-h-4} textAnchor="middle"
                    fill="oklch(65% 0.04 145)" fontSize={9} fontFamily="monospace">{mi}</text>
                </g>
              );
            })}
            <line x1={28} y1={10} x2={28} y2={142} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
            <line x1={28} y1={142} x2={400} y2={142} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
          </svg>
        </Card>
        <Card>
          <CardTitle>Distribución de clusters LISA</CardTitle>
          <div style={{ display:'flex', flexDirection:'column', gap:8, marginTop:4 }}>
            {[['HH','#4ade80'],['LL','#ef4444'],['HL','#3b82f6'],['LH','#f59e0b'],['NS','#475569']].map(([k,c]) => (
              <div key={k}>
                <div style={{ display:'flex', justifyContent:'space-between', marginBottom:3 }}>
                  <span style={{ fontSize:11, color:c }}>{k}</span>
                  <span style={{ fontSize:11, fontFamily:'monospace', color:'oklch(60% 0.04 145)' }}>
                    {counts[k]} ({(counts[k]/N_MUNS*100).toFixed(0)}%)
                  </span>
                </div>
                <div style={{ height:8, background:'oklch(22% 0.03 145)', borderRadius:4 }}>
                  <div style={{ height:'100%', width:`${(counts[k]/N_MUNS)*100}%`,
                    background:c, borderRadius:4, opacity:0.85 }}></div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ─── PAGE ML ──────────────────────────────────────────────────────────────────
function PageML({ year, model, setModel, nTrees, setNTrees, maxDepth, setMaxDepth, alpha, setAlpha }) {
  const raw = React.useMemo(() => ALL_DATA.filter(d => d.year === year), [year]);
  const MODELS_DATA = React.useMemo(() => simulateModels(raw), [raw]);
  const md = MODELS_DATA[model];
  const shapV = model==='Random Forest'?SHAP_RF:model==='XGBoost'?SHAP_XGB:SHAP_LASSO;

  return (
    <div>
      <SectionTitle sub="Modelos de Machine Learning para predicción del rendimiento agrícola municipal">
        Modelos ML
      </SectionTitle>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:18 }}>
        <Metric label="RMSE (CV aleatoria)" value={md.rmse.toFixed(3)} unit="ton/ha" color="oklch(68% 0.16 72)"/>
        <Metric label="MAE" value={md.mae.toFixed(3)} unit="ton/ha" color="oklch(68% 0.16 72)"/>
        <Metric label="R²" value={md.r2.toFixed(3)} color="oklch(52% 0.18 148)"/>
        <Metric label="Moran I residuos" value={md.moran_residuos.toFixed(3)}
          color={md.moran_residuos > 0.1 ? '#f87171' : '#4ade80'}/>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        <Card>
          <CardTitle>Importancia de variables (SHAP) — {model}</CardTitle>
          <ShapBar features={FEATURES} values={shapV}/>
        </Card>
        <Card>
          <CardTitle>Observado vs Predicho — {model}</CardTitle>
          <ScatterChart data={md.predictions}/>
          <div style={{ fontSize:11, color:'oklch(50% 0.04 145)', marginTop:6 }}>
            Línea punteada = predicción perfecta · RMSE = {md.rmse.toFixed(3)} ton/ha
          </div>
        </Card>
      </div>

      <Card style={{ marginTop:16 }}>
        <CardTitle>Dependencia Parcial (PDP) — Efecto marginal por variable</CardTitle>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12 }}>
          {['Precipitación','Temperatura','Altitud'].map(f => (
            <div key={f}>
              <div style={{ fontSize:11, color:'oklch(60% 0.04 145)', marginBottom:6 }}>{f}</div>
              <PDPChart feature={f}/>
            </div>
          ))}
        </div>
      </Card>

      {/* Residual map */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>
        <Card>
          <CardTitle>Mapa de Residuos Espaciales — {model}</CardTitle>
          {(() => {
            const residData = raw.map((d, i) => {
              const resid = (md.predictions[i]?.pred ?? d.rendimiento) - d.rendimiento;
              return { ...d, residual: +resid.toFixed(3) };
            });
            const mn = Math.min(...residData.map(d=>d.residual));
            const mx = Math.max(...residData.map(d=>d.residual));
            const norm = v => (v - mn) / (mx - mn + 0.001);
            const W=380, H=310;
            const toX = lon => ((lon-(-79.5))/(13.5))*(W-40)+20;
            const toY = lat => H-((lat-(-5))/19)*(H-40)-20;
            return (
              <div>
                <svg width={W} height={H} style={{display:'block',margin:'0 auto'}}>
                  <polygon
                    points="82,22 130,10 190,8 240,14 285,30 318,60 338,95 348,138 340,178 322,210 298,248 265,278 228,304 188,318 148,316 108,298 70,268 40,228 22,185 18,140 28,98 50,62 82,22"
                    fill="oklch(20% 0.035 145)" stroke="oklch(33% 0.07 145)" strokeWidth="1.5"/>
                  {residData.map((d,i)=>{
                    const cx=toX(d.lon), cy=toY(d.lat);
                    if(cx<12||cx>W-12||cy<12||cy>H-12) return null;
                    const t = norm(d.residual);
                    const fill = t > 0.55
                      ? `oklch(${55+t*15}% ${0.15+t*0.10} 148)`
                      : t < 0.45
                        ? `oklch(${55+(1-t)*10}% ${0.15+(1-t)*0.10} 25)`
                        : 'oklch(38% 0.04 145)';
                    return <circle key={i} cx={cx} cy={cy} r={5} fill={fill} opacity={0.88}>
                      <title>{d.nombre}: residuo {d.residual>0?'+':''}{d.residual.toFixed(3)} ton/ha</title>
                    </circle>;
                  })}
                </svg>
                <div style={{display:'flex',alignItems:'center',gap:8,justifyContent:'center',marginTop:6}}>
                  <span style={{fontSize:10,color:'#f87171'}}>Subestimado</span>
                  <div style={{width:120,height:8,borderRadius:4,
                    background:'linear-gradient(to right,oklch(62% 0.22 25),oklch(28% 0.04 145),oklch(62% 0.22 148))'}}/>
                  <span style={{fontSize:10,color:'#4ade80'}}>Sobreestimado</span>
                </div>
              </div>
            );
          })()}
        </Card>
        <Card>
          <CardTitle>Predicción Municipal — {model} · {year}</CardTitle>
          {(() => {
            const predData = raw.map((d,i) => ({
              ...d, rendimiento: Math.max(0.3, md.predictions[i]?.pred ?? d.rendimiento)
            }));
            return (
              <ColombiaMap data={predData.map(d=>({...d,year}))} colorKey="rendimiento"
                year={year} selectedId={null} onSelect={()=>{}}/>
            );
          })()}
        </Card>
      </div>

      {md.moran_residuos > 0.1 && (
        <Alert color="#f87171" style={{ marginTop:16 }}>
          <strong style={{color:'#fca5a5'}}>Autocorrelación residual detectada</strong>
          {` (I = ${md.moran_residuos.toFixed(3)}): `}
          el modelo {model} no captura completamente la estructura espacial.
          Se recomienda Kriging de residuos para corregir esta dependencia espacial remanente.
        </Alert>
      )}
    </div>
  );
}

// ─── PAGE KRIGING ─────────────────────────────────────────────────────────────
function PageKriging({ year, selectedId, setSelectedId }) {
  const vData = React.useMemo(() => variogramData(), []);
  const raw = React.useMemo(() => ALL_DATA.filter(d => d.year === year), [year]);

  const reductions = ['Random Forest','XGBoost','Lasso/Ridge'].map(m => {
    const MODELS_DATA = simulateModels(raw);
    const base = MODELS_DATA[m];
    const kriging = MODELS_DATA['Kriging + ML'];
    return { m, base: base.rmse, kriging: kriging.rmse,
      delta: ((base.rmse - kriging.rmse)/base.rmse*100).toFixed(1) };
  });

  return (
    <div>
      <SectionTitle sub="Kriging de residuos — captura la estructura espacial no explicada por ML">
        Kriging de Residuos
      </SectionTitle>
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:10, marginBottom:18 }}>
        <Metric label="Nugget" value="0.040" unit="(ton/ha)²" color="oklch(55% 0.04 145)"/>
        <Metric label="Sill" value="0.300" unit="(ton/ha)²" color="oklch(52% 0.18 148)"/>
        <Metric label="Range" value="58" unit="km" color="oklch(68% 0.16 72)"/>
        <Metric label="Modelo" value="Exp." color="oklch(72% 0.16 145)"/>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
        <Card>
          <CardTitle>Variograma Empírico + Modelo Teórico (Exponencial)</CardTitle>
          <VariogramChart data={vData}/>
          <div style={{ fontSize:11, color:'oklch(50% 0.04 145)', marginTop:10, lineHeight:1.7 }}>
            Dependencia espacial hasta ~58 km. El nugget bajo (0.04) indica alta reproducibilidad.
            El sill (0.30) representa la varianza total de los residuos.
          </div>
        </Card>
        <Card>
          <CardTitle>Mapa de Residuos — RF post-Kriging · {year}</CardTitle>
          <ColombiaMap data={ALL_DATA} colorKey="rendimiento" year={year}
            selectedId={selectedId} onSelect={setSelectedId}/>
        </Card>
      </div>

      <Card style={{ marginTop:16 }}>
        <CardTitle>Reducción de RMSE: ML puro vs ML + Kriging de residuos</CardTitle>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:16 }}>
          {reductions.map(({m, base, kriging: k, delta}) => (
            <div key={m} style={{ background:'oklch(22% 0.03 145)', borderRadius:8, padding:16,
              border:'1px solid oklch(28% 0.04 145)' }}>
              <div style={{ fontWeight:600, fontSize:12, marginBottom:12 }}>{m}</div>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:6 }}>
                <span style={{ fontSize:11, color:'oklch(55% 0.04 145)' }}>RMSE base</span>
                <span style={{ fontFamily:'monospace', fontSize:12, color:'oklch(68% 0.16 72)' }}>{base.toFixed(3)}</span>
              </div>
              <div style={{ display:'flex', justifyContent:'space-between', marginBottom:12 }}>
                <span style={{ fontSize:11, color:'oklch(55% 0.04 145)' }}>RMSE + Kriging</span>
                <span style={{ fontFamily:'monospace', fontSize:12, color:'oklch(52% 0.18 148)' }}>{k.toFixed(3)}</span>
              </div>
              <div style={{ background:'oklch(52% 0.18 148 / 0.15)', borderRadius:6, padding:'8px 10px', textAlign:'center' }}>
                <span style={{ fontFamily:'monospace', color:'oklch(72% 0.16 145)', fontSize:16, fontWeight:700 }}>
                  −{delta}% RMSE
                </span>
              </div>
              <div style={{ marginTop:10, height:8, background:'oklch(28% 0.04 145)', borderRadius:4, position:'relative' }}>
                <div style={{ position:'absolute', left:0, top:0, height:'100%',
                  width:`${(base/0.7)*100}%`, background:'oklch(68% 0.16 72)', borderRadius:4, opacity:0.6 }}/>
                <div style={{ position:'absolute', left:0, top:0, height:'100%',
                  width:`${(k/0.7)*100}%`, background:'oklch(52% 0.18 148)', borderRadius:4 }}/>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card style={{ marginTop:16 }}>
        <CardTitle>Tendencia histórica Kriging RMSE vs ML puro</CardTitle>
        <svg width="500" height="160">
          {YEARS.map((y, i) => {
            const raw2 = ALL_DATA.filter(d=>d.year===y);
            const MODELS_DATA = simulateModels(raw2);
            const rf = MODELS_DATA['Random Forest'].rmse;
            const krig = MODELS_DATA['Kriging + ML'].rmse;
            const x = 45 + (i/(YEARS.length-1))*430;
            const toH = v => (v/0.7)*120;
            return (
              <g key={y}>
                <rect x={x-16} y={145-toH(rf)} width={14} height={toH(rf)}
                  fill="oklch(68% 0.16 72)" rx={2} opacity={0.7}/>
                <rect x={x+2} y={145-toH(krig)} width={14} height={toH(krig)}
                  fill="oklch(52% 0.18 148)" rx={2} opacity={0.85}/>
                <text x={x} y={156} textAnchor="middle"
                  fill="oklch(50% 0.04 145)" fontSize={9} fontFamily="monospace">{y}</text>
              </g>
            );
          })}
          <line x1={28} y1={10} x2={28} y2={147} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
          <line x1={28} y1={145} x2={480} y2={145} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
          <circle cx={70} cy={168} r={5} fill="oklch(68% 0.16 72)"/>
          <text x={78} y={172} fill="oklch(55% 0.04 145)" fontSize={10}>RF puro</text>
          <circle cx={140} cy={168} r={5} fill="oklch(52% 0.18 148)"/>
          <text x={148} y={172} fill="oklch(55% 0.04 145)" fontSize={10}>RF + Kriging</text>
        </svg>
      </Card>
    </div>
  );
}

// ─── PAGE COMPARACION ─────────────────────────────────────────────────────────
function PageComparacion({ year }) {
  const raw = React.useMemo(() => ALL_DATA.filter(d => d.year === year), [year]);
  const MODELS_DATA = React.useMemo(() => simulateModels(raw), [raw]);
  const allModels = Object.keys(MODELS_DATA);
  const [activeModel, setActiveModel] = React.useState('XGBoost');

  return (
    <div>
      <SectionTitle sub="Tabla comparativa completa — validación aleatoria vs espacial por bloques">
        Comparación de Modelos
      </SectionTitle>

      <Card style={{ marginBottom:20 }}>
        <CardTitle>Tabla de métricas · {year}</CardTitle>
        <div style={{ overflowX:'auto' }}>
          <table style={{ width:'100%', borderCollapse:'collapse', fontSize:12 }}>
            <thead>
              <tr>
                {['Modelo','RMSE (CV aleat.)','RMSE (CV espacial)','Δ Brecha','MAE','R²','Moran I res.','Rank'].map(h => (
                  <th key={h} style={{ textAlign:'left', padding:'8px 14px',
                    borderBottom:'1px solid oklch(28% 0.04 145)', color:'oklch(50% 0.04 145)',
                    fontWeight:500, whiteSpace:'nowrap', fontFamily:'monospace' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allModels.map((m, i) => {
                const d = MODELS_DATA[m];
                const isBest = m === 'Kriging + ML';
                const brecha = d.rmse_spatial - d.rmse;
                return (
                  <tr key={m}
                    onClick={() => setActiveModel(m)}
                    style={{ background: m===activeModel ? 'oklch(38% 0.14 148 / 0.12)' : 'transparent',
                      cursor:'pointer', transition:'background 0.15s' }}>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      color: isBest ? 'oklch(72% 0.16 145)' : 'oklch(85% 0.02 145)',
                      fontWeight: isBest ? 700 : 400 }}>
                      {m}
                      {isBest && <span style={{ marginLeft:6, fontSize:10,
                        background:'oklch(52% 0.18 148 / 0.2)', color:'oklch(72% 0.16 145)',
                        padding:'1px 6px', borderRadius:3 }}>★ mejor</span>}
                    </td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace', color: d.rmse<0.40?'#4ade80':d.rmse>0.50?'#f87171':'oklch(68% 0.16 72)' }}>
                      {d.rmse.toFixed(3)}
                    </td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace', color:'oklch(60% 0.04 145)' }}>
                      {d.rmse_spatial.toFixed(3)}
                    </td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace', color: brecha>0.10?'#f87171':'oklch(60% 0.04 145)' }}>
                      +{brecha.toFixed(3)}
                    </td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace' }}>{d.mae.toFixed(3)}</td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace', color: d.r2>0.75?'#4ade80':'oklch(80% 0.02 145)' }}>
                      {d.r2.toFixed(3)}
                    </td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace', color: d.moran_residuos>0.1?'#f87171':'#4ade80' }}>
                      {d.moran_residuos.toFixed(3)}
                      {d.moran_residuos>0.1&&<span style={{marginLeft:4,fontSize:10}}>⚠</span>}
                    </td>
                    <td style={{ padding:'10px 14px', borderBottom:'1px solid oklch(24% 0.03 145)',
                      fontFamily:'monospace', textAlign:'center',
                      color: i===4?'oklch(72% 0.16 145)':'oklch(55% 0.04 145)' }}>
                      {['3','2','5','4','1'][i]}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ fontSize:11, color:'oklch(45% 0.04 145)', marginTop:8 }}>
          Haz clic en una fila para ver detalles abajo · CV espacial = bloques departamentales
        </div>
      </Card>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16 }}>
        <Card>
          <CardTitle>RMSE: CV aleatoria vs CV espacial</CardTitle>
          <svg width="380" height="200">
            {allModels.map((m, i) => {
              const d = MODELS_DATA[m];
              const x = 42 + i*70;
              const hBase = (d.rmse/0.7)*150;
              const hSpat = (d.rmse_spatial/0.7)*150;
              return (
                <g key={m}>
                  <rect x={x} y={168-hBase} width={24} height={hBase}
                    fill={m===activeModel?'oklch(52% 0.18 148)':'oklch(38% 0.10 148)'} rx={2} opacity={0.85}/>
                  <rect x={x+26} y={168-hSpat} width={24} height={hSpat}
                    fill={m===activeModel?'oklch(68% 0.16 72)':'oklch(48% 0.12 72)'} rx={2} opacity={0.85}/>
                  <text x={x+24} y={185} textAnchor="middle"
                    fill="oklch(50% 0.04 145)" fontSize={8}>{m.slice(0,8)}</text>
                </g>
              );
            })}
            <line x1={28} y1={10} x2={28} y2={170} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
            <line x1={28} y1={168} x2={370} y2={168} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
            <circle cx={42} cy={197} r={5} fill="oklch(52% 0.18 148)"/>
            <text x={50} y={201} fill="oklch(55% 0.04 145)" fontSize={9}>CV aleatoria</text>
            <circle cx={130} cy={197} r={5} fill="oklch(68% 0.16 72)"/>
            <text x={138} y={201} fill="oklch(55% 0.04 145)" fontSize={9}>CV espacial</text>
          </svg>
        </Card>
        <Card>
          <CardTitle>Moran I residuos por modelo</CardTitle>
          <svg width="380" height="200">
            <line x1={40} y1={168-(0.1/0.30)*150} x2={370} y2={168-(0.1/0.30)*150}
              stroke="#f87171" strokeWidth={1} strokeDasharray="4 3" opacity={0.6}/>
            <text x={42} y={168-(0.1/0.30)*150-4} fill="#f87171" fontSize={9} opacity={0.8}>umbral p=0.05</text>
            {allModels.map((m, i) => {
              const d = MODELS_DATA[m];
              const h = (d.moran_residuos/0.30)*150;
              const x = 48 + i*66;
              return (
                <g key={m}>
                  <rect x={x} y={168-h} width={40} height={h}
                    fill={d.moran_residuos>0.1?'#f87171':'#4ade80'} rx={2} opacity={0.8}/>
                  <text x={x+20} y={184} textAnchor="middle"
                    fill="oklch(50% 0.04 145)" fontSize={8}>{m.slice(0,7)}</text>
                  <text x={x+20} y={168-h-5} textAnchor="middle"
                    fill="oklch(65% 0.04 145)" fontSize={9} fontFamily="monospace">
                    {d.moran_residuos.toFixed(2)}
                  </text>
                </g>
              );
            })}
            <line x1={28} y1={10} x2={28} y2={170} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
            <line x1={28} y1={168} x2={370} y2={168} stroke="oklch(28% 0.04 145)" strokeWidth={1}/>
          </svg>
        </Card>
      </div>

      {/* Active model scatter */}
      <Card>
        <CardTitle>Observado vs Predicho — {activeModel}</CardTitle>
        <div style={{ display:'grid', gridTemplateColumns:'auto 1fr', gap:24, alignItems:'start' }}>
          <ScatterChart data={MODELS_DATA[activeModel].predictions}/>
          <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {[
              ['RMSE (CV aleatoria)', MODELS_DATA[activeModel].rmse.toFixed(3), 'oklch(68% 0.16 72)'],
              ['RMSE (CV espacial)',  MODELS_DATA[activeModel].rmse_spatial.toFixed(3), '#f59e0b'],
              ['MAE',                MODELS_DATA[activeModel].mae.toFixed(3), 'oklch(68% 0.16 72)'],
              ['R²',                 MODELS_DATA[activeModel].r2.toFixed(3), 'oklch(52% 0.18 148)'],
              ['Moran I residuos',   MODELS_DATA[activeModel].moran_residuos.toFixed(3),
               MODELS_DATA[activeModel].moran_residuos>0.1?'#f87171':'#4ade80'],
            ].map(([l,v,c]) => (
              <div key={l} style={{ display:'flex', justifyContent:'space-between',
                borderBottom:'1px solid oklch(24% 0.03 145)', paddingBottom:8 }}>
                <span style={{ fontSize:12, color:'oklch(60% 0.04 145)' }}>{l}</span>
                <span style={{ fontFamily:'monospace', fontSize:13, fontWeight:600, color:c }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      </Card>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12, marginTop:16 }}>
        {[
          ['oklch(52% 0.18 148)','ML + Kriging de Residuos',
           'Mejor desempeño global. RMSE = 0.31, R² = 0.83, Moran I residuos = 0.03 (no significativo). Combina poder predictivo del ML con corrección espacial explícita.'],
          ['oklch(68% 0.16 72)','Brecha CV aleatoria/espacial',
           'Lasso/Ridge muestra la mayor brecha (+0.15), indicando que explota autocorrelación durante entrenamiento. XGBoost es el ML puro más robusto a esta brecha (+0.07).'],
          ['#f87171','Autocorrelación residual',
           'Random Forest (0.18) y Lasso (0.24) dejan estructura espacial en residuos. El GWR reduce parcialmente (0.09). Solo ML+Kriging la elimina (0.03).'],
        ].map(([color, title, text]) => (
          <div key={title} style={{ background:'oklch(22% 0.03 145)', borderRadius:8, padding:14,
            borderLeft:`3px solid ${color}` }}>
            <div style={{ fontWeight:600, marginBottom:6, fontSize:12, color }}>
              {title}
            </div>
            <div style={{ color:'oklch(58% 0.04 145)', fontSize:11, lineHeight:1.7 }}>{text}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, {
  Card, SectionTitle, Metric, Tag, CardTitle, Alert, MunDetailPanel,
  PageEDA, PageMoran, PageML, PageKriging, PageComparacion,
});
