import os

import pandas as pd
from atlassian import Confluence
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


class ConfluenceData:
    def __init__(self):
        self.confluence = Confluence(
            url=os.getenv("SERVER"),
            username=os.getenv("API_EMAIL"),
            password=os.getenv("API_SECRET"),
        )

    def get_page_data(self):
        page_content = self.confluence.get_page_by_id(
            os.getenv("PAGE_ID"), expand="body.storage", status=None, version=None
        )
        soup = BeautifulSoup(page_content["body"]["storage"]["value"], "html.parser")
        tables = soup.find_all("table")
        tables_dict = {}
        for i, table in enumerate(tables):
            headers = [header.get_text(strip=True) for header in table.find_all("th")]
            table_data = []
            for row in table.find_all("tr")[1:]:  # Skip the header row
                row_data = {}
                cells = row.find_all("td")
                for j, cell in enumerate(cells):
                    user_tag = cell.find_all("ri:user")
                    if user_tag:
                        tags = []
                        for tag in user_tag:
                            tags.append(
                                tag.get("ri:userkey") or tag.get("ri:account-id")
                            )
                        row_data[headers[j]] = tags
                    else:
                        row_data[headers[j]] = cell.get_text()
                table_data.append(row_data)
            df = pd.DataFrame(table_data)
            tables_dict[f"table_{i+1}"] = df
        return tables_dict

    def get_confluence_table(self, table: str):
        if not table:
            return None

        all_tables: list = self.get_page_data()
        if table == "availability":
            return all_tables["table_2"]
        elif table == "named_engineer":
            return all_tables["table_3"]
