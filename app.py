import os
import imaplib
import email
from email.header import decode_header
from email.utils import getaddresses
from flask import Flask, request, render_template

EMAIL_ADDRESS = 'mailsabuzon@gmail.com'
EMAIL_PASSWORD = 'meck lnim hmjl iliq'

app = Flask(__name__)

def decodificar_asunto(asunto_raw):
    if not asunto_raw:
        return "Sin asunto"
    decoded, charset = decode_header(asunto_raw)[0]
    if isinstance(decoded, bytes):
        return decoded.decode(charset or "utf-8", errors="ignore")
    return decoded

def obtener_correo_por_destinatario(correo_cliente):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "ALL")
        messages = messages[0].split()
        messages.reverse()

        for email_id in messages:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)

            subject_raw = email_message["Subject"]
            subject = decodificar_asunto(subject_raw)
            from_header = email_message["From"]
            to_header = email_message.get("To", "")
            recipients = [addr.lower() for name, addr in getaddresses([to_header])]

            if correo_cliente.lower() in recipients:
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break
                        elif content_type == "text/plain" and not body:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                else:
                    body = email_message.get_payload(decode=True).decode(errors="ignore")

                return {
                    "from": from_header,
                    "subject": subject,
                    "body": body
                }

        return {
            "from": "Sistema",
            "subject": "No se encontró un correo para ese destinatario",
            "body": "Verifica que el correo haya sido recibido correctamente en la cuenta central."
        }

    except Exception as e:
        return {
            "from": "Error",
            "subject": "No se pudo recuperar el correo",
            "body": str(e)
        }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get_last_email", methods=["POST"])
def get_last_email():
    correo_cliente = request.form["email"]
    email_data = obtener_correo_por_destinatario(correo_cliente)
    return render_template("index.html", email_data=email_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
