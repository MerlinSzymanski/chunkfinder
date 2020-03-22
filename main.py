#! usr/bin/env python3

"""Aim of the project - write a simple script to check if there are identical
parts/chunks of pixels within one picture. The intention is to find e.g photoshoped
bands in scientific publications"""

'''Basic principle. first rough approach: Split picture into 15x15 pixel chunks.
compose a "Hash" from the pixel values, compare the values. If there are two Hashes 
exactly the same, mark it on the image. Later, use a BLAST-like approach 
to find the whole area from a seed-area'''

from PIL import Image, ImageDraw
from collections import defaultdict, Counter
import random
from scipy.stats import entropy
import sys

class Chunk():
    """This class stores the overlapping blocks as one chunk, replacing the older block-structure"""
    def __init__(self, block):
        self.blocks = [block]
        self.x1 = block.x1
        self.y1 = block.y1
        self.x2 = block.x2
        self.y2 = block.y2

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
        self.entropy = self.get_entropy()
        self.assigned_to_chunk = False
        global window
        global slide
        
    def get_entropy(self):
        """This calculates the shannon-entropy of the pixel values in the picture to filter out the
        most noisy chunks. Most evenly distributed colors mean heigh shannon entropy"""
        pix_values = []
        px = self.crop.load()
        width, height = window, window
        for i in range(width):
            for j in range(height):
                pix_values.append("".join([str(x) for x in px[i,j]]))
        length = len(pix_values)
        count = Counter(pix_values)
        for key in count:
            count[key] = count[key]/length
        return entropy(list(count.values()))
        
    def get_coords_within(self):
        coords = []
        for i in range(self.x1,self.x1+window-slide, slide):
            for j in range(self.y1,self.y1+window-slide,slide):
                coords.append((i,j))
        return coords
        
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
#global variables

blocklist = []
coord_block_dict = {}
window = 15
slide = 5
thresh = 3

#open the image
im = Image.open(sys.argv[1])

#For the status window
m = 0
for x in range(0,im.size[0]-window,slide):
    for y in range(0,im.size[1]-window,slide):
        m+=1

#The analysis
n = 0
for x in range(0,im.size[0]-window,slide):
    for y in range(0,im.size[1]-window,slide):
        n+=1
        print(n,"/",m, end = "\r")
        #create a subimage
        block = Block(im, x,y,x+window,y+window)
        if(block.entropy > thresh):
            #save the block
            blocklist.append(block)
            coord_block_dict[(block.x1,block.y1)]=block

#Now find Chunks
chunklist = []
for block in blocklist:
    if(block.assigned_to_chunk == False):
        chunk = Chunk(block)
        for coords in block.get_coords_within():
            try:
                chunk.blocks.append(coord_block_dict[coords])
                coord_block_dict[coords].assigned_to_chunk = True
            except KeyError:
                pass
    chunklist.append(chunk)
print("")
print(len(blocklist))
print(len(chunklist))

#Draw the clusters
draw = ImageDraw.Draw(im)
for blk in blocklist:
    col = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    draw.rectangle((blk.x1,blk.y1,blk.x2,blk.y2), fill=None, outline=col)

im.save(f"done_{sys.argv[1]}")

