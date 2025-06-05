import pytest
from unittest.mock import patch, MagicMock
from Parcial3Big.ZappaScrap import scrap


@patch("Parcial3Big.Zappa_Scrap.scrap.requests.get")
@patch("Parcial3Big.Zappa_Scrap.scrap.s3_client.put_object")
def test_download_and_upload_success(mock_put_object, mock_requests_get):
    # Simular respuesta exitosa
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html><head></head><body>Contenido</body></html>"
    mock_requests_get.return_value = mock_response

    result = scrap.download_and_upload({}, {})

    assert result["status"] == "OK"
    assert "completada" in result["message"]

    mock_requests_get.assert_called_once_with(
        "https://www.eltiempo.com/",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    mock_put_object.assert_called_once()
    args, kwargs = mock_put_object.call_args
    assert kwargs["Bucket"] == scrap.S3_BUCKET
    assert kwargs["Key"].startswith("headlines/raw/contenido-eltiempo-")
    assert kwargs["Body"] == mock_response.text


@patch("Parcial3Big.Zappa_Scrap.scrap.requests.get")
@patch("Parcial3Big.Zappa_Scrap.scrap.s3_client.put_object")
def test_download_and_upload_fail_status_code(mock_put_object, mock_requests_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    result = scrap.download_and_upload({}, {})
    assert result["status"] == "OK"
    assert "completada" in result["message"]

    mock_put_object.assert_not_called()


@patch("Parcial3Big.Zappa_Scrap.scrap.requests.get", side_effect=Exception("Timeout"))
@patch("Parcial3Big.Zappa_Scrap.scrap.s3_client.put_object")
def test_download_and_upload_exception(mock_put_object, mock_requests_get):
    result = scrap.download_and_upload({}, {})
    assert result["status"] == "OK"
    assert "completada" in result["message"]

    mock_put_object.assert_not_called()
