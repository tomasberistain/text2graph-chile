"""
Visualización interactiva del grafo de memoria.

Lee output/grafo_memoria_chile.ttl (generado por construir_grafo.py) y escribe
output/grafo_memoria_chile.html (y una copia en docs/index.html para GitHub Pages):

    python src/visualizacion.py
"""
from pathlib import Path

from pyvis.network import Network
from rdflib import Graph, Namespace
from rdflib.namespace import DCTERMS, RDF, RDFS

RAIZ = Path(__file__).resolve().parent.parent
TTL_ENTRADA = RAIZ / "output" / "grafo_memoria_chile.ttl"
HTML_SALIDA = RAIZ / "output" / "grafo_memoria_chile.html"
HTML_PAGES = RAIZ / "docs" / "index.html"  # versión publicada en GitHub Pages

CHILE = Namespace("http://text2kg/chile/memoria#")

# === CATEGORÍAS (nodos ancla) ===
CATEGORIAS = {
    "FUERZAS_DEL_ESTADO": ("FUERZAS DEL ESTADO", "#e67e22", 65),
    "ORGANISMOS_REPRESORES": ("ORGANISMOS REPRESORES", "#2c3e50", 60),
    "VICTIMAS": ("VÍCTIMAS", "#3498db", 62),
    "DESAPARICIONES": ("DESAPARICIONES", "#e74c3c", 60),
    "EJECUCIONES": ("EJECUCIONES", "#c0392b", 58),
    "TORTURA": ("TORTURA", "#9b59b6", 58),
    "DETENCION_ILEGAL": ("DETENCIÓN ILEGAL", "#8e44ad", 55),
    "CARCELES": ("CÁRCELES / PRISIONES", "#1abc9c", 55),
    "INSTALACIONES_MILITARES": ("INSTALACIONES MILITARES", "#16a085", 55),
}

# === REGLAS DE CLASIFICACIÓN (por palabras clave sobre la etiqueta) ===
FRASES_VICTIMA = ["asesinado por", "asesinos de", "víctima de", "muerto por", "torturado por"]
ORGANISMOS = ["dina", "cni", "comando conjunto", "brigada lautaro", "agente"]
RANGOS = ["coronel", "general", "comandante", "capitán", "teniente", "mayor",
          "suboficial", "carabinero", "militar", "oficial", "almirante", "sargento"]

VIOLENCIA = [  # (palabras, etiqueta corta, categoría)
    (["desaparición", "desaparecido", "desaparece"], "Desaparición", "DESAPARICIONES"),
    (["secuestro", "secuestrado"], "Secuestro", "DETENCION_ILEGAL"),
    (["ejecu", "fusil", "asesina", "ultima"], "Ejecución", "EJECUCIONES"),
    (["tortura", "electricidad", "eléctric", "parrilla", "submarino"], "Tortura", "TORTURA"),
    (["deten", "arresto"], "Detención ilegal", "DETENCION_ILEGAL"),
]

CARCELES = ["cárcel", "carcel", "prisión", "prision", "penitenciaría", "penitenciaria",
            "centro de detención", "centros de detención", "centro de tortura",
            "campo de concentración", "centro clandestino", "recinto penitenciario",
            "calabozo", "comisaría"]
MILITARES = ["base militar", "base aérea", "cuartel", "regimiento", "batallón", "batallon",
             "brigada", "escuela militar"]

ETIQUETAS_ARISTA = {
    CHILE.mencionaAgenteSospechoso: "menciona represor",
    CHILE.mencionaViolenciaRepresiva: "describe violencia",
    CHILE.mencionaLugarOficial: "lugar oficial",
    CHILE.mencionaLugarRepresivoDetectado: "lugar represivo",
}


def contiene(texto, palabras):
    return any(p in texto for p in palabras)


