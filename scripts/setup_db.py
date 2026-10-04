"""Initialize credentials for a freshly initialized, loopback-only MySQL instance."""
import json
import secrets
from pathlib import Path
import pymysql

root = Path(__file__).resolve().parents[1]
credential_file = root / '.runtime' / 'mysql-credentials.json'
if credential_file.exists():
    raise SystemExit('Credentials already exist. Refusing to overwrite an existing database setup.')
admin_password = secrets.token_hex(24)
app_password = secrets.token_hex(24)
conn = pymysql.connect(host='127.0.0.1', port=3307, user='root', password='')
with conn.cursor() as c:
    c.execute('CREATE DATABASE IF NOT EXISTS fold_studio CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    c.execute("CREATE USER 'fold_app'@'127.0.0.1' IDENTIFIED BY %s", (app_password,))
    c.execute("GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, REFERENCES ON fold_studio.* TO 'fold_app'@'127.0.0.1'")
    c.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (admin_password,))
conn.close()
credential_file.write_text(json.dumps({'root_password':admin_password,'app_password':app_password}), encoding='utf-8')
(root / 'backend' / '.env').write_text(f'DATABASE_URL=mysql+pymysql://fold_app:{app_password}@127.0.0.1:3307/fold_studio?charset=utf8mb4\nCORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173\n',encoding='utf-8')
print('MySQL database and dedicated application account created. Credentials saved locally (gitignored).')
