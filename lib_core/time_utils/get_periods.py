from dateutil.relativedelta import relativedelta
import datetime


MONTHS = {
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
}

REVERSE_MONTHS = {
    v: k for k, v in MONTHS.items()}

class GetPeriod:
    def __init__(self):
        pass

    @staticmethod
    def get_expected_periods(account_created, today):
        """
        :param account_created: Fecha de creación de la cuenta (formato ISO 8601 con hora)
        :param today_str: Fecha actual en formato YYYY-MM-DD
        :return: Lista de períodos mensuales esperados, desde la creación hasta el último período válido
        """

        # Evaluar si se debe incluir el mes pasado o el antepenúltimo
        is_after_fifth = today.day >= 5
        end_month = today.replace(day=1) if is_after_fifth else (today.replace(day=1) - relativedelta(months=1))

        start_month = account_created.replace(day=1)

        periods = []
        current = end_month - relativedelta(months=1)

        while current >= start_month:
            periods.append({
                "month": str(current.month),
                "year": str(current.year),
                "title": f"{REVERSE_MONTHS[current.month]} Reporte"
            })
            current -= relativedelta(months=1)

        return periods


# 👇 Este es el JSON de ejemplo, ahora generado dinámicamente para que
# los períodos coincidan con la lógica de `GetPeriod.get_expected_periods`
from lib_core.time_utils.date_utils import generate_time

_account_created_date_str = "2024-11-27T13:36:44.071022997Z"
_account_created_date = datetime.datetime.fromisoformat(
    _account_created_date_str.split("T")[0]
).date()

_today = datetime.datetime.fromisoformat(generate_time().split("T")[0]).date()
_all_expected_periods = GetPeriod.get_expected_periods(
    account_created=_account_created_date,
    today=_today,
)

# La API debe devolver como máximo 12 períodos.
_period_list = (
    _all_expected_periods[:12] if len(_all_expected_periods) > 12 else _all_expected_periods
)

response_json = {
    "accountCreatedDate": _account_created_date_str,
    "periodList": _period_list,
}