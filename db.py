import sqlite3

class database:

    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        # create a new database table if not exists
        self.cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY, 
                            user_id INTEGER UNIQUE NOT NULL, 
                            username TEXT, 
                            user_group TEXT, 
                            join_date DATETIME NOT NULL DEFAULT ((DATETIME('now'))), 
                            last_schedule_request_time REAL DEFAULT 0, 
                            last_group_request_time REAL DEFAULT 0,
                            last_ping_request_time REAL DEFAULT 0)
""")
        # here goes checks for all new columns that were added with updates
        self.add_column_if_not_exists('last_ping_request_time', 'REAL', 0)
    
    # guess what does this do
    def add_column_if_not_exists(self, c_name: str, c_type: str, c_default=None):
        # fetch all columns from database
        columns = [info[1] for info in self.cursor.execute('PRAGMA table_info(users)').fetchall()]
        # add new column if there is not
        if c_name not in columns:
            # DEFAULT is set
            if c_default is not None:
                self.cursor.execute(f'ALTER TABLE users ADD COLUMN {c_name} {c_type} DEFAULT {c_default}')
            # DEFAULT is not set
            else:
                self.cursor.execute(f'ALTER TABLE users ADD COLUMN {c_name} {c_type}')
        return self.connection.commit()

    # Check if user exists
    def user_exists(self, user_id):
        result = self.cursor.execute('SELECT id FROM users WHERE user_id = ?', (user_id,))
        return bool(len(result.fetchall()))
    
    # Check if user has group
    def user_has_group(self, user_id):
        result = self.cursor.execute('SELECT user_group FROM users WHERE user_id = ?', (user_id,))
        return bool(len(result.fetchall()))
    
    # Add user to database
    def add_user(self, user_id, username):
        self.cursor.execute('INSERT INTO users (`user_id`, `username`, `last_schedule_request_time`, `last_group_request_time`) VALUES (?, ?, ?, ?)', (user_id, username, 0, 0))
        return self.connection.commit()
    
    # set value in given column
    def set_value(self, user_id: int, column: str, value: None):
        self.cursor.execute(f'UPDATE users SET {column} = \'{value}\' WHERE user_id = {user_id}')
        return self.connection.commit()

    # get value from given column
    def get_value(self, user_id: int, column: str):
        result = self.cursor.execute(f'SELECT {column} FROM users WHERE user_id = {user_id}')
        return result.fetchone()[0]

    # get all values of given column
    def get_all_values(self, column: str):
        result = self.cursor.execute(f'SELECT {column} FROM users')
        return result.fetchall()

    # CLose database connection. Just for fun i guess
    def close(self):
        self.connection.close()