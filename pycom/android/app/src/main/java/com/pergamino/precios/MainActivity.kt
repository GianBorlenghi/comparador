package com.pergamino.precios

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.*
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder
import java.text.NumberFormat
import java.util.Locale

// Colores por super
val MasOnlineCol = Color(0xFF1565C0)
val VEACol = Color(0xFFC62828)
val CarrefourCol = Color(0xFF0D47A1)
val Teal = Color(0xFF00796B)

data class Producto(
    val supermercado: String,
    val nombre: String,
    val precio: Double,
    val precioOriginal: Double?,
    val precioStr: String,
    val promos: List<String>,
    val precioEfectivo: Double?,
    val promoEfectiva: String?,
    val imagen: String,
    val url: String
)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { PergaminoApp() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PergaminoApp() {
    var query by remember { mutableStateOf("coca cola 2.25") }
    var resultados by remember { mutableStateOf<List<Producto>>(emptyList()) }
    var cargando by remember { mutableStateOf(false) }
    var tab by remember { mutableStateOf(0) } // 0 comparar, 1 promos
    var status by remember { mutableStateOf("Tocá Buscar para comparar") }
    val scope = rememberCoroutineScope()
    val historial = remember { mutableStateListOf("coca cola 2.25","leche serenisima","yerba amanda 1kg","fideos lucchetti") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Column { Text("Pergamino Precios", fontWeight=FontWeight.ExtraBold); Text("MasOnline • VEA • Carrefour", fontSize=11.sp, color=Color.White.copy(0.85f)) } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor=Teal, titleContentColor=Color.White),
                navigationIcon = { Icon(Icons.Filled.Menu, null, tint=Color.White) }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(selected=tab==0, onClick={tab=0}, icon={Icon(Icons.Filled.Search,null)}, label={Text("Comparar")})
                NavigationBarItem(selected=tab==1, onClick={tab=1}, icon={Icon(Icons.Filled.CreditCard,null)}, label={Text("Promos bancarias")})
            }
        }
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize().background(Color(0xFFF5F7F7))) {
            if(tab==0){
                Column(Modifier.fillMaxSize()){
                    // Buscador
                    Card(Modifier.padding(12.dp).fillMaxWidth(), shape=RoundedCornerShape(16.dp), colors=CardDefaults.cardColors(containerColor=Color.White), elevation=CardDefaults.cardElevation(2.dp)){
                        Column(Modifier.padding(12.dp), verticalArrangement=Arrangement.spacedBy(8.dp)){
                            Row(verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(8.dp)){
                                OutlinedTextField(value=query, onValueChange={query=it}, placeholder={Text("Buscá: coca cola 2.25")}, modifier=Modifier.weight(1f), shape=RoundedCornerShape(24.dp), singleLine=true)
                                Button(onClick={
                                    if(query.isNotBlank()){
                                        if(!historial.contains(query)) historial.add(0,query)
                                        cargando=true; status="Buscando en 3 supers…"
                                        scope.launch{
                                            val res=buscarEnTodos(query)
                                            resultados=res
                                            cargando=false
                                            if(res.isEmpty()) status="Sin resultados para \"$query\""
                                            else {
                                                val min=res.minOf{it.precio}
                                                val minIg=res.filter{it.precioEfectivo!=null}.minOfOrNull{it.precioEfectivo!!} ?: min
                                                status="${res.size} productos • Más barato: ${formatear(min)} • Con promo: ${formatear(minIg)} c/u"
                                            }
                                        }
                                    }
                                }, colors=ButtonDefaults.buttonColors(containerColor=Teal)) { Text("Buscar") }
                            }
                            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement=Arrangement.spacedBy(6.dp)){
                                historial.take(5).forEach{ h->
                                    SuggestionChip(onClick={query=h}, label={Text(h, fontSize=12.sp)})
                                }
                            }
                            Text(status, color=Color.Gray, fontSize=11.sp, modifier=Modifier.fillMaxWidth(), textAlign=androidx.compose.ui.text.style.TextAlignment.Center)
                        }
                    }
                    if(cargando){
                        Box(Modifier.fillMaxSize(), contentAlignment=Alignment.Center){ CircularProgressIndicator(color=Teal) }
                    } else {
                        LazyColumn(Modifier.fillMaxSize().padding(horizontal=12.dp), verticalArrangement=Arrangement.spacedBy(12.dp), contentPadding=PaddingValues(bottom=12.dp)){
                            if(resultados.isNotEmpty()){
                                val pmin=resultados.minOf{it.precio}
                                val pminIg=resultados.filter{it.precioEfectivo!=null}.minOfOrNull{it.precioEfectivo!!} ?: pmin
                                val mejor=resultados.minByOrNull{it.precio}!!
                                val mejorIg=resultados.filter{it.precioEfectivo!=null}.minByOrNull{it.precioEfectivo!!}
                                item{
                                    Card(Modifier.fillMaxWidth(), shape=RoundedCornerShape(16.dp), colors=CardDefaults.cardColors(containerColor=Color(0xFFE8F5E9))){
                                        Column(Modifier.padding(14.dp), verticalArrangement=Arrangement.spacedBy(4.dp)){
                                            Text("⭐ Más barato (1 unid.): ${mejor.precioStr} en ${mejor.supermercado}", fontWeight=FontWeight.Bold, color=Color(0xFF1B5E20), fontSize=13.sp)
                                            Text(mejor.nombre.take(52), fontSize=11.sp, color=Color.Gray, maxLines=1, overflow=TextOverflow.Ellipsis)
                                            if(mejorIg!=null && mejorIg.precioEfectivo!! < pmin -0.01){
                                                Text("🎁 Con promo: ${formatear(mejorIg.precioEfectivo!!)} c/u en ${mejorIg.supermercado} • ${mejorIg.promoEfectiva?.split("→")?.get(0)?.trim()?.take(30) ?: ""}", fontSize=11.sp, color=Color(0xFF0D47A1))
                                            }
                                        }
                                    }
                                }
                                val porSuper=resultados.groupBy{it.supermercado}
                                for(superN in listOf("MasOnline","VEA","Carrefour")){
                                    val items=porSuper[superN] ?: continue
                                    item{ SuperHeader(superN, items.size) }
                                    items(items){ prod->
                                        val esMin = kotlin.math.abs(prod.precio - pmin) < 0.01
                                        val esMinIg = prod.precioEfectivo!=null && kotlin.math.abs(prod.precioEfectivo!! - pminIg) < 0.01
                                        ProductoCard(prod, esMin, esMinIg)
                                    }
                                }
                            }
                        }
                    }
                }
            } else {
                PromosScreen()
            }
        }
    }
}

