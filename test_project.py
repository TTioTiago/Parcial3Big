import pytest
from unittest.mock import Mock, patch
import function

def test_extract_data_from_html():
    html_content = '<script type="application/ld+json">{"about": [{"address": {"addressLocality": "Chapinero"}, "description": "desde $ 500000000", "numberOfBedrooms": 1, "numberOfBathroomsTotal": 1, "floorSize": {"value": 50}}]}</script>'
    result = function.extract_data_from_html(html_content)
    
    assert result == [["Chapinero", "500000000", 1, 1, 50]]

@patch("function.s3_client.get_object")
def test_lambda_handler(mock_get_object):
    event = {
        "Records": [
            {"s3": {"bucket": {"name": "bucket-zappascrap"}, "object": {"key": "pagina-1.html"}}}
        ]
    }

    mock_get_object.return_value = {"Body": Mock(read=lambda: b'<script type="application/ld+json">{"about": [{"address": {"addressLocality": "Chapinero"}, "description": "desde $ 500000000", "numberOfBedrooms": 1, "numberOfBathroomsTotal": 1, "floorSize": {"value": 50}}]}</script>')}

    result = function.app_function(event, None)

    assert result["status"] == "OK"

def test_app_function_no_records():
    event = {}
    result = function.app_function(event, None)
    assert result["status"] == "ERROR"
