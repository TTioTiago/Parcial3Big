import pytest
from Parcial3Big.Sapcsv import func
from unittest.mock import patch, MagicMock
from datetime import datetime


def test_extract_data_from_html():
    html_content = '''
        <html>
        <body>
            <article class="c-articulo--textual" data-category="Actualidad">
                <a class="c-articulo__titulo__txt" href="https://www.eltiempo.com/noticia1">Titular 1</a>
            </article>
            <article class="c-articulo--textual" data-category="Deportes">
                <a class="c-articulo__titulo__txt" href="https://www.eltiempo.com/noticia2">Titular 2</a>
            </article>
        </body>
        </html>
    '''
    result = func.extract_data_from_html(html_content)
    assert result == [
        ["Actualidad", "Titular 1", "https://www.eltiempo.com/noticia1"],
        ["Deportes", "Titular 2", "https://www.eltiempo.com/noticia2"]
    ]


@patch("Parcial3Big.Sapcsv.func.s3_client")
@patch("Parcial3Big.Sapcsv.func.extract_data_from_html")
def test_app_success(mock_extract, mock_s3_client):
    mock_extract.return_value = [["Categoria", "Titular", "Enlace"]]
    mock_s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: "<html></html>")}

    event = {
        "Records": [
            {"s3": {"object": {"key": "raw/test.html"}}}
        ]
    }

    response = func.app(event, None)
    assert response["status"] == "OK"
    assert "exitosamente" in response["message"]
    mock_s3_client.put_object.assert_called_once()
    mock_extract.assert_called_once()


def test_app_no_records():
    event = {}
    result = func.app(event, None)
    assert result["status"] == "ERROR"
    assert "Records" in result["message"]


@patch("Parcial3Big.Sapcsv.func.s3_client")
@patch("Parcial3Big.Sapcsv.func.extract_data_from_html")
def test_app_no_news_found(mock_extract, mock_s3_client):
    mock_extract.return_value = []
    mock_s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: "<html></html>")}

    event = {
        "Records": [
            {"s3": {"object": {"key": "raw/empty.html"}}}
        ]
    }

    result = func.app(event, None)
    assert result["status"] == "ERROR"
    assert "válida" in result["message"]
