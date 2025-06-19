import os
from sqlalchemy import create_engine, text
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DrugAgeDBTools:
    """A toolset for interacting with the DrugAge SQLite database."""

    def __init__(self):
        """Initializes the tool by setting up the database engine."""
        try:
            # Construct the path to the database file, assuming it's in a sibling 'data-prep' folder
            script_dir = os.path.dirname(os.path.abspath(__file__)) # agent-app directory
            project_root = os.path.dirname(script_dir) # repo directory
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
        """
        Executes a read-only SQL query against the DrugAge database and returns the result.
        
        Args:
            query: A syntactically correct SQLite query string to execute. 
                   Only SELECT statements are allowed.
        
        Returns:
            A string representation of the query result, or an error message if the query fails.
            The result will be formatted as a list of tuples.
        """
        if self.engine is None:
            return "Error: Database connection not initialized."

        # Security check: Basic protection against modification queries
        if not query.strip().lower().startswith('select'):
            return "Error: Only SELECT queries are allowed for security reasons."

        try:
            with self.engine.connect() as connection:
                logging.info(f"Executing query: {query}")
                result = connection.execute(text(query))
                rows = result.fetchall()
                
                if not rows:
                    return "Query executed successfully, but returned no results."
                
                # Convert list of Row objects to list of tuples for a clean string representation
                result_list = [tuple(row) for row in rows]
                logging.info(f"Query returned {len(result_list)} rows.")
                return str(result_list)
        except Exception as e:
            logging.error(f"Query failed: {query} | Error: {e}")
            return f"Error executing query: {e}"

# Example of how to use this tool (for testing purposes)
if __name__ == '__main__':
    print("--- Testing DrugAgeDBTools ---")
    db_tool = DrugAgeDBTools()
    
    # Test a valid query
    test_query = "SELECT compound_name, species FROM drug_data WHERE compound_name = 'Metformin' LIMIT 2;"
    result = db_tool.run_sql_query(test_query)
    print("\nTest Query Result:")
    print(result)

    # Test an invalid query
    invalid_query = "DROP TABLE drug_data;"
    result = db_tool.run_sql_query(invalid_query)
    print("\nInvalid Query Result:")
    print(result)
