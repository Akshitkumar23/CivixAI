from .v1_router import router as v1_router
from .admin_router import router as admin_router
from .rag_router import router as rag_router
from .programmes_router import router as programmes_router

__all__ = ["v1_router", "admin_router", "rag_router", "programmes_router"]
