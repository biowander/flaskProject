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
    return render_template('index.html')


@app.route('/protein')
def protein():
    return render_template('chart4.html')


# @app.route('/data')
# def data():
#     protein_id = request.args.get('proteinID')  # 从查询参数获取 proteinID
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     if protein_id:
#         cursor.execute("SELECT proteinID, speciesName, value FROM MPlantTs ORDER BY speciesName, proteinID")
#         all_proteins = cursor.fetchall()
#         # print(protein_id)
#         # print(all_proteins)
#         # 过滤出具有有效 value 的蛋白质
#         valid_proteins = [p for p in all_proteins if p['value'] != "NA"]
#         # print(type(valid_proteins))
#         # print(len(valid_proteins))
#
#         try:
#             index = next(i for i, p in enumerate(valid_proteins) if p['proteinID'] == protein_id)
#             # print(index)
#             # 计算起始和结束索引
#             start_index = max(0, index - 3*6)
#             # print(start_index)
#             end_index = min(len(valid_proteins), start_index + 3*13)  # 确保获取足够数量的蛋白质
#             # print(end_index)
#             # print(len(valid_proteins[start_index:end_index]))
#             protein_subset = [p['proteinID'] for p in valid_proteins[start_index:end_index]]
#             # print(protein_subset)
#             format_strings = ','.join(['%s'] * len(protein_subset))
#             # print(format_strings)
#             cursor.execute(f"SELECT proteinID, speciesName, value FROM MPlantTs WHERE proteinID IN ({format_strings}) ORDER BY speciesName, proteinID",
#                            tuple(protein_subset))
#         except StopIteration:
#             # 如果找不到指定的 proteinID，返回空结果
#             cursor.close()
#             conn.close()
#             return jsonify([])
#     else:
#         cursor.execute("SELECT proteinID, speciesName, value FROM MPlantTs ORDER BY speciesName, proteinID")
#
#     query_results = cursor.fetchall()
#     # print(query_results)
#     cursor.close()
#     conn.close()
#
#     protein_data = {}
#     for row in query_results:
#         proteinID, speciesName = row['proteinID'], row['speciesName']
#         try:
#             value = float(row['value'])
#         except ValueError:
#             continue
#         if proteinID not in protein_data:
#             protein_data[proteinID] = {'values': [], 'speciesName': speciesName}
#         protein_data[proteinID]['values'].append(value)
#
#     processed_data = []
#     for proteinID, data in protein_data.items():
#         average = np.mean(data['values'])
#         std_dev = np.std(data['values'])
#         processed_data.append({
#             'proteinID': proteinID,
#             'average': average,
#             'error': std_dev,
#             'speciesName': data['speciesName']
#         })
#
#     return jsonify(processed_data)

@app.route('/data')
def data():
    protein_id = request.args.get('proteinID')  # 从查询参数获取 proteinID
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if protein_id:
            # 首先，获取所有蛋白质的ID
            cursor.execute("SELECT proteinID FROM MPlantTs WHERE value != 'NA' ORDER BY speciesName, proteinID")
            all_protein_ids = [row['proteinID'] for row in cursor.fetchall()]

            # 然后，找到目标蛋白质的索引
            if protein_id in all_protein_ids:
                index = all_protein_ids.index(protein_id)
                # 计算前后各6个蛋白质的索引范围，确保不会超出列表边界
                start_index = max(0, index - 18)
                print(start_index)
                end_index = min(len(all_protein_ids), index + 21)
                print(end_index)
                # 获取这个范围内的蛋白质ID
                query_ids = all_protein_ids[start_index:end_index]
                print(query_ids)
            else:
                return jsonify([])  # 如果找不到指定的proteinID，直接返回空结果

            # 使用这些ID执行查询
            format_strings = ','.join(['%s'] * len(query_ids))
            query = f"SELECT proteinID, speciesName, value, HOG, Protein_names AS proteinNames FROM MPlantTs WHERE proteinID IN ({','.join(['%s'] * len(query_ids))}) ORDER BY FIELD(proteinID, {','.join(['%s'] * len(query_ids))})"
            cursor.execute(query, query_ids * 2)  # 参数需要重复两次，因为它们既用于IN又用于FIELD
        else:
            cursor.execute(
                "SELECT proteinID, speciesName, value, HOG, Protein_names AS proteinNames FROM MPlantTs WHERE value != 'NA' ORDER BY speciesName, proteinID")

        query_results = cursor.fetchall()

    finally:
        cursor.close()
        conn.close()

    return jsonify(process_query_results(query_results))


def process_query_results(query_results):
    protein_data = {}
    for row in query_results:
        proteinID, speciesName, HOG, proteinNames = row['proteinID'], row['speciesName'], row['HOG'], row['proteinNames']
        try:
            value = float(row['value'])
        except ValueError:
            continue

        if proteinID not in protein_data:
            protein_data[proteinID] = {'values': [], 'speciesName': speciesName, 'HOG': HOG, 'proteinNames': proteinNames}
        protein_data[proteinID]['values'].append(value)


    processed_data = []
    for proteinID, data in protein_data.items():
        average = np.mean(data['values'])
        std_dev = np.std(data['values'])

        processed_data.append({
            'proteinID': proteinID,
            'average': average,
            'error': std_dev,
            'speciesName': data['speciesName'],
            'HOG': data['HOG'],  # 添加HOG值
            'ProteinNames': data['proteinNames']
        })

    return processed_data

if __name__ == '__main__':
    app.run(debug=True)