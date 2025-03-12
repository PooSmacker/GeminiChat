import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import google.generativeai as genai
import argparse
from dotenv import load_dotenv
from io import BytesIO
from PIL import Image
import base64

app = FastAPI(title="Gemini File Context Web")

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variables
scan_directory = Path.cwd()  
file_contents = {} 
gemini_api_key = None
selected_model = "gemini-2.0-flash" 
use_file_context = True 

API_KEY_FILE = ".gemini_api_key"

load_dotenv()


# --- Helper Functions ---
def load_api_key():
    global gemini_api_key
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        try:
            with open(API_KEY_FILE, "r") as f:
                gemini_api_key = f.read().strip()
        except FileNotFoundError:
            return None
    return gemini_api_key


def save_api_key(api_key: str):
    global gemini_api_key
    gemini_api_key = api_key
    with open(API_KEY_FILE, "w") as f:
        f.write(api_key)


IGNORE_DIRS = {
    'node_modules',
    '__pycache__',
    'venv',
    '.git',
    '.idea',
    '.vscode',
    'dist',
    'build',
    'target',
    'bin',
    'obj',
    '.next',
    '.cache',
    '.npm',
    'vendor',
}

IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.dll', '.so', '.dylib',  
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico',  
    '.mp3', '.wav', '.ogg', '.flac', '.aac',  
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',  
    '.zip', '.tar', '.gz', '.rar', '.7z', '.jar',  
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',  
    '.bin', '.dat', '.db', '.sqlite', '.sqlite3',  
}


def get_file_content(file_path: Path) -> Optional[str]:
    if file_path.suffix.lower() in IGNORE_EXTENSIONS:
        return None

    try:
        if (file_path.is_symlink() or
                file_path.stat().st_size > 1_000_000 or
                file_path.name.startswith('.')):
            return None

        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

            if '\0' in content:
                return None

            return content
    except Exception:
        return None


def should_process_directory(path: Path, ignore_dirs: Set[str]) -> bool:
    if path.name.startswith('.'):
        return False

    if path.name in ignore_dirs:
        return False

    return True


async def scan_directory_for_files(directory: Path,
                                     ignore_dirs: Set[str]) -> Dict[str, Dict]:
    file_contents = {}
    file_info = []

    try:
        for root, dirs, files in os.walk(directory, topdown=True):
            dirs[:] = [
                d for d in dirs
                if should_process_directory(Path(root) / d, ignore_dirs)
            ]

            root_path = Path(root)
            for file in files:
                file_path = root_path / file

                content = get_file_content(file_path)
                if content:
                    rel_path = str(file_path.relative_to(directory))
                    file_contents[rel_path] = content

                    file_info.append({
                        "path": rel_path,
                        "size": len(content)
                    })

        return {
            "status": "success",
            "files": file_info,
            "file_contents": file_contents
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def format_files_for_context(file_contents: Dict[str, str]) -> str:
    context = "Here are the files in the project:\n\n"

    for file_path, content in file_contents.items():
        context += f"### FILE: {file_path}\n```\n{content}\n```\n\n"

    return context


async def query_gemini(file_contents: Dict[str, str], user_prompt: str, model_name: str, image_data: Optional[bytes], use_file_context: bool, pasted_image_data: Optional[str] = None) -> Dict[str, Any]:
    global gemini_api_key
    if not gemini_api_key:
        return {"status": "error", "message": "GEMINI_API_KEY not configured"}

    try:
        genai.configure(api_key=gemini_api_key)

        full_context = format_files_for_context(file_contents) if use_file_context else ""

        complete_prompt = f"{full_context}\n\nUser Query: {user_prompt}\n\nPlease analyze these files and take them into context. And then respond to the query." if use_file_context else f"User Query: {user_prompt}\n\nPlease respond to the query."

        model = genai.GenerativeModel(model_name)

        generation_config = {
            "max_output_tokens": 8192,
            "temperature": 0.4,
            "top_p": 0.8,
            "top_k": 40
        }

        content_parts = []

        if pasted_image_data:
            try:
                header, encoded = pasted_image_data.split(",", 1)
                image_data = base64.b64decode(encoded)
                image = Image.open(BytesIO(image_data))
                content_parts.append(image)
            except Exception as e:
                return {"status": "error", "message": f"Error processing pasted image: {str(e)}"}

        elif image_data:
            image = Image.open(BytesIO(image_data))
            content_parts.append(image)


        content_parts.append(complete_prompt)

        response = model.generate_content(
            content_parts,
            generation_config=generation_config
        )

        return {"status": "success", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if not load_api_key():
        return RedirectResponse("/api-key", status_code=302)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "api_key_set": True
    })


