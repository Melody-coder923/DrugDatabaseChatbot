import pandas as pd
import matplotlib.pyplot as plt
import io
import logging
import ast

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PlottingTools:
    """A class that provides tools for creating different types of plots."""

    def _prepare_data(self, data_string: str) -> pd.DataFrame | None:
        """Helper method to safely convert a string representation of a list of tuples into a DataFrame."""
        try:
            # Safely evaluate the string to a Python object
            data_list = ast.literal_eval(data_string)
            if not isinstance(data_list, list) or not all(isinstance(i, tuple) for i in data_list):
                raise ValueError("Data string is not a list of tuples.")
            
            # Dynamically determine column names if possible, otherwise use generic names
            num_cols = len(data_list[0]) if data_list else 0
            col_names = [f'column_{i+1}' for i in range(num_cols)]
            
            df = pd.DataFrame(data_list, columns=col_names)
            return df
        except (ValueError, SyntaxError, IndexError) as e:
            logging.error(f"Failed to parse data string for plotting: {e}")
            return None

    def create_bar_chart(self, data_string: str, x_col: str, y_col: str, title: str) -> bytes | str:
        """
        Creates a horizontal bar chart from data. 
        Use this for comparing a categorical column against a numerical column (e.g., top 5 drugs and their effect size).
        Args:
            data_string (str): A string that looks like a Python list of tuples, e.g., "[('Rapamycin', 22.9), ('Acarbose', 22.0)]".
            x_col (str): The name to assign to the first column (the labels on the y-axis).
            y_col (str): The name to assign to the second column (the values for the x-axis).
            title (str): The title for the chart.
        Returns:
            bytes: The PNG image data of the chart as bytes, or an error string.
        """
        logging.info(f"Attempting to create bar chart with title: {title}")
        df = self._prepare_data(data_string)
        if df is None:
            return "Error: Data for plotting was in an invalid format."

        # Rename columns based on agent's request
        df.columns = [x_col, y_col]

        # Ensure the value column is numeric
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce').fillna(0)
        
        # Sort for better visualization
        df = df.sort_values(by=y_col, ascending=True)

        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.barh(df[x_col], df[y_col], color='#4A90E2')
        
        ax.set_xlabel(y_col.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel(x_col.replace('_', ' ').title(), fontsize=12)
        ax.set_title(title, fontsize=16, weight='bold')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        
        logging.info("Bar chart created successfully.")
        return buf.getvalue()

    def create_scatter_plot(self, data_string: str, x_col: str, y_col: str, title: str) -> bytes | str:
        """
        Creates a scatter plot from data.
        Use this to visualize the relationship between two different numerical columns (e.g., avg_lifespan_change vs. max_lifespan_change).
        Args:
            data_string (str): A string that looks like a Python list of tuples, e.g., "[(10, 12), (15, 18)]".
            x_col (str): The name for the x-axis data.
            y_col (str): The name for the y-axis data.
            title (str): The title for the chart.
        Returns:
            bytes: The PNG image data of the chart as bytes, or an error string.
        """
        logging.info(f"Attempting to create scatter plot with title: {title}")
        df = self._prepare_data(data_string)
        if df is None:
            return "Error: Data for plotting was in an invalid format."

        df.columns = [x_col, y_col]
        df[x_col] = pd.to_numeric(df[x_col], errors='coerce').fillna(0)
        df[y_col] = pd.to_numeric(df[y_col], errors='coerce').fillna(0)

        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.scatter(df[x_col], df[y_col], alpha=0.7, color='#50E3C2')

        ax.set_xlabel(x_col.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel(y_col.replace('_', ' ').title(), fontsize=12)
        ax.set_title(title, fontsize=16, weight='bold')
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)

        logging.info("Scatter plot created successfully.")
        return buf.getvalue()

# Example of how to use this tool (for testing purposes)
if __name__ == '__main__':
    print("--- Testing PlottingTools ---")
    plotter = PlottingTools()
    
    # Test Bar Chart
    bar_data_str = "[('Rapamycin', 22.9), ('Acarbose', 22.0), ('17-alpha-estradiol', 19.0)]"
    bar_chart_bytes = plotter.create_bar_chart(bar_data_str, 'compound_name', 'avg_lifespan_change_percent', 'Test Bar Chart')
    if isinstance(bar_chart_bytes, bytes):
        with open("test_bar_chart.png", "wb") as f:
            f.write(bar_chart_bytes)
        print("-> Test bar chart saved to 'test_bar_chart.png'")

    # Test Scatter Plot
    scatter_data_str = "[(10, 12), (15, 18), (8, 9), (22, 21), (5, 7)]"
    scatter_plot_bytes = plotter.create_scatter_plot(scatter_data_str, 'avg_lifespan_change', 'max_lifespan_change', 'Test Scatter Plot')
    if isinstance(scatter_plot_bytes, bytes):
        with open("test_scatter_plot.png", "wb") as f:
            f.write(scatter_plot_bytes)
        print("-> Test scatter plot saved to 'test_scatter_plot.png'")
