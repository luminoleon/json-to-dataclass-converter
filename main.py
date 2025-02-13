import os
import sys
import time
import webbrowser

from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi.responses import HTMLResponse

from api.bodies import Json2DataclassBody
from json_dataclass_converter import DataClassGenerator
from api.responses import ErrorResponse, Json2DataclassResponse, Message

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    host = "127.0.0.1"
    port = 8000
    if "--host" in sys.argv:
        host = sys.argv[sys.argv.index("--host") + 1]
    if "--port" in sys.argv:
        port = sys.argv[sys.argv.index("--port") + 1]
    url = f"http://{host}:{port}"
    time.sleep(1)
    open_browser_if_desktop(url)
    yield


app = FastAPI(lifespan=lifespan)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)


def open_browser_if_desktop(url: str):
    time.sleep(1)
    if sys.platform == "win32" or sys.platform == "darwin":
        webbrowser.open(url)
    if sys.platform == "linux" and os.getenv("DISPLAY"):
        webbrowser.open(url)


@app.post("/json2dataclass")
@limiter.limit("10/second")
async def json2dataclass(request: Request, body: Json2DataclassBody):
    try:
        if not body.class_name:
            builder = DataClassGenerator(use_dataclass_json=True)
        else:
            builder = DataClassGenerator(
                body.class_name, use_dataclass_json=True
            )
        builder.from_json(body.json_string)
        return Json2DataclassResponse(
            message=Message.SUCCESS,
            data=builder.to_string(with_imports=body.with_imports),
        )
    except Exception as e:
        return ErrorResponse(message=Message.ERROR, data=str(e))


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>JSON to Dataclass</title>
    </head>
    <body>
        <h1>JSON to Dataclass Converter</h1>
        <form id="json2dataclass-form">
            <label for="withImports">With Imports:</label>
            <input type="checkbox" id="withImports" name="withImports" checked><br><br>
            <label for="className">Class Name:</label>
            <input type="text" id="className" name="className"><br><br>
            <label for="jsonString">JSON String:</label><br>
            <textarea id="jsonString" name="jsonString" rows="10" cols="50"></textarea><br><br>
            <input type="button" value="Convert" onclick="convertJsonToDataclass()">
        </form>
        <pre id="result"></pre>
        <script>
            async function convertJsonToDataclass() {
                const className = document.getElementById('className').value;
                const jsonString = document.getElementById('jsonString').value;
                const withImports = document.getElementById('withImports').checked;
                const response = await fetch('/json2dataclass', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ className: className, jsonString: jsonString, withImports: withImports })
                });
                const result = await response.json();
                document.getElementById('result').textContent = result.data;
            }
        </script>
        <footer>
            <p>&copy; 2025 Luminoleon. All rights reserved.</p>
        </footer>
    </body>
    </html>
    """
