import json
import os
import uuid  # For generating unique filenames
import aiofiles  # For async file operations
from datetime import datetime
from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"  # Optional: if you want to save uploads
DOWNLOAD_DIR = BASE_DIR / "downloads"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

# --- FastAPI App Initialization ---
app = FastAPI(title="Drone Mission Adapter (Australia)")

# Mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# --- Core Logic Function (Adapted to return data/errors) ---
def create_geojson_from_data(risk_cells, altitude_m=60, hover_time_s=120, input_filename=""):
    """
    Converts a list of risk cell dicts into a GeoJSON data structure.

    Args:
        risk_cells (list): List of dicts, each with 'latitude' and 'longitude'.
        altitude_m (int): Target flight altitude (AGL).
        hover_time_s (int): Hover time at each waypoint (seconds).
        input_filename (str): Original filename for metadata.

    Returns:
        tuple: (bool, dict | str) - (success_status, geojson_data or error_message)
    """
    features = []
    waypoint_counter = 1
    valid_cells_processed = 0

    if not isinstance(risk_cells, list):
        return False, "Input data is not a valid list of risk cells."

    for cell in risk_cells:
        if 'latitude' not in cell or 'longitude' not in cell:
            print(f"Warning: Skipping cell due to missing coordinates: {cell.get('cell_id', 'Unknown ID')}")
            continue  # Skip invalid cells silently in web context, or collect warnings

        properties = {
            "name": f"Waypoint_{waypoint_counter}",
            "description": f"Patrol target. Risk: {cell.get('risk_value', 'N/A')} ({cell.get('risk_type', 'N/A')}). Cell: {cell.get('cell_id', 'N/A')}",
            "altitude_m_agl": altitude_m,
            "hover_time_s": hover_time_s,
            "timestamp_created": datetime.now().isoformat()
        }
        geometry = {
            "type": "Point",
            "coordinates": [cell['longitude'], cell['latitude']]  # GeoJSON standard: [longitude, latitude]
        }
        feature = {
            "type": "Feature",
            "properties": properties,
            "geometry": geometry
        }
        features.append(feature)
        waypoint_counter += 1
        valid_cells_processed += 1

    if not features:
        return False, "No valid waypoints could be generated from the input data (check coordinates)."

    geojson_data = {
        "type": "FeatureCollection",
        "metadata": {
            "name": f"Drone Patrol Mission - Source: {input_filename}",
            "creator": "Unified Drone Mission Web Adapter",
            "creation_date": datetime.now().isoformat()
        },
        "features": features
    }
    return True, geojson_data


# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process", response_class=JSONResponse)
async def process_file(
        request: Request,
        risk_file: UploadFile = File(...),
        altitude_m: int = Form(60),  # Default values here
        hover_time_s: int = Form(120)
):
    """Handles file upload, processing, and returns status/download link."""

    # --- Input Validation ---
    if not risk_file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JSON file.")
    if altitude_m <= 0 or hover_time_s < 0:
        raise HTTPException(status_code=400,
                            detail="Invalid parameters. Altitude must be > 0, Hover Time must be >= 0.")

    # --- Read Uploaded File ---
    try:
        contents = await risk_file.read()
        risk_data = json.loads(contents)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Could not decode JSON from file. Please check the file format.")
    except Exception as e:
        print(f"Error reading uploaded file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading uploaded file: {e}")
    finally:
        await risk_file.close()  # Ensure file is closed

    # --- Process Data ---
    success, result_data = create_geojson_from_data(
        risk_data, altitude_m, hover_time_s, risk_file.filename
    )

    if not success:
        # result_data contains the error message here
        raise HTTPException(status_code=400, detail=result_data)

        # --- Save Output File ---
    output_filename = f"mission_{uuid.uuid4()}.geojson"  # Generate unique filename
    output_filepath = DOWNLOAD_DIR / output_filename

    try:
        async with aiofiles.open(output_filepath, 'w') as f:
            await f.write(json.dumps(result_data, indent=4))  # result_data is the geojson dict

        waypoint_count = len(result_data.get("features", []))

        return JSONResponse(content={
            "status": "success",
            "message": f"Successfully generated mission file with {waypoint_count} waypoints.",
            "download_filename": output_filename  # Send filename back to frontend
        })
    except Exception as e:
        print(f"Error writing output file: {e}")
        raise HTTPException(status_code=500, detail=f"Error writing output file: {e}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Provides the generated GeoJSON file for download."""
    file_path = DOWNLOAD_DIR / filename

    # Security: Ensure the filename is safe and exists
    if not filename.startswith("mission_") or not filename.endswith(".geojson"):
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    # Prevent directory traversal
    try:
        _ = file_path.relative_to(DOWNLOAD_DIR)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied.")

    return FileResponse(
        path=file_path,
        filename=filename,  # Suggests filename to browser
        media_type='application/geo+json'
    )


# --- Run the server (for local development) ---
if __name__ == "__main__":
    import uvicorn

    # Make sure DOWNLOAD_DIR exists before starting
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    print(f"INFO:     Server starting. Access at http://127.0.0.1:8000")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)