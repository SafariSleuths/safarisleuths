import json
from typing import TypedDict, List

from api.redis_client import redis_client

REDIS_KEY = 'sessions'


class Session(TypedDict):
    id: str
    name: str


def session_exists(session_id: str) -> bool:
    return redis_client.hget(REDIS_KEY, session_id) is not None


def get_sessions() -> List[Session]:
    return [json.loads(s) for s in redis_client.hvals(REDIS_KEY)]


def save_session(session: Session) -> None:
    redis_client.hset(REDIS_KEY, session['id'], json.dumps(session))
