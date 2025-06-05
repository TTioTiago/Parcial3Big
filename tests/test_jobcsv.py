import pytest
from unittest.mock import patch, MagicMock
from Parcial3Big import jobcsv
import pandas as pd


def test_extract_data_from_html_empty():
    html = "<html></html>"
    result = jobcsv.extract_data_from_html(html)
    assert result == []


def test_extract_data_from_html_valid():
    html = '''
        <html><body>
        <article class="c-articulo--textual" data-category="Noticias">
            <a class="c-articulo__titulo__txt" href="/noticia-1">Titular Uno</a>
        </article>
        </body></html>
    '''
    result = jobcsv.extract_data_from_html(html)
    assert len(result) == 1
    assert result[0][0] == "Noticias"
    assert result[0][1] == "Titular Uno"
    assert result[0][2] == "/noticia-1"


@patch("Parcial3Big.jobcsv.s3_client")
def test_main_success_with_date_in_filename(mock_s3_client):
    # Simula un archivo .html con fecha
    mock_s3_client.list_objects_v2.return_value = {
        "Contents": [{"Key": "headlines/raw/contenido-2024-05-20.html"}]
    }

    html_content = '''
        <article class="c-articulo--textual" data-category="Política">
            <a class="c-articulo__titulo__txt" href="/p1">Noticia política</a>
        </article>
    '''
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=html_content))
    }

    mock_s3_client.put_object.return_value = {}

    # Ejecuta main y asegura que put_object fue llamado
    jobcsv.main()

    mock_s3_client.put_object.assert_called_once()
    args, kwargs = mock_s3_client.put_object.call_args
    assert kwargs["Bucket"] == jobcsv.S3_BUCKET
    assert "year=2024/month=05/day=20" in kwargs["Key"]
    df = pd.read_csv(StringIO(kwargs["Body"]))
    assert df.shape == (1, 3)
    assert df.iloc[0]["Titular"] == "Noticia política"


@patch("Parcial3Big.jobcsv.s3_client")
def test_main_skips_non_html_files(mock_s3_client):
    mock_s3_client.list_objects_v2.return_value = {
        "Contents": [{"Key": "headlines/raw/informe.txt"}]
    }
    jobcsv.main()
    mock_s3_client.get_object.assert_not_called()


@patch("Parcial3Big.jobcsv.s3_client")
def test_main_empty_bucket(mock_s3_client):
    mock_s3_client.list_objects_v2.return_value = {}
    result = jobcsv.main()
    assert result is None
