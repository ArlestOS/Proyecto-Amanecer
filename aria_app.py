import streamlit as st
import os
import re
import base64
import json
import requests
import replicate
import google.generativeai as genai
from google.generativeai.types import Tool
from supabase import create_client
from datetime import datetime
from PIL import Image
import time

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
# ========= SUPABASE =========
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

supabase = create_client(supabase_url, supabase_key)

# 4. DEFINICIÓN DE CARPETA BASE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ========== FUNCIONES UTILIDAD ==========
def cargar_json(ruta, valor_por_defecto):
    if not os.path.exists(ruta): 
        return valor_por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f: 
            return json.load(f)
    except: 
        return valor_por_defecto

def guardar_json(ruta, datos):
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except:
        pass

def get_b64(mood, tipo):
    """Obtiene imagen en base64 según mood y tipo (cerrada/abierta)"""
    nombre_archivo = RUTAS_FOTOS.get(mood, RUTAS_FOTOS["SERIA"]).get(tipo, "Seria cerrada.png")
    ruta = os.path.join(BASE_DIR, "static", nombre_archivo)
    
    if os.path.exists(ruta):
        with open(ruta, "rb") as f: 
            return base64.b64encode(f.read()).decode()
    return ""

def filtrar_modo_publico(texto):
    """Filtra contenido NSFW en modo público"""
    if st.session_state.get("publico", False):
        palabras_censurar = ["horny", "sexy", "nsfw", "privado", "intimidad"]
        for palabra in palabras_censurar:
            texto = re.sub(palabra, "***", texto, flags=re.IGNORECASE)
    return texto

# ========== DEFINICIÓN DE RUTAS DE FOTOS ==========
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

# ========== CARGA DE PROMPTS Y MEMORIA ==========
# ========= MEMORIA SUPABASE =========

def cargar_memoria():
    try:
        response = supabase.table("memoria").select("*").eq("user_id", "fer").execute()

        if response.data:
            return response.data[0]["contenido"]

    except Exception as e:
        print("ERROR MEMORIA:", e)

    return {
        "resumen_relacion": "Comenzando la relación con Aria 2.0.",
        "hechos_clave": []
    }


def guardar_memoria(memoria):
    try:
        supabase.table("memoria").upsert({
            "user_id": "fer",
            "contenido": memoria
        }).execute()

    except Exception as e:
        print("ERROR GUARDANDO:", e)


def extraer_recuerdo(prompt):
    trigger_palabras = [
        "recuerda que",
        "mi ciudad es",
        "vivo en",
        "me gusta",
        "mi color favorito es",
        "mi número favorito es"
    ]

    texto = prompt.lower()

    for trigger in trigger_palabras:
        if trigger in texto:
            return prompt

    return None


memoria_lp = cargar_memoria()
# Cargar system prompt
try:
    with open(os.path.join(BASE_DIR, "system_prompt.txt"), "r", encoding="utf-8") as f:
        base_prompt = f.read()
except:
    base_prompt = "Eres Aria, una asistente IA."

# ========== INICIALIZACIÓN DE SESIÓN ==========

# Función para obtener el system prompt actualizado (hora en tiempo real)
def get_current_system_instruction():
    hora_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    recuerdos = "\n".join(
        [f"- {r}" for r in memoria_lp.get("hechos_clave", [])]
    )

    return (
        base_prompt +
        "\n\n=== MEMORIA DE FER ===\n" +
        recuerdos +
        "\n=======================\n" +
        f"\nFecha y hora actual: {hora_actual}\n" +
        f"\nModo Público: {st.session_state.get('publico', False)}\n" +
        "\nTienes permitido usar búsqueda web para obtener información actualizada cuando sea necesario."
    )

# Configuración del modelo con búsqueda web
tools = [{"google_search_retrieval": {}}]

st.session_state.model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=get_current_system_instruction(),
    tools=tools
)

st.session_state.chat_session = st.session_state.model.start_chat(history=[])

if "historial" not in st.session_state: 
    st.session_state.historial = []
if "mood" not in st.session_state: 
    st.session_state.mood = "SERIA"
if "audio" not in st.session_state: 
    st.session_state.audio = None
if "publico" not in st.session_state: 
    st.session_state.publico = False
