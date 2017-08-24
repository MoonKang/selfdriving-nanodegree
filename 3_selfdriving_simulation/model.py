
# coding: utf-8

# In[18]:

import numpy as np
import tensorflow as tf
import csv
import matplotlib.pyplot as plt
import os, sys
import cv2
from sklearn.model_selection import train_test_split
from keras.models import Sequential, Model
from keras.layers.core import Dense, Dropout, Activation,Lambda
from keras.optimizers import Adam
from keras.utils import np_utils
from keras.layers import Convolution2D, MaxPooling2D, Flatten, Input, ELU
from keras import initializations
from sklearn.utils import shuffle
import json
import gc
import math
import pandas as pd


# Referred https://chatbotslife.com/using-augmentation-to-mimic-human-driving-496b569760a9#.v76laaz7d
# # Data Prep

# In[19]:

csv_path = 'data/driving_log.csv'  # udacity data (fastest graphic mode)


# In[20]:

# read csv file

np.random.seed(30)
with open(csv_path) as csvfile:
    reader = csv.DictReader(csvfile)
    center_db, left_db, right_db, steer_db = [], [], [], []
    for row in reader:
        if float(row['steering']) != 0.0:
            center_db.append(row['center'])
            left_db.append(row['left'].strip())
            right_db.append(row['right'].strip())
            steer_db.append(float(row['steering']))
        else:
            # To reduce bias for straights
            prob = np.random.uniform()
            if prob <= 0.1:
                center_db.append(row['center'])
                left_db.append(row['left'].strip())
                right_db.append(row['right'].strip())
                steer_db.append(float(row['steering']))


# In[22]:

center_db, left_db, right_db, steer_db = shuffle(center_db, left_db, right_db, steer_db)

# split train & valid data
img_train, img_valid, steer_train, steer_valid = train_test_split(center_db, steer_db, test_size=0.1, random_state=30)




# In[25]:
new_size_col,new_size_row = 64, 64

