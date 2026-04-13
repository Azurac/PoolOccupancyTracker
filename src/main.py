import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, time

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.scrapers.kravi_hora_scraper import fetch_occupancy
from src.storage import append_record, read_records

templates = Jinja2Templates(directory="templates")

INTERVAL_MINUTES = 10

def seconds_until_next_interval(interval_minutes: int) -> float:
    now = datetime.now()

    remainder = now.minute % interval_minutes
    minutes_to_add = interval_minutes - remainder

    next_run = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)

    delta = next_run - now
    return delta.total_seconds()

def check_visit_hours(start: int, end: int) -> bool:
    now = datetime.now()
    return time(hour=start, minute=0, second=0) < now.time() < time(hour=end, minute=0, second=0)

async def collector_loop():
        while True:
            try:
                if check_visit_hours(6, 22):
                    sleep_seconds = seconds_until_next_interval(INTERVAL_MINUTES)
                else:
                    now = datetime.now()
                    sleep_seconds = ((now.replace(hour=6, minute=0,second=0, microsecond=0) + timedelta(days=1)) - now).total_seconds()
                await asyncio.sleep(sleep_seconds)

                value = fetch_occupancy()

                if value is not None:
                    append_record(value)
                    print(f"[COLLECTED] {value}")
                else:
                    print("[COLLECTED] no data")
            except Exception as e:
                print(f"[ERROR] Collector failed: {e}")


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
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/data")
def get_data(start: str | None = Query(None), end: str | None = Query(None), limit: int | None = Query(None)):
    data = read_records(start, end)

    if limit:
        data = data[-limit:]

    return data


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
