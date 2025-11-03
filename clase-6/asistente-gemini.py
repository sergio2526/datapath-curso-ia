import os
import queue
import sounddevice as sd
import traceback
from dotenv import load_dotenv

from google.cloud import speech_v2
from google.cloud.speech_v2.types import (
    RecognitionConfig,
    StreamingRecognizeRequest,
    ExplicitDecodingConfig,
)

from google import genai

# Cargar variables de entorno
load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
RECOGNIZER_ID = os.getenv("RECOGNIZER_ID")
LOCATION = os.getenv("LOCATION")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./cuenta-servicio.json"

# Inicializar cliente Gen AI para Vertex AI
genai_client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=LOCATION
)

# Parámetros de audio
RATE = 8000
CHANNELS = 1
CHUNK = int(RATE / 10)
audio_q = queue.Queue()

# Callback del micrófono
def audio_callback(indata, frames, time, status):
    if status:
        print("⚠️", status)
    audio_q.put(bytes(indata))

# Función para consultar Gemini y obtener respuesta en texto
def responder_con_gemini(texto_usuario: str):
    print("🤖 Escribiendo...")
    try:
        response = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reponda de formar breve y concisa, no más de 100 caracteres: " + texto_usuario
        )
        if response and response.text:
            print(f"🧩 Gemini: {response.text}")
        else:
            print("⚠️ Gemini no devolvió respuesta.")
    except Exception as e:
        print("❌ Error al consultar Gemini:", e)

# Transcripción en streaming con Speech-to-Text v2
def stream_transcription():
    client = speech_v2.SpeechClient()
    recognizer = f"projects/{PROJECT_ID}/locations/global/recognizers/{RECOGNIZER_ID}"

    decoding_config = ExplicitDecodingConfig(
        encoding="LINEAR16",
        sample_rate_hertz=RATE,
        audio_channel_count=CHANNELS,
    )

    config = RecognitionConfig(
        explicit_decoding_config=decoding_config,
        language_codes=["es-CO"],
        model="telephony"
    )

    streaming_config = StreamingRecognitionConfig(config=config)

    def request_generator():
        yield StreamingRecognizeRequest(
            recognizer=recognizer,
            streaming_config=streaming_config,
        )
        while True:
            data = audio_q.get()
            if data is None:
                break
            yield StreamingRecognizeRequest(audio=data)

    print("🎧 Habla con XAIOP. ¿ En qué puedo ayudarte ? (tu asistente IA). Di 'salir' para terminar.")

    try:
        with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype="int16",
                            callback=audio_callback):
            responses = client.streaming_recognize(requests=request_generator())
            for response in responses:
                for result in response.results:
                    if result.alternatives:
                        text = result.alternatives[0].transcript.strip()
                        print(f"🗣️ {text}")
                        if result.is_final:
                            print("✅ Usuario:", text)
                            if "salir" in text.lower():
                                print("👋 Fin del asistente por comando de voz. ¡Gracias por usar XAIOP!")
                                return
                            responder_con_gemini(text)
    except KeyboardInterrupt:
        print("\n👋 Finalizado por el usuario.")
    except Exception as e:
        print("❌ Error en streaming:", e)
        traceback.print_exc()

if __name__ == "__main__":
    stream_transcription()
