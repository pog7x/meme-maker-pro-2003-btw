from PIL import Image, ImageDraw, ImageFont


TEXT_FILL_COLOR = (255, 255, 255)
TEXT_STROKE_COLOR = (0, 0, 0)


class MemeTextRenderer:
    """Renders auto-wrapped, auto-sized meme text onto an image.

    For each text block (top / bottom) the renderer:

    1. Reserves a *zone* — a percentage of the image height where text may live.
    2. Starting from the largest font size that looks good, wraps the text
       word-by-word using actual pixel measurements (``textbbox``).
    3. Shrinks the font until the wrapped block fits inside the zone.
    4. Draws the result centred horizontally with a proportional outline stroke.
    """

    HORIZONTAL_PADDING_RATIO = 0.05
    VERTICAL_PADDING_RATIO = 0.04
    TEXT_ZONE_RATIO = 0.35
    MAX_FONT_HEIGHT_RATIO = 0.14
    MIN_FONT_SIZE = 10

    def __init__(self, image: Image.Image, font_path: str) -> None:
        self._image = image
        self._font_path = font_path
        self._draw = ImageDraw.Draw(image)
        self._img_width, self._img_height = image.size

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> str:
        """Word-wrap *text* so every line fits within *max_width* pixels."""
        words = text.split()
        if not words:
            return ""

        lines: list[str] = []
        current_line = words[0]

        for word in words[1:]:
            candidate = f"{current_line} {word}"
            bbox = self._draw.textbbox((0, 0), candidate, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line = candidate
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)
        return "\n".join(lines)

    def _fit_text(
        self,
        text: str,
        max_width: int,
        max_height: int,
    ) -> tuple[ImageFont.FreeTypeFont, str]:
        """Return the largest font + wrapped text that fits the given box."""
        max_font_size = max(
            self.MIN_FONT_SIZE,
            int(self._img_height * self.MAX_FONT_HEIGHT_RATIO),
        )

        for size in range(max_font_size, self.MIN_FONT_SIZE - 1, -1):
            font = ImageFont.truetype(self._font_path, size)
            wrapped = self._wrap_text(text, font, max_width)
            bbox = self._draw.multiline_textbbox((0, 0), wrapped, font=font)
            if (bbox[3] - bbox[1]) <= max_height:
                return font, wrapped

        font = ImageFont.truetype(self._font_path, self.MIN_FONT_SIZE)
        return font, self._wrap_text(text, font, max_width)

    def _draw_outlined_text(
        self,
        xy: tuple[float, float],
        text: str,
        font: ImageFont.FreeTypeFont,
        anchor: str,
    ) -> None:
        stroke_width = max(1, font.size // 12)
        self._draw.multiline_text(
            xy=xy,
            text=text,
            font=font,
            fill=TEXT_FILL_COLOR,
            stroke_fill=TEXT_STROKE_COLOR,
            stroke_width=stroke_width,
            anchor=anchor,
            align="center",
        )

    def _text_zone(self) -> tuple[int, int, int]:
        """Return (max_width, max_height, vertical_padding) for a text zone."""
        h_pad = int(self._img_width * self.HORIZONTAL_PADDING_RATIO)
        v_pad = int(self._img_height * self.VERTICAL_PADDING_RATIO)
        max_width = self._img_width - 2 * h_pad
        max_height = int(self._img_height * self.TEXT_ZONE_RATIO)
        return max_width, max_height, v_pad

    def draw_top_text(self, text: str) -> None:
        """Draw *text* at the top of the image, centred and auto-sized."""
        max_width, max_height, v_pad = self._text_zone()
        font, wrapped = self._fit_text(text, max_width, max_height)
        self._draw_outlined_text(
            xy=(self._img_width / 2, v_pad),
            text=wrapped,
            font=font,
            anchor="ma",
        )

    def draw_bottom_text(self, text: str) -> None:
        """Draw *text* at the bottom of the image, centred and auto-sized."""
        max_width, max_height, v_pad = self._text_zone()
        font, wrapped = self._fit_text(text, max_width, max_height)
        self._draw_outlined_text(
            xy=(self._img_width / 2, self._img_height - v_pad),
            text=wrapped,
            font=font,
            anchor="md",
        )
