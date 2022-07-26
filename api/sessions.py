import json
from typing import TypedDict, List

import flask
from flask import request

from api.redis_client import redis_client

REDIS_KEY = 'sessions'


class Session(TypedDict):
    id: str
    name: str


def must_get_session_id() -> str:
    session_id = request.args.get('session_id')
    if session_id is not None:
        if not session_exists(session_id):
            flask.abort(400, f'Session ID `{session_id}` not found.')
        if session_exists(session_id):
            return session_id

    session_id = request.headers.get('SessionID', '')
    if session_id == '':
        flask.abort(400, 'Header `SessionID` required.')
    if not session_exists(session_id):
        flask.abort(400, f'Session ID `{session_id}` not found.')
    return session_id


def session_exists(session_id: str) -> bool:
    return redis_client.hget(REDIS_KEY, session_id) is not None


def get_sessions() -> List[Session]:
    return [json.loads(s) for s in redis_client.hvals(REDIS_KEY)]


def save_session(session: Session) -> None:
    redis_client.hset(REDIS_KEY, session['id'], json.dumps(session))
