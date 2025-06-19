import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from db_tools import DrugAgeDBTools
from plotting_tools import PlottingTools 
import os
import re
import pandas as pd
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="Longevity Research Agent",
    page_icon="🔬",
    layout="centered"
)

# --- Agent Definition ---
@st.cache_resource
def get_agent():
    """Initializes and returns the Agno agent. Cached for performance."""
    print("--- Initializing Agent ---")
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]

        # This agent's ONLY job is to return a well-formatted markdown string.
        # We have REMOVED the PlottingTools from its direct control.
        agent = Agent(
            model=Groq(id="llama3-70b-8192", api_key=groq_api_key),
            tools=[DrugAgeDBTools()], # Only has DB tool
            description="You are an expert data analyst and research assistant for the DrugAge database.",
            # --- NEW, MORE PRECISE INSTRUCTIONS FOR TABLE FORMATTING ---
            instructions=[
                "1. First, analyze the user's question and formulate a brief, one-sentence plan.",
                "2. Generate the exact SQL query needed. Choose relevant columns like `avg_lifespan_change_percent`.",
                "3. Use the `run_sql_query` tool to execute the query.",
                "4. **CRITICAL:** You MUST format the raw results from the tool into a perfect, clean markdown table. The table MUST have a header row with `|` separators and a separator line `| --- | --- |`. Example:",
                "    | compound_name | avg_lifespan_change_percent |",
                "    | :--- | :--- |",
                "    | Rapamycin | 22.9 |",
                "    | Acarbose | 22.0 |",
                "5. Provide a final, concluding text summary of the key findings.",
                "6. Combine all of these parts into a single, final markdown response. Use markdown headers (e.g., '### Plan', '### SQL Query', '### Results', '### Summary') to structure the response."
            ],
            markdown=True,
        )
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None

def extract_markdown_table(markdown_text):
    """
    Finds and extracts the first markdown table from a string.
    Returns the table as a string, ready for Pandas.
    """
    # Regex to find a markdown table
    match = re.search(r'(\|.*\|[\r\n]+)((?:\|.*\|[\r\n]?)+)', markdown_text)
    if match:
        # Combine header and body
        table_str = match.group(1) + match.group(2)
        # Clean up by removing leading/trailing whitespace from each line
        cleaned_table = "\n".join([line.strip() for line in table_str.strip().split('\n')])
        return cleaned_table
    return None

# --- Main App Logic ---
st.title("🔬 Longevity Research Agent")
st.caption("Ask me anything about the DrugAge database!")

if "agent" not in st.session_state:
    st.session_state.agent = get_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.agent:
    st.stop()

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Process new user input
if prompt := st.chat_input("e.g., Show top 5 drugs for mice"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("The agent is thinking and querying the database..."):
            # The agent returns a RunResponse object with a markdown string in .content
            response_object = st.session_state.agent.run(prompt)
            
            final_markdown = ""
            if hasattr(response_object, 'content') and isinstance(response_object.content, str):
                final_markdown = response_object.content
            else:
                st.error("The agent returned an unexpected response format.")
                st.write(response_object)

            # Display the full text response from the agent
            if final_markdown:
                st.markdown(final_markdown)
                st.session_state.messages.append({"role": "assistant", "content": final_markdown})

                # --- NEW PLOTTING LOGIC (Handled by Python, not the agent) ---
                table_string = extract_markdown_table(final_markdown)
                
                if table_string:
                    try:
                        # Convert the markdown table string to a DataFrame
                        # We use StringIO to treat the string as a file
                        df = pd.read_csv(io.StringIO(table_string), sep='|', index_col=1).dropna(axis=1, how='all').iloc[1:]
                        df.columns = [col.strip() for col in df.columns]

                        # Check if the DataFrame is suitable for plotting
                        if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                            st.write("### Chart Visualization")
                            plotter = PlottingTools()
                            # Use the first column for labels and the second for values
                            image_bytes = plotter.create_bar_chart(
                                data_string=df.to_string(),
                                x_col=df.columns[0], 
                                y_col=df.columns[1],
                                title="Query Results"
                            )
                            st.image(image_bytes, caption="A chart generated from the agent's results.")
                    except Exception as e:
                        st.warning(f"Could not generate a plot from the data. Error: {e}")

