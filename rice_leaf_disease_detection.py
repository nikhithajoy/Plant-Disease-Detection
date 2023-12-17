# -*- coding: utf-8 -*-
"""Rice_Detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Oh3EvKnhWivaqaNAj6EWKwvO0OppB9dl

##Install Dependencies
"""

from google.colab import drive
import os
import cv2
import numpy as np

#data augmentation
from tensorflow.keras.preprocessing.image import ImageDataGenerator

#to display images and graphs
import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras import layers, models

drive.mount('/content/drive/')

#obtaining the labels
data_directory = '/content/drive/MyDrive/Leaf disease Dataset/Rice'
os.listdir(os.path.join(data_directory))

data = ImageDataGenerator(
    rotation_range=20,  # Randomly rotate images by 20 degrees
    zoom_range=0.2,     # Randomly zoom images by 20%
    horizontal_flip=True,  # Randomly flip images horizontally
    brightness_range=(0.8, 1.2),  # Randomly adjust brightness
    rescale=1./255      # Rescale pixel values to [0, 1]
)

# Apply data augmentation to the images in the directory and load the augmented data
augmented_data = data.flow_from_directory(data_directory, target_size=(256, 256), batch_size=32, class_mode='binary')

# Convert the augmented data to TensorFlow dataset using image_dataset_from_directory
data = tf.keras.utils.image_dataset_from_directory(data_directory, batch_size=32, image_size=(256, 256), label_mode='binary')

"""1488 - healthy
977 - infected
"""

data_iterator = data.as_numpy_iterator()

batch = data_iterator.next()

fig, ax = plt.subplots(ncols=4, figsize=(20,20))
for idx, img in enumerate(batch[0][:4]):
    ax[idx].imshow(img.astype(int))
    ax[idx].title.set_text(batch[1][idx])

"""Data Splitting"""

len(data)

train_size = int(len(data)*0.7)
val_size = int(len(data)*0.2)+1
test_size = int(len(data)*0.1)+1

train_size+test_size+val_size

train = data.take(train_size)
val = data.skip(train_size).take(val_size)
test = data.skip(train_size+val_size).take(test_size)

print(len(test))
print(len(train))
print(len(val))

"""Model Building"""

# Load EfficientNet-B0 model with pre-trained weights
base_model = tf.keras.applications.EfficientNetB0(
  weights="imagenet", include_top=False, input_shape=(256, 256, 3)
)

# Freeze pre-trained layers to avoid overfitting
for layer in base_model.layers[:]:
  layer.trainable = False

# Add custom classification head
x = base_model.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(128, activation="relu")(x)
output = layers.Dense(1, activation="sigmoid")(x)

# Define the entire model
model = models.Model(inputs=base_model.input, outputs=output)

# Compile the model
model.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])

# Train the model
hist = model.fit(
    train,
    epochs=10,
    validation_data=val,
)

fig = plt.figure()
plt.plot(hist.history['loss'], color='teal', label='loss')
plt.plot(hist.history['val_loss'], color='orange', label='val_loss')
fig.suptitle('Loss', fontsize=20)
plt.legend(loc="upper left")
plt.show()

fig = plt.figure()
plt.plot(hist.history['accuracy'], color='teal', label='accuracy')
plt.plot(hist.history['val_accuracy'], color='orange', label='val_accuracy')
fig.suptitle('Accuracy', fontsize=20)
plt.legend(loc="upper left")
plt.show()

from tensorflow.keras.metrics import Precision, Recall, BinaryAccuracy

pre = Precision()
re = Recall()
acc = BinaryAccuracy()

for batch in test.as_numpy_iterator():
    X, y = batch
    yhat = model.predict(X)
    pre.update_state(y, yhat)
    re.update_state(y, yhat)
    acc.update_state(y, yhat)

print(pre.result(), re.result(), acc.result())

img = cv2.imread("/content/test_rice.jpg")
plt.imshow(img)
plt.show()

resize = tf.image.resize(img, (256,256))
plt.imshow(resize.numpy().astype(int))
plt.show()

yhat = model.predict(np.expand_dims(resize/255, 0))
yhat

if yhat > 0.5:
    print(f'Predicted class is healthy')
else:
    print(f'Predicted class is infected')

model.save(os.path.join('Rice_Detection.h5'))

