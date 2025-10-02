import requests
from bs4 import BeautifulSoup

def get_omxs30_tickers():
    try:
        url = "https://www.nasdaqomxnordic.com/index/index_info?Instrument=SE0000337842"
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        tickers = []
        table = soup.find("table", {"id": "IndexComponentTable"})
        if table:
            rows = table.find_all("tr")[1:]
            for row in rows:
                cols = row.find_all("td")
                if len(cols) > 1:
                    ticker = cols[0].text.strip()
                    if ticker:
                        tickers.append(ticker + ".ST")
        if tickers:
            return tickers
    except Exception as e:
        print("Error fetching OMXI30 tickers:", e)

    # Static fallback list of OMXS30 tickers
    return [
        "VOLV-B.ST", "ERIC-B.ST", "ASSA-B.ST", "ATCO-A.ST", "ATCO-B.ST",
        "AZN.ST", "EQT.ST", "SAND.ST", "ESSITY-B.ST", "SHB-A.ST",
        "SEB-A.ST", "SKF-B.ST", "SWED-A.ST", "TEL2-B.ST", "TELIA.ST",
        "HEXA-B.ST", "NDA-SE.ST", "INVE-B.ST", "KINV-B.ST", "HUSQ-B.ST",
        "BOL.ST", "SSAB-A.ST", "ALFA.ST", "SCA-B.ST", "CAST.ST",
        "ELUX-B.ST", "LATO-B.ST", "SWMA.ST", "SINCH.ST", "SAAB-B.ST"
    ]
