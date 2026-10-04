"""Add board thickness, retaining existing designs as zero-thickness models."""
import json
from pathlib import Path
import pymysql
root=Path(__file__).resolve().parents[1]
credentials=json.loads((root/'.runtime/mysql-credentials.json').read_text(encoding='utf-8'))
with pymysql.connect(host='127.0.0.1',port=3307,user='root',password=credentials['root_password'],database='fold_studio') as conn:
    with conn.cursor() as c:
        c.execute("SHOW COLUMNS FROM designs LIKE 'thickness'")
        if not c.fetchone():
            c.execute('ALTER TABLE designs ADD COLUMN thickness DOUBLE NOT NULL DEFAULT 0')
print('Thickness storage ready.')
