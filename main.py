from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = FastAPI(title="Campus Navigation API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Location database
LOCATIONS = {
    # Ground Floor
    'Entrance Lobby': {'floor': 'ground', 'type': 'entrance', 'position': 'west'},
    'Admin Office': {'floor': 'ground', 'type': 'office', 'position': 'center'},
    'Ladies Washroom (Ground)': {'floor': 'ground', 'type': 'facility', 'position': 'east'},
    'Classroom G1': {'floor': 'ground', 'type': 'classroom', 'position': 'northwest', 'adjacent': ['Entrance Lobby']},
    'Classroom G2': {'floor': 'ground', 'type': 'classroom', 'position': 'north', 'adjacent': ['Classroom G1', 'Admin Office']},
    'Classroom G3': {'floor': 'ground', 'type': 'classroom', 'position': 'northcenter', 'adjacent': ['Classroom G2', 'Admin Office']},
    'Classroom G4': {'floor': 'ground', 'type': 'classroom', 'position': 'northcentereast', 'adjacent': ['Classroom G3']},
    'Classroom G5': {'floor': 'ground', 'type': 'classroom', 'position': 'northeast', 'adjacent': ['Classroom G4']},
    'Classroom G6': {'floor': 'ground', 'type': 'classroom', 'position': 'eastmost', 'adjacent': ['Classroom G5']},
    'Classroom G7': {'floor': 'ground', 'type': 'classroom', 'position': 'southwestcenter', 'adjacent': ['Entrance Lobby', 'Admin Office']},
    'Classroom G8': {'floor': 'ground', 'type': 'classroom', 'position': 'southcenter', 'adjacent': ['Admin Office', 'Classroom G7']},
    'Admin Office Room': {'floor': 'ground', 'type': 'office', 'position': 'centercenter', 'adjacent': ['Classroom G8']},
    'Classroom G9': {'floor': 'ground', 'type': 'classroom', 'position': 'southcentereast', 'adjacent': ['Admin Office Room']},
    'Classroom G10': {'floor': 'ground', 'type': 'classroom', 'position': 'southeast', 'adjacent': ['Classroom G9', 'Ladies Washroom (Ground)']},
    
    # First Floor
    'Research Wing': {'floor': 'first', 'type': 'entrance', 'position': 'west'},
    'Seminar Hall (First)': {'floor': 'first', 'type': 'hall', 'position': 'center'},
    'Computer Lab 1': {'floor': 'first', 'type': 'lab', 'position': 'southwest', 'adjacent': ['Research Wing']},
    'Physics Lab': {'floor': 'first', 'type': 'lab', 'position': 'southcenter', 'adjacent': ['Computer Lab 1', 'Seminar Hall (First)']},
    'Physics Aid Room': {'floor': 'first', 'type': 'room', 'position': 'southcenter2', 'adjacent': ['Physics Lab', 'Seminar Hall (First)']},
    'Viceprincipal': {'floor': 'first', 'type': 'office', 'position': 'southeastcenter', 'adjacent': ['Physics Aid Room']},
    "HOD's Restroom": {'floor': 'first', 'type': 'facility', 'position': 'east', 'adjacent': ['Viceprincipal']},
    'Firstly Floor Washroom': {'floor': 'first', 'type': 'facility', 'position': 'east'},
    'Classroom F1': {'floor': 'first', 'type': 'classroom', 'position': 'northwest', 'adjacent': ['Research Wing']},
    'Classroom F2': {'floor': 'first', 'type': 'classroom', 'position': 'north', 'adjacent': ['Classroom F1']},
    'Classroom F3': {'floor': 'first', 'type': 'classroom', 'position': 'northcenter', 'adjacent': ['Classroom F2', 'Seminar Hall (First)']},
    'Classroom F4': {'floor': 'first', 'type': 'classroom', 'position': 'northcentereast', 'adjacent': ['Classroom F3']},
    'Classroom F5': {'floor': 'first', 'type': 'classroom', 'position': 'northeast', 'adjacent': ['Classroom F4']},
    'Classroom F6': {'floor': 'first', 'type': 'classroom', 'position': 'eastmost', 'adjacent': ['Classroom F5']},
    'Classroom F7': {'floor': 'first', 'type': 'classroom', 'position': 'southeastmost', 'adjacent': ['Viceprincipal', 'Firstly Floor Washroom']},
    
    # Second Floor
    'Entrance Wing (Second)': {'floor': 'second', 'type': 'entrance', 'position': 'west'},
    'Seminar Hall (Second)': {'floor': 'second', 'type': 'hall', 'position': 'center'},
    'Firstly Floor Washroom (Second)': {'floor': 'second', 'type': 'facility', 'position': 'east'},
    'Computer Lab 2': {'floor': 'second', 'type': 'lab', 'position': 'northwest', 'adjacent': ['Entrance Wing (Second)']},
    'Electrical Lab': {'floor': 'second', 'type': 'lab', 'position': 'southwest', 'adjacent': ['Entrance Wing (Second)', 'Computer Lab 2']},
    'Research Wing (Second)': {'floor': 'second', 'type': 'lab', 'position': 'southwestcenter', 'adjacent': ['Electrical Lab']},
    'Biology Lab': {'floor': 'second', 'type': 'lab', 'position': 'southcenter', 'adjacent': ['Research Wing (Second)', 'Seminar Hall (Second)']},
    'Bio-Coty Lab': {'floor': 'second', 'type': 'lab', 'position': 'southcentereast', 'adjacent': ['Biology Lab', 'Seminar Hall (Second)']},
    'Biochemy Lab': {'floor': 'second', 'type': 'lab', 'position': 'southeastcenter', 'adjacent': ['Bio-Coty Lab']},
    "Won's Restroom": {'floor': 'second', 'type': 'facility', 'position': 'southeastmost', 'adjacent': ['Biochemy Lab']},
    'Dorm Room': {'floor': 'second', 'type': 'classroom', 'position': 'northcenter', 'adjacent': ['Seminar Hall (Second)']},
    'Seminar Hall Center': {'floor': 'second', 'type': 'hall', 'position': 'northcentereast', 'adjacent': ['Dorm Room']},
    '9696Com Classroom': {'floor': 'second', 'type': 'classroom', 'position': 'northeastcenter', 'adjacent': ['Seminar Hall Center']},
    'Classroom S1': {'floor': 'second', 'type': 'classroom', 'position': 'eastmost', 'adjacent': ['9696Com Classroom']},
}

# Request/Response Models
class RouteRequest(BaseModel):
    start: str
    destination: str
    use_ai: bool = True

class RouteResponse(BaseModel):
    steps: List[str]
    startFloor: str
    endFloor: str
    estimatedTime: float
    valid: bool
    aiGenerated: bool = False

# Routing Logic
def calculate_route(start: str, destination: str) -> RouteResponse:
    """Rule-based route calculation (fallback)"""
    start_loc = LOCATIONS.get(start)
    end_loc = LOCATIONS.get(destination)
    
    if not start_loc or not end_loc:
        return RouteResponse(
            steps=['Invalid location. Please check the room names.'],
            startFloor='',
            endFloor='',
            estimatedTime=0,
            valid=False
        )
    
    steps = []
    
    steps.append(f"Starting from {start} ({start_loc['floor'].upper()} FLOOR)")
    
    if start_loc['type'] in ['classroom', 'lab', 'office']:
        steps.append(f"Exit {start} and turn into the corridor")
    
    if start_loc['floor'] != end_loc['floor']:
        steps.append("Navigate to the stairs on the left side")
        
        floor_order = ['ground', 'first', 'second']
        start_idx = floor_order.index(start_loc['floor'])
        end_idx = floor_order.index(end_loc['floor'])
        
        if end_idx > start_idx:
            for i in range(start_idx, end_idx):
                steps.append(f"Take the stairs UP to {floor_order[i+1].upper()} FLOOR")
        else:
            for i in range(start_idx, end_idx, -1):
                steps.append(f"Take the stairs DOWN to {floor_order[i-1].upper()} FLOOR")
        
        steps.append("Exit the staircase and turn right into the corridor")
    
    if 'north' in end_loc['position']:
        steps.append("Walk along the top corridor")
    elif 'south' in end_loc['position']:
        steps.append("Walk along the bottom corridor")
    
    if 'west' in end_loc['position']:
        steps.append(f"{destination} is on your left")
    elif 'east' in end_loc['position']:
        steps.append(f"{destination} is on your right")
    
    steps.append(f"You have arrived at {destination}")
    
    floor_order = ['ground', 'first', 'second']
    floor_changes = abs(floor_order.index(start_loc['floor']) - floor_order.index(end_loc['floor']))
    estimated_time = 2.0 + (floor_changes * 1.5)
    
    return RouteResponse(
        steps=steps,
        startFloor=start_loc['floor'],
        endFloor=end_loc['floor'],
        estimatedTime=estimated_time,
        valid=True
    )

async def generate_ai_route(start: str, destination: str) -> RouteResponse:
    """AI-powered route generation using Gemini"""
    start_loc = LOCATIONS.get(start)
    end_loc = LOCATIONS.get(destination)
    
    if not start_loc or not end_loc:
        return RouteResponse(
            steps=['Invalid location.'],
            startFloor='',
            endFloor='',
            estimatedTime=0,
            valid=False
        )
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Warning: No GEMINI_API_KEY found, using rule-based routing")
        return calculate_route(start, destination)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        floor_context = f"""
You are a campus navigation assistant. Generate clear step-by-step walking directions.

Building Layout:
- 3 floors: Ground, First, Second
- Stairs located on LEFT SIDE of each floor
- Corridors: TOP (north) and BOTTOM (south) horizontal corridors, CENTER vertical corridor

Ground Floor: Entry: Entrance Lobby | Center: Admin Office
- Top corridor: Classrooms G1, G2, G3, G4, G5, G6 (left to right)
- Bottom corridor: Classrooms G7, G8, Admin Room, G9, G10 (left to right)
- Right side: Ladies Washroom

First Floor: Entry: Research Wing | Center: Seminar Hall
- Top corridor: Classrooms F1, F2, F3, F4, F5, F6 (left to right)
- Bottom corridor: Computer Lab 1, Physics Lab, Classroom F7 (left to right)
- Right side: HOD's Restroom, Washroom

Second Floor: Entry: Entrance Wing | Center: Seminar Hall
- Top corridor: Computer Lab 2, Dorm Room, 9696Com, Classroom S1 (left to right)
- Bottom corridor: Electrical Lab, Biology Lab, Bio-Coty Lab, Biochemy Lab (left to right)
- Right side: Washroom

Current Task:
Navigate from: {start} ({start_loc['floor']} floor, {start_loc['position']} position, {start_loc['type']})
To: {destination} ({end_loc['floor']} floor, {end_loc['position']} position, {end_loc['type']})

Rules:
1. Use simple directions: "turn left", "turn right", "walk straight"
2. Use "top corridor" and "bottom corridor" instead of north/south
3. Use "left side" and "right side" instead of west/east
4. Stairs are ALWAYS on the left side
5. Add emojis for clarity (door, walking, stairs, etc)
6. Be specific about turns and landmarks
7. Keep each step clear and actionable

Generate numbered step-by-step directions:
"""
        
        response = model.generate_content(floor_context)
        ai_text = response.text
        
        # Parse response
        steps = []
        for line in ai_text.split('\n'):
            line = line.strip()
            if line and len(line) > 3:
                # Remove numbering and bullets
                line = line.lstrip('0123456789.-*) ')
                if line:
                    steps.append(line)
        
        if not steps:
            print("AI returned empty response, using fallback")
            return calculate_route(start, destination)
        
        floor_order = ['ground', 'first', 'second']
        floor_changes = abs(floor_order.index(start_loc['floor']) - floor_order.index(end_loc['floor']))
        estimated_time = 2.0 + (floor_changes * 1.5)
        
        return RouteResponse(
            steps=steps,
            startFloor=start_loc['floor'],
            endFloor=end_loc['floor'],
            estimatedTime=estimated_time,
            valid=True,
            aiGenerated=True
        )
    except Exception as e:
        print(f"AI Error: {e}, using fallback")
        return calculate_route(start, destination)

# API Endpoints
@app.get("/")
def read_root():
    return {
        "message": "Campus Navigation API with AI",
        "version": "1.0",
        "ai_enabled": bool(os.getenv('GEMINI_API_KEY'))
    }

@app.get("/locations")
def get_locations():
    """Get all available locations"""
    return {"locations": LOCATIONS}

@app.get("/locations/{floor}")
def get_locations_by_floor(floor: str):
    """Get locations for a specific floor"""
    floor_locations = {k: v for k, v in LOCATIONS.items() if v['floor'] == floor}
    return {"floor": floor, "locations": floor_locations}

@app.post("/route")
async def get_route(request: RouteRequest):
    """Calculate route between two locations"""
    try:
        if request.use_ai:
            route = await generate_ai_route(request.start, request.destination)
        else:
            route = calculate_route(request.start, request.destination)
        
        return route
    except Exception as e:
        print(f"Route error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_configured": bool(os.getenv('GEMINI_API_KEY'))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)