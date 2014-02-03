import webpixels

controller = webpixels.ColorKinetics(host="192.168.1.44")

pixels = []
for i in xrange(8):
   r, g, b = controller.channels[i*3:i*3+3]
   pixels.append(webpixels.RgbPixel(r, g, b))

print pixels
