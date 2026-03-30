import datetime
import logging
import pytest
import json
from dateutil.relativedelta import relativedelta
from lib_core.time_utils.get_periods import *
from lib_core.time_utils.date_utils import generate_time

@pytest.mark.regression
class TestExtractPeriods:
    def setup_method(self):
        self.today = generate_time().split('T')[0]

    def test_qa_reports(self):
        """
        Valida que, con el filtro vacío, el request solamente traiga
        datos del usuario ERA.
        """
        response = response_json # Acá va el servicio
        logging.info(json.dumps(response["periodList"], indent=4))

        actual_periods = response["periodList"]  # lista de dicts
        account_created_str = (response["accountCreatedDate"]).replace("Z", "")

        # Convertir a objetos datetime.date
        account_created = datetime.datetime.fromisoformat(account_created_str.split("T")[0]).date()
        today = datetime.datetime.fromisoformat(self.today).date()

        expected_periods = GetPeriod.get_expected_periods(account_created=account_created, today=today)

        #Validar cantidad esperada de reportes según si la fecha de creación es mayor a 1 año entonces debe mostrar 12 reportes
        if (today - account_created).days > 365:
            assert len(actual_periods) == 12, f"Se esperaban 12 reportes, pero se encontraron {len(actual_periods)}"
        else:
            #Validar si la cantidad de reportes es acorde entre lo actual y lo esperado ya que la cantidad a mostrar es menor a 12 por la validación anterior
            assert len(actual_periods) == len(expected_periods), (
                f"Cantidad de reportes incorrecta. Esperados: {len(expected_periods)}."
                f"Recibidos: {len(actual_periods)}"
            )

        #Validar orden descendente de títulos y fechas
        for expected, actual in zip(expected_periods, actual_periods):
            assert expected["month"] == actual["month"], f"Mes incorrecto: esperado {expected['month']}, recibido {actual['month']}"
            assert expected["year"] == actual["year"], f"Mes incorrecto: esperado {expected['year']}, recibido {actual['year']}"
            assert expected["title"] == actual["title"], f"Mes incorrecto: esperado {expected['title']}, recibido {actual['title']}"

    def test_get_periods_incluye_mes_anterior_si_hoy_mayor_igual_cinco(self):
        """
        Si hoy es posterior o igual al día 5 del mes, el período más reciente
        debe corresponder al mes anterior.
        """
        account_created = datetime.date(2024, 11, 27)
        today = datetime.date(2025, 3, 10)  # día 10 -> incluye mes anterior

        periods = GetPeriod.get_expected_periods(account_created=account_created, today=today)

        assert len(periods) > 0, "Se esperaba al menos un período generado"

        # El período más reciente debe corresponder al mes anterior al actual
        previous_month_date = today.replace(day=1) - relativedelta(months=1)
        expected_month = str(previous_month_date.month)
        expected_year = str(previous_month_date.year)
        expected_title = f"{REVERSE_MONTHS[previous_month_date.month]} Reporte"

        first = periods[0]
        assert first["month"] == expected_month
        assert first["year"] == expected_year
        assert first["title"] == expected_title

        # No debe aparecer el mes actual en la lista de períodos
        assert not any(
            p["month"] == str(today.month) and p["year"] == str(today.year)
            for p in periods
        )

    def test_get_periods_excluye_mes_anterior_si_hoy_menor_cinco(self):
        """
        Si hoy es anterior al día 5 del mes, el período más reciente
        debe corresponder al mes ante-anterior (se saltea el mes pasado).
        """
        account_created = datetime.date(2024, 11, 27)
        today = datetime.date(2025, 3, 3)  # día 3 -> se saltea mes pasado

        periods = GetPeriod.get_expected_periods(account_created=account_created, today=today)

        assert len(periods) > 0, "Se esperaba al menos un período generado"

        # El período más reciente debe ser dos meses hacia atrás (se saltea el mes pasado)
        two_months_back_date = today.replace(day=1) - relativedelta(months=2)
        expected_month = str(two_months_back_date.month)
        expected_year = str(two_months_back_date.year)
        expected_title = f"{REVERSE_MONTHS[two_months_back_date.month]} Reporte"

        first = periods[0]
        assert first["month"] == expected_month
        assert first["year"] == expected_year
        assert first["title"] == expected_title

        # No debe aparecer el mes pasado en la lista de períodos
        one_month_back_date = today.replace(day=1) - relativedelta(months=1)
        assert not any(
            p["month"] == str(one_month_back_date.month)
            and p["year"] == str(one_month_back_date.year)
            for p in periods
        )