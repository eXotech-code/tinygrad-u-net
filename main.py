#!/usr/bin/env python3

import sys
import os
import numpy
import re
from PIL import Image
from random import shuffle
from tinygrad import *
from input_transform import preprocess

"""
An implementation of U-Net using tinygrad.
Based on https://arxiv.org/abs/1505.04597 and https://github.com/milesial/Pytorch-UNet.
Fueled by truckloads of Yerbata, way too many Serbian movies and ADHD meds.
"""

# TODO)) Investigate whether adding the dice score to the loss
# (like in the Pytorch-UNet implementation) helps with training.
# TODO)) Find out what kind of weight map generation scheme would be
# effective on ultrasound images.
# TODO)) Understand what kind of deformations are done to the data in the whitepaper.

class DoubleConv:
  """
  Each convolutional layer of the U-Net consists of two conv blocks
  followed by a max pooling operation.
  Each conv block is made out of one 3x3 kernel convolution operation, batch norm and a ReLu.
  """

  def __init__(self, in_chan, out_chan):
    self.conv1 = Conv2d(in_chan, out_chan, 3, bias=False)
    self.bn = BatchNorm(out_chan)
    self.conv2 = Conv2d(out_chan, out_chan, 3, bias=False)

  def __call__(self, x):
    x = self.conv1(x)
    x = self.bn(x)
    x = x.relu()
    x = self.conv2(x)
    x = self.bn(x)
    return x.relu()

  def weights(self):
    return [self.conv1.weight, self.conv2.weight]


class EncoderLayer:
  def __init__(self, in_chan, out_chan):
    self.conv = DoubleConv(in_chan, out_chan)

  def __call__(self, x):
    return self.conv(x.max_pool2d())

  def weights(self):
    return self.conv.weights()


class DecoderLayer:
  def __init__(self, in_chan, out_chan):
    self.transpose_conv = ConvTranspose2d(in_chan, in_chan, 2)
    self.conv = DoubleConv(in_chan, out_chan)

  def __call__(self, x):
    x = self.transpose_conv(x)
    return self.conv(x)

  def weights(self):
   return [self.transpose_conv.weight, self.conv.weights()]

class UNet():
  def __init__(self):
    self.initial = DoubleConv(1, 64)
    self.e1 = EncoderLayer(64, 128)
    self.e2 = EncoderLayer(128, 256)
    self.e3 = EncoderLayer(256, 512)
    self.e4 = EncoderLayer(512, 1024)
    self.d1 = DecoderLayer(1024, 512)
    self.d2 = DecoderLayer(512, 256)
    self.d3 = DecoderLayer(256, 128)
    self.d4 = DecoderLayer(128, 64)
    self.final = Conv2d(64, 2, 1)

  def __call__(self, x):
    x = self.e1(x)
    x = self.e2(x)
    x = self.e3(x)
    x = self.e4(x)
    x = self.d1(x)
    x = self.d2(x)
    x = self.d3(x)
    x = self.d4(x)
    return self.final(x)

  def weights(self):
   return self.initial.weights()
   + self.e1.weights() + self.e2.weights() + self.e3.weights() + self.e4.weights()
   + self.d1.weights() + self.d2.weights() + self.d3.weights() + self.d4.weights()
   + self.final.weights()

def get_data():
  root = "data"
  dirs = ["benign", "malignant", "normal"]
  data = []
  for dir in dirs:
    current_dir = os.path.join("data", dir)
    files = filter(lambda x: re.search("_mask*", x) is None, os.listdir(current_dir))
    for filename in files:
      data.append(preprocess(os.path.join(current_dir, filename)))
  return data


def train():
  data = get_data()
  shuffle(data)
  train_size = int(len(data) * 0.6)
  train, val = data[:train_size], data[train_size:]

if __name__ == "__main__":
  train()
