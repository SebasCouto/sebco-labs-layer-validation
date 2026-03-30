from decimal import Decimal
from pathlib import Path

import pytest

from lib_core.documents.pdf_utils import (
    assert_contains_text,
    extract_full_text,
    get_page_count,
    is_probably_scanned_pdf,
)
from tests.mocks.report_march_2025_mocks import (
    CUENTA_USUARIO_MOCK,
    MOVIMIENTOS_MOCK,
    TEXTOS_REPORTE_MOCK,
    calculate_closing_balance,
    calculate_totals,
)

pytestmark = pytest.mark.regression


PDF_PATH = Path("tests/resources/sebco_labs_monthly_report.pdf")


def _money_to_pdf_format(value: str) -> str:
    """
    Convierte '85666.40' -> '$ 85.666,40'
    """
    amount = Decimal(value)
    integer_part, decimal_part = f"{amount:.2f}".split(".")
    integer_part = f"{int(integer_part):,}".replace(",", ".")
    return f"$ {integer_part},{decimal_part}"


class TestStatementMarch2025Regression:
    def test_pdf_exists_and_has_expected_pages(self):
        assert PDF_PATH.exists(), f"No existe el PDF esperado en: {PDF_PATH}"
        assert get_page_count(PDF_PATH) == 2

    def test_pdf_is_not_scanned(self):
        assert not is_probably_scanned_pdf(PDF_PATH)

    def test_pdf_contains_user_and_account_header_data(self):
        account_data = CUENTA_USUARIO_MOCK["data"]
        statement = account_data["statement"]
        account = account_data["account"]

        assert_contains_text(PDF_PATH, account_data["holder_name"])
        assert_contains_text(PDF_PATH, f'{statement["period_start"]} - {statement["period_end"]}',)
        assert_contains_text(PDF_PATH, account_data["document_number"])
        assert_contains_text(PDF_PATH, account["cbu"])
        assert_contains_text(PDF_PATH, account["account_number"])

    def test_pdf_contains_summary_totals_from_mock(self):
        statement = CUENTA_USUARIO_MOCK["data"]["statement"]

        assert_contains_text(PDF_PATH, _money_to_pdf_format(statement["opening_balance"]))
        assert_contains_text(PDF_PATH, _money_to_pdf_format(statement["money_in_total"]))
        assert_contains_text(PDF_PATH, _money_to_pdf_format(statement["money_out_total"]))
        assert_contains_text(PDF_PATH, _money_to_pdf_format(statement["closing_balance"]))

    def test_mock_balance_formula_is_consistent(self):
        statement = CUENTA_USUARIO_MOCK["data"]["statement"]
        totals = calculate_totals(MOVIMIENTOS_MOCK)
        calculated_closing_balance = calculate_closing_balance(statement["opening_balance"],MOVIMIENTOS_MOCK,)

        assert totals["money_in_total"] == Decimal(statement["money_in_total"])
        assert totals["money_out_total"] == Decimal(statement["money_out_total"])
        assert calculated_closing_balance == Decimal(statement["closing_balance"])

    def test_pdf_contains_branding_and_not_legacy_brand(self):
        full_text = extract_full_text(PDF_PATH)

        assert "Usuario SebCo. Labs" in full_text
        assert "https://github.com/SebasCouto" in full_text
        assert TEXTOS_REPORTE_MOCK["data"]["sections"]["canales_atencion_title"] in full_text
        assert "Ualá" not in full_text
