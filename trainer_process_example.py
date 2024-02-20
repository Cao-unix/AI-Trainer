from frame_instance import FrameInstance
from state_tracker import StateTracker
import time
# 完成一个动作的状态序列
COMPLETE_STATE_SEQUENCE = ['s1', 's2', 's3', 's4']
global start_time,end_time,start_pos,end_pos
# 未活动监测的时长阈值，单位秒
INACTIVE_THRESH = 60.0


def trainer_process(frame_instance, state_tracker, frame_width, frame_height):
    angle_shldr_nose = frame_instance.get_angle('left_shldr', 'nose', 'right_shldr')

    if angle_shldr_nose > 35:
        # 朝向正面，重置状态
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
        # 朝向侧面。可以进行深蹲监测

        # region 判断状态
        # 获取需要监测的角度
        # draw_and_get_angle_vertical(): 计算并画出两点与垂线的夹角
        body_vertical_angle = frame_instance.get_angle_and_draw('right_shldr', 'hip', 'vertical')
        body_angle = int(body_vertical_angle)
        right_shldr_x = frame_instance.get_coord('right_shldr')[0]
        hip_x = frame_instance.get_coord('hip')[0]

        # 判断当前状态
        if body_angle >= 45 and right_shldr_x > hip_x:
            # 臀肩角度<-45° s1状态
            state_tracker.set_state('s1')
        elif body_angle >= 20 and right_shldr_x < hip_x and state_tracker.get_state() == 's1':
            # 臀膝角度在35~65之间是s2状态
            state_tracker.set_state('s2')

        elif body_angle <= 10 and state_tracker.get_state() == 's2':
            # 臀膝角度在70~95之间是s3状态
            state_tracker.set_state('s3')
            start_time = time.perf_counter()
            start_pos = right_shldr_x
        elif 10 <= body_angle <= 30 and right_shldr_x > hip_x and state_tracker.get_state() == 's3':
            # 臀膝角度在70~95之间是s3状态
            state_tracker.set_state('s4')
            end_time = time.perf_counter()
            end_pos = right_shldr_x
            # endregion

        now_state = state_tracker.get_state()
        if now_state != None:
            frame_instance.draw_text(
                text=f'State: {now_state}',
                pos=(30, 40),
                text_color=(255, 255, 230),
                font_scale=0.65,
                bg_color=(255, 153, 0),
            )
        if state_tracker.get_state() == 's4':
            frame_instance.draw_text(
                    text=f"Speed: {(end_pos-start_pos)/(end_time-start_time)}",
                    pos=(int(frame_instance.get_frame_width() * 0.68), 50),
                    text_color=(255, 255, 230),
                    font_scale=0.7,
                    bg_color=(18, 185, 0)
                )
        # frame_instance.show_feedback(text=now_state, y=40, text_color='black', bg_color='yellow')
        # region 画点画线
        # line(): 画出两点之间的连线
        frame_instance.line('shldr', 'elbow', 'light_blue', 4)
        frame_instance.line('wrist', 'elbow', 'light_blue', 4)
        frame_instance.line('hip', 'shldr', 'light_blue', 4)
        frame_instance.line('hip', 'knee', 'light_blue', 4)
        frame_instance.line('ankle', 'knee', 'light_blue', 4)

        # point()：画点
        frame_instance.circle('elbow', 'wrist', 'shldr', 'hip', 'knee', 'ankle', radius=7, color='yellow')

        arm_shldr_angle = frame_instance.get_angle_and_draw('elbow', 'shldr', 'hip')
        arm_body_angle = int(arm_shldr_angle)
        arm_vertical_angle = frame_instance.get_angle_and_draw('shldr', 'elbow', 'vertical')
        arm_angle = int(arm_vertical_angle)
        if state_tracker.get_state() == 's1':
            if body_angle > 70:
                # 提示背太弯
                frame_instance.show_feedback(text='Your back is too bent.', y=150, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
            # if arm_angle > 10:
            #     # 提示手不垂直
            #     frame_instance.show_feedback(text='Your arms are not vertical.', y=100, text_color='black',
            #                                  bg_color='yellow')
            #     state_tracker.set_incorrect_posture()
        if state_tracker.get_state() == 's2':
            if arm_body_angle < 170:
                # 提示胳膊不平行
                frame_instance.show_feedback(text='Your arms are not parallel to your body.', y=80, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
        if state_tracker.get_state() == 's3':
            if arm_body_angle < 170:
                # 提示胳膊不平行
                frame_instance.show_feedback(text='Your arms are not parallel to your body.', y=80, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
        if state_tracker.get_state() == 's4':
            if 80 < arm_angle < 100:
                # 提示胳膊不平行
                frame_instance.show_feedback(text='Your arms are not parallel.', y=80, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()

        if state_tracker.get_state() == 's3':
            if 80 < arm_angle < 100:
                # 提示胳膊不平行
                frame_instance.show_feedback(text='Your arms are not parallel.', y=80, text_color='black',
                                             bg_color='yellow')
                state_tracker.set_incorrect_posture()
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
