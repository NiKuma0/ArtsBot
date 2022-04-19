from .user import register_user_handlers
from .base import register_base_handler
from .artist import register_artist_handler
from .admin import register_admin_handler
from .orders import register_orders_handler
from .comments import register_comments_handler

__all__ = (
    register_base_handler,
    register_admin_handler,
    register_user_handlers,
    register_artist_handler,
    register_orders_handler,
    register_comments_handler,
)
