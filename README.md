# RAG-Based Excel Q\&A Bot 🤖

Ever wished you could just *talk* to your Excel files? This project makes that possible\! It's a smart Q\&A application that lets you upload an Excel sheet (specifically with candidate recruiting data in this example) and ask complex questions about it in plain English.

Behind the scenes, it uses a powerful technique called Retrieval-Augmented Generation (RAG) combined with LangChain agents to understand your data and find the right answers. No more complex formulas or filtering—just ask, and get your answer.

-----

### \#\# ✨ Features

  * **Excel File Upload**: Easily upload your `.xlsx` or `.xls` files through a simple API endpoint.
  * **Intelligent Q\&A**: Ask complex questions like "What's the average salary for candidates with Python skills?" or "Find me candidates in Mumbai with over 5 years of experience."
  * **Powered by RAG**: Uses a vector store (FAISS) to perform quick and relevant semantic searches on your data.
  * **Smart LangChain Agents**: Employs LangChain agents with custom tools to intelligently decide how to find the answer. It can perform semantic searches, retrieve specific data, and even perform calculations like averages.
  * **FastAPI Backend**: Built on a modern, fast, and asynchronous web framework.

-----

### \#\# 🧠 How It Works

The magic happens in a few simple steps:

1.  **Upload & Ingest**: When you upload an Excel file, the application reads it using **Pandas**. It then processes each row, treating the 'Skills' column as the main content and the other columns (like 'Location', 'CTC', 'Exp') as metadata.
2.  **Vectorize**: The data is split into chunks and converted into numerical representations (embeddings) using **OpenAI's models**. These embeddings are stored in an in-memory **FAISS vector store**, which is like a super-fast library for your data.
3.  **Query & Retrieve**: When you ask a question, a **LangChain agent** kicks in. It analyzes your query and decides which custom tool to use:
      * `retrieve_documents`: For general questions about skills or candidates. It performs a similarity search on the vector store.
      * `get_all_ctc_values`: If you ask about salaries (like the average CTC), it uses this tool to grab all salary data for calculations.
      * `get_exp_locations`: If you ask for the locations of candidates with a specific experience level, this tool filters the original DataFrame to find them.
4.  **Generate Answer**: The agent takes the information gathered by the tools, passes it to a powerful language model (**GPT-4o**), and generates a human-readable answer for you.

-----

### \#\# 🛠️ Tech Stack

  * **Backend**: FastAPI & Uvicorn
  * **AI/ML**: LangChain, OpenAI (GPT-4o & Embeddings)
  * **Data Handling**: Pandas
  * **Vector Store**: FAISS (in-memory)

-----

### \#\# 🚀 Getting Started

Ready to try it out? Here’s how to get it running on your local machine.

#### **1. Prerequisites**

  * Python 3.8+
  * An OpenAI API Key

#### **2. Clone the Repository**

```bash
git clone https://github.com/your-username/rag_paywatch.git
cd rag_paywatch
```

#### **3. Install Dependencies**

It's a good practice to use a virtual environment.

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install the required packages
pip install -r requirements.txt
```

*(Note: You'll need to create a `requirements.txt` file from the imports in the Python scripts).*

#### **4. Set Up Environment Variables**

Create a `.env` file in the root directory of the project and add your API keys.

```env
OPENAI_API_KEY="your_openai_api_key_here"
API_KEY="your_secret_api_key_for_app_security"
CURRENCY_API_URL="your currency api key"
```

The `API_KEY` is a simple security measure to protect your endpoints.

-----

### \#\# ▶️ Running the Application

Once everything is set up, start the server with Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will now be running at `http://localhost:8000`.

-----

### \#\# 📡 API Endpoints

You can interact with the application using the following endpoints.

#### **1. Upload Excel File**

Upload your Excel file to be processed and stored in memory.

  * **URL**: `/upload-excel/`
  * **METHOD**: 'POST'
#### **2. Query Your Data**

Ask a question about the uploaded data.

  * **URL**: `/query/`
  * **Method**: `POST`


-----

### \#\# 🔮 Future Improvements

  * **Add a Frontend**: A simple Streamlit or React frontend would make the application more user-friendly.
  * **Support More File Types**: Extend functionality to support `.csv` and `.json` files.
  * **Persistent Storage**: Integrate a persistent vector database like ChromaDB or Pinecone so the data isn't lost when the server restarts.
  * **More Advanced Tools**: Create more sophisticated tools for data analysis and visualization.