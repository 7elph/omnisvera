"""Real SDK client -> stdio MCP -> disposable native HTTP rehearsal.

Only test credentials are used. The repaired daily ring lifecycle must pass.
Run this with observer dependencies; no OpenCode/LLM account is needed.
"""
import asyncio
import argparse
from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import time
import uuid
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(full=False, ui=False):
    output=Path(tempfile.mkdtemp(prefix='omnisvera-mcp-test-smoke-'))
    script=Path(__file__).with_name('companion_test_mcp.py')
    server=StdioServerParameters(command=sys.executable,args=[str(script)],cwd=str(script.parents[2]))
    request_id='mcp-smoke-'+uuid.uuid4().hex
    with (output/'mcp.private.log').open('w',encoding='utf-8') as errors:
        async with stdio_client(server,errlog=errors) as (reader,writer):
            async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                tools=await session.list_tools()
                assert {t.name for t in tools.tools}=={'companion_test_capabilities','companion_test_start','companion_test_status'}
                assert all(t.outputSchema for t in tools.tools)
                capabilities=await session.call_tool('companion_test_capabilities',{})
                assert not capabilities.isError and capabilities.structuredContent['isolation']
                args={'request_id':request_id,'actors':['vezemir','raziel'],
                    'scenarios':['vezemir:Poção de HP + ataque no mesmo turno','raziel:Anel Rúnico']}
                if full:args={'request_id':request_id,'actors':['vezemir','morthak','raziel','dorn7']}
                if ui:args['ui']=True
                started=await session.call_tool('companion_test_start',args)
                assert not started.isError,started.content
                run=started.structuredContent
                retry=await session.call_tool('companion_test_start',args)
                assert not retry.isError and retry.structuredContent['run_id']==run['run_id']
                deadline=time.monotonic()+(1150 if ui else 600)
                while True:
                    status=await session.call_tool('companion_test_status',{'run_id':run['run_id']})
                    assert not status.isError,status.content
                    data=status.structuredContent
                    if data['state']!='RUNNING':break
                    if time.monotonic()>=deadline:raise TimeoutError('MCP rehearsal did not complete')
                    await asyncio.sleep(1)
                assert data['state']=='COMPLETED' and data['verdict']=='PASS',data
                expected={'PASS':64,'EXPECTED_BLOCK':1} if full else {'PASS':2}
                assert data['report']['scenario_counts']==expected,data['report']
                assert data['production_modified'] is False
                if ui:assert data['ui'] and data['report']['ui_smoke']['status']=='PASS',data['report'].get('ui_smoke')
                assert not data['report']['all_actions_certified']
                (output/'mcp-evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        # Reconnect a NEW stdio server/client: the durable receipt must recover
        # the completed job, not create a second fixture or replay combat.
        async with stdio_client(server,errlog=errors) as (reader,writer):
            async with ClientSession(reader,writer,read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                recovered=await session.call_tool('companion_test_start',args)
                assert not recovered.isError,recovered.content
                receipt=recovered.structuredContent
                assert receipt['run_id']==data['run_id'] and receipt['created_at']==data['created_at']
                assert receipt['state']=='COMPLETED' and receipt['report']==data['report']
    print(json.dumps({'status':'PASS','transport':'real MCP stdio + native HTTP',
        'request_retry':'same run_id, including a new stdio server/client','rehearsal_verdict':'PASS (repaired daily ring lifecycle)',
        'evidence':str(output/'mcp-evidence.json')},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--full',action='store_true');parser.add_argument('--ui',action='store_true')
    args=parser.parse_args();asyncio.run(main(args.full,args.ui))
