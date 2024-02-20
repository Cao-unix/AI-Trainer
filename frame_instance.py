import time
import cv2
import numpy as np
import mediapipe as mp

from utils import find_angle, get_landmark_features, draw_text, draw_dotted_line, calculate_angle_between_two_points

COLORS = {
    'black'         : (0, 0, 0),
    'blue'          : (0, 127, 255),
    'red'           : (255, 50, 50),
    'green'         : (0, 255, 127),
    'light_green'   : (100, 233, 127),
    'yellow'        : (255, 255, 0),
    'light_yellow'  : (255, 255, 230),
    'magenta'       : (255, 0, 255),
    'white'         : (255,255,255),
    'cyan'          : (0, 255, 255),
    'light_blue'    : (102, 204, 255)
}

LINE_TYPE = cv2.LINE_AA
FONT = cv2.FONT_HERSHEY_SIMPLEX
OFFSET_THRESH = 35.0

global_data = {
    'keeping_feedback': []
}

class FrameInstance:
    def __init__(self, frame: np.array, pose: mp.solutions.pose.Pose):
        self._frame = frame
        self._pose = pose
        self.frame_height, self.frame_width, _ = frame.shape

        self.keypoints = pose.process(frame)

        self.coord = {
            'nose': None,
            'left_shldr': None,
            'left_elbow': None,
            'left_wrist': None,
            'left_hip': None,
            'left_knee': None,
            'left_ankle': None,
            'left_foot': None,
            'left_heel': None,
            'right_shldr': None,
            'right_elbow': None,
            'right_wrist': None,
            'right_hip': None,
            'right_knee': None,
            'right_ankle': None,
            'right_foot': None,
            'right_heel': None,
            'shldr': None,
            'elbow': None,
            'wrist': None,
            'hip': None,
            'knee': None,
            'ankle': None,
            'foot': None,
            'heel': None
        }
        self.angle = {}
        self.orientation = None
        self.__keep_feedback__()

        if self.validate():
            ps_lm = self.keypoints.pose_landmarks
            self.coord['nose'] = get_landmark_features(ps_lm.landmark, 'nose', self.frame_width, self.frame_height)
            self.coord['left_shldr'], self.coord['left_elbow'], self.coord['left_wrist'], self.coord['left_hip'], \
                self.coord['left_knee'], self.coord['left_ankle'], self.coord['left_foot'], self.coord['left_heel'] \
                = get_landmark_features(ps_lm.landmark, 'left', self.frame_width, self.frame_height)
            self.coord['right_shldr'], self.coord['right_elbow'], self.coord['right_wrist'], self.coord['right_hip'], \
                self.coord['right_knee'], self.coord['right_ankle'], self.coord['right_foot'], self.coord['right_heel'] \
                = get_landmark_features(ps_lm.landmark, 'right', self.frame_width, self.frame_height)

            offset_angle = self.get_angle('left_shldr', 'nose', 'right_shldr')

            if offset_angle > OFFSET_THRESH:
                self.orientation = 'front'
            else:
                dist_l_sh_hip = abs(self.coord['left_foot'][1] - self.coord['left_shldr'][1])
                dist_r_sh_hip = abs(self.coord['right_foot'][1] - self.coord['right_shldr'][1])

                if dist_l_sh_hip > dist_r_sh_hip:
                    self.orientation = 'left'
                    self.coord['shldr'] = self.coord['left_shldr']
                    self.coord['elbow'] = self.coord['left_elbow']
                    self.coord['wrist'] = self.coord['left_wrist']
                    self.coord['hip'] = self.coord['left_hip']
                    self.coord['knee'] = self.coord['left_knee']
                    self.coord['ankle'] = self.coord['left_ankle']
                    self.coord['foot'] = self.coord['left_foot']
                    self.coord['heel'] = self.coord['left_heel']
                else:
                    self.orientation = 'right'
                    self.coord['shldr'] = self.coord['right_shldr']
                    self.coord['elbow'] = self.coord['right_elbow']
                    self.coord['wrist'] = self.coord['right_wrist']
                    self.coord['hip'] = self.coord['right_hip']
                    self.coord['knee'] = self.coord['right_knee']
                    self.coord['ankle'] = self.coord['right_ankle']
                    self.coord['foot'] = self.coord['right_foot']
                    self.coord['heel'] = self.coord['right_heel']

    def validate(self):
        if self.keypoints.pose_landmarks:
            return True
        else:
            return False

    def get_frame(self):
        return self._frame

    def get_frame_width(self):
        return self.frame_width

    def get_frame_height(self):
        return self.frame_height

    def get_coord(self, feature):
        if self.validate():
            return self.coord[feature]
        else:
            return np.array([0, 0])

    def get_orientation(self):
        return self.orientation

    def get_angle(self, point1, point2, point3):
        angle, coord1, coord2, coord3  = self.__get_angle__(point1, point2, point3)
        return int(angle)

    def get_angle_and_draw(self, point1, point2, point3, text_color='light_green', line_color='light_blue', point_color='yellow', ellipse_color='white', dotted_line_color='blue'):
        angle, coord1, coord2, coord3 = self.__get_angle__(point1, point2, point3)

        # 以point2为原点，转换坐标系
        converted_cood1 = self.__convert_coord__(coord1, coord2)
        converted_cood2 = self.__convert_coord__(coord2, coord2)
        converted_cood3 = self.__convert_coord__(coord3, coord2)
        # cv2的角度是按顺时针方向计算，因此，常规角度要变号
        start_angle = 0 - calculate_angle_between_two_points(converted_cood2, converted_cood3)
        end_angle =  0 - calculate_angle_between_two_points(converted_cood2, converted_cood1)
        # print('>>angle: ', point1, point2, point3, coord1, coord2, coord3,
        #       converted_cood1, converted_cood2, converted_cood3, start_angle, end_angle)
        if abs(end_angle - start_angle) > 180:
            if end_angle > 0:
                end_angle = end_angle - 360
            else:
                end_angle = 360 + end_angle
            # print('>>angle change 1: ', start_angle, end_angle)
        cv2.ellipse(self._frame, coord2, (20, 20),
                    angle=0, startAngle=start_angle, endAngle=end_angle,
                    color=self.__get_color__(ellipse_color), thickness=3, lineType=LINE_TYPE)

        # draw lines between points
        self.line(point1, point2, line_color, 4)
        if point3 == 'vertical' or point3 == 'horizontal' or point3 == 'nvertical' or point3 == 'nhorizontal':
            # draw vertical or horizontal line
            draw_dotted_line(self._frame, coord2, start=coord2[1] - 50, end=coord2[1] + 20,
                             line_color=self.__get_color__(dotted_line_color))
        else:
            self.line(point2, point3, line_color, 4)

        # draw point cicle
        self.circle(point1, radius=7, color=point_color)
        self.circle(point2, radius=7, color=point_color)
        if point3 in self.coord:
            self.circle(point3, radius=7, color=point_color)

        # show angle value
        cv2.putText(self._frame, str(int(angle)), (coord2[0] + 15, coord2[1]), FONT, 0.6,
                    self.__get_color__(text_color), 2, lineType=LINE_TYPE)

        return int(angle)

    def circle(self, *args, radius=7, color='yellow'):
        for arg in args:
            cv2.circle(self._frame, self.coord[arg], radius, self.__get_color__(color), -1)
            # cv2.circle(self._frame, self.coord[center], radius, self.__get_color__(color), -1, LINE_TYPE)

    def line(self, pt1, pt2, color='light_blue', thickness=4):
        cv2.line(self._frame, self.coord[pt1], self.coord[pt2], self.__get_color__(color), thickness, LINE_TYPE)

    def draw_text(self, text, width=8, font=FONT, pos=(0, 0), font_scale=1.0, font_thickness=2, text_color=(0, 255, 0)
                  , bg_color=(0, 0, 0)):
        draw_text(self._frame, text, width, font, pos, font_scale, font_thickness, self.__get_color__(text_color), self.__get_color__(bg_color))

    def put_text(self, text, pos, font_scale, color, thickness, line_type=LINE_TYPE):
        cv2.putText(self._frame, text=text, org=pos, fontFace=FONT, fontScale=font_scale,
                    color=self.__get_color__(color), thickness=thickness, lineType=line_type)

    def show_feedback(self, text, y, text_color, bg_color, hide_delay=0):
        if hide_delay > 0:
            global_data['keeping_feedback'].append({
                'hide_time': time.perf_counter() + hide_delay,
                'text': text,
                'y': y,
                'text_color': text_color,
                'bg_color': bg_color
            })

        self.draw_text(
            text,
            pos=(30, y),
            text_color=self.__get_color__(text_color),
            font_scale=0.6,
            bg_color=self.__get_color__(bg_color)
        )

        return self._frame

    def __keep_feedback__(self):
        temp_keeping_feedback = []
        for feedback in global_data['keeping_feedback']:
            if time.perf_counter() <= feedback['hide_time']:
                temp_keeping_feedback.append(feedback)
                self.show_feedback(feedback['text'], feedback['y'], feedback['text_color'], feedback['bg_color'], 0)

        global_data['keeping_feedback'] = temp_keeping_feedback

    def __get_angle__(self, point1, point2, point3):
        key = point1 + '#' + point2 + '#' + point3
        if key not in self.angle:
            coord1 = self.get_coord(point1)
            coord2 = self.get_coord(point2)
            coord3 = None
            if point3 in self.coord:
                coord3 = self.get_coord(point3)
            else:
                if point3 == 'vertical':
                    coord3 = self.__get_vertical_coord__(point2)
                if point3 == 'horizontal':
                    coord3 = self.__get_horizontal_coord__(point2)
                if point3 == 'nvertical':
                    coord3 = self.__get_nvertical_coord__(point2)
                if point3 == 'nhorizontal':
                    coord3 = self.__get_nhorizontal_coord__(point2)

            if coord3 is None:
                return 0, np.array([0, 0]), np.array([0, 0]), np.array([0, 0])

            angle = find_angle(coord1, coord3, coord2)
            self.angle[key] = {
                'angle': angle,
                'coord1': coord1,
                'coord2': coord2,
                'coord3': coord3,
            }

        return self.angle[key]['angle'], self.angle[key]['coord1'], self.angle[key]['coord2'], self.angle[key]['coord3']

    def __get_color__(self, color):
        if isinstance(color, str):
            return COLORS[color]
        else:
            return color

    def __get_vertical_coord__(self, feature):
        return np.array([self.get_coord(feature)[0], 0])

    def __get_horizontal_coord__(self, feature):
        return np.array([0, self.get_coord(feature)[1]])

    def __get_nvertical_coord__(self, feature):
        return np.array([self.get_coord(feature)[0], self.frame_height])

    def __get_nhorizontal_coord__(self, feature):
        return np.array([self.frame_width, self.get_coord(feature)[1]])

    def __convert_coord__(self, coord, origin_coord):
        return np.array([coord[0] - origin_coord[0], 0 - (coord[1] - origin_coord[1])])