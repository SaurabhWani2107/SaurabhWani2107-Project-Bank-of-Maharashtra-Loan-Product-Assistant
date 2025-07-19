from playwright.sync_api import sync_playwright

URL = "https://bankofmaharashtra.in/mahabank-vehicle-loan-scheme-for-second-hand-car"
OUTPUT_FILE = "../Extracteddata_scriptwise/script_6.txt"

def extract_sub_table(sub_table, label=None):
    lines = []
    # Add a label for clarity
    if label:
        lines.append(f"    [Sub-table: {label}]")
    # Extract headers from thead or first row
    headers = [th.inner_text().strip() for th in sub_table.query_selector_all("thead tr th")]
    body_rows = sub_table.query_selector_all("tbody tr")
    if not headers and body_rows:
        headers = [td.inner_text().strip() for td in body_rows[0].query_selector_all("td")]
        body_rows = body_rows[1:]
    if headers:
        lines.append("    " + " | ".join(headers))
        lines.append("    " + "-" * (len(" | ".join(headers))))
    for row in body_rows:
        cells = row.query_selector_all("td")
        if cells:
            row_text = "    " + " | ".join([cell.inner_text().strip() for cell in cells])
            lines.append(row_text)
    return "\n".join(lines)

def extract_table_structured(table):
    output = []
    # Only get direct tr children of the main table's tbody
    rows = table.query_selector_all(":scope > tbody > tr")
    for row in rows:
        cells = row.query_selector_all("td")
        if len(cells) == 3:
            s_no = cells[0].inner_text().strip()
            particular = cells[1].inner_text().strip()
            scheme_cell = cells[2]

            scheme_text_parts = []

            # Extract <ul> lists
            ul_lists = scheme_cell.query_selector_all("ul")
            for ul in ul_lists:
                for li in ul.query_selector_all("li"):
                    scheme_text_parts.append("  - " + li.inner_text().strip())

            # Extract <ol> lists
            ol_lists = scheme_cell.query_selector_all("ol")
            for ol in ol_lists:
                for idx, li in enumerate(ol.query_selector_all("li"), 1):
                    scheme_text_parts.append(f"  {idx}. {li.inner_text().strip()}")

            # Extract sub-tables (tables inside the cell)
            sub_tables = scheme_cell.query_selector_all("table")
            for sub_table in sub_tables:
                scheme_text_parts.append(extract_sub_table(sub_table, label="Embedded Table"))

            # Get direct text, but remove text from sub-tables and lists to avoid duplication
            direct_text = scheme_cell.inner_text().strip()
            for el in ul_lists + ol_lists + sub_tables:
                el_text = el.inner_text().strip()
                if el_text and el_text in direct_text:
                    direct_text = direct_text.replace(el_text, "")
            if direct_text:
                scheme_text_parts.insert(0, direct_text.strip())

            # Remove duplicates and empty lines, preserve order
            seen = set()
            scheme_text = "\n".join(
                x for x in scheme_text_parts if x and not (x in seen or seen.add(x))
            )

            output.append(
                f"\nS.No: {s_no}\nParticulars: {particular}\nScheme guidelines:\n{scheme_text}\n"
            )
    return output

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()
        page.goto(URL, timeout=60000)
        page.wait_for_selector("div.page-con-list-block", timeout=15000)
        block = page.query_selector("div.page-con-list-block")

        output_lines = []

        # --- Intro Section ---
        heading = block.query_selector("h1")
        subheading = block.query_selector("h2")
        intro_paragraph = block.query_selector("p")
        output_lines.append("--- Intro ---")
        if heading:
            output_lines.append(heading.inner_text().strip())
        if subheading:
            output_lines.append(subheading.inner_text().strip())
        if intro_paragraph:
            output_lines.append(intro_paragraph.inner_text().strip())

        # --- Table Extraction ---
        table = block.query_selector("table")
        output_lines.append("\n--- Scheme Table ---")
        if table:
            output_lines.extend(extract_table_structured(table))
        else:
            output_lines.append("Table not found.")

        # Write to output file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines))

        browser.close()

if __name__ == "__main__":
    main() 