from tuya_connector import TuyaOpenAPI

def get_tuya_devices():
    ACCESS_ID = "gdxerg7daagmwqnyyw4n"
    ACCESS_KEY = "d6da79b6577b4d9aa2e33790c71bfc77"
    API_ENDPOINT = "https://openapi.tuyaus.com"

    openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
    openapi.connect()

    response = openapi.get("/v1.0/users/az16414220244323I8o9/devices", {})

    dispositivos = []
    if response and 'result' in response:
        for device in response['result']:
            dispositivos.append({
                'id': device['id'],
                'name': device['name'],
                'category': device['category'],
            })

    return openapi, dispositivos
