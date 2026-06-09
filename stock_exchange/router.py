import asyncio
import inspect
from dataclasses import dataclass, field
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
    deps: dict[str, Callable] = field(default_factory=dict)


class Router:
    def __init__(self, max_concurrency: int = 10):
        self.registry = []
        self.middleware_list = []
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self._lifespan_fn = None
        self._lifespan_ctx = None

    def register(
        self,
        method: str,
        path: str,
        handler: Callable,
        request_model: Optional[type],
        response_model: type,
        deps: dict[str, Callable] = None,
    ):
        deps = deps or {}
        entry = RouteEntry(
            method, path_to_regex(path), handler, request_model, response_model, deps
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

    def add_middleware(self, func: Callable):
        self.middleware_list.append(func)

    async def _run_middleware(self, context: dict):
        for md_func in self.middleware_list:
            if inspect.iscoroutinefunction(md_func):
                await md_func(context)
            else:
                md_func(context)

    def set_lifespan(self, func: Callable):
        self._lifespan_fn = func

    async def start(self):
        if self._lifespan_fn:
            self._lifespan_ctx = self._lifespan_fn()
            await self._lifespan_ctx.__aenter__()

    async def stop(self):
        if self._lifespan_ctx:
            await self._lifespan_ctx.__aexit__(None, None, None)

    async def _schedule_tasks(self, background_tasks: list[Callable]):
        for func in background_tasks:
            if inspect.iscoroutinefunction(func):
                asyncio.create_task(func())
            else:
                asyncio.create_task(asyncio.to_thread(func))

    async def _resolve_deps(self, deps: dict):
        resolved = {}
        for name, dep_func in deps.items():
            if inspect.iscoroutinefunction(dep_func):
                resolved[name] = await dep_func()
            else:
                resolved[name] = dep_func()
        return resolved

    async def dispatch(
        self,
        method: str,
        path: str,
        body: dict | None,
        background_tasks: list[Callable] = None,
    ):

        try:
            entry, params = self._match(method, path)
        except MethodNotAllowedException as msg:
            return {"error": msg, "status_code": 405}
        except NotFoundException as msg:
            return {"error": msg, "status_code": 404}
        await self._run_middleware({"method": method, "path": path, "body": body})
        resolved = await self._resolve_deps(entry.deps)
        kwargs = {**params, **resolved}
        if entry.request_model:
            try:
                valid_rq = entry.request_model(**body)
                kwargs["body"] = valid_rq
            except ValidationError as msg:
                return {"error": msg, "status_code": 422}
        try:
            async with self.semaphore:
                result = await entry.handler(**kwargs)
        except NotFoundException as msg:
            return {"error": msg, "status_code": 404}
        if background_tasks:
            await self._schedule_tasks(background_tasks)
        if entry.response_model:
            try:
                valid_rp = entry.response_model(**result)
                result = valid_rp.model_dump()
            except ValidationError as msg:
                return {"error": msg, "status_code": 422}
        return result
