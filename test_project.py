from unittest.mock import Mock, patch
import sys
sys.path.insert(0, "Parcial1Big/Zappacsv")  # Ajusta según la estructura real de tu proyecto
import function


def test_extract_data_from_html():
    """Prueba la extracción de datos desde el HTML."""
    html_content = (
        '<script type="application/ld+json">'
        '{"about": [{"address": {"addressLocality": "Chapinero"}, '
        '"description": "desde $ 500000000", "numberOfBedrooms": 1, '
        '"numberOfBathroomsTotal": 1, "floorSize": {"value": 50}}]}'
        "</script>"
    )
    result = function.extract_data_from_html(html_content)

    assert result == [["Chapinero", "500000000", 1, 1, 50]]


@patch("function.s3_client.get_object")
def test_lambda_handler(mock_get_object):
    """Prueba la ejecución de la función Lambda con un archivo S3."""
    event = {
        "Records": [
            {"s3": {"bucket": {"name": "bucket-zappascrap"}, "object": {"key": "pagina-1.html"}}}
        ]
    }

    mock_get_object.return_value = {
        "Body": Mock(
            read=lambda: b'<script type="application/ld+json">'
            b'{"about": [{"address": {"addressLocality": "Chapinero"}, '
            b'"description": "desde $ 500000000", "numberOfBedrooms": 1, '
            b'"numberOfBathroomsTotal": 1, "floorSize": {"value": 50}}]}'
            b"</script>"
        )
    }

    result = function.app(event, None)

    assert result["status"] == "OK"


def test_app_function_no_records():
    """Prueba cuando el evento no contiene 'Records'."""
    event = {}
    result = function.app(event, None)

    assert result["status"] == "ERROR"
    assert result["message"] == "Evento sin 'Records'"
