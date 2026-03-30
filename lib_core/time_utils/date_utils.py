"""
Archivo .py con funciones que permiten dar formato a fechas
"""
import datetime
from datetime import timezone

def generate_time():
    """
    Método que devuelve una string con la hora actual (UTC) en formato utilizado para DynamoDB (AWS)

    :return type: String
    :return: Horario UTC actual con formato apto para DynamoDB(AWS)

    Ejemplo::

        utc_now_dynamo = generate_time_aws()
        print(utc_now_dynamo)
        >> '2021-09-07T12:42:25.809410+00:00Z'
    """
    timestamp = datetime.datetime.now(timezone.utc).isoformat()
    return timestamp + 'Z'