"""OAuth boundary for the Claude connector; no Omnisvera domain logic."""
import hashlib
import hmac
import json
import secrets
import sqlite3
import time
from contextlib import closing
from urllib.parse import urlencode

from mcp.server.auth.provider import (
    AccessToken, AuthorizationCode, AuthorizationParams, RefreshToken,
    AuthorizeError, RegistrationError, TokenError, construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from starlette.responses import HTMLResponse, RedirectResponse, JSONResponse

CALLBACK = "https://claude.ai/api/mcp/auth_callback"


class ClaudeOAuth:
    def __init__(self, path, issuer, password):
        self.path, self.issuer = str(path), issuer.rstrip("/")
        self.resource = self.issuer + "/mcp"
        self.password_hash = hashlib.sha256(password.encode()).digest()
        self.failures = []
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS credentials(kind TEXT, id TEXT, payload TEXT, expires REAL, PRIMARY KEY(kind,id))")

    def put(self, kind, key, payload, expires):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM credentials WHERE expires < ?", (time.time(),))
            db.execute("INSERT OR REPLACE INTO credentials VALUES(?,?,?,?)",
                       (kind, hashlib.sha256(key.encode()).hexdigest(), json.dumps(payload), expires))

    def get(self, kind, key, consume=False):
        digest = hashlib.sha256(key.encode()).hexdigest()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload,expires FROM credentials WHERE kind=? AND id=?", (kind,digest)).fetchone()
            if consume:
                db.execute("DELETE FROM credentials WHERE kind=? AND id=?", (kind,digest))
            return json.loads(row[0]) if row and row[1] > time.time() else None

    async def get_client(self, client_id):
        raw = self.get("client",client_id)
        return OAuthClientInformationFull.model_validate(raw) if raw else None

    async def register_client(self, client_info):
        if [str(x) for x in client_info.redirect_uris] != [CALLBACK]:
            raise RegistrationError("invalid_redirect_uri","Only Claude web callback is allowed")
        if client_info.token_endpoint_auth_method != "none":
            raise RegistrationError("invalid_client_metadata","Use public client with PKCE")
        with closing(sqlite3.connect(self.path)) as db:
            count = db.execute("SELECT count(*) FROM credentials WHERE kind='client'").fetchone()[0]
        if count >= 100:
            raise RegistrationError("invalid_client_metadata","Client registration limit reached")
        self.put("client",client_info.client_id,client_info.model_dump(mode="json"),time.time()+365*86400)

    async def authorize(self, client, params):
        if str(params.redirect_uri) != CALLBACK or params.resource not in (None,self.resource):
            raise AuthorizeError("invalid_request","Invalid redirect or resource")
        if not set(params.scopes or ["omnisvera.read"]) <= {"omnisvera.read","offline_access"}:
            raise AuthorizeError("invalid_scope","Read-only connector")
        nonce = secrets.token_urlsafe(32)
        self.put("pending",nonce,dict(client_id=client.client_id,params=params.model_dump(mode="json")),time.time()+300)
        return self.issuer + "/login?" + urlencode({"request":nonce})

    async def login(self, request):
        # no-referrer makes Chromium send Origin: null for native form POSTs.
        # same-origin preserves CSRF origin checks and leaks nothing to Claude.
        headers={"Cache-Control":"no-store", "Referrer-Policy":"same-origin",
                 "Content-Security-Policy":f"default-src 'none'; form-action 'self' {CALLBACK}; frame-ancestors 'none'"}
        if request.method == "GET":
            nonce=request.query_params.get("request","")
            if not self.get("pending",nonce):
                return JSONResponse({"error":"expired_login"},status_code=400,headers=headers)
            # Nonce is server-generated URL-safe data; no client text rendered.
            html='<!doctype html><meta charset="utf-8"><title>OMNISVERA</title><h1>Conectar OMNISVERA ao Claude</h1><p>Permitir leitura de Worlds, Experience e Predictions. Escrita não autorizada.</p><p>Destino: claude.ai</p><form method="post" action="/login"><input type="hidden" name="request" value="'+nonce+'"><label>Senha local do conector <input type="password" name="password" required autocomplete="current-password"></label><button type="submit">Autorizar leitura</button></form>'
            html=html.replace('Escrita não autorizada.','Por padrão, somente leitura; a opção abaixo autoriza um commit restrito.')
            html=html.replace('<button type="submit">Autorizar leitura</button>',
                '<p><label><input type="checkbox" name="crypto_consent" value="yes"> '
                'Autorizar também commit de Predictions somente como crypto.btc.direction. '
                'Football, resolução e outras escritas continuam bloqueados.</label></p>'
                '<button type="submit">Autorizar sessão</button>')
            response=HTMLResponse(html,headers=headers)
            response.set_cookie("claude_consent",nonce,secure=True,httponly=True,samesite="lax",max_age=300,path="/login")
            return response
        allowed_origins = {self.issuer, "https://claude.ai"}
        if request.headers.get("origin") not in allowed_origins:
            return JSONResponse({"error":"invalid_origin"},status_code=403,headers=headers)
        body=await request.body()
        if len(body)>4096:
            return JSONResponse({"error":"request_too_large"},status_code=413,headers=headers)
        from urllib.parse import parse_qs
        fields=parse_qs(body.decode("utf-8"))
        nonce=fields.get("request",[""])[0]
        if not nonce or not hmac.compare_digest(nonce,request.cookies.get("claude_consent","")):
            return JSONResponse({"error":"invalid_consent"},status_code=403,headers=headers)
        now=time.time()
        self.failures=[t for t in self.failures if now-t<60]
        if len(self.failures)>=5:
            return JSONResponse({"error":"try_later"},status_code=429,headers=headers)
        password=fields.get("password",[""])[0]
        if not hmac.compare_digest(hashlib.sha256(password.encode()).digest(),self.password_hash):
            self.failures.append(now)
            return JSONResponse({"error":"invalid_login"},status_code=403,headers=headers)
        pending=self.get("pending",nonce,consume=True)
        if not pending:
            return JSONResponse({"error":"expired_login"},status_code=400,headers=headers)
        params=AuthorizationParams.model_validate(pending["params"])
        code=secrets.token_urlsafe(32)
        ac=AuthorizationCode(code=code,client_id=pending["client_id"],expires_at=now+120,
            scopes=params.scopes or ["omnisvera.read"],code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            resource=self.resource,subject="sage")
        code_data=ac.model_dump(mode="json",exclude={"code"})
        code_data["profile"]="crypto" if fields.get("crypto_consent")==["yes"] else "observer"
        self.put("code",code,code_data,now+120)
        response=RedirectResponse(construct_redirect_uri(str(params.redirect_uri),code=code,state=params.state),status_code=303,headers=headers)
        response.delete_cookie("claude_consent",path="/login")
        return response

    async def load_authorization_code(self,client,authorization_code):
        data=self.get("code",authorization_code)
        if data: data.pop("profile",None)
        return AuthorizationCode(code=authorization_code,**data) if data and data["client_id"]==client.client_id else None

    def issue(self,client_id,scopes,profile="observer"):
        if profile not in ("observer","crypto"):
            raise TokenError("invalid_grant","Unknown consent profile")
        now=int(time.time()); access=secrets.token_urlsafe(32); refresh=secrets.token_urlsafe(32)
        self.put("access",access,dict(client_id=client_id,scopes=scopes,expires_at=now+1800,
            resource=self.resource,subject="sage",claims={"caller_class":"external-ai","profile":profile}),now+1800)
        self.put("refresh",refresh,dict(client_id=client_id,scopes=scopes,expires_at=now+30*86400,
            subject="sage",resource=self.resource,access_hash=access,profile=profile),now+30*86400)
        return OAuthToken(access_token=access,token_type="Bearer",expires_in=1800,
                          refresh_token=refresh,scope=" ".join(scopes))

    async def exchange_authorization_code(self,client,authorization_code):
        data=self.get("code",authorization_code.code,consume=True)
        if not data or data["client_id"]!=client.client_id:
            raise TokenError("invalid_grant","Code already used")
        return self.issue(client.client_id,data["scopes"],data.get("profile","observer"))

    async def load_refresh_token(self,client,refresh_token):
        data=self.get("refresh",refresh_token)
        if not data or data["client_id"]!=client.client_id or data.get("resource")!=self.resource: return None
        data.pop("resource",None)
        data.pop("access_hash",None)
        data.pop("profile",None)
        return RefreshToken(token=refresh_token,**data)

    async def exchange_refresh_token(self,client,refresh_token,scopes):
        data=self.get("refresh",refresh_token.token,consume=True)
        if not data or data["client_id"]!=client.client_id or data.get("resource")!=self.resource or not set(scopes)<=set(data["scopes"]):
            raise TokenError("invalid_grant","Refresh token invalid")
        self.get("access",data["access_hash"],consume=True)
        return self.issue(client.client_id,scopes,data.get("profile","observer"))

    async def load_access_token(self,token):
        data=self.get("access",token)
        return AccessToken(token=token,**data) if data and data["resource"]==self.resource else None

    async def revoke_token(self,token):
        if isinstance(token,RefreshToken):
            data=self.get("refresh",token.token,consume=True)
            if data: self.get("access",data["access_hash"],consume=True)
        else:
            self.get("access",token.token,consume=True)
