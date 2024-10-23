import sqlite3, time

class database:

    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY, 
                            user_id INTEGER UNIQUE NOT NULL, 
                            username TEXT, 
                            user_group TEXT, 
                            join_date DATETIME NOT NULL DEFAULT ((DATETIME('now'))), 
                            last_schedule_request_time REAL, 
                            last_group_request_time REAL)
""")
    
    # Check if user exists
    def user_exists(self, user_id):
        result = self.cursor.execute('SELECT id FROM users WHERE user_id = ?', (user_id,))
        return bool(len(result.fetchall()))
    
    # Check if user has group
    def user_has_group(self, user_id):
        result = self.cursor.execute('SELECT user_group FROM users WHERE user_id = ?', (user_id,))
        return bool(len(result.fetchall()))

    # Getting database 'id' of user
    def get_db_id(self, user_id):
        result = self.cursor.execute('SELECT id FROM users WHERE user_id = ?', (user_id,))
        return result.fetchone()[0]
    
    def get_group(self, user_id):
        result = self.cursor.execute('SELECT user_group FROM users WHERE user_id = ?', (user_id,))
        return result.fetchone()[0]
    
    # Adding user to database
    def add_user(self, user_id, username):
        self.cursor.execute('INSERT INTO users (`user_id`, `username`, `last_schedule_request_time`, `last_group_request_time`) VALUES (?, ?, ?, ?)', (user_id, username, 0, 0))
        return self.connection.commit()
    
    # Set user group
    def set_group(self, user_id, group):
        #self.cursor.execute('UPDATE `users` SET `group` = ? WHERE `user_id` = ?', [group, user_id])
        self.cursor.execute('UPDATE users SET user_group = ? WHERE user_id = ?', (group, user_id))
        return self.connection.commit()
    
    def update_schedule_request_time(self, user_id):
        self.cursor.execute('UPDATE users SET last_schedule_request_time = ? WHERE user_id = ?', (time.time(), user_id))
        return self.connection.commit()
    
    def update_group_request_time(self, user_id):
        self.cursor.execute('UPDATE users SET last_group_request_time = ? WHERE user_id = ?', (time.time(), user_id))
        return self.connection.commit()
    
    def get_schedule_request_time(self, user_id):
        result = self.cursor.execute('SELECT last_schedule_request_time FROM users WHERE user_id = ?', (user_id,))
        return result.fetchone()[0]
    
    def get_group_request_time(self, user_id):
        result = self.cursor.execute('SELECT last_group_request_time FROM users WHERE user_id = ?', (user_id,))
        return result.fetchone()[0]

    # CLosing database connection
    def close(self):
        self.connection.close()