from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
from tkinter import Tk, filedialog

from graph import generate_course_stream

app = FastAPI(title="Course Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/select_folder")
def select_folder():
    try:
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory()
        root.destroy()
        return {"folder_path": folder_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GenerationRequest(BaseModel):
    topic: str
    folder_path: str

@app.post("/generate")
async def generate_course(req: GenerationRequest):
    if not os.path.exists(req.folder_path) or not os.path.isdir(req.folder_path):
        raise HTTPException(status_code=400, detail="Invalid folder path")
    
    def event_generator():
        try:
            for message in generate_course_stream(req.topic, req.folder_path):
                yield f"data: {message}\n\n"
        except Exception as e:
            import json
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
