import psycopg2

conn = psycopg2.connect(dbname='asdf', user='postgres', password='MyStrongPassword123!', host='localhost')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='floors' ORDER BY ordinal_position;")
rows = cur.fetchall()
print('columns in floors:')
for r in rows:
    print(r)
cur.close()
conn.close()