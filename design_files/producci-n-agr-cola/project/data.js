// ─── DATA ENGINE ─────────────────────────────────────────────────────────────
const seed = (n) => { let x = Math.sin(n + 1) * 10000; return x - Math.floor(x); };

const REGIONES = ['Andina', 'Caribe', 'Pacífica', 'Orinoquía', 'Amazonía'];
const REGION_COLORS = {
  'Andina':    '#4ade80',
  'Caribe':    '#f59e0b',
  'Pacífica':  '#3b82f6',
  'Orinoquía': '#a78bfa',
  'Amazonía':  '#34d399',
};

const REGION_BOUNDS = {
  'Andina':    { latMin: 1,  latMax: 8,  lonMin: -76, lonMax: -72 },
  'Caribe':    { latMin: 8,  latMax: 12, lonMin: -76, lonMax: -72 },
  'Pacífica':  { latMin: 1,  latMax: 7,  lonMin: -78, lonMax: -76 },
  'Orinoquía': { latMin: 2,  latMax: 7,  lonMin: -72, lonMax: -67 },
  'Amazonía':  { latMin: -4, latMax: 2,  lonMin: -74, lonMax: -68 },
};

const MUNICIPIOS_BASE = [
  'Montería','Sincelejo','Valledupar','Cereté','San Andrés de Sotavento',
  'Sahagún','Lorica','Chinú','Planeta Rica','Montelíbano',
  'Maicao','Riohacha','Fonseca','Manaure','San Juan del Cesar',
  'Villavicencio','Puerto López','Acacías','Granada','San Martín',
  'Restrepo','Cumaral','Puerto Gaitán','La Macarena','Mesetas',
  'Ibagué','Espinal','Melgar','Chaparral','Purificación',
  'Neiva','Garzón','Pitalito','La Plata','Campoalegre',
  'Popayán','Santander de Quilichao','Patía','Miranda','Corinto',
  'Tuluá','Buga','Palmira','Cartago','Roldanillo',
  'Armenia','Quimbaya','Calarcá','Montenegro','La Tebaida',
  'Pereira','Dosquebradas','Santa Rosa','Marsella','Balboa',
  'Manizales','Chinchiná','Palestina','Villamaría','Neira',
  'Duitama','Sogamoso','Tunja','Chiquinquirá','Paipa',
  'Bucaramanga','Floridablanca','Girón','Piedecuesta','Lebrija',
  'Cúcuta','Los Patios','Villa del Rosario','Ocaña','Pamplona',
  'Bogotá','Soacha','Zipaquirá','Facatativá','Chía',
  'Medellín','Bello','Itagüí','Envigado','Rionegro',
  'Pasto','Ipiales','Túquerres','La Unión','Samaniego',
  'Florencia','Belén de los Andaquíes','Morelia','Valparaíso','Albania',
  'Yopal','Paz de Ariporo','Aguazul','Tauramena','Orocué',
  'Puerto Inírida','Mitú','Puerto Carreño','San José del Guaviare','Leticia',
  'Cartagena','Barranquilla','Santa Marta','Magangué','Mompox',
  'Bogotá Rural','El Rosal','Mosquera','Madrid','Funza',
  'Cali','Jamundí','Yumbo','Candelaria','Florida',
  'Barrancabermeja','Puerto Berrío','Sabana de Torres','Puerto Wilches','Cimitarra',
];

