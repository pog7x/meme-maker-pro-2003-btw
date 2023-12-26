import base64
import os
import time

from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse, StreamingHttpResponse
from django.shortcuts import render
from django.views import View
from PIL import Image, ImageDraw, ImageFont

dq = []


def image_list(from_folder: str):
    all_images = []

    for file in os.listdir(f"{settings.STATICFILES_DIRS[0]}{from_folder}"):
        if file.endswith(".png") or file.endswith(".jpg"):
            all_images.append(file)

    return sorted(all_images, reverse=True)


def get_file_path(file, folder):
    return f"{settings.STATICFILES_DIRS[0]}{folder}{file}"


format_ext = {
    "png": "png",
    "jpg": "jpeg",
    "jpeg": "jpeg",
}


class StreamView(View):
    def get(self, request: HttpRequest) -> StreamingHttpResponse:
        return StreamingHttpResponse(
            self.event_stream(),
            content_type="text/event-stream",
        )

    @staticmethod
    def event_stream():
        while True:
            yield dq.pop() if dq else ""
            time.sleep(1)


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
        ctx = {
            "top_text": top_text,
            "bottom_text": bottom_text,
            "file": file,
        }

        if request.POST.get("share") == "true":
            file_name = f"{int(time.time())}.{file.split('.')[-1]}"
            with open(get_file_path(file_name, "/shared/"), "wb+") as f:
                f.write(base64.b64decode(encoded_string))
                dq.append(f'data: <img src="static/shared/{file_name}" alt="">\n\n')
            return render(request, self.template_name, context=ctx)

        if file:
            buffered = BytesIO()

            file_path = Path(get_file_path(file, "/img/"))
            if not file_path.exists():
                return render(request, self.template_name)

            pil_img = Image.open(get_file_path(file, "/img/"))

            base_width = 300
            wpercent = base_width / float(pil_img.size[0])
            hsize = int((float(pil_img.size[1]) * float(wpercent)))

            pil_img = pil_img.resize((base_width, hsize), Image.Resampling.LANCZOS)

            draw = ImageDraw.Draw(pil_img)
            _, img_height = pil_img.size
            font = ImageFont.truetype(get_file_path("impact.ttf", "/fonts/"), 20)

            if top_text:
                draw.text(
                    xy=(50, 20),
                    text=top_text,
                    fill=(255, 255, 255),
                    font=font,
                    stroke_fill=(0, 0, 0),
                    stroke_width=2,
                )

            if bottom_text:
                draw.text(
                    xy=(50, img_height - 60),
                    text=bottom_text,
                    fill=(255, 255, 255),
                    font=font,
                    stroke_fill=(0, 0, 0),
                    stroke_width=2,
                )

            pil_img.save(buffered, format=format_ext.get(file.split(".")[-1]))

            encoded_string = base64.b64encode(buffered.getvalue())
            ctx["encoded_string"] = encoded_string.decode("utf-8")

            return render(request, self.template_name, context=ctx)

        return render(request, self.template_name)
