import re  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, Callable, Optional  # noqa: F401

from regex import path_to_regex


def run_drill_86():
    """
    SCENARIO: Police Station Incident Desk
    =======================================
    The incident desk at a police station routes incoming reports to the
    correct officer. Each route has a path pattern and an allowed method.
    If the path matches but the method is wrong, the desk rejects with
    "Method Not Allowed". If the path doesn't match anything, it rejects
    with "Not Found". Only if both match does the report reach the officer.

    NEW CONCEPT: 404 vs 405 routing logic
    --------------------------------------
    When matching routes, track two outcomes separately:
      - Path matched but method wrong  → 405 Method Not Allowed
      - No path matched at all         → 404 Not Found
    Rule: never raise inside the loop. Collect match results first,
    then raise after the loop based on what was found.
    Pattern:
      path_matched = False
      for route in routes:
          if path matches:
              path_matched = True
              if method matches:
                  return handler
      if path_matched:
          raise 405
      raise 404

    REQUIREMENTS
    ============

    1. RouteEntry
       - A dataclass representing one registered route at the desk.
       - path: str — the URL-style path pattern for this route
         (e.g. "/incident/{id}").
       - method: str — the HTTP-style method this route accepts
         (e.g. "GET", "POST").
       - handler: Callable — the officer function called when this route matches.
       - params: dict — extracted path parameters parsed from the URL;
         must use field(default_factory=dict), never a mutable default.

    2. IncidentRouter
       - A class representing the incident desk.
       - __init__(self):
           - self.routes: list — the ordered list of RouteEntry objects
             registered on this desk; initialised as an empty list using
             = [], never a type annotation alone.
       - def add_route(self, path: str, method: str, handler: Callable) -> None
           - path: str — the path pattern to register.
           - method: str — the method this route accepts.
           - handler: Callable — the officer to call on match.
           - Converts path to a regex by replacing {param} with a named
             capture group (?P<param>[^/]+), then appends a RouteEntry
             to self.routes. Store the regex string on the entry as
             entry.path (overwrite the original pattern string).
       - def resolve(self, path: str, method: str) -> dict
           - path: str — the incoming report's path to match.
           - method: str — the incoming report's method to match.
           - Iterates self.routes. For each entry, test entry.path as a
             regex against path using re.fullmatch.
           - Tracks whether any path matched using a local bool, initialised
             to False before the loop. Never raise inside the loop.
           - After the loop:
               - If path matched but no method matched: raise ValueError
                 with message "405 Method Not Allowed".
               - If no path matched: raise ValueError with message
                 "404 Not Found".
           - On full match (path + method): extract named groups from the
             match into a dict and return a context dict built manually
             with keys "handler", "params", "method" — never use {**entry}
             or similar unpacking of the RouteEntry object itself.

    3. Handler functions (plain functions, not methods)

       def get_incident(params: dict) -> str
           - params: dict — the extracted path parameters from the URL.
           - Returns "Fetching incident <params['id']>".

       def file_incident(params: dict) -> str
           - params: dict — the extracted path parameters from the URL.
           - Returns "Filing new incident".

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class RouteEntry:
        path: str
        method: str
        handler: Callable
        params: dict = field(default_factory=dict)

    class IncidentRouter:
        def __init__(self):
            self.routes = []

        def add_route(self, path: str, method: str, handler: Callable):
            self.routes.append(RouteEntry(path_to_regex(path), method, handler))

        def resolve(self, path: str, method: str):
            path_matched = False
            for entry in self.routes:
                match = entry.path.fullmatch(path)
                if match:
                    path_matched = True
                    params = match.groupdict()
                    if method == entry.method:
                        return {
                            "handler": entry.handler,
                            "params": params,
                            "method": entry.method,
                        }
            if path_matched:
                raise ValueError("405 Method Not Allowed")
            else:
                raise ValueError("404 Not Found")

    def get_incident(params: dict):
        return f"Fetching incident {params['id']}"

    def file_incident(params: dict):
        return "Filing new incident"

    # Test 1: GET match returns correct context
    router = IncidentRouter()
    router.add_route("/incident/{id}", "GET", get_incident)
    router.add_route("/incident", "POST", file_incident)

    ctx1 = router.resolve("/incident/42", "GET")
    print("Test 1: GET /incident/42 matched")
    print(f"  handler={ctx1['handler'].__name__!r}")
    print(f"  params={ctx1['params']}")
    print(f"  method={ctx1['method']!r}")
    assert ctx1["handler"] is get_incident
    assert ctx1["params"] == {"id": "42"}
    assert ctx1["method"] == "GET"
    print("  PASS")

    # Test 2: POST match returns correct context
    ctx2 = router.resolve("/incident", "POST")
    print("Test 2: POST /incident matched")
    print(f"  handler={ctx2['handler'].__name__!r}")
    print(f"  params={ctx2['params']}")
    assert ctx2["handler"] is file_incident
    assert ctx2["params"] == {}
    print("  PASS")

    # Test 3: path matches but wrong method → 405
    print("Test 3: wrong method raises 405")
    try:
        router.resolve("/incident/42", "POST")
        assert False, "should have raised"
    except ValueError as e:
        print(f"  error={str(e)!r}")
        assert str(e) == "405 Method Not Allowed"
    print("  PASS")

    # Test 4: no path match → 404
    print("Test 4: unknown path raises 404")
    try:
        router.resolve("/unknown", "GET")
        assert False, "should have raised"
    except ValueError as e:
        print(f"  error={str(e)!r}")
        assert str(e) == "404 Not Found"
    print("  PASS")

    # Test 5: RouteEntry params default not shared between instances
    r1 = RouteEntry(path="/a", method="GET", handler=get_incident)
    r2 = RouteEntry(path="/b", method="GET", handler=get_incident)
    r1.params["case"] = "open"
    print("Test 5: RouteEntry params mutable default isolation")
    print(f"  r1.params={r1.params}")
    print(f"  r2.params={r2.params}")
    assert r1.params == {"case": "open"}
    assert r2.params == {}
    print("  PASS")

    # Test 6: handler called via context dict works correctly
    result6 = ctx1["handler"](ctx1["params"])
    print("Test 6: handler called via context dict")
    print(f"  result={result6!r}")
    assert result6 == "Fetching incident 42"
    print("  PASS")


run_drill_86()


# EXPECTED OUTPUT
# ===============
# Test 1: GET /incident/42 matched
#   handler='get_incident'
#   params={'id': '42'}
#   method='GET'
#   PASS
# Test 2: POST /incident matched
#   handler='file_incident'
#   params={}
#   PASS
# Test 3: wrong method raises 405
#   error='405 Method Not Allowed'
#   PASS
# Test 4: unknown path raises 404
#   error='404 Not Found'
#   PASS
# Test 5: RouteEntry params mutable default isolation
#   r1.params={'case': 'open'}
#   r2.params={}
#   PASS
# Test 6: handler called via context dict
#   result='Fetching incident 42'
#   PASS
