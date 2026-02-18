import sqlite3
import os
DB='unitool_data.db'
if not os.path.exists(DB):
    print('DB file not found:', DB)
    raise SystemExit
conn=sqlite3.connect(DB)
c=conn.cursor()
print('PRAGMA table_info(targets):')
for row in c.execute("PRAGMA table_info(targets)"):
    print(row)

pseudo='jaron'
print('\nSELECT * for', pseudo)
for row in c.execute('SELECT * FROM targets WHERE pseudo=?',(pseudo,)):
    print(row)

print('\nSELECT explicit columns for', pseudo)
sql = ("SELECT pseudo, org, ship, threat, notes, date, wins, losses, alignment, "
       "pvp_lvl, activity, sid, org_rank, enlisted_date, language FROM targets WHERE pseudo=?")
for row in c.execute(sql,(pseudo,)):
    print(row)

conn.close()