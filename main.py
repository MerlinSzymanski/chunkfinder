#! usr/bin/env python3

"""Aim of the project - write a simple script to check if there are identical
parts/chunks of pixels within one picture. The intention is to find e.g photoshoped
bands in scientific publications"""

'''Basic principle. first rough approach: Split picture into 15x15 pixel chunks.
compose a "Hash" from the pixel values, compare the values. If there are two Hashes 
exactly the same, mark it on the image. Later, use a BLAST-like approach 
to find the whole area from a seed-area'''

from PIL import Image, ImageDraw
from collections import defaultdict
import random

class Block():
    """
The Block-class is the most important class of this script. It saves the 
information of the pixels as a "hash" and stores the coordinates of the block on 
the picture.the hashes are later used to determine equal content among the blocks
    """
    def __init__(self,image,x1,y1,x2,y2):
        self.image = image
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.crop = image.crop((x1,y1,x2,y2))
        self.hash =  self.get_hash()
        
    def get_hash(self):
        hash = ""
        px = self.crop.load()
        width, height = self.crop.size
        for i in range(width):
            for j in range(height):
                hash = hash + "".join([str(x) for x in px[i,j]])
        return hash
    
    def check_intercept(self, block):
        """This method is later used to get the network of blocks... For now it is not used
        any further"""
        upper_block = self if self.y1<block.y1 else block
        lower_block = self if self.y1>block.y1 else block
        
        if(upper_block.y2 > lower_block.y1):
            if(lower_block.x2 > upper_block.x1 and lower_block.x1 < upper_block.x2):
                return True
        return False

"""Main"""

blocklist = defaultdict(list)
im = Image.open("example3.jpeg")
window = 20

m = 0
for x in range(0,im.size[0]-window,5):
    for y in range(0,im.size[1]-window,5):
        m+=1
        
n = 0
for x in range(0,im.size[0]-window,5):
    for y in range(0,im.size[1]-window,5):
        n+=1
        print(n,"/",m, end = "\r")
        block = Block(im, x,y,x+window,y+window)
        blocklist[block.hash].append(block)

to_draw = {}
for hash in blocklist:
    if(len(blocklist[hash])>1):
        to_draw[hash] = blocklist[hash]

draw = ImageDraw.Draw(im)
for hash in to_draw:
    col = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    for block in to_draw[hash]:
        draw.rectangle((block.x1,block.y1,block.x2,block.y2), fill=None, outline=col)

im.save("example4.jpeg")

