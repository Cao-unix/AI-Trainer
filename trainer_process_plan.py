from frame_instance import FrameInstance
from state_tracker import StateTracker
import numpy as np
import simpleaudio as sa
import threading
import sqlite3
import time
from time import strftime, gmtime
from datetime import date
import cv2
# 完成一个动作的状态序列
COMPLETE_STATE_SEQUENCE = ['s1', 's2', 's3', 's4']
# 倒计时启动训练，做够10次停止训练，并记录训练内容到数据表。
FONT: int = cv2.FONT_HERSHEY_SIMPLEX
data = {
    'plan': None,
    'loaded': False,
    'current_set': 1, # 当前训练组号
    'rest_start': 0, # 休息的开始时间
    'started': False,
    'screen_shot': False
}
start_time = None
end_time = None
start_pos = None
end_pos = None
speed = None
average_speed = None
max_speed = None
Speed = []
is_playing = False
is_playing_bgm = False
# 未活动监测的时长阈值，单位秒
INACTIVE_THRESH = 60.0
show = False
train_time = 0
def play_bgm(sound_file):
    global is_playing_bgm
    wave_obj = sa.WaveObject.from_wave_file(f"{sound_file}.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()
    is_playing_bgm = False  # 音频播放完成，更新状态


def play_sound(sound_file):
    global is_playing
    wave_obj = sa.WaveObject.from_wave_file(f"{sound_file}.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()
    is_playing = False  # 音频播放完成，更新状态


def trainer_process(frame_instance: FrameInstance, state_tracker: StateTracker, frame_width, frame_height, thresholds):
    # # 加载运动计划
    if not data['loaded'] and data['plan'] is None:
        data['loaded'] = True
        # 连接数据库
        conn = sqlite3.connect('data/train.db')
        # 创建游标
        cursor = conn.cursor()
        # 读取数据
        cursor.execute(
            "SELECT plandate,sets,reps,rest,state FROM train_plan WHERE state<>'done' and plandate=?",
            (date.today().isoformat(),)
        )
        for row in cursor:
            data['plan'] = {
                'plandate': row[0],
                'sets': row[1],
                'reps': row[2],
                'rest': row[3],
                'state': row[4] if row[4] is not None else ''
            }
            frame_instance.show_feedback(
                text=" {0}, sets: {1}, reps: {2}".format(row[0], row[1], row[2]),
                y=215, text_color='green',
                bg_color=(255, 153, 0),
                hide_delay=3)
            break
        # 关闭游标
        cursor.close()
        # 关闭数据库
        conn.close()

    # 加载不到计划，直接返回
    if data['plan'] is None:
        frame_instance.draw_text(
            text='NO PLAN',
            pos=(int(frame_instance.frame_width / 2) - 100, int(frame_instance.frame_height / 2) - 30),
            text_color='green',
            font_scale=2,
            bg_color=(255, 153, 0),
        )
        return
    global is_playing, is_playing_bgm
    angle_shldr_nose = frame_instance.get_angle('left_shldr', 'nose', 'right_shldr')
    if not is_playing_bgm:
        is_playing_bgm = True  # 标记音频播放
        sound_thread = threading.Thread(target=play_sound, args=("all falls down",))  # args中参数为播放音乐名，音乐为wav格式
        sound_thread.start()

    if angle_shldr_nose > 35:
        # 朝向正面，重置状态
        # 当前没有音频正在播放
        if not is_playing:
            is_playing = True  # 标记音频播放
            sound_thread = threading.Thread(target=play_sound, args=("reset_counters",))  # args中参数为播放音乐名，音乐为wav格式
            sound_thread.start()
        state_tracker.reset_state()

        # 画点
        frame_instance.circle('left_shldr', 'nose', 'right_shldr', radius=7, color='yellow')
        # ####################################### 如果朝向正面，提示角度错误 ####################################
        frame_instance.draw_text(
            text='CAMERA NOT ALIGNED PROPERLY!!!',
            pos=(30, frame_height - 60),
            text_color=(255, 255, 230),
            font_scale=0.65,
            bg_color=(255, 153, 0),
        )

        frame_instance.draw_text(
            text='OFFSET ANGLE: ' + str(angle_shldr_nose),
            pos=(30, frame_height - 30),
            text_color=(255, 255, 230),
            font_scale=0.65,
            bg_color=(255, 153, 0),
        )
    else:
        global train_time
        global game_start_time
        global speed, Speed, average_speed, max_speed
        global show
        if show == True:
            # 读取运动结果图
            image_result = cv2.imread('result.jpg')
            image_height, image_width, _ = image_result.shape
            # 将运动结果图放置在图像中央
            x = int((frame_width - image_width) / 2)
            y = int((frame_height - image_height) / 2)
            frame = frame_instance.get_frame()
            frame[y:(y + image_height), x:(x + image_width)] = image_result
            # 填写运动分析结果
            # 日期
            cv2.putText(frame, text=date.today().isoformat(), org=(x + 130, y + 25), fontFace=FONT, fontScale=0.5,
                        color=(195, 195, 195), thickness=2)
            # 总次数
            cv2.putText(frame, text=f"Total:{state_tracker.get_finished_count()}", org=(x + 130, y + 70), fontFace=FONT,
                        fontScale=0.8,
                        color=(0, 0, 0), thickness=2)
            # 运动时长
            cv2.putText(frame, text=train_time, org=(x + 50, y + 140),
                        fontFace=FONT, fontScale=0.4,
                        color=(0, 0, 0), thickness=1)
            # 热量
            cv2.putText(frame,
                        text=f"{5 * 0.5 * state_tracker.get_finished_count() * 2}J",
                        org=(x + 50, y + 205), fontFace=FONT, fontScale=0.4,
                        color=(0, 0, 0), thickness=1)
            # 成功次数
            cv2.putText(frame, text=f"{state_tracker.get_correct_count()}", org=(x + 225, y + 140), fontFace=FONT,
                        fontScale=0.4,
                        color=(76, 142, 44), thickness=1)
            # 失败次数
            cv2.putText(frame, text=f"{state_tracker.get_incorrect_count()}", org=(x + 225, y + 205), fontFace=FONT,
                        fontScale=0.4,
                        color=(250, 51, 29), thickness=1)
            frame_instance.show_feedback(
                text="finish",
                y=215, text_color='green',
                bg_color=(255, 153, 0),
                hide_delay=3)

            return
        # 朝向侧面。可以进行动作监测
        if not state_tracker.is_tracking():
            return

        # 判断是否训练结束
        if data['current_set'] > data['plan']['sets']:
            state_tracker.stop()
            # 记录本次训练
            # 连接数据库
            conn = sqlite3.connect('data/train.db')
            # 创建游标
            cursor = conn.cursor()
            # 更新计划状态
            cursor.execute("update train_plan set state='done' where plandate=?", (data['plan']['plandate'],))
            # 向数据库中插入数据
            cursor.execute(
                "insert into train_record (train_time,correct_count,incorrect_count,train_long) VALUES (?,?,?,?)",
                (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(state_tracker.start_time)),
                 state_tracker.get_correct_count(), state_tracker.get_incorrect_count(),
                 int(state_tracker.end_time - state_tracker.start_time))
            )
            # 提交数据
            conn.commit()
            # 关闭游标
            cursor.close()
            # 关闭数据库
            conn.close()
            train_time = strftime("%H:%M:%S", gmtime(state_tracker.end_time - state_tracker.start_time))
            show = True



        # 判断当前训练组是否完成
        if data['rest_start'] <= 0 and state_tracker.get_stage_finished_count() >= data['plan']['reps']:
            data['current_set'] += 1
            data['rest_start'] = time.perf_counter()
            state_tracker.pause()
            return

        # 判断休息时间
        if data['rest_start'] > 0:
            if time.perf_counter() - data['rest_start'] < data['plan']['rest']:
                # 休息5秒
                state_tracker.pause()
                sec = int(time.perf_counter() - data['rest_start'])
                frame_instance.draw_text(
                    text=str(data['plan']['rest'] - sec),
                    pos=(int(frame_instance.frame_width / 2) - 30, int(frame_instance.frame_height / 2) - 30),
                    text_color='green',
                    font_scale=2,
                    bg_color=(255, 153, 0),
                )
                return
            else:
                state_tracker.resume()
                data['rest_start'] = 0

        # region 判断状态
        # 获取需要监测的角度
        # draw_and_get_angle_vertical(): 计算并画出两点与垂线的夹角
        body_vertical_angle = frame_instance.get_angle_and_draw('right_shldr', 'hip', 'vertical')
        body_angle = int(body_vertical_angle)
        right_shldr_x = frame_instance.get_coord('right_shldr')[0]
        right_shldr_y = frame_instance.get_coord('right_shldr')[1]
        hip_x = frame_instance.get_coord('hip')[0]
        hip_y = frame_instance.get_coord('hip')[1]
        # 判断当前状态
        if body_angle >= 45 and right_shldr_x > hip_x:
            # 臀肩角度<-45° s1状态
            state_tracker.set_state('s1')
        elif body_angle >= 20 and right_shldr_x < hip_x and state_tracker.get_state() == 's1':
            # 臀膝角度>20°  s2状态
            state_tracker.set_state('s2')

        elif body_angle <= 10 and state_tracker.get_state() == 's2':
            # 臀膝角度<10°  s3状态
            global start_time
            start_time = time.perf_counter()
            global start_pos
            start_pos = right_shldr_x
            state_tracker.set_state('s3')
        elif 10 <= body_angle <= 30 and right_shldr_x > hip_x and state_tracker.get_state() == 's3':

            if state_tracker.get_finished_count() == 1 and not data['screen_shot']:
                # 用一个标记，标识已经执行了截图操作。避免重复截图。
                data['screen_shot'] = True
                # 转换图片的格式
                img = cv2.cvtColor(frame_instance.get_frame(), cv2.COLOR_BGR2RGB)
                # 可以对转换后的图片进行处理
                cv2.putText(img, 'GOOD JOB!', (40, 120), cv2.FONT_HERSHEY_SIMPLEX,
                            1.0, (0, 255, 0), 6)
                # 保存截图
                cv2.imwrite('screen_shot.jpg', img)

            # 臀膝角度 10到30° s4状态
            global end_time
            end_time = time.perf_counter()
            global end_pos
            end_pos = right_shldr_x
            state_tracker.set_state('s4')
            # endregion

        now_state = state_tracker.get_state()
        if now_state != None:
            frame_instance.draw_text(
                text=f'State: {now_state}',
                pos=(30, 40),
                text_color=(255, 255, 230),
                font_scale=1,
                bg_color=(255, 153, 0),
            )
        if state_tracker.get_state() == 's4':
            speed = round((end_pos - start_pos) * 0.0139 / (end_time - start_time), 1)
            Speed.append(speed)
            average_speed = round(np.mean(Speed),1)
            max_speed = np.max(Speed)
        if speed != None:
            frame_instance.draw_text(
                text=f"Now Speed: {speed} m/s",
                pos=(int(frame_instance.get_frame_width() * 0.68), 150),
                text_color=(255, 255, 230),
                font_scale=1,
                bg_color=(0, 0, 0)
            )
            frame_instance.draw_text(
                text=f"Average Speed: {average_speed} m/s",
                pos=(int(frame_instance.get_frame_width() * 0.68), 200),
                text_color=(255, 255, 230),
                font_scale=1,
                bg_color=(0, 0, 0)
            )
            frame_instance.draw_text(
                text=f"Max Speed: {max_speed} m/s",
                pos=(int(frame_instance.get_frame_width() * 0.68), 250),
                text_color=(255, 255, 230),
                font_scale=1,
                bg_color=(0, 0, 0)
            )

        # region 画点画线
        # line(): 画出两点之间的连线
        frame_instance.line('shldr', 'elbow', 'light_blue', 4)
        frame_instance.line('wrist', 'elbow', 'light_blue', 4)
        frame_instance.line('hip', 'shldr', 'light_blue', 4)
        frame_instance.line('hip', 'knee', 'light_blue', 4)
        frame_instance.line('ankle', 'knee', 'light_blue', 4)

        # point()：画点
        frame_instance.circle('elbow', 'wrist', 'shldr', 'hip', 'knee', 'ankle', radius=7, color='yellow')

        # 姿态矫正
        arm_shldr_angle = frame_instance.get_angle_and_draw('elbow', 'shldr', 'hip')
        arm_body_angle = int(arm_shldr_angle)
        arm_vertical_angle = frame_instance.get_angle_and_draw('shldr', 'elbow', 'vertical')
        arm_angle = int(arm_vertical_angle)
        if state_tracker.get_state() == 's1':
            if body_angle > 70:
                # 提示背太弯
                frame_instance.show_feedback(text='Your back is too bent.', y=hip_y, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
                if not is_playing:
                    is_playing = True  # 标记音频播放
                    sound_thread = threading.Thread(target=play_sound,
                                                    args=("incorrect",))  # args中参数为播放音乐名，音乐为wav格式
                    sound_thread.start()
            # if arm_angle > 10:
            #     # 提示手不垂直
            #     frame_instance.show_feedback(text='Your arms are not vertical.', y=right_shldr_y, text_color='black',
            #                                  bg_color='yellow')
            #     state_tracker.set_incorrect_posture()

        if state_tracker.get_state() == 's2':
            if arm_body_angle < thresholds['ARM_BODY_ANGLE']:
                # 提示胳膊不平行
                frame_instance.show_feedback(text='Your arms are not parallel to your body.', y=right_shldr_y,
                                             text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
                if not is_playing:
                    is_playing = True  # 标记音频播放
                    sound_thread = threading.Thread(target=play_sound,
                                                    args=("incorrect",))  # args中参数为播放音乐名，音乐为wav格式
                    sound_thread.start()
        if state_tracker.get_state() == 's3':
            if arm_body_angle < thresholds['ARM_BODY_ANGLE']:
                # 提示胳膊不平行
                frame_instance.show_feedback(text='Your arms are not parallel to your body.', y=right_shldr_y,
                                             text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
                if not is_playing:
                    is_playing = True  # 标记音频播放
                    sound_thread = threading.Thread(target=play_sound,
                                                    args=("incorrect",))  # args中参数为播放音乐名，音乐为wav格式
                    sound_thread.start()

        # if state_tracker.get_state() == 's4':
        #     if 80 < arm_angle < 100:
        #         # 提示胳膊不水平
        #         frame_instance.show_feedback(text='Your arms are not parallel.', y=right_shldr_y, text_color='black',
        #                                      bg_color='yellow')
        #         state_tracker.set_incorrect_posture()

        # knee_vertical_angle = frame_instance.get_angle_and_draw('hip', 'knee', 'vertical')
        # hip_vertical_angle = frame_instance.get_angle_and_draw('shldr', 'hip', 'vertical')
        # ankle_vertical_angle = frame_instance.get_angle_and_draw('knee', 'ankle', 'vertical')
        #
        # # ####################################### 判断前倾或后仰，并提示 #######################################
        # if hip_vertical_angle > 50:
        #     frame_instance.show_feedback(text='BEND BACKWARDS', y=215, text_color='light_yellow', bg_color='blue')
        # elif hip_vertical_angle < 10 and state_tracker.get_state_count('s2') == 1:
        #     frame_instance.show_feedback(text='BEND FORWARD', y=215, text_color='light_yellow', bg_color='blue')
        #
        # # ####################################### 下蹲深度提示 ###############################################
        # if 50 < knee_vertical_angle < 70 and state_tracker.get_state_count('s2') == 1:
        #     # 提示蹲的深度不够
        #     frame_instance.show_feedback(text='LOWER YOUR HIPS', y=80, text_color='black', bg_color='yellow')
        # elif knee_vertical_angle > 95:
        #     # 提示蹲的过深
        #     frame_instance.show_feedback(text='SQUAT TOO DEEP', y=125, text_color='light_yellow', bg_color='red')
        #     # 标记“不正确的姿势”
        #     state_tracker.set_incorrect_posture()
        #
        # # ####################################### 膝盖位置提示 #################################################
        # if ankle_vertical_angle > 45:
        #     # 提示膝盖过脚尖
        #     frame_instance.show_feedback(text='KNEE FALLING OVER TOE', y=170, text_color='light_yellow', bg_color='yellow')
        #     # 标记“不正确的姿势”
        #     state_tracker.set_incorrect_posture()

        # endregion
