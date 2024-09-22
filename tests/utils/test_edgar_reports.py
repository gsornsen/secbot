from unittest.mock import MagicMock, patch

import pytest

from utils.edgar_reports import get_latest_report


@pytest.fixture
def mock_edgar():
    with patch("src.utils.edgar_reports.edgar") as mock:
        yield mock


def test_get_latest_report_success(mock_edgar):
    mock_company = MagicMock()
    mock_filings = MagicMock()
    mock_edgar.Company.return_value = mock_company
    mock_company.get_filings.return_value.latest.return_value = mock_filings
    mock_filings.markdown.return_value = "Mocked report content"

    result = get_latest_report("AAPL", "10-K")

    assert result == "Mocked report content"
    mock_edgar.set_identity.assert_called_once_with("Gerald Sornsen gsornsen@gmail.com")
    mock_edgar.Company.assert_called_once_with("AAPL")
    mock_company.get_filings.assert_called_once_with(form="10-K")
    mock_company.get_filings.return_value.latest.assert_called_once_with(1)


def test_get_latest_report_company_not_found(mock_edgar):
    mock_edgar.Company.return_value = None

    result = get_latest_report("INVALID", "10-K")

    assert result == "Company 'INVALID' not found in EDGAR database."


def test_get_latest_report_no_filings(mock_edgar):
    mock_company = MagicMock()
    mock_edgar.Company.return_value = mock_company
    mock_company.get_filings.return_value.latest.return_value = None

    result = get_latest_report("AAPL", "10-Q")

    assert result == "No 10-Q filings found for AAPL."


def test_get_latest_report_exception(mock_edgar):
    mock_edgar.Company.side_effect = Exception("Test error")

    result = get_latest_report("AAPL", "10-K")

    assert result == "An error occurred while fetching the report: Test error"


def test_get_latest_report_empty_company(mock_edgar):
    result = get_latest_report("", "10-K")

    assert result == "Company '' not found in EDGAR database."
    mock_edgar.Company.assert_called_once_with("")


def test_get_latest_report_empty_report_type(mock_edgar):
    mock_company = MagicMock()
    mock_edgar.Company.return_value = mock_company
    mock_company.get_filings.return_value.latest.return_value = None

    result = get_latest_report("AAPL", "")

    assert result == "No  filings found for AAPL."
    mock_company.get_filings.assert_called_once_with(form="")
