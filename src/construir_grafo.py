"""
Construye el grafo RDF a partir de los resultados de la extracción.

Lee output/resultados_memoria_chile.json (generado por extraccion.py) y escribe
output/grafo_memoria_chile.ttl. No necesita API key ni el corpus, así que puede
correrse directamente con los resultados incluidos en el repositorio:

    python src/construir_grafo.py
"""
import json
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, RDF, RDFS

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS_JSON = RAIZ / "output" / "resultados_memoria_chile.json"
CORPUS_JSON = RAIZ / "data" / "reference" / "corpus.json"
TTL_SALIDA = RAIZ / "output" / "grafo_memoria_chile.ttl"

CHILE = Namespace("http://text2kg/chile/memoria#")

# campo del JSON -> (predicado, clase de la entidad)
RELACIONES = {
    "lugares_oficiales": (CHILE.mencionaLugarOficial, CHILE.Lugar),
    "lugares_nuevos_represivos": (CHILE.mencionaLugarRepresivoDetectado, CHILE.Lugar),
    "agentes_sospechosos": (CHILE.mencionaAgenteSospechoso, CHILE.Persona),
    "violencia_represiva": (CHILE.mencionaViolenciaRepresiva, CHILE.Violencia),
}

PREFIJO_CLASE = {CHILE.Lugar: "Lugar", CHILE.Persona: "Persona", CHILE.Violencia: "Violencia"}


def uri(tipo: str, texto: str):
    """URI estable y válida: espacios a '_' y el resto codificado (acentos, comas, comillas...)."""
    return CHILE[f"{tipo}/{quote(texto.strip().replace(' ', '_'), safe='_')}"]


def construir_grafo(resultados: dict, corpus: Optional[dict] = None) -> Graph:
    corpus = corpus or {}
    g = Graph()
    g.bind("chile", CHILE)
    g.bind("dcterms", DCTERMS)

    for clave, datos in resultados.items():
        texto = uri("Texto", clave)
        meta = corpus.get(clave, {})
        g.add((texto, RDF.type, CHILE.Texto))
        g.add((texto, RDFS.label, Literal(meta.get("titulo", datos.get("texto", clave)), lang="es")))
        if "autor" in meta:
            g.add((texto, DCTERMS.creator, Literal(meta["autor"])))

        for campo, (predicado, clase) in RELACIONES.items():
            for valor in datos.get(campo, []):
                entidad = uri(PREFIJO_CLASE[clase], valor)
                g.add((entidad, RDF.type, clase))
                g.add((entidad, RDFS.label, Literal(valor, lang="es")))
                g.add((texto, predicado, entidad))
    return g


def main():
    resultados = json.loads(RESULTADOS_JSON.read_text(encoding="utf-8"))
    corpus = json.loads(CORPUS_JSON.read_text(encoding="utf-8")) if CORPUS_JSON.exists() else {}
    g = construir_grafo(resultados, corpus)
    g.serialize(TTL_SALIDA, format="turtle", encoding="utf-8")
    print(f"Grafo RDF: {TTL_SALIDA.relative_to(RAIZ)} ({len(g)} triples, {len(resultados)} textos)")


if __name__ == "__main__":
    main()
