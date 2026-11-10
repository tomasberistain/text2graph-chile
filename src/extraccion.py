
# =========================================================
# PROYECTO FINAL TEXT2KG - Literatura chilena y memoria de la dictadura
# CARTOGRAFIANDO LA VIOLENCIA
# =========================================================

import os
import json
import re
import time
from pathlib import Path
from openai import OpenAI
from openai import RateLimitError

RUTA = Path("data/input")

from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ------------------- CARGA DE ARCHIVOS DE REFERENCIA -------------------
# 1. Lista oficial de palabras clave
with open("data/reference/palabras_clave_memoria_chile.json", "r", encoding="utf-8") as f:
    palabras_data = json.load(f)

PALABRAS_CLAVE = []
for categoria in palabras_data["palabras_clave"].values():
    PALABRAS_CLAVE.extend([kw.lower() for kw in categoria])

CATEGORIAS_CLAVE = palabras_data["palabras_clave"]

# 2. Lista de personas y lugares históricos conocidos
with open("data/reference/referencia_dictadura_chile.json", "r", encoding="utf-8") as f:
    referencia = json.load(f)

personas_ref = set(referencia["personas"] + referencia["oposicion_personas"])
lugares_ref = (
    set(referencia["lugares_tortura_detencion"]) |
    set(referencia["lugares_gobierno_dictadura"]) |
    set(referencia["lugares_oposicion"])
)

# ------------------- FUNCIÓN DE CLASIFICACIÓN -------------------
def clasificar_con_palabra_clave(entidad: str):
    entidad_lower = entidad.lower()
    if any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["tortura_violencia"]):
        return "tortura_violencia"
    if any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["desaparicion_detencion"]):
        return "desaparicion_detencion"
    if any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["centros_represion"]):
        return "centros_represion"
    if any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["inteligencia_represiva"]):
        return "inteligencia_represiva"
    if any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["temas_memoria_trauma"]):
        return "temas_memoria_trauma"
    if (any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["cargos_militares"]) or
        any(kw in entidad_lower for kw in CATEGORIAS_CLAVE["asociaciones_probables_chile"])):
        return "militar_policial"
    return None

# ------------------- FILTRO DE PÁRRAFOS -------------------
"""
 def tiene_nombres_propios(parrafo: str) -> bool:
     palabras = parrafo.split()
     contador = 0
     for palabra in palabras:
         if len(palabra) > 2 and palabra[0].isupper() and any(c.isupper() for c in palabra[1:]):
             contador += 1
             if contador >= 2:
                 return True
     return contador >= 2
"""
# ------------------- EXTRACCIÓN CON OPENAI + FILTROS -------------------
def extraer_entidades(texto: str):
    # Filtrar párrafos relevantes
    parrafos = re.split(r'\n\s*\n|\r\n\r\n', texto)
    relevantes = [p.strip() for p in parrafos if len(p.strip()) > 80]
    texto_procesar = "\n\n".join(relevantes[:10]) if relevantes else texto[:2200]

    #PROMPT
    prompt = f"""Eres un experto en literatura chilena de memoria y dictadura.
    Extrae del siguiente fragmento:

    1. TODAS las personas (nombres propios o personajes sin nombre: "el detenido", "la madre", "el oficial")
    2. TODOS los lugares mencionados, incluyendo:
       - Lugares históricos reales (Villa Grimaldi, Londres 38, etc.)
       - Lugares genéricos o simbólicos (casa, sótano, bosque, río, pieza, patio, cuarto oscuro, etc.)
    3. TODAS las descripciones o actos de violencia física, psicológica o sexual (incluso si son frases completas)

    Devuelve SOLO JSON válido con exactamente estas claves:
    {{
      "personas": ["Pedro", "el capitán", "la detenida"...],
      "lugares": ["Villa Grimaldi", "el sótano de la casa", "bosque", "pieza oscura"...],
      "violencia": ["golpes en el estómago", "aplicación de corriente eléctrica", "simulacro de fusilamiento", "desaparición del cuerpo"...]
    }}

    Fragmento:
    \"\"\"{texto_procesar}\"\"\"
    
"""

    for intento in range(5):
        try:
            respuesta = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=400
            )
            contenido = respuesta.choices[0].message.content.strip()
            if contenido.startswith("```json"):
                contenido = contenido[7:]
            if contenido.endswith("```"):
                contenido = contenido[:-3]
            data = json.loads(contenido)

            # === POST-PROCESAMIENTO CON FILTROS ===
            personas = data.get("personas", [])
            lugares = data.get("lugares", [])
            violencia = data.get("violencia", [])

            lugares_en_listas = [l for l in lugares if l in lugares_ref]

            lugares_nuevos_con_kw = []
            categorias_encontradas = {}
            for lugar in lugares:
                if lugar not in lugares_ref:
                    cat = clasificar_con_palabra_clave(lugar)
                    if cat:
                        lugares_nuevos_con_kw.append(lugar)
                        categorias_encontradas[lugar] = cat

            personas_agentes = [p for p in personas
                              if p not in personas_ref and clasificar_con_palabra_clave(p) == "militar_policial"]

            violencia_represiva = []
            for v in violencia:
                cat = clasificar_con_palabra_clave(v)
                if cat:
                    violencia_represiva.append(v)
                    categorias_encontradas[v] = cat  # Agregar categorías para violencia también

            return {
                "personas_todas": personas,
                "lugares_todos": lugares,
                "lugares_en_listas_oficiales": lugares_en_listas,
                "lugares_nuevos_con_palabra_clave": lugares_nuevos_con_kw,
                "categorias_lugares_nuevos": categorias_encontradas,
                "personas_agentes_sospechosos": personas_agentes,
                "violencia_represiva": violencia_represiva
            }

        except RateLimitError:
            time.sleep(30)
        except Exception as e:
            print(f"Error en chunk: {e}")
            if intento == 4:
                return {
                    "personas_todas": [], "lugares_todos": [],
                    "lugares_en_listas_oficiales": [], "lugares_nuevos_con_palabra_clave": [],
                    "categorias_lugares_nuevos": {}, "personas_agentes_sospechosos": [],
                    "violencia_represiva": []
                }
            time.sleep(10)

    return {"personas_todas": [], "lugares_todos": [], "lugares_en_listas_oficiales": [],
            "lugares_nuevos_con_palabra_clave": [], "categorias_lugares_nuevos": {}, "personas_agentes_sospechosos": [],
            "violencia_represiva": []}

