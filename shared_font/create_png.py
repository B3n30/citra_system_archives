import json
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

font = PIL.ImageFont.truetype("Montserrat-Regular.otf", 22)

chars = dict()
with open('code_manifest.json','r') as f:
    content = json.loads(f.read().replace('\n', ' '))['glyphMap']
    chars= {y:x for x,y in content.iteritems()}

specific_offsets={"m":[-2,0]}

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
                if (chars[current_char] in specific_offsets):
                    draw.text((pos_x+specific_offsets[chars[current_char]][0], pos_y+specific_offsets[chars[current_char]][1]), chars[current_char], "#FFF", font=font)
                else:
                    draw.text((pos_x, pos_y), chars[current_char], "#FFF", font=font)
            current_char += 1
            if (current_char > 94):
                font = PIL.ImageFont.truetype("unifont-10.0.05.ttf", 22)
            pos_x += x_offset
        pos_y += y_offset
    img.save("code_sheet"+str(sheet)+".png","PNG")
