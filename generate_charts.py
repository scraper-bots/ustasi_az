"""
Ustasi.az Data Analysis and Visualization
This script generates insightful charts from the scraped listing data.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import os

# Set style for better-looking charts
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create charts directory if it doesn't exist
os.makedirs('charts', exist_ok=True)

# Load the data
print("Loading data...")
df = pd.read_csv('ustasi_listings.csv')
print(f"Loaded {len(df)} listings")

# Configure matplotlib for better display
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10

# 1. TOP SERVICE CATEGORIES
print("\n1. Generating service categories chart...")
categories_all = []
for cat in df['categories'].dropna():
    categories_all.extend([c.strip() for c in str(cat).split(',')])

category_counts = Counter(categories_all)
top_categories = dict(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:15])

plt.figure(figsize=(14, 7))
bars = plt.barh(list(top_categories.keys()), list(top_categories.values()), color='#3498db')
plt.xlabel('Number of Listings', fontsize=12, fontweight='bold')
plt.ylabel('Service Category', fontsize=12, fontweight='bold')
plt.title('Top 15 Service Categories on Ustasi.az', fontsize=14, fontweight='bold', pad=20)
plt.gca().invert_yaxis()

# Add value labels on bars
for i, (bar, value) in enumerate(zip(bars, top_categories.values())):
    plt.text(value + 2, bar.get_y() + bar.get_height()/2,
             str(value), va='center', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/top_service_categories.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/top_service_categories.png")
plt.close()

# 2. LOCATION DISTRIBUTION (BAR CHART)
print("\n2. Generating location distribution chart...")
location_counts = df['location'].value_counts()

plt.figure(figsize=(12, 7))
colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12'][:len(location_counts)]
bars = plt.bar(location_counts.index, location_counts.values, color=colors, edgecolor='black', linewidth=1.5)
plt.xlabel('Location', fontsize=12, fontweight='bold')
plt.ylabel('Number of Listings', fontsize=12, fontweight='bold')
plt.title('Geographic Distribution of Service Listings', fontsize=14, fontweight='bold', pad=20)
plt.xticks(rotation=45, ha='right')
plt.ylim(0, max(location_counts.values) * 1.1)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}\n({height/len(df)*100:.1f}%)',
             ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('charts/location_distribution.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/location_distribution.png")
plt.close()

# 3. PRICE AVAILABILITY
print("\n3. Generating price availability chart...")
has_price = df['price'].notna() & (df['price'] != '')
price_data = {
    'With Price': has_price.sum(),
    'Without Price': (~has_price).sum()
}

plt.figure(figsize=(10, 7))
colors_price = ['#2ecc71', '#e74c3c']
bars = plt.bar(price_data.keys(), price_data.values(), color=colors_price, edgecolor='black', linewidth=1.5)
plt.ylabel('Number of Listings', fontsize=12, fontweight='bold')
plt.title('Price Information Availability', fontsize=14, fontweight='bold', pad=20)
plt.ylim(0, max(price_data.values()) * 1.15)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}\n({height/len(df)*100:.1f}%)',
             ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig('charts/price_availability.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/price_availability.png")
plt.close()

# 4. LISTING ACTIVITY OVER TIME
print("\n4. Generating activity timeline chart...")
df['date_clean'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
date_counts = df['date_clean'].dt.to_period('D').value_counts().sort_index()

plt.figure(figsize=(14, 6))
date_counts.plot(kind='line', color='#3498db', linewidth=2, marker='o', markersize=4)
plt.xlabel('Date', fontsize=12, fontweight='bold')
plt.ylabel('Number of Listings', fontsize=12, fontweight='bold')
plt.title('Daily Listing Activity on Ustasi.az', fontsize=14, fontweight='bold', pad=20)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('charts/listing_activity_timeline.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/listing_activity_timeline.png")
plt.close()

# 5. TOP MAIN CATEGORIES (First category only)
print("\n5. Generating main categories distribution chart...")
df['main_category'] = df['categories'].str.split(',').str[0].str.strip()
main_cat_counts = df['main_category'].value_counts().head(10)

plt.figure(figsize=(12, 7))
colors_gradient = plt.cm.viridis(range(len(main_cat_counts)))
bars = plt.bar(range(len(main_cat_counts)), main_cat_counts.values,
               color=colors_gradient, edgecolor='black', linewidth=1.5)
plt.xticks(range(len(main_cat_counts)), main_cat_counts.index, rotation=45, ha='right')
plt.ylabel('Number of Listings', fontsize=12, fontweight='bold')
plt.title('Top 10 Main Service Categories', fontsize=14, fontweight='bold', pad=20)

# Add value labels on bars
for i, (bar, value) in enumerate(zip(bars, main_cat_counts.values)):
    plt.text(bar.get_x() + bar.get_width()/2., value,
             str(value), ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('charts/main_categories_distribution.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/main_categories_distribution.png")
plt.close()

# 6. PROVIDER BRANDING & IDENTITY
print("\n6. Generating provider branding chart...")
with_identity = (df['user_name'].notna() & (df['user_name'] != '')).sum()
anonymous = (~(df['user_name'].notna() & (df['user_name'] != ''))).sum()

user_data = {
    'Branded Providers\n(Public Identity)': with_identity,
    'Anonymous Providers\n(No Public Identity)': anonymous
}

plt.figure(figsize=(12, 7))
colors_user = ['#27ae60', '#95a5a6']  # Green for branded, gray for anonymous
bars = plt.bar(user_data.keys(), user_data.values(), color=colors_user,
               edgecolor='black', linewidth=2, alpha=0.85)
plt.ylabel('Number of Service Providers', fontsize=13, fontweight='bold')
plt.title('Provider Branding Strategy: Identity vs Anonymity', fontsize=15, fontweight='bold', pad=20)
plt.ylim(0, max(user_data.values()) * 1.15)

# Add value labels on bars with insights
for i, bar in enumerate(bars):
    height = bar.get_height()
    percentage = height/len(df)*100

    # Main count and percentage
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)} providers\n({percentage:.1f}%)',
             ha='center', va='bottom', fontweight='bold', fontsize=12)

    # Add insight label
    if i == 0:
        insight = "Brand Building\nOpportunity"
    else:
        insight = "Market\nMajority"
    plt.text(bar.get_x() + bar.get_width()/2., height * 0.5,
             insight, ha='center', va='center',
             fontsize=10, style='italic', color='white', fontweight='bold')

# Add a subtle grid
plt.grid(axis='y', alpha=0.2, linestyle='--')

plt.tight_layout()
plt.savefig('charts/user_info_availability.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/user_info_availability.png")
plt.close()

# 7. MONTHLY ACTIVITY COMPARISON
print("\n7. Generating monthly activity comparison chart...")
monthly_counts = df['date_clean'].dt.to_period('M').value_counts().sort_index()

plt.figure(figsize=(10, 7))
bars = plt.bar([str(m) for m in monthly_counts.index], monthly_counts.values,
               color=['#3498db', '#e74c3c'][:len(monthly_counts)],
               edgecolor='black', linewidth=1.5)
plt.xlabel('Month', fontsize=12, fontweight='bold')
plt.ylabel('Number of Listings', fontsize=12, fontweight='bold')
plt.title('Monthly Listing Activity', fontsize=14, fontweight='bold', pad=20)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             str(int(height)), ha='center', va='bottom', fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig('charts/monthly_activity.png', dpi=300, bbox_inches='tight')
print("   ✓ Saved: charts/monthly_activity.png")
plt.close()

print("\n" + "="*60)
print("✓ All charts generated successfully!")
print("="*60)
print(f"\nTotal charts created: 7")
print("Location: ./charts/")
print("\nGenerated files:")
print("  1. top_service_categories.png")
print("  2. location_distribution.png")
print("  3. price_availability.png")
print("  4. listing_activity_timeline.png")
print("  5. main_categories_distribution.png")
print("  6. user_info_availability.png")
print("  7. monthly_activity.png")
