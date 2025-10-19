from ninja import NinjaAPI
from .routers.videos import videos_router
from .routers.rag import rag_router
from .routers.digest import digest_router

# Define the main entrypoint for the entire backend API (central 'switchboard').
api = NinjaAPI()

# Mount the modular API routers onto the main API instance.
api.add_router("/videos", videos_router)
api.add_router("/rag", rag_router)
api.add_router("/digests", digest_router)
