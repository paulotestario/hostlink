import sqlite3

conn = sqlite3.connect('hostlink.db')
cursor = conn.cursor()

cursor.execute('SELECT id, municipio_id, created_at FROM analyses ORDER BY id DESC LIMIT 3')
results = cursor.fetchall()

print('ID | municipio_id | created_at')
print('-' * 40)
for r in results:
    print(f'{r[0]} | {r[1]} | {r[2]}')

conn.close()