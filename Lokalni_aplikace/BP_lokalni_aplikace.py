from flask import Flask, jsonify, request, render_template
import psycopg2
import os
# kniha umožňující přístup k databázi na AWS
# from flask_cors import CORS

app = Flask(__name__, template_folder="templates")

# povolení CORS pro všechny domény (pro testování)	
# CORS(app)
# host pokud ma aplikace pristupovat k databazi na AWS
# db_host = os.environ.get("DB_HOST", "bp-postgres.czu0u4q4suc8.eu-central-1.rds.amazonaws.com")

# host pokud ma aplikace pristupovat k databazi na lokálním počítači
db_host = os.environ.get("DB_HOST", "localhost")

db_name = os.environ.get("DB_NAME", "postgres")
db_user = os.environ.get("DB_USER", "postgres")
db_password = os.environ.get("DB_PASSWORD", "12345678")

db="body"
# Připojení k databázi
try:
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port="5432"
    )
    print("Pripojeno k databazi")
except Exception as err:
    print(Exception,err)

cur=conn.cursor()


@app.route('/')
def index():
    return render_template("index.html")

# funkce pro získání všech bodů
@app.route('/body', methods=['GET'])
def vypis_body():
    cur.execute(f"SELECT * FROM {db} LIMIT 100")
    body=cur.fetchall()
    return jsonify(body)

# funkce pro získání bodu podle názvu
@app.route('/body/<string:name>', methods=['GET'])
def ziskej_bod(name):
    cur.execute(f"SELECT * FROM {db} WHERE nazevbodu = %s", (name,))
    bod = cur.fetchone()
    if bod:
        bod_dict = {
            'nazevbodu': bod[0],
            'x': bod[1],
            'y': bod[2],
            'z': bod[3]
        }
        return jsonify(bod_dict)
    else:
        return jsonify({'error': f'Bod {name} nenalezen'}), 404

# funkce pro vytvoření nového bodu
@app.route('/body', methods=['POST'])
def vytvor_bod():
    data = request.get_json()
    required_fields = ['name', 'x', 'y', 'z']
    if not data or not all(field in data and data[field] not in [None, ""] for field in required_fields):
        return jsonify({'error': 'Neplatný vstup, všechny hodnoty musí být zadány'}), 400
    # Zkontroluj, zda bod se stejným názvem již existuje
    cur.execute(f"SELECT 1 FROM {db} WHERE nazevbodu = %s", (data['name'],))
    if cur.fetchone():
        return jsonify({'error': 'Bod s tímto názvem již existuje'}), 400
    new_bod = {
        'name': data['name'],
        'x': data['x'],
        'y': data['y'],
        'z': data['z']
    }
    cur.execute(f"INSERT INTO {db} (nazevbodu, x, y, z) VALUES (%s, %s, %s, %s)", (new_bod['name'], new_bod['x'], new_bod['y'], new_bod['z']))
    conn.commit()
    return jsonify(new_bod), 201

# funkce pro smazání bodu podle názvu
@app.route('/body/<string:name>', methods=['DELETE'])
def smaz_bod(name):
    cur.execute(f"DELETE FROM {db} WHERE nazevbodu = %s", (name,))
    conn.commit()
    return jsonify({'zprava': f'Bod {name} byl smazán'}), 200


if __name__ == "__main__":
    app.run(debug=True)