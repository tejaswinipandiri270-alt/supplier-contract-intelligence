
import re
import calendar
from datetime import date

MONTHS = {
    month.lower(): number
    for number, month in enumerate(
        [
            "January", "February", "March", "April",
            "May", "June", "July", "August",
            "September", "October", "November", "December"
        ],
        start=1
    )
}


def parse_filters(question: str) -> tuple[dict, str, bool]:
    q = question.lower()
    filters = {}

    # 1. Contract category
    for category in ["IT", "Facilities", "Logistics"]:
        if re.search(rf"\b{category.lower()}\b", q):
            filters["category"] = category

    # 2. Auto-renewal filter
    if re.search(
        r"\b(do not|does not|doesn't|not|never)\s+"
        r"(?:automatically\s+)?auto[\s-]?renew\b",
        q
    ):
        filters["auto_renew"] = False

    elif any(term in q for term in [
        "auto-renew",
        "auto renew",
        "automatically renew",
        "automatic renewal"
    ]):
        filters["auto_renew"] = True

    # 3. Quarter-based date filtering
    quarter_match = re.search(r"\bq([1-4])\s*(20\d{2})\b", q)

    if quarter_match:
        quarter = int(quarter_match.group(1))
        year = int(quarter_match.group(2))

        start_month = 1 + (quarter - 1) * 3
        end_month = start_month + 2

        filters["end_date_range"] = {
            "gte": f"{year}-{start_month:02d}-01",
            "lte": (
                f"{year}-{end_month:02d}-"
                f"{calendar.monthrange(year, end_month)[1]:02d}"
            )
        }

    else:
        # Dates such as before 31 March 2027
        date_match = re.search(
            r"(?:before|by|on or before|no later than)\s+"
            r"(\d{1,2})\s+"
            r"(january|february|march|april|may|june|july|"
            r"august|september|october|november|december)\s+"
            r"(20\d{2})",
            q
        )

        if date_match:
            day = int(date_match.group(1))
            month = MONTHS[date_match.group(2)]
            year = int(date_match.group(3))

            parsed_date = date(year, month, day).isoformat()

            filters["end_date_range"] = {
                "lte": parsed_date
            }

        else:
            # ISO date such as 2027-03-31
            iso_match = re.search(
                r"(?:before|by)\s+(20\d{2}-\d{2}-\d{2})",
                q
            )

            if iso_match:
                filters["end_date_range"] = {
                    "lte": iso_match.group(1)
                }

    # 4. Supplier-name extraction
    supplier_match = re.search(
        r"\b(?:for|about|of|terminate|terminating|with|the)\s+"
        r"(?:the\s+)?"
        r"([A-Z][A-Za-z0-9&.-]*"
        r"(?:\s+[A-Z][A-Za-z0-9&.-]*)*)"
        r"\s+(?:(?:IT|facilities|logistics)\s+)?"
        r"(?:contract|agreement)\b",
        question
    )

    if supplier_match:
        candidate = supplier_match.group(1).strip()

        if candidate.lower() not in {
            "which", "what", "this", "these"
        }:
            filters["supplier"] = candidate

    # 5. Identify list questions
    asks_for_list = bool(
        re.search(
            r"\b(which|list|all|show me|identify)\b",
            q
        )
        and re.search(
            r"\b(contracts|suppliers)\b",
            q
        )
    )

    is_list = asks_for_list

    # 6. Prepare semantic search query
    semantic = question

    semantic = re.sub(
        r"\b(which|contracts|contract|before|by|"
        r"in q[1-4]|all|suppliers)\b",
        " ",
        semantic,
        flags=re.IGNORECASE
    )

    semantic = re.sub(
        r"\s+",
        " ",
        semantic
    ).strip()

    return filters, semantic, is_list
