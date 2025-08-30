import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from .services.rag_service import RAGService
from .security.security_utils import get_api_key
from .models.schemas import UploadStatus, QueryRequest
import os
import re
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

app = FastAPI()

rag_service = RAGService()

@app.post("/upload-excel/", response_model=UploadStatus)
async def upload_excel_file(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    """
    Endpoint to upload and ingest an Excel file into the in-memory vector store.
    """
    if file.filename.endswith(('.xlsx', '.xls')):
        file_content = await file.read()
        if rag_service.ingest_data(file_content):
            return UploadStatus(message="Data ingested successfully!", index_name="in-memory-faiss")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to ingest data. Check file format or content."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an Excel (.xlsx, .xls) file."
        )

@app.post("/query/")
async def query_data(request: QueryRequest, api_key: str = Depends(get_api_key)):
    """
    Endpoint to query the RAG application and get a response.
    """
    try:
        agent_executor = rag_service.get_agent_executor()
        response = await agent_executor.ainvoke({"input": request.query})
        return {"answer": response["output"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)