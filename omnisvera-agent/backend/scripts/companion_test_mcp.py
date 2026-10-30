"""Local MCP tools for other AIs. Stdio only; no public port or live credentials."""
from contextlib import asynccontextmanager
from typing import Annotated, Literal, Any
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

try:
    from .agent_test_jobs import TestJobs, capabilities
except ImportError:
    from agent_test_jobs import TestJobs, capabilities


class TestRunResponse(BaseModel):
    schema_version: Literal[1]
    run_id: str
    request_id: str
    actors: list[Literal['raziel','morthak','vezemir','dorn7']]
    scenarios: list[str]
    ui: bool = False
    ui_suite: Literal['full','combat','lightning','hemomancy','vampiric','necromancy','rest','passives','summon_turns','friday','oct24','monster_defaults','active_spells','catalog','inventory_summons','sprite_studio','item_families'] = 'full'
    certification_ready: bool = False
    state: Literal['RUNNING','COMPLETED','ERROR','CANCELLED','INTERRUPTED']
    verdict: Literal['PASS','FAIL','INCONCLUSIVE']
    production_modified: Literal[False]
    created_at: float
    finished_at: float | None = None
    exit_code: int | None = None
    error: str | None = None
    report: dict[str, Any] | None = None
    partial_report: dict[str, Any] | None = None
    progress: dict[str, Any] | None = None


def create_server(manager_factory=TestJobs):
    holder={}

    def jobs():
        if 'jobs' not in holder:holder['jobs']=manager_factory()
        return holder['jobs']

    @asynccontextmanager
    async def lifespan(server):
        try:yield {}
        finally:
            if 'jobs' in holder:holder['jobs'].close()

    server=FastMCP('Omnisvera Companion Tests',instructions=
        'Use these tools to discover, run and inspect native sheet rehearsals. '
        'They never apply proposals to live state. Retain request_id/run_id for retries. '
        'COMPLETED/FAIL is a real failed test; ERROR/INCONCLUSIVE is a harness problem. '
        'PASS certifies only cited scenarios, never all abilities or real-network reliability.',
        lifespan=lifespan,log_level='WARNING')

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True,destructiveHint=False,openWorldHint=False))
    def companion_test_capabilities() -> dict[str, Any]:
        """Discover supported actors, suite, inputs, verdicts and safety limits. No campaign writes."""
        return capabilities()

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False,destructiveHint=False,idempotentHint=True,openWorldHint=False))
    def companion_test_start(
        request_id: Annotated[str,Field(min_length=8,max_length=120,pattern=r'^[A-Za-z0-9._:-]+$')],
        actors: Annotated[list[Literal['raziel','morthak','vezemir','dorn7']],Field(min_length=1,max_length=4)],
        scenarios: Annotated[list[str],Field(min_length=1,max_length=100)] | None = None,
        ui: bool = False,
        ui_suite: Literal['full','combat','lightning','hemomancy','vampiric','necromancy','rest','passives','summon_turns','friday','oct24','monster_defaults','active_spells','catalog','inventory_summons','sprite_studio','item_families'] = 'full',
    ) -> TestRunResponse:
        """Start a bounded TEMP rehearsal asynchronously. Reuse identical request_id/inputs after lost response.

        Omit scenarios for every existing adapter of selected actors. For a focused retry,
        pass exact scenario_id values from a prior report. No live token, command, SQL,
        custom URL, database path or rule approval is accepted. Poll companion_test_status.
        ui=true adds built desktop/mobile checks. Inspect certification_ready and
        report.certification.gaps; scenario PASS alone is not full sheet certification.
        ui_suite=combat explicitly selects sheet readiness and extended action UI,
        leaving map/shop suites out of this batch; default full preserves all checks.
        ui_suite=lightning runs readiness and the approved native multi-target pilot.
        ui_suite=hemomancy runs only the approved five-weapon UI flow, with all four actors required.
        ui_suite=vampiric runs Regeneration, Bite, Coffin and Night Form in two fixed halves; all four actors required.
        ui_suite=necromancy runs Morthak's touch/fear, controlled summons and high spells in three fixed scripts; all four actors required.
        ui_suite=rest runs map controls and four-sheet full-rest cleanup/counter checks in two fixed scripts; all four actors required.
        ui_suite=passives runs the five approved hemomancy passive triggers; all four actors required.
        ui_suite=summon_turns runs controlled summon attacks and turn lifecycle; all four actors required.
        ui_suite=inventory_summons runs HP purchase/use and hidden old-map skeleton replacement; all four actors required.
        ui_suite=friday runs private preparations, real copied Thoradin purchase, combat, passives, summons and rest sequentially; all four actors required.
        Inspect progress while running. ERROR may retain partial_report, never certification.
        """
        return TestRunResponse(**jobs().start(request_id=request_id,actors=actors,scenarios=scenarios,ui=ui,ui_suite=ui_suite))

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True,destructiveHint=False,openWorldHint=False))
    def companion_test_status(run_id: Annotated[str,Field(pattern=r'^test-[a-f0-9]{32}$')]) -> TestRunResponse:
        """Read RUNNING or terminal state and structured sheet coverage/results. Private local-agent access only.

        COMPLETED + FAIL is a test failure, not a transport failure. ERROR + INCONCLUSIVE
        means no trustworthy result. PENDING/ASSISTED/RULE_BLOCKED must never be called automated.
        """
        return TestRunResponse(**jobs().status(run_id))

    return server


if __name__=='__main__':
    create_server().run(transport='stdio')
