from flask import Flask, request, jsonify
from flask_cors import CORS
from decouple import config
import mysql.connector
from openai import OpenAI
from fuzzywuzzy import fuzz
import logging

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cargar credenciales desde .env
XAI_API_KEY = config('XAI_API_KEY')
DB_CONFIG = {
    "host": config("DB_HOST"),
    "user": config("DB_USER"),
    "password": config("DB_PASSWORD"),
    "database": config("DB_NAME")
}

# Conectar con OpenAI para xAI API
client = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1",
)

# Contexto de CoST Jalisco
cost_description = """
La iniciativa de Transparencia en Infraestructura, conocida como "CoST" (Construction Sector Transparency Initiative), tiene como misión principal fomentar la transparencia, la rendición de cuentas y la eficiencia en todas las etapas de los proyectos de infraestructura y obra pública. Esto incluye desde la planeación y contratación hasta la ejecución y entrega final de las obras. CoST busca garantizar que los recursos públicos se utilicen de manera responsable y que la ciudadanía pueda acceder a información clara y confiable sobre cómo se invierte en infraestructura.

Actualmente, esta iniciativa está presente en 19 países distribuidos en cuatro continentes: América, África, Asia y Europa. En cada uno de estos lugares, CoST colabora estrechamente con gobiernos locales, organizaciones de la sociedad civil y empresas del sector de la construcción para asegurar la divulgación de datos relevantes, la validación de la información proporcionada y la interpretación adecuada de los resultados, todo con el objetivo de mejorar la gestión de los proyectos y fortalecer la confianza pública en las instituciones.
"""

# Conectar a la base de datos MySQL
def conectar_bd():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        logger.info("Conexión a la base de datos establecida con éxito.")
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        return None

# Formatear respuesta de proyecto individual
def format_project_response(proyecto):
    return f"""
📌 *{proyecto['title']}* (Estado: {proyecto['estado']})
📝 Descripción: {proyecto['description'][:150] + '...' if proyecto['description'] else 'No disponible.'}
📍 Ubicación: {proyecto['location_name'] or 'No especificada.'}
💰 Presupuesto: ${proyecto['presupuesto_monto']:,.2f} MXN
🏗️ Sector: {proyecto['sector'] or 'No especificado'}
🏛️ Organización: {proyecto['organization_name'] or 'No disponible'}
📅 Aprobación: {proyecto['fecha_aprobacion'] or 'No disponible'}
✨ ¿Te gustaría saber más sobre este proyecto?
"""

