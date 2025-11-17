from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from oreka_backend.upload import FileProcessor

app = FastAPI(title="Oreka Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize file processor
file_processor = FileProcessor()


@app.get("/")
async def root():
    return {"message": "Oreka Backend API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process CSV (Cachier export) or PDF (invoice) files.

    - **file**: CSV or PDF file to be processed

    Returns processed data in JSON format.
    """
    try:
        processed_data = await file_processor.process_file(file)
        return JSONResponse(
            status_code=200,
            content={"message": "File processed successfully", "data": processed_data},
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/dashboard")
async def dashboard():
    """
    Dashboard endpoint showing all computations and uploaded file summaries.

    Returns:
    - Summary statistics of all processed files
    - List of recent files
    - File type breakdown
    """
    try:
        computations = file_processor.get_computations_summary()
        all_files = file_processor.get_all_processed_files()

        return JSONResponse(
            status_code=200,
            content={"dashboard": {"summary": computations, "all_files": all_files}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating dashboard: {str(e)}"
        )


@app.get("/dashboard/files")
async def get_all_files():
    """
    Get detailed information about all processed files.
    """
    try:
        files = file_processor.get_all_processed_files()
        return JSONResponse(
            status_code=200, content={"files": files, "count": len(files)}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving files: {str(e)}")
