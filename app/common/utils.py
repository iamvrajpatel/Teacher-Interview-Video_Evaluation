import os
import re
import json
import time
import cv2
import math
import librosa
import numpy as np

from openai import OpenAI
from mutagen.mp3 import MP3
from collections import Counter
from pydub import AudioSegment, silence

from app.common.constants import knowledge_prompt, grammer_prompt, \
    knowledge_prompt_non_acedamics, \
    sys_instruct_non_academic


def detect_silence(audio_path):
    myaudio = AudioSegment.from_mp3(audio_path)
    dBFS = myaudio.dBFS
    sil = silence.detect_silence(myaudio, silence_thresh=dBFS - 16)
    sil = [((start / 1000), (stop / 1000)) for start, stop in sil]  #in sec
    sec = 0
    for s in sil:
        sec += int(s[1] - s[0])

    audio = MP3(audio_path)
    length = audio.info.length

    voiced_ratio = (length - sec) / length
    if voiced_ratio >= 0.9:
        return 1
    else:
        return voiced_ratio / 0.9


def confidence_retrival(text, audio_path, logger):
    start = time.time()
    analysis = {
        "volume": False,
        "pace": False,
        "speech_rate": False,
        "language": False,
        "intensity_variability": False
    }

    # Language: Check for assertive language
    print("Language")
    weak_phrases = re.findall(r'\b(Umm|Uhh|Err|Maybe|I think|I guess|Kind of|Sort of|You see|You know|Possibly|Probably|It seems|I assume|Somewhat|I suppose|I believe|It appears|It could be|As I recall|Like I said|I am not sure|More or less|One of those|So, basically|Something like|Not quite sure|Well, it is like|As far as I know|It could be said|How do I put this|It is possible that|I think it might be|If that makes sense|You know what I mean|If I remember correctly)\b',
                              text, re.IGNORECASE)
    analysis["language"] = len(weak_phrases) < len(text.split()) * 0.1  # Less than 10% fillers

    # Load audio file for further analysis
    y, sr = librosa.load(audio_path)

    # Volume: Calculate average volume (RMS)
    print("Volume")
    rms = librosa.feature.rms(y=y)
    mean_rms = np.mean(rms)
    analysis["volume"] = mean_rms > 0.02  # Threshold for audible volume

    # Pace: Calculate tempo
    print("Pace")
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    analysis["pace"] = 90 <= tempo <= 180  # Typical speech tempo range in BPM

    # Speech rate: Words per minute
    print("Speech Rate")
    words = text.split()
    duration = librosa.get_duration(y=y, sr=sr)
    words_per_minute = len(words) / (duration / 60)
    analysis["speech_rate"] = 120 <= words_per_minute <= 160

    # Intensity variability: Dynamic range
    print("Intensity")
    intensity_variability = np.max(rms) - np.min(rms)
    analysis["intensity_variability"] = intensity_variability > 0.1  # Threshold for dynamic range

    # Determine confidence level
    print("Conf Score")
    confidence_level = sum(analysis.values()) / len(analysis)
    weight = detect_silence(audio_path)
    confidence_score = int(confidence_level * weight * 10)
    logger.info("Calculated Confidence Score in " + str(time.time() - start))

    time_management_score = 0

    if 120 <= words_per_minute <= 150:
        time_management_score += 5

    if duration >= 600:
        if duration >= 900:
            time_management_score += 3
        else:
            time_management_score += 5

    return {'confidence': confidence_score, 'time_management_score': time_management_score}


def analyze_transcript(txt, dic: dict, logger):
    logger.info("Comparison of content started")
    start = time.time()

    prompt = knowledge_prompt(
        txt=txt,
        subject=dic.get('subject', ''),
        level=dic.get('level', ''),
        topic=dic.get('topic', ''),
    )

    client = OpenAI(api_key=os.getenv("OpenAI_API_KEY"))
    response = client.chat.completions.create(model="gpt-4o-mini", messages=[
        {
            'role': 'user',
            'content': prompt
        }
    ], temperature=0.01)
    end = time.time()
    logger.info("Content comparison in " + str(round(end-start, 2)) + "s")
    j = json.loads(response.choices[0].message.content.replace("```", "").replace("json", ""))
    knowledge_score = j['knowledge_score']
    introduction_score = 0

    persona_score = sum([j.get("name_provided", False), j.get("name_provided", False), j.get("name_provided", False)])
    explanation_score = sum([j.get("role_provided", False), j.get("summary_given", False)])

    introduction_score += 5 if persona_score == 3 else persona_score*2
    introduction_score += explanation_score*2+1 if explanation_score > 0 else 0

    example_score = 0

    example_score += 4 * j.get("example_provided", False)
    example_score += 3 * sum([j.get("metaphor_provided", False), j.get("analogy_provided", False)])

    bloom_tag_list = j['bloom_tag_list']

    methodology_score = 0

    for bloom_tag in bloom_tag_list:
        if bloom_tag.lower() == "application" or bloom_tag.lower() == "applying":
            methodology_score = 10

    return knowledge_score, introduction_score, example_score, methodology_score


