import base64
import os
import queue
import threading
import time
import uuid

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from django_htmx.http import trigger_client_event
from PIL import Image, ImageDraw, ImageFont


KEEPALIVE_INTERVAL_SECONDS = 15
IMAGE_BASE_WIDTH = 300
MEME_FONT_SIZE = 20
TEXT_FILL_COLOR = (255, 255, 255)
TEXT_STROKE_COLOR = (0, 0, 0)
TEXT_STROKE_WIDTH = 2


def image_list(from_folder: str) -> list[str]:
    """Return sorted list of image filenames from the given static subfolder."""
    static_root = settings.STATICFILES_DIRS[0]
    return sorted(
        [
            f
            for f in os.listdir(f"{static_root}{from_folder}")
            if f.endswith((".png", ".jpg"))
        ],
        reverse=True,
    )


def get_file_path(file: str, folder: str) -> str:
    """Build absolute path to a file inside the static directory."""
    return f"{settings.STATICFILES_DIRS[0]}{folder}{file}"


FORMAT_EXT = {
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg",
}


class SSEBroker:
    """Thread-safe pub/sub broker that broadcasts SSE messages to all subscribers.

    Each SSE client gets its own ``queue.Queue``.  When ``broadcast()`` is
    called, the message is pushed into every active queue so that **all**
    connected tabs / users receive the event.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, queue.Queue[str]] = {}
        self._lock = threading.Lock()

    def subscribe(self) -> tuple[str, queue.Queue[str]]:
        """Register a new subscriber and return (subscriber_id, queue)."""
        subscriber_id = uuid.uuid4().hex
        subscriber_queue: queue.Queue[str] = queue.Queue()
        with self._lock:
            self._subscribers[subscriber_id] = subscriber_queue
        return subscriber_id, subscriber_queue

    def unsubscribe(self, subscriber_id: str) -> None:
        """Remove a subscriber when the SSE connection is closed."""
        with self._lock:
            self._subscribers.pop(subscriber_id, None)

    def broadcast(self, message: str) -> None:
        """Push *message* into every subscriber's queue (non-blocking)."""
        with self._lock:
            for subscriber_queue in self._subscribers.values():
                subscriber_queue.put_nowait(message)

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)


sse_broker = SSEBroker()


def format_sse(data: str, event: str | None = None) -> str:
    """Format a payload as a valid SSE frame.

    See https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events#event_stream_format
    """
    lines = []
    if event:
        lines.append(f"event: {event}")
    for line in data.splitlines():
        lines.append(f"data: {line}")
    lines.append("\n")
    return "\n".join(lines)


class StreamView(View):
    """SSE endpoint that broadcasts shared memes to every connected client."""

    def get(self, request: HttpRequest) -> StreamingHttpResponse:
        response = StreamingHttpResponse(
            self._event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

    @staticmethod
    def _event_stream():
        subscriber_id, subscriber_queue = sse_broker.subscribe()
        try:
            while True:
                try:
                    message = subscriber_queue.get(
                        timeout=KEEPALIVE_INTERVAL_SECONDS,
                    )
                    yield message
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            sse_broker.unsubscribe(subscriber_id)


class IndexView(View):
    template_name = "index.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        ctx = {
            "image_list": image_list("/img"),
            "shared_image_list": image_list("/shared"),
        }
        return render(request, self.template_name, context=ctx)


class MemeView(View):
    template_name = "meme.html"

    def post(self, request: HttpRequest) -> HttpResponse:
        file = request.POST.get("file")
        top_text = request.POST.get("top_text")
        bottom_text = request.POST.get("bottom_text")
        encoded_string = request.POST.get("encoded_string")
        is_share = request.POST.get("share") == "true"
        ctx = {
            "top_text": top_text,
            "bottom_text": bottom_text,
            "file": file,
            "encoded_string": encoded_string,
        }

        if is_share:
            file_name = f"{int(time.time())}.{file.split('.')[-1]}"
            with open(get_file_path(file_name, "/shared/"), "wb+") as f:
                f.write(base64.b64decode(encoded_string))

            sse_broker.broadcast(
                format_sse(
                    data=f'<img src="static/shared/{file_name}" alt="">',
                    event="message",
                )
            )

            return trigger_client_event(
                response=render(request, self.template_name, context=ctx),
                name="new_picture",
            )

        if file:
            file_path = Path(get_file_path(file, "/img/"))
            if not file_path.exists():
                return render(request, self.template_name)

            pil_img = Image.open(file_path)
            wpercent = IMAGE_BASE_WIDTH / float(pil_img.size[0])
            hsize = int(float(pil_img.size[1]) * wpercent)
            pil_img = pil_img.resize(
                (IMAGE_BASE_WIDTH, hsize), Image.Resampling.LANCZOS
            )

            draw = ImageDraw.Draw(pil_img)
            _, img_height = pil_img.size
            font = ImageFont.truetype(
                get_file_path("impact.ttf", "/fonts/"), MEME_FONT_SIZE
            )

            if top_text:
                draw.text(
                    xy=(50, 20),
                    text=top_text,
                    fill=TEXT_FILL_COLOR,
                    font=font,
                    stroke_fill=TEXT_STROKE_COLOR,
                    stroke_width=TEXT_STROKE_WIDTH,
                )

            if bottom_text:
                draw.text(
                    xy=(50, img_height - 60),
                    text=bottom_text,
                    fill=TEXT_FILL_COLOR,
                    font=font,
                    stroke_fill=TEXT_STROKE_COLOR,
                    stroke_width=TEXT_STROKE_WIDTH,
                )

            buffered = BytesIO()
            pil_img.save(buffered, format=FORMAT_EXT.get(file.split(".")[-1]))

            encoded_string = base64.b64encode(buffered.getvalue())
            ctx["encoded_string"] = encoded_string.decode("utf-8")

            return render(request, self.template_name, context=ctx)

        return render(request, self.template_name)
