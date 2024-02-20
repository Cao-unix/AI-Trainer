import os
import sqlite3
import sys

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid

BASE_DIR = os.path.abspath(os.path.join(__file__, '../../'))
sys.path.append(BASE_DIR)

st.title('训练数据')

train_record = []
# 读取训练计划
# 连接数据库
conn = sqlite3.connect('data/train.db')
# 创建游标
cursor = conn.cursor()
# 读取数据
cursor.execute("SELECT id,train_time,correct_count,incorrect_count,train_long,calorie FROM train_record")
for row in cursor:
    train_record.append({
            'id': row[0],
            'train_time': row[1],
            'correct_count': row[2],
            'incorrect_count': row[3],
            'train_long': row[4],
            'calorie':row[5]
        })
# 关闭游标
cursor.close()
# 关闭数据库
conn.close()

df = pd.DataFrame(data=train_record)
gridOptions = {
    'columnDefs': [
        {'field': 'train_time', 'headerName': '训练时间', 'width': '100'},
        {'field': 'correct_count', 'headerName': '正确次数', 'width': '100'},
        {'field': 'incorrect_count', 'headerName': '错误次数', 'width': '100'},
        {'field': 'train_long', 'headerName': '训练时长', 'width': '100'},
        {'field': 'calorie', 'headerName': '消耗热量', 'width': '100'},
       ]
}

AgGrid(
    df,
    gridOptions=gridOptions
)

st.empty()
st.line_chart(df, x='train_time', y=['correct_count', 'incorrect_count', 'calorie'])