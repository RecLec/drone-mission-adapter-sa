# Drone Mission Adapter SA (South Australia)

Web app MVP to convert bushfire high-risk area JSON data to drone mission GeoJSON for South Australia.

## Overview

This tool provides a simple web interface to:
1. Upload a JSON file containing geographic coordinates (latitude, longitude) of high-risk areas identified by bushfire prediction algorithms (e.g., FWI, AFDRS, NFDRS-IC, probability models).
2. Set basic mission parameters (altitude, hover time).
3. Generate a GeoJSON file containing these locations as waypoints, suitable for import into common drone ground control station (GCS) software (like QGroundControl, Mission Planner).

## Prerequisites

* Python 3.9 or higher installed.
* `pip` (Python package installer).
* Git (optional, for cloning the repository. You can also download the ZIP).

## Setup Instructions

1.  **Get the code:**
    * Clone the repository: 
        ```bash
        git clone [https://github.com/RecLec/drone-mission-adapter-sa.git](https://github.com/RecLec/drone-mission-adapter-sa.git)
        ```
    * Or, download the ZIP file from the repository page and extract it.

2.  **Navigate to the project directory:**
    ```bash
    cd drone-mission-adapter-sa 
    ```

3.  **Create and activate a virtual environment (Recommended):**
    * On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  **Start the FastAPI server:**
    Make sure your virtual environment is activated and you are in the project directory. Run:
    ```bash
    uvicorn main:app --reload 
    ```
    *(The `--reload` flag is for development; it automatically restarts the server when code changes. For simple running, `uvicorn main:app` is sufficient.)*

2.  **Access the web interface:**
    Open your web browser and navigate to:
    `http://127.0.0.1:8000`

## Usage

1.  **Upload File:** Drag and drop your JSON input file onto the designated area, or click the area to browse for the file. The filename will appear below the drop zone.
2.  **Set Parameters:** Adjust the `Altitude` (in metres above ground level) and `Hover Time` (in seconds) as needed. Defaults are provided.
3.  **Generate:** Click the "Generate Mission File" button.
4.  **Status & Download:** The status area will show progress (currently very fast) and then either a success message with a download link or an error message. Click the download link to save the generated `.geojson` file.

## Input File Format

The input must be a JSON file containing a list (`[]`) of objects (`{}`). Each object represents a high-risk cell or point and **must** contain `latitude` and `longitude` keys with valid numerical values (WGS-84 standard).

Optional keys like `cell_id`, `risk_value`, `risk_type` can be included and will be added to the description of the waypoint in the output file.

**Example (`example_input.json` is included in this repository):**
```json
[
  {"cell_id": "SA_Grid_001", "latitude": -34.9285, "longitude": 138.6007, "risk_value": 75, "risk_type": "probability"},
  {"cell_id": "SA_Grid_002", "latitude": -34.9310, "longitude": 138.6030, "risk_value": 90, "risk_type": "IC"},
  {"cell_id": "SA_Grid_003", "latitude": -34.9250, "longitude": 138.5980, "risk_value": 120, "risk_type": "FBI"}
]

