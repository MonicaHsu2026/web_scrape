import requests  # HTTP library for fetching web pages
from bs4 import BeautifulSoup  # HTML parser for extracting content
from tabulate import tabulate  # Library for formatting output as a table


def get_sp500_symbols():  # Function to extract S&P 500 company symbols from Wikipedia
    """Extract the list of S&P 500 company symbols from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"  # Wikipedia S&P 500 list URL
    headers = {  # Headers to mimic a browser request
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=15)  # Fetch the Wikipedia page
    response.raise_for_status()  # Raise error if request fails
    soup = BeautifulSoup(response.text, "html.parser")  # Parse the HTML

    tables = soup.find_all("table")  # Find all tables on the page

    companies = []  # List to store company data
    
    # The first table contains the main S&P 500 companies list
    if tables:  # if tables exist
        main_table = tables[0]  # Get the first table
        
        # Get all rows except the header
        rows = main_table.find_all("tr")[1:]  # Skip header row
        
        for row in rows:  # Loop through each row
            cols = row.find_all("td")  # Find all columns (td elements)
            if cols:  # if columns exist
                symbol = cols[0].get_text(strip=True)  # Extract symbol from first column
                security = cols[1].get_text(strip=True) if len(cols) > 1 else ""  # Extract security name
                sector = cols[2].get_text(strip=True) if len(cols) > 2 else ""  # Extract GICS sector
                industry = cols[3].get_text(strip=True) if len(cols) > 3 else ""  # Extract GICS sub-industry
                location = cols[4].get_text(strip=True) if len(cols) > 4 else ""  # Extract headquarters location
                
                companies.append({  # Add company data to list
                    "Symbol": symbol,
                    "Security": security,
                    "Sector": sector,
                    "Industry": industry,
                    "Location": location
                })
    
    return companies  # Return the list of companies


if __name__ == "__main__":  # Main execution block
    import argparse  # Parse command line arguments
    
    parser = argparse.ArgumentParser(  # Create argument parser
        description="Extract S&P 500 company symbols from Wikipedia."
    )
    parser.add_argument("--table", action="store_true", help="Display output as a formatted table")  # Optional table flag
    parser.add_argument("--symbols-only", action="store_true", help="Display only the symbols (one per line)")  # Optional symbols only flag
    parser.add_argument("--sector", help="Filter by GICS sector")  # Optional sector filter
    parser.add_argument("--count", action="store_true", help="Display the total count of companies")  # Optional count flag
    args = parser.parse_args()  # Parse the CLI arguments
    
    companies = get_sp500_symbols()  # Fetch all S&P 500 companies
    
    # Apply sector filter if specified
    if args.sector:  # if sector filter is provided
        companies = [c for c in companies if c["Sector"].lower() == args.sector.lower()]  # Filter by sector
    
    if args.count:  # if count flag is set
        print(f"Total companies: {len(companies)}")  # Print the count
    elif args.symbols_only:  # if symbols only flag is set
        for company in companies:  # Loop through each company
            print(company["Symbol"])  # Print just the symbol
    elif args.table:  # if table flag is set
        table_data = [[  # Create table data
            c["Symbol"],  # symbol column
            c["Security"],  # security column
            c["Sector"],  # sector column
            c["Industry"],  # industry column
            c["Location"]  # location column
        ] for c in companies]  # for each company
        print(tabulate(table_data, headers=["Symbol", "Security", "Sector", "Industry", "Location"], tablefmt="grid"))  # Print as table
    else:  # Otherwise
        for company in companies:  # Loop through each company
            print(f"{company['Symbol']}: {company['Security']} ({company['Sector']})")  # Print company info
