import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.scrapers.kravi_hora_scraper import fetch_occupancy
from src.storage import append_record, read_records

templates = Jinja2Templates(directory="templates")

INTERVAL = 15 * 60  # 15 minutes


async def collector_loop():
    while True:
        try:
            value = fetch_occupancy()

            if value is not None:
                append_record(value)
                print(f"[COLLECTED] {value}")
            else:
                print("[COLLECTED] no data")
        except Exception as e:
            print(f"[ERROR] Collector failed: {e}")

        await asyncio.sleep(INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(collector_loop())
    print("[LIFESPAN] Collector started")

    yield  # Aplikace běží

    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    print("[LIFESPAN] Collector finished")


app = FastAPI(lifespan=lifespan)

@app.get("/data")
def get_data(start: str | None = Query(None), end: str | None = Query(None), limit: int | None = Query(None)):
    data = read_records(start, end)

    if limit:
        data = data[-limit:]

    return data


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
