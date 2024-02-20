import os
import sqlite3
import sys
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid

BASE_DIR = os.path.abspath(os.path.join(__file__, '../../'))
sys.path.append(BASE_DIR)

st.title('训练计划')

begin_date = st.date_input("起始日期", date.today())
days = st.number_input('训练天数', min_value=1, max_value=100, value=30, format="%d")

if st.button('设置训练计划'):
    # 设置训练计划
    # 连接数据库
    conn = sqlite3.connect('data/train.db')
    # 创建游标
    cursor = conn.cursor()
    # 清空当前计划
    cursor.execute("DELETE FROM train_plan")
    # 写入新计划
    last_date = None
    reps = 2
    sets = 1
    rest = 10
    for data_inc in range(0, days, 3):
        # 写入数据
        plan_date = begin_date + timedelta(days=data_inc)
        if last_date is not None:
            if plan_date - last_date >= timedelta(days=7):
                last_date = plan_date
                reps += 2
        else:
            last_date = plan_date
        cursor.execute(
            "INSERT INTO train_plan (plandate,sets,reps,rest,state) VALUES (?,?,?,?,'')",
            (plan_date.isoformat(),sets,reps,rest,)
        )
    # 提交数据
    conn.commit()
    # 关闭游标
    cursor.close()
    # 关闭数据库
    conn.close()

# 读取训练计划
plan_data = []
# 连接数据库
conn = sqlite3.connect('data/train.db')
# 创建游标
cursor = conn.cursor()
# 读取数据
cursor.execute("SELECT plandate,sets,reps,state FROM train_plan")
days = 0
for row in cursor:
    days += 1
    plan_data.append(
        {'plandate': row[0], 'routine': '{}组,每组{}个'.format(row[1],row[2]), 'state': '完成' if row[3] == 'done' else '未完成'})
# 关闭游标
cursor.close()
# 关闭数据库
conn.close()

# 显示训练计划
if len(plan_data) == 0:
    st.info('暂无训练计划')
else:
    df = pd.DataFrame(data=plan_data)
    AgGrid(
        df,
        gridOptions={'columnDefs': [
            {'field': 'plandate', 'headerName': '训练日期'},
            {'field': 'routine', 'headerName': '训练内容'},
            {'field': 'state', 'headerName': '完成情况'},
        ]},
    )

