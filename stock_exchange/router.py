from dataclasses import dataclass
from typing import Callable, Optional

from exceptions import MethodNotAllowedException, NotFoundException
from pydantic import ValidationError
from regex import path_to_regex


@dataclass
class RouteEntry:
    method: str
    path: str
    handler: Callable
    request_model: Optional[type]
    response_model: type


class Router:
    def __init__(self):
        self.registry = []

    def register(
        self,
        method: str,
        path: str,
        handler: Callable,
        request_model: Optional[type],
        response_model: type,
    ):
        entry = RouteEntry(
            method, path_to_regex(path), handler, request_model, response_model
        )
        self.registry.append(entry)

    def _match(self, method: str, path: str):
        path_matched = False
        for entry in self.registry:
            match = entry.path.match(path)
            if match:
                path_matched = True
                if entry.method == method:
                    params = {k: int(v) for k, v in match.groupdict().items()}
                    return entry, params
        if path_matched:
            raise MethodNotAllowedException("Method not allowed")
        else:
            raise NotFoundException("Path not found")

    async def dispatch(self, method: str, path: str, body: dict | None):
        try:
            entry, params = self._match(method, path)
        except MethodNotAllowedException as msg:
            return {"error": msg, "status_code": 405}
        except NotFoundException as msg:
            return {"error": msg, "status_code": 404}
        kwargs = {**params}
        if entry.request_model:
            try:
                valid_rq = entry.request_model(**body)
                kwargs["body"] = valid_rq
            except ValidationError as msg:
                return {"error": msg, "status_code": 422}
        try:
            result = await entry.handler(**kwargs)
        except NotFoundException as msg:
            return {"error": msg, "status_code": 404}
        if entry.response_model:
            try:
                valid_rp = entry.response_model(**result)
                result = valid_rp.model_dump()
            except ValidationError as msg:
                return {"error": msg, "status_code": 422}
        return result
