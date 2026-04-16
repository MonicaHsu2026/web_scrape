import requests  # HTTP library used to fetch the Yahoo Finance page
from bs4 import BeautifulSoup  # HTML parser for extracting page content
from tabulate import tabulate  # Library for formatting output as a table
import re  # import regex library for parsing


def get_stock_table(symbol: str) -> dict:  # function that extracts all stock metrics from Previous Close to 1y Target Est
    """Return a dictionary of Yahoo Finance stock metrics for a given symbol."""
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
    text = response.text  # get raw text for regex extraction

    metrics = {}  # dictionary to store extracted metrics

    # Mapping of data-field names to display names (for fin-streamer elements)
    fin_field_mapping = [  # define metrics available in fin-streamer elements
        ("regularMarketPrice", "Current Price"),
        ("regularMarketOpen", "Open"),
        ("regularMarketVolume", "Volume"),
        ("averageVolume", "Avg. Volume"),
        ("marketCap", "Market Cap"),
        ("targetMeanPrice", "1y Target Est"),
        ("regularMarketPreviousClose", "Previous Close"),
    ]

    # Try to extract from HTML fin-streamer elements
    for field_name, display_name in fin_field_mapping:  # loop through each metric
        fin_streamer = soup.find("fin-streamer", {"data-field": field_name})  # search for the element
        if fin_streamer:  # if element is found
            value = fin_streamer.get_text(strip=True)  # get the text content
            metrics[display_name] = value if value else "N/A"  # add to metrics dict

    # Extract metrics from li > span.label structure
    lis = soup.find_all("li")  # find all list items
    for li in lis:  # loop through each list item
        label = li.find("span", class_="label")  # find the label span
        if label:  # if label exists
            label_text = label.get_text(strip=True)  # get label text
            all_text = li.get_text(strip=True)  # get all text in the list item
            # Extract value by removing the label from the total text
            value = all_text.replace(label_text, "", 1).strip() if label_text in all_text else ""

            if label_text == "Bid":  # handle Bid
                bid_value = value.split()[0] if value else "N/A"  # extract just the number (before 'x')
                metrics["Bid"] = bid_value  # add to metrics
            elif label_text == "Ask":  # handle Ask
                ask_value = value.split()[0] if value else "N/A"  # extract just the number (before 'x')
                metrics["Ask"] = ask_value  # add to metrics
            elif label_text == "Day's Range":  # handle Day's Range
                range_parts = value.split("-") if "-" in value else []  # split by dash
                if len(range_parts) == 2:  # if we have two values
                    low_val = range_parts[0].strip()  # first value is low
                    high_val = range_parts[1].strip()  # second value is high
                    metrics["Day High"] = high_val  # add day high
                    metrics["Day Low"] = low_val  # add day low
            elif label_text == "52 Week Range":  # handle 52 Week Range
                range_parts = value.split("-") if "-" in value else []  # split by dash
                if len(range_parts) == 2:  # if we have two values
                    low_val = range_parts[0].strip()  # first value is low
                    high_val = range_parts[1].strip()  # second value is high
                    metrics["52 Week High"] = high_val  # add 52 week high
                    metrics["52 Week Low"] = low_val  # add 52 week low
            elif label_text == "Beta (5Y, monthly)":  # handle Beta
                metrics["Beta (5Y)"] = value if value else "N/A"  # add beta
            elif label_text == "EPS (TTM)":  # handle EPS
                metrics["EPS (TTM)"] = value if value else "N/A"  # add EPS
            elif label_text == "PE Ratio (TTM)":  # handle PE Ratio
                metrics["PE Ratio (TTM)"] = value if value else "N/A"  # add PE ratio

    # Fallback: search for values in embedded JSON for fields not found in HTML
    json_fallback = [  # fields that might be in JSON but not in HTML
        ("trailingPE", "PE Ratio (TTM)"),
        ("epsTrailingTwelveMonths", "EPS (TTM)"),
    ]

    for json_key, display_name in json_fallback:  # loop through fallback metrics
        if display_name not in metrics or metrics[display_name] == "N/A":  # only if not already found
            pattern = rf'{json_key}["\\]*\s*:\s*([0-9]+(?:\.[0-9]+)?|null)'  # regex pattern for the metric
            match = re.search(pattern, text)  # search for the metric in the page text
            if match:  # if a match is found
                value = match.group(1)  # get the captured value
                metrics[display_name] = value if value != "null" else "N/A"  # add to metrics dict

    return metrics  # return the extracted metrics


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
        description="Fetch stock metrics from Yahoo Finance for a given ticker."
    )  # create the argument parser
    parser.add_argument("symbol", help="Ticker symbol, e.g. AAPL")  # required ticker symbol
    parser.add_argument("--table", action="store_true", help="Display output as a formatted table")  # optional table flag
    args = parser.parse_args()  # parse the CLI args

    metrics = get_stock_table(args.symbol)  # fetch all metrics for the provided symbol
    
    # Define display order for metrics
    display_order = [  # define the order to display metrics
        "Current Price",
        "Previous Close",
        "Open",
        "Bid",
        "Ask",
        "Day High",
        "Day Low",
        "52 Week High",
        "52 Week Low",
        "Volume",
        "Avg. Volume",
        "Market Cap",
        "Beta (5Y)",
        "PE Ratio (TTM)",
        "EPS (TTM)",
        "1y Target Est",
    ]
    
    if args.table:  # if table flag is set
        table_data = []  # create empty table data
        for key in display_order:  # loop through display order
            if key in metrics:  # if metric exists
                table_data.append([key, metrics[key]])  # add to table
        print(tabulate(table_data, headers=["Metric", "Value"], tablefmt="grid"))  # print as formatted table
    else:  # otherwise
        for key in display_order:  # loop through display order
            if key in metrics:  # if metric exists
                print(f"{key}: {metrics[key]}")  # print each metric