@app.get("/api-key", response_class=HTMLResponse)
async def get_api_key_page(request: Request):
    return templates.TemplateResponse("api_key.html", {"request": request})


@app.post("/api-key")
async def set_api_key(request: Request, api_key: str = Form(...)):
    save_api_key(api_key)
    return RedirectResponse("/", status_code=302)


@app.get("/get-current-directory")
async def get_current_directory():
    global scan_directory
    return {"directory": str(scan_directory)}


@app.post("/scan-directory")
async def scan_directory_endpoint(request: Request):
    global scan_directory, file_contents
    data = await request.json()

    directory_path = data.get("directory")
    ignore_dirs_str = data.get("ignore_dirs", "")

    if not directory_path:
        return JSONResponse(status_code=400,
                            content={
                                "status": "error",
                                "message": "No directory provided"
                            })

    ignore_dirs = set(IGNORE_DIRS)
    if ignore_dirs_str:
        custom_ignores = {d.strip() for d in ignore_dirs_str.split(',')}
        ignore_dirs.update(custom_ignores)

    try:
        directory = Path(directory_path).expanduser().resolve()
        if not directory.is_dir():
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"{directory} is not a valid directory"
                })
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Invalid directory path: {str(e)}"
            })

    result = await scan_directory_for_files(directory, ignore_dirs)

    if result["status"] == "success":
        file_contents = result["file_contents"]
        scan_directory = directory  
        return {"status": "success", "files": result["files"]}
    else:
        return {"status": "error", "message": result["message"]}


@app.post("/query")
async def query_endpoint(request: Request):
    global file_contents, scan_directory, selected_model, use_file_context

    if not file_contents:
        return {
            "status": "error",
            "message": "No files have been scanned yet. Please scan a directory first."
        }

    form_data = await request.form()
    prompt = form_data.get("prompt")
    image_file = form_data.get("image")
    model_name = form_data.get("model")
    use_file_context_str = form_data.get("use_file_context")
    pasted_image_data = form_data.get("pasted_image_data") 


    if not prompt:
        return {"status": "error", "message": "No prompt provided"}

    if model_name:
        selected_model = model_name

    if use_file_context_str:
        use_file_context = use_file_context_str.lower() == "true"

    image_data = None
    if image_file and image_file.filename:
        image_data = await image_file.read()


    scan_result = await scan_directory_for_files(scan_directory, IGNORE_DIRS)
    if scan_result["status"] == "success":
        file_contents = scan_result["file_contents"]
    else:
        return scan_result  

    response = await query_gemini(file_contents, prompt, selected_model, image_data, use_file_context, pasted_image_data)
    return response


# --- Startup and Configuration ---

def parse_args():
    parser = argparse.ArgumentParser(
        description="Gemini File Context Web Application")
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=str(Path.cwd()),
        help="Directory to scan (default: current working directory)")
    parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to run the web server on (default: 8000)")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the web server on (default: 127.0.0.1)")
    return parser.parse_args()


def run_server():
    args = parse_args()

    global scan_directory
    scan_directory = Path(args.directory).expanduser().resolve()

    print(f"Starting Gemini File Context Web on http://{args.host}:{args.port}")
    print(f"Initial directory: {scan_directory}")

    load_api_key()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    run_server()
