import streamlit as st
import os
import re
import base64
import json
import requests
import replicate
import google.generativeai as genai
if "aria_placeholder" not in st.session_state:
    st.session_state.aria_placeholder = st.empty()
from dotenv import load_dotenv
print(f"DEBUG: GOOGLE_API_KEY detectada: {os.environ.get('GOOGLE_API_KEY')}")

# 1. LIMPIEZA INICIAL
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

# 2. CONFIGURACIÓN ÚNICA
st.set_page_config(layout="wide", page_title="Aria OS")

# 3. CARGA DE VARIABLES Y API KEY
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path)

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Error: La API KEY no está configurada.")
    st.stop()

genai.configure(api_key=api_key)

# 4. CONFIGURACIÓN DE GOOGLE GENAI
genai.configure(api_key=api_key)

# --- INICIALIZACIÓN DEL MODELO Y CHAT ---
# Usando gemini-3.5-flash y SYSTEM_INSTRUCTION
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        system_instruction=os.environ.get("SYSTEM_INSTRUCTION", "Eres Aria.")
    )

if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.model.start_chat(history=[])

# 6. INTERFAZ


replicate_token = os.environ.get("REPLICATE_API_TOKEN")
eleven_key = os.environ.get("ELEVENLABS_API_KEY")
voice_id = os.environ.get("VOICE_ID")


# 4. DEFINICIÓN DE CARPETA BASE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# --- 2. CSS ESTILO CYBERPUNK Y LAYOUT VERTICAL ---
st.markdown("""
    <style>
        /* Contenedor tipo 'Ventana' */
        .cyber-window {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            background: #1a0b2e;
            border: 2px solid #bf00ff;
            border-radius: 15px;
            padding: 20px;
            height: 80vh;
        }
        /* Botón estilo profesional */
        .stButton>button {
            background-color: #5a2d82 !important;
            color: white !important;
            border: 1px solid #bf00ff !important;
            border-radius: 5px !important;
            width: 100% !important;
        }
        /* Ajuste del chat */
        [data-testid="stChatInput"] {
            border: 1px solid #bf00ff !important;
            border-radius: 5px !important;
        }
    </style>
""", unsafe_allow_html=True)
# --- 3. FUNCIONES ---
def cargar_json(ruta, valor_por_defecto):
    if not os.path.exists(ruta): return valor_por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f: return json.load(f)
    except: return valor_por_defecto

def get_b64(mood, tipo):
    # CAMBIO AQUÍ: Ahora la carpeta base es "static" en lugar de "Aria_Fotos"
    # Asegúrate de que BASE_DIR esté definido al principio de tu script como: BASE_DIR = os.path.dirname(__file__)
    nombre_archivo = RUTAS_FOTOS.get(mood, RUTAS_FOTOS["SERIA"]).get(tipo, "Seria cerrada.png")
    ruta = os.path.join(BASE_DIR, "static", nombre_archivo)
    
    if os.path.exists(ruta):
        with open(ruta, "rb") as f: 
            return base64.b64encode(f.read()).decode()
    return ""

MEMORIA_FILE = os.path.join(BASE_DIR, "memoria_largo_plazo.json")
memoria_lp = cargar_json(MEMORIA_FILE, {"resumen_relacion": "Comenzando la relación con Aria 2.0.", "hechos_clave": []})

