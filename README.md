# text2graph-chile

Extracción de entidades y construcción de grafos de conocimiento a partir de literatura chilena de memoria y dictadura.

## Descripción

Este proyecto procesa un corpus de doce obras literarias chilenas vinculadas a la dictadura militar (1973–1990), extrayendo entidades (personas, lugares, actos de violencia) mediante un modelo de lenguaje y estructurándolas como un grafo de conocimiento en formato RDF.

El resultado es una visualización interactiva que mapea la violencia represiva tal como aparece en la literatura: agentes del Estado, víctimas, centros de detención, y formas de violencia, conectados entre sí y con los textos que los mencionan.

## Corpus

| Obra | Autora/Autor |
|------|-------------|
| A Media Asta | Carmen Berenguer |
| Bandera de Chile | Elvira Hernández |
| Bobby Sands Desfallece | Carmen Berenguer |
| La casa de los espíritus | Isabel Allende |
| La dimensión desconocida | Nona Fernández |
| Nocturno de Chile | Roberto Bolaño |
| Purgatorio | Raúl Zurita |
| Anteparaíso | Raúl Zurita |
| La ciudad está triste | Ramón Díaz Eterovic |
| Estrella distante | Roberto Bolaño |
| Loco afán: crónicas de sidario | Pedro Lemebel |
| Tengo miedo torero | Pedro Lemebel |

## Flujo del proyecto
```
Textos literarios (.txt) → Extracción de entidades (GPT-4o-mini) → Filtrado por palabras clave → Triples RDF (.ttl) → Grafo interactivo (.html)
```

## Estructura del repositorio
```
text2graph-chile/
├─ data/
│  ├─ input/          ← textos literarios (no incluidos, ver nota)
│  └─ reference/      ← listas de referencia histórica y palabras clave
├─ output/            ← resultados: JSON, TTL, HTML del grafo
├─ ontologia/         ← ontología OWL del dominio
├─ src/
│  ├─ PROYECTO_FINAL_TEXT_2_GRAPH.py   ← extracción y generación de triples
│  └─ GrafoFinal.py                    ← construcción y visualización del grafo
├─ .env.example
├─ requirements.txt
└─ README.md
```

## Requisitos

- Python 3.9+
- Docker no requerido
- API key de OpenAI

## Instalación
```bash
git clone https://github.com/tomasberistain/text2graph-chile.git
cd text2graph-chile
pip install -r requirements.txt
```

Crear un archivo `.env` en la raíz del proyecto basándose en `.env.example`:
```
OPENAI_API_KEY=tu_api_key
```

## Uso

**1. Extracción de entidades y generación de triples RDF:**

Colocar los archivos `.txt` del corpus en `data/input/` y ejecutar:
```bash
python src/PROYECTO_FINAL_TEXT_2_GRAPH.py
```

Genera `output/RESULTADOS_FINALES_MEMORIA_CHILE.json` y `output/grafo_memoria_chile.ttl`.

**2. Visualización del grafo:**
```bash
python src/GrafoFinal.py
```

Genera `output/memoria_chile_grafo_CATEGORIAS_ACTUALIZADAS.html`, que puede abrirse directamente en el navegador.

## Archivos de referencia

- `data/reference/referencia_dictadura_chile.json` — lista curada de personas, organismos y lugares históricos de la dictadura chilena, usada para validar y clasificar las entidades extraídas.
- `data/reference/palabras_clave_memoria_chile.json` — vocabulario temático organizado por categorías (tortura, desaparición, represión, etc.) para el filtrado de entidades.

## Nota sobre los textos

Los textos del corpus no se incluyen en este repositorio por razones de derechos de autor.

## Tecnologías

- [OpenAI API](https://platform.openai.com/) — extracción de entidades con GPT-4o-mini
- [rdflib](https://rdflib.readthedocs.io/) — construcción y serialización del grafo RDF
- [pyvis](https://pyvis.readthedocs.io/) — visualización interactiva del grafo

## Hallazgos


**Densidad por texto**
*La dimensión desconocida* de Nona Fernández es el texto con mayor densidad del corpus: 54 instancias de violencia, 41 lugares represivos detectados y 3 lugares oficiales. Es seguida por *La casa de los espíritus* de Isabel Allende con 24 instancias de violencia y 14 agentes identificados. En el extremo opuesto, los textos poéticos de Zurita (*Purgatorio*, *Anteparaíso*) y *Bobby Sands desfallece* de Berenguer registran muy poca o ninguna violencia explícita — la represión aparece de forma oblicua o simbólica.

**"El capitán"**
La figura de "el capitán" aparece en 9 de los 12 textos del corpus — en Berenguer, Allende, Fernández, Bolaño, Zurita (dos veces), Díaz Eterovic, Lemebel (dos veces). El grafo no puede resolver si se trata del mismo hombre, pero su recurrencia a lo largo de autoras y géneros tan distintos sugiere que opera como arquetipo literario del agente represor anónimo.

**Lugares**
El Estadio Nacional aparece en 3 textos (*Bandera de Chile*, *La dimensión desconocida*, *Tengo miedo torero*), la Escuela Militar en 4, y la Vicaría de la Solidaridad en 2. Los textos narrativos concentran la mayoría de los lugares oficiales; la poesía tiende a lugares genéricos o simbólicos (cárceles, cuarteles sin nombre).

**Formas de violencia**
La desaparición es la forma de violencia más distribuida a lo largo del corpus — aparece en casi todos los textos narrativos. La tortura física (golpes, electroshock, sangre) se concentra especialmente en Fernández y Allende. *A media asta* de Berenguer incluye un simulacro de fusilamiento como única instancia de violencia estructurada.

**Lo que el grafo no captura**
Los textos de Zurita son los más resistentes al método: *Purgatorio* y *Anteparaíso* registran cero lugares oficiales y mínima violencia explícita, pero son centrales en la literatura de memoria chilena. Esto sugiere un límite del enfoque basado en extracción de entidades para textos de alto contenido lírico o fragmentario.