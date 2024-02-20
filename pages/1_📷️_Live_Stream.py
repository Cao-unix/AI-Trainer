import av
import os
import sys
import streamlit as st
from streamlit_webrtc import VideoHTMLAttributes, webrtc_streamer
from aiortc.contrib.media import MediaRecorder
import traceback

BASE_DIR = os.path.abspath(os.path.join(__file__, '../../'))
sys.path.append(BASE_DIR)

from utils import get_mediapipe_pose
from process import process, data
from trainer_process_match import data as name
from frame_instance import FrameInstance
from thresholds import get_thresholds_beginner_with_goal, get_thresholds_pro_with_goal, get_thresholds_beginner, get_thresholds_pro
st.title('AI Fitness Trainer: Solid Ball')
grade = st.radio('Select Grade', ['Beginner', 'Pro'], horizontal=True)
example = st.radio('Select Mode', ['Free', 'Plan', 'Free_Goal','Match'], horizontal=True)
data['example'] = example
thresholds = None
if example == 'Match':
    nick_name = st.text_input('请输入昵称', 'player')
    name['nick_name'] = nick_name

if data['example'] == 'Free_Goal':
    goal = st.number_input('Set A Goal', 1,30)
    if grade == 'Beginner':
        thresholds = get_thresholds_beginner_with_goal(goal)
    elif grade == 'Pro':
        thresholds = get_thresholds_pro_with_goal(goal)
else:
    if grade == 'Beginner':
        thresholds = get_thresholds_beginner()

    elif grade == 'Pro':
        thresholds = get_thresholds_pro()
# Initialize face mesh solution
pose = get_mediapipe_pose()

if 'download' not in st.session_state:
    st.session_state['download'] = False

output_video_file = f'output_live.flv'


def video_frame_callback(frame: av.VideoFrame):
    try:
        frame = frame.to_ndarray(format="rgb24")  # Decode and get RGB frame
        frame = process(FrameInstance(frame, pose),thresholds)  # Process frame
        return av.VideoFrame.from_ndarray(frame, format="rgb24")  # Encode and return BGR frame
    except Exception as ex:
        traceback.print_exc()


def out_recorder_factory() -> MediaRecorder:
    return MediaRecorder(output_video_file)


ctx = webrtc_streamer(
    key="Squats-pose-analysis",
    video_frame_callback=video_frame_callback,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},  # Add this config
    media_stream_constraints={"video": {"width": {'min': 480, 'ideal': 480}}, "audio": True},
    video_html_attrs=VideoHTMLAttributes(autoPlay=True, controls=False, muted=True),
    out_recorder_factory=out_recorder_factory
)

download_button = st.empty()

if os.path.exists(output_video_file):
    with open(output_video_file, 'rb') as op_vid:
        download = download_button.download_button('Download Video', data=op_vid, file_name='output_live.flv')

        if download:
            st.session_state['download'] = True

if os.path.exists(output_video_file) and st.session_state['download']:
    os.remove(output_video_file)
    st.session_state['download'] = False
    download_button.empty()





