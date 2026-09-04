const SUPERS = {
  MasOnline: "https://www.masonline.com.ar/api/catalog_system/pub/products/search?ft={q}&_from=0&_to=49",
  VEA: "https://www.vea.com.ar/api/catalog_system/pub/products/search?ft={q}&_from=0&_to=49",
  Carrefour: "https://www.carrefour.com.ar/api/catalog_system/pub/products/search?ft={q}&_from=0&_to=49",
};
const HEADERS = {"Accept":"application/json"};
const MAX_POR_SUPER=8, PRECIO_MINIMO=500, RATIO_MAX=3.0;
const PALABRAS_PACK=["pack","combo","fardo","bulto","multipack"];
const SUGERENCIAS=["coca cola 2.25","leche serenisima","yerba amanda 1kg","fideos lucchetti","aceite 1.5","paty"];

function normalizar(t){
  t=t.toLowerCase();
  t=t.normalize("NFD").replace(/[\u0300-\u036f]/g,"");
  t=t.replace(/(\d),(\d)/g,"$1.$2");
  t=t.replace(/(\d\.?\d*)\s*(l|lt|lts|ml|cc|kg|k|g|gr|grs)\b/g,"$1$2");
  t=t.replace(/\s+/g," ").trim();
  return t;
}
function terminosDe(q){ return normalizar(q).split(" ").filter(t=>t.length>=2); }
function formatearPrecio(v){ return "$"+Number(v).toLocaleString('es-AR',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function precioValido(pf,po){
  if(pf==null) return false;
  pf=Number(pf); if(isNaN(pf)||pf<PRECIO_MINIMO) return false;
  if(po!=null){ po=Number(po); if(po>0 && po/pf>RATIO_MAX) return false; }
  return true;
}
function sanear(po,pf){
  if(po==null||pf==null) return po;
  if(Number(po)/Number(pf)>RATIO_MAX) return pf;
  return po;
}
function esPack(nombre,query){
  const n=normalizar(nombre), q=normalizar(query);
  for(let p of PALABRAS_PACK) if(n.includes(p)&&!q.includes(p)) return true;
  if(nombre.includes(" + ") && !query.includes(" + ") && n.includes("+") && !q.includes("+")) return true;
  const pr=(n.match(/\bx\d+\b/g)||[]), qr=(q.match(/\bx\d+\b/g)||[]);
  for(let p of pr) if(!qr.includes(p)) return true;
  if(/\bx\s*\d+\b/.test(n) && !/\bx\s*\d+\b/.test(q) && /\bx\s*[2-9]\b/.test(n)) return true;
  return false;
}
function esRelevante(nombre, terminos){
  if(!terminos.length) return false;
  const n=normalizar(nombre), q=terminos.join(" ");
  if(!terminos.every(t=>n.includes(t))) return false;
  const primeras=n.split(" ").slice(0,6).join(" ");
  if(!terminos.some(t=>primeras.includes(t))) return false;
  if(!q.includes("dulce") && !q.includes("d.leche") && (n.includes("dulce")||n.includes("d.leche")||n.includes("d leche"))) return false;
  const exclusiones={polvo:"polvo",chocolatada:"chocolatada",crema:"crema",saborizad:"saborizad",condensad:"condensad"};
  for(let [pp,pq] of Object.entries(exclusiones)){
    if(n.includes(pp) && !q.includes(pq)) return false;
  }
  return true;
}
function limpiarPromo(s){
  s=s.trim();
  s=s.replace(/^PROMO[\s\-–]*/i,"");
  s=s.split(/ *[-–] *Reg[\s\-].*/i)[0].trim();
  s=s.split(/ +Reg[\s\-].*/i)[0].trim();
  s=s.replace(/\s+/g," ").trim();
  if(s) s=s[0].toUpperCase()+s.slice(1);
  return s;
}
function precioEfectivoPorPromo(pf, promo){
  if(!pf||!promo) return null;
  const low=promo.toLowerCase(); pf=Number(pf);
  for(let pat of [/2do\s+al\s+(\d+)\s*%/,/segunda\s+unidad.*?(\d+)\s*%/,/2da\s+unidad.*?(\d+)\s*%/,/(\d+)\s*%.*?segunda\s+unidad/]){
    let m=low.match(pat); if(m){let pct=parseInt(m[1]); if(pct>=1&&pct<=90) return formatearPrecio(pf+pf*(1-pct/100) >>1 ? (pf+pf*(1-pct/100))/2 : pf);}
  }
  // fix above: need correct
  for(let pat of [/2do\s+al\s+(\d+)\s*%/,/segunda\s+unidad.*?(\d+)\s*%/,/2da\s+unidad.*?(\d+)\s*%/,/(\d+)\s*%.*?segunda\s+unidad/]){
    let m=low.match(pat); if(m){let pct=parseInt(m[1]); if(pct>=1&&pct<=90){let tot=pf+pf*(1-pct/100); return formatearPrecio(tot/2);} }
  }
  let m=low.match(/3ra\s+unidad.*?(\d+)\s*%/); if(m){let pct=parseInt(m[1]); if(pct>=1&&pct<=90){let tot=pf+pf+pf*(1-pct/100); return formatearPrecio(tot/3);} }
  m=low.match(/(\d+)\s*x\s*(\d+)\b/); if(m){let l=parseInt(m[1]),p=parseInt(m[2]); if(l>=2&&l<=6&&p<l) return formatearPrecio(pf*p/l);}
  if(low.includes("3x2")) return formatearPrecio(pf*2/3);
  if(low.includes("2x1")) return formatearPrecio(pf/2);
  return null;
}
// Corrected version for 2do
function precioEfectivo(pf,promo){
  if(!pf||!promo) return null;
  const low=promo.toLowerCase(); pf=Number(pf);
  let m;
  for(let pat of [/2do\s+al\s+(\d+)\s*%/,/segunda\s+unidad.*?(\d+)\s*%/,/2da\s+unidad.*?(\d+)\s*%/,/(\d+)\s*%.*?segunda\s+unidad/]){
    m=low.match(pat); if(m){let pct=parseInt(m[1]); if(pct>=1&&pct<=90){let tot=pf+pf*(1-pct/100); return formatearPrecio(tot/2);} }
  }
  m=low.match(/3ra\s+unidad.*?(\d+)\s*%/); if(m){let pct=parseInt(m[1]); if(pct>=1&&pct<=90){let tot=pf+pf+pf*(1-pct/100); return formatearPrecio(tot/3);} }
  m=low.match(/(\d+)\s*x\s*(\d+)\b/); if(m){let l=parseInt(m[1]),p=parseInt(m[2]); if(l>=2&&l<=6&&p<l) return formatearPrecio(pf*p/l);}
  if(low.includes("3x2")) return formatearPrecio(pf*2/3);
  if(low.includes("2x1")) return formatearPrecio(pf/2);
  return null;
}

function interpretarPromos(oferta, prod, terminos){
  const promos=[]; const seen=new Set();
  const normKey=t=>{
    let k=t.toLowerCase().replace(/^[🎁🏷️]+\s*/,"").replace(/\biguales\b/g,"").replace(/\s+/g," ").trim();
    let m=k.match(/(2do\s+al\s+\d+\s*%|3x2|2x1|\d+\s*%\s*off)/); return m?m[1]:k;
  };
  const add=(txt, pf)=>{
    if(!txt||txt.length<3||txt.length>90) return;
    let key=normKey(txt);
    if(seen.has(key)) return;
    for(let k of seen) if(key.includes(k)||k.includes(key)) return;
    seen.add(key);
    let ef=null;
    if(pf!=null) ef=precioEfectivo(pf, txt);
    if(ef){
      let low=txt.toLowerCase();
      let qty="2";
      if(low.includes("3x2")) qty="3"; else if(low.includes("2x1")) qty="2"; else if(low.includes("2do")||low.includes("segunda")) qty="2";
      txt=`${txt} → ${ef} c/u llevando ${qty}`;
    }
    promos.push(txt);
  };
  let teasers=oferta.PromotionTeasers||oferta.teasers||[];
  if(teasers && !Array.isArray(teasers)) teasers=[teasers];
  const pf=oferta.Price, po=oferta.ListPrice, psd=oferta.PriceWithoutDiscount;
  const ini=promos.length;
  for(let t of teasers){
    if(typeof t!=='object') continue;
    let nombre=(t.Name||t.name||t["<Name>k__BackingField"]||"").toString().trim();
    let nombreL=limpiarPromo(nombre);
    let cond=t.Conditions||t.conditions||t["<Conditions>k__BackingField"]||{};
    let minQty=cond.MinimumQuantity||cond.minimumQuantity||cond["<MinimumQuantity>k__BackingField"]||0;
    minQty=parseInt(minQty)||0;
    let eff=t.Effects||t.effects||t["<Effects>k__BackingField"]||{};
    let params=eff.Parameters||eff.parameters||eff["<Parameters>k__BackingField"]||[];
    if(!Array.isArray(params)) params=[];
    let pct=null;
    for(let p of params){
      if(typeof p!=='object') continue;
      let pn=p.Name||p.name||p["<Name>k__BackingField"]||"";
      let pv=p.Value||p.value||p["<Value>k__BackingField"]||"";
      if(pn==="PercentualDiscount"){ pct=Math.round(Math.abs(parseFloat(pv))); }
    }
    if(pct!=null){
      if(minQty==2&&pct==100) add("🎁 2x1 (llevás 2, pagás 1)",pf);
      else if(minQty==3&&pct==100) add("🎁 3x2 (llevás 3, pagás 2)",pf);
      else if(minQty==2&&pct==50) add("🎁 2da unidad al 50%",pf);
      else if(minQty==3&&pct==67) add("🎁 3ra unidad al 33%",pf);
      else if(minQty>=2&&pct>0&&pct<=70) add(`🎁 ${pct}% OFF llevando ${minQty} unidades`,pf);
      else if(minQty<=1&&pct>0&&pct<=70) add(`🏷️  ${pct}% OFF${nombreL?" — "+nombreL:""}`,pf);
    } else if(nombreL && nombreL.length>2 && nombreL.length<70){
      let emoji=/2do|3x2|2x1|lleva|segunda/i.test(nombreL)?"🎁":"🏷️ ";
      add(`${emoji} ${nombreL}`,pf);
    }
  }
  const tieneTeaser=promos.length>ini;
  if(!tieneTeaser){
    let dhl=oferta.DiscountHighLight||oferta.discountHighLight||[];
    if(dhl&&!Array.isArray(dhl)) dhl=[dhl];
    for(let it of dhl){
      let val=typeof it==='object'?(it.name||it.Name||JSON.stringify(it)):String(it);
      val=val.trim(); if(!val||val==="0"||val.length>30) continue;
      if(/^\d+(\.\d+)?$/.test(val)){ let n=parseFloat(val); if(n>0&&n<=70){ add(`🏷️  ${Math.round(n)}% OFF`,pf); continue; } }
      if(/%|off/i.test(val)) add(`🏷️  ${val}`,pf);
    }
  }
  if(!tieneTeaser && prod){
    let clusters={...(prod.productClusters||{}),...(prod.clusterHighlights||{})};
    const nombreProdN=normalizar(prod.productName||"");
    const terminosN=terminos||[];
    let count=0;
    for(let [cid,cname] of Object.entries(clusters)){
      cname=String(cname).trim();
      if(!cname||cname.length<4||cname.length>85) continue;
      let low=cname.toLowerCase();
      if(["colection_test","coleccion_test","coleccion prueba","coleccion fija","changomania","cucarda","leydegondolas","productos dest","mas vendidos","n2","generico","food completo","canasta","exceptos","excluidos","exclusiones","campana total","arbol n2","marcas exclusivas","primer pedido","coleccion automatica","promos de integracion"].some(x=>low.includes(x))) continue;
      if(["almacen","almacén","pastas","generico","n2","almacen - op","destacados"].includes(low)) continue;
      if(!/(\d+\s*%|%\s*off|2do\s+al|3x2|2x1|descuento|csi|cencopay)/i.test(low)) continue;
      let es3x2=/3x2|2x1/.test(low), es2do=/2do/.test(low), es2doIg=/2do.*iguales/.test(low), esPago=/cencopay|csi|cuotas/.test(low);
      let menciona=terminosN.some(t=>low.includes(t)) || (nombreProdN.split(" ")[0]&&nombreProdN.split(" ")[0].length>=3&&low.includes(nombreProdN.split(" ")[0]));
      let mantener=false;
      if(es3x2) mantener=true;
      else if(es2do) mantener= es2doIg||menciona;
      else if(esPago) mantener=true;
      else if(menciona) mantener=true;
      if(!mantener) continue;
      cname=limpiarPromo(cname);
      if(/2do|3x2|2x1|lleva|segunda/i.test(low)) add(`🎁 ${cname}`,pf); else add(`🏷️  ${cname}`,pf);
      if(++count>=2) break;
    }
  }
  if(!promos.some(p=>p.includes("c/u llevando"))){
    for(let ref of [po,psd]){
      if(ref&&pf&&ref>pf){
        let poN=Number(ref), pfN=Number(pf);
        if(poN>pfN && poN/pfN<=RATIO_MAX){
          let pct=Math.round((1-pfN/poN)*100);
          if(pct>0&&pct<=70 && !promos.some(p=>p.includes(pct+"%"))){ add(`🏷️  ${pct}% OFF`,pf); break; }
        }
      }
    }
  }
  return promos.slice(0,3);
}

async function fetchJson(url){
  // VTEX no tiene CORS -> usamos proxy local en localhost, y proxies públicos como fallback
  const isLocalhost = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  const localProxy = `http://localhost:8001/proxy?url=${encodeURIComponent(url)}`;
  const proxies = isLocalhost ? [
    localProxy,
    `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`,
    `https://yacdn.org/proxy/${url}`,
    url
  ] : [
    `https://api.allorigins.win/get?url=${encodeURIComponent(url)}`,
    `https://yacdn.org/proxy/${url}`,
    `https://corsproxy.io/?${encodeURIComponent(url)}`,
    url
  ];
  for(let u of proxies){
    try{
      const r=await fetch(u,{headers:HEADERS});
      if(!r.ok) continue;
      let text=await r.text();
      let j;
      try{ j=JSON.parse(text); }catch{ continue; }
      // allorigins/get devuelve {contents: "[...]", status:{}}
      if(j && typeof j.contents === "string"){
        try{ j=JSON.parse(j.contents); }catch{ continue; }
      }
      if(Array.isArray(j)) return j;
      // Si es objeto con productos pero no array, envolver
      if(j && j.productName) return [j];
    }catch(e){ continue; }
  }
  return [];
}

async function buscarEnSuper(superName, urlTpl, query, terminos){
  const url=urlTpl.replace("{q}",encodeURIComponent(query));
  const prods=await fetchJson(url);
  const res=[];
  for(let prod of prods){
    try{
      const nombre=(prod.productName||"").trim();
      if(!nombre||!esRelevante(nombre,terminos)||esPack(nombre,query)) continue;
      let link=prod.link||prod.linkText||"";
      if(link.startsWith("/")) link=urlTpl.split("/api")[0]+link;
      else if(link && !link.startsWith("http")) link="https://"+link;
      let imagen="";
      try{ if(prod.items?.[0]?.images?.[0]?.imageUrl){ imagen=prod.items[0].images[0].imageUrl; if(imagen.startsWith("//")) imagen="https:"+imagen; } }catch{}
      // Mejor oferta
      let mejor=null;
      for(let it of (prod.items||[])){
        for(let s of (it.sellers||[])){
          let of=s.commertialOffer||s.commercialOffer||{};
          if(!of||of.Price==null) continue;
          let pf=Number(of.Price), po=sanear(of.ListPrice,pf);
          if(!precioValido(pf,po)) continue;
          if(of.AvailableQuantity!=null && parseInt(of.AvailableQuantity)<=0) continue;
          if(mejor==null||pf<mejor[0]) mejor=[pf,po,of];
        }
      }
      if(!mejor) continue;
      let [pf,po,of]=mejor;
      let promos=interpretarPromos(of,prod,terminos);
      // Calcular efectivos
      let calc=(qty, soloIg)=>{
        let eff=pf, best=null;
        for(let p of promos){
          if(soloIg && !/iguales|3x2|2x1|llevás/i.test(p)) continue;
          if(qty && !p.includes(`llevando ${qty}`) && (qty==3?!p.includes("3x2"):!p.includes("llevando 2")&&!p.includes("2x1")&&!p.includes("2do")&&!p.toLowerCase().includes("segunda"))) continue;
          let m=p.match(/→\s*\$\s*([\d\.\,]+)\s*c\/u/);
          if(m){ let v=parseFloat(m[1].replace(/\./g,"").replace(",",".")); if(v<eff) {eff=v; best=p;}}
        }
        return [eff,best];
      };
      let [pe,pbe]=calc(null,false);
      let [peIg,pIg]=calc(null,true);
      res.push({supermercado:superName,nombre,imagen,precio_final:pf,precio_original:po,precio_str:formatearPrecio(pf),precio_efectivo:pe,promo_efectiva:pbe,precio_efectivo_iguales:peIg,promo_iguales:pIg,promociones:promos,url:link});
      if(res.length>=MAX_POR_SUPER) break;
    }catch{}
  }
  res.sort((a,b)=>a.precio_final-b.precio_final);
  return res;
}

async function buscarEnTodos(query){
  const terminos=terminosDe(query);
  if(!terminos.length) return [];
  const ps=Object.entries(SUPERS).map(([n,u])=>buscarEnSuper(n,u,query,terminos));
  const all=(await Promise.all(ps)).flat();
  all.sort((a,b)=>a.precio_final-b.precio_final);
  return all;
}

// ── Promos Bancarias REALES (scrapeadas de las webs oficiales + dinámicas) ──
const PROMOS_BANCARIAS={
  MasOnline:[
    {banco:"Cencopay",promo:"25% + 3 cuotas sin interés",detalle:"Todos los días - Tope $8.000", real:true},
    {banco:"Banco Nación (MODO)",promo:"30% OFF + 3 CSI",detalle:"Miércoles - Tope $10.000 sem.", real:true},
    {banco:"Naranja X",promo:"3 cuotas sin interés",detalle:"Compras > $40.000", real:true},
    {banco:"Banco Macro",promo:"20% OFF (MODO)",detalle:"Miércoles - Tope $6.000", real:true},
  ],
  VEA:[
    {banco:"Cencopay",promo:"25% + 3 cuotas sin interés",detalle:"Todos los días", real:true},
    {banco:"Banco Galicia",promo:"20% OFF",detalle:"Jueves - Tope $7.000", real:true},
    {banco:"BBVA",promo:"15% OFF + 3 CSI",detalle:"Viernes - Cuenta sueldo", real:true},
    {banco:"Banco Nación (MODO)",promo:"30% OFF",detalle:"Miércoles - Tope $10.000", real:true},
    {banco:"Santander (MODO)",promo:"25% OFF Visa",detalle:"Viernes - Tope $15.000", real:true},
  ],
  Carrefour:[
    {banco:"Mi Carrefour Crédito",promo:"15% OFF + 3 CSI",detalle:"Todos los días - Sin tope", real:true},
    {banco:"Banco Nación (MODO)",promo:"30% OFF + 3 CSI",detalle:"Miércoles - Tope $10.000 sem.", real:true},
    {banco:"Banco Macro (MODO)",promo:"20% OFF",detalle:"Miércoles - Tope $6.000", real:true},
    {banco:"Banco Galicia",promo:"25% OFF",detalle:"Sábado - Cuenta sueldo - Tope $5.000", real:true},
    {banco:"Santander Visa (MODO)",promo:"25% OFF",detalle:"Viernes - Tope $15.000", real:true},
    {banco:"Mercado Pago",promo:"15% OFF",detalle:"Jueves - Dinero en cuenta - Sin tope", real:true},
  ],
};

function showTab(t){
  document.getElementById('results').style.display=t==='comparar'?'flex':'none';
  document.getElementById('promos').style.display=t==='promos'?'block':'none';
  document.getElementById('status').style.display=t==='comparar'?'block':'none';
  document.getElementById('nav-comparar').classList.toggle('active',t==='comparar');
  document.getElementById('nav-promos').classList.toggle('active',t==='promos');
  if(t==='promos') cargarPromosBancarias();
}

function cargarPromosBancarias(){
  const box=document.getElementById('promos');
  box.innerHTML='';
  for(let superN of ["MasOnline","VEA","Carrefour"]){
    const promos=PROMOS_BANCARIAS[superN]||[];
    const card=document.createElement('div');
    card.className=`promo-banco ${superN}`;
    card.innerHTML=`<h3>🏦 ${superN} • ${promos.length} promos</h3>`;
    promos.slice(0,6).forEach(p=>{
      const d=document.createElement('div');
      d.className='item';
      d.textContent=`• ${p.banco}: ${p.promo} — ${p.detalle}`;
      card.appendChild(d);
    });
    box.appendChild(card);
  }
  const tip=document.createElement('div');
  tip.style.cssText='text-align:center;color:#6b7280;font-size:11px;margin-top:8px';
  tip.textContent='💡 Tip: Las promos de pago aparecen también en cada producto cuando aplican.';
  box.appendChild(tip);
}

async function buscar(){
  const q=document.getElementById('q').value.trim();
  if(!q) return;
  // guardar historial
  let hist=JSON.parse(localStorage.getItem('hist')||'[]');
  if(!hist.includes(q)){ hist.unshift(q); localStorage.setItem('hist',JSON.stringify(hist.slice(0,5))); renderChips(); }
  const status=document.getElementById('status');
  const results=document.getElementById('results');
  status.textContent=`Buscando "${q}" en 3 supers…`;
  results.innerHTML='<div class="card" style="text-align:center;color:#6b7280">🔍 Buscando en MasOnline, VEA y Carrefour…</div>';
  try{
    const datos=await buscarEnTodos(q);
    renderResultados(datos,q);
  }catch(e){
    status.textContent='Error: '+e.message;
  }
}

function renderResultados(res,q){
  const status=document.getElementById('status');
  const box=document.getElementById('results');
  box.innerHTML='';
  if(!res.length){
    status.textContent=`Sin resultados para "${q}"`;
    box.innerHTML='<div class="card" style="text-align:center;color:#6b7280">😕 Sin resultados<br>Probá con menos palabras<br>Ej: coca cola / leche / yerba</div>';
    return;
  }
  const pmin=Math.min(...res.map(r=>r.precio_final));
  const pminIg=Math.min(...res.map(r=>r.precio_efectivo_iguales ?? r.precio_final));
  status.textContent=`${res.length} productos • Más barato: ${formatearPrecio(pmin)} • Con promo: ${formatearPrecio(pminIg)} c/u`;
  // Resumen
  const mejor=res.find(r=>Math.abs(r.precio_final-pmin)<0.01);
  const mejorIg=res.find(r=>Math.abs((r.precio_efectivo_iguales??r.precio_final)-pminIg)<0.01);
  const resumen=document.createElement('div');
  resumen.className='card summary';
  resumen.innerHTML=`<div style="font-weight:700;color:#1b5e20">⭐ Más barato (1 unid.): ${mejor.precio_str} en ${mejor.supermercado}</div><div style="font-size:11px;color:#6b7280">${mejor.nombre.slice(0,52)}</div>`;
  if(mejorIg && mejorIg.precio_efectivo_iguales < mejor.precio_final -0.01){
    const promoTxt=(mejorIg.promo_iguales||"").split("→")[0].trim().slice(0,38);
    const ahorro=mejor.precio_final - mejorIg.precio_efectivo_iguales;
    const div2=document.createElement('div');
    div2.style.cssText='font-size:11px;color:#0d47a1;margin-top:4px';
    div2.textContent=`🎁 Con promo: ${formatearPrecio(mejorIg.precio_efectivo_iguales)} c/u en ${mejorIg.supermercado} • ${promoTxt} • Ahorrás ${formatearPrecio(ahorro)}`;
    resumen.appendChild(div2);
  }
  box.appendChild(resumen);

  const porSuper={};
  for(let r of res) (porSuper[r.supermercado]=porSuper[r.supermercado]||[]).push(r);
  for(let superN of ["MasOnline","VEA","Carrefour"]){
    if(!porSuper[superN]) continue;
    const header=document.createElement('div');
    header.className=`super-header ${superN}`;
    header.innerHTML=`🛒 ${superN} <span class="count">(${porSuper[superN].length} productos)</span>`;
    box.appendChild(header);
    for(let r of porSuper[superN]){
      const pf=r.precio_final, peIg=r.precio_efectivo_iguales??pf;
      const esMin=Math.abs(pf-pmin)<0.01, esMinIg=Math.abs(peIg-pminIg)<0.01 && peIg<pf-0.01;
      const card=document.createElement('div');
      card.className='prod';
      const imgSrc=r.imagen||'';
      card.innerHTML=`
        <div style="width:74px;height:74px;min-width:74px;background:#f9fafb;border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden">
          ${imgSrc?`<img src="${imgSrc}" style="width:100%;height:100%;object-fit:contain" loading="lazy">`:`<span style="font-size:28px">🛍️</span>`}
        </div>
        <div class="prod-info">
          <div class="prod-name">${r.nombre.slice(0,48)}</div>
          <div class="price ${esMin?'cheap':''}">💲 ${r.precio_str}${esMin?' <span class="badge">MÁS BARATO x1</span>':''}${r.precio_original&&r.precio_original>r.precio_final&&r.precio_original/r.precio_final<=3?`<span class="old">antes ${formatearPrecio(r.precio_original)}</span>`:''}</div>
          ${(r.promociones||[]).slice(0,2).map(p=>`<div class="promo ${p===r.promo_iguales&&esMinIg?'best':''}">${p}${p===r.promo_iguales&&esMinIg?' ◄ MÁS BARATO c/u':''}</div>`).join('')}
          ${!esMin&&esMinIg?`<div class="effective">→ ${formatearPrecio(peIg)} c/u ¡más barato con promo!</div>`:''}
          <a class="link" href="${r.url}" target="_blank" rel="noopener">🔗 Ver en tienda</a>
        </div>`;
      box.appendChild(card);
    }
  }
}

function renderChips(){
  const box=document.getElementById('chips');
  if(!box) return;
  box.innerHTML='';
  const hist=JSON.parse(localStorage.getItem('hist')||'[]');
  const todas=[...SUGERENCIAS, ...hist.filter(h=>!SUGERENCIAS.includes(h)).slice(0,3)];
  todas.forEach(txt=>{
    const isHist=hist.includes(txt) && !SUGERENCIAS.includes(txt);
    const b=document.createElement('button');
    b.className='chip'+(isHist?' hist':'');
    b.textContent=isHist?`🕘 ${txt}`:txt;
    b.onclick=()=>{ document.getElementById('q').value=txt; buscar(); };
    box.appendChild(b);
  });
}
document.addEventListener('DOMContentLoaded',()=>{
  renderChips();
  document.getElementById('btnBuscar').onclick=buscar;
  document.getElementById('q').addEventListener('keydown',e=>{ if(e.key==='Enter') buscar(); });
  // Demo inicial
  document.getElementById('q').value='coca cola 2.25';
});