@Composable
fun SuperHeader(nombre:String, count:Int){
    val col = when(nombre){ "MasOnline"->MasOnlineCol; "VEA"->VEACol; else->CarrefourCol }
    Row(verticalAlignment=Alignment.CenterVertically, modifier=Modifier.padding(top=8.dp)){
        Box(Modifier.width(4.dp).height(18.dp).clip(RoundedCornerShape(4.dp)).background(col)){}
        Spacer(Modifier.width(8.dp))
        Text("🛒 $nombre", fontWeight=FontWeight.ExtraBold, color=col, fontSize=14.sp)
        Text("($count productos)", color=Color.Gray, fontSize=11.sp, modifier=Modifier.padding(start=6.dp))
    }
}

@Composable
fun ProductoCard(p:Producto, esMin:Boolean, esMinIg:Boolean){
    val ctx=LocalContext.current
    val col = when(p.supermercado){ "MasOnline"->MasOnlineCol; "VEA"->VEACol; else->CarrefourCol }
    Card(Modifier.fillMaxWidth(), shape=RoundedCornerShape(16.dp), colors=CardDefaults.cardColors(Color.White), elevation=CardDefaults.cardElevation(1.dp)){
        Row(Modifier.padding(10.dp), verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(10.dp)){
            Box(Modifier.size(74.dp).clip(RoundedCornerShape(12.dp)).background(Color(0xFFF9FAFB)), contentAlignment=Alignment.Center){
                if(p.imagen.isNotBlank()) AsyncImage(model=p.imagen, contentDescription=null, modifier=Modifier.fillMaxSize(), contentScale=ContentScale.Fit)
                else Text("🛍️", fontSize=28.sp)
            }
            Column(Modifier.weight(1f), verticalArrangement=Arrangement.spacedBy(2.dp)){
                Text(p.nombre.take(48), fontWeight=FontWeight.SemiBold, fontSize=13.sp, maxLines=1, overflow=TextOverflow.Ellipsis)
                Row(verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(6.dp)){
                    Text("💲 ${p.precioStr}", fontWeight=FontWeight.ExtraBold, fontSize=16.sp, color=if(esMin) Color(0xFF2E7D32) else Color.Black)
                    if(esMin) Text("MÁS BARATO x1", fontSize=9.sp, color=Color.White, modifier=Modifier.clip(RoundedCornerShape(6.dp)).background(Color(0xFF2E7D32)).padding(horizontal=6.dp, vertical=2.dp))
                    if(p.precioOriginal!=null && p.precioOriginal>p.precio*1.01 && p.precioOriginal/p.precio<=3) Text("antes ${formatear(p.precioOriginal)}", fontSize=10.sp, color=Color.Gray)
                }
                p.promos.take(2).forEach{ promo->
                    val isBest = esMinIg && promo==p.promoEfectiva
                    Text("• $promo${if(isBest) " ◄ MÁS BARATO c/u" else ""}", fontSize=11.sp, color=if(isBest) Color(0xFF1B5E20) else Color(0xFF6D4C00), modifier=if(isBest) Modifier.clip(RoundedCornerShape(8.dp)).background(Color(0xFFE8F5E9)).padding(horizontal=6.dp, vertical=2.dp) else Modifier)
                }
                Text("🔗 Ver en tienda", color=col, fontSize=11.sp, fontWeight=FontWeight.SemiBold, modifier=Modifier.clickable{
                    try{ ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(p.url))) }catch{}
                })
            }
        }
    }
}

