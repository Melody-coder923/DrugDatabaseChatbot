import os
from sqlalchemy import create_engine, inspect

# --- Configuration ---
DB_NAME = "drugage.sqlite"
EXPECTED_TABLE = "drug_data"

def verify_database_schema():
    """
    Connects to the SQLite database and verifies its contents.
    - Checks if the database file exists.
    - Lists all tables found in the database.
    - Checks if our expected table exists.
    """
    print("--- Starting Database Verification ---")

    # --- 1. Check if the database file exists ---
    if not os.path.exists(DB_NAME):
        print(f"Error: Database file '{DB_NAME}' not found.")
        print("Please run the 'prepare_data.py' script first.")
        return

    try:
        # --- 2. Connect to the database ---
        engine = create_engine(f'sqlite:///{DB_NAME}')
        
        # Use the inspector to get schema information
        inspector = inspect(engine)

        # --- 3. Get and print the list of tables ---
        tables = inspector.get_table_names()
        print(f"Found tables: {tables}")

        # --- 4. Verify our specific table exists ---
        if EXPECTED_TABLE in tables:
            print(f"Success: The table '{EXPECTED_TABLE}' was found.")
            
            # --- Bonus: Let's inspect the columns too ---
            print(f"Columns in '{EXPECTED_TABLE}':")
            columns = inspector.get_columns(EXPECTED_TABLE)
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")

        else:
            print(f"Error: The expected table '{EXPECTED_TABLE}' was NOT found.")

    except Exception as e:
        print(f"\nAn error occurred during verification: {e}")

    finally:
        print("--- Database Verification Complete ---")


if __name__ == "__main__":
    verify_database_schema()
