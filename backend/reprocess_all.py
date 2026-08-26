import sqlite3
from app.main import init_database, process_upload

con = sqlite3.connect('data/fls_demo.db')
con.row_factory = sqlite3.Row
drawings = [dict(r) for r in con.execute('SELECT id, file_url, file_type, floor_name, page_index FROM drawings').fetchall()]
print(f'Total drawings in DB: {len(drawings)}')

for d in drawings:
    d_id = d['id']
    p_idx = d.get('page_index', 0)
    name = d.get('floor_name')
    print(f'Reprocessing {d_id} ({name}, page={p_idx})...')
    try:
        process_upload(d_id, page_index=p_idx)
    except Exception as e:
        print(f'  Failed: {e}')

print('Reprocessing complete!')
