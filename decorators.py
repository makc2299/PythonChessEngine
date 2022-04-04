import sqlite3

def get_from_db(func):
	def wrapper(*args):
		conn = sqlite3.connect('game_results.db')
		with conn:
			c = conn.cursor()
			c.execute("""
				SELECT * FROM results 
				""")
			data = c.fetchall()
			conn.commit()
		return func(*args,data)
	return wrapper
