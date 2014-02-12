from flask import Flask
import webpixels

app = Flask(__name__)

controller = webpixels.ColorKinetics(host="192.168.1.44")

pixels = []
for i in range(8):
   r, g, b = controller.channels[i*3:i*3+3]
   pixels.append(webpixels.RgbPixel(r, g, b))

@app.route('/get/<int:pixel>')
def pixel_get(pixel):
   r, g, b = pixels[pixel].get()
   color = r << 16 | g << 8 | b
   return '%06x' % color

@app.route('/set/<int:pixel>/<color>')
def pixel_set(pixel, color):
   color = int(color, 16)
   r, g, b = color >> 16 & 255, color >> 8 & 255, color & 255
   pixels[pixel].set(r, g, b)
   controller.sync()
   return ''

@app.route('/reset')
def pixel_reset():
   for pixel in pixels:
      pixel.set(0, 0, 0)
   controller.sync()
   return ''

if __name__ == '__main__':
   controller.sync()
   app.debug = True
   app.run(host='0.0.0.0', port=80)
