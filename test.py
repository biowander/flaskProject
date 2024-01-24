import pymysql
import numpy as np
import yaml

# 从配置文件加载数据库配置
db_config = yaml.load(open('db.yaml'), Loader=yaml.FullLoader)

def get_db_connection():
    return pymysql.connect(host=db_config['mysql_host'],
                           user=db_config['mysql_user'],
                           password=db_config['mysql_password'],
                           db=db_config['mysql_db'],
                           cursorclass=pymysql.cursors.DictCursor)

def data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT proteinID, variable, value FROM MPlantTs")
    query_results = cursor.fetchall()
    cursor.close()
    conn.close()

    # 数据处理
    protein_data = {}
    for row in query_results:
        proteinID = row['proteinID']
        try:
            # 确保 value 是数值类型
            value = float(row['value'])
        except ValueError:
            # 如果 value 无法转换为浮点数，跳过这个数据点
            continue
        protein_data.setdefault(proteinID, []).append(value)
    print(protein_data.get("A0A2K3DWI2"))

    # 计算每个 proteinID 的平均值和标准差
    processed_data = []
    for proteinID, values in protein_data.items():
        if (proteinID == "A0A2K3DWI2"):
            print(values)
            average = np.mean(values)
            std_dev = np.std(values)
            print(std_dev)
            processed_data.append({
                'proteinID': proteinID,
                'average': average,
                'error': std_dev
            })
            break
    print(processed_data)

if __name__ == '__main__':
    data()


