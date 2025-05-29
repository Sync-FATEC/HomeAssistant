from tuya_connector import TuyaOpenAPI
import os
import configparser

def get_tuya_devices():
    # Tenta carregar as credenciais do arquivo de configuração
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.ini')
    
    if os.path.exists(config_path):
        config = configparser.ConfigParser()
        config.read(config_path)
        
        if 'TuyaAPI' in config:
            ACCESS_ID = config.get('TuyaAPI', 'access_id', fallback='')
            ACCESS_KEY = config.get('TuyaAPI', 'access_key', fallback='')
            API_ENDPOINT = config.get('TuyaAPI', 'api_endpoint', fallback='https://openapi.tuyaus.com')
            USER_ID = config.get('TuyaAPI', 'user_id', fallback='')
        else:
            # Fallback para valores padrão
            ACCESS_ID = "gdxerg7daagmwqnyyw4n"
            ACCESS_KEY = "d6da79b6577b4d9aa2e33790c71bfc77"
            API_ENDPOINT = "https://openapi.tuyaus.com"
            USER_ID = "az16414220244323I8o9"
    else:
        # Fallback para valores padrão
        ACCESS_ID = "gdxerg7daagmwqnyyw4n"
        ACCESS_KEY = "d6da79b6577b4d9aa2e33790c71bfc77"
        API_ENDPOINT = "https://openapi.tuyaus.com"
        USER_ID = "az16414220244323I8o9"
    
    # Verifica se as credenciais estão configuradas
    if not ACCESS_ID or not ACCESS_KEY:
        return None, []
    
    try:
        openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
        openapi.connect()
        
        # Usa o USER_ID das configurações ou tenta buscar todos os dispositivos
        if USER_ID:
            response = openapi.get(f"/v1.0/users/{USER_ID}/devices", {})
        else:
            # Se não houver USER_ID, tenta obter dispositivos do projeto
            response = openapi.get("/v1.0/devices", {})

        dispositivos = []
        if response and 'result' in response:
            for device in response['result']:
                dispositivos.append({
                    'id': device['id'],
                    'name': device['name'],
                    'category': device['category'],
                })
    except Exception as e:
        print(f"Erro ao conectar à API Tuya: {e}")
        return None, []

    return openapi, dispositivos
