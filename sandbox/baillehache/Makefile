run:
	python __main__.py

edit:
	geany Makefile *.py

video:
	ffmpeg -framerate 2 -pattern_type glob -i 'Data/b*.png' \
  -c:v libopenh264 -pix_fmt yuv420p Data/video.mp4

dependencies:
	pip install earthengine-api torch torchvision opencv-python
