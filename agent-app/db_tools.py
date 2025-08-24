import os
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DrugAgeDBTools:
    """A toolset for interacting with the DrugAge SQLite database."""

    def __init__(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            db_path = os.path.join(project_root, 'data-prep', 'drugage.sqlite')
            logging.info(f"Connecting to database at: {db_path}")
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database not found at {db_path}. Please run the data preparation script.")
            self.engine = create_engine(f'sqlite:///{db_path}')
            logging.info("Database engine created successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize database engine: {e}")
            self.engine = None

    def run_sql_query(self, query: str) -> str:
        if self.engine is None:
            return "Error: Database connection not initialized."
        if not query.strip().lower().startswith('select'):
            return "Error: Only SELECT queries are allowed for security reasons."
        try:
            with self.engine.connect() as connection:
                logging.info(f"Executing query: {query}")
                result = connection.execute(text(query))
                rows = result.fetchall()
                if not rows:
                    return "Query executed successfully, but returned no results."
                result_list = [tuple(row) for row in rows]
                logging.info(f"Query returned {len(result_list)} rows.")
                return str(result_list)
        except Exception as e:
            logging.error(f"Query failed: {query} | Error: {e}")
            return f"Error executing query: {e}"

    def get_unique_values(self, column_name: str) -> list:
        """
        从 drug_data 表中获取指定列的唯一值。
        """
        allowed_columns = ["species", "value_type"]
        if column_name not in allowed_columns:
            raise ValueError(f"Column '{column_name}' not supported.")

        query = f"SELECT DISTINCT {column_name} FROM drug_data"
        if self.engine is None:
            raise RuntimeError("Database engine not initialized.")

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                return [row[0] for row in rows if row[0] is not None]
        except Exception as e:
            logging.error(f"Failed to fetch distinct values from {column_name}: {e}")
            return []

if __name__ == '__main__':
    print("--- Testing DrugAgeDBTools ---")
    db_tool = DrugAgeDBTools()

    test_query = "SELECT compound_name, species FROM drug_data WHERE compound_name = 'Metformin' LIMIT 2;"
    result = db_tool.run_sql_query(test_query)
    print("\nTest Query Result:")
    print(result)

    invalid_query = "DROP TABLE drug_data;"
    result = db_tool.run_sql_query(invalid_query)
    print("\nInvalid Query Result:")
    print(result)

    # 测试 get_unique_values
    print("\nUnique species values:")
    print(db_tool.get_unique_values("species"))

    print("\nUnique value_type values:")
    print(db_tool.get_unique_values("value_type"))