**Behavioral Cloning Project**

The goals / steps of this project are the following:
* Use the simulator to collect data of good driving behavior
* Build, a convolution neural network in Keras that predicts steering angles from images
* Train and validate the model with a training and validation set
* Test that the model successfully drives around track


[//]: # (Image References)

[image1]: ./steering_dist.png "Steering distribution"
[image2]: ./steering_hist.png "Steering Histogram"
[image3]: ./img.png "Image1"
[image4]: ./img_adj.png "Image2"
[image5]: ./image_adj.png "Image3"
[image6]: ./steering_adj.png "Steering New Histogram"


#### Files

My project includes the following files:
* model.py containing the script to create and train the CNN model
* drive.py for driving the car in autonomous mode
* model.h5 containing a trained convolution neural network 
* writeup_report.md or writeup_report.pdf summarizing the results

### Model Architecture and Training Strategy

#### 1. Model
The model architecture (model2) consists of 4 convolution neural network layers with 3x3, 2x2 filter sizes and depths of 32, 64, 128, and 128. (model.py lines 243-268). The data is normalized in the model using a Keras lambda layer (code line 250). Between cnn layers I have added RELU for nonlinearity and maxpooling to focus on neurons that mattered the most. 

#### 2. Attempts to reduce overfitting

The model contains dropout layers in order to reduce overfitting (model.py lines 259,261,263). After trying a few variations for dropout rate, I have found 0.5 to work well in mitigating bias toward going straight. 

The model was trained and validated on different data sets to ensure that the model was not overfitting (code line 71). The model was tested by running it through the simulator and ensuring that the vehicle could stay on the track.

#### 3. Model parameter tuning

The model used an adam optimizer and have set parameters to be following: (lr=1e-4, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0). 

#### 4. Data Exploration

I found that data fluctuation is quite consistent over time frame and 
![alt text][image1]

that  data is highly concentrated near 0 steering angle. 

![alt text][image2]

I have used a combination of center, right, and left images and have adjusted +- 0.22 for left and right images. 

![alt text][image3]

Then I have 1) shifted, adjusted brightness, shadowed, and flipped images. 

![alt text][image4]

Then I have resized images to be 64x64 for training.

![alt text][image5]

I randomly shuffled the data set and put 10% of the data into a validation set. I used this training data for training the model. The validation set helped determine if the model was over or under fitting. The ideal number of epochs was 14 as evidenced by trials with epoch of 10 and 15.

#### 5. Approach 
My first step was to use a convolution neural network architecture similar to the one provided by Nvidia. I was able to get good training and valid loss but I was not able to complete a lap on track with the trained model. Then I added max pool layers between cnn so that the model can be more focused in training. 

In order to gauge how well the model was working, I split my image and steering angle data into a training and validation set. I found that my first model had a low mean squared error on the training set but a high mean squared error on the validation set. This implied that the model was overfitting. To combat the overfitting, I modified the model to include dropouts. 

The final step was to run the simulator to see how well the car was driving around track one. There were a few spots where the vehicle fell off the track.  To improve the driving behavior in these cases, I have added more data for curves at dirt road after bridge.  At the end of the process, the vehicle is able to drive autonomously around the track without leaving the road.
