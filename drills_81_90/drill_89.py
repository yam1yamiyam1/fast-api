import asyncio  # noqa: F401
from dataclasses import dataclass, field  # noqa: F401
from typing import Any, Callable, Optional  # noqa: F401


def run_drill_89():
    """
    SCENARIO: Data Center Job Scheduler
    =====================================
    A data center runs compute jobs but limits how many can execute at the
    same time — too many concurrent jobs overheat the rack. A semaphore acts
    as the slot counter: only N jobs may run at once. Excess jobs wait until
    a slot opens. The scheduler tracks which jobs completed.

    NEW CONCEPT: asyncio.Semaphore
    ------------------------------
    asyncio.Semaphore(n) allows at most n coroutines past its gate at once.
    Pattern:
        sem = asyncio.Semaphore(n)
        async with sem:
            # at most n coroutines here simultaneously
    Use asyncio.create_task() to launch jobs concurrently, then
    asyncio.gather() to wait for all of them.
    Rule: acquire the semaphore inside the task, not before creating it —
    otherwise you block the event loop before tasks are scheduled.

    REQUIREMENTS
    ============

    1. JobResult
       - A dataclass representing the outcome of a single compute job.
       - job_id: str — the identifier label assigned to this job.
       - output: str — the result string produced when the job completes.
       - completed: bool — whether this job finished successfully;
         default value False, written as a plain field assignment, not
         a type annotation alone.

    2. Scheduler
       - A class representing the data center's job scheduler.
       - __init__(self, limit: int):
           - limit: int — the maximum number of jobs that may run
             concurrently on this scheduler.
           - self.semaphore: asyncio.Semaphore — the concurrency gate
             initialised with limit; written as = asyncio.Semaphore(limit),
             never as a type annotation alone.
           - self.results: list — the list of JobResult objects collected
             as jobs complete; initialised as an empty list using = [],
             never a type annotation alone.
       - async def run_job(self, job_id: str, work: Callable) -> None
           - job_id: str — the identifier for this job.
           - work: Callable — an async callable that takes no arguments
             and returns a string output.
           - Acquires self.semaphore with `async with`, calls await work()
             inside, creates a JobResult(job_id=job_id, output=result,
             completed=True) and appends it to self.results.
       - async def run_all(self, jobs: list) -> list
           - jobs: list — a list of (job_id, work) tuples to schedule.
           - Creates a task for each (job_id, work) pair using
             asyncio.create_task(self.run_job(job_id, work)), then awaits
             asyncio.gather(*tasks). Returns self.results.

    TESTS
    =====
    """

    # --- YOUR CODE HERE ---
    @dataclass
    class JobResult:
        job_id: str
        output: str
        completed: bool = False

    class Scheduler:
        def __init__(self, limit: int):
            self.semaphore = asyncio.Semaphore(limit)
            self.results = []

        async def run_job(self, job_id: str, work: Callable):
            async with self.semaphore:
                output = await work()
                self.results.append(
                    JobResult(job_id=job_id, output=output, completed=True)
                )

        async def run_all(self, jobs: list[tuple]):
            tasks = []
            for job_id, work in jobs:
                tasks.append(asyncio.create_task(self.run_job(job_id, work)))
            await asyncio.gather(*tasks)
            return self.results

    async def main():
        # Test 1: all jobs complete and results collected
        scheduler = Scheduler(limit=2)

        async def job_a():
            return "output-A"

        async def job_b():
            return "output-B"

        async def job_c():
            return "output-C"

        results = await scheduler.run_all(
            [
                ("J-1", job_a),
                ("J-2", job_b),
                ("J-3", job_c),
            ]
        )
        ids = {r.job_id for r in results}
        outputs = {r.output for r in results}
        print("Test 1: all jobs completed")
        print(f"  job_ids={sorted(ids)}")
        print(f"  outputs={sorted(outputs)}")
        assert ids == {"J-1", "J-2", "J-3"}
        assert outputs == {"output-A", "output-B", "output-C"}
        assert all(r.completed is True for r in results)
        print("  PASS")

        # Test 2: semaphore limits concurrency — at most `limit` jobs at once
        active = []
        peak = []

        async def tracked_job():
            active.append(1)
            peak.append(len(active))
            await asyncio.sleep(0.01)
            active.pop()
            return "done"

        sched2 = Scheduler(limit=2)
        await sched2.run_all(
            [
                ("T-1", tracked_job),
                ("T-2", tracked_job),
                ("T-3", tracked_job),
                ("T-4", tracked_job),
            ]
        )
        print("Test 2: concurrency capped at semaphore limit")
        print(f"  peak_concurrent={max(peak)}")
        assert max(peak) <= 2
        print("  PASS")

        # Test 3: results default not shared between Scheduler instances
        s1 = Scheduler(limit=1)
        s2 = Scheduler(limit=1)
        s1.results.append(JobResult(job_id="X", output="x"))
        print("Test 3: results mutable default isolation")
        print(f"  s1.results count={len(s1.results)}")
        print(f"  s2.results count={len(s2.results)}")
        assert len(s1.results) == 1
        assert len(s2.results) == 0
        print("  PASS")

        # Test 4: JobResult completed default is False before run
        jr = JobResult(job_id="Z", output="")
        print("Test 4: JobResult completed defaults to False")
        print(f"  completed={jr.completed}")
        assert jr.completed is False
        print("  PASS")

    asyncio.run(main())


run_drill_89()


# EXPECTED OUTPUT
# ===============
# Test 1: all jobs completed
#   job_ids=['J-1', 'J-2', 'J-3']
#   outputs=['output-A', 'output-B', 'output-C']
#   PASS
# Test 2: concurrency capped at semaphore limit
#   peak_concurrent=2
#   PASS
# Test 3: results mutable default isolation
#   s1.results count=1
#   s2.results count=0
#   PASS
# Test 4: JobResult completed defaults to False
#   completed=False
#   PASS
