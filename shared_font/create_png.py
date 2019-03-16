#!/usr/bin/env python3

import json
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

#font = PIL.ImageFont.truetype("Anonymous.ttf", 20)
font = PIL.ImageFont.truetype("Montserrat-Regular.otf", 20)

chars = dict()
with open('code_manifest.json','r') as f:
    content = json.loads(f.read().replace('\n', ' '))['glyphMap']
    chars= {y:x for x,y in content.items()}

rows=1
cols=5
sheetCount = 1501
width=128
height=32

x_start_offset = 0
y_start_offset = 1
x_offset = 25
y_offset = 25

current_char = 0
for sheet in range(sheetCount):
    img = PIL.Image.new("RGBA", (width, height))
    draw = PIL.ImageDraw.Draw(img)
    pos_y = y_start_offset
    for row in range(rows):
        pos_x = x_start_offset
        for col in range(cols):
            if (current_char in chars.keys()):
                draw.text((pos_x, pos_y), chars[current_char], "#FFF", font=font)
            current_char += 1
            if (current_char > 94):
                font = PIL.ImageFont.truetype("unifont-10.0.05.ttf", 22)
            pos_x += x_offset
        pos_y += y_offset
    img.save("code_sheet"+str(sheet)+".png","PNG")
