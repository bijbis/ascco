import os
import urllib2
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image

filename = './logo.png'


# def get_python_image():
#     """ Get a python logo image for this example """
#     if not os.path.exists(filename):
#         response = urllib2.urlopen('http://www.python.org/community/logos/python-logo.png')
#         f = open(filename, 'w')
#         f.write(response.read())
#         f.close()


# get_python_image()

doc = SimpleDocTemplate("image.pdf", pagesize=letter)
parts = []
parts.append(Image(filename, height=80, width=150))
doc.build(parts)
