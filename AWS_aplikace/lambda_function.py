from flask import Flask, jsonify, request,render_template
import psycopg2
import os
import awsgi

app = Flask(__name__)


db = "body"
db_host = os.environ.get("DB_HOST", "bp-postgres.czu0u4q4suc8.eu-central-1.rds.amazonaws.com")
db_name = os.environ.get("DB_NAME", "postgres")
db_user = os.environ.get("DB_USER", "postgres")
db_password = os.environ.get("DB_PASSWORD", "12345678")

def get_db_connection():
    return psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port="5432"
    )

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/body', methods=['GET'])
def vypis_body():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {db} LIMIT 100")
    body = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(body)

"""@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response"""

@app.route('/body/<string:name>', methods=['GET'])
def ziskej_bod(name):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {db} WHERE nazevbodu = %s", (name,))
        bod = cur.fetchone()
        cur.close()
        conn.close()
        if bod:
            return jsonify({'nazevbodu': bod[0], 'x': bod[1], 'y': bod[2], 'z': bod[3]})
        else:
            return jsonify({'error': f'Bod {name} nenalezen'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/body', methods=['POST'])
def vytvor_bod():
    data = request.get_json()
    if not all(k in data for k in ('name', 'x', 'y', 'z')):
        return jsonify({'error': 'Neplatný vstup'}), 400
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT 1 FROM {db} WHERE nazevbodu = %s", (data['name'],))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'Bod s tímto názvem již existuje'}), 400
    cur.execute(f"INSERT INTO {db} (nazevbodu, x, y, z) VALUES (%s, %s, %s, %s)", (data['name'], data['x'], data['y'], data['z']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(data), 201

@app.route('/body/<string:name>', methods=['DELETE'])
def smaz_bod(name):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {db} WHERE nazevbodu = %s", (name,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'zprava': f'Bod {name} byl smazán'}), 200


def lambda_handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png"})