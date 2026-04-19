import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src import __version__ as version
from src.collectors.collector_loop import CollectorLoop
from src.collectors.schedule_helper import ScheduleHelper
from src.config import DB_FILE, CSV_FILE, DEFAULT_QUERY_LIMIT, ROLLOUT_LIMIT
from src.scrapers.kravi_hora_scraper import KraviHoraScraper
from src.storage.database import Database
from src.storage.occupancy_repository import OccupancyRepository

# --- Dependency setup ---

_db = Database(DB_FILE)
_repository = OccupancyRepository(_db)
_scraper = KraviHoraScraper()
_schedule = ScheduleHelper()
_collector = CollectorLoop(_scraper, _repository, _schedule)

templates = Jinja2Templates(directory="templates")


# --- Lifespan ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    _db.init()
    _db.migrate_from_csv(CSV_FILE)

    task = asyncio.create_task(_collector.run())
    print("[LIFESPAN] Collector started")

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    print("[LIFESPAN] Collector finished")


# --- App ---

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Routes ---

@app.get("/version")
def get_version():
    return {"version": version}


@app.get("/data")
def get_data(start: str = Query(None), end: str = Query(None), limit: int = Query(DEFAULT_QUERY_LIMIT)):
    records = _repository.find_by_range(start, end, limit)
    return [r.to_dict() for r in records]


@app.get("/rollout")
def get_rollout():
    records = _repository.find_latest(ROLLOUT_LIMIT)
    return [r.to_dict() for r in records]


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")