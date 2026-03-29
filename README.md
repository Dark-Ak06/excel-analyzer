# 📊 Excel Analyzer API

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/pandas-2.x-150458?style=flat-square&logo=pandas&logoColor=white"/>
  <img src="https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/excel-analyzer/ci.yml?style=flat-square&label=CI"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square"/>
</p>

<p align="center">
  A REST API that transforms Excel files into structured analytics — metrics, insights, and LLM-ready summaries.<br/>
  <strong>FastAPI · pandas · Pydantic · pytest</strong>
</p>

---

## 🎯 What problem does this solve?

Analysts spend hours manually opening Excel files, computing metrics, and writing conclusions. This API automates the entire pipeline:

| Before | After |
|---|---|
| Open Excel manually | POST /analyze with the file |
| Compute mean, sum, std by hand | JSON response in milliseconds |
| Write insights manually | Auto-generated text insights |
| Can't connect to LLM | LLM-ready summary string included |

---

## ✨ Features

- **Automatic metrics** — mean, median, sum, min, max, std per numeric column
- **Smart insights** — skew detection, variability analysis, outlier warnings, missing value alerts
- **Data quality report** — missing values, column types, row/column counts
- **LLM-ready summary** — compact string you can pass directly to GPT-4 / Claude for deeper analysis
- **Swagger UI** — interactive API documentation at `/docs`
- **Type-safe** — full Pydantic v2 validation on all inputs and outputs
- **Tested** — 15+ unit tests with pytest

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/excel-analyzer.git
cd excel-analyzer

# Install
pip install -r requirements.txt

# Run
uvicorn main:app --reload
```

Open **http://localhost:8000/docs** — you'll see the interactive Swagger UI where you can upload a file directly.

---

## 📡 API

### `POST /analyze`

Upload an Excel file, get back full analytics.

**Request:** `multipart/form-data` with field `file` (.xlsx or .xls, max 10 MB)

**Response:**
```json
{
  "metrics": {
    "Revenue": {
      "mean": 52300.5,
      "median": 48000.0,
      "sum": 1569015.0,
      "min": 12000.0,
      "max": 145000.0,
      "std": 21500.3,
      "count": 30
    }
  },
  "insights": [
    "Revenue: mean (52,300) > median (48,000) — right-skewed, possible growth trend.",
    "Revenue: high variability (cv=41%) — consider investigating outliers."
  ],
  "quality": {
    "total_rows": 30,
    "total_columns": 5,
    "numeric_columns": 3,
    "missing_values": { "Cost": 2 },
    "dtypes": { "Revenue": "float64", "Month": "object" }
  },
  "llm_summary": "Dataset: 30 rows, 5 columns. Metrics — Revenue (mean=52,300, std=21,500, min=12,000, max=145,000). Missing values — Cost: 2."
}
```

### `GET /health`

```json
{ "status": "healthy" }
```

---

## 🏗️ Project Structure

```
excel-analyzer/
│
├── main.py               # FastAPI app, routes
├── src/
│   ├── __init__.py
│   ├── analyzer.py       # Core analytics pipeline
│   ├── models.py         # Pydantic request/response models
│   └── utils.py          # Data cleaning, number formatting
│
├── tests/
│   └── test_analyzer.py  # 15+ unit tests
│
├── data/samples/         # Sample Excel files for testing
├── .github/workflows/    # GitHub Actions CI
├── requirements.txt
└── README.md
```

---

## 🤖 LLM Integration

The `llm_summary` field is designed to be passed directly to any LLM:

```python
import openai
from your_client import analyze_excel

result = analyze_excel("sales_q1.xlsx")

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a financial analyst."},
        {"role": "user", "content": f"{result['llm_summary']}\n\nProvide a business analysis with recommendations."},
    ]
)
print(response.choices[0].message.content)
```

The architecture is ready for LLM extension — no refactoring needed.

---

## 🔬 Analytics Pipeline

```
Excel file
    ↓
pandas.read_excel()
    ↓
clean_dataframe()          ← drop empty rows/cols, strip whitespace
    ↓
select_dtypes("number")    ← numeric columns only
    ↓
compute_metrics()          ← mean, median, sum, min, max, std, count
    ↓
generate_insights()        ← skew detection, variability, outliers, missing
    ↓
build_llm_summary()        ← compact string for LLM prompts
    ↓
AnalysisResponse (JSON)
```

**Insight rules:**
- `mean > median × 1.05` → right-skewed (possible growth)
- `mean < median × 0.95` → left-skewed (possible decline)
- `cv > 0.5` → high variability, investigate outliers
- `max / min > 100` → extreme range detected
- Any `NaN` → missing value warning with percentage

---

## 🧪 Tests

```bash
pytest tests/ -v
```

```
tests/test_analyzer.py::TestFormatNumber::test_millions         PASSED
tests/test_analyzer.py::TestCleanDataframe::test_drops_empty_columns  PASSED
tests/test_analyzer.py::TestExcelAnalyzer::test_metrics_correct PASSED
tests/test_analyzer.py::TestExcelAnalyzer::test_no_numeric_cols_raises PASSED
... (15 tests)
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **FastAPI** | REST API framework, auto Swagger docs |
| **pandas** | Data loading and statistical computation |
| **openpyxl** | Excel file parsing |
| **Pydantic v2** | Request/response validation and serialization |
| **pytest** | Unit testing |
| **GitHub Actions** | CI/CD pipeline |

---

## 💼 Skills Demonstrated

- **REST API design** — clean endpoints, proper HTTP status codes, error handling
- **Data engineering** — pandas pipelines, data cleaning, statistical analysis
- **Software architecture** — separation of concerns (routes / logic / models / utils)
- **Testing** — unit tests covering edge cases (empty file, no numeric columns, missing values)
- **Production readiness** — file size limits, type validation, CI/CD

---

## 🚀 Possible Extensions

- Connect to OpenAI / local LLM for natural language reports
- Add authentication (JWT / API keys)
- Support CSV, Google Sheets
- Persist results to PostgreSQL
- Deploy with Docker + cloud (Railway, Fly.io, AWS)

---

## 📄 License

MIT © 2024