@Composable
fun PromosScreen(){
    val promos = mapOf(
        "MasOnline" to listOf("Cencopay 25% + 3 CSI — Todos los días (Tope \$8.000)","BNA 30% MODO — Miércoles (Tope \$10k)","Naranja X 3 cuotas — >\$40k"),
        "VEA" to listOf("Cencopay 25% + 3 CSI — Todos los días","Galicia 20% — Jueves (Tope \$7k)","BBVA 15% + 3 CSI — Viernes","BNA 30% MODO — Miércoles"),
        "Carrefour" to listOf("Mi Carrefour 15% + 3 CSI — Todos los días","BNA 30% MODO — Miércoles","Macro 20% MODO — Miércoles","Santander 25% Visa MODO — Viernes","BBVA 25% — Sábado cuenta sueldo")
    )
    LazyColumn(Modifier.fillMaxSize().padding(12.dp), verticalArrangement=Arrangement.spacedBy(14.dp)){
        item{ Text("Promos bancarias vigentes", fontWeight=FontWeight.Bold, fontSize=14.sp, color=Color.Gray) }
        promos.forEach{ (superN, items)->
            val col = when(superN){ "MasOnline"->MasOnlineCol; "VEA"->VEACol; else->CarrefourCol }
            item{
                Card(Modifier.fillMaxWidth(), shape=RoundedCornerShape(16.dp), colors=CardDefaults.cardColors(Color.White), elevation=CardDefaults.cardElevation(1.dp)){
                    Column(Modifier.padding(14.dp), verticalArrangement=Arrangement.spacedBy(8.dp)){
                        Row(verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(8.dp)){
                            Box(Modifier.width(4.dp).height(22.dp).clip(RoundedCornerShape(4.dp)).background(col)){}
                            Text("🏦 $superN", fontWeight=FontWeight.ExtraBold, color=col, fontSize=15.sp)
                            Text("${items.size} promos", color=Color.Gray, fontSize=11.sp)
                        }
                        Divider(color=Color(0xFFF3F4F6))
                        items.forEach{ txt->
                            Row(verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(8.dp)){
                                Text("💳", fontSize=14.sp)
                                Text(txt, fontSize=12.sp, color=Color(0xFF1F2937))
                            }
                        }
                    }
                }
            }
        }
        item{ Text("💡 Tip: Los descuentos de pago aparecen también en cada producto cuando aplican.", color=Color.Gray, fontSize=11.sp, textAlign=androidx.compose.ui.text.style.TextAlignment.Center, modifier=Modifier.fillMaxWidth().padding(top=8.dp)) }
    }
}

