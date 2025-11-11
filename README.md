# Ustasi.az Scraper

Asynchronous web scraper for https://ustasi.az/ using asyncio and aiohttp.

## Features

- Asynchronous scraping using `asyncio` and `aiohttp` for fast performance
- Automatic pagination with infinite loop detection
- Extracts comprehensive listing data including:
  - Title, categories, price
  - User information (name, ID)
  - Location and date
  - Full description
  - Phone numbers (via AJAX requests)
- Exports data to both CSV and JSON formats
- Rate limiting to be respectful to the server
- Concurrent requests with semaphore control

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the scraper:
```bash
python scraper.py
```

The scraper will:
1. Fetch all listing pages from the homepage
2. Extract URLs for all individual listings
3. Visit each listing page and extract detailed information
4. Make AJAX calls to retrieve phone numbers
5. Save results to `ustasi_listings.json` and `ustasi_listings.csv`

## Output

### JSON Format
```json
[
  {
    "listing_id": "1160",
    "title": "Su Sızma Təyini və Təmiri",
    "categories": "Təmir Ustasi, Su Sızması",
    "price": "50 Azn",
    "phone": "0702472442",
    "user_name": "Aleksandr kondrashov",
    "user_id": "246380",
    "location": "Bakı şəhəri",
    "date": "09.11.2025",
    "description": "Full description text...",
    "url": "https://ustasi.az/su-sizma-teyini-ve-temiri-1160.html"
  }
]
```

### CSV Format
CSV file with columns: `listing_id`, `title`, `categories`, `price`, `phone`, `user_name`, `user_id`, `location`, `date`, `description`, `url`

## Configuration

You can modify these parameters in the `UstasiScraper` class:

- `max_concurrent` (default: 5): Maximum number of concurrent requests
- Delays between requests (default: 0.3-0.5 seconds)
- `max_consecutive_empty` (default: 3): Number of empty pages before stopping pagination

## How It Works

### Pagination
The scraper makes POST requests to `/homelist/?start=X` incrementing the start parameter. It stops when it encounters 3 consecutive empty pages to avoid infinite loops.

### Phone Number Extraction
Phone numbers require an AJAX call to `/ajax.php` with specific parameters:
- `act=telshow`
- `id={listing_id}`
- `t=product`
- `h={hash}`

The scraper attempts to extract the hash from the page HTML or uses a fallback.

### Rate Limiting
- 0.5 second delay between pagination requests
- 0.3 second delay between detail page requests
- Maximum 5 concurrent detail page requests

## Error Handling

- Connection timeouts (30 seconds)
- HTTP error responses
- Missing data fields (uses empty strings)
- Failed phone number AJAX calls (continues without phone)

## Notes

- Be respectful of the website's resources
- The scraper includes delays to avoid overloading the server
- Some listings may not have phone numbers if the AJAX call fails
- The scraper removes duplicate URLs automatically
