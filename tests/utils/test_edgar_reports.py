from unittest.mock import MagicMock, patch

import pytest

from src.utils.edgar_reports import get_latest_report


@pytest.mark.asyncio
async def test_get_latest_report_success():
    mock_company = MagicMock()
    mock_filings = MagicMock()
    mock_filings.markdown.return_value = "Mocked report content"

    with patch('edgar.Company', return_value=mock_company), \
         patch('edgar.set_identity') as mock_set_identity:
        mock_company.get_filings.return_value.latest.return_value = mock_filings

        result = await get_latest_report("AAPL", "10-K")

        assert result == "Mocked report content"
        mock_set_identity.assert_called_once_with("Gerald Sornsen gsornsen@gmail.com")
        mock_company.get_filings.assert_called_once_with(form="10-K")
        mock_company.get_filings.return_value.latest.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_get_latest_report_company_not_found():
    with patch('edgar.Company', side_effect=Exception("Company not found")), \
         patch('edgar.set_identity'):
        result = await get_latest_report("INVALID", "10-K")

        assert result == """
        An error occurred while fetching the
        report: Company not found
        """

@pytest.mark.asyncio
async def test_get_latest_report_no_filings():
    mock_company = MagicMock()
    mock_company.get_filings.return_value.latest.return_value = None

    with patch('edgar.Company', return_value=mock_company), \
         patch('edgar.set_identity'):
        result = await get_latest_report("AAPL", "10-Q")

        assert result == "No 10-Q filings found for AAPL."

@pytest.mark.asyncio
async def test_get_latest_report_exception():
    with patch('edgar.Company', side_effect=Exception("Test error")), \
         patch('edgar.set_identity'):
        result = await get_latest_report("AAPL", "10-K")

        assert result == "An error occurred while fetching the report: Test error"

@pytest.mark.asyncio
async def test_get_latest_report_company_none():
    with patch('edgar.Company', return_value=None), \
         patch('edgar.set_identity'):
        result = await get_latest_report("", "10-K")

        assert result == "Company '' not found in EDGAR database."

@pytest.mark.asyncio
async def test_get_latest_report_other_exception():
    with patch('edgar.Company', side_effect=ValueError("Unexpected error")), \
         patch('edgar.set_identity'):
        result = await get_latest_report("AAPL", "10-K")

        assert result == "An error occurred while fetching the report: Unexpected error"

@pytest.mark.asyncio
async def test_get_latest_report_empty_report():
    mock_company = MagicMock()
    mock_filings = MagicMock()
    mock_filings.markdown.return_value = ""

    with patch('edgar.Company', return_value=mock_company), \
         patch('edgar.set_identity'):
        mock_company.get_filings.return_value.latest.return_value = mock_filings

        result = await get_latest_report("AAPL", "10-K")

        assert result == "No 10-K filings found for AAPL."
