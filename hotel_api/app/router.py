import re
from typing import Callable

from exceptions import MethodNotAllowedException, NotFoundException, ValidationException
from pydantic import BaseModel, ValidationError


def path_to_regex(pattern: str) -> re.Pattern:
    mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
    return re.compile(f"^{mod_str}$")


class Router:
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.routes = []

    def register(
        self,
        method: str,
        path: str,
        handler: Callable,
        rq_model: BaseModel,
        rp_model: BaseModel,
    ):
        self.routes.append(
            (method, path_to_regex(self.prefix + path), handler, rq_model, rp_model)
        )

    async def dispatch(self, method: str, path: str, body: dict | None):
        path_matched = False
        for r_method, regex, func, rq_model, rp_model in self.routes:
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
                        result = await func(**kwargs, body=valid_body)
                    else:
                        return await func(**kwargs)
                    if rp_model:
                        if isinstance(result, dict):
                            return rp_model(**result).model_dump()
                        elif isinstance(result, rp_model):
                            return result.model_dump()
                    else:
                        return result
        if path_matched:
            raise MethodNotAllowedException(f"Method not allowed: {method} {path}")
        else:
            raise NotFoundException(f"Not found: {path}")
