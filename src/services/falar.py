from google.cloud import texttospeech
import os
from playsound import playsound

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secret.json"

def falar(texto):
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=texto)

    # Configurações de voz (pt-BR e voz feminina WaveNet)
    voice = texttospeech.VoiceSelectionParams(
        language_code="pt-BR",
        name="pt-BR-Wavenet-A"
    )

    # Configurações de áudio
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Geração do áudio
    response = client.synthesize_speech(
        input=input_text,
        voice=voice,
        audio_config=audio_config
    )

    # Salvar e reproduzir
    filename = "resposta.mp3"
    with open(filename, "wb") as out:
        out.write(response.audio_content)

    # Reproduzir com playsound para compatibilidade com Raspberry Pi
    playsound(filename)
    os.remove(filename)
