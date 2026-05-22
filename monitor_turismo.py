import os
import feedparser
import anthropic
from datetime import datetime, timedelta
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

FUENTES_RSS = [
    "https://www.unwto.org/feed",
    "https://skift.com/feed/",
    "https://www.hosteltur.com/rss",
    "https://www.traveldailymedia.com/feed/",
    "https://www.phocuswire.com/rss",
    "https://www.ttnworldwide.com/rss.xml",
]

def recolectar_noticias():
    noticias = []
    for url in FUENTES_RSS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
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
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    noticias_texto = "\n\n".join([
        f"[{n['fuente']}] {n['titulo']}\n{n['resumen']}"
        for n in noticias
    ])

    prompt = f"""Eres un analista de turismo internacional que trabaja para la Subsecretaría de Turismo de Chile.

A continuación tienes las principales noticias de turismo mundial de la última semana:

{noticias_texto}

Elabora un RESUMEN EJECUTIVO SEMANAL con el siguiente formato:

1. TITULARES DE LA SEMANA
(3-5 noticias más relevantes globalmente, cada una con un párrafo breve)

2. TENDENCIAS EMERGENTES
(patrones o temas recurrentes esta semana)

3. RELEVANCIA PARA CHILE
(qué implica esto para el turismo chileno o latinoamericano)

4. PARA TENER EN RADAR
(1-2 temas a seguir la próxima semana)

El tono debe ser profesional, conciso y orientado a la toma de decisiones. Máximo 700 palabras."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def crear_word(resumen):
    doc = Document()

    # Título principal
    titulo = doc.add_heading("MONITOR DE TURISMO MUNDIAL", 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtítulo con fecha
    fecha = datetime.now().strftime("%d de %B de %Y")
    subtitulo = doc.add_heading(f"Resumen Ejecutivo Semanal — {fecha}", 2)
    subtitulo.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("")  # espacio

    # Línea divisoria
    doc.add_paragraph("─" * 60)

    # Fuente
    fuente = doc.add_paragraph()
    fuente.add_run("Elaborado por: ").bold = True
    fuente.add_run("Unidad de Estudios, Subsecretaría de Turismo de Chile")

    fuente2 = doc.add_paragraph()
    fuente2.add_run("Fuentes: ").bold = True
    fuente2.add_run("UNWTO, Skift, Hosteltur, PhocusWire, Travel Daily Media, TTN Worldwide")

    doc.add_paragraph("─" * 60)
    doc.add_paragraph("")

    # Contenido del resumen
    for linea in resumen.split("\n"):
        linea = linea.strip()
        if not linea:
            doc.add_paragraph("")
            continue
        # Detectar secciones numeradas como títulos
        if linea and linea[0].isdigit() and "." in linea[:3]:
            doc.add_heading(linea, level=2)
        else:
            doc.add_paragraph(linea)

    # Pie de página
    doc.add_paragraph("")
    doc.add_paragraph("─" * 60)
    pie = doc.add_paragraph()
    pie.add_run("Documento generado automáticamente. ").italic = True
    pie.add_run(f"Semana del {datetime.now().strftime('%d/%m/%Y')}").italic = True

    nombre = f"Monitor_Turismo_{datetime.now().strftime('%Y_%m_%d')}.docx"
    doc.save(nombre)
    print(f"✅ Archivo Word generado: {nombre}")
    return nombre

if __name__ == "__main__":
    print("🔍 Recolectando noticias...")
    noticias = recolectar_noticias()
    print(f"   → {len(noticias)} noticias encontradas")

    print("🤖 Generando resumen con Claude...")
    resumen = generar_resumen(noticias)

    print("📄 Creando archivo Word...")
    crear_word(resumen)
    
