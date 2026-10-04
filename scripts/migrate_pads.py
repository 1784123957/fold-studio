"""Add pad storage without changing existing designs or application privileges."""
import json
from pathlib import Path
import pymysql

root = Path(__file__).resolve().parents[1]
credentials = json.loads((root / '.runtime/mysql-credentials.json').read_text(encoding='utf-8'))
with pymysql.connect(host='127.0.0.1', port=3307, user='root', password=credentials['root_password'], database='fold_studio') as connection:
    with connection.cursor() as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS design_pads (
            design_id INTEGER NOT NULL PRIMARY KEY,
            items JSON NOT NULL,
            FOREIGN KEY (design_id) REFERENCES designs(id)
        )''')
print('Pad storage ready; existing designs unchanged.')