def random_brightness(image):
    """
    randomly change brightness
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    bv = .3 + np.random.random()
    hsv[::2] = hsv[::2]*bv
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

def random_shift(image, steer):
    """
    randomly shift image horizontally
    """
    max_shift = 50
    max_ang = 0.2  # ang_per_pixel = 0.004

    rows, cols, _ = image.shape

    random_x = np.random.randint(-max_shift, max_shift + 1)
    random_steer = steer + (random_x / max_shift) * max_ang
    if abs(random_steer) > 1:
        random_steer = -1 if (random_steer < 0) else 1

    mat = np.float32([[1, 0, random_x], [0, 1, 0]])
    random_img = cv2.warpAffine(image, mat, (cols, rows))
    return random_img, random_steer

def random_shadow(image):
    """
    generate random shadow in random region
    """
    top_y = 320*np.random.uniform()
    top_x = 0
    bot_x = 160
    bot_y = 320*np.random.uniform()
    image_hls = cv2.cvtColor(image,cv2.COLOR_RGB2HLS)
    shadow_mask = 0*image_hls[:,:,1]
    X_m = np.mgrid[0:image.shape[0],0:image.shape[1]][0]
    Y_m = np.mgrid[0:image.shape[0],0:image.shape[1]][1]
    shadow_mask[((X_m-top_x)*(bot_y-top_y) -(bot_x - top_x)*(Y_m-top_y) >=0)]=1
    #random_bright = .25+.7*np.random.uniform()
    if np.random.randint(2)==1:
        random_bright = .5
        cond1 = shadow_mask==1
        cond0 = shadow_mask==0
        if np.random.randint(2)==1:
            image_hls[:,:,1][cond1] = image_hls[:,:,1][cond1]*random_bright
        else:
            image_hls[:,:,1][cond0] = image_hls[:,:,1][cond0]*random_bright    
    image = cv2.cvtColor(image_hls,cv2.COLOR_HLS2RGB)
    return image


def random_flip(image, steering):
    """
    randomly flip image
    """
    flip_image, flip_steering = cv2.flip(image, 1), -steering
    return flip_image, flip_steering


def select_img(center_list, left_list, right_list, steer_list, num, offsets=0.22):
    """
    randomly select among center, left, right images
    """
    rand = np.random.randint(3)
    log_path = './data'
    if rand == 0:
        image, steer = load_image(center_list[num]), steer_list[num]
    elif rand == 1:
        image, steer = load_image(left_list[num]), steer_list[num] + offsets
    elif rand == 2:
        image, steer = load_image(right_list[num]), steer_list[num] - offsets   
    if abs(steer) > 1:
        steer = -1 if (steer < 0) else 1
    return image, steer


def crop_resize(image):
    """
    Crop out image and resize to 64x64
    """
    cropped_img = image[63:136, 0:319]
    resized_img = cv2.resize(cropped_img, (new_size_col, new_size_row), cv2.INTER_AREA)
    img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
    return img
    
    
def generate_train(center_list, left_list, right_list, steer_list):
    num = np.random.randint(0, len(steer_list))
    image, steer = select_img(center_list, left_list, right_list, steer_list, num)
     
    image,steer = random_shift(image, steer)
    image = random_brightness(image)
    image = random_shadow(image)
    ind_flip = np.random.randint(2)
    if ind_flip==0:
        image,steer = random_flip(image, steer)
    
    image = crop_resize(image)
    #image = np.array(image)
    return image, steer


# # Model

# In[27]:


def nvidia_model(dropout=.4):
    """
    architecture: 5 convolutional layer with dropout, 3 fully connected layer
    activation func : elu
    """
    model = Sequential()
    model.add(Lambda(lambda x: x / 127.5 - 1.0, input_shape=(new_size_row, new_size_col, 3), name='Normalized'))
    
    nb_filters = [24, 36, 48, 64, 64]
    kernel_size = [(5, 5), (5, 5), (5, 5), (3, 3), (3, 3)]
    same, valid = ('same', 'valid')
    padding = [valid, valid, valid, valid, valid]
    strides = [(2, 2), (2, 2), (2, 2), (1, 1), (1, 1)]
    for l in range(len(nb_filters)):
        model.add(Convolution2D(nb_filters[l],
                                kernel_size[l][0], kernel_size[l][1],
                                border_mode=padding[l],
                                subsample=strides[l],
                                activation='elu'))
        model.add(Dropout(dropout))
    model.add(Flatten())
    neurons = [100, 50, 10]
    for l in range(len(neurons)):
        model.add(Dense(neurons[l], activation='elu'))
        model.add(Dropout(dropout))   
    model.add(Dense(1, activation='elu', name='Out'))
    model.add(Dense(1))
    model.summary()
    return model


def model2():
    """
    architecture: 4 convolutional layer, 3 fully connected layer with dropout
    activation func : relu
    pooling : maxpooling
    """
    model = Sequential()
    model.add(Lambda(lambda x: x / 127.5 - 1.0, input_shape=(new_size_row, new_size_col, 3), name='Normalized'))
    
    nb_filters = [32, 64, 128, 128]
    kernel_size = [(3, 3), (3, 3), (3, 3), (2, 2)]
    same, valid = ('same', 'valid')
    padding = [same, same, same, same]
    strides = [(2, 2), (2, 2), (1, 1), (1, 1)]
    
    a= len(nb_filters)-1
    for l in range(len(nb_filters)-1):
        model.add(Convolution2D(nb_filters[l],
                                kernel_size[l][0], kernel_size[l][1],
                                border_mode=padding[l],
                                subsample=strides[l],
                                activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2), strides=None, border_mode='same'))
    
    
    model.add(Convolution2D(nb_filters[a],
                                kernel_size[a][0], kernel_size[a][1],
                                border_mode=padding[a],
                                subsample=strides[a],
                                activation='relu'))
    model.add(Flatten())
    model.add(Dropout(0.5))
    model.add(Dense(128, activation='relu', name='FC1'))
    model.add(Dropout(0.5))
    model.add(Dense(128, activation='relu', name='FC2'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu', name='FC3'))
    model.add(Dense(1))
    model.summary()
    return model


# In[30]:

def model3():
    """
    architecture: 4 convolutional layer with dropout, 3 fully connected layer 
    activation func : relu
    pooling : maxpooling
    """
        model = Sequential()
    model.add(Lambda(lambda x: x / 127.5 - 1.0, input_shape=(new_size_row, new_size_col, 3), name='Normalized'))
    
    nb_filters = [32, 64, 128, 128]
    kernel_size = [(3, 3), (3, 3), (3, 3), (2, 2)]
    same, valid = ('same', 'valid')
    padding = [same, same, same, same]
    strides = [(2, 2), (2, 2), (1, 1), (1, 1)]
    
    a= len(nb_filters)-1
    for l in range(len(nb_filters)-1):
        model.add(Convolution2D(nb_filters[l],
                                kernel_size[l][0], kernel_size[l][1],
                                border_mode=padding[l],
                                subsample=strides[l],
                                activation='relu'))
        model.add(MaxPooling2D(pool_size=(2, 2), strides=None, border_mode='same'))
        model.add(Dropout(0.5))
    
    model.add(Convolution2D(nb_filters[a],
                                kernel_size[a][0], kernel_size[a][1],
                                border_mode=padding[a],
                                subsample=strides[a],
                                activation='relu'))
    model.add(Flatten())
    model.add(Dropout(0.5))
    model.add(Dense(128, activation='relu', name='FC1'))
    model.add(Dropout(0.5))
    model.add(Dense(128, activation='relu', name='FC2'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu', name='FC3'))
    model.add(Dense(1))
    model.summary()
    return model



# # Train

# In[31]:
log_path = './data'

def valid_img(img_valid, steer_valid, num):
    """ using only center image for validation """
    steering = steer_valid[num]
    image = cv2.imread(img_valid[num])
    return image, steering

def load_image(filename):
    filename = filename.strip()
    if filename.startswith('IMG'):
        filename = log_path+'/'+filename
    else:
        # load it relative to where log file is now, not whats in it
        filename = log_path+'/IMG/'+PurePosixPath(filename).name
    img = cv2.imread(filename)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def generate_valid(img_valid, steer_valid):
    """ generate validation set """
    img_set = np.zeros((len(img_valid), new_size_row, new_size_col, 3))
    steer_set = np.zeros(len(steer_valid))

    for i in range(len(img_valid)):
        img, steer = load_image(img_valid[i]), steer_valid[i]
        img_set[i] = crop_resize(img)
        steer_set[i] = steer
    return img_set, steer_set

def generate_train_batch(center, left, right, steering, batch_size):
    """ compose training batch set """
    image_set = np.zeros((batch_size, new_size_row, new_size_col, 3))
    steering_set = np.zeros(batch_size)

    while True:
        for i in range(batch_size):
            img, steer = generate_train(center, left, right, steering)
            image_set[i] = img
            steering_set[i] = steer
        yield image_set, steering_set




batch_size = 128
epoch = 14

train_generator = generate_train_batch(center_db, left_db, right_db, steer_db, batch_size)
image_val, steer_val = generate_valid(img_valid, steer_valid)



model = model2()

adam = Adam(lr=1e-4)
model.compile(optimizer=adam, loss='mse')

model_weights = 'model_5.h5'

history = model.fit_generator(train_generator, samples_per_epoch=20224, nb_epoch=epoch,
                              validation_data=(image_val, steer_val), verbose=1)


model.save(model_weights)