def categoria_persona(etiqueta):
    t = etiqueta.lower()
    if contiene(t, FRASES_VICTIMA):
        return "VICTIMAS", "#3498db", "Víctima identificada"
    if contiene(t, ORGANISMOS):
        return "ORGANISMOS_REPRESORES", "#e74c3c", "Agente de organismo represor"
    if contiene(t, RANGOS):
        return "FUERZAS_DEL_ESTADO", "#f39c12", "Militar o carabinero"
    return "VICTIMAS", "#3498db", "Víctima / testigo"


def main():
    g = Graph()
    g.parse(TTL_ENTRADA, format="turtle")

    def etiqueta(nodo):
        return str(g.value(nodo, RDFS.label) or nodo)

    net = Network(height="1000px", width="100%", bgcolor="#111111", font_color="white",
                  directed=True, cdn_resources="remote")

    for clave, (label, color, size) in CATEGORIAS.items():
        net.add_node(clave, label=label, title=label, color=color, size=size, shape="box",
                     font={"size": 22, "strokeWidth": 3, "strokeColor": "#ffffff"})
    net.add_edge("DESAPARICIONES", "DETENCION_ILEGAL", label="subtipo de", color="#e74c3c", width=6)

    # TEXTOS
    for texto in g.subjects(RDF.type, CHILE.Texto):
        autor = g.value(texto, DCTERMS.creator)
        net.add_node(str(texto), label=etiqueta(texto), title=f"{etiqueta(texto)} — {autor}" if autor else etiqueta(texto),
                     color="#f1c40f", size=40, shape="box", font={"size": 16, "color": "#111111"})

    # PERSONAS
    for persona in g.subjects(RDF.type, CHILE.Persona):
        nombre = etiqueta(persona)
        cat, color, tipo = categoria_persona(nombre)
        net.add_node(str(persona), label=nombre, title=tipo, color=color, size=28, shape="ellipse")
        net.add_edge(str(persona), cat, color=CATEGORIAS[cat][1], width=4)

    # VIOLENCIA: etiqueta corta en el nodo, frase completa al pasar el cursor
    for acto in g.subjects(RDF.type, CHILE.Violencia):
        frase = etiqueta(acto)
        t = frase.lower()
        for palabras, corta, cat in VIOLENCIA:
            if contiene(t, palabras):
                net.add_node(str(acto), label=corta, title=frase, color=CATEGORIAS[cat][1], size=26, shape="hexagon")
                net.add_edge(str(acto), cat, color=CATEGORIAS[cat][1], width=4)
                break
        else:
            net.add_node(str(acto), label=frase, title=frase, color="#9b59b6", size=20, shape="hexagon")

    # LUGARES
    for lugar in g.subjects(RDF.type, CHILE.Lugar):
        nombre = etiqueta(lugar)
        t = nombre.lower()
        if contiene(t, CARCELES):
            net.add_node(str(lugar), label=nombre, title="Cárcel / centro de detención",
                         color="#1abc9c", size=30, shape="diamond")
            net.add_edge(str(lugar), "CARCELES", color="#1abc9c", width=4)
        elif contiene(t, MILITARES):
            net.add_node(str(lugar), label=nombre, title="Instalación militar",
                         color="#16a085", size=30, shape="diamond")
            net.add_edge(str(lugar), "INSTALACIONES_MILITARES", color="#16a085", width=4)
        else:
            net.add_node(str(lugar), label=nombre, title="Lugar de represión",
                         color="#2ecc71", size=28, shape="diamond")

    # ARISTAS TEXTO -> ENTIDAD
    for predicado, label in ETIQUETAS_ARISTA.items():
        for texto, entidad in g.subject_objects(predicado):
            net.add_edge(str(texto), str(entidad), label=label, color="#95a5a6", width=1.8, font={"size": 11})

    net.set_options("""
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
    """)

    net.write_html(str(HTML_SALIDA), notebook=False)
    HTML_PAGES.parent.mkdir(exist_ok=True)
    HTML_PAGES.write_text(HTML_SALIDA.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Grafo interactivo: {HTML_SALIDA.relative_to(RAIZ)} (copia para GitHub Pages en docs/index.html)")


if __name__ == "__main__":
    main()
