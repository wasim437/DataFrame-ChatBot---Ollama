import pandas as pd
import streamlit as st
from langchain.agents import AgentType
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_ollama import ChatOllama
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit web app configuration
st.set_page_config(
    page_title="DF Chat",
    page_icon="💬",
    layout="centered"
)

def read_data(file):
    """Reads CSV or Excel files into pandas DataFrame."""
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

# Streamlit page title
st.title("🤖 DataFrame ChatBot - Ollama")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Initialize dataframe
if "df" not in st.session_state:
    st.session_state.df = None

# File upload widget
uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls"])

if uploaded_file:
    # Read data and store it in session state
    st.session_state.df = read_data(uploaded_file)
    st.write("DataFrame Preview:")
    st.dataframe(st.session_state.df.head())

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input field for user's message
user_prompt = st.chat_input("Ask about your DataFrame...")

if user_prompt:
    # Add user's message to chat history and display it
    st.chat_message("user").markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # Check if dataframe is loaded before proceeding
    if st.session_state.df is not None:
        # Load the LLM
        llm = ChatOllama(model="gemma:2b", temperature=0)

        # Create the pandas dataframe agent
        pandas_df_agent = create_pandas_dataframe_agent(
            llm,
            st.session_state.df,
            verbose=True,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            allow_dangerous_code=True
        )

        # Invoke the agent with the user prompt
        try:
            response = pandas_df_agent.invoke(user_prompt)
            assistant_response = response["output"]

            # Save the assistant's message to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

            # Display assistant's response
            with st.chat_message("assistant"):
                st.markdown(assistant_response)

            # Generate a simple plot based on DataFrame (only if the user mentions "plot")
            if "plot" in user_prompt.lower():
                fig, ax = plt.subplots(figsize=(8, 6))
                st.write("Generating Graph...")

                # You could modify this logic to ask the user for specific columns, for now, it's just the first two columns.
                if len(st.session_state.df.columns) >= 2:
                    sns.barplot(x=st.session_state.df.columns[0], y=st.session_state.df.columns[1], data=st.session_state.df, ax=ax)
                    st.pyplot(fig)
                else:
                    st.write("Not enough columns to generate a plot. Please upload a DataFrame with at least two columns.")

        except Exception as e:
            # Handle any exceptions and display a friendly error message
            st.session_state.chat_history.append({"role": "assistant", "content": f"Error: {str(e)}"})
            with st.chat_message("assistant"):
                st.markdown(f"Error: {str(e)}")
    else:
        # If no DataFrame is loaded, show a message to the user
        st.chat_message("assistant").markdown("Please upload a CSV or Excel file first to query the DataFrame.")
