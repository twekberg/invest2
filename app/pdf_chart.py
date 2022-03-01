"""
Draw a simple line graph of (x,y) points with a caption.
"""

# Reference:
#   https://www.reportlab.com/docs/reportlab-userguide.pdf

import math
from io import StringIO
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from datetime import date, timedelta
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.graphics import renderPDF
from reportlab.pdfgen.canvas import Canvas
import reportlab.lib.colors

# User Guide Chapter 11 Graphics
# Page 114

def caption(drawing, text, width, height):
    """
    Draw a caption for the graph centered at the top.
    """
    lab = Label()
    lab.setOrigin(width / 2, height + 60)
    lab.boxAnchor = 's'
    lab.textAnchor = 'middle'
    lab.dx = 0
    lab.dy = 0
    lab.setText(text)
    drawing.add(lab)

def legend(drawing, gd):
    """
    Draw the legend.
    """
    
    # Calculate width of legend
    dev_null = StringIO.StringIO()
    c = Canvas(dev_null)
    max_width = 0
    for text in gd['legend_text']:
        max_width = max(max_width, c.stringWidth(text, 'Helvetica', 12))
    dev_null.close()

    x = gd['graph_width'] + (gd['width'] - gd['graph_width']) / 2 + gd['legend_pad']
    y = gd['graph_height'] - gd['base_legend_height'] - gd['n_graphs'] * gd['font_height']
    r = Rect(x, y, gd['base_legend_width'] + max_width + gd['legend_pad'],
             gd['base_legend_height'] + gd['n_graphs'] * gd['font_height'],
             fillColor=colors.white, strokeColor=colors.black,
             strokeWidth=1)
    drawing.add(r)

    line_no = 1
    for (text, color) in zip(gd['legend_text'], gd['graph_colors']):
        x = gd['graph_width'] + (gd['width'] - gd['graph_width']) / 2 + gd['legend_pad'] * 2 \
            + gd['legend_text_indent']
        #y = gd['graph_x'] + gd['graph_height'] - gd['legend_pad'] - gd['font_height'] * line_no
        y = gd['graph_height'] - gd['legend_pad'] - gd['font_height'] * line_no
        s = String(x, y, text)
        drawing.add(s)

        # Colored bar
        b = Rect(x-gd['legend_text_indent'], y,
                 gd['legend_text_indent'] / 2, gd['legend_text_indent'] / 2,
                 fillColor = color, strokeColor=color,
                 strokeWidth=1)
        drawing.add(b)
        line_no += 1


# Graph Detail
gd = dict(caption='This is the graph caption',
          width=720,
          height=360,
          font_height=10,
          graph_x=50,
          graph_y=50,
          graph_width=540,
          graph_height=225,
          graph_colors=(reportlab.lib.colors.red,
                        reportlab.lib.colors.blue,
                        reportlab.lib.colors.green,
                        reportlab.lib.colors.magenta,
                        reportlab.lib.colors.cyan,
                        reportlab.lib.colors.black),
          legend_text= ('Red', 'Blue', 'Green', 'Magenta', 'Cyan', 'Black'),
          legend_pad=5,         # Pad around legend border
          legend_text_indent=10,# separation between bar and text
          base_legend_width=10, # Acount for small box and spacing
          base_legend_height=10,
          n_graphs=1,
)


def render_chart(filename, caption_text, data, legend_text, **kwargs):
    """
    Render the chart with a caption. Allows up to 6 simultaneous
    colored graphs.

    filename - if None performs the operations to render the chart
    simply returns the drawing object. This allows the caller to
    incorporate the chart into a document.

    caption_text - text to appear above the graph

    data - array of an array of (x,y) points. This allows one to draw
    multiple graphs at the same time, each with different colors.

    legend_text - array of text to appear in the legend to the right
    of the graph. The len of this array should be the same as
    len(data).  A small colored rectangle appears to the left of the
    text matching the color of the corresponding graph.

    kwargs - allows one to override values in gd. Some of the other
    required parameters could be specified this way, but since they
    are required they are not.
    """
    gd['caption'] = caption_text
    gd['legend_text'] = legend_text
    for name, value in kwargs.items():
        if name in gd:
            gd[name] = value

    minx = 1e20
    maxx = 0                    # ordinal date
    maxy = 0                    # money
    gd['n_graphs'] = len(data)
    for points in data:
        for (x,y) in points:
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y > maxy:
                maxy = y
    # Convert to multiple of a power of 10.
    p = pow(10, int(math.log10(maxy)))
    maxy = math.ceil(maxy / p) * p
    drawing = Drawing(gd['width'], gd['height'])
    lp = LinePlot()
    lp.x = gd['graph_x']
    lp.y = gd['graph_y']
    lp.height = gd['graph_height']
    lp.width = gd['graph_width']
    lp.data = data
    for (i, marker) in zip(range(len(data)), ['FilledCircle', 'FilledTriangle',
                                             'FilledDiamond', 'FilledStarFive',
                                             'FilledSquare', 'FilledPentagon']):
        lp.lines[i].symbol = makeMarker(marker)
        lp.lines[i].strokeColor = gd['graph_colors'][i]
    lp.joinedLines = 1
    lp.strokeColor = colors.black
    lp.xValueAxis.valueMin = minx
    lp.xValueAxis.valueMax = maxx
    lp.xValueAxis.valueStep = .5 # Every 6 months
    lp.xValueAxis.labelTextFormat = '%3.2f'
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = maxy
    lp.yValueAxis.valueStep = p
    drawing.add(lp)
    caption(drawing, gd['caption'], gd['width'], gd['graph_height'])
    legend(drawing, gd)
    if filename:
        renderPDF.drawToFile(drawing, filename, 'lineplot with dates')
    return drawing
