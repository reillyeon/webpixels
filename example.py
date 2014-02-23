import webpixels
import webpixels.controller
import time

controller = webpixels.controller.ColorKinetics(host="10.11.1.116")

pixels = []
for i in xrange(16):
   r, g, b = controller.channels[i*3:i*3+3]
   pixels.append(webpixels.RgbPixel(r, g, b))

while True:
   for i in xrange(len(pixels)):
      for j in xrange(len(pixels)):
         if i == j:
            pixels[j].set(255, 255, 255)
         else:
            pixels[j].set(0, 0, 0)
      controller.sync()
      time.sleep(1)

#pixels[0].set(255, 0, 0)
#pixels[1].set(255, 255, 0)
#pixels[2].set(0, 255, 0)
#pixels[3].set(0, 255, 255)
#pixels[4].set(0, 0, 255)
#pixels[5].set(255, 0, 255)
#pixels[6].set(255, 255, 255)
#pixels[7].set(128, 255, 0)

controller.sync()
