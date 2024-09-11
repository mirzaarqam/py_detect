from flask import Flask, render_template, request, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import datetime
from datetime import datetime

from pyparsing import empty

app = Flask(__name__)

# Database connection details
app.config['MYSQL_HOST'] = '192.168.1.100'
app.config['MYSQL_USER'] = 'ubuntu'
app.config['MYSQL_PASSWORD'] = '123456@a'
app.config['MYSQL_DB'] = 'trafficlogs'

# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'bilal1416179'
# app.config['MYSQL_DB'] = 'trafficlogs'


mysql = MySQL(app)

#
# def get_time_from_db():
#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     # SQL query to search for IPs that hit the provided IP within the time range
#     query = '''SELECT time
#                 FROM logs
#                 WHERE id = (SELECT MIN(id) FROM logs)
#                 OR id = (SELECT MAX(id) FROM logs)'''
#
#     cursor.execute(query)
#     results = cursor.fetchall()
#     print(results)
#
#     return results
#
#
# @app.route('/')
# def index():
#     time_db = get_time_from_db()
#     # Extract the first and last times
#     first_time = time_db[0]['time']
#     last_time = time_db[1]['time']
#
#     return render_template('search.html', first_time=first_time, last_time=last_time)
#
#
# @app.route('/search', methods=['POST'])
# def search():
#     # Retrieve the input data from the form
#     ip = request.form['ip']
#     port = request.form['port']
#     from_time = request.form['from_time']
#     from_time = from_time.replace('T', ' ')
#     to_time = request.form['to_time']
#     to_time = to_time.replace('T', ' ')
#
#     print(from_time)
#     print(to_time)
#
#     # Ensure the time range is valid (You can add more checks here if needed)
#     if not from_time or not to_time or not ip:
#         return "Please provide valid time range and IP."
#
#     # try:
#     #     # Convert the time range to datetime objects
#     #     from_time_dt = datetime.strptime(from_time, '%Y-%m-%d %H:%M:%S')
#     #     to_time_dt = datetime.strptime(to_time, '%Y-%m-%d %H:%M:%S')
#     # except ValueError:
#     #     return "Invalid time format. Please use 'YYYY-MM-DD HH:MM:SS'."
#
#     # Connect to the MySQL database and execute the query
#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#
#     # SQL query to search for IPs that hit the provided IP within the time range
#     if (port != empty):
#         query = '''
#                 SELECT  *
#                 FROM logs
#                 WHERE destination_ip = %s AND destination_port = %s AND time BETWEEN %s AND %s
#                 '''
#         cursor.execute(query, (ip, port, from_time, to_time))
#         results = cursor.fetchall()
#
#     else:
#         query = '''
#         SELECT  *
#         FROM logs
#         WHERE destination_ip = %s AND time BETWEEN %s AND %s
#         '''
#         cursor.execute(query, (ip, from_time, to_time))
#         results = cursor.fetchall()
#         port = 'All'
#
#     print(results)
#     if results:
#         return render_template('result.html', results=results, ip=ip, port=port)
#     else:
#         return "No records found for the specified IP and time range."
#


def get_time_from_db():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = '''SELECT time
                FROM logs
                WHERE id = (SELECT MIN(id) FROM logs)
                OR id = (SELECT MAX(id) FROM logs)'''
    cursor.execute(query)
    results = cursor.fetchall()
    return results


@app.route('/')
def index():
    time_db = get_time_from_db()
    first_time = time_db[0]['time']
    last_time = time_db[1]['time']
    return render_template('search.html', first_time=first_time, last_time=last_time)


@app.route('/search', methods=['POST'])
def search():
    ip = request.form['ip']
    port = request.form['port']
    from_time = request.form['from_time'].replace('T', ' ')
    to_time = request.form['to_time'].replace('T', ' ')

    if not from_time or not to_time or not ip:
        return jsonify({"error": "Please provide valid time range and IP."}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    query = '''
    SELECT *
    FROM logs
    WHERE destination_ip = %s AND time BETWEEN %s AND %s
    '''
    params = (ip, from_time, to_time)
    if port:
        query += ' AND destination_port = %s'
        params += (port,)

    cursor.execute(query, params)
    results = cursor.fetchall()

    if results:
        return jsonify(results)
    else:
        return jsonify([])


if __name__ == '__main__':
    app.run(host='192.168.1.105', port=5002, debug=True)
