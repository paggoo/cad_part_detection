import tensorflow as tf
from tensorflow import compat
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns

#tf.disable_v2_behavior()

# import data
zoo = pd.read_csv("zoo.csv")
print(zoo.head())
print("This ZOO dataset is consised of", len(zoo), "rows.")

# see animal_type
#sns.barplot(x = zoo.class_type.value_counts().index, y = zoo.class_type.value_counts())
sns.countplot(x = 'class_type', data = zoo)
plt.title('class_type')
plt.show()

# plot correlation of features
corr = zoo.iloc[:,1:-1].corr()
colormap = sns.diverging_palette(220, 10, as_cmap = True)
plt.figure(figsize=(14,14))
sns.heatmap(corr, cbar=True,  square=True, annot=True, fmt='.2f', annot_kws={'size': 12},
            cmap=colormap, linewidths=0.1, linecolor='white')
plt.title('Correlation of ZOO Features', y=1.05, size=15)
plt.show()

# prepare for split
x_data = zoo.iloc[:,:-1]
print(x_data.head())
print('features: ', x_data.shape)
y_data = zoo.iloc[:, -1:]
print(y_data.head())
print('labels: ', y_data.shape)

# split train test
from sklearn.model_selection import train_test_split
x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, train_size = 0.8, test_size = 0.2, shuffle=True)

print('x_train: ', x_train.shape)
print('y_train: ', y_train.shape)
print('x_test: ', x_test.shape)
print('y_test: ', y_test.shape)

# drop animal_name column
train_name = x_train['animal_name']
test_name = x_test['animal_name']
x_train = x_train.iloc[:,1:]
x_test = x_test.iloc[:,1:]

print('x_train: ', x_train.shape)
print(x_train.head())
print('x_test: ', x_test.shape)
print(x_test.head())

# tensorflow placeholder
house = tf.keras.datasets.boston_housing

#tfd = tfp.distributions
init = tf.compat.v1.global_variables_initializer()
with tf.compat.v1.Session() as sess:
    sess.run(init)

    model = tf.keras.Sequential([
      tf.keras.layers.Dense(1,kernel_initializer='glorot_uniform'),
      #tfp.layers.DistributionLambda(lambda t: tfd.Normal(loc=t, scale=1))
    ])
X = tf.placeholder(tf.float32, [None,16])
Y = tf.placeholder(tf.int32, [None, 1])

# one hot
Y_one_hot = tf.one_hot(Y, 7)
Y_one_hot = tf.reshape(Y_one_hot, [-1, 7])


