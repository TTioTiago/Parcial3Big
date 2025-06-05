import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from datetime import datetime
import pandas as pd

# Importar funciones
from Zappacsv import function1, function2, job_csv, tiempo_job

SAMPLE_HTML = """
<article class="c-articulo--textual" data-category="Tecnología">
  <a class="c-articulo__titulo__txt" href="/noticia123">Titular de Prueba</a>
</article>
"""

def test_extract_data_from_html_function1():
    result = function1.extract_data_from_html(SAMPLE_HTML)
    assert len(result) == 1
    assert result[0][0] == "Tecnología"
    assert result[0][1] == "Titular de Prueba"
    assert result[0][2] == "/noticia123"

def test_extract_data_from_html_job_csv():
    result = job_csv.extract_data_from_html(SAMPLE_HTML)
    assert len(result) == 1
    assert result[0][0] == "Tecnología"

@patch("Zappacsv.function1.s3_client")
def test_app_lambda(mock_s3):
    mock_event = {
        "Records": [{"s3": {"object": {"key": "fakefile.html"}}}]
    }

    mock_s3.get_object.return_value = {"Body": BytesIO(SAMPLE_HTML.encode("utf-8"))}
    result = function1.app(mock_event, {})
    assert result["status"] == "OK"

@patch("Zappacsv.function2.s3_client")
@patch("Zappacsv.function2.requests.get")
def test_download_and_upload(mock_get, mock_s3):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_HTML
    mock_get.return_value = mock_response

    result = function2.download_and_upload({}, {})
    assert result["status"] == "OK"
    mock_s3.put_object.assert_called()

@patch("Zappacsv.job_csv.s3_client")
def test_job_csv_main(mock_s3):
    mock_s3.list_objects_v2.return_value = {
        "Contents": [{"Key": "headlines/raw/contenido-2024-01-01.html"}]
    }
    mock_s3.get_object.return_value = {"Body": BytesIO(SAMPLE_HTML.encode("utf-8"))}
    job_csv.main()
    mock_s3.put_object.assert_called()

@patch("Zappacsv.tiempo_job.s3")
@patch("Zappacsv.tiempo_job.requests.get")
def test_tiempo_job(mock_get, mock_s3):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = SAMPLE_HTML
    mock_get.return_value = mock_response

    tiempo_job.today = datetime.utcnow().strftime("%Y-%m-%d")  # mock fecha
    tiempo_job.sites = {"eltiempo": "http://fake.url"}
    exec(open("Parcial1Big/Zappacsv/tiempo_job.py").read())  # Ejecuta script completo
    mock_s3.put_object.assert_called()
