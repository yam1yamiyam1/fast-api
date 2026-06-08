import asyncio
import inspect
import re
from typing import Callable

from pydantic import BaseModel, ValidationError

from app.exceptions import (
    MethodNotAllowedException,
    NotFoundException,
    ValidationException,
)


def path_to_regex(pattern: str) -> re.Pattern:
    mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
    return re.compile(f"^{mod_str}$")


class Router:
    def __init__(self, prefix: str = "", concurrency_limit: int = None):
        self.prefix = prefix
        self.routes = []
        self.middleware = []
        self.on_startup = None
        self.on_shutdown = None
        self.concurrency_limit = (
            asyncio.Semaphore(concurrency_limit) if concurrency_limit else None
        )

    def register(
        self,
        method: str,
        path: str,
        handler: Callable,
        rq_model: BaseModel,
        rp_model: BaseModel,
        deps: dict = None,
    ):
        if deps is None:
            deps = {}
        self.routes.append(
            (
                method,
                path_to_regex(self.prefix + path),
                handler,
                rq_model,
                rp_model,
                deps,
            )
        )

    def add_middleware(self, func: Callable):
        self.middleware.append(func)

    def set_lifespan(self, on_startup=None, on_shutdown=None):
        self.on_startup = on_startup
        self.on_shutdown = on_shutdown

    async def start(self):
        if self.on_startup:
            await self.on_startup()

    async def stop(self):
        if self.on_shutdown:
            await self.on_shutdown()

    async def dispatch(
        self, method: str, path: str, body: dict | None, background=None
    ):
        path_matched = False

        for mid_func in self.middleware:
            if inspect.iscoroutinefunction(mid_func):
                await mid_func(method, path, body)
            else:
                mid_func(method, path, body)

        for r_method, regex, func, rq_model, rp_model, deps in self.routes:
            match = regex.match(path)
            if match:
                path_matched = True
                if r_method == method:
                    kwargs = match.groupdict()

                    if rq_model:
                        try:
                            valid_body = rq_model(**body)
                        except ValidationError:
                            raise ValidationException("Invalid request body")

                    checks = {}
                    for name, d_fn in deps.items():
                        if inspect.iscoroutinefunction(d_fn):
                            checks[name] = await d_fn()
                        else:
                            checks[name] = d_fn()

                    if self.concurrency_limit:
                        async with self.concurrency_limit:
                            if rq_model:
                                result = await func(**kwargs, body=valid_body, **checks)
                            else:
                                result = await func(**kwargs, **checks)
                    else:
                        if rq_model:
                            result = await func(**kwargs, body=valid_body, **checks)
                        else:
                            result = await func(**kwargs, **checks)

                    if rp_model:
                        if isinstance(result, dict):
                            try:
                                result = rp_model(**result).model_dump()
                            except ValidationError:
                                raise ValidationException("Invalid response body")
                        else:
                            result = result.model_dump()

                    if background:
                        for name, fn, kwargs_dict in background:
                            asyncio.create_task(fn(**kwargs_dict))

                    return result

        if path_matched:
            raise MethodNotAllowedException(f"Method not allowed: {method} {path}")
        else:
            raise NotFoundException(f"Not found: {path}")
