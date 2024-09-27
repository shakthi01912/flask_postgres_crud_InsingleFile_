from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# creating logging
logging.basicConfig(level=logging.INFO)
# Creating web server instance
app = Flask(__name__)
CORS(app)

# Database details
DB_HOST = os.getenv('DB_HOST')
DB_DATABASE = os.getenv('DB_DATABASE')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Creating connection with database
def db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_DATABASE,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None

# Create table 
def create_table():
    dbConn = db_connection()
    if dbConn is None:
        return  # Exit if connection failed
    dbCursor = dbConn.cursor()
    
    try:
        dbCursor.execute(
            '''CREATE TABLE IF NOT EXISTS notewithenv (
                id SERIAL PRIMARY KEY,
                note_name VARCHAR(255) NOT NULL,
                note_description VARCHAR(255)
            );
            ''')
        dbConn.commit()
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        dbCursor.close()
        dbConn.close()

@app.route('/insert2', methods=['POST'])
def insert_note():
    # Requested data
    userInputArray = request.json
    
    # Check if required fields are present
    if 'note_name' not in userInputArray or 'note_description' not in userInputArray:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Extracted data from request
    name_input = userInputArray['note_name']
    description_input = userInputArray['note_description']
    
    # DB connection
    dbConn = db_connection()
    
    if dbConn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = dbConn.cursor()
    
    try:
        logging.info(f"Inserting note: name={name_input}, description={description_input}")
        # Print for debugging before the insertion
        print(f"Inserting note: name={name_input}, description={description_input}")
        
        # Execute the insert SQL query within cursor
        cur.execute('INSERT INTO notewithenv (note_name, note_description) VALUES (%s, %s) RETURNING id;', (name_input, description_input))
        note_id = cur.fetchone()[0] 
        
        # Commit the transaction explicitly
        dbConn.commit()
        
        logging.info(f"Inserted note ID: {note_id}")
        
        # Return the message
        return jsonify({'id': note_id}), 201
    except Exception as e:
        print(f"Error inserting note: {e}") 
        dbConn.rollback() 
        return jsonify({'error': 'Failed to insert note'}), 500
    finally:
        # Clean up
        cur.close()
        dbConn.close()

@app.route('/update2/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    # Collecting the array from request
    userInputArray = request.json
    
    # Requested ID and data from request
    name_input = userInputArray.get('note_name')  # Use .get() to avoid KeyError
    description_input = userInputArray.get('note_description') 

    # DB connection
    dbConn = db_connection()
    if dbConn is None:
        return jsonify({'error': "Database connection unsuccessful"}), 500
    
    cur = dbConn.cursor()
    
    try: 
        # Execute the ID checking query within cursor
        cur.execute('SELECT * FROM notewithenv WHERE id = %s;', (note_id,))
        existing_note_id = cur.fetchone()
       
        if existing_note_id:
            # ID is available; execute the update query
            cur.execute('UPDATE notewithenv SET note_name = %s, note_description = %s WHERE id = %s;', (name_input, description_input, note_id))
            dbConn.commit()
            return jsonify({'message': 'Note updated successfully'}), 200
        else:
            return jsonify({'message': 'ID not found'}), 404
            
    except Exception as e:
        print("Error in updating:", e)
        return jsonify({'error': 'Failed to update'}), 500
    
    finally:
        cur.close()
        dbConn.close()
        
@app.route('/viewAll2/', methods=['GET'])  # Ensure it's a GET request
def viewall():
    # DB connection
    dbConn = db_connection()
    if dbConn is None:
        return jsonify({'error': 'Database connection unsuccessful'}), 500
    
    cur = dbConn.cursor()
    
    try:
        # Execute the select query within cursor
        cur.execute('SELECT * FROM notewithenv;')
        
        # Fetch all records
        all_records = cur.fetchall()  # Call the method with parentheses
        
        # Prepare the records for JSON response
        result = [{'id': record[0], 'note_name': record[1], 'note_description': record[2]} for record in all_records]
        
        # Return jsonify
        return jsonify(result), 200  # Return with a 200 OK status
        
    except Exception as e:
        print("Error in retrieving records:", e)
        return jsonify({'error': 'Failed to retrieve records'}), 500
    
    finally:
        cur.close()
        dbConn.close()
        
@app.route('/delete2/<int:note_id>', methods=['DELETE']) 
def delete(note_id):
    # db connection
    dbConn = db_connection()
    
    # intializing cursor
    cur = dbConn.cursor()
    print("cursor is done" , note_id)
    # cursor checking
    if cur is None:
        return jsonify({'error':'error in databse connection'}),500
        # if cur is true
    try:
        cur.execute('delete from notewithenv where id = %s;', (note_id,) )
        dbConn.commit()
        
        if cur.rowcount == 0:
            return jsonify({'message': 'ID not found'}), 400
            
        return jsonify({'message':'deleted successfully'}), 200
        
    except Exception as e:
        print("error in dleteing : " , e)
        return jsonify({'error':' error in deleting'}),400
        
        
    finally:
        cur.close()
        dbConn.close()
        
    


if __name__ == '__main__':
    create_table()  
    app.run(debug=True)