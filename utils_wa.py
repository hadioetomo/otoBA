import requests

WHATSAPP_API_URL = "https://api.watzap.id/v1/send_message"
WHATSAPP_API_KEY = "V3ELWOCBWBWHDEMX"
WHATSAPP_NUMBER_KEY = "4Kpb4E1ohwAcU7XT"

def send_whatsapp_message(phone_number, message):
    payload = {
        "api_key": WHATSAPP_API_KEY,
        "number_key": WHATSAPP_NUMBER_KEY,
        "phone_no": phone_number,
        "message": message
    }
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, timeout=15)
        return response.json()
    except Exception as e:
        return {"status": False, "message": str(e)}
