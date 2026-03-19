# visualizar_grafo_memoria_chile
from rdflib import Graph, Namespace, URIRef
from pyvis.network import Network
import json

TTL_FILE = "output/grafo_memoria_chile.ttl"
JSON_FILE = "output/RESULTADOS_FINALES_MEMORIA_CHILE.json"
OUTPUT_HTML = "output/memoria_chile_grafo_CATEGORIAS_ACTUALIZADAS.html"

CHILE = Namespace("http://text2kg/chile/memoria#")
g = Graph()
g.parse(TTL_FILE, format="turtle")

with open(JSON_FILE, "r", encoding="utf-8") as f:
    datos = json.load(f)

net = Network(height="1000px", width="100%", bgcolor="#111111", font_color="white", directed=True)
net.force_atlas_2based(gravity=-140, central_gravity=0.02, spring_length=320, damping=0.93)

# === CATEGORÍAS ===
categorias = {
    "FUERZAS_DEL_ESTADO": {"label": "FUERZAS DEL ESTADO", "color": "#e67e22", "size": 65, "shape": "box"},
    "DESAPARICIONES": {"label": "DESAPARICIONES", "color": "#e74c3c", "size": 60, "shape": "box"},
    "EJECUCIONES": {"label": "EJECUCIONES", "color": "#c0392b", "size": 58, "shape": "box"},
    "TORTURA": {"label": "TORTURA", "color": "#9b836b", "size": 58, "shape": "box"},
    "DETENCION_ILEGAL": {"label": "DETENCIÓN ILEGAL", "color": "#8e44ad", "size": 55, "shape": "box"},
    "VÍCTIMAS": {"label": "VÍCTIMAS", "color": "#3498db", "size": 62, "shape": "box"},
    "CARCELES": {"label": "CÁRCELES / PRISIONES", "color": "#1abc9c", "size": 55, "shape": "box"},
    "INSTALACIONES_MILITARES": {"label": "INSTALACIONES MILITARES", "color": "#16a085", "size": 55, "shape": "box"}

}

for cat_name, props in categorias.items():
    uri = str(CHILE) + cat_name
    net.add_node(uri, title=props["label"], font={"size": 22, "strokeWidth": 3, "strokeColor": "#ffffff"}, **props)

# CONEXIÓN ENTRE CATEGORÍAS GRANDES
net.add_edge(str(CHILE.DESAPARICIONES), str(CHILE.DETENCION_ILEGAL), label="subtipo de ", color="#e74c3c", width=6,
             arrows="to")

nodos_agregados = set()