if "mood_queue" not in st.session_state: 
    st.session_state.mood_queue = []
if "aria_placeholder" not in st.session_state:
    st.session_state.aria_placeholder = None

# ========== ESTILOS CSS ==========
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
        .aria-panel { 
            border: 2px solid #bf00ff; 
            border-radius: 15px; 
            padding: 15px; 
            background: rgba(26, 11, 46, 0.8); 
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# Cargar CSS externo si existe
try:
    with open(os.path.join(BASE_DIR, "style.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# ========== INTERFAZ PRINCIPAL ==========
# Botón para cambiar modo público/privado
col_top_left, col_top_right = st.columns([1, 2])
with col_top_left:
    modo_texto = "🌍 Público" if st.session_state.publico else "🔒 Privado"
    if st.button(modo_texto, use_container_width=True):
        st.session_state.publico = not st.session_state.publico
        st.rerun()

# Layout principal
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown('<div class="aria-panel">', unsafe_allow_html=True)
    
    # Crear placeholder para la imagen
    aria_placeholder = st.empty()
    st.session_state.aria_placeholder = aria_placeholder
    
    # Mostrar imagen inicial
    mood_actual = "CHIBI" if st.session_state.publico else st.session_state.mood
    img_base64 = get_b64(mood_actual, "cerrada")
    if img_base64:
        aria_placeholder.image(f"data:image/png;base64,{img_base64}", width=250)
    else:
        aria_placeholder.write("📸 Imagen no disponible")
    
    # File uploader
    uploaded_file = st.file_uploader("Subir", label_visibility="collapsed")
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    container = st.container(height=500)
    
    # Mostrar historial
    for msg in st.session_state.historial:
        role = msg["role"]
        text = msg["text"]
        
        # En modo público, filtrar contenido
        if st.session_state.publico:
            text = filtrar_modo_publico(text)
        
        container.chat_message(role).write(text)
    
    prompt = st.chat_input("Escribe algo...")
    imagen_subida = None

if uploaded_file is not None:
    imagen_subida = Image.open(uploaded_file)
# ========== PROCESAMIENTO DE INPUT ==========
if prompt:
    recuerdo = extraer_recuerdo(prompt)

    if recuerdo:
        memoria_lp["hechos_clave"].append(recuerdo)

        guardar_memoria(memoria_lp)
        print(memoria_lp)

        print("MEMORIA GUARDADA:", recuerdo)
    # Agregar mensaje del usuario al historial
    st.session_state.historial.append({"role": "user", "text": prompt})
    
    # 1. DETECCIÓN DE SOLICITUD DE IMAGEN
    if any(keyword in prompt.lower() for keyword in ["generame una imagen", "haz un dibujo", "dame una foto", "muéstrate"]):
        if "muéstrate" in prompt.lower() or "una foto tuya" in prompt.lower():
            respuesta_aria = "[COQUETA] *Me pongo en posición... dame un segundo.*"
            prompt_final = "score_9, score_8_up, (aria:1.2), (long pink hair:1.2), high ponytail, celestial blue eyes, deep black lipstick, gothic clothing, large breasts, voluptuous body, thigh-high stockings, sexy, professional goth makeup, dark room background"
        else:
            prompt_limpio = prompt.replace('generame una imagen de ', '').replace('haz un dibujo de ', '')
            respuesta_aria = f"[ALEGRE] *Claro, aquí tienes tu dibujo de '{prompt_limpio}'... dame un segundo.*"
            prompt_final = f"score_9, score_8_up, {prompt_limpio}, high quality, detailed"
        
        st.session_state.historial.append({"role": "assistant", "text": respuesta_aria})
        
        try:
            output = replicate.run(
                "lucataco/pony-diffusion-v6-xl:a566580f",
                input={
                    "prompt": prompt_final,
                    "negative_prompt": "lowres, bad anatomy, bad hands",
                    "num_outputs": 1
                }
            )
            st.session_state.historial.append({"role": "assistant", "text": f"![Imagen Generada]({output[0]})"})
        except Exception as e:
            st.session_state.historial.append({"role": "assistant", "text": f"❌ Error generando imagen: {e}"})
        
        st.rerun()
    
# 2. PROCESAMIENTO NORMAL DE CHAT
            else:
                # Actualizamos el system prompt con la hora actual y herramientas de búsqueda
                st.session_state.model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=get_current_system_instruction(),
                    tools=[{"google_search_retrieval": {}}]
                )
                
                # Reiniciamos la sesión manteniendo el historial anterior
                st.session_state.chat_session = st.session_state.model.start_chat(
                    history=st.session_state.chat_session.history
                )
                
                response = st.session_state.chat_session.send_message(prompt)
            except:
                resp = str(response.candidates[0].content.parts[0])

        except Exception as e:
            resp = f"❌ Error de conexión: {e}"

        # Agregar respuesta al historial
        st.session_state.historial.append({
            "role": "assistant",
            "text": resp
        })

        # --- DETECCIÓN Y PROCESAMIENTO DE EMOCIONES ---
        emociones = re.findall(r'\[([A-Z]+)\]', resp)
        print(f"DEBUG: Emociones detectadas: {emociones}")

        if emociones:
            st.session_state.mood_queue = emociones
            st.session_state.mood = emociones[0]
        else:
            st.session_state.mood_queue = [st.session_state.mood]

        # Limpieza de texto para audio
        texto_limpio = re.sub(r'\[.*?\]', '', resp)
        texto_limpio = re.sub(r'\*.*?\*', '', texto_limpio)
        texto_limpio = re.sub(r'_.*?_', '', texto_limpio)
        texto_limpio = re.sub(r'[!¡?¿]+', ' ', texto_limpio)
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()

        # --- ELEVENLABS ---
        if texto_limpio and os.environ.get("ELEVENLABS_API_KEY") and os.environ.get("VOICE_ID"):

            payload = {
                "text": texto_limpio,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.40,
                    "similarity_boost": 0.65,
                    "style": 0.4,
                    "use_speaker_boost": True
                }
            }

            headers = {
                "xi-api-key": os.environ.get("ELEVENLABS_API_KEY"),
                "Content-Type": "application/json"
            }

            try:

                r = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{os.environ.get('VOICE_ID')}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )

                if r.status_code == 200:
                    st.session_state.audio = base64.b64encode(r.content).decode()
                    print(f"DEBUG: Audio generado exitosamente: {len(r.content)} bytes")

                else:
                    print(f"DEBUG: Error ElevenLabs: {r.status_code} - {r.text}")

            except Exception as e:
                print(f"DEBUG: Excepción ElevenLabs: {e}")

        # Guardar memoria
        guardar_memoria(memoria_lp)

        st.rerun()

