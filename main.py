"""
Excel Analyzer API — entry point.

Run locally:
    uvicorn main:app --reload

Then open:
    http://localhost:8000/docs   ← interactive Swagger UI
    http://localhost:8000/redoc  ← ReDoc documentation
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import io

from src.analyzer import ExcelAnalyzer
from src.models import AnalysisResponse

app = FastAPI(
    title="Excel Analyzer API",
    description="Automated analytics for Excel files — metrics, insights, LLM-ready.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "Excel Analyzer API is running."}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}


@app.post("/analyze", response_model=AnalysisResponse, tags=["analysis"])
async def analyze_excel(file: UploadFile = File(...)):
    """
    Upload an Excel file (.xlsx / .xls) and receive:
    - per-column metrics (mean, median, sum, min, max, std)
    - auto-generated text insights
    - data quality report (missing values, dtypes)
    - LLM-ready summary string
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=422,
            detail="Only .xlsx and .xls files are supported.",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

    try:
        analyzer = ExcelAnalyzer(io.BytesIO(content))
        result = analyzer.run()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    return result