def video_capture(emotion_function, video_path: str, logger, frequency: int = 100):
    """_summary_

    Args:
        emotion_function (function)
        frequency (int)

    Returns:
        emotion_lst: list
    """
    logger.info("Preparing emotion_dictionary...")
    start = time.time()
    vid = cv2.VideoCapture(video_path)
    emotion_lst = []
    length = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
    jump = length // frequency
    for selected_frame in range(jump, length - jump - jump, jump):
        vid.set(cv2.CAP_PROP_POS_FRAMES, selected_frame - 1)
        res, frame = vid.read()
        emotion_lst.append(emotion_function(frame))

    vid.release()
    cv2.destroyAllWindows()
    counter = Counter(emotion_lst)
    end = time.time()
    logger.info("Prepared emotion_dictionary in " + str(round(end-start, 2)) + "s")
    return dict(counter)


def grammer_score_func(txt, demo_content, logger):
    logger.info("Started grammer_score_func")
    start = time.time()
    client = OpenAI(api_key=os.environ.get("OpenAI_API_KEY"))
    subject = demo_content.get('subject','')
    prompt = grammer_prompt(txt, subject)
    response = client.chat.completions.create(model="gpt-3.5-turbo",
                                              messages=[
                                                  {
                                                      'role': 'user',
                                                      'content': prompt
                                                  }
                                              ],
                                              temperature=0.01, max_tokens=10, top_p=1, frequency_penalty=0,
                                              presence_penalty=0)
    response = str(response.choices[0].message.content)

    for i in response:
        if i.isnumeric():
            end = time.time()
            logger.info("grammer_score calculated in " + str(round(end-start, 2)) + "s")
            return int(i)

    end = time.time()
    logger.info("grammer_score calculated in " + str(round(end-start, 2)) + "s")
    return 0


def emotion_score(emotion_dictionary: dict, logger):
    """_summary_

    Args:
        emotion_dictionary (dict): _description_

    Returns:
        _type_: _description_
    """
    lst = []
    for key, value in emotion_dictionary.items():
        lst.append((key, value))
    lst = sorted(lst, key=lambda x: x[-1], reverse=True)
    lst = [i[0] for i in lst][:2]
    logger.info("Calculated emotion_score")
    if ('Anger' in lst) or ('Sad' in lst):
        return 5
    else:
        return 10


def analyze_transcript_non_academics(txt, dic: dict, logger):
    knowledge_score = 0
    adaptability_score = 0
    introduction_score = 0
    feedback_handling_score = 0
    
    logger.info("Comparison of content started")
    client = OpenAI(api_key=os.environ.get("OpenAI_API_KEY"))
    start = time.time()

    prompt = knowledge_prompt_non_acedamics(
        txt=txt,
        subject=dic.get('subject', ''),
        role=dic.get('role', '')
    )
    
    sys_instruct = sys_instruct_non_academic(dic.get('role', ''), dic.get('subject', ''))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                'role': 'system',
                'content': sys_instruct
            },
            {
                'role': 'user',
                'content': prompt
            }
    ], temperature=0.01)
    end = time.time()
    logger.info("Content comparison in " + str(round(end-start, 2)) + "s")    
    
    res_score = json.loads(response.choices[0].message.content.replace("```", "").replace("json", "").strip())
    
    introduction_score = (res_score.get('question_1_rate', 0) + res_score.get('question_2_rate', 0))/2
    
    adaptability_score = (res_score.get('question_3_rate', 0) + res_score.get('question_4_rate', 0) + res_score.get('question_5_rate', 0) + res_score.get('question_6_rate', 0))/4
    
    feedback_handling_score = res_score.get('question_7_rate', 0)
    knowledge_score = res_score.get('knowledge_score', 0)

    return math.ceil(knowledge_score), math.ceil(introduction_score), math.ceil(adaptability_score), math.ceil(feedback_handling_score)