fun formatear(v:Double):String{
    val nf=NumberFormat.getCurrencyInstance(Locale("es","AR"))
    return nf.format(v).replace("ARS","\$").trim()
}

// ── Lógica igual a core.py pero en Kotlin ──
val client=OkHttpClient()

fun normalizar(s:String):String{
    var t=s.lowercase()
    t=java.text.Normalizer.normalize(t, java.text.Normalizer.Form.NFD).replace(Regex("\\p{Mn}"),"")
    t=t.replace(Regex("(\\d),(\\d)"),"$1.$2")
    t=t.replace(Regex("(\\d\\.?\\d*)\\s*(l|lt|lts|ml|cc|kg|k|g|gr|grs)\\b"),"$1$2")
    t=t.replace(Regex("\\s+")," ").trim()
    return t
}
fun terminosDe(q:String)=normalizar(q).split(" ").filter{it.length>=2}
fun precioValido(pf:Double?, po:Double?):Boolean{
    if(pf==null||pf<500) return false
    if(po!=null&&po>0&&po/pf>3.0) return false
    return true
}
suspend fun fetchJson(url:String): JSONArray{
    return withContext(Dispatchers.IO){
        try{
            val req=Request.Builder().url(url).header("User-Agent","Mozilla/5.0").header("Accept","application/json").build()
            val res=client.newCall(req).execute()
            if(!res.isSuccessful) return@withContext JSONArray()
            val body=res.body?.string() ?: return@withContext JSONArray()
            JSONArray(body)
        }catch(e:Exception){ JSONArray() }
    }
}
suspend fun buscarEnSuper(superN:String, tpl:String, query:String, terminos:List<String>):List<Producto>{
    val url=tpl.replace("{q}", URLEncoder.encode(query,"UTF-8"))
    val arr=fetchJson(url)
    val res=mutableListOf<Producto>()
    for(i in 0 until arr.length()){
        try{
            val prod=arr.getJSONObject(i)
            val nombre=(prod.optString("productName")?:"").trim()
            if(nombre.isEmpty()||!terminos.all{ normalizar(nombre).contains(it)} ) continue
            val primeras=normalizar(nombre).split(" ").take(6).joinToString(" ")
            if(terminos.none{primeras.contains(it)}) continue
            if(listOf("polvo","chocolatada","crema","saborizad","condensad").any{ normalizar(nombre).contains(it) && !terminos.joinToString(" ").contains(it)}) continue
            if(!terminos.joinToString(" ").contains("dulce") && (normalizar(nombre).contains("dulce")||normalizar(nombre).contains("d.leche"))) continue
            if(nombre.contains(" + ") && !query.contains(" + ")) continue
            var link=prod.optString("link","")
            if(link.startsWith("/")) link=tpl.split("/api")[0]+link
            var imagen=""
            try{ imagen=prod.getJSONArray("items").getJSONObject(0).getJSONArray("images").getJSONObject(0).optString("imageUrl",""); if(imagen.startsWith("//")) imagen="https:"+imagen }catch{}
            var mejor:Triple<Double,Double?,JSONObject>?=null
            val items=prod.optJSONArray("items")?:continue
            for(j in 0 until items.length()){
                val sellers=items.getJSONObject(j).optJSONArray("sellers")?:continue
                for(k in 0 until sellers.length()){
                    val of=sellers.getJSONObject(k).optJSONObject("commertialOffer")?:sellers.getJSONObject(k).optJSONObject("commercialOffer")?:continue
                    val pf=of.optDouble("Price",Double.NaN); if(pf.isNaN()) continue
                    var po=of.optDouble("ListPrice",Double.NaN); if(po.isNaN()) po=pf
                    if(po/pf>3.0) po=pf
                    if(!precioValido(pf,po)) continue
                    val avail=of.optInt("AvailableQuantity",1)
                    if(avail<=0) continue
                    if(mejor==null||pf<mejor.first) mejor=Triple(pf,po,of)
                }
            }
            if(mejor==null) continue
            val (pf,po,of)=mejor
            // Promos simplificadas: Price vs ListPrice + Teasers nombre
            val promos=mutableListOf<String>()
            val teasers=of.optJSONArray("PromotionTeasers")
            if(teasers!=null) for(t in 0 until teasers.length()){
                val obj=teasers.optJSONObject(t)?:continue
                val name=obj.optString("Name","").trim()
                if(name.length in 3..70) promos.add("🎁 ${limpiarPromo(name)}")
            }
            if(promos.isEmpty() && po!=null && po>pf && po/pf<=3){
                val pct=((1-pf/po)*100).toInt()
                if(pct in 1..70) promos.add("🏷️ ${pct}% OFF")
            }
            // Precio efectivo
            var pe:Double?=null; var peStr:String?=null
            for(promo in promos){
                val m=Regex("""2do\s+al\s+(\d+)\s*%""").find(promo.lowercase())
                if(m!=null){ val pct=m.groupValues[1].toInt(); val tot=pf+pf*(1-pct/100.0); val eff=tot/2; if(pe==null||eff<pe!!){ pe=eff; peStr=promo } }
                val m2=Regex("""(\d+)\s*x\s*(\d+)""").find(promo.lowercase())
                if(m2!=null){ val l=m2.groupValues[1].toInt(); val pg=m2.groupValues[2].toInt(); if(l in 2..6 && pg<l){ val eff=pf*pg/l; if(pe==null||eff<pe!!){pe=eff; peStr=promo} } }
            }
            val peFmt=pe?.let{formatear(it)}
            val promoEff=peStr?.let{"$it → $peFmt c/u llevando ${if(it.contains("3x2"))"3" else "2"}"}
            val promosFinal=if(promoEff!=null) listOf(promoEff) else promos.take(2)
            res.add(Producto(superN,nombre,pf,po,formatear(pf),promosFinal,pe,promoEff,imagen,link))
            if(res.size>=8) break
        }catch{}
    }
    return res.sortedBy{it.precio}
}
fun limpiarPromo(s:String):String{
    var t=s.trim().replace(Regex("^PROMO[\\s\\-–]*",RegexOption.IGNORE_CASE),"")
    t=t.split(Regex("""\s*[-–]\s*Reg[\s\-].*""",RegexOption.IGNORE_CASE))[0].trim()
    t=t.replace(Regex("\\s+")," ").trim()
    return if(t.isNotEmpty()) t[0].uppercase()+t.drop(1) else t
}
suspend fun buscarEnTodos(query:String):List<Producto>{
    val terminos=terminosDe(query)
    if(terminos.isEmpty()) return emptyList()
    val jobs=listOf(
        async{ buscarEnSuper("MasOnline", SUPERS["MasOnline"]!!, query, terminos) },
        async{ buscarEnSuper("VEA", SUPERS["VEA"]!!, query, terminos) },
        async{ buscarEnSuper("Carrefour", SUPERS["Carrefour"]!!, query, terminos) }
    )
    return jobs.awaitAll().flatten().sortedBy{it.precio}
}
