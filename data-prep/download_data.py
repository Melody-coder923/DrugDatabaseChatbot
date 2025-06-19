import pandas as pd
from sqlalchemy import create_engine, text
import os
import requests 
import zipfile   
import io        

# --- Configuration ---
CSV_URL = "https://genomics.senescence.info/drugs/dataset.zip"
DB_NAME = "drugage.sqlite"
TABLE_NAME = "drug_data"

def prepare_database():
    """
    Downloads, cleans, and loads the DrugAge dataset into an SQLite database.
    This function is idempotent: if the database already exists, it will not be recreated.
    """
    print("--- Starting Data Preparation ---")

    # --- 1. Check if the database already exists ---
    if os.path.exists(DB_NAME):
        print(f"Database '{DB_NAME}' already exists. Preparation skipped.")
        print("To re-create the database, please delete the file 'drugage.db'.")
        print("--- Data Preparation Complete ---")
        return

    try:
        # --- 2. Download and Load the Data using Pandas ---
        print(f"Downloading data from {CSV_URL}...")
        
        # Make an HTTP request to get the content of the ZIP file
        response = requests.get(CSV_URL)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Use BytesIO to treat the ZIP file content as a file in memory
        zip_file = io.BytesIO(response.content)

        # Use zipfile to open the archive and read the specific CSV file
        with zipfile.ZipFile(zip_file) as z:
            with z.open('drugage.csv') as f:
                df = pd.read_csv(f)

        print("Data downloaded successfully.")

        # --- 3. Clean and Standardize the Data ---
        print("Cleaning and standardizing data...")
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        print(f"Found {len(df)} records.")
        
        # --- 4. Create SQLite Database and Load Data ---
        print(f"Creating database '{DB_NAME}' and table '{TABLE_NAME}'...")
        engine = create_engine(f'sqlite:///{DB_NAME}')
        df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
        print(f"Data successfully loaded into '{TABLE_NAME}' table.")

        # --- 5. Verify the Data (Optional) ---
        print("Verifying data load...")
        with engine.connect() as connection:
            result = connection.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
            count = result.scalar()
            print(f"Verification successful: Found {count} rows in the database table.")

    except Exception as e:
        print(f"\nAn error occurred during data preparation: {e}")
        print("Please check your internet connection and permissions.")

    finally:
        print("--- Data Preparation Complete ---")


if __name__ == "__main__":
    prepare_database()