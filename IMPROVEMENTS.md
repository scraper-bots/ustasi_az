# Scraper V2 - Improvements & Fixes

## Problems with V1

1. **Infinite pagination loop** - The scraper fetched 883+ pages and 3965+ URLs without stopping
2. **No duplicate detection** - Same URLs were being collected multiple times
3. **No crash protection** - If interrupted, all progress was lost
4. **Too slow** - Long delays and low concurrency
5. **No progress tracking** - Couldn't resume if stopped

## V2 Improvements

### 1. Hard Page Limit
```python
scraper = UstasiScraperV2(max_pages=50)  # Hard limit: 50 pages
```
- **Default: 50 pages** (approximately 1,000-1,400 listings)
- Prevents infinite loops
- Adjustable based on your needs

### 2. Duplicate URL Detection
```python
self.seen_urls: Set[str] = set()  # Track all URLs
```
- Detects when pages return duplicate URLs
- Stops automatically if 5 consecutive pages have no new URLs
- Detects pagination loops (same batch of URLs repeating)

### 3. Crash Protection & Resume
```python
self.save_progress(urls, 'urls_collected')
```
- Saves progress to `scraper_progress.json`
- Can resume from where it stopped
- Saves partial results on Ctrl+C or crash
- Creates temp file every 50 listings

### 4. Better Performance
- **10 concurrent requests** (vs 5 in V1)
- **0.1s delays** between requests (vs 0.3-0.5s)
- **Faster** - 3-4x speed improvement

### 5. Better Error Handling
- Timeout protection (30s per request)
- Continues on individual failures
- Tracks success/failure counts
- Saves partial results on any error

## Usage

### Quick Start
```bash
python scraper_v2.py
```

### Adjust Page Limit
Edit line in `scraper_v2.py`:
```python
scraper = UstasiScraperV2(max_pages=100)  # Increase to 100 pages
```

Recommended limits:
- **20 pages** = ~400-600 listings (5-10 minutes)
- **50 pages** = ~1,000-1,400 listings (15-25 minutes) ✅ Default
- **100 pages** = ~2,000-2,800 listings (30-50 minutes)
- **200 pages** = ~4,000+ listings (1-2 hours)

### Resume After Crash
If the scraper stops unexpectedly:
```bash
python scraper_v2.py  # Automatically resumes
```

It will detect saved progress and skip the URL collection phase.

### Stop Safely
Press **Ctrl+C** to stop. The scraper will:
1. Stop gracefully
2. Save all scraped data so far
3. Create `ustasi_listings_partial.json` and `ustasi_listings_partial.csv`

## Output Files

### During Scraping
- `scraper_progress.json` - Progress state (can resume)
- `ustasi_listings_temp.json` - Intermediate results (updated every 50 listings)

### After Completion
- `ustasi_listings.json` - Final JSON results
- `ustasi_listings.csv` - Final CSV results

### On Interruption
- `ustasi_listings_partial.json` - Partial JSON results
- `ustasi_listings_partial.csv` - Partial CSV results

## Performance Comparison

| Feature | V1 | V2 |
|---------|----|----|
| Page limit | None (infinite loop) | 50 (configurable) |
| Duplicate detection | No | Yes |
| Crash protection | No | Yes |
| Resume capability | No | Yes |
| Concurrent requests | 5 | 10 |
| Speed | Slow | 3-4x faster |
| Progress saving | No | Yes (every 50) |
| Timeout handling | Basic | Advanced |

## Troubleshooting

### "Too many requests" error
Reduce concurrency:
```python
await self.scrape_all_listings(urls, max_concurrent=5)  # Reduce from 10 to 5
```

### Want more listings
Increase page limit:
```python
scraper = UstasiScraperV2(max_pages=100)  # Increase from 50 to 100
```

### Scraper stops too early
Check the output - if it says "Detected pagination loop", the site is returning duplicate URLs.
This is normal behavior to prevent infinite loops.

### Want to start fresh
Delete progress file:
```bash
rm scraper_progress.json ustasi_listings_temp.json
python scraper_v2.py
```

## Comparison: scraper.py vs scraper_v2.py

| Use Case | Use This |
|----------|----------|
| Quick test (5 listings) | `test_scraper.py` |
| Old version (not recommended) | `scraper.py` |
| **Production use (recommended)** | **`scraper_v2.py`** ✅ |

## Why V2 is Better

1. **Won't get stuck** - Hard limits and duplicate detection
2. **Won't lose progress** - Saves and can resume
3. **Much faster** - 10 concurrent requests, shorter delays
4. **Safer** - Better error handling, timeout protection
5. **User-friendly** - Progress updates, clear status messages
6. **Configurable** - Easy to adjust speed and limits

## Recommended Settings

For most users:
```python
scraper = UstasiScraperV2(max_pages=50)  # Default - good balance
```

For small dataset:
```python
scraper = UstasiScraperV2(max_pages=20)  # Fast test
```

For complete scrape:
```python
scraper = UstasiScraperV2(max_pages=200)  # Full dataset
```
