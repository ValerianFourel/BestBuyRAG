import pandas as pd
import glob
import os

# Get all CSV files that start with 'all_products'
csv_files = glob.glob('../dataBestBuy/dataLakeBestBuy/all_products*.csv')

# Create empty list to store dataframes
dfs = []

# Read each CSV file
for file in csv_files:
    df = pd.read_csv(file,
                     quoting=1,
                     escapechar='\\',
                     on_bad_lines='skip',
                     encoding='utf-8',
                     delimiter=',',
                     dtype=str)  # Read all columns as strings initially

    print(f"File {file} shape: {df.shape}")
    dfs.append(df)

# Merge all dataframes
merged_df = pd.concat(dfs, ignore_index=True)
merged_df = merged_df.drop_duplicates()

print(f"Final merged shape: {merged_df.shape}")

# Create datawarehouse directory if it doesn't exist
os.makedirs('../datawarehouse', exist_ok=True)

# Save as parquet in datawarehouse folder
merged_df.to_parquet('../dataBestBuy/datawarehouse/merged_products_reviews_All.parquet')
print("Successfully saved as parquet file")
