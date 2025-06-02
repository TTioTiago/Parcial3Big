import os
import json
import requests
import boto3
from datetime import datetime

# Configuración de S3
S3_BUCKET = "headlinesbucket"
S3_PREFIX = "headlines/raw"

# URLs de las páginas principales
SOURCES = {
    "eltiempo": "https://www.eltiempo.com/"
}

s3_client = boto3.client("s3")

def download_and_upload(event, context):
    """Descarga las páginas principales y las guarda en S3."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    for name, url in SOURCES.items():
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200:
                filename = f"{S3_PREFIX}/contenido-{name}-{today}.html"
                s3_client.put_object(Bucket=S3_BUCKET, Key=filename, Body=response.text)
                print(f"✅ Guardado: s3://{S3_BUCKET}/{filename}")
            else:
                print(f"❌ Error {response.status_code} al descargar {url}")
        except Exception as e:
            print(f"❌ Excepción al descargar {url}: {e}")

    return {"status": "OK", "message": "Descarga completada"}

# Para pruebas locales
if __name__ == "__main__":
    download_and_upload({}, {})

