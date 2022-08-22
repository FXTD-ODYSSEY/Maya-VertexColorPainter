
# Maya-VertexColorPainter

Single Channel Vertex Color Painter for

[Blog Post](https://blog.l0v0.com/posts/1cdbfd5e.html)

[en_US](./README.md) | [zh_CN](./README_zh.md)


## Installation 

I using a module installer method to install VertexColorPainter plugin, which you could check [here](https://github.com/robertjoosten/maya-module-installer)   
All you need to do is pretty simple, follow the step below.

1. download the release version of the plugin. (you also can clone the release branch)
2. unzip the folder to any location in your computer.(skip this step if you clone the branch)
3. drag the `VertexColorPainter.mel` to your running Maya viewport.

When you run the mel script once, the `vertex_color_painter.py` will load every time you open Maya.    

## Usage Video

https://cdn.jsdelivr.net/gh/FXTD-odyssey/FXTD-odyssey.github.io@master/post_img/1cdbfd5e/demo.mp4

## Usage

![alt](https://cdn.jsdelivr.net/gh/FXTD-odyssey/FXTD-odyssey.github.io@master/post_img/1cdbfd5e/dfb9ca62bbf7b8121c65dfb559630a1c.jpeg)

Add two UI into Maya native Paint Vertex Color Tool.

**Single Channel**
1. RGB
2. R
3. G
4. B
5. A

RGB represent all color mode  
all color mode work same as the native tool.  
Single Channel Mode only paint specified channel color.

---

**Color Display**
1. Auto
2. RGB
3. R
4. G
5. B
6. A

Switch Vertex Color Display.

