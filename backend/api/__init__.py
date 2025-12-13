"""API routes package."""

from .auth import auth_bp
from .screen_time import screen_time_bp
from .badges import badges_bp
from .friendship import friendship_bp
from .leaderboard import leaderboard_bp
from .challenges import challenges_bp

__all__ = [
    'auth_bp',
    'screen_time_bp',
    'badges_bp',
    'friendship_bp',
    'leaderboard_bp',
    'challenges_bp',
]
