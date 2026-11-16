
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import json
from datetime import datetime, timezone

BASE_URL = "https://www.tn.gov.in/"

INPUT_FILE = Path("data/raw/schemes_index.html")
OUTPUT_FILE = Path("data/processed/departments.json")


class DepartmentParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.departments = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attributes = dict(attrs)
            href = attributes.get("href", "")

            if "scheme_list.php?dep_id=" in href:
                self.current_link = {
                    "name": "",
                    "url": href
                }

    def handle_data(self, data):
        if self.current_link:
            self.current_link["name"] += data.strip() + " "

    def handle_endtag(self, tag):
        if tag == "a" and self.current_link:
            name = self.current_link["name"].strip()

            if name:
                self.departments.append({
                    "department_name": name,
                    "department_url": urljoin(
                        BASE_URL,
                        self.current_link["url"]
                    )
                })

            self.current_link = None


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Source HTML not found: {INPUT_FILE}"
        )

    html = INPUT_FILE.read_text(
        encoding="utf-8",
        errors="replace"
    )

    parser = DepartmentParser()
    parser.feed(html)

    # Remove duplicate URLs
    unique_departments = {
        department["department_url"]: department
        for department in parser.departments
    }

    results = list(unique_departments.values())

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output = {
        "source": BASE_URL + "schemes.php",
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_departments": len(results),
        "departments": results
    }

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("Department extraction completed.")
    print("Total departments:", len(results))
    print("Output:", OUTPUT_FILE)

    for index, department in enumerate(results, 1):
        print(
            f"{index}. {department['department_name']}"
        )
        print(
            f"   {department['department_url']}"
        )


if __name__ == "__main__":
    main()
