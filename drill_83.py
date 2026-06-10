import asyncio  # noqa: F401
import inspect  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, Callable, Optional  # noqa: F401


def run_drill_83():
    """
    SCENARIO: Courthouse Filing System
    ===================================
    The courthouse has a filing desk that processes case submissions.
    Before a case reaches the clerk (handler), it passes through a pipeline
    of bailiffs (middleware). Any bailiff can REJECT the case outright —
    returning an error response immediately without passing the case further.
    Only if all bailiffs approve does the clerk process the filing.

    NEW CONCEPT: Dispatch pipeline short-circuiting
    ------------------------------------------------
    A middleware chain short-circuits when one layer returns a response
    directly instead of calling next(). The handler is never reached.
    Pattern: each middleware receives a `call_next` callable. If it calls
    call_next(), the chain continues. If it returns without calling it,
    the chain is cut — the handler and all later middleware are skipped.
    Rule: short-circuit by returning early; never raise to exit the chain.

    REQUIREMENTS
    ============

    1. CaseRequest
       - A dataclass representing a case submission arriving at the courthouse.
       - case_id: str — the unique identifier printed on the filing envelope.
       - case_type: str — the category of legal matter (e.g. "civil", "criminal").
       - filed_by: str — the name of the attorney submitting the case.
       - metadata: dict — supplementary annotations attached to the filing;
         must use field(default_factory=dict), never a mutable default.

    2. CaseResponse
       - A dataclass representing the desk's reply after processing.
       - status: str — the outcome word returned to the filer ("accepted" or "rejected").
       - message: str — the plain-English explanation given back to the filer.
       - data: dict — any additional payload the clerk includes in the reply;
         must use field(default_factory=dict), never a mutable default.

    3. Courthouse
       - A class representing the filing desk and its pipeline.
       - __init__(self):
           - self.middlewares: list — the ordered list of bailiff callables
             registered on this desk; initialised as an empty list, using
             = [], never a type annotation alone.
           - self.handler: Optional[Callable] — the clerk function that
             processes approved filings; initialised to None using = None.
       - add_middleware(self, fn: Callable) -> None
           - fn: Callable — a bailiff function to append to self.middlewares.
           - Appends fn to self.middlewares. No return value.
       - set_handler(self, fn: Callable) -> None
           - fn: Callable — the clerk function that will handle approved cases.
           - Assigns fn to self.handler. No return value.
       - async dispatch(self, request: CaseRequest) -> CaseResponse
           - request: CaseRequest — the incoming filing to be processed.
           - Builds and runs the middleware chain, then calls self.handler if
             the chain is not short-circuited.
           - Chain construction: starting from the innermost layer (self.handler
             wrapped as a no-argument async callable), wrap each middleware in
             reverse order so that middlewares[0] runs first.
           - Each middleware is called as: await fn(request, call_next), where
             call_next is the next layer in the chain (no arguments).
           - If any middleware returns a CaseResponse without calling call_next,
             the handler is never reached.
           - Returns whatever CaseResponse the chain produces.

    4. Middleware functions (plain async functions, not methods)

       async def type_check_middleware(request: CaseRequest, call_next) -> CaseResponse
           - request: CaseRequest — the filing being inspected by this bailiff.
           - call_next: Callable — the next layer; call with no arguments to continue.
           - If request.case_type is not in ("civil", "criminal", "family"),
             return CaseResponse(status="rejected",
                                 message="Unknown case type: <case_type>")
             without calling call_next.
           - Otherwise call call_next() and return its result.

       async def attorney_check_middleware(request: CaseRequest, call_next) -> CaseResponse
           - request: CaseRequest — the filing being inspected by this bailiff.
           - call_next: Callable — the next layer; call with no arguments to continue.
           - If request.filed_by is an empty string, return
             CaseResponse(status="rejected", message="Attorney name required")
             without calling call_next.
           - Otherwise call call_next() and return its result.

    5. clerk_handler
       async def clerk_handler(request: CaseRequest) -> CaseResponse
           - request: CaseRequest — the approved filing reaching the clerk's desk.
           - Returns CaseResponse(status="accepted",
                                  message="Case <case_id> filed successfully",
                                  data={"filed_by": request.filed_by,
                                        "case_type": request.case_type})

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class CaseRequest:
        case_id: str
        case_type: str
        filed_by: str
        metadata: dict = field(default_factory=dict)

    @dataclass
    class CaseResponse:
        status: str
        message: str
        data: dict = field(default_factory=dict)

    class Courthouse:
        def __init__(self):
            self.middlewares = []
            self.handler: Optional[Callable] = None

        def add_middleware(self, fn: Callable):
            self.middlewares.append(fn)

        def set_handler(self, fn: Callable):
            self.handler = fn

        async def dispatch(self, request: CaseRequest) -> CaseResponse:
            async def call_next():
                return await self.handler(request)

            chain = call_next
            for mw_fn in reversed(self.middlewares):
                prev = chain

                async def call_next(mw=mw_fn, prev=prev):
                    return await mw(request, prev)

                chain = call_next
            return await chain()

    async def type_check_middleware(request: CaseRequest, call_next):

        if request.case_type not in ("civil", "criminal", "family"):
            return CaseResponse(
                status="rejected", message=f"Unknown case type: {request.case_type}"
            )
        return await call_next()

    async def attorney_check_middleware(request: CaseRequest, call_next):
        if not request.filed_by:
            return CaseResponse(status="rejected", message="Attorney name required")
        return await call_next()

    async def clerk_handler(request: CaseRequest):

        return CaseResponse(
            status="accepted",
            message=f"Case {request.case_id} filed successfully",
            data={"filed_by": request.filed_by, "case_type": request.case_type},
        )

    async def main():
        desk = Courthouse()
        desk.add_middleware(type_check_middleware)
        desk.add_middleware(attorney_check_middleware)
        desk.set_handler(clerk_handler)

        # Test 1: valid case passes through entire chain
        req1 = CaseRequest(case_id="C-001", case_type="civil", filed_by="Atty. Reyes")
        resp1 = await desk.dispatch(req1)
        print("Test 1: valid case accepted")
        print(f"  status={resp1.status!r}, message={resp1.message!r}")
        print(f"  data={resp1.data}")
        assert resp1.status == "accepted"
        assert resp1.message == "Case C-001 filed successfully"
        assert resp1.data == {"filed_by": "Atty. Reyes", "case_type": "civil"}
        print("  PASS")

        # Test 2: unknown case_type — short-circuits at type_check_middleware
        req2 = CaseRequest(case_id="C-002", case_type="maritime", filed_by="Atty. Cruz")
        resp2 = await desk.dispatch(req2)
        print("Test 2: unknown case type rejected by first bailiff")
        print(f"  status={resp2.status!r}, message={resp2.message!r}")
        assert resp2.status == "rejected"
        assert resp2.message == "Unknown case type: maritime"
        print("  PASS")

        # Test 3: empty attorney — passes type check, short-circuits at attorney_check
        req3 = CaseRequest(case_id="C-003", case_type="criminal", filed_by="")
        resp3 = await desk.dispatch(req3)
        print("Test 3: missing attorney rejected by second bailiff")
        print(f"  status={resp3.status!r}, message={resp3.message!r}")
        assert resp3.status == "rejected"
        assert resp3.message == "Attorney name required"
        print("  PASS")

        # Test 4: metadata default is not shared between instances
        req4a = CaseRequest(
            case_id="C-004", case_type="family", filed_by="Atty. Santos"
        )
        req4b = CaseRequest(case_id="C-005", case_type="family", filed_by="Atty. Lim")
        req4a.metadata["priority"] = "urgent"
        print("Test 4: metadata mutable default isolation")
        print(f"  req4a.metadata={req4a.metadata}")
        print(f"  req4b.metadata={req4b.metadata}")
        assert req4a.metadata == {"priority": "urgent"}
        assert req4b.metadata == {}
        print("  PASS")

        # Test 5: CaseResponse data default is not shared between instances
        resp5a = CaseResponse(status="accepted", message="ok")
        resp5b = CaseResponse(status="accepted", message="ok")
        resp5a.data["note"] = "sealed"
        print("Test 5: CaseResponse data mutable default isolation")
        print(f"  resp5a.data={resp5a.data}")
        print(f"  resp5b.data={resp5b.data}")
        assert resp5a.data == {"note": "sealed"}
        assert resp5b.data == {}
        print("  PASS")

    asyncio.run(main())


run_drill_83()


# EXPECTED OUTPUT
# ===============
# Test 1: valid case accepted
#   status='accepted', message='Case C-001 filed successfully'
#   data={'filed_by': 'Atty. Reyes', 'case_type': 'civil'}
#   PASS
# Test 2: unknown case type rejected by first bailiff
#   status='rejected', message='Unknown case type: maritime'
#   PASS
# Test 3: missing attorney rejected by second bailiff
#   status='rejected', message='Attorney name required'
#   PASS
# Test 4: metadata mutable default isolation
#   req4a.metadata={'priority': 'urgent'}
#   req4b.metadata={}
#   PASS
# Test 5: CaseResponse data mutable default isolation
#   resp5a.data={'note': 'sealed'}
#   resp5b.data={}
#   PASS
