import time
from frame_instance import FrameInstance
class StateTracker:
    def __init__(self, complete_state_sequence, inactive_thresh, auto_start: bool = True):
        self._frame_instance = None
        self.complete_state_sequence = complete_state_sequence
        self.begin_state = complete_state_sequence[0]
        self.end_state = complete_state_sequence[len(complete_state_sequence) - 1]
        self.end_state_thresh = complete_state_sequence.count(self.end_state)
        self.state_trans_pairs = []
        temp_pair = []
        for state in complete_state_sequence:
            temp_pair.append(state)
            if len(temp_pair) == 2:
                self.state_trans_pairs.append(temp_pair)
                temp_pair = [state]

        self.inactive_thresh = inactive_thresh

        self.state_seq = []
        self.temp_state = None
        self.state = None
        self.prev_state = None

        self.start_inactive_time = time.perf_counter()
        self.inactive_long = 0.0

        self.incorrect_posture = False

        self.squat_count = 0
        self.improper_squat = 0
        self._stage_correct_count = 0
        self._stage_incorrect_count = 0
        self._show_stage_count = False

        self._tracking = False
        self._pausing = False
        self.start_time = None
        self.end_time = None
        self.track_start_delay = 0
        self.track_count_down_start = None

        if auto_start:
            self.start(0)

    def start(self, delay):
        if self._tracking:
            return

        if self.track_count_down_start is None:
            self.track_count_down_start = time.perf_counter()
            self.track_start_delay = delay
            if delay <= 0:
                self.__start()
                return True

        track_count_down = self.track_start_delay - int(time.perf_counter() - self.track_count_down_start)
        if track_count_down <= 0:
            self.__start()
            return True
        else:
            if self._frame_instance is not None:
                self._frame_instance.draw_text(
                    text=str(track_count_down),
                    pos=(int(self._frame_instance.frame_width / 2) - 30, int(self._frame_instance.frame_height / 2) - 30),
                    text_color='green',
                    font_scale=2,
                    bg_color=(255, 153, 0),
                )
            return False

    def __start(self):
        self.reset()
        self._tracking = True
        self.start_time = time.time()

    def stop(self):
        self._tracking = False
        self.track_count_down_start = None
        self.end_time = time.time()

    def pause(self):
        if not self._tracking:
            return
        self._pausing = True
        self._stage_correct_count = 0
        self._stage_incorrect_count = 0

    def resume(self):
        self._pausing = False

    def is_tracking(self):
        return self._tracking

    def set_state(self, state):
        if not self._tracking:
            return

        self.temp_state = state
        if self.temp_state == self.state:
            return
        self.state = state

        idx = len(self.state_seq)
        if idx >= len(self.complete_state_sequence):
            return

        if idx == 0 and state != self.begin_state:
            return

        # for pair in self.state_trans_pairs:
        #     if pair[0] == self.state and pair[1] == self.temp_state:
        #         self.state_seq.append(state)
        #         break
        self.state_seq.append(state)
        self.__reset_inactive_tracker__()
        # print(">>state seq: ", self.state_seq)

    def get_state(self):
        return self.state

    def get_state_count(self, state):
        return self.state_seq.count(state)

    def get_finished_count(self):
        return self.squat_count + self.improper_squat

    def get_correct_count(self):
        return self.squat_count

    def get_incorrect_count(self):
        return self.improper_squat

    def get_stage_finished_count(self):
        return self._stage_correct_count + self._stage_incorrect_count

    def get__stage_correct_count(self):
        return self._stage_correct_count

    def get__stage_incorrect_count(self):
        return self._stage_incorrect_count

    def reset_state(self):
        self.state_seq = []
        self.temp_state = None
        self.state = None
        self.prev_state = None
        self.incorrect_posture = False

    def set_incorrect_posture(self):
        if not self._tracking:
            return

        self.incorrect_posture = True

    def before_process(self, frame_instance: FrameInstance):
        self._frame_instance = frame_instance

        if not self._tracking:
            return

        self.prev_state = self.state
        self.temp_state = None

    def after_process(self,thresholds):
        if not self._tracking:
            self._frame_instance = None
            return

        display_inactivity = False
        end_time = 0.0

        if self._pausing:
            self.__reset_inactive_tracker__()
        else:
            if self.temp_state is None or self.temp_state == self.prev_state:
                end_time = time.perf_counter()
                self.inactive_long += end_time - self.start_inactive_time
                self.start_inactive_time = end_time
                if self.inactive_long >= self.inactive_thresh:
                    self.squat_count = 0
                    self.improper_squat = 0
                    self._frame_instance.put_text(
                        text='Resetting SQUAT_COUNT due to inactivity!!!',
                        pos=(10, self._frame_instance.get_frame_height() - 25),
                        font_scale=0.7,
                        color='blue',
                        thickness=2)
                    display_inactivity = True
            else:
                is_full = len(self.state_seq) == len(self.complete_state_sequence)
                end_state_cnt = self.state_seq.count(self.end_state)
                checked_end_state = self.temp_state == self.end_state and end_state_cnt >= self.end_state_thresh
                if self.complete_state_sequence == self.state_seq:
                    if self.incorrect_posture:
                        self.improper_squat += 1
                        self._stage_incorrect_count += 1
                    else:
                        self.squat_count += 1
                        self._stage_correct_count += 1
                    self.reset_state()
                elif is_full:
                    if self.temp_state == self.end_state:
                        self.improper_squat += 1
                        self._stage_incorrect_count += 1
                    self.reset_state()
                elif checked_end_state:
                    self.improper_squat += 1
                    self._stage_incorrect_count += 1
                    self.reset_state()
        if 'GOAL' in thresholds:
            self._frame_instance.draw_text(
                    text="GOAL: " + str(self.improper_squat+self.squat_count)+f"/{thresholds['GOAL']}",
                    pos=(30, 100),
                    text_color=(255, 255, 230),
                    font_scale=0.7,
                    bg_color=(221, 0, 0)
                )
        self._frame_instance.draw_text(
                text="CORRECT: " + str(self.squat_count if not self._show_stage_count else self._stage_correct_count),
                pos=(int(self._frame_instance.get_frame_width() * 0.68), 30),
                text_color=(255, 255, 230),
                font_scale=0.7,
                bg_color=(18, 185, 0)
            )

        self._frame_instance.draw_text(
                text="INCORRECT: " + str(self.improper_squat if not self._show_stage_count else self._stage_incorrect_count),
                pos=(int(self._frame_instance.get_frame_width() * 0.68), 80),
                text_color=(255, 255, 230),
                font_scale=0.7,
                bg_color=(221, 0, 0)
            )

        if display_inactivity:
            self.__reset_inactive_tracker__()

        self._frame_instance = None

    def reset(self):
        self.state_seq = []
        self.temp_state = None
        self.state = None

        self.start_inactive_time = time.perf_counter()
        self.inactive_long = 0.0 # INACTIVE_TIME

        self.incorrect_posture = False

        self.squat_count = 0 # SQUAT_COUNT
        self.improper_squat = 0 # IMPROPER_SQUAT

    def set_show_stage_count(self, val: bool):
        self._show_stage_count = val

    def __reset_inactive_tracker__(self):
        self.start_inactive_time = time.perf_counter()
        self.inactive_long = 0.0
