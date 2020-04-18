from keras.models import Model
from keras.layers import Input, Dense, Cropping2D, Add, Activation, Flatten
from keras.layers.core import Dropout, Lambda, SpatialDropout2D
from keras.layers.convolutional import Conv2D, Conv2DTranspose
from keras.layers.pooling import MaxPooling2D
from keras.layers.merge import concatenate
import keras 
from metrics import jaccard_index, jaccard_index_softmax

def cnn_oztel_2017(image_shape, activation='relu', lr=0.1, optimizer="sgd"):
    """Create the CNN proposed by Oztel et. al.

       Args:
            image_shape (3D tuple): dimensions of the input image.

            activation (str, optional): Keras available activation type.

            lr (float, optional): learning rate value.

            optimizer (str, optional): optimizer used to minimize the loss
            function. Posible options: 'sgd' or 'adam'.
        
       Returns:
            model (Keras model): model containing the CNN created.
    """

    #dinamic_dim = (None,)*(len(image_shape)-1) + (1,)
    #inputs = Input(dinamic_dim, name="input")
    inputs = Input(image_shape)
        
    conv1 = Conv2D(32, (5, 5), activation=activation,
                   kernel_initializer='he_normal', padding='same', 
                   name="conv1") (inputs)
    p1 = MaxPooling2D((2, 2)) (conv1)
    conv2 = Conv2D(32, (5, 5), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv2") (p1)
    p2 = MaxPooling2D((2, 2)) (conv2)
    conv3 = Conv2D(64, (5, 5), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv3") (p2)
    p3 = MaxPooling2D((2, 2)) (conv3)
    conv4 = Conv2D(64, (4, 4), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv4") (p3)

    o = Flatten() (conv4)
    outputs = Dense(1, activation='sigmoid') (o)
 
    # Loss type 
    model = Model(inputs=[inputs], outputs=[outputs])
    
    # Select the optimizer
    if optimizer == "sgd":
        opt = keras.optimizers.SGD(lr=lr, momentum=0.99, decay=0.0, 
                                   nesterov=False)
    elif optimizer == "adam":
        opt = keras.optimizers.Adam(lr=lr, beta_1=0.9, beta_2=0.999, 
                                    epsilon=None, decay=0.0, amsgrad=False)
    else:
        raise ValueError("Error: optimizer value must be 'sgd' or 'adam'")
        
    # Compile the model
    model.compile(optimizer=opt, loss='binary_crossentropy',
                  metrics=["accuracy"])

    return model

def cnn_oztel_2017_test(model, image_shape, activation='relu', lr=0.1, 
                        optimizer="sgd"):

    dinamic_dim = (None,)*(len(image_shape)-1) + (1,)
    inputs = Input(dinamic_dim, name="input")
    #inputs = Input((image_shape[0], image_shape[1], image_shape[2]))

    conv1 = Conv2D(32, (5, 5), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv1") (inputs)
    p1 = MaxPooling2D((2, 2)) (conv1)
    conv2 = Conv2D(32, (5, 5), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv2") (p1)
    p2 = MaxPooling2D((2, 2)) (conv2)
    conv3 = Conv2D(64, (5, 5), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv3") (p2)
    p3 = MaxPooling2D((2, 2)) (conv3)
    conv4 = Conv2D(64, (4, 4), activation=activation,
                   kernel_initializer='he_normal', padding='same',
                   name="conv4") (p3)

    o = Conv2D(2, (1 ,1), activation=activation, kernel_initializer='he_normal',
               padding='valid')(conv4)
    o = Conv2DTranspose(2, kernel_size=(4,4), strides=(2,2),
                        kernel_initializer='he_normal')(o)
    o = Cropping2D(((1, 1), (1, 1)))(o)

    o2 = Conv2D(2, (1, 1), activation=activation)(p2)
    o = Add()([o , o2])

    o = Conv2DTranspose(2, kernel_size=(4,4), strides=(2,2), padding='valid')(o)
    o = Cropping2D(((1, 1), (1, 1)))(o)

    o1 = Conv2D(2, (1, 1), activation=activation)(p1)
    o = Add()([o , o1])

    o = Conv2DTranspose(2, kernel_size=(2,2), strides=(2,2), padding='same')(o)

    outputs = Activation('softmax')(o)

    model_test = Model(inputs=[inputs], outputs=[outputs])

    # Load the weights of the train model
    model_test.get_layer("conv1").set_weights(model.get_layer("conv1").get_weights()) 
    model_test.get_layer("conv2").set_weights(model.get_layer("conv2").get_weights()) 
    model_test.get_layer("conv3").set_weights(model.get_layer("conv3").get_weights()) 
    model_test.get_layer("conv4").set_weights(model.get_layer("conv4").get_weights()) 

    # Select the optimizer
    if optimizer == "sgd":
        opt = keras.optimizers.SGD(lr=lr, momentum=0.99, decay=0.0,
                                   nesterov=False)
    elif optimizer == "adam":
        opt = keras.optimizers.Adam(lr=lr, beta_1=0.9, beta_2=0.999,
                                    epsilon=None, decay=0.0, amsgrad=False)
    else:
        raise ValueError("Error: optimizer value must be 'sgd' or 'adam'")

    del model

    # Compile the model
    model_test.compile(optimizer=opt, loss='categorical_crossentropy',
                       metrics=[jaccard_index_softmax])

    return model_test
