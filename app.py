from flask import Flask, jsonify, render_template, request
import pymysql
import yaml
import numpy as np

app = Flask(__name__)

# 从配置文件加载数据库配置
db_config = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)


def get_db_connection():
    return pymysql.connect(host=db_config['mysql_host'],
                           user=db_config['mysql_user'],
                           password=db_config['mysql_password'],
                           db=db_config['mysql_db'],
                           cursorclass=pymysql.cursors.DictCursor)


@app.route('/')
def index():
    return render_template('chart.html')


@app.route('/data')
def data():
    protein_id = request.args.get('proteinID')  # 从查询参数获取 proteinID
    conn = get_db_connection()
    cursor = conn.cursor()

    if protein_id:
        cursor.execute("SELECT proteinID, speciesName, value FROM MPlantTs WHERE proteinID = %s", (protein_id,))
    else:
        cursor.execute("SELECT proteinID, speciesName, value FROM MPlantTs")

    query_results = cursor.fetchall()
    cursor.close()
    conn.close()

    protein_data = {}
    for row in query_results:
        proteinID, speciesName = row['proteinID'], row['speciesName']
        try:
            value = float(row['value'])
        except ValueError:
            continue
        if proteinID not in protein_data:
            protein_data[proteinID] = {'values': [], 'speciesName': speciesName}
        protein_data[proteinID]['values'].append(value)

    processed_data = []
    for proteinID, data in protein_data.items():
        average = np.mean(data['values'])
        std_dev = np.std(data['values'])
        processed_data.append({
            'proteinID': proteinID,
            'average': average,
            'error': std_dev,
            'speciesName': data['speciesName']
        })

    return jsonify(processed_data)


if __name__ == '__main__':
    app.run(debug=True)