import os
import feedparser
import anthropic
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Fuentes RSS de turismo mundial ──────────────────────────────────────
FUENTES_RSS = [
    "https://www.unwto.org/feed",
    "https://wttc.org/feed",
    "https://skift.com/feed/",
    "https://www.hosteltur.com/rss",
    "https://www.traveldailymedia.com/feed/",
    "https://www.phocuswire.com/rss",
    "https://www.ttnworldwide.com/rss.xml",
]

def recolectar_noticias():
    """Recolecta noticias de los últimos 7 días desde los RSS."""
    noticias = []
    hace_7_dias = datetime.now() - timedelta(days=7)

    for url in FUENTES_RSS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:  # máx 10 por fuente
                noticias.append({
                    "titulo": entry.get("title", ""),
                    "resumen": entry.get("summary", "")[:500],
                    "fuente": feed.feed.get("title", url),
                    "link": entry.get("link", ""),
                })
        except Exception as e:
            print(f"Error en {url}: {e}")

    return noticias

def generar_resumen(noticias):
    """Usa Claude para generar el resumen ejecutivo."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    noticias_texto = "\n\n".join([
        f"[{n['fuente']}] {n['titulo']}\n{n['resumen']}"
        for n in noticias
    ])

    prompt = f"""Eres un analista de turismo internacional que trabaja para la Subsecretaría de Turismo de Chile.

A continuación tienes las principales noticias de turismo mundial de la última semana:

{noticias_texto}

Elabora un RESUMEN EJECUTIVO SEMANAL con el siguiente formato:

1. **Titulares de la semana** (3-5 noticias más relevantes globalmente)
2. **Tendencias emergentes** (patrones o temas recurrentes)
3. **Relevancia para Chile** (qué implica esto para el turismo chileno o latinoamericano)
4. **Para tener en radar** (1-2 temas a seguir la próxima semana)

El tono debe ser profesional, conciso y orientado a la toma de decisiones. Máximo 600 palabras."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def enviar_email(resumen):
    """Envía el resumen por correo electrónico."""
    remitente = os.environ["EMAIL_REMITENTE"]
    destinatario = os.environ["EMAIL_DESTINATARIO"]
    password = os.environ["EMAIL_PASSWORD"]

    fecha = datetime.now().strftime("%d/%m/%Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Monitor Turismo Mundial — Semana del {fecha}"
    msg["From"] = remitente
    msg["To"] = destinatario

    cuerpo = MIMEText(resumen, "plain", "utf-8")
    msg.attach(cuerpo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())

    print(f"✅ Resumen enviado a {destinatario}")

if __name__ == "__main__":
    print("🔍 Recolectando noticias...")
    noticias = recolectar_noticias()
    print(f"   → {len(noticias)} noticias encontradas")

    print("🤖 Generando resumen con Claude...")
    resumen = generar_resumen(noticias)

    print("📧 Enviando email...")
    enviar_email(resumen)
