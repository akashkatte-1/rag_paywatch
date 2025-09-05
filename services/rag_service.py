import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain.agents import tool, AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain import hub
import os
from langchain_core.messages import AIMessage, HumanMessage
import io
import re

# <-- 1. ADD THIS IMPORT 
# Assuming currency_service.py is in the same directory or accessible via path.
# If main.py, rag_service.py and currency_service.py are in the same folder, this import will fail. 
# Make sure your project structure is like:
# main.py
# - services/
#   - __init__.py
#   - rag_service.py
#   - currency_service.py
# Or adjust the import path accordingly. For example, 'from currency_service import get_exchange_rate'
# if it is in the same folder.
from .currency_service import get_exchange_rate


class RAGService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.vector_store = None
        self.docs = []
        self.df = None

    def ingest_data(self, file_content: bytes):
        """Processes the Excel file and ingests data into the in-memory vector store."""
        try:
            self.df = pd.read_excel(io.BytesIO(file_content))
            
            if 'Name' in self.df.columns:
                self.df = self.df.drop(columns=["Name"])
            
            docs = []
            for _, row in self.df.iterrows():
                metadata = {col: str(row[col]) for col in self.df.columns if col != 'Skills' and pd.notna(row[col])}
                page_content = str(row['Skills'])
                docs.append(Document(page_content=page_content, metadata=metadata))

            self.docs = self.text_splitter.split_documents(docs)
            
            self.vector_store = FAISS.from_documents(
                self.docs,
                self.embeddings
            )
            return True
        except Exception as e:
            print(f"Error ingesting data: {e}")
            return False

    def get_agent_executor(self):
        """
        Returns an agent executor with all the necessary tools.
        """
        if self.vector_store is None or self.df is None:
            raise Exception("Vector store is not initialized. Please ingest data first.")
        
        @tool
        def retrieve_documents(query: str) -> str:
            """
            This tool performs a semantic search on documents to find information about candidates' skills, experience, and location.
            Use this tool to answer questions about specific candidates or their qualifications.
            """
            # Determine requested number of results from query; default to 3 when unspecified
            requested_k = 3
            try:
                match = re.search(r"\b(?:top|first)\s*(\d+)\b", query, flags=re.IGNORECASE)
                if not match:
                    match = re.search(r"\b(\d+)\s*(?:results|records|candidates|items)\b", query, flags=re.IGNORECASE)
                if match:
                    requested_k = max(1, int(match.group(1)))
            except Exception:
                requested_k = 3

            results = self.vector_store.similarity_search(query, k=requested_k)
            return "\n".join([f"Skills: {doc.page_content}, Metadata: {doc.metadata}" for doc in results])
        
        @tool
        def get_all_ctc_values() -> str:
            """
            This tool retrieves all CTC values from the dataset.
            Use this to perform calculations like finding the average or total CTC.
            """
            try:
                ctc_series = pd.to_numeric(self.df['CTC'], errors='coerce').dropna()
                return ctc_series.to_json(orient='records')
            except Exception as e:
                return f"An error occurred while retrieving CTC data: {e}"
        
        @tool
        def get_exp_locations(experience: str) -> str:
            """
            This tool finds the locations of candidates with a specific amount of experience.
            Use this tool to answer questions about where candidates with a certain experience level are located.
            The 'experience' input should be an exact string, for example, '2y 6m'.
            """
            try:
                filtered_df = self.df[self.df['Exp'].astype(str) == experience]
                
                if filtered_df.empty:
                    return "No candidates found with that exact experience."
                
                locations = filtered_df['Location'].tolist()
                return f"The locations for candidates with {experience} of experience are: {', '.join(locations)}"
            except Exception as e:
                return f"An error occurred: {e}"

        @tool
        def ctc_query(query: str) -> str:
            """
            Parse a natural-language query to return candidates with lowest/highest CTC, with optional
            location filtering and respecting a requested top-N. Defaults to top 3 when not specified.

            Examples:
            - "lowest ctc in pune top 5"
            - "highest salary bangalore first 2 candidates"
            - "show 6 results of lowest ctc for hyderabad"
            """
            try:
                if 'CTC' not in self.df.columns:
                    return "CTC column not found in dataset."

                # Normalize CTC to numeric
                df_local = self.df.copy()
                df_local['CTC_numeric'] = pd.to_numeric(df_local['CTC'], errors='coerce')
                df_local = df_local.dropna(subset=['CTC_numeric'])

                # Determine order (lowest/highest)
                q_lower = query.lower()
                order = 'lowest' if any(w in q_lower for w in ['lowest', 'min', 'minimum', 'least']) else 'highest'

                # Determine top N (default 3)
                top_n = 3
                m = re.search(r"\b(?:top|first)\s*(\d+)\b", query, flags=re.IGNORECASE)
                if not m:
                    m = re.search(r"\b(\d+)\s*(?:results|records|candidates|items)\b", query, flags=re.IGNORECASE)
                if m:
                    try:
                        top_n = max(1, int(m.group(1)))
                    except Exception:
                        top_n = 3

                # Detect location by matching known locations present in the dataset
                location_value = None
                if 'Location' in df_local.columns:
                    unique_locations = [str(x) for x in df_local['Location'].dropna().unique().tolist()]
                    for loc in unique_locations:
                        if loc and str(loc).lower() in q_lower:
                            location_value = loc
                            break

                if location_value is not None:
                    df_local = df_local[df_local['Location'].astype(str).str.lower() == location_value.lower()]

                if df_local.empty:
                    return "No matching records found for the given criteria."

                df_sorted = df_local.sort_values('CTC_numeric', ascending=(order == 'lowest'))
                df_selected = df_sorted.head(top_n)

                # Select relevant columns to report back (all available except helper numeric)
                cols = [c for c in df_selected.columns if c != 'CTC_numeric']
                records = df_selected[cols].to_dict(orient='records')

                return {
                    'order': order,
                    'location': location_value,
                    'count': len(records),
                    'results': records
                }
            except Exception as e:
                return f"An error occurred while processing CTC query: {e}"

        # <-- 2. ADD THE get_exchange_rate TOOL TO THIS LIST
        tools = [retrieve_documents, get_all_ctc_values, get_exp_locations, ctc_query, get_exchange_rate]

        llm = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))
        
        # <-- 3. (RECOMMENDED) ENHANCED PROMPT
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """You are a helpful assistant with access to tools for analyzing candidate data from an Excel file.
- The data columns include: 'Skills', 'Exp' (experience, e.g., 2y 6m), 'Location', 'CTC', and 'Company'.
- IMPORTANT: All 'CTC' values in the source data are in Indian Rupees (INR).
- Your primary goal is to provide accurate answers based on this data.
- When a user asks about CTC or any monetary value, you MUST:
  1. Find the relevant CTC value in INR from the data.
  2. Use the 'get_exchange_rate' tool to get the conversion rate from 'INR' to 'USD'.
  3. Calculate the final value in USD.
  4. Provide INR figures in lakhs alongside USD conversion when relevant.
  5. For CTC-related questions that require lowest/highest or top-N results, prefer the 'ctc_query' tool. If only aggregate values are needed, you may use 'get_all_ctc_values'.
  6. Respect the user's requested number of results (e.g., top 5 or first 6). When unspecified, default to 3 results.
  7. Provide the final answer to the user ONLY in USD, clearly stating the currency, and you may include INR (lakhs) for reference."""),
                AIMessage(content="I'm ready to help. What is your question?"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        return agent_executor