# Quick Usage Guide

## Files Created

1. **scraper.py** - Full production scraper (scrapes all listings)
2. **test_scraper.py** - Test scraper (limited to 5 listings, for testing)
3. **requirements.txt** - Python dependencies
4. **README.md** - Comprehensive documentation

## Quick Start

### 1. Test the Scraper (Recommended First)

Test with a small sample before running the full scraper:

```bash
python test_scraper.py
```

This will:
- Fetch 2 listing pages
- Scrape 5 listings
- Save to `test_results.json`
- Show results in terminal

**Expected output:**
```
============================================================
TEST SCRAPER - Limited scope
============================================================

1. Fetching listing pages...
  Fetching page start=0...
    Found 3 listings
  ...

2. Scraping detail pages...
  [1/5] Scraping: https://ustasi.az/...
    Phone: 0552276465
    ✓ Success
  ...

TEST RESULTS: 5 listings scraped
✓ Saved to test_results.json
```

### 2. Run Full Scraper

Once the test works, run the full scraper:

```bash
python scraper.py
```

This will:
- Fetch ALL listing pages (with pagination)
- Scrape ALL individual listings
- Save to `ustasi_listings.json` and `ustasi_listings.csv`
- Show progress in terminal

**Note:** This may take a while depending on how many listings exist on the site.

## Output Files

### JSON Format (`ustasi_listings.json`)
```json
[
  {
    "listing_id": "1615",
    "title": "Mətbəx mebelləri",
    "categories": "Təmir Ustasi, Mebel ustası",
    "price": "119 Azn",
    "phone": "0552276465",
    "user_name": "Company Name",
    "user_id": "123456",
    "location": "Bakı şəhəri",
    "date": "09.11.2025",
    "description": "Full description text...",
    "url": "https://ustasi.az/..."
  }
]
```

### CSV Format (`ustasi_listings.csv`)
Spreadsheet with columns:
- listing_id
- title
- categories
- price
- phone
- user_name
- user_id
- location
- date
- description
- url

## Configuration

Edit `scraper.py` to customize:

```python
class UstasiScraper:
    def __init__(self):
        # ... existing code ...

# Adjust these in the methods:

# In fetch_all_listing_urls():
max_consecutive_empty = 3  # Stop after N empty pages

# In scrape_all_listings():
max_concurrent = 5  # Number of parallel requests

# Delays:
await asyncio.sleep(0.5)  # Between page requests
await asyncio.sleep(0.3)  # Between detail requests
```

## Troubleshooting

### No phone numbers extracted
- The scraper now correctly extracts phone numbers via AJAX
- Some listings may not have phone numbers (will be empty string)

### Connection timeout
- Increase timeout in `create_session()`:
```python
timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds
```

### Too many requests / Rate limiting
- Increase delays between requests:
```python
await asyncio.sleep(1.0)  # Increase from 0.5 to 1.0
```

- Reduce concurrency:
```python
max_concurrent = 3  # Reduce from 5 to 3
```

### Pagination not stopping
- The scraper stops after 3 consecutive empty pages
- If needed, set a hard limit in `fetch_all_listing_urls()`:
```python
max_pages = 100  # Add a maximum page limit
while consecutive_empty < max_consecutive_empty and start < max_pages:
    # ... existing code ...
```

## Features Implemented

✅ Asynchronous scraping with asyncio/aiohttp
✅ POST requests for pagination
✅ Infinite pagination trap detection
✅ Phone number extraction via AJAX
✅ Complete data extraction (title, price, description, etc.)
✅ CSV and JSON export
✅ Rate limiting and polite scraping
✅ Error handling
✅ Progress tracking
✅ Concurrent requests with semaphore

## Notes

- The scraper is polite and includes delays to avoid overloading the server
- Failed phone number extractions are logged but don't stop the scraper
- Duplicate URLs are automatically removed
- Empty fields are saved as empty strings (not null)
