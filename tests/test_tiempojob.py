import pytest
from unittest.mock import patch, MagicMock
import builtins



@patch("Parcial3Big.tiempojob.boto3.client")
@patch("Parcial3Big.tiempojob.requests.get")
@patch("builtins.print")
def test_tiempojob_success(mock_print, mock_requests_get, mock_boto3_client):
    # Simula una respuesta exitosa
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>contenido</html>"
    mock_response.raise_for_status = MagicMock()
    mock_requests_get.return_value = mock_response

    mock_s3 = MagicMock()
    mock_boto3_client.return_value = mock_s3

    # Vuelve a importar el archivo para ejecutar su cuerpo
    import importlib
    from Parcial3Big import tiempojob
    importlib.reload(tiempojob)

    # Verifica que se haya llamado put_object
    assert mock_s3.put_object.called
    args, kwargs = mock_s3.put_object.call_args
    assert kwargs["Bucket"] == tiempojob.BUCKET
    assert kwargs["ContentType"] == "text/html"
    assert kwargs["Key"].startswith("headlines/raw/contenido-eltiempo-")


@patch("Parcial3Big.tiempojob.boto3.client")
@patch("Parcial3Big.tiempojob.requests.get")
@patch("builtins.print")
def test_tiempojob_failed_request(mock_print, mock_requests_get, mock_boto3_client):
    mock_requests_get.side_effect = Exception("Falló la descarga")
    mock_s3 = MagicMock()
    mock_boto3_client.return_value = mock_s3

    import importlib
    from Parcial3Big import tiempojob
    importlib.reload(tiempojob)

    mock_print.assert_any_call("❌ Error al procesar https://www.eltiempo.com/: Falló la descarga")
    assert not mock_s3.put_object.called
