import sqlite3, os, re
DB='unitool_data.db'
if not os.path.exists(DB):
    print('DB not found')
    raise SystemExit
conn=sqlite3.connect(DB)
c=conn.cursor()
rows = c.execute("SELECT pseudo, pvp_lvl, date FROM targets").fetchall()
pattern = re.compile(r"^\d{2}/\d{2}/\d{4}$")
bad=[]
for r in rows:
    if r[1] and pattern.match(r[1]):
        bad.append(r)
print('rows with pvp_lvl looking like a date:', len(bad))
for r in bad[:20]:
    print(r)
conn.close()