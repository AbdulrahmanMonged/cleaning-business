from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.api import main

app = FastAPI()
app.include_router(main.router)


@app.exception_handler(StarletteHTTPException)
async def general_req_handler(req: Request, exc: StarletteHTTPException):
    return JSONResponse(
        content={"message", exc.detail},
        headers=exc.headers,
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def general_validation_error(req: Request, exc: RequestValidationError):
    return JSONResponse(
        content={"message": ", ".join((err.get("msg") for err in exc.errors()))},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