# Función inteligente para obtener datos
def obtener_datos(user_message, previous_context=None):
    user_message = user_message.lower().strip()
    conn = conectar_bd()
    if not conn:
        return "⚠️ Lo siento, hay un problema técnico con la base de datos. Intenta de nuevo más tarde."
    cursor = conn.cursor(dictionary=True)

    # Tokenización y palabras clave
    words = user_message.split()
    keywords = [w for w in words if w not in ["de", "el", "la", "en", "un", "una", "sobre", "qué", "cuál", "cuáles"]]

    # 🔍 Búsqueda específica de un proyecto
    if any(w in words for w in ["proyecto", "obra", "detalle", "información"]) and keywords:
        query = """
        SELECT p.id, p.title, p.description, ps.titulo as estado, 
            sect.titulo as sector, pt.titulo as tipo, 
            pc.montocontrato as presupuesto_monto, pc.fechapublicacion as fecha_aprobacion,
            pf.fechafinalizacion as fecha_fin, pf.costofinalizacion as valor_final,
            l.lat, l.lng, l.description as location_name,
            o.name as organization_name
        FROM project p
        LEFT JOIN projectstatus ps ON p.status = ps.id
        LEFT JOIN projectsector sect ON p.sector = sect.id
        LEFT JOIN projecttype pt ON p.type = pt.id
        LEFT JOIN proyecto_contratacion pc ON p.id = pc.id_project
        LEFT JOIN proyecto_finalizacion pf ON p.id = pf.id_project
        LEFT JOIN project_locations pl ON p.id = pl.id_project
        LEFT JOIN locations l ON pl.id_location = l.id
        LEFT JOIN project_organizations po ON p.id = po.id_project
        LEFT JOIN organization o ON po.id_organization = o.id
        WHERE pc.montocontrato IS NOT NULL
        """
        cursor.execute(query)
        proyectos = cursor.fetchall()

        project_matches = []
        for proyecto in proyectos:
            text_to_search = " ".join([
                proyecto['title'] or '',
                proyecto['description'] or '',
                proyecto['sector'] or '',
                proyecto['tipo'] or '',
                proyecto['location_name'] or '',
                proyecto['organization_name'] or ''
            ]).lower()
            score = max(fuzz.partial_ratio(keyword, text_to_search) for keyword in keywords)
            if score > 75:  # Umbral más alto para mayor precisión
                project_matches.append((proyecto, score))

        if project_matches:
            project_matches.sort(key=lambda x: x[1], reverse=True)
            best_project, _ = project_matches[0]
            conn.close()
            return format_project_response(best_project)
        conn.close()
        return f"🤔 No encontré un proyecto relacionado con '{user_message}'. ¿Podrías darme más detalles o probar con otro nombre?"

    # 🔍 Lista general de proyectos
    if any(w in words for w in ["proyectos", "lista", "infraestructura"]) and not "sector" in user_message:
        query = """
        SELECT p.id, p.title, p.description, ps.titulo as estado, 
            sect.titulo as sector, pt.titulo as tipo, 
            pc.montocontrato as presupuesto_monto, pc.fechapublicacion as fecha_aprobacion,
            pf.fechafinalizacion as fecha_fin, pf.costofinalizacion as valor_final,
            l.lat, l.lng, l.description as location_name,
            o.name as organization_name
        FROM project p
        LEFT JOIN projectstatus ps ON p.status = ps.id
        LEFT JOIN projectsector sect ON p.sector = sect.id
        LEFT JOIN projecttype pt ON p.type = pt.id
        LEFT JOIN proyecto_contratacion pc ON p.id = pc.id_project
        LEFT JOIN proyecto_finalizacion pf ON p.id = pf.id_project
        LEFT JOIN project_locations pl ON p.id = pl.id_project
        LEFT JOIN locations l ON pl.id_location = l.id
        LEFT JOIN project_organizations po ON p.id = po.id_project
        LEFT JOIN organization o ON po.id_organization = o.id
        WHERE pc.montocontrato IS NOT NULL
        ORDER BY p.id
        LIMIT 5
        """
        cursor.execute(query)
        proyectos = cursor.fetchall()
        conn.close()
        if proyectos:
            respuesta = "Aquí tienes algunos proyectos en CoST Jalisco:\n\n" + "\n".join([
                f"📌 *{p['title']}* (Estado: {p['estado']})\n"
                f"📝 Descripción: {p['description'][:100] + '...' if p['description'] else 'No disponible.'}\n"
                f"💰 Presupuesto: ${p['presupuesto_monto']:,.2f} MXN"
                for p in proyectos
            ]) + "\n✨ ¿Te interesa más detalles de alguno o una lista más amplia?"
            return respuesta
        return "📋 No hay proyectos registrados en este momento. ¿Quieres que investigue algo más?"

    # 📊 Sectores más activos
    if "sector" in user_message and any(w in user_message for w in ["más", "activos", "infraestructura"]):
        query = """
        SELECT sect.titulo as sector, COUNT(p.id) as total_proyectos, SUM(pc.montocontrato) as total_presupuesto
        FROM project p
        LEFT JOIN projectsector sect ON p.sector = sect.id
        LEFT JOIN proyecto_contratacion pc ON p.id = pc.id_project
        GROUP BY sect.titulo
        ORDER BY total_proyectos DESC
        LIMIT 3
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        conn.close()
        if resultados:
            sectores = "\n".join([
                f"🔹 *{s['sector']}*: {s['total_proyectos']} proyectos (${s['total_presupuesto']:,.2f} MXN)"
                for s in resultados if s['sector']
            ])
            return f"🏗️ Los sectores con más actividad en CoST Jalisco son:\n{sectores}\n✨ ¿Quieres explorar algún sector en detalle?"
        return "🤔 No hay datos suficientes para identificar sectores activos."

    # 📊 Presupuesto total
    if any(w in user_message for w in ["presupuesto total", "dinero invertido", "cuánto se ha gastado"]):
        query = "SELECT SUM(pc.montocontrato) as total_presupuesto, COUNT(*) as total_proyectos FROM proyecto_contratacion pc"
        cursor.execute(query)
        resultado = cursor.fetchone()
        conn.close()
        presupuesto = resultado["total_presupuesto"] if resultado["total_presupuesto"] else 0
        proyectos = resultado["total_proyectos"]
        return f"💰 El presupuesto total en CoST Jalisco es **${presupuesto:,.2f} MXN** para {proyectos} proyectos. ¿Quieres un desglose por sectores?"

    # 📊 Desglose del presupuesto
    if user_message in ["sí", "si", "sí, por favor", "sí quiero"] and previous_context and any(w in previous_context for w in ["presupuesto total", "dinero invertido"]):
        query = """
        SELECT sect.titulo as sector, SUM(pc.montocontrato) as total_sector, COUNT(p.id) as total_proyectos
        FROM project p
        LEFT JOIN projectsector sect ON p.sector = sect.id
        LEFT JOIN proyecto_contratacion pc ON p.id = pc.id_project
        GROUP BY sect.titulo
        ORDER BY total_sector DESC
        LIMIT 5
        """
        cursor.execute(query)
        resultados = cursor.fetchall()
        conn.close()
        if resultados:
            desglose = "\n".join([
                f"🔹 *{s['sector']}*: ${s['total_sector']:,.2f} MXN ({s['total_proyectos']} proyectos)"
                for s in resultados if s['sector']
            ])
            return f"💰 Desglose del presupuesto:\n{desglose}\n✨ ¿Te interesa más información sobre algún sector?"
        return "🤔 No hay datos suficientes para desglosar el presupuesto."

    # Saludo genérico
    if "hola" in user_message:
        conn.close()
        return "¡Hola! ¿Cómo puedo ayudarte hoy con CoST Jalisco y los proyectos de infraestructura? ¿Tienes alguna pregunta sobre obras o transparencia?"

    conn.close()
    return None

# Ruta del chatbot con contexto
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

    # Respuesta desde la base de datos
    respuesta_bd = obtener_datos(user_message, previous_context)
    if respuesta_bd:
        return jsonify({'response': respuesta_bd})

    # Respuesta desde xAI
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"Eres Grok, un asistente inteligente de CoST Jalisco. Da respuestas claras, concisas y útiles sobre proyectos de infraestructura. Usa un tono amigable y sugiere opciones relevantes. Contexto: {cost_description}"},
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