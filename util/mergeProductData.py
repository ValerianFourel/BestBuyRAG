import pandas as pd
import glob
import os

# Get all CSV files that start with 'products_data'
csv_files = glob.glob('../dataBestBuy/dataLakeBestBuy/products_data*.csv')

# Print the files found to debug
print(f"Found files: {csv_files}")

# Check if any files were found
if not csv_files:
    raise FileNotFoundError("No files matching 'products_data*.csv' were found in '../dataBestBuy/' directory")

# Create empty list to store dataframes
dfs = []

# Read each CSV file
for file in csv_files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        print(f"File {file} shape: {df.shape}")
        dfs.append(df)
    else:
        print(f"File not found: {file}")

# Check if any dataframes were loaded
if not dfs:
    raise ValueError("No dataframes were created from the files")

# Merge all dataframes and remove duplicates
merged_df = pd.concat(dfs, ignore_index=True)
merged_df = merged_df.drop_duplicates()
print(f"Original merged shape: {merged_df.shape}")
print(f"Shape after removing duplicates: {merged_df.shape}")

# Create datawarehouse directory if it doesn't exist
os.makedirs('../datawarehouse', exist_ok=True)

# Save as parquet in datawarehouse folder
merged_df.to_parquet('../dataBestBuy/datawarehouse/products_data_All.parquet')
print("Successfully saved as parquet file")