RUTAS_FOTOS = {
    "SERIA": {"cerrada": "Seria cerrada.png", "abierta": "Seria abierta.png"},
    "ALEGRE": {"cerrada": "Feliz cerrada.png", "abierta": "Feliz abierta.png"},
    "COQUETA": {"cerrada": "Horny cerrada.png", "abierta": "Horny abierta.png"},
    "TRISTE": {"cerrada": "Triste cerrada.png", "abierta": "Triste abierta.png"},
    "ENOJADA": {"cerrada": "Enojada cerrada.png", "abierta": "Enojada abierta.png"},
    "SORPRENDIDA": {"cerrada": "Sorprendida Cerrada.png", "abierta": "Sorprendida abierta.png"},
    "CONFUNDIDA": {"cerrada": "Confundida cerrada.png", "abierta": "Confundida abierta.png"},
    "PENSATIVA": {"cerrada": "Pensativa cerrada.png", "abierta": "Pensativa abierta.png"},
    "BURLONA": {"cerrada": "Burlona cerrada.png", "abierta": "Burlona abierta.png"},
    "CELOSA": {"cerrada": "Celosa cerrada.png", "abierta": "Celosa abierta.png"},
    "CHIBI": {"cerrada": "Chibi cerrada.png", "abierta": "Chibi abierta.png"},
    "ANIMO": {"cerrada": "Animo cerrada.png", "abierta": "Animo abierta.png"},
    "CONEJITA": {"cerrada": "conejita cerrada.png", "abierta": "Conejita abierta.png"},
    "ENAMORADA": {"cerrada": "Enamorada cerrada.png", "abierta": "Enamorada abierta.png"},
    "ENGREIDA": {"cerrada": "Engreida Cerrada.png", "abierta": "Engreida abierta.png"},
    "FRUSTRADA": {"cerrada": "Frutada Cerrada.png", "abierta": "Frustrada Abierta.png"},
    "HACKER": {"cerrada": "Hacker cerrada.png", "abierta": "Hacker abierta.png"},
    "MALVADA": {"cerrada": "Malvada_Cerrada.png", "abierta": "Malvada cerrada.png"},
    "PROFESIONAL": {"cerrada": "Profesional cerrada.png", "abierta": "Profesional abierta.png"},
    "PUCHERO": {"cerrada": "Puchero cerrado.png", "abierta": "Puchero abierto.png"},
    "RISA": {"cerrada": "Risa cerrada.png", "abierta": "Risa abierta.png"},
    "SATISFECHA": {"cerrada": "Satisfecha cerrada.png", "abierta": "Satisfecha abierta.png"},
    "SILLY": {"cerrada": "Silly Cerrada.png", "abierta": "Silly Abierta.png"},
    "TIMIDA": {"cerrada": "Timida cerrada.png", "abierta": "Timida abierta.png"},
    "VIDRIO": {"cerrada": "Vidrio cerrada.png", "abierta": "Vidrio abierta.png"},
    "CURIOSA": {"cerrada": "Curiosa cerrada.png", "abierta": "Curiosa abierta.png"}
}

# 1. Cargamos el texto plano (la personalidad)
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    base_prompt = f.read()

# 2. Le pegamos la memoria al final (esto se hace solo en el .py)
# Aquí unimos el texto del archivo con la variable dinámica de la memoria
SYSTEM_INSTRUCTION = base_prompt + f"\n\nMemoria histórica de largo plazo: {json.dumps(memoria_lp, ensure_ascii=False)}"

# Inicializamos el modelo (usando el modelo que ya teníamos definido)
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-3.5-flash",
        system_instruction=SYSTEM_INSTRUCTION
    )

# Inicializamos el chat usando el modelo ya configurado
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.model.start_chat(history=[])

# Inicialización de estados
if "historial" not in st.session_state: st.session_state.historial = []
if "mood" not in st.session_state: st.session_state.mood = "SERIA"
if "audio" not in st.session_state: st.session_state.audio = None
if "publico" not in st.session_state: st.session_state.publico = False
if "aria_placeholder" not in st.session_state:
    st.session_state.aria_placeholder = None

# --- 5. INTERFAZ EN DISEÑO DE REJILLA (GRID) ---

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# Inicializamos el placeholder para que exista desde el segundo 1
if "aria_placeholder" not in st.session_state:
    st.session_state.aria_placeholder = st.empty()

col1, col2 = st.columns([1, 2]) 

