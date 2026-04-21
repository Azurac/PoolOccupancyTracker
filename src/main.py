import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import __version__ as version
from src.collectors import ScheduleHelper
from src.pools.registry import create_collectors, get_repository, get_scraper
from src.storage.database import Database
from src.storage.occupancy_repository import DEFAULT_QUERY_LIMIT

# --- Dependency setup ---

DB_FILE = Path("data.db")
CSV_FILE = Path("data.csv")

_db = Database(DB_FILE)
_schedule = ScheduleHelper()

templates = Jinja2Templates(directory="templates")


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    _db.init("kravi_hora")
    _db.migrate_from_csv(CSV_FILE, "kravi_hora")

    collectors = create_collectors(_db, _schedule)
    tasks = [asyncio.create_task(c.run()) for c in collectors]
    print("[LIFESPAN] Collector started")

    yield

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    print("[LIFESPAN] Collector finished")


# --- App ---

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Routes ---

@app.get("/version")
def get_version():
    return {"version": version}


@app.get("/data/{pool_id}")
def get_data(pool_id: str, start: str = Query(None), end: str = Query(None), limit: int = Query(DEFAULT_QUERY_LIMIT)):
    records = get_repository(pool_id).find_by_range(start, end, limit)
    return [r.to_dict() for r in records]


@app.get("/rollout/{pool_id}")
def get_rollout(pool_id: str):
    scraper = get_scraper(pool_id)
    records = get_repository(pool_id).find_latest(scraper.config.get_rollout_limit()) if scraper else []
    return [r.to_dict() for r in records]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")