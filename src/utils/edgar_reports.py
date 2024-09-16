import edgar


async def get_latest_report(company: str, report_type: str) -> str:
    edgar.set_identity("Gerald Sornsen gsornsen@gmail.com")
    try:
        company_obj = edgar.Company(company)
        if not company or company_obj is None:
            return f"Company '{company}' not found in EDGAR database."

        filings = company_obj.get_filings(form=report_type).latest(1)
        if not filings:
            return f"No {report_type} filings found for {company}."

        report = filings.markdown()
        return report
    except Exception as e:
        return f"An error occurred while fetching the report: {str(e)}"
