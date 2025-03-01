# Indexed PNG Palette Swapper

```
usage: spriterecolor.py [-h] (--file FILE | --directory DIRECTORY) [--overwrite] --reference REFERENCE output

Given an indexed .png file or a directory of indexed .png files, recolors them using another provided indexed .png file's palette.

positional arguments:
  output                Directory to put output files.

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           File to recolor.
  --directory DIRECTORY Directory of files to recolor.
  --overwrite           Overwrite existing files in output directory.
  --reference REFERENCE Reference file to take palette from.
```

Small python script that lets you transfer one indexed png's palette to another indexed png (or a directory of them.) Either set `--file` or `--directory`, not both.

Requires the `pillow` python package.

Tries to keep transparency where possible. I highly recommend ensuring that all transparent colors have completely unique rgb values from other colors, as doing otherwise can cause strange behavior when you try to use the image in general.

<p align="center">
  <img src="ex.png" /> <br>
  <i>wow look it's transparent</i>
</p>