# ------------------- PROCESAMIENTO PRINCIPAL -------------------
archivos = sorted(RUTA.glob("*.txt"))
print(f"Encontrados {len(archivos)} archivos .txt\n")

resultados = {}

for archivo in archivos:
    nombre = archivo.stem
    print(f"Procesando → {nombre}")

    texto = archivo.read_text(encoding="utf-8")
    fragmentos = [texto[i:i+2200] for i in range(0, len(texto), 2000)]

    # Acumuladores
    lugares_oficiales = set()
    lugares_nuevos = set()
    categorias_globales = {}
    agentes_sospechosos = set()
    violencia_represiva = set()

    for i, frag in enumerate(fragmentos):
        print(f"   Chunk {i+1}/{len(fragmentos)}", end=" ")
        data = extraer_entidades(frag)
        lugares_oficiales.update(data["lugares_en_listas_oficiales"])
        lugares_nuevos.update(data["lugares_nuevos_con_palabra_clave"])
        agentes_sospechosos.update(data["personas_agentes_sospechosos"])
        violencia_represiva.update(data["violencia_represiva"])
        for key, cat in data["categorias_lugares_nuevos"].items():
            categorias_globales[key] = cat
        print("✓")

        time.sleep(26)

    resultados[nombre] = {
        "texto": nombre.replace("_", " "),
        "lugares_oficiales": sorted(lugares_oficiales),
        "lugares_nuevos_represivos": sorted(lugares_nuevos),
        "categorias_detectadas": categorias_globales,
        "agentes_sospechosos": sorted(agentes_sospechosos),
        "violencia_represiva": sorted(violencia_represiva)
    }

    print(f"Listo el texto {nombre}")
    print(f"   {len(lugares_oficiales)} lugares oficiales")
    print(f"   {len(lugares_nuevos)} lugares nuevos detectados por palabras clave")
    print(f"   {len(agentes_sospechosos)} posibles agentes")
    print(f"   {len(violencia_represiva)} instancias de violencia represiva\n")

# GUARDAR LOS RESULTADOS EN UN JSON
with open("output/RESULTADOS_FINALES_MEMORIA_CHILE.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

# GENERAR LOS TRIPLES
triples = ['@prefix : <http://text2kg/chile/memoria#> .', '']

for nombre, data in resultados.items():
    texto_id = nombre.replace(" ", "_")
    for lugar in data["lugares_oficiales"]:
        l_id = lugar.replace(" ", "_").replace("(", "").replace(")", "")
        triples.append(f":Texto/{texto_id} :mencionaLugarOficial :Lugar/{l_id} .")
    for lugar in data["lugares_nuevos_represivos"]:
        l_id = lugar.replace(" ", "_").replace("(", "").replace(")", "")
        triples.append(f":Texto/{texto_id} :mencionaLugarRepresivoDetectado :Lugar/{l_id} .")
    for persona in data["agentes_sospechosos"]:
        p_id = persona.replace(" ", "_")
        triples.append(f":Texto/{texto_id} :mencionaAgenteSospechoso :Persona/{p_id} .")
    for vio in data["violencia_represiva"]:
        v_id = vio.replace(" ", "_").replace("(", "").replace(")", "")
        triples.append(f":Texto/{texto_id} :mencionaViolenciaRepresiva :Violencia/{v_id} .")

with open("output/grafo_memoria_chile.ttl", "w", encoding="utf-8") as f:
    f.write("\n".join(triples))

