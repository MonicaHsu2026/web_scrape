import requests  # HTTP library used to fetch the Yahoo Finance page
from bs4 import BeautifulSoup  # HTML parser for extracting page content


def get_previous_close(symbol: str) -> float:  # function that returns the previous close price
    """Return the Yahoo Finance previous close price for a stock symbol."""
    url = f"https://finance.yahoo.com/quote/{symbol}"  # build the ticker URL for Yahoo Finance
    headers = {  # request headers to mimic a real browser
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",  # prefer English content
    }

    response = requests.get(url, headers=headers, timeout=15)  # fetch the page
    response.raise_for_status()  # raise an error if the request failed

    soup = BeautifulSoup(response.text, "html.parser")  # parse the HTML response
    prev_close_cell = soup.find("td", {"data-test": "PREV_CLOSE-value"})  # look for the previous close cell

    if prev_close_cell is not None:  # if the expected HTML element exists
        previous_close_text = prev_close_cell.get_text(strip=True)  # grab the text and strip whitespace
        return float(previous_close_text.replace(",", ""))  # convert the text to a float

    # Fallback: parse the embedded JSON-like data on the page.
    import re  # import regex library for fallback parsing

    match = re.search(r'previousClose["\\]*\s*:\s*([0-9]+(?:\.[0-9]+)?)', response.text)  # search for previousClose in JSON text
    if match:  # if a match is found
        return float(match.group(1))  # return the numeric capture group

    raise ValueError(  # raise an error if the value cannot be found
        "Could not find the previous close value on the Yahoo Finance page. "
        "The page structure may have changed."
    )


if __name__ == "__main__":  # only execute when run as a script
    import argparse  # parse command line arguments

    parser = argparse.ArgumentParser(
        description="Fetch the previous close price from Yahoo Finance for a stock ticker."
    )  # create the argument parser
    parser.add_argument("symbol", help="Ticker symbol, e.g. AAPL")  # required ticker symbol
    args = parser.parse_args()  # parse the CLI args

    price = get_previous_close(args.symbol)  # fetch the price for the provided symbol
    print(price)  # print the result to stdout
