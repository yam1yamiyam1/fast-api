import asyncio  # noqa: F401
import inspect  # noqa: F401
import re  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Callable, Optional  # noqa: F401


def run_drill_81():
    """
    Scenario: University Course Registry
    The university needs a request dispatcher for its course management system.
    Handlers are registered by path pattern and method. Incoming requests are
    matched, dependencies are resolved, and handlers are called with merged
    kwargs.

    Requirements:
    - A RouteEntry dataclass with fields: method (str), pattern (str),
      handler (Callable), deps (list of Callable). deps must default to an
      empty list without using [] as the default value.
    - A path_to_regex function that converts a path like "/courses/{code}"
      into a compiled regex that captures named groups.
    - A Router class with:
        - An __init__ that initialises an internal list of RouteEntry objects
          using assignment, not annotation.
        - A register method that accepts method, path, handler, and an optional
          deps list, and appends a RouteEntry to the internal list.
        - A _match method that accepts method and path, iterates all entries,
          and returns (entry, path params dict) for the first match.
          Returns (None, None) if no entry matches the path at all.
          Returns ("405", None) if a path matches but the method does not.
        - A _resolve_deps method that accepts an entry and returns a dict of
          resolved dependency values, keyed by the dep function's __name__.
        - A dispatch method that accepts method, path, and an optional body
          dict. It must: resolve the match, raise a 405 string error if method
          mismatch, raise a 404 string error if no match, resolve deps, cast
          any path param values that look like integers to int, then call the
          handler with path params, deps, and body merged as kwargs.
    - All Router methods must have self as the first parameter.
    - Two Router instances must never share the same internal route list.
    - Two RouteEntry instances with no deps argument must never share the same
      deps list.
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class RouteEntry:
        method: str
        pattern: str
        handler: Callable
        deps: list[Callable] = field(default_factory=list)

    def path_to_regex(pattern: str) -> re.Pattern:

        mod_str = re.sub(r"\{([^}]+)\}", r"(?P<\g<1>>[^/]+)", pattern)
        return re.compile(f"^{mod_str}$")

    class Router:
        def __init__(self):
            self.routes = []

        def register(
            self,
            method: str,
            path: str,
            handler: Callable,
            deps: list[Callable] | None = None,
        ):
            deps = deps or []
            self.routes.append(RouteEntry(method, path_to_regex(path), handler, deps))

        def _match(self, method: str, path: str):
            path_matched = False
            for entry in self.routes:
                match = entry.pattern.match(path)
                if match:
                    path_matched = True
                    if entry.method == method:
                        params = match.groupdict()
                        return entry, params
            if path_matched:
                return ("405", None)
            else:
                return (None, None)

        def _resolve_deps(self, entry: RouteEntry):
            resolved = {}
            for dep_func in entry.deps:
                resolved[dep_func.__name__] = dep_func()
            return resolved

        def dispatch(self, method: str, path: str, body: Optional[dict] = None):
            entry, params = self._match(method, path)
            if entry == "405":
                raise ValueError("405")
            if entry is None:
                raise ValueError("404")
            for k, v in params.items():
                if isinstance(v, str) and v.isdigit():
                    params[k] = int(v)
            resolved = self._resolve_deps(entry)
            kwargs = {**params, **resolved, **(body or {})}
            return entry.handler(**kwargs)

    # Tests
    print("Test 1: RouteEntry deps default is independent per instance")
    e1 = RouteEntry(method="GET", pattern="/a", handler=lambda: None)
    e2 = RouteEntry(method="GET", pattern="/b", handler=lambda: None)
    e1.deps.append("x")
    assert "x" not in e2.deps, f"Shared deps list: {e2.deps}"
    print(f"  e1.deps={e1.deps}, e2.deps={e2.deps}")
    print("  PASS")

    print("Test 2: Two Router instances have independent route lists")
    r1 = Router()
    r2 = Router()
    r1.register("GET", "/courses/{code}", lambda code: code)
    assert len(r2.routes) == 0, f"r2 should be empty, got: {r2.routes}"
    print(f"  r1 routes={len(r1.routes)}, r2 routes={len(r2.routes)}")
    print("  PASS")

    print(
        "Test 3: _match returns entry and params on hit, 405 on method mismatch, None pair on miss"
    )
    router = Router()

    def get_course(code: int):
        return {"code": code}

    router.register("GET", "/courses/{code}", get_course)

    entry, params = router._match("GET", "/courses/42")
    assert entry is not None
    assert params == {"code": "42"}

    result_405, _ = router._match("POST", "/courses/42")
    assert result_405 == "405"

    result_none, params_none = router._match("GET", "/unknown")
    assert result_none is None and params_none is None

    print(f"  match params={params}, 405={result_405}, miss={result_none}")
    print("  PASS")

    print("Test 4: dispatch resolves deps, casts int params, calls handler")
    router2 = Router()

    def auth_dep():
        return "student_user"

    def fetch_course(code: int, auth_dep: str):
        return {"code": code, "user": auth_dep}

    router2.register("GET", "/courses/{code}", fetch_course, deps=[auth_dep])

    result = router2.dispatch("GET", "/courses/7")
    assert result == {"code": 7, "user": "student_user"}, f"Got: {result}"
    print(f"  result={result}")
    print("  PASS")

    print("Test 5: dispatch raises 404 and 405 correctly")
    try:
        router2.dispatch("GET", "/no/such/path")
        assert False, "Should have raised"
    except Exception as e:
        assert "404" in str(e), f"Expected 404, got: {e}"

    try:
        router2.dispatch("DELETE", "/courses/1")
        assert False, "Should have raised"
    except Exception as e:
        assert "405" in str(e), f"Expected 405, got: {e}"

    print("  404 and 405 raised correctly")
    print("  PASS")


run_drill_81()

# --- Expected Output ---
# Test 1: RouteEntry deps default is independent per instance
#   e1.deps=['x'], e2.deps=[]
#   PASS
# Test 2: Two Router instances have independent route lists
#   r1 routes=1, r2 routes=0
#   PASS
# Test 3: _match returns entry and params on hit, 405 on method mismatch, None pair on miss
#   match params={'code': '42'}, 405=405, miss=None
#   PASS
# Test 4: dispatch resolves deps, casts int params, calls handler
#   result={'code': 7, 'user': 'student_user'}
#   PASS
# Test 5: dispatch raises 404 and 405 correctly
#   404 and 405 raised correctly
#   PASS
