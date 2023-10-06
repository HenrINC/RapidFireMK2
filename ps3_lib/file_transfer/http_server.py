import fastapi
from fastapi import Request, Response
import uvicorn

app = fastapi.FastAPI()

files:dict[str, bytes] = {}

@app.get("/{file_id}")
async def get_file(file_id: str):
    return Response(content=files[file_id], media_type="application/octet-stream")

@app.put("/{file_id}")
async def put_file(file_id: str, request: Request):
    files[file_id] = await request.body()
    return {"status": "ok"}

@app.delete("/{file_id}")
async def delete_file(file_id: str):
    del files[file_id]
    return {"status": "ok"}

def get_server(port):
    return uvicorn.Server(
        uvicorn.Config(
            app,
            port=port,
            log_level="warning",
            access_log=False,
            lifespan="off",
        )
    )