import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, time

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import __version__ as version
from src.scrapers.kravi_hora_scraper import fetch_occupancy
from src.storage import append_record, read_records, init_db, migrate_from_csv

templates = Jinja2Templates(directory="templates")

INTERVAL_MINUTES = 10


def seconds_until_next_interval(interval_minutes: int) -> float:
    now = datetime.now()
    remainder = now.minute % interval_minutes
    minutes_to_add = interval_minutes - remainder

    next_run = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
    return (next_run - now).total_seconds()


def check_visit_hours(start: int, end: int) -> bool:
    now = datetime.now()
    return time(hour=start) < now.time() < time(hour=end)


async def collector_loop():
    while True:
        try:
            if check_visit_hours(6, 22):
                sleep_seconds = seconds_until_next_interval(INTERVAL_MINUTES)
            else:
                now = datetime.now()
                sleep_seconds = (
                        (now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)) - now
                ).total_seconds()

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
    init_db()
    migrate_from_csv()

    task = asyncio.create_task(collector_loop())
    print("[LIFESPAN] Collector started")

    # Starts application
    yield

    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    print("[LIFESPAN] Collector finished")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/version")
def get_version():
    return {"version": version}


@app.get("/data")
def get_data(start: str = Query(None), end: str = Query(None), limit: int = Query(None)):
    data = read_records(start, end)

    if limit:
        data = data[-limit:]

    return data


@app.get("/rollout")
def get_rollout():
    data = read_records()
    open_hours = 16
    limit = open_hours * int(60 / INTERVAL_MINUTES) + 1
    return data[-limit:]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")
