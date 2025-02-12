import pandas as pd

# Read the CSV file
df = pd.read_csv('products_data.csv')

# Get the number of rows
num_entries = len(df)

print(f"Number of entries in products_data.csv: {num_entries}")


# Read the CSV file
df = pd.read_csv('products_data_v2.csv')

# Get the number of rows
num_entries = len(df)

print(f"Number of entries in products_data_v2.csv: {num_entries}")



# Read the CSV file
df = pd.read_csv('products_data_v2_reverseOrder.csv')

# Get the number of rows
num_entries = len(df)

print(f"Number of entries in products_data_v2_ReserverOrder.csv: {num_entries}")


