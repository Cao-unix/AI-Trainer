from frame_instance import FrameInstance
from state_tracker import StateTracker
import time
import numpy as np
import simpleaudio as sa
import threading
# 完成一个动作的状态序列
COMPLETE_STATE_SEQUENCE = ['s1', 's2', 's3', 's4']
start_time =None
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
set_goal = 20
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

    global is_playing,is_playing_bgm
    angle_shldr_nose = frame_instance.get_angle('left_shldr', 'nose', 'right_shldr')
    if not is_playing_bgm:
        is_playing_bgm = True  # 标记音频播放
        sound_thread = threading.Thread(target=play_sound, args=("reset_counters",))  # args中参数为播放音乐名，音乐为wav格式
        sound_thread.start()


    if angle_shldr_nose > 35:
        # 朝向正面，重置状态

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
        if not is_playing_bgm:
            is_playing_bgm = True  # 标记音频播放
            sound_thread = threading.Thread(target=play_sound, args=("reset_counters",))  # args中参数为播放音乐名，音乐为wav格式
            sound_thread.start()
        # 朝向侧面。可以进行深蹲监测
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
            start_pos= right_shldr_x
            state_tracker.set_state('s3')
        elif 10 <= body_angle <= 30 and right_shldr_x > hip_x and state_tracker.get_state() == 's3':
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
        global speed,Speed,average_speed,max_speed
        if state_tracker.get_state() == 's4':
            speed = round((end_pos - start_pos)*0.0139 / (end_time - start_time),1)
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
                frame_instance.show_feedback(text='Your arms are not parallel to your body.', y=right_shldr_y, text_color='black',
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
                frame_instance.show_feedback(text='Your arms are not parallel to your body.', y=right_shldr_y, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
                if not is_playing:
                    is_playing = True  # 标记音频播放
                    sound_thread = threading.Thread(target=play_sound,
                                                    args=("incorrect",))  # args中参数为播放音乐名，音乐为wav格式
                    sound_thread.start()

