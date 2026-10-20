import asyncio
from sqlalchemy import text
from app.db import engine

async def main():
    async with engine.connect() as c:
        print('MySQL database:', await c.scalar(text('SELECT DATABASE()')))
        for sql in ['SHOW TABLES', 'DESCRIBE users']:
            print('\nSQL> '+sql+';')
            rows=await c.execute(text(sql))
            headers=list(rows.keys()); data=[[str(v) if v is not None else 'NULL' for v in r] for r in rows]
            widths=[max(len(headers[i]),*(len(r[i]) for r in data)) for i in range(len(headers))]
            line='+'+'+'.join('-'*(n+2) for n in widths)+'+'
            print(line)
            for row in [headers]+data: print('| '+' | '.join(v.ljust(n) for v,n in zip(row,widths))+' |')
            print(line)
        print('\nSQLAlchemy: async_sessionmaker / expire_on_commit=False')
        print('One AsyncSession per HTTP request; MySQL pool_size=10, max_overflow=20')
    await engine.dispose()
asyncio.run(main())
