import sqlite3, os, re
DB='unitool_data.db'
if not os.path.exists(DB):
    print('DB not found')
    raise SystemExit
conn=sqlite3.connect(DB)
c=conn.cursor()
pattern = "[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]"
# Count affected
res = c.execute(f"SELECT COUNT(*) FROM targets WHERE pvp_lvl GLOB '{pattern}'").fetchone()[0]
print('Matching rows before update:', res)
if res>0:
    c.execute(f"UPDATE targets SET pvp_lvl='Inconnu' WHERE pvp_lvl GLOB '{pattern}'")
    conn.commit()
    print('Updated rows to Inconnu')
# Show the row now
rows = c.execute("SELECT pseudo, pvp_lvl, date FROM targets WHERE pvp_lvl='Inconnu'").fetchall()
print('Rows with pvp_lvl Inconnu:', len(rows))
for r in rows[:20]:
    print(r)
conn.close()