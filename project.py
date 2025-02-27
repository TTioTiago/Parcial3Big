import json
import datetime

def app(event, context):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"¡Lambda ejecutada con Zappa! Hora actual: {current_time}"

    print(message)  # Esto aparecerá en CloudWatch Logs

    return {
        "statusCode": 200,
        "body": json.dumps({"message": message})
    }
