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

    # 根据是否提供了 proteinID 修改 SQL 查询
    if protein_id:
        cursor.execute("SELECT proteinID, variable, value FROM MPlantTs WHERE proteinID = %s", (protein_id,))
    else:
        cursor.execute("SELECT proteinID, variable, value FROM MPlantTs")

    query_results = cursor.fetchall()
    cursor.close()
    conn.close()

    # 数据处理
    protein_data = {}
    for row in query_results:
        proteinID = row['proteinID']
        try:
            value = float(row['value'])
        except ValueError:
            continue
        protein_data.setdefault(proteinID, []).append(value)

    processed_data = []
    for proteinID, values in protein_data.items():
        average = np.mean(values)
        std_dev = np.std(values)
        processed_data.append({
            'proteinID': proteinID,
            'average': average,
            'error': std_dev
        })

    return jsonify(processed_data)


if __name__ == '__main__':
    app.run(debug=True)
