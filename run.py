import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    # Change to the directory where run.py is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)