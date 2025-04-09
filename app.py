from flask import Flask, request, jsonify
from flask_cors import CORS
from decouple import config
from openai import OpenAI
import logging

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cargar credenciales desde .env
XAI_API_KEY = config('XAI_API_KEY')

# Conectar con OpenAI para xAI API
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

# Contexto de CoST Jalisco entrenado con datos reales
dashboard_context = """
La iniciativa de Transparencia en Infraestructura [Construction Sector Transparency Initiative] o "CoST" por sus siglas en inglés, es la encargada de promover la transparencia y la rendición de cuentas dentro de las diferentes etapas de los proyectos de infraestructura y obra pública.

Actualmente, tiene presencia en 19 países distribuidos en cuatro continentes, donde trabaja directamente con el Gobierno, la sociedad civil y la industria del ramo de la construcción para promover la divulgación, validación e interpretación de datos de proyectos de infraestructura y obra pública.

CoST Jalisco es el capítulo local, único en México, de la Iniciativa Internacional de Transparencia en Infraestructura "CoST", el cual es dirigido por un Grupo Multisectorial con la finalidad de mejorar el valor de las inversiones en infraestructura y obra pública, aumentando la Transparencia y la Rendición de Cuentas.

El Grupo Multisectorial "GMS" está conformado por instituciones de Gobierno, del sector privado, del sector académico y de la sociedad civil. Este grupo, a través de los representantes de cada una de las instituciones que lo integra, es el responsable de guiar el desarrollo, la implementación y supervisión de la iniciativa de CoST en Jalisco.

---

📊 Estadísticas descriptivas:
- Total de proyectos: 682
- Proyectos por sector:
  - Infraestructura: 516
  - Edificación: 164
  - Urbanos: 2
- Principales organizaciones ejecutoras:
  - Ayuntamiento de Guadalajara: 479
  - Gobierno del Estado de Jalisco (SIOP): 174
  - Tlajomulco de Zúñiga: 18
  - Zapopan: 11

💰 Estadísticas del presupuesto:
- Promedio: $24,171,700 MXN
- Mediana: $6,263,982 MXN
- Máximo: $2,663,051,000 MXN
- Presupuesto total por sector:
  - Infraestructura: $15,475,300,000 MXN
  - Edificación: $995,558,100 MXN
  - Urbanos: $14,239,220 MXN
- Presupuesto total por organización:
  - Gobierno de Jalisco (SIOP): $11,806,480,000 MXN
  - Guadalajara: $4,510,330,000 MXN
  - Zapopan: $92,139,920 MXN
  - Tlajomulco: $76,149,770 MXN

📅 Duración de proyectos:
- Duración promedio: 197 días
- Rango: 32 a 709 días

🚨 Valores nulos:
- 'tipo': 3 nulos
- 'fecha_fin': 27 nulos
- 'valor_final': 26 nulos
- 'lat', 'lng', 'location_name': 13 nulos

---

¿Cómo usar el dashboard?
- Filtra proyectos por estado, tipo, organización o nombre específico
- Revisa la nube de palabras generada con las descripciones
- Analiza gráficos de dona sobre presupuesto y costos por sector
- Ajusta fechas de aprobación y finalización para análisis temporal
- Usa el tablero para encontrar prioridades de inversión, comparar organizaciones y evaluar transparencia en infraestructura
"""

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').lower()
    model = data.get('model', 'grok-2-latest')
    previous_context = data.get('previous_message', '')  # Contexto previo

    if not user_message:
        return jsonify({
            'response': "👋 ¡Bienvenido(a) al Asistente CoST Jalisco! Puedo ayudarte con proyectos, estadísticas y más. ¿Qué te gustaría saber?"
        }), 400

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Eres Grok, un asistente experto de CoST Jalisco. Responde de forma clara, ágil y accesible. Apóyate en el siguiente contexto extraído de los datos oficiales del tablero de infraestructura de CoST Jalisco:\n{dashboard_context}"},
                {"role": "user", "content": f"Contexto previo: {previous_context}\nPregunta actual: {user_message}"},
            ],
        )
        bot_response = completion.choices[0].message.content
        logger.info(f"Respuesta de xAI para: {user_message}")
        return jsonify({'response': bot_response})
    except Exception as e:
        logger.error(f"Error con xAI: {e}")
        return jsonify({'response': f"⚠️ Ups, algo salió mal: {e}. ¿Qué más puedo hacer por ti?"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
