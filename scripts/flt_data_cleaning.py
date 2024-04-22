import pandas as pd
import numpy as np
import os
import re
from scipy.stats import zscore

def read_ict_file_with_header_info(file_path):
    try:
        with open(file_path, 'r') as file:
            first_line = file.readline().strip()
            first_row, last_row = map(int, first_line.split(','))
        skiprows = first_row - 1
        nrows = last_row - first_row + 1
        df = pd.read_csv(file_path, sep=',', skiprows=skiprows, nrows=nrows)
        df.replace(-9999.0, np.nan, inplace=True)  # Replace -9999.0 with NaN to indicate missing values
        return df
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of an error

data_dir = 'data/'
all_flights_merged_df = pd.DataFrame()

for flt_folder in next(os.walk(data_dir))[1]:
    flt_number = re.sub("[^0-9]", "", flt_folder)  # Extract the numeric part of the flight number
    
    flt_path = os.path.join(data_dir, flt_folder)
    dfs = {}
    filenames = {
        'JNO2': f'JNO2_N57_{flt_number}_RA.ict',
        'NOxCaRD': f'NOxCaRD_N57_{flt_number}_R0.ict',
        'NOAAPicarro': f'NOAAPicarro-CO2-CH4-CO-H2O_N57_{flt_number}_R0.ict',
        'FlightData': f'FlightData_N57_{flt_number}_RA.ict'
    }

    for key, filename in filenames.items():
        file_path = os.path.join(flt_path, filename)
        df = read_ict_file_with_header_info(file_path)
        # Remove any empty spaces in column headers
        df.columns = df.columns.str.strip()
        if not df.empty:
            dfs[key] = df

    merged_df = None
    for key, df in dfs.items():
        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.merge(merged_df, df, on='TO_Time_UTC', how='outer')

    if merged_df is not None:
        # Remove rows without geospatial data
        geospacial_columns = ['GPSAlt', 'GPSLat', 'GPSLon']
        merged_df = merged_df.dropna(subset=geospacial_columns)
        
        merged_df['Flight_Number'] = flt_number  # Add the flight number
        
        all_flights_merged_df = pd.concat([all_flights_merged_df, merged_df], ignore_index=True)

all_flights_merged_df.sort_values(by=['Flight_Number', 'TO_Time_UTC'], inplace=True)
all_flights_merged_df.to_csv('all_flights_merged_data.csv', index=False)



# Normalization of the data 
# List of columns you want to normalize. Adjust the column names as per your DataFrame.
columns_to_normalize = ['CO2_ppm', 'CH4_ppb', 'CO_ppb', 'H2O_pct', 'NO_ppbv', 'NO2_ppbv', 'NOy_ppbv', 'O3_ppbv', 'NOx_ppbv', 'Ox_ppbv']

# Apply Z-score normalization
for col in columns_to_normalize:
    if col in all_flights_merged_df.columns:  # Check if the column exists in the DataFrame
        all_flights_merged_df[col + '_zscore'] = zscore(all_flights_merged_df[col].dropna())

# Note: The .dropna() method is used to exclude NaN values from the calculation, as zscore does not handle NaNs by default.
# The normalized values are stored in new columns with '_zscore' appended to the original column names.

# List of specific columns to retain along with normalized columns
specific_columns_to_keep = ['GPSLat', 'GPSLon', 'GPSAlt', 'AmbTemp']

# Create a list of normalized column names with '_zscore' suffix
normalized_columns = [f"{col}_zscore" for col in columns_to_normalize if f"{col}_zscore" in all_flights_merged_df.columns]

# Combine the specific columns to keep with the normalized columns
columns_to_keep = specific_columns_to_keep + normalized_columns

# Create a new DataFrame with only these columns
norm_all_flights_df = all_flights_merged_df[columns_to_keep]

norm_all_flights_df.to_csv('norm_all_flights_merged_data.csv', index=False)