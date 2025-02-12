import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Read the parquet file
df = pd.read_parquet('dataBestBuy/merged_products_reviews_All.parquet')

# Print column names
print("Column names:")
for i, column in enumerate(df.columns):
    print(f"{i}. {column}")

# Get value counts
value_counts = df.iloc[:, 0].value_counts()

# Print summary statistics
print(f"Total unique values: {len(value_counts)}")
print(f"Total rows: {len(df)}")
print(f"\nMost common values (top 10):")
print(value_counts.head(10))
print(f"\nLeast common values (bottom 10):")
print(value_counts.tail(10))
print(f"\nDescriptive statistics of counts:")
print(value_counts.describe())


# Convert columns to numeric, replacing non-numeric values with NaN
df['helpful_count'] = pd.to_numeric(df['helpful_count'], errors='coerce')
df['unhelpful_count'] = pd.to_numeric(df['unhelpful_count'], errors='coerce')

# Get basic statistics for both columns
print("Helpful Count Statistics:")
print(df['helpful_count'].describe())
print("\nUnhelpful Count Statistics:")
print(df['unhelpful_count'].describe())

# Create a figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Plot helpful_count distribution
sns.histplot(data=df, x='helpful_count', ax=ax1)
ax1.set_title('Distribution of Helpful Counts')
ax1.set_xlabel('Helpful Count')
ax1.set_ylabel('Frequency')

# Plot unhelpful_count distribution
sns.histplot(data=df, x='unhelpful_count', ax=ax2)
ax2.set_title('Distribution of Unhelpful Counts')
ax2.set_xlabel('Unhelpful Count')
ax2.set_ylabel('Frequency')

plt.tight_layout()
# Save the distribution plots
plt.savefig('helpful_unhelpful_distributions.png', dpi=300, bbox_inches='tight')
plt.close()

# Create scatter plot
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='helpful_count', y='unhelpful_count', alpha=0.5)
plt.title('Helpful vs Unhelpful Counts')
plt.xlabel('Helpful Count')
plt.ylabel('Unhelpful Count')
# Save the scatter plot
plt.savefig('helpful_vs_unhelpful_scatter.png', dpi=300, bbox_inches='tight')
plt.close()

# Print value counts for small numbers (0-5) to see common patterns
print("\nMost common helpful count values:")
print(df['helpful_count'].value_counts().head(10))
print("\nMost common unhelpful count values:")
print(df['unhelpful_count'].value_counts().head(10))

# Calculate correlation
correlation = df['helpful_count'].corr(df['unhelpful_count'])
print(f"\nCorrelation between helpful and unhelpful counts: {correlation:.3f}")


