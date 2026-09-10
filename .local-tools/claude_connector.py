"""Claude-only HTTPS/OAuth deployment of the existing MCP registry."""
import json
import os
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from uuid import uuid4

from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.routing import Route
from mcp.server.auth.routes import build_metadata, cors_middleware
from mcp.server.auth.handlers.metadata import MetadataHandler
from claude_oauth import ClaudeOAuth
from omnisvera_mcp.bridge import register_remote_bridge_tools, remote_bridge_context
from omnisvera_mcp.core.context import CallContext
from omnisvera_mcp.core.registry import IDENTITY_ARGUMENTS


def claude_context():
    token=get_access_token()
    if not token or token.subject != "sage" or "omnisvera.read" not in token.scopes:
        raise PermissionError("Claude OAuth authorization required")
    crypto=token.claims.get("profile")=="crypto" if token.claims else False
    scopes={s for s in remote_bridge_context().scopes if s.endswith(".read")}
    if crypto:
        scopes.add("claude.crypto.commit")
    return CallContext(actor="crypto.btc.direction" if crypto else "claude.observer",client="claude",transport="streamable-http",
        scopes=frozenset(scopes),
        request_id=uuid4().hex,project_id="omnisvera")


class ClaudeRegistry:
    """Transport-only grant; never expose the Core's broad write scope globally."""
    def __init__(self,registry): self.registry=registry
    def __getattr__(self,name): return getattr(self.registry,name)
    def invoke(self,name,context,arguments=None):
        arguments = arguments or {}
        if (name=="epistemic.snapshot_from_model" and context.actor=="crypto.btc.direction"
                and "claude.crypto.commit" in context.scopes):
            model = arguments.get("model") if isinstance(arguments, dict) else None
            if isinstance(model, dict) and model.get("world_id") == "crypto":
                context=replace(context,scopes=context.scopes | {"epistemic.write"})
        if (name=="epistemic.commit_candidate" and context.actor=="crypto.btc.direction"
                and "claude.crypto.commit" in context.scopes):
            context=replace(context,scopes=context.scopes | {"epistemic.write"})
        return self.registry.invoke(name,context,arguments)


class ClaudeAudit:
    def __init__(self,sink): self.sink=sink
    def record(self,event):
        if event.get("client")=="claude":
            event={**event,"metadata":{**event.get("metadata",{}),"caller_class":"external-ai"}}
        self.sink.record(event)


class RequestBoundary:
    def __init__(self,app,resource): self.app,self.resource=app,resource
    async def __call__(self,scope,receive,send):
        if scope.get("type")!="http" or scope.get("method")!="POST":
            return await self.app(scope,receive,send)
        chunks=[]; size=0
        while True:
            message=await receive()
            if message["type"]!="http.request": return
            chunk=message.get("body",b""); size+=len(chunk)
            if size>262144:
                return await JSONResponse({"error":"request_too_large"},status_code=413)(scope,receive,send)
            chunks.append(chunk)
            if not message.get("more_body"): break
        body=b"".join(chunks)
        if scope.get("path")=="/token":
            try:
                resources=parse_qs(body.decode('utf-8')).get('resource',[])
            except UnicodeDecodeError:
                resources=['invalid']
            if resources and resources != [self.resource]:
                return await JSONResponse({"error":"invalid_target"},status_code=400)(scope,receive,send)
        if scope.get("path")=="/mcp":
            try:
                data=json.loads(body)
                args=data.get("params",{}).get("arguments",{}) if isinstance(data,dict) else {}
                if isinstance(args,dict) and IDENTITY_ARGUMENTS.intersection(args):
                    return await JSONResponse({"error":"Identity fields are transport-controlled"},status_code=400)(scope,receive,send)
            except (ValueError,AttributeError): pass
        consumed=False
        async def replay():
            nonlocal consumed
            if not consumed:
                consumed=True
                return {"type":"http.request","body":body,"more_body":False}
            return await receive()
        await self.app(scope,replay,send)


def build_connector(registry,issuer,db,password,port=8767):
    if urlparse(issuer).scheme!="https" or urlparse(issuer).path not in ("", "/"):
        raise ValueError("Public HTTPS origin required")
    issuer=issuer.rstrip("/")
    provider=ClaudeOAuth(db,issuer,password)
    mcp=FastMCP("OMNISVERA",host="127.0.0.1",port=port,streamable_http_path="/mcp",
        stateless_http=True,json_response=True,auth_server_provider=provider,
        auth=AuthSettings(issuer_url=issuer,resource_server_url=issuer+"/mcp",
            required_scopes=["omnisvera.read"],client_registration_options=ClientRegistrationOptions(
                enabled=True,valid_scopes=["omnisvera.read","offline_access"],default_scopes=["omnisvera.read"])),
        transport_security=TransportSecuritySettings(allowed_hosts=[urlparse(issuer).netloc,"127.0.0.1:*"],
            allowed_origins=[issuer,"https://claude.ai"]))
    registry._audit=ClaudeAudit(registry._audit)
    register_remote_bridge_tools(mcp,ClaudeRegistry(registry),context_factory=claude_context)
    mcp.custom_route("/login",methods=["GET","POST"])(provider.login)
    app=mcp.streamable_http_app()
    # SDK defaults advertise confidential clients although this provider only
    # accepts public DCR clients. Publish the actual supported token auth method.
    metadata=build_metadata(mcp.settings.auth.issuer_url, None,
                            mcp.settings.auth.client_registration_options, RevocationOptions())
    metadata.token_endpoint_auth_methods_supported=["none"]
    for index, route in enumerate(app.router.routes):
        if getattr(route,"path",None)=="/.well-known/oauth-authorization-server":
            app.router.routes[index]=Route(route.path,
                endpoint=cors_middleware(MetadataHandler(metadata).handle,["GET","OPTIONS"]),
                methods=["GET","OPTIONS"])
            break
    return RequestBoundary(app,issuer+"/mcp"),app,provider,mcp


if __name__=="__main__":
    import uvicorn
    import mcp_server
    root=Path(__file__).resolve().parents[1]/".assistant-runtime"/"claude-connector"
    config=json.loads((root/"config.json").read_text())
    password=(root/"login-password.txt").read_text().strip()
    app,_,_,_=build_connector(mcp_server.CORE_REGISTRY,config["issuer"],root/"oauth.db",password)
    # OAuth query strings and authorization codes must not enter access logs.
    uvicorn.run(app,host="127.0.0.1",port=8767,access_log=False,log_level="warning")
