from lib_core.time_utils.date_utils import generate_time
from datetime import datetime, timedelta

class ScheduleDate:
    def __init__(self):
        pass

    @staticmethod
    def get_customized_date(number_of_days):
        dateTime = generate_time().split('T')[0]
        
        # Convertir la cadena de fecha en un objeto datetime
        date_object = datetime.strptime(dateTime, '%Y-%m-%d')
        
        # Sumar la cantidad de días
        next_day = date_object + timedelta(days=number_of_days)
        
        # Formatear el resultado como una cadena de fecha
        formatted_day = next_day.strftime('%Y-%m-%d')
        return formatted_day