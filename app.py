"""Public static connectivity probe. No database, identity, storage or patient imports."""
import asyncio

from fastapi import FastAPI
from starlette.responses import Response

HEALTH_BODY=b'{"status":"ok","service":"connectivity-pilot"}'
HEADERS={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}
api=FastAPI(openapi_url=None,docs_url=None,redoc_url=None,redirect_slashes=False)


@api.get('/health')
async def health():
    return Response(HEALTH_BODY,media_type='application/json',headers=HEADERS)


class HealthOnly:
    def __init__(self,inner,timeout=2):self.inner=inner;self.timeout=timeout

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.inner(scope,receive,send)
        async def reject(status):
            await Response(b'{"status":"unavailable"}',status_code=status,
                           media_type='application/json',headers=HEADERS)(scope,receive,send)
        if scope['path']!='/health' or scope.get('raw_path',b'/health')!=b'/health':return await reject(404)
        if scope['method']!='GET':return await reject(405)
        if scope.get('query_string'):return await reject(400)
        for key,value in scope.get('headers',[]):
            if key.lower()==b'transfer-encoding':return await reject(413)
            if key.lower()==b'content-length' and value!=b'0':return await reject(413)
        # Buffer this tiny static response so timeout/error cannot expose a partial
        # response or framework exception. No request body is consumed or stored.
        messages=[];size=0
        async def collect(message):
            nonlocal size
            size+=len(message.get('body',b''))
            if size>4096 or len(messages)>=4:raise ValueError('Response bound')
            messages.append(message)
        try:await asyncio.wait_for(self.inner(scope,receive,collect),timeout=self.timeout)
        except asyncio.TimeoutError:return await reject(503)
        except Exception:return await reject(500)
        for message in messages:await send(message)


app=HealthOnly(api)
