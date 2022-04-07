from .user import register_user_handlers
from .base import register_base_handler
from .artist import register_artist_handler
from .admin import register_admin_handler

__all__ = (
    register_base_handler,
    register_user_handlers,
    register_admin_handler,
    register_artist_handler,
)
