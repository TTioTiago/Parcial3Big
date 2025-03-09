import os
import json
import boto3
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO

# Configuración de S3
S3_BUCKET = "bucket-zappascrap"  # Mismo bucket de los HTML
s3_client = boto3.client("s3")

import re  # Para buscar números en la descripción

from bs4 import BeautifulSoup

def extract_data_from_html(html_content):
    """Extrae la información de los apartaestudios desde el HTML"""
    soup = BeautifulSoup(html_content, "html.parser")

    properties = []
    
    for listing in soup.find_all("a", class_="listing listing-card"):
        # Extraer datos del atributo data-price
        precio = listing.get("data-price", "N/A").replace(",", "")

        # Extraer ubicación
        barrio = listing.get("data-location", "Desconocido")

        # Extraer habitaciones y baños
        num_habitaciones = listing.get("data-rooms", "N/A")
        num_banos = listing.find("p", {"data-test": "bathrooms"})
        num_banos = num_banos["content"] if num_banos else "N/A"

        # Extraer metros cuadrados
        mts2 = listing.find("p", {"data-test": "floor-area"})
        mts2 = mts2["content"].replace(" m²", "") if mts2 else "N/A"

        properties.append([barrio, precio, num_habitaciones, num_banos, mts2])

    return properties



def app(event, context):
    print("✅ Lambda ejecutada correctamente")

    """Lambda que procesa archivos HTML desde S3 y actualiza el CSV del día"""
    if "Records" not in event:
        print("⚠️ El evento no contiene 'Records'. Verifica el trigger de S3.")
        return {"status": "ERROR", "message": "Evento sin 'Records'"}
    
    today = datetime.utcnow().strftime("%Y-%m-%d")
    csv_filename = f"{today}.csv"

    all_properties = []

    for record in event["Records"]:
        file_key = record["s3"]["object"]["key"]

        # Descargar el archivo HTML
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=file_key)
        html_content = response["Body"].read().decode("utf-8")

        # Extraer información
        properties = extract_data_from_html(html_content)

        if not properties:
            print(f"⚠️ No se encontraron propiedades en {file_key}")
            continue
        
        all_properties.extend(properties)

    if not all_properties:
        print("⚠️ No se encontraron propiedades en ningún archivo procesado")
        return {"status": "ERROR", "message": "No se encontraron propiedades"}

    # Intentar descargar el CSV existente de S3
    try:
        csv_obj = s3_client.get_object(Bucket=S3_BUCKET, Key=csv_filename)
        existing_data = pd.read_csv(csv_obj["Body"])
    except s3_client.exceptions.NoSuchKey:
        existing_data = pd.DataFrame(columns=["FechaDescarga", "Barrio", "Valor", "NumHabitaciones", "NumBanos", "mts2"])

    # Convertir la nueva data en un DataFrame y agregarla al existente
    df_new = pd.DataFrame(all_properties, columns=["Barrio", "Valor", "NumHabitaciones", "NumBanos", "mts2"])
    df_new.insert(0, "FechaDescarga", today)

    df_final = pd.concat([existing_data, df_new], ignore_index=True)

    # Guardar CSV en /tmp y subirlo a S3
    csv_buffer = StringIO()
    df_final.to_csv(csv_buffer, index=False)
    s3_client.put_object(Bucket=S3_BUCKET, Key=csv_filename, Body=csv_buffer.getvalue())

    print(f"✅ CSV actualizado en s3://{S3_BUCKET}/{csv_filename}")

    return {"status": "OK", "message": "CSV actualizado correctamente"}
