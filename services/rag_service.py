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
            results = self.vector_store.similarity_search(query, k=3)
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
                # Filter the DataFrame for the exact experience string
                filtered_df = self.df[self.df['Exp'].astype(str) == experience]
                
                if filtered_df.empty:
                    return "No candidates found with that exact experience."
                
                locations = filtered_df['Location'].tolist()
                return f"The locations for candidates with {experience} of experience are: {', '.join(locations)}"
            except Exception as e:
                return f"An error occurred: {e}"

        tools = [retrieve_documents, get_all_ctc_values, get_exp_locations]

        llm = ChatOpenAI(temperature=0, model="gpt-4o", openai_api_key=os.getenv("OPENAI_API_KEY"))
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant whi can give answers based on provided excel data with access to tools. Your goal is to provide accurate answers to the user's questions based in given excel data. Use the tools when necessary. and do calculations if required. If you need to convert currency, use the get_exchange_rate tool. and provide the final answer in USD currency. Be aware about all the columns in the data: Skills, Exp (y means years, m means months e.g 2y 2m) means experiance, Location, CTC, Company search for result in these columns.and give accurate answers."),
                AIMessage(content="I'm ready to help. What is your question?"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        return agent_executor
    
    
    