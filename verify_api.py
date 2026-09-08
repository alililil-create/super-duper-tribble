"""启动真实 Uvicorn 服务并发送 HTTP 请求，输出可复查的证据。"""
from pathlib import Path
import json
import subprocess
import sys
import time
import httpx

root = Path(__file__).parent
evidence = root/'evidence'
evidence.mkdir(exist_ok=True)
rows = []
with (evidence/'server.log').open('w', encoding='utf-8') as log:
    server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8765'], cwd=root, stdout=log, stderr=log)
    try:
        with httpx.Client(base_url='http://127.0.0.1:8765', trust_env=False) as client:
            for _ in range(60):
                if server.poll() is not None:
                    raise RuntimeError('Uvicorn failed to start; see evidence/server.log')
                try:
                    client.get('/openapi.json').raise_for_status()
                    break
                except httpx.ConnectError:
                    time.sleep(0.2)
            else:
                raise RuntimeError('Server startup timed out')

            def check(method, url, status, expected=None, body=None):
                response = client.request(method, url, **({'json': body} if body is not None else {}))
                data = response.json()
                passed = response.status_code == status and (expected is None or data == expected)
                rows.append({'method': method, 'url': url, 'request': body, 'status': response.status_code, 'response': data, 'passed': passed})
                assert passed, rows[-1]

            check('GET', '/', 200, {'Hello':'World'})
            check('GET', '/item?item_id=2', 200, {'item_id':2})
            check('GET', '/item2/2', 200, {'item_id':2})
            check('GET', '/item', 422)
            check('GET', '/item2/abc', 422)
            check('POST', '/item3', 200, {'name':'书本','price':1012.5,'is_offer':False}, {'name':'书本','price':12.5})
            check('POST', '/item3', 422, body={'name':'书本','price':'bad'})
            check('POST', '/items', 422, body={'name':'缺少价格'})
            item = {'id':3,'name':'书本','price':12.5,'is_offer':False}
            check('POST', '/items', 200, {'message':'新增成功','item':item}, {'name':'书本','price':12.5})
            check('GET', '/items/3', 200, item)
            item = {'id':3,'name':'课本','price':20.0,'is_offer':True}
            check('PUT', '/items/3', 200, {'message':'修改成功','item':item}, {'name':'课本','price':20,'is_offer':True})
            check('GET', '/items/3', 200, item)
            check('GET', '/items/999', 404, {'detail':'商品不存在'})
            check('PUT', '/items/999', 404, {'detail':'商品不存在'}, {'name':'课本','price':20})
            schema = client.get('/openapi.json').json()
            assert {'name','price'} == set(schema['components']['schemas']['Item']['required'])
            assert client.get('/docs').status_code == 200
            (evidence/'openapi.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        server.terminate()
        server.wait(timeout=10)
        (evidence/'api-results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(rows)}/{len(rows)} HTTP checks passed; OpenAPI and /docs also verified.')