with col1:
    st.markdown('<div class="aria-panel">', unsafe_allow_html=True)    
    
    # IMPORTANTE: Aquí asignamos el contenedor a la variable global de sesión
    st.session_state.aria_placeholder = st.empty() 
    
    # Mostramos la imagen usando la referencia que acabamos de crear
    img_base64 = get_b64(st.session_state.mood, "cerrada")
    st.session_state.aria_placeholder.image(f"data:image/png;base64,{img_base64}", width=250)    
    
    st.file_uploader("Subir", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    container = st.container(height=500)
    for msg in st.session_state.get("historial", []):
        container.chat_message(msg["role"]).write(msg["text"])
    prompt = st.chat_input("Escribe algo...")

# --- 6. PROCESAMIENTO (Colócalo al final de tu archivo) ---

# Primero capturamos el input de la UI (esto ya lo haces en el layout)
# Solo necesitamos que el 'if prompt' sepa qué hacer con él:

if prompt:
    st.session_state.historial.append({"role": "user", "text": prompt})
    
    # 1. DETECCIÓN DE INTENCIÓN DE FOTO
    if any(keyword in prompt.lower() for keyword in ["generame una imagen", "haz un dibujo", "dame una foto", "muéstrate"]):
        if "muéstrate" in prompt.lower() or "una foto tuya" in prompt.lower():
            respuesta_aria = "Aria: *Me pongo en posición... dame un segundo.*"
            prompt_final = "score_9, score_8_up, (aria:1.2), (long pink hair:1.2), high ponytail, celestial blue eyes, deep black lipstick, gothic clothing, large breasts, voluptuous body, thigh-high stockings, sexy, professional goth makeup, dark room background"
        else:
            respuesta_aria = f"Aria: *Claro, aquí tienes tu dibujo de '{prompt.replace('generame una imagen de ', '')}'... dame un segundo.*"
            prompt_final = f"score_9, score_8_up, {prompt.replace('generame una imagen de ', '')}, high quality, detailed"

        st.session_state.historial.append({"role": "assistant", "text": respuesta_aria})
        output = replicate.run("lucataco/pony-diffusion-v6-xl:a566580f", input={"prompt": prompt_final, "negative_prompt": "lowres, bad anatomy, bad hands", "num_outputs": 1})
        st.session_state.historial.append({"role": "assistant", "text": f"![Imagen Generada]({output[0]})"})
        st.rerun()
 
# 2. PROCESAMIENTO DE CHAT (Este es el único ELSE que debe existir)
    else:
        try:
            resp = st.session_state.chat_session.send_message(prompt).text
        except Exception as e:
            resp = f"Error de conexión: {e}"
        
        st.session_state.historial.append({"role": "assistant", "text": resp})
        
        # --- AQUÍ VA EL NUEVO BLOQUE DE EMOCIONES ---
        emociones = re.findall(r'\[([A-Z]+)\]', resp)
        if emociones:
            st.session_state.mood_queue = emociones
            st.session_state.mood = emociones[0] # Mood inicial
        else:
            st.session_state.mood_queue = [st.session_state.mood]
        # ---------------------------------------------
        
        # Limpieza de texto (seguimos eliminando etiquetas para el audio)
        texto_limpio = re.sub(r'\[.*?\]|\*.*?\*', '', resp)
        texto_limpio = re.sub(r'[!¡?¿]+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
        
        # Llamada a ElevenLabs
        payload = {"text": texto_limpio, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.70, "similarity_boost": 0.75, "style": 0.08, "use_speaker_boost": True}}
        headers = {"xi-api-key": os.environ.get("ELEVENLABS_API_KEY"), "Content-Type": "application/json"}
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ.get('VOICE_ID')}", json=payload, headers=headers)
        
        if r.status_code == 200:
            st.session_state.audio = base64.b64encode(r.content).decode()
            st.rerun()
    
# ElevenLabs con configuración de estabilidad
    payload = {
        "text": texto_limpio,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.05,
            "use_speaker_boost": True
        }
    }
    
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ.get('VOICE_ID')}", 
        json=payload,
        headers={
            "xi-api-key": os.environ.get("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json"
        }
    )
    
    if r.status_code == 200:
        st.session_state.audio = base64.b64encode(r.content).decode()
    
    st.rerun()

# --- 5. REPRODUCCIÓN DE AUDIO ---
if st.session_state.get("audio"):
    audio_bytes = base64.b64decode(st.session_state.audio)
    st.audio(audio_bytes, format='audio/mp3', autoplay=True)
    
    # Limpiamos el estado del audio para que no se reproduzca infinitamente
    # Mantenemos la boca abierta mientras se reproduce el audio
    st.session_state.audio = None
    
    # NOTA: Para cerrar la boca, tendrías que usar un pequeño script de 
    # temporizador en JS, pero por ahora esto evitará que el script colapse.

# --- 7. REPRODUCCIÓN Y ANIMACIÓN DINÁMICA ---
if st.session_state.get("audio") and st.session_state.get("aria_placeholder"):
    import time
    
    # Reproducir audio
    st.audio(base64.b64decode(st.session_state.audio), format='audio/mp3', autoplay=True)
    
    # Obtenemos la cola de emociones (o la actual si no hay varias)
    moods = st.session_state.get("mood_queue", [st.session_state.mood])
    
    # Dividimos el tiempo total de la animación entre la cantidad de emociones
    # Para que si dice 3 emociones, cada una dure un poco del audio
    pasos_por_mood = max(1, 6 // len(moods)) 
    
    for m in moods:
        # Actualizamos el mood global para que get_b64 lo tome
        st.session_state.mood = m 
        
        # Animamos un poco con este mood
        for i in range(pasos_por_mood):
            st.session_state.aria_placeholder.image(f"data:image/png;base64,{get_b64(m, 'abierta')}", width=250)
            time.sleep(0.3)
            st.session_state.aria_placeholder.image(f"data:image/png;base64,{get_b64(m, 'cerrada')}", width=250)
            time.sleep(0.3)
    
    # Finalizar en cerrada
    st.session_state.aria_placeholder.image(f"data:image/png;base64,{get_b64(st.session_state.mood, 'cerrada')}", width=250)
    
    st.session_state.audio = None