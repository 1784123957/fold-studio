import json
from pathlib import Path
import pymysql
root=Path(__file__).resolve().parents[1]
credentials=json.loads((root/'.runtime/mysql-credentials.json').read_text())
try:
    conn=pymysql.connect(host='127.0.0.1',port=3307,user='root',password=credentials['root_password'])
except pymysql.err.OperationalError as e:
    if e.args[0] == 2003:
        print('MySQL is already stopped.')
    else: raise
else:
    with conn.cursor() as cursor: cursor.execute('SHUTDOWN')
    conn.close()
    print('MySQL shut down cleanly.')
