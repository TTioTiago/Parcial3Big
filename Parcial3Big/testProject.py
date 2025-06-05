import unittest
from unittest.mock import patch, MagicMock
import boto3
from moto import mock_s3
from io import BytesIO
import os
import json
from datetime import datetime

# Importar funciones
from Zappacsv.function import app, extract_data_from_html
from Zappacsv.scrap import download_and_upload

# Valores comunes
BUCKET_NAME = "headlinesbucket"


class TestFunctionApp(unittest.TestCase):

    @mock_s3
    def test_app_success(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET_NAME)

        sample_html = '''
            <article class="c-articulo--textual" data-category="Internacional">
                <a class="c-articulo__titulo__txt" href="/noticia.html">Titular de Prueba</a>
            </article>
        '''

        # Subir archivo simulado
        s3.put_object(Bucket=BUCKET_NAME, Key="test.html", Body=sample_html)

        mock_event = {
            "Records": [
                {
                    "s3": {
                        "object": {"key": "test.html"}
                    }
                }
            ]
        }

        # Ejecutar Lambda
        with patch("Zappacsv.function.s3_client", s3):
            response = app(mock_event, {})

        self.assertEqual(response["status"], "OK")

    def test_extract_data_from_html(self):
        html = '''
            <article class="c-articulo--textual" data-category="Tecnología">
                <a class="c-articulo__titulo__txt" href="/noticia.html">Noticia Tech</a>
            </article>
        '''
        result = extract_data_from_html(html)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "Tecnología")
        self.assertEqual(result[0][1], "Noticia Tech")
        self.assertEqual(result[0][2], "/noticia.html")


class TestScrap(unittest.TestCase):

    @mock_s3
    @patch("Zappacsv.scrap.requests.get")
    def test_download_and_upload(self, mock_get):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET_NAME)

        # Mock de la respuesta HTTP
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Contenido</html>"
        mock_get.return_value = mock_response

        with patch("Zappacsv.scrap.s3_client", s3):
            response = download_and_upload({}, {})

        self.assertEqual(response["status"], "OK")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"headlines/raw/contenido-eltiempo-{today}.html"
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
        keys = [obj["Key"] for obj in objects.get("Contents", [])]
        self.assertIn(key, keys)


if __name__ == "__main__":
    unittest.main()
