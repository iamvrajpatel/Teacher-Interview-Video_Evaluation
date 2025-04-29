import logging
import traceback
import concurrent.futures

from dotenv import load_dotenv

from app.common.utils import *
from app.services.audio_transcribe import *
from app.services.data_processing import Data_processing
from app.services.emotion_detection import EmotionDetection

load_dotenv()

logging.basicConfig(level=logging.INFO, force=True)
logger = logging.getLogger(__name__)


def __process_audio(video_path: str, audio_path: str, subject: str):
    audio_extraction_status = Data_processing(video_path=video_path, audio_path=audio_path)

    if audio_extraction_status:
        logger.info("Audio extraction successful")
        txt = transcribe(audio_path=audio_path, subject=subject)
        if txt == "":
            raise Exception('No utterances found!!')
    else:
        raise Exception('Audio extraction Failed!!')

    return txt


def __similarity_score(txt, dic):
    try:
        if dic.get("department_group") == "Academic":
            similarity_score, introduction_score, example_score, methodology_score = \
                analyze_transcript(txt=txt, dic=dic, logger=logger)
            print("Academics Flow")
        else:
            similarity_score, introduction_score, example_score, methodology_score = \
                analyze_transcript_non_academics(txt=txt, dic=dic, logger=logger)
            print("Non-Academics Flow")
                
        return {'similarity_score': similarity_score, 'introduction_score': introduction_score,
            'example_score': example_score, 'methodology_score': methodology_score}
    except:
        print(traceback.format_exc())
        similarity_score = 0
        introduction_score = 0
        example_score = 0
        methodology_score = 0


def __grammar_score(txt, demo_content):
    # Calculate grammar score
    grammar_score = grammer_score_func(txt=txt, demo_content=demo_content, logger=logger)
    return {'grammar_score': grammar_score}


def __cv_task_handler(video_path):
    emotion_dictionary = video_capture(emotion_function=EmotionDetection, video_path=video_path, logger=logger)
    emotion_score_value = emotion_score(emotion_dictionary=emotion_dictionary, logger=logger)
    return {'emotion_score': emotion_score_value}


def __format_output(future_lst):
    confidence = future_lst.get('confidence', 0)
    similarity_score = future_lst.get('similarity_score', 0)
    introduction_score = future_lst.get('introduction_score', 0)
    emotion_score = future_lst.get('emotion_score', 0)
    grammar_score = future_lst.get('grammar_score', 0)
    example_score = future_lst.get('example_score', 0)
    methodology_score = future_lst.get('methodology_score', 0)
    time_management_score = future_lst.get('time_management_score', 0)

    response_lst = {
        'confidence': confidence if confidence > 0 else 0,
        'similarity_score': similarity_score if similarity_score > 0 else 0,
        'introduction_score': introduction_score if introduction_score > 0 else 0,
        'emotion_score': emotion_score if emotion_score > 0 else 0,
        'grammar_score': grammar_score if grammar_score > 0 else 0,
        'example_score': example_score if example_score > 0 else 0,
        'methodology_score': methodology_score if methodology_score > 0 else 0,
        'time_management_score': time_management_score if time_management_score > 0 else 0,
    }
    return response_lst


def main(video_path: str, audio_path: str, demo_content: dict):
    """
    Args:
        video_path (str): Path of the video file
        audio_path (str): Path of the audio file to save in a specific directory
    """
    try:
        future_lst = {}
        futures = []

        executor = concurrent.futures.ThreadPoolExecutor(os.cpu_count() - 2)

        transcription = executor.submit(__process_audio, video_path, audio_path, demo_content.get('subject',''))
        future_1 = executor.submit(__cv_task_handler, video_path)
        futures.append(future_1)

        concurrent.futures.wait([transcription])
        txt = transcription.result()

        future_2 = executor.submit(confidence_retrival, txt, audio_path, logger)
        futures.append(future_2)
        future_3 = executor.submit(__similarity_score, txt, demo_content)
        futures.append(future_3)
        future_4 = executor.submit(__grammar_score, txt, demo_content)
        futures.append(future_4)

        concurrent.futures.wait(futures)
        for future in futures:
            future_lst.update(future.result())

        response_lst = __format_output(future_lst)
        return response_lst

    except Exception:
        logger.error(traceback.format_exc())
        return {
            'confidence': 0,
            'similarity_score': 0,
            'introduction_score': 0,
            'emotion_score': 0,
            'grammar_score': 0,
            'example_score': 0,
            'methodology_score': 0,
            'time_management_score': 0
        }
