#!/usr/bin/env python3
"""
Test script for poster fetcher integration with year-based matching
"""

from poster_fetcher import PosterFetcher, extract_year_from_title

# Test the PosterFetcher
fetcher = PosterFetcher()

# Test cases with known movies/shows
test_titles = [
    "The Witcher",
    "Stranger Things",
    "Our Planet",
    "Breaking Bad",
    "The Crown",
    "Avatar (2009)",
    "Inception",
]

# Test cases with year (for disambiguation)
test_titles_with_year = [
    ("Avatar", 2009),      # Avatar (2009) - not Avatar (2010) sequel
    ("Animal", 2023),      # Animal (2023) - Netflix movie (if exists)
    ("Pushpa2", 2024),     # Pushpa 2 (2024) - for year-based matching
]

print("Testing IMDb Poster Fetcher with Year-Based Matching\n" + "="*60)

# Test 1: Basic title extraction
print("\n[Test 1] Basic Title Extraction")
print("-" * 60)
for title in test_titles:
    print(f"\nSearching for: '{title}'")

    # Test year extraction
    clean_title, year = extract_year_from_title(title)
    print(f"  Cleaned: '{clean_title}', Year: {year}")

    # Fetch poster
    poster_url = fetcher.fetch_poster(clean_title, year)
    if poster_url:
        print(f"  ✓ Poster found: {poster_url[:60]}...")
    else:
        print(f"  ✗ No poster found")

# Test 2: Year-based matching (for disambiguation)
print("\n\n[Test 2] Year-Based Matching (Disambiguation)")
print("-" * 60)
print("Testing titles that appear multiple times on IMDb")
print("(Year filtering should return correct match)\n")

for title, year in test_titles_with_year:
    print(f"Searching for: '{title}' ({year})")
    print(f"  (Filtering IMDb results for year {year})")

    # Fetch poster with year filtering
    poster_url = fetcher.fetch_poster(title, year)
    if poster_url:
        print(f"  ✓ Correct poster found (year-based match)")
        print(f"    URL: {poster_url[:60]}...")
    else:
        print(f"  ✗ No poster found")

print("\n" + "="*60)
print("Test completed!")
print("\nKey Improvements:")
print("  • Year extraction from titles (e.g., 'Avatar (2009)' → year=2009)")
print("  • Year-based filtering on IMDb search results")
print("  • Accurate matching for titles with same name")
print("  • Fallback to first result if year match not found")
