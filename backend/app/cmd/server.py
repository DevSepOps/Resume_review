"""`uvicorn app.cmd.server:app` or `python -m app.cmd.server`."""

from app.api.http.app import create_app

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.cmd.server:app", host="0.0.0.0", port=8000)
