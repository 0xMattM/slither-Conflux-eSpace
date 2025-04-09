import requests
import json
import os
import sys
from collections import defaultdict

def download_source_code(address):
    url = f"https://evmapi.confluxscan.org/api?module=contract&action=getsourcecode&address={address}"
    print(f"[+] Fetching source code from {url}")
    response = requests.get(url)
    data = response.json()

    if data["status"] != "1":
        raise Exception(f"Error fetching source code: {data.get('message', 'Unknown error')}")

    source_code = data["result"][0]["SourceCode"]

    if not source_code:
        raise Exception("No source code found.")

    filename = f"{address}.sol"
    with open(filename, "w") as f:
        f.write(source_code)

    print(f"[+] Source code saved to {filename}")
    return filename

def run_slither_analysis(filename, address):
    json_output = f"{address}_report.json"
    cmd = f"slither {filename} --json {json_output}"
    print(f"[+] Running Slither analysis: {cmd}")
    os.system(cmd)
    return json_output

def group_lines(lines):
    """ Agrupa líneas consecutivas en rangos """
    lines = sorted(set(lines))
    ranges = []
    start = prev = lines[0]

    for line in lines[1:]:
        if line == prev + 1:
            prev = line
        else:
            if start == prev:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{prev}")
            start = prev = line

    if start == prev:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{prev}")

    return ", ".join(ranges)

def generate_summary(json_file, summary_file):
    with open(json_file, "r") as f:
        slither_data = json.load(f)

    findings = defaultdict(lambda: {
        "impact": "",
        "files": defaultdict(list),
        "wiki": ""
    })

    for vuln in slither_data.get("results", {}).get("detectors", []):
        check_name = vuln.get("check", "Unknown Check")
        impact = vuln.get("impact", "Unknown")
        wiki_url = vuln.get("wiki", {}).get("url", "")
        elements = vuln.get("elements", [])

        for el in elements:
            source_mapping = el.get("source_mapping", {})
            filename = source_mapping.get("filename", "Unknown File")
            lines = source_mapping.get("lines", [])

            findings[check_name]["impact"] = impact
            findings[check_name]["wiki"] = wiki_url
            findings[check_name]["files"][filename].extend(lines)

    with open(summary_file, "w") as f:
        f.write("# Slither Analysis Summary\n\n")

        for check, details in findings.items():
            f.write(f"## {check}\n")
            f.write(f"- **Severity:** {details['impact']}\n")
            for file, lines in details["files"].items():
                grouped = group_lines(lines)
                f.write(f"- **File:** {file}\n")
                f.write(f"- **Lines:** {grouped}\n")
            f.write(f"- **Reference:** {details['wiki']}\n\n")

    print(f"[+] Summary saved to {summary_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <contract-address>")
        exit(1)

    address = sys.argv[1]
    filename = download_source_code(address)
    json_report = run_slither_analysis(filename, address)
    summary_file = f"{address}_summary.md"
    generate_summary(json_report, summary_file)
