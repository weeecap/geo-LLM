import json
import logging
import tempfile
import os

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from schemas import ChatRequest
from engine import generate_response, LLMManager
from utils import logger
from ingest.documents import ingest_doc
from ingest.geo import ingest_feature
from crud.qdrant_ops import collection_delete, select_by_condition, retrieve_point

@asynccontextmanager
async def lifespan(app:FastAPI):
    LLMManager.get_instance()
    yield

app = FastAPI(lifespan=lifespan)
logging.info('Backend is started')

@app.get("/")
async def read_root():
    return {'message':"Hello"}

@app.post('/add_plots')
async def add_plots(
    file:UploadFile = File(...), 
    collection_name:str = Form("land_plots")
):
    contents = await file.read()
    try:
        geojson_data = json.loads(contents.decode("utf-8"))
    except json.JSONDecodeError:
        logging.error('Inaccurate JSON')
        raise HTTPException(400, "Inaccurate JSON")

    try:
        result = await run_in_threadpool(ingest_feature, geojson_data, collection_name)
    except Exception as e:
        logging.error(f'Error while perform add_plots endpoint: {str(e)}')
        raise HTTPException(500, f"Error while upload: {str(e)}")

    if result["status"] == "error":
        logging.error(f'Error 400 while perform add_plots endpoint')
        raise HTTPException(400, result["message"])
    return JSONResponse(result)

@app.post("/add_docs")
async def upload_docs(
    file:UploadFile=File(...),
    collection_name:str=Form("document")
):  
    file_name = file.filename  
    try:
        document = await file.read()
    except Exception as e:
        raise HTTPException(400, "Inaccurate PDF")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(document)
        tmp_path = tmp.name

    try:
        result = await run_in_threadpool(ingest_doc, tmp_path, collection_name, file_name)
    except Exception as e:
        raise HTTPException(500, f"Error while uploading '{file}'")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError as e:
            logger.warning(f"Failed to delete temp file {tmp_path}: {e}")
    return JSONResponse(result)

@app.delete('/delete_collection')
async def delete_collection(collection_name:str = Form("land_plots")):
    try:
        result = await run_in_threadpool(collection_delete, collection_name)
    except Exception as e:
        logging.error(f'Error while perform delete_plots endpoint: {str(e)}')
        raise HTTPException(500, f"An error occured while deleting '{collection_name}" )
    return JSONResponse(result)

# @app.post('/delete_points')
# async def delete_points():
#     try:
#         result = await run_in_threadpool()
#     return JSONResponse

@app.get("/select_by_value")
async def select_by_value(collection_name:str, key:str, value:str):
    try:
        result = await run_in_threadpool(select_by_condition, collection_name, key, value)
    except Exception as e:
        logging.error(f'Error while perform select_by_value endpoint: {str(e)}')
        raise HTTPException(500, f"An error occured while filtering '{collection_name}' by '{key}':'{value}'")
    return JSONResponse(result)

@app.get("/select_by_id")
async def select_by_id(collection_name:str, value:int):
    try:
        result = await run_in_threadpool(retrieve_point, collection_name, value)
    except Exception as e:
        logging.error(f'Error while perform select_by_id endpoint: {str(e)}')
        raise HTTPException(500,f"An error occured while retriecing by id:'{value}'")
    return JSONResponse(result)

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response = await run_in_threadpool(
            generate_response,
            prompt=request.messages
        )
        return {"response": response}
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))