"""Typed state for the agent pipeline graph.

The state is the shared context every node reads from and writes to. Designing it
up front (see ADR-006) keeps the graph clean as it grows: a node returns only the
fields it changes, and LangGraph merges them into the running state using each
field's reducer.

Fields:

* ``task`` — the incoming task description. Set once at the start; every node
  reads it to know what is being asked.
* ``next`` — the supervisor's routing decision: a worker name or ``"FINISH"``.
  The conditional edge reads this to decide where to go next. Last write wins.
* ``worker_results`` — the list of results accumulated so far, one per worker
  invocation. Uses an additive reducer so each worker *appends* its result
  rather than overwriting the others — without this, only the last worker's
  output would survive and the ReportAgent would have nothing to synthesise.
* ``status`` — ``in_progress`` | ``completed`` | ``failed``; drives persistence
  and the UI.
* ``final_output`` — the synthesised answer the supervisor produces when it
  decides the run is finished.
"""

import operator
from typing import Annotated, TypedDict


class WorkerResult(TypedDict):
    """One worker's contribution to the run."""

    worker: str
    output: str


class PipelineState(TypedDict, total=False):
    """Shared, accumulating state for the agent pipeline."""

    task: str
    next: str
    worker_results: Annotated[list[WorkerResult], operator.add]
    status: str
    final_output: str