function generateData() {
  const years = [2018, 2019, 2020, 2021, 2022, 2023];
  const municipios = [];

  MUNICIPIOS_BASE.forEach((nombre, i) => {
    const regionIdx = Math.floor(i / 24) % 5;
    const region = REGIONES[regionIdx];
    const b = REGION_BOUNDS[region];
    const lat = b.latMin + seed(i * 7.3) * (b.latMax - b.latMin);
    const lon = b.lonMin + seed(i * 3.7) * (b.lonMax - b.lonMin);
    const baseYield = 2.0 + Math.sin(lat * 0.8) * 0.9 + Math.cos(lon * 0.6) * 0.7
      + seed(i * 11) * 1.8 - 0.5;
    const area = 500 + seed(i * 5.1) * 4500;

    years.forEach(year => {
      const yearEffect = (year - 2018) * 0.07 + seed(i * year * 0.00013) * 0.2 - 0.1;
      const noise = seed(i * year * 0.001) * 0.5 - 0.25;
      const precip = 800 + seed(i * year * 0.003) * 1400;
      const temp = 18 + seed(i * year * 0.007) * 12;
      const altitude = 100 + seed(i * 13) * 2800;
      const nbi = 10 + seed(i * 17) * 70;
      const dist_mercado = 10 + seed(i * 23) * 200;
      const rendimiento = Math.max(0.4, baseYield + yearEffect + noise
        + (precip > 1200 ? 0.25 : -0.2)
        + (altitude > 1500 ? -0.35 : 0.1));

      municipios.push({
        id: i,
        nombre,
        region,
        lat: +lat.toFixed(4),
        lon: +lon.toFixed(4),
        year,
        rendimiento: +rendimiento.toFixed(3),
        produccion: +(rendimiento * area).toFixed(0),
        area_sembrada: +area.toFixed(0),
        precipitacion: +precip.toFixed(0),
        temperatura: +temp.toFixed(1),
        altitud: +altitude.toFixed(0),
        nbi: +nbi.toFixed(1),
        dist_mercado: +dist_mercado.toFixed(1),
      });
    });
  });
  return municipios;
}

const ALL_DATA = generateData();
const YEARS = [2018, 2019, 2020, 2021, 2022, 2023];
const N_MUNS = MUNICIPIOS_BASE.length;

// Spatial lag for Moran
function addMoranAttrs(data) {
  return data.map((d, i) => {
    const lisa = seed(i * 43) > 0.75
      ? (d.rendimiento > 3.0 ? 'HH' : 'LL')
      : seed(i * 43) > 0.55
        ? (d.rendimiento > 3.0 ? 'HL' : 'LH')
        : 'NS';
    const lag = d.rendimiento * 0.58 + seed(i * 99) * 1.0;
    return { ...d, lisa, lag: +lag.toFixed(3) };
  });
}

function simulateModels(data) {
  const models = {};
  const specs = [
    { name:'Random Forest',  rmse:0.41, mae:0.31, r2:0.71, rmse_sp:0.50, moran:0.18 },
    { name:'XGBoost',        rmse:0.38, mae:0.29, r2:0.76, rmse_sp:0.45, moran:0.15 },
    { name:'Lasso/Ridge',    rmse:0.52, mae:0.40, r2:0.61, rmse_sp:0.67, moran:0.24 },
    { name:'GWR',            rmse:0.44, mae:0.33, r2:0.68, rmse_sp:0.50, moran:0.09 },
    { name:'Kriging + ML',   rmse:0.31, mae:0.23, r2:0.83, rmse_sp:0.35, moran:0.03 },
  ];
  specs.forEach((s, mi) => {
    models[s.name] = {
      ...s,
      rmse_spatial: s.rmse_sp,
      moran_residuos: s.moran,
      predictions: data.map((d, i) => {
        const noise = seed(i * (mi + 1) * 31) * s.rmse * 2 - s.rmse;
        return { obs: d.rendimiento, pred: Math.max(0.3, d.rendimiento + noise), id: d.id, nombre: d.nombre };
      })
    };
  });
  return models;
}

const FEATURES = ['Precipitación','Temperatura','Altitud','NBI','Dist. Mercado','Área Sembrada'];
const SHAP_RF   = [0.31, 0.22, 0.18, 0.11, 0.10, 0.08];
const SHAP_XGB  = [0.28, 0.25, 0.20, 0.12, 0.09, 0.06];
const SHAP_LASSO= [0.27, 0.21, 0.22, 0.13, 0.09, 0.08];

function variogramData() {
  const lags = [10,20,30,40,50,60,70,80,90,100,120,140,160];
  return lags.map((h, i) => ({
    h,
    gamma: +(0.28 * (1 - Math.exp(-h / 55)) + 0.04 + seed(i * 77) * 0.03).toFixed(3),
    theoretical: +(0.30 * (1 - Math.exp(-h / 58)) + 0.04).toFixed(3)
  }));
}

// Export to window
Object.assign(window, {
  seed, REGIONES, REGION_COLORS, REGION_BOUNDS, MUNICIPIOS_BASE,
  ALL_DATA, YEARS, N_MUNS,
  addMoranAttrs, simulateModels,
  FEATURES, SHAP_RF, SHAP_XGB, SHAP_LASSO,
  variogramData,
});
