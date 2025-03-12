# Gemini File Context Web Application

## Overview

This web application allows you to leverage the power of Google's Gemini models to analyze files within a specified directory. It scans the directory, indexes the file contents (excluding ignored files and directories), and provides a user interface to query the Gemini API with the context of these files. You can ask questions about your codebase, understand project structure, and more.  Optionally, you can also include images in your queries.

## Setup

1.  **Prerequisites:**
    -   Python 3.7+
    -   pip (Python package installer)

2.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    *(Replace `<repository_url>` and `<repository_directory>` with your actual repository details)*

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Ensure you have a `requirements.txt` file in the project directory with the following content or similar):*
    ```
    fastapi
    uvicorn
    google-generativeai
    python-dotenv
    Pillow
    jinja2
    requests
    ```

4.  **Set up Gemini API Key:**
    You need a Google Gemini API key to use this application. You can obtain one from [Google AI Studio](https://makersuite.google.com/app/apikey).

    There are two ways to provide your API key:

    *   **Environment Variable:** Set an environment variable named `GEMINI_API_KEY` with your API key.
        ```bash
        export GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```
        *(Replace `YOUR_API_KEY_HERE` with your actual API key)*

    *   **`.gemini_api_key` File:** Create a file named `.gemini_api_key` in the project's root directory and paste your API key into it.

## Running the Application

1.  **Navigate to the project directory** in your terminal.

2.  **Run the application using uvicorn:**
    ```bash
    python main.py
    ```
    or
    ```bash
    python -m main
    ```

    You can also specify the directory to scan and the port using command-line arguments:
    ```bash
    python main.py --directory /path/to/your/code --port 8080
    ```
    or
    ```bash
    python main.py -d /path/to/your/code -p 8080
    ```

3.  **Access the application in your browser:**
    Open your web browser and go to `http://127.0.0.1:8000` (or the host and port you specified).

## Usage

1.  **Enter Gemini API Key:** If you haven't set up the API key yet, you will be redirected to the API key input page. Enter your Gemini API key and submit.

2.  **Scan Directory:**
    *   In the sidebar, under "Scan Directory", enter the path to the directory you want to analyze in the "Directory path" input. You can use the "refresh" icon to use the current working directory.
    *   Optionally, you can specify directories to ignore in the "Directories to ignore" input (comma-separated). Default ignored directories are provided.
    *   Click the "Scan Directory" button.
    *   The application will scan the directory and list the files in the "Files" section. The file count will be updated.

3.  **Model Selection:**
    *   Under "Model Selection", you can choose the Gemini model you want to use from the dropdown.

4.  **Use File Context Toggle:**
    *   The "Use Scanned Directory as Context" toggle is enabled by default. When enabled, the content of the scanned files will be included as context in your queries to Gemini. You can disable it if you want to query Gemini without file context.

5.  **Image Input (Optional):**
    *   You can optionally upload an image file using the "Image Input" file selector. This image will be included in your query to Gemini, allowing for multimodal prompts.
    *   You can also paste images directly into the prompt textarea. Pasted images will be previewed and used in your query.

6.  **Ask Questions:**
    *   In the prompt textarea at the bottom, type your question or query related to the scanned files (or general questions if context is disabled).
    *   Click the "Send" button.
    *   The application will send your query to the Gemini API, including the file context if enabled and the image if provided.
    *   The response from Gemini will be displayed in the main content area. Code blocks in the response will be syntax highlighted, and a "Copy" button will be available for code snippets.

## License

This project is released under the MIT License.

**MIT License**

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

**You are free to do whatever you want with this software.**
