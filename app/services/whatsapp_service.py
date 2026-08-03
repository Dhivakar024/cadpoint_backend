import os
import requests

def send_whatsapp_notification(phone_number, full_name, reg_id):
    """Send Registration WhatsApp Notification"""
    token = os.getenv('WHATSAPP_TOKEN', '')
    phone_id = os.getenv('WHATSAPP_PHONE_ID', '')
    admin_whatsapp = os.getenv('WHATSAPP_PHONE', '919566679928')

    print(f"[WhatsApp Notification] Sending registration alert for {full_name} ({reg_id}) to Admin WhatsApp: {admin_whatsapp} & Student Phone: {phone_number}")

    if not token or token == 'demo_token':
        return True

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": admin_whatsapp,
        "type": "template",
        "template": {
            "name": "registration_confirmation",
            "language": { "code": "en_US" },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": full_name },
                        { "type": "text", "text": reg_id }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"WhatsApp API Exception: {e}")
        return False


def send_contact_whatsapp_notification(name, phone, subject):
    """Send Contact Us Lead Notification to Admin WhatsApp"""
    admin_whatsapp = os.getenv('WHATSAPP_PHONE', '919566679928')
    print(f"[WhatsApp Contact Alert] New Enquiry Lead from {name} ({phone}) for {subject} routed to {admin_whatsapp}")
    return True
