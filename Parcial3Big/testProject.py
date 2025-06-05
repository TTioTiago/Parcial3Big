import unittest
from unittest.mock import patch, MagicMock
import boto3
from moto.s3 import mock_s3
from io import BytesIO, StringIO
from datetime import datetime
import os
import pandas as pd

# Ajuste de imports según la estructura
from Sapcsv.function import app, extract_data_from_html
from ZappaScrap.scrap import download_and_upload
from jobcsv import extract_data_from_html as extract_csv
import tiempojob


BUCKET_NAME = "headlinesbucket"
JOBS_BUCKET = "headlinesjobs"


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

        with patch("Sapcsv.function.s3_client", s3):
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
    @patch("ZappaScrap.scrap.requests.get")
    def test_download_and_upload(self, mock_get):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET_NAME)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>Contenido</html>"
        mock_get.return_value = mock_response

        with patch("ZappaScrap.scrap.s3_client", s3):
            response = download_and_upload({}, {})

        self.assertEqual(response["status"], "OK")
        today = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"headlines/raw/contenido-eltiempo-{today}.html"
        objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
        keys = [obj["Key"] for obj in objects.get("Contents", [])]
        self.assertIn(key, keys)


class TestJobCSV(unittest.TestCase):

    def test_extract_data_from_html_jobCSV(self):
        html = '''
            <article class="c-articulo--textual" data-category="Cultura">
                <a class="c-articulo__titulo__txt" href="/cultura.html">Titular Cultura</a>
            </article>
        '''
        result = extract_csv(html)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "Cultura")
        self.assertEqual(result[0][1], "Titular Cultura")
        self.assertEqual(result[0][2], "/cultura.html")

    @mock_s3
    def test_jobcsv_main_process(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=JOBS_BUCKET)

        html = '''
            <article class="c-articulo--textual" data-category="Cultura">
                <a class="c-articulo__titulo__txt" href="/cultura.html">Titular Cultura</a>
            </article>
        '''
        today = datetime.utcnow().strftime("%Y-%m-%d")
        s3_key = f"headlines/raw/contenido-{today}.html"
        s3.put_object(Bucket=JOBS_BUCKET, Key=s3_key, Body=html)

        with patch("jobcsv.s3_client", s3):
            with patch("builtins.print"):
                tiempojob.main()

            result = s3.list_objects_v2(Bucket=JOBS_BUCKET, Prefix="headlines/final/")
            keys = [obj["Key"] for obj in result.get("Contents", [])]
            self.assertTrue(any("headlines.csv" in key for key in keys))


class TestTiempoJob(unittest.TestCase):

    @mock_s3
    @patch("tiempojob.requests.get")
    def test_tiempo_job_download_and_save(self, mock_get):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=JOBS_BUCKET)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>contenido</html>"
        mock_get.return_value = mock_response

        with patch("tiempojob.s3", s3):
            with patch("builtins.print"):
                tiempojob.main()

            today = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"headlines/raw/contenido-eltiempo-{today}.html"
            result = s3.list_objects_v2(Bucket=JOBS_BUCKET, Prefix="headlines/raw/")
            keys = [obj["Key"] for obj in result.get("Contents", [])]
            self.assertIn(key, keys)


if __name__ == "__main__":
    unittest.main()
