from datetime import datetime
from io import StringIO
import boto3
import pandas as pd
from bs4 import BeautifulSoup

# Configuración de S3
S3_BUCKET = "headlinesbucket"
s3_client = boto3.client("s3")


def extract_data_from_html(html_content):
    """Extrae categoría, titular y enlace de artículos de apertura de eltiempo.com"""
    soup = BeautifulSoup(html_content, "html.parser")
    news_data = []

    for article in soup.find_all("article", class_="c-articulo--textual"):
        # Titular
        title_tag = article.find("a", class_="c-articulo__titulo__txt")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        # Enlace
        link = title_tag.get("href", "Sin enlace")

        # Categoría
        category = article.get("data-category", "Sin categoría")

        news_data.append([category, title, link])

    return news_data


def app(event, context):
    """Lambda activada por S3 que extrae titulares desde archivos HTML de eltiempo y guarda CSVs"""
    print("✅ Lambda ejecutada correctamente")

    if "Records" not in event:
        print("⚠️ El evento no contiene 'Records'. Verifica el trigger de S3.")
        return {"status": "ERROR", "message": "Evento sin 'Records'"}

    all_news = []
    today = datetime.utcnow()
    year = today.strftime("%Y")
    month = today.strftime("%m")
    day = today.strftime("%d")

    for record in event["Records"]:
        file_key = record["s3"]["object"]["key"]
        print(f"📄 Procesando archivo: {file_key}")
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        html_content = response["Body"].read()
        news = extract_data_from_html(html_content)

        if not news:
            print(f"⚠️ No se encontraron noticias en {file_key}")
            continue

        all_news.extend(news)

    if not all_news:
        print("❌ No se encontraron noticias en ningún archivo procesado.")
        return {"status": "ERROR", "message": "No se extrajo información válida"}

    # Crear DataFrame
    df = pd.DataFrame(all_news, columns=["Categoria", "Titular", "Enlace"])

    # Ruta final en S3
    output_key = (
        f"headlines/final/periodico=eltiempo/year={year}/month={month}/day={day}/headlines.csv"
    )

    # Guardar en /tmp y subir a S3
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=S3_BUCKET, Key=output_key, Body=csv_buffer.getvalue())

    print(f"✅ CSV creado en s3://{S3_BUCKET}/{output_key}")
    return {"status": "OK", "message": "Noticias extraídas y almacenadas exitosamente"}
