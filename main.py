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
        
    def find_coordinates(self):
        self.x1 = min([blk.x1 for blk in self.blocks]) -5
        self.x2 = max([blk.x2 for blk in self.blocks]) +5
        self.y1 = min([blk.y1 for blk in self.blocks]) -5
        self.y2 = max([blk.y2 for blk in self.blocks]) +5
        
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
        self.crossing_blocks = []
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
        self.counter = Counter(pix_values)
        count = self.counter
        for key in count:
            count[key] = count[key]/length
        return entropy(list(count.values()))
        
    def get_coords_within(self):
        coords = []
        for i in range(self.x1,self.x1+window, slide):
            for j in range(self.y1,self.y1+window,slide):
                coords.append((i,j))
        return coords
    
    def calc_hist(self):
        return is_uniform(list(self.counter.values()))
        
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
coord_block_dict1 = {}
coord_block_dict2 = {}
coord_block_dict3 = {}
coord_block_dict4 = {}

window = 30
slide = 15
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
        print("Analyze Moving Frame",n,"/",m, end = "\r")
        #create a subimage
        block = Block(im, x,y,x+window,y+window)
        if(block.entropy > thresh):
            #save the block
            blocklist.append(block)
            coord_block_dict1[(block.x1,block.y1)]=block
            coord_block_dict2[(block.x1,block.y2)]=block
            coord_block_dict3[(block.x2,block.y1)]=block
            coord_block_dict4[(block.x2,block.y2)]=block
            #find crossing blocks
            for cord in block.get_coords_within():
                for blockdict in [coord_block_dict1,coord_block_dict2,coord_block_dict3,coord_block_dict4]:
                    try:
                        crossing_block = blockdict[cord]
                        block.crossing_blocks.append(crossing_block)
                        crossing_block.crossing_blocks.append(block)
                    except KeyError:
                        pass
                    
print("")
print("Found Complex Blocks: ",len(blocklist))
#Now find chunks
#recursive block-finder
def get_blocks(block):
    blocks = block.crossing_blocks
    for blk in blocks:
        if(not blk.assigned_to_chunk):
            blk.assigned_to_chunk = True
            blocks.extend(get_blocks(blk))
    return blocks

chunklist = []
for block in blocklist:
    if(block.assigned_to_chunk == False):
        chunk = Chunk(block)
        block.assigned_to_chunk == True
        chunk.blocks.extend(get_blocks(block))
        chunklist.append(chunk)
print("Found Clusters: ",len(chunklist))

#Find and exclude Text 
from pytesseract import image_to_string
print("Exclude text and draw")

draw = ImageDraw.Draw(im)
for chunk in chunklist:
    chunk.find_coordinates()
    subim = im.crop((chunk.x1,chunk.y1,chunk.x2,chunk.y2))
    text = image_to_string(subim)
    if(text == ""):
        col = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        draw.rectangle((chunk.x1,chunk.y1,chunk.x2,chunk.y2), fill=None, outline=col)

im.save(f"done_{sys.argv[1]}")

