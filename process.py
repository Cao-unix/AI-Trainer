import time
import numpy as np
from trainer_process_goal import COMPLETE_STATE_SEQUENCE, INACTIVE_THRESH
from trainer_process_goal import trainer_process as trainer_goal_process
from trainer_process_free import trainer_process as trainer_free_process
from trainer_process_plan import trainer_process as trainer_plan_process
from trainer_process_match import trainer_process as trainer_match_process
from state_tracker import StateTracker

state_tracker = StateTracker(COMPLETE_STATE_SEQUENCE, INACTIVE_THRESH)
data = {
    'example': 'Normal',
    'nick_name':'nobody'
}
def process(frame_instance,thresholds):
    frame_width = frame_instance.get_frame_width()
    frame_height = frame_instance.get_frame_height()
    # if 'GOAL' in thresholds:
    #     trainer_goal_process(frame_instance, state_tracker, frame_width, frame_height, thresholds)
    if data['example'] == 'Free':
        trainer_process = trainer_free_process
    elif data['example'] == 'Plan':
        trainer_process = trainer_plan_process
    elif data['example'] == 'Free_Goal':
        trainer_process = trainer_goal_process
    elif data['example'] == 'Match':
        trainer_process = trainer_match_process
    # Process the image.
    state_tracker.before_process(frame_instance)
    if frame_instance.validate():
        trainer_process(frame_instance, state_tracker, frame_width, frame_height, thresholds)
        state_tracker.after_process(thresholds)

    else:
        state_tracker.after_process(thresholds)
        state_tracker.reset()

    return frame_instance.get_frame()