# PERSONAS
for s, p, o in g:
    if not isinstance(o, URIRef):
        continue
    local_name = str(o).replace(str(CHILE), "")

    if local_name.startswith(("Persona_", "Persona/")) and str(o) not in nodos_agregados:
        nodos_agregados.add(str(o))
        nombre_raw = local_name.replace("Persona_", "").replace("Persona/", "").replace("_", " ")
        nombre = nombre_raw.title()
        texto_lower = nombre_raw.lower()

        # Detección de VÍCTIMAS (asesinado por, asesinos de, etc.)
        if any(frase in texto_lower for frase in
               ["asesinado por", "asesinos de", "víctima de", "muerto por", "torturado por"]):
            net.add_node(str(o), label=nombre, color="#3498db", size=28, shape="ellipse", title="Víctima identificada")
            net.add_edge(str(o), str(CHILE.VÍCTIMAS), color="#3498db", width=5, arrows="to")

        # Organismos represores
        elif any(org in texto_lower for org in ["dina", "cni", "comando conjunto", "brigada lautaro", "agente"]):
            net.add_node(str(o), label=nombre, color="#e74c3c", size=30, shape="ellipse",
                         title="Agente de organismo represor")
            net.add_edge(str(o), str(CHILE.ORGANISMOS_REPRESORES), color="#2c3e50", width=5, arrows="to")

        # Fuerzas del Estado
        elif any(rango in texto_lower for rango in ["coronel", "general", "comandante", "capitán", "teniente", "mayor",
                                                    "suboficial", "carabinero", "militar", "oficial"]):
            net.add_node(str(o), label=nombre, color="#f39c12", size=28, shape="ellipse", title="Militar o carabinero")
            net.add_edge(str(o), str(CHILE.FUERZAS_DEL_ESTADO), color="#e67e22", width=5, arrows="to")

        # Otras víctimas por default
        else:
            net.add_node(str(o), label=nombre, color="#3498db", size=25, shape="ellipse", title="Víctima / Testigo")
            net.add_edge(str(o), str(CHILE.VÍCTIMAS), color="#3498db", width=4, arrows="to")

    # VIOLENCIA
    elif local_name.startswith(("Violencia_", "Violencia/")) and str(o) not in nodos_agregados:
        nodos_agregados.add(str(o))
        v = local_name.replace("Violencia_", "").replace("Violencia/", "").replace("_", " ").lower()

        # Desapariciones: cualquier mención con "desaparición" (incluyendo "del cuerpo")
        if "desaparición" in v or "desaparecido" in v or "desaparece" in v:
            net.add_node(str(o), label="Desaparición", color="#e74c3c", size=27, shape="hexagon")
            net.add_edge(str(o), str(CHILE.DESAPARICIONES), color="#e74c3c", width=5)

        # Secuestros, Detención Ilegal
        elif "secuestro" in v or "secuestrado" in v:
            net.add_node(str(o), label="Secuestro (Detención ilegal)", color="#8e44ad", size=25, shape="hexagon")
            net.add_edge(str(o), str(CHILE.DETENCION_ILEGAL), color="#8e44ad", width=4)


        elif any(pal in v for pal in ["ejecu", "fusil", "asesina", "asesinado", "ultima"]):
            net.add_node(str(o), label="Ejecución", color="#c0392b", size=27, shape="hexagon")
            net.add_edge(str(o), str(CHILE.EJECUCIONES), color="#c0392b", width=5)


        elif any(pal in v for pal in ["tortura", "electricidad", "parrilla", "submarino"]):
            net.add_node(str(o), label="Tortura", color="#9b59b6", size=27, shape="hexagon")
            net.add_edge(str(o), str(CHILE.TORTURA), color="#9b59b6", width=5)

        elif "deten" in v or "arresto" in v:
            net.add_node(str(o), label="Detención ilegal", color="#8e44ad", size=25, shape="hexagon")
            net.add_edge(str(o), str(CHILE.DETENCION_ILEGAL), color="#8e44ad", width=4)

        else:
            net.add_node(str(o), label=v.title(), color="#9b59b6", size=20, shape="hexagon")

    #LUGARES
    elif local_name.startswith(("Lugar_", "Lugar/")) and str(o) not in nodos_agregados:
        nodos_agregados.add(str(o))
        lugar_raw = local_name.replace("Lugar_", "").replace("Lugar/", "").replace("_", " ").lower()
        lugar_label = lugar_raw.title()

        # CARCELES / CENTROS DE DETENCIÓN
        if any(pal in lugar_raw for pal in [
            "cárcel", "carcel", "prisión", "prision", "penitenciaría", "penitenciaria",
            "centro de detención", "centro de tortura", "campo de concentración",
            "centro clandestino", "recinto penitenciario"
        ]):
            net.add_node(str(o), label=lugar_label, color="#1abc9c", size=30, shape="diamond",
                         title="Cárcel / Centro de detención")
            net.add_edge(str(o), str(CHILE.CARCELES), color="#1abc9c", width=4)

        #INSTALACIONES MILITARES: bases, cuarteles, regimientos, etc
        elif any(pal in lugar_raw for pal in [
            "base militar", "cuartel", "cuarteles", "regimiento", "regimientos",
            "batallón", "batallon", "brigada", "patio de regimiento", "escuela militar"
        ]):
            net.add_node(str(o), label=lugar_label, color="#16a085", size=30, shape="diamond",
                         title="Instalación militar")
            net.add_edge(str(o), str(CHILE.INSTALACIONES_MILITARES), color="#16a085", width=4)


        else:
            net.add_node(str(o), label=lugar_label, color="#2ecc71", size=28, shape="diamond",
                         title="Lugar de represión")

#TEXTOS
for s, p, o in g:
    if isinstance(s, URIRef):
        local_name = str(s).replace(str(CHILE), "")
        if local_name.startswith(("Texto_", "Texto/")) and str(s) not in nodos_agregados:
            nodos_agregados.add(str(s))
            clave = local_name.replace("Texto_", "").replace("Texto/", "")
            titulo = datos.get(clave, {}).get("texto", clave.replace("_", " "))
            net.add_node(str(s), label=titulo, color="#e74c3c", size=40, shape="box", font={"size": 16})

# ARISTAS ORIGINALES
for s, p, o in g:
    if isinstance(s, URIRef) and isinstance(o, URIRef):
        label = ""
        if "AgenteSospechoso" in str(p):
            label = "menciona represor "
        elif "ViolenciaRepresiva" in str(p):
            label = "describe violencia "
        elif "LugarOficial" in str(p):
            label = "lugar oficial "
        elif "LugarRepresivoDetectado" in str(p):
            label = "lugar represivo "
        net.add_edge(str(s), str(o), label=label, color="#95a5a6", width=1.8, font={"size": 11})

# Física
net.set_options('''
{
  "physics": {
    "enabled": true,
    "forceAtlas2Based": {
      "gravitationalConstant": -160,
      "centralGravity": 0.025,
      "springLength": 360,
      "springConstant": 0.11,
      "damping": 0.94
    },
    "maxVelocity": 75,
    "minVelocity": 1.0
  }
}
''')

net.show(OUTPUT_HTML, notebook=False)
print(f"Grafo: {OUTPUT_HTML}")