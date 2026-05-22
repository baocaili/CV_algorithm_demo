"""Small toolbar icons (PIL → Tk PhotoImage); keep references on the app to avoid GC."""

from __future__ import annotations

import tkinter as tk

from PIL import Image, ImageDraw, ImageTk


def _icon(master: tk.Misc, draw) -> tk.PhotoImage:
    im = Image.new("RGBA", (22, 22), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    draw(dr, 22, 22)
    ph = ImageTk.PhotoImage(im, master=master)
    return ph


def build_toolbar_icons(master: tk.Misc) -> dict[str, tk.PhotoImage]:
    def disk(d, w, h):
        d.rectangle((3, 5, 15, 15), outline=(50, 100, 200), width=2)
        d.polygon([(10, 3), (17, 10), (10, 10)], fill=(50, 100, 200))

    def film(d, w, h):
        d.rounded_rectangle((3, 6, 19, 16), radius=2, outline=(120, 60, 160), width=2)
        for x in (6, 10, 14):
            d.rectangle((x, 8, x + 2, 14), fill=(120, 60, 160))

    def cam(d, w, h):
        d.rounded_rectangle((4, 7, 18, 16), radius=2, outline=(60, 120, 80), width=2)
        d.ellipse((8, 4, 14, 10), outline=(60, 120, 80), width=2)

    def pencil(d, w, h):
        d.line([(5, 17), (17, 5)], fill=(40, 40, 40), width=3)
        d.polygon([(16, 4), (18, 6), (15, 7)], fill=(200, 140, 60))

    def save(d, w, h):
        d.rectangle((5, 3, 15, 14), outline=(50, 110, 70), width=2)
        d.polygon([(7, 14), (15, 14), (11, 19)], fill=(50, 110, 70))

    def rec(d, w, h):
        d.ellipse((6, 6, 16, 16), outline=(200, 50, 50), width=2)
        d.ellipse((10, 10, 12, 12), fill=(200, 50, 50))

    def stop(d, w, h):
        d.rounded_rectangle((6, 6, 16, 16), radius=1, fill=(160, 40, 40))

    keys = ("open_image", "open_video", "camera", "draw", "save", "rec_start", "rec_stop")
    funcs = (disk, film, cam, pencil, save, rec, stop)
    return {k: _icon(master, f) for k, f in zip(keys, funcs)}


def build_draw_tool_icons(master: tk.Misc) -> dict[str, tk.PhotoImage]:
    """Icons for draw-mode tool palette (pencil, line, polygon, circle)."""

    def pencil_ic(d, w, h):
        d.line([(5, 17), (17, 5)], fill=(40, 40, 40), width=3)
        d.polygon([(16, 4), (18, 6), (15, 7)], fill=(200, 140, 60))

    def line_ic(d, w, h):
        d.line([(5, 16), (17, 6)], fill=(30, 50, 180), width=3)

    def poly_ic(d, w, h):
        d.polygon([(6, 16), (17, 16), (13, 5)], outline=(0, 110, 40), width=2)

    def circle_ic(d, w, h):
        d.ellipse((5, 5, 17, 17), outline=(180, 70, 0), width=2)

    keys = ("draw_pencil", "draw_line", "draw_poly", "draw_circle")
    funcs = (pencil_ic, line_ic, poly_ic, circle_ic)
    return {k: _icon(master, f) for k, f in zip(keys, funcs)}
