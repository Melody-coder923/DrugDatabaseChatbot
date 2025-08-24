import streamlit as st
from agno.agent import Agent
from agno.models.groq import Groq
from db_tools import DrugAgeDBTools
from plotting_tools import PlottingTools
import pandas as pd
import io
import re
from agno.memory.v2 import Memory
# --- 页面配置 ---
st.set_page_config(
    page_title="Longevity Research Agent",
    page_icon="🔬",
    layout="centered"
)

# --- Agent 初始化 ---
@st.cache_resource
def get_agent():
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        agent = Agent(
            model=Groq(id="llama3-70b-8192", api_key=groq_api_key),
            tools=[DrugAgeDBTools()],
            description="You are an expert data analyst and research assistant for the DrugAge database.",
            instructions=[
                "1. Analyze the user's question and formulate a brief, one-sentence plan.",
                "2. Generate the exact SQL query needed.",
                "3. Use `run_sql_query` tool to execute it.",
                "4. Format results into a clean markdown table.",
                "5. Summarize key findings in text.",
                "6. Structure output using markdown headers."
            ],
            markdown=True,
            memory=Memory(),
            add_history_to_messages=True,
            num_history_runs=30,
        )
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        return None
user_1_id = "user_101"
user_1_session_id = "session_101"
# --- 提取第一个 markdown 表格 ---
def extract_markdown_table(markdown_text):
    match = re.search(r'(\|.*\|[\r\n]+)((?:\|.*\|[\r\n]?)+)', markdown_text)
    if match:
        table_str = match.group(1) + match.group(2)
        cleaned_table = "\n".join([line.strip() for line in table_str.strip().split('\n')])
        return cleaned_table
    return None

# --- 缓存支持的关键词 ---
@st.cache_data
def get_supported_keywords():
    db_tool = DrugAgeDBTools()
    return {
        "species": [s.lower() for s in db_tool.get_unique_values("species")],
        "value_type": [v.lower() for v in db_tool.get_unique_values("value_type")],
    }

# --- 更新用户上下文 ---
def update_user_context(prompt, supported_species, supported_value_types, session_state):
    lower_prompt = prompt.lower()

    # 默认值（确保一定有）
    if "species" not in session_state["user_settings"]:
        session_state["user_settings"]["species"] = "mice"
    if "value_type" not in session_state["user_settings"]:
        session_state["user_settings"]["value_type"] = "average"

    # 发现提示中有对应关键词，更新状态
    for s in supported_species:
        if s in lower_prompt:
            session_state["user_settings"]["species"] = s
            break
    for v in supported_value_types:
        if v in lower_prompt:
            session_state["user_settings"]["value_type"] = v
            break

# --- 应用入口 ---
st.title("🔬 Longevity Research Agent")
st.caption("Ask me anything about the DrugAge database!")

if "agent" not in st.session_state:
    st.session_state.agent = get_agent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_settings" not in st.session_state:
    st.session_state.user_settings = {}

if not st.session_state.agent:
    st.stop()

# 展示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 处理新输入
if prompt := st.chat_input("e.g., Show top 5 drugs for mice"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("The agent is thinking and querying the database..."):

            # 更新上下文
            SUPPORTED_KEYWORDS = get_supported_keywords()
            update_user_context(prompt, SUPPORTED_KEYWORDS["species"], SUPPORTED_KEYWORDS["value_type"], st.session_state)

            user_settings = st.session_state.user_settings
            species = user_settings.get("species", "mice")
            value_type = user_settings.get("value_type", "average")

            augmented_prompt = f"""
You are analyzing lifespan interventions in DrugAge.
Use species: **{species}**, and value type: **{value_type}** (e.g. lifespan change % based on {value_type}).
Unless the user says otherwise, always use these values.

User question: {prompt}
"""

            # 让 agent 运行
            response_object = st.session_state.agent.run(
                                                            augmented_prompt,
                                                            session_id=user_1_session_id,
                                                            user_id=user_1_id)

            final_markdown = ""
            if hasattr(response_object, 'content') and isinstance(response_object.content, str):
                final_markdown = response_object.content
            else:
                st.error("The agent returned an unexpected response format.")
                st.write(response_object)

            if final_markdown:
                st.markdown(final_markdown)
                st.session_state.messages.append({"role": "assistant", "content": final_markdown})

                # 试图提取表格并绘图
                table_string = extract_markdown_table(final_markdown)
                if table_string:
                    try:
                        df = pd.read_csv(io.StringIO(table_string), sep='|', index_col=1).dropna(axis=1, how='all').iloc[1:]
                        df.columns = [col.strip() for col in df.columns]
                        if len(df.columns) >= 2 and pd.api.types.is_numeric_dtype(df[df.columns[1]]):
                            st.write("### Chart Visualization")
                            plotter = PlottingTools()
                            image_bytes = plotter.create_bar_chart(
                                data_string=df.to_string(),
                                x_col=df.columns[0],
                                y_col=df.columns[1],
                                title="Query Results"
                            )
                            st.image(image_bytes, caption="A chart generated from the agent's results.")
                    except Exception as e:
                        st.warning(f"Could not generate a plot from the data. Error: {e}")