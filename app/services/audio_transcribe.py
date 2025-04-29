import os
import assemblyai as aai

from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline


def transcribe(audio_path: str, subject: str):
    """_summary_

    Args:
        audio_path (str): path of the audio file to be transcribed
        subject (str): subject of the video
    """
    if subject.lower() == 'hindi':
        aai.settings.api_key = os.getenv("Assembly_API_KEY")
        transcriber = aai.Transcriber()
        config = aai.TranscriptionConfig(
            language_code='hi',
            speech_model=aai.SpeechModel.best,
        )

        transcript = transcriber.transcribe(audio_path, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            return ""
        else:
            return transcript.text
    else:
        model_id = "distil-whisper/distil-small.en"

        model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id)
        processor = AutoProcessor.from_pretrained(model_id)
        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor
        )
        transcript = pipe(audio_path)
        # print(transcript)
        return transcript['text']
