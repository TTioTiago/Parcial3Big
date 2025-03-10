from unittest.mock import Mock, patch
from io import StringIO
import function


def test_extract_data_from_html():
    """Prueba la extracción de datos desde el HTML con la estructura de Mitula."""
    html_content = """
    <a class="listing listing-card"
       data-price="500000000"
       data-location="Chapinero"
       data-rooms="1">
        <p data-test="bathrooms" content="1"></p>
        <p data-test="floor-area" content="50 m²"></p>
    </a>
    """
    result = function.extract_data_from_html(html_content)

    assert result == [["Chapinero", "500000000", "1", "1", "50"]]


@patch("function.s3_client.get_object")
def test_lambda_handler(mock_get_object):
    """Prueba la ejecución de la función Lambda con un archivo S3."""
    event = {
        "Records": [
            {"s3": {"bucket": {"name": "bucket-zappascrap"}, "object": {"key": "pagina-1.html"}}}
        ]
    }

    html_mock = """
    <a class="listing listing-card"
       data-price="450000000"
       data-location="Suba"
       data-rooms="2">
        <p data-test="bathrooms" content="2"></p>
        <p data-test="floor-area" content="60 m²"></p>
    </a>
    """

    mock_get_object.return_value = {
        "Body": StringIO(html_mock)  # 🔥 Simula un archivo en memoria
    }

    result = function.app(event, None)

    assert result["status"] == "OK"


def test_app_function_no_records():
    """Prueba cuando el evento no contiene 'Records'."""
    event = {}
    result = function.app(event, None)

    assert result["status"] == "ERROR"
    assert result["message"] == "Evento sin 'Records'"
    