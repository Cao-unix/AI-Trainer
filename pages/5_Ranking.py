import os
import sqlite3
import sys

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid

BASE_DIR = os.path.abspath(os.path.join(__file__, '../../'))
sys.path.append(BASE_DIR)

st.title('排行榜')

train_record = []
# 读取训练计划
# 连接数据库
conn = sqlite3.connect('data/train.db')
# 创建游标
cursor = conn.cursor()
# 读取数据
cursor.execute("SELECT nick_name,total_count,correct_count,incorrrect_count,score,max_speed FROM match_record ORDER BY score DESC")
place = 0
for row in cursor:
    place += 1
    icon = ''
    if place == 1:
        icon = '🥇'
    elif place == 2:
        icon = '🥈'
    elif place == 3:
        icon = '🥉'
    train_record.append({
            'place': '{}{}'.format(place, icon),
            'nick_name': row[0],
            'correct_count': row[2],
            'incorrect_count': row[3],
            'score': row[4],
            'max_speed':row[5]
        })
# 关闭游标
cursor.close()
# 关闭数据库
conn.close()

df = pd.DataFrame(data=train_record)
gridOptions = {
    'columnDefs': [
        {'field': 'place', 'headerName': '名次', 'width': '100'},
        {'field': 'nick_name', 'headerName': '选手', 'width': '100'},
        {'field': 'correct_count', 'headerName': '正确次数', 'width': '120'},
        {'field': 'incorrect_count', 'headerName': '错误次数', 'width': '120'},
        {'field': 'score', 'headerName': '分数', 'width': '120'},
        {'field': 'max_speed', 'headerName': '最快速度', 'width': '120'},
       ]
}

AgGrid(
    df,
    gridOptions=gridOptions,
    theme= 'material'
)
