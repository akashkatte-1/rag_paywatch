import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from services.rag_service import RAGService
from services.logging_service import LoggingService
from security.security_utils import get_api_key
from security.logging_utils import hash_api_key, extract_user_id_from_api_key, get_request_metadata
from models.schemas import UploadStatus, QueryRequest
import os
import re
import time
from langchain_openai import ChatOpenAI
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage

app = FastAPI()

rag_service = RAGService()
logging_service = LoggingService()

@app.post("/upload-excel/", response_model=UploadStatus)
async def upload_excel_file(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    """
    Endpoint to upload and ingest an Excel file into the in-memory vector store.
    """
    # Extract user information for logging
    api_key_hash = hash_api_key(api_key)
    user_id = extract_user_id_from_api_key(api_key)
    
    try:
        if file.filename.endswith(('.xlsx', '.xls')):
            file_content = await file.read()
            file_size = len(file_content)
            
            # Log file upload attempt
            logging_service.log_file_upload(
                filename=file.filename,
                file_size=file_size,
                success=True,
                user_id=user_id,
                api_key_hash=api_key_hash
            )
            try:
                if rag_service.ingest_data(file_content):
                return UploadStatus(message="Data ingested successfully!", index_name="in-memory-faiss")
            except Exception as e :
                return
            # else:
            #     error_msg = "Failed to ingest data. Check file format or content."
            #     logging_service.log_error(
            #         error_message=error_msg,
            #         error_type="ingestion_error",
            #         user_id=user_id,
            #         api_key_hash=api_key_hash,
            #         additional_data={"filename": file.filename, "file_size": file_size}
            #     )
            #     raise HTTPException(
            #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            #         detail=error_msg
            #     )
        else:
            error_msg = "Invalid file type. Please upload an Excel (.xlsx, .xls) file."
            logging_service.log_error(
                error_message=error_msg,
                error_type="invalid_file_type",
                user_id=user_id,
                api_key_hash=api_key_hash,
                additional_data={"filename": file.filename}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except HTTPException:
        # Re-raise HTTP exceptions as they're already handled
        raise
    except Exception as e:
        # Log unexpected errors
        logging_service.log_error(
            error_message=str(e),
            error_type="unexpected_error",
            user_id=user_id,
            api_key_hash=api_key_hash,
            additional_data={"filename": file.filename if file else "unknown"}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@app.post("/query/")
async def query_data(request: QueryRequest, api_key: str = Depends(get_api_key)):
    """
    Endpoint to query the RAG application and get a response.
    """
    # Extract user information for logging
    api_key_hash = hash_api_key(api_key)
    user_id = extract_user_id_from_api_key(api_key)
    
    # Log the user query
    logging_service.log_query(
        query=request.query,
        user_id=user_id,
        api_key_hash=api_key_hash,
        additional_data=get_request_metadata({"query": request.query})
    )
    
    start_time = time.time()
    
    try:
        agent_executor = rag_service.get_agent_executor()
        response = await agent_executor.ainvoke({"input": request.query})
        
        processing_time = time.time() - start_time
        response_text = response["output"]
        
        # Log the RAG response
        logging_service.log_rag_response(
            query=request.query,
            response=response_text,
            processing_time=processing_time,
            user_id=user_id,
            api_key_hash=api_key_hash,
            additional_data={
                "response_length": len(response_text),
                "processing_time_seconds": processing_time
            }
        )
        
        return {"answer": response_text}
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        # Log the error
        logging_service.log_error(
            error_message=str(e),
            error_type="query_error",
            user_id=user_id,
            api_key_hash=api_key_hash,
            additional_data={
                "query": request.query,
                "processing_time_seconds": processing_time
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {e}"
        )

@app.get("/logs/")
async def get_logs(date: str = None, log_type: str = "all", api_key: str = Depends(get_api_key)):
    """
    Endpoint to retrieve logs for monitoring purposes.
    
    Args:
        date: Date in YYYYMMDD format (defaults to today)
        log_type: Type of logs to retrieve (queries, responses, uploads, errors, all)
        api_key: API key for authentication
    """
    from datetime import datetime
    
    # Extract user information for logging
    api_key_hash = hash_api_key(api_key)
    user_id = extract_user_id_from_api_key(api_key)
    
    try:
        # Use today's date if not provided
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # Validate log type
        valid_log_types = ["queries", "responses", "uploads", "errors", "all"]
        if log_type not in valid_log_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log_type. Must be one of: {valid_log_types}"
            )
        
        # Get logs
        logs = logging_service.get_logs_by_date(date, log_type)
        
        # Log this access attempt
        logging_service.log_query(
            query=f"Log access request - Date: {date}, Type: {log_type}",
            user_id=user_id,
            api_key_hash=api_key_hash,
            additional_data={"log_access": True, "date": date, "log_type": log_type}
        )
        
        return {
            "date": date,
            "log_type": log_type,
            "count": len(logs),
            "logs": logs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging_service.log_error(
            error_message=str(e),
            error_type="log_access_error",
            user_id=user_id,
            api_key_hash=api_key_hash,
            additional_data={"date": date, "log_type": log_type}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving logs: {e}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)