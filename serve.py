"""Independent Linux/Windows entrypoint; never imports the IBD backend or .env."""
import logging
import os
import sys

import uvicorn
from app import app


class SafeFormatter(logging.Formatter):
    def format(self,record):return record.levelname+' connectivity_pilot_event'


def options(env):
    mode=env.get('PILOT_ENV')
    if mode not in ('local','hosted-synthetic'):raise ValueError('Explicit pilot environment required')
    port=env.get('PORT','')
    if not port.isascii() or not port.isdecimal() or not 1<=int(port)<=65535:raise ValueError('Explicit port required')
    return dict(host='127.0.0.1' if mode=='local' else '0.0.0.0',port=int(port),
        workers=1,loop='asyncio',http='h11',ws='none',reload=False,
        proxy_headers=False,forwarded_allow_ips='',access_log=False,server_header=False,
        limit_concurrency=20,backlog=32,timeout_keep_alive=5,timeout_graceful_shutdown=5,
        h11_max_incomplete_event_size=8192,
        log_config={'version':1,'disable_existing_loggers':False,
            'formatters':{'safe':{'()':SafeFormatter}},
            'handlers':{'safe':{'class':'logging.StreamHandler','formatter':'safe','stream':'ext://sys.stderr'}},
            'root':{'handlers':['safe'],'level':'INFO'},
            'loggers':{'uvicorn':{'handlers':['safe'],'level':'INFO','propagate':False},
                'uvicorn.error':{'handlers':['safe'],'level':'INFO','propagate':False},
                'uvicorn.access':{'handlers':[],'propagate':False}}})


if __name__=='__main__':
    try:settings=options(os.environ)
    except ValueError:
        print('ERROR connectivity_pilot_config_invalid',file=sys.stderr);sys.exit(2)
    uvicorn.run(app,**settings)
