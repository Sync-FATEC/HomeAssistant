import pvporcupine
import pyaudio
import speech_recognition as sr
from services import conectar_dispositivo, perguntar, tuya_api, falar

COMANDOS_DISPOSITIVO = {
        "ligar", "acender", "ativar", "iniciar", "começar", "acionar",
        "ligue", "acenda", "ative", "inicie", "comece", "aciona", "liga", "ativa", "acende", 
        "desligar", "apagar", "desativar", "parar", "encerrar", "desacionar",
        "desligue", "apague", "desative", "pare", "encerre", "desaciona", "desliga", "desativa", "apaga"
    }

def comando_controla_dispositivo(texto: str) -> bool:
    return any(palavra in texto.lower() for palavra in COMANDOS_DISPOSITIVO)

def executar_comando(texto: str, openapi, devices):
    if comando_controla_dispositivo(texto):
        if not devices:
            falar.falar("Nenhum dispositivo encontrado.")
            return
        conectar_dispositivo.conectar_tuya(texto, openapi, devices)
    else:
        resposta = perguntar.perguntar_gemini(texto)
        falar.falar(resposta)

def wake_word_listener(openapi, devices):
    porcupine = pvporcupine.create(
        access_key="fOnTL0b3dkpAXakuPhoncWUi/cehGu7KoXuctpYNuHMwrgShm5WUWg==",
        keywords=["alexa"],
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
    )

    recognizer = sr.Recognizer()
    mic = sr.Microphone()


    try:
        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_unpacked = memoryview(pcm).cast('h')
            keyword_index = porcupine.process(pcm_unpacked)

            if keyword_index >= 0:
                print("Palavra-chave detectada. Ouvindo comando...")

                with mic as source:
                    try:
                        audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
                        texto = recognizer.recognize_google(audio, language="pt-BR").lower()

                        if texto.startswith("alexa"):
                            texto = texto.replace("alexa", "", 1).strip()

                        print(f"Comando reconhecido: {texto}")

                        if texto == "sair":
                            falar.falar("Encerrando assistente. Até logo!")
                            break

                        executar_comando(texto, openapi, devices)

                    except sr.WaitTimeoutError:
                        print("Você não falou nada após a palavra-chave.")
                        falar.falar("Não ouvi nada. Pode tentar novamente.")
                    except sr.UnknownValueError:
                        print("Não entendi o comando.")
                        falar.falar("Desculpe, não entendi.")
                    except sr.RequestError as e:
                        print(f"Erro ao conectar com API de voz: {e}")
                        falar.falar("Erro ao conectar com o serviço de voz.")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

def main():
    openapi, devices = tuya_api.get_tuya_devices()
    wake_word_listener(openapi, devices)

if __name__ == "__main__":
    main()
