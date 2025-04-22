import sqlite3

global status_db_name
status_db_name = ''


def init_db(workshop_db):
    global status_db_name 
    status_db_name = workshop_db
    conn = sqlite3.connect(status_db_name)

    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS order_status
                 (unique_id TEXT PRIMARY KEY, status TEXT, reason TEXT)''')
    conn.commit()
    conn.close()

def insert_order_status(unique_id,status,reason):
    #print('insert_order_status start')
    #print(status_db_name)
    conn = sqlite3.connect(status_db_name)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO order_status (unique_id,status, reason) VALUES (?,?,?)''', (unique_id,status,reason))
    conn.commit()
    conn.close()

def update_order_recieved(unique_id):
    conn = sqlite3.connect(status_db_name)
    c = conn.cursor()
    c.execute('''update order_status set status = ? where unique_id = ?''', ('received',unique_id))
    conn.commit()
    conn.close()

def update_order_bad_request(unique_id,data):
    conn = sqlite3.connect(status_db_name)
    c = conn.cursor()
    c.execute('''update order_status set status = ?, reason = ? where unique_id = ?''', ('bad request',data,unique_id))
    conn.commit()
    conn.close()

# The order_status_db parameter is nesesary to be able to call the function from a seperate thread
def update_order_processing(unique_id,order_status_db):
    conn = sqlite3.connect(order_status_db)
    c = conn.cursor()
    c.execute('''update order_status set status = ? where unique_id = ?''', ('processing',unique_id))
    #print('update_order_processing')
    #print(unique_id)    
    #print(order_status_db)
    conn.commit()
    conn.close()

# The order_status_db parameter is nesesary to be able to call the function from a seperate thread
def update_order_failed(unique_id,reason,order_status_db):
    conn = sqlite3.connect(order_status_db)
    c = conn.cursor()
    c.execute('''update order_status set status = ?,reason = ? where unique_id = ?''', ('failed',reason,unique_id))
    conn.commit()
    conn.close()

def update_order_completed(unique_id,order_status_db):
    #print('update_order_compleated')
    #print(unique_id)    
    #print(order_status_db)
    conn = sqlite3.connect(order_status_db)
    c = conn.cursor()
    c.execute('''update order_status set status = ? where unique_id = ?''', ('completed',unique_id))
    conn.commit()
    conn.close()

def get_order_status(unique_id):
    conn = sqlite3.connect(status_db_name)
    c = conn.cursor()
    c.execute('''SELECT unique_id,status,reason FROM order_status WHERE unique_id = ?''', (unique_id,))
    status_line = c.fetchone()
    conn.close()
    return status_line if status_line else None