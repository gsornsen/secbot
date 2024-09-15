import argparse

import edgar

edgar.set_identity("Gerald Sornsen gsornsen@gmail.com")


def get_latest_report(company, report_type):
    filings = edgar.Company(f"{company}").get_filings(form=f"{report_type}").latest(1)
    report = filings.markdown()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch the latest SEC report for a company."
    )
    parser.add_argument("company", type=str, help="The name of the company")
    parser.add_argument(
        "report_type", type=str, help="The type of report (e.g., 10-K, 10-Q)"
    )

    args = parser.parse_args()

    report = get_latest_report(args.company, args.report_type)
    print(report)
