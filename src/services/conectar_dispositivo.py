import unicodedata
import re
from . import falar

def normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^\w\s]', '', texto)  # remove pontuação
    return texto.strip()

def identificar_acao(texto: str) -> bool | None:
    texto = normalizar(texto)
    comandos_ligar = {
        "ligar", "acender", "ativar", "iniciar", "começar", "acionar",
        "ligue", "acenda", "ative", "inicie", "comece", "aciona", "liga", "ativa", "acende"
    }
    comandos_desligar = {
        "desligar", "apagar", "desativar", "parar", "encerrar", "desacionar",
        "desligue", "apague", "desative", "pare", "encerre", "desaciona", "desliga", "desativa", "apaga"
    }

    if any(p in texto.split() for p in comandos_desligar):
        return False
    elif any(p in texto.split() for p in comandos_ligar):
        return True
    else:
        return None

def conectar_tuya(texto, openapi, devices) -> None:
    texto_limpo = normalizar(texto)
    action = identificar_acao(texto_limpo)

    if action is None:
        falar.falar("Não consegui identificar se você quer ligar ou desligar.")
        return

    dispositivo_alvo = None
    maior_correspondencia = 0

    for device in devices:
        nome = normalizar(device['name'])
        palavras_nome = set(nome.split())
        palavras_texto = set(texto_limpo.split())
        correspondencias = palavras_nome & palavras_texto

        if len(correspondencias) > maior_correspondencia:
            maior_correspondencia = len(correspondencias)
            dispositivo_alvo = device
        elif len(correspondencias) == maior_correspondencia and dispositivo_alvo:
            if len(device['name']) < len(dispositivo_alvo['name']):
                dispositivo_alvo = device

    if not dispositivo_alvo:
        falar.falar("Dispositivo correspondente não encontrado.")
        return

    categoria = dispositivo_alvo.get('category', '')
    if categoria == 'cz':      # tomada
        code = 'switch_1'
    elif categoria == 'dj':    # lâmpada
        code = 'switch_led'
    else:
        falar.falar(f"A categoria do dispositivo {dispositivo_alvo['name']} não é suportada.")
        return

    try:
        commands = [{'code': code, 'value': action}]
        openapi.post(
            f'/v1.0/devices/{dispositivo_alvo["id"]}/commands',
            {'commands': commands}
        )
        acao_texto = "ligado" if action else "desligado"
        falar.falar(f"Dispositivo {dispositivo_alvo['name']} {acao_texto}.")
    except Exception as e:
        falar.falar("Houve um erro ao enviar o comando para o dispositivo.")
