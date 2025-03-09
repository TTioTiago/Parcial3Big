import os
import json
import requests
import boto3
from datetime import datetime

# Configuración de S3
S3_BUCKET = "bucket-zappascrap"
BASE_URL = "https://casas.mitula.com.co/find?operationType=sell&propertyType=mitula_studio_apartment&geoId=mitula-CO-poblacion-0000014156&text=Bogot%C3%A1%2C++%28Cundinamarca%29"

s3_client = boto3.client("s3")

def download_and_upload(event, context):
    """Descarga las primeras 10 páginas y las guarda en S3."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    for page in range(1, 11):
        url = BASE_URL if page == 1 else f"{BASE_URL}&page={page}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

        if response.status_code == 200:
            file_name = f"{today}/pagina-{page}.html"
            s3_client.put_object(Bucket=S3_BUCKET, Key=file_name, Body=response.text)
            print(f"✅ Página {page} guardada en s3://{S3_BUCKET}/{file_name}")
        else:
            print(f"❌ Error al descargar {url}: {response.status_code}")

    return {"status": "OK", "message": "Descarga completada"}

# Si ejecutas localmente para prueba
if __name__ == "__main__":
    download_and_upload({}, {})