# ========== REPRODUCCIÓN DE AUDIO Y ANIMACIÓN ==========
if st.session_state.get("audio") and st.session_state.aria_placeholder:
    audio_bytes = base64.b64decode(st.session_state.audio)
    
    # Reproducir audio
    st.audio(audio_bytes, format='audio/mp3', autoplay=True)
    
    # Obtener cola de emociones
    moods = st.session_state.get("mood_queue", [st.session_state.mood])
    print(f"DEBUG: Moods para animar: {moods}")
    
    # Calcular duración aproximada del audio (44100 Hz, 16-bit)
    duracion_audio = len(audio_bytes) / (44100 * 2)
    duracion_por_mood = duracion_audio / len(moods)
    
    # Animación sincronizada
    for m in moods:
        st.session_state.mood = m
        pasos = 2
        
        for _ in range(pasos):
            img_abierta = get_b64(m, "abierta")
            if img_abierta:
                st.session_state.aria_placeholder.image(f"data:image/png;base64,{img_abierta}", width=250)
            time.sleep(0.03)
            
            img_cerrada = get_b64(m, "cerrada")
            if img_cerrada:
                st.session_state.aria_placeholder.image(f"data:image/png;base64,{img_cerrada}", width=250)
            time.sleep(0.1)
    
    # Finalizar en cerrada
    img_final = get_b64(st.session_state.mood, "cerrada")
    if img_final:
        st.session_state.aria_placeholder.image(f"data:image/png;base64,{img_final}", width=250)
    
    print(f"DEBUG: Animación completada")
    
    # Limpiar estado de audio
    st.session_state.audio = None
