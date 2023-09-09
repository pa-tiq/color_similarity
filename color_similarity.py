import math
import json
from pathlib import Path
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.widgets import Slider  # , Button
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
import numpy


def patch_asscalar(a):
    return a.item()


setattr(numpy, "asscalar", patch_asscalar)


def update_view(newSelected=None):
    global selected
    if newSelected is not None:
        selected = newSelected
    global css4colors
    global fig
    global ax
    global precision
    plot_colors(
        colors=css4colors,
        primaryHex=css4colors[selected],
        precision=precision,
        considerLAB=False,
        fig=fig,
        ax=ax,
        selected=selected,
    )


def update_deltae_file():
    global precision
    with open("colors_deltae_precision.txt", "w") as cdp:
        json.dump(precision, cdp)


def onclick(event):
    # print(
    #     "%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f"
    #     % (
    #         "double" if event.dblclick else "single",
    #         event.button,
    #         event.x,
    #         event.y,
    #         event.xdata,
    #         event.ydata,
    #     )
    # )
    if event.xdata == None or event.y < 60:
        return
    for key, value in color_positions.items():
        if (
            event.xdata >= value[0]
            and event.xdata <= value[0] + 100
            and event.ydata >= value[1]
            and event.ydata <= value[1] + 20
        ):
            update_view(newSelected=key)
            break


def plot_colors(
    colors,
    *,
    ncols=4,
    sort_colors=True,
    primaryHex,
    precision,
    considerLAB,
    fig=None,
    ax=None,
    selected,
):
    cell_width = 320
    cell_height = 22
    swatch_width = 48
    margin = 12

    # Sort colors by hue, saturation, value and name.
    if sort_colors is True:
        names = sorted(
            colors, key=lambda c: tuple(mcolors.rgb_to_hsv(mcolors.to_rgb(c)))
        )
    else:
        names = list(colors)

    n = len(names)
    nrows = math.ceil(n / ncols)

    width = cell_width * 4 + 2 * margin
    height = cell_height * nrows + 2 * margin
    dpi = 72

    first_render = True

    with plt.ion():
        if fig and ax:
            ax.clear()
            first_render = False
        else:
            fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
            fig.subplots_adjust(
                margin / width,
                margin / height,
                (width - margin) / width,
                (height - margin) / height,
            )
            cid = fig.canvas.mpl_connect("button_press_event", onclick)
            fig.subplots_adjust(bottom=0.1)

        # ax_button = fig.add_axes([0.8, 0.025, 0.1, 0.04])
        # button = Button(ax_button, "Apply", hovercolor="0.975")

        # def apply_slider_value(event):
        #     # global precision
        #     # global selected
        #     print(precision_slider.val)
        #     print(precision[selected])
        #     print(event)

        # button.on_clicked(apply_slider_value)

        ax_precision = fig.add_axes([0.10, 0.03, 0.65, 0.03])
        ax_precision.clear()
        precision_slider = Slider(
            ax=ax_precision,
            label="Precisão",
            valmin=1,
            valmax=60,
            valinit=precision[selected],
            valstep=0.5,
        )

        def update_precision_slider(val):
            precision[selected] = precision_slider.val
            fig.canvas.draw_idle()
            update_deltae_file()
            update_view()

        precision_slider.on_changed(update_precision_slider)

        ax.set_xlim(0, cell_width * 4)
        ax.set_ylim(cell_height * (nrows - 0.5), -cell_height / 2.0)
        ax.yaxis.set_visible(False)
        ax.xaxis.set_visible(False)
        ax.set_axis_off()

        for i, name in enumerate(names):
            row = i % nrows
            col = i // nrows
            y = row * cell_height

            swatch_start_x = cell_width * col
            text_pos_x = cell_width * col + swatch_width + 7

            # rgb_tuple = mcolors.to_rgb(name)
            # rgb_255 = []
            # for rgb_value in rgb_tuple:
            #    rgb_255.append(int(rgb_value * 255))

            deltae = delta_e_str(colors[name], primaryHex, considerLAB=considerLAB)

            if first_render:
                color_positions[name] = (swatch_start_x, y - 9)

            ax.text(
                text_pos_x,
                y,
                # name + " " + str(rgb_255),
                name + "|∆=" + deltae + "|P=" + str(precision[name]),
                # name,
                fontsize=18 if selected == name else 14,
                horizontalalignment="left",
                verticalalignment="center",
                fontweight="extra bold" if selected == name else "normal",
            )

            ax.add_patch(
                Rectangle(
                    xy=(swatch_start_x, y - 9),
                    width=swatch_width,
                    height=18,
                    facecolor=colors[name]
                    if float(deltae) < precision[selected]
                    else "#FFFFFF",
                    edgecolor="0.7",
                )
            )

    return fig, ax


def delta_e_str(hex1, hex2, considerLAB=True):
    hex1 = hex1.lstrip("#")
    hex2 = hex2.lstrip("#")
    rgb1 = tuple(int(hex1[i : i + 2], 16) for i in (0, 2, 4))
    rgb2 = tuple(int(hex2[i : i + 2], 16) for i in (0, 2, 4))
    srgbHEX1 = sRGBColor(rgb1[0], rgb1[1], rgb1[2], is_upscaled=True)
    srgbHEX2 = sRGBColor(rgb2[0], rgb2[1], rgb2[2], is_upscaled=True)
    lab1 = convert_color(srgbHEX1, LabColor)
    lab2 = convert_color(srgbHEX2, LabColor)
    if not considerLAB:
        lab1.lab_l = 50.0
        lab2.lab_l = 50.0
    deltae = delta_e_cie2000(lab1, lab2)
    return f"{deltae:.2f}"


red = sRGBColor(255, 0, 0, is_upscaled=True)
blue = sRGBColor(0, 0, 255, is_upscaled=True)
deepskyblue = sRGBColor(0, 191, 255, is_upscaled=True)
green = sRGBColor(0, 255, 0, is_upscaled=True)
yellow = sRGBColor(255, 255, 0, is_upscaled=True)
brown = sRGBColor(165, 42, 42, is_upscaled=True)
orange = sRGBColor(255, 160, 0, is_upscaled=True)
grey = sRGBColor(128, 128, 128, is_upscaled=True)

# green: precision = 21 sem considerar LAB
# deepskyblue: precision = 23 sem considerar LAB
# grey: precision = 4 sem considerar LAB

css4colors = mcolors.CSS4_COLORS
primary_rbg_hex = grey.get_rgb_hex()
css4colors["grey"] = primary_rbg_hex

color_positions = {}
selected = "grey"
precision = {}

path = Path("./colors_deltae_precision.txt")
if path.is_file():
    with open("colors_deltae_precision.txt", "r") as cdp:
        precision = json.load(cdp)
else:
    for key in css4colors.keys():
        precision[key] = 20
    precision["grey"] = 4
    with open("colors_deltae_precision.txt", "w") as cdp:
        json.dump(precision, cdp)


fig, ax = plot_colors(
    colors=css4colors,
    primaryHex=primary_rbg_hex,
    precision=precision,
    considerLAB=False,
    selected=selected,
)
plt.show()
