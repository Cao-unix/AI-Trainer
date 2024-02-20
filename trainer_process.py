from frame_instance import FrameInstance
from state_tracker import StateTracker
# 完成一个动作的状态序列
COMPLETE_STATE_SEQUENCE =['s1', 's2', 's3', 's2', 's1']

# 未活动监测的时长阈值，单位秒
INACTIVE_THRESH = 60.0

def trainer_process(frame_instance: FrameInstance, state_tracker: StateTracker, frame_width, frame_height):
    # region ###### 状态处理 ######

    # endregion

    # region ###### 错误姿势判断，显示提示信息 ######

    # endregion