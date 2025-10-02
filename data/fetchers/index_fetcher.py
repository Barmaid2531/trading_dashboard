import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_omxs30_tickers():
    """
    Fetch OMXS30 tickers dynamically from Nasdaq OMX Nordic.
    """
    url = "https://www.nasdaqomxnordic.com/index/index_info?Instrument=SE0000337842"  # OMXS30 index page
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    tickers = []
    table = soup.find("table", {"id": "IndexComponentTable"})
    if table:
        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) > 1:
                ticker = cols[0].text.strip()
                if ticker:
                    # Append ".ST" for Yahoo Finance lookup
                    tickers.append(ticker + ".ST")
    return tickers
