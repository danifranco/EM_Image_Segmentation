import tensorflow as tf
from tensorflow.keras.layers import Dropout, SpatialDropout3D, Conv3D,\
                                    Conv3DTranspose, MaxPooling3D, concatenate,\
                                    ELU, BatchNormalization, Activation, \
                                    ZeroPadding3D, Add, Multiply
from tensorflow.keras import Model, Input
from metrics import binary_crossentropy_weighted, jaccard_index, \
                    jaccard_index_softmax, weighted_bce_dice_loss


def Attention_U_Net_3D(image_shape, activation='elu', feature_maps=[32, 64, 128, 256], 
                       depth=3, drop_values=[0.1,0.1,0.1,0.1], spatial_dropout=False, 
                       batch_norm=False, k_init='he_normal', z_down=2,
                       loss_type="bce", optimizer="sgd", lr=0.001, n_classes=1):
    """Create 3D U-Net with Attention blocks.                                   
                                                                                
       Based on `Attention U-Net: Learning Where to Look for the Pancreas <https://arxiv.org/abs/1804.03999>`_.

       Parameters
       ----------
       image_shape : 3D tuple
           Dimensions of the input image.

       activation : str, optional
           Keras available activation type.

       feature_maps : array of ints, optional
           Feature maps to use on each level. Must have the same length as the 
           ``depth+1``.
   
       depth : int, optional
           Depth of the network.

       drop_values : float, optional
           Dropout value to be fixed. 

       spatial_dropout : bool, optional
           Use spatial dropout instead of the `normal` dropout.

       batch_norm : bool, optional
           Make batch normalization.
    
       k_init : string, optional
           Kernel initialization for convolutional layers.

       z_down : int, optional
           Downsampling used in z dimension. Set it to 1 if the dataset is not 
           isotropic.
        
       loss_type : str, optional
           Loss type to use, three type available: ``bce`` (Binary Cross Entropy) 
           , ``w_bce`` (Weighted BCE, based on weigth maps) and ``w_bce_dice`` 
           (Weighted loss: ``weight1*BCE + weight2*Dice``). 

       optimizer : str, optional
           Optimizer used to minimize the loss function. Posible options: ``sgd``
           or ``adam``.

       lr : float, optional
           Learning rate value.

       n_classes: int, optional                                                 
           Number of classes.    

       Returns
       -------
       model : Keras model
           Model containing the U-Net.

    
       Calling this function with its default parameters returns the following
       network:


       Example
       -------

       Calling this function with its default parameters returns the following
       network:

       .. image:: img/unet_3d.png
           :width: 100%
           :align: center

       Image created with `PlotNeuralNet <https://github.com/HarisIqbal88/PlotNeuralNet>`_.

       That networks incorporates in skip connecions Attention Gates (AG), which
       can be seen as follows:

       .. image:: img/attention_gate.png
           :width: 100%
           :align: center

       Image extracted from `Attention U-Net: Learning Where to Look for the Pancreas <https://arxiv.org/abs/1804.03999>`_.
    """

    if len(feature_maps) != depth+1:                                            
        raise ValueError("feature_maps dimension must be equal depth+1")        
    if len(drop_values) != depth+1:                                             
        raise ValueError("'drop_values' dimension must be equal depth+1")       

    #dinamic_dim = (None,)*(len(image_shape)-1) + (image_shape[-1],)
    #inputs = Input(dinamic_dim)
    x = Input(image_shape)
    inputs = x
        
    if loss_type == "w_bce":
        weights = Input(image_shape)

    # List used to access layers easily to make the skip connections of the U-Net
    l=[]

    # ENCODER
    for i in range(depth):
        x = Conv3D(feature_maps[i], (3, 3, 3), activation=None,
                   kernel_initializer=k_init, padding='same') (x)
        x = BatchNormalization() (x) if batch_norm else x 
        x = Activation(activation) (x)

        if spatial_dropout and drop_values[i] > 0:
            x = SpatialDropout3D(drop_values[i]) (x)
        elif drop_values[i] > 0 and not spatial_dropout:
            x = Dropout(drop_values[i]) (x)

        x = Conv3D(feature_maps[i], (3, 3, 3), activation=None,
                   kernel_initializer=k_init, padding='same') (x)
        x = BatchNormalization() (x) if batch_norm else x 
        x = Activation(activation) (x)

        l.append(x)
    
        x = MaxPooling3D((2, 2, z_down))(x)

    # BOTTLENECK
    x = Conv3D(feature_maps[depth], (3, 3, 3), activation=None,
               kernel_initializer=k_init, padding='same')(x)
    x = BatchNormalization() (x) if batch_norm else x
    x = Activation(activation) (x)

    if spatial_dropout and drop_values[depth] > 0:
        x = SpatialDropout3D(drop_values[depth]) (x)
    elif drop_values[depth] > 0 and not spatial_dropout:
        x = Dropout(drop_values[depth]) (x)

    x = Conv3D(feature_maps[depth], (3, 3, 3), activation=None,
               kernel_initializer=k_init, padding='same') (x)
    x = BatchNormalization() (x) if batch_norm else x
    x = Activation(activation) (x)

    # DECODER
    for i in range(depth-1, -1, -1):
        x = Conv3DTranspose(feature_maps[i], (2, 2, 2),                            
                            strides=(2, 2, z_down), padding='same') (x)                 
        attn = AttentionBlock(x, l[i], feature_maps[i], batch_norm)               
        x = concatenate([x, attn])  
        x = Conv3D(feature_maps[i], (3, 3, 3), activation=None,
                   kernel_initializer=k_init, padding='same') (x)
        x = BatchNormalization() (x) if batch_norm else x
        x = Activation(activation) (x)

        if spatial_dropout and drop_values[i] > 0:
            x = SpatialDropout3D(drop_values[i]) (x)
        elif drop_values[i] > 0 and not spatial_dropout:
            x = Dropout(drop_values[i]) (x)

        x = Conv3D(feature_maps[i], (3, 3, 3), activation=None,
                   kernel_initializer=k_init, padding='same') (x)
        x = BatchNormalization() (x) if batch_norm else x
        x = Activation(activation) (x)

    outputs = Conv3D(n_classes, (1, 1, 1), activation='sigmoid') (x)
    
    # Loss type 
    if loss_type == "w_bce":
        model = Model(inputs=[inputs, weights], outputs=[outputs]) 
    else:
        model = Model(inputs=[inputs], outputs=[outputs])
    
    # Select the optimizer
    if optimizer == "sgd":
        opt = tf.keras.optimizers.SGD(
            lr=lr, momentum=0.99, decay=0.0, nesterov=False)
    elif optimizer == "adam":
        opt = tf.keras.optimizers.Adam(
            lr=lr, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, 
            amsgrad=False)
    else:
        raise ValueError("Error: optimizer value must be 'sgd' or 'adam'")
        
    # Compile the model
    if loss_type == "bce":
        if n_classes > 1:                                                       
            model.compile(optimizer=opt, loss='categorical_crossentropy',       
                          metrics=[jaccard_index_softmax])                      
        else:                                                                   
            model.compile(optimizer=opt, loss='binary_crossentropy',            
                          metrics=[jaccard_index])        
    elif loss_type == "w_bce":
        model.compile(optimizer=opt, loss=binary_crossentropy_weighted(weights), 
                      metrics=[jaccard_index])
    elif loss_type == "w_bce_dice":
        model.compile(optimizer=opt, 
                      loss=weighted_bce_dice_loss(w_dice=0.66, w_bce=0.33),
                      metrics=[jaccard_index])
    else:
        raise ValueError("'loss_type' must be 'bce', 'w_bce' or 'w_bce_dice'")

    return model


                                                                                
def AttentionBlock(x, shortcut, filters, batch_norm):                           
    """Attention block.                                                         
                                                                                
       Extracted from `Kaggle <https://www.kaggle.com/c/tgs-salt-identification-challenge/discussion/64367>`_.
                                                                                
       Parameters                                                               
       ----------                                                               
       x : Keras layer                                                          
           Input layer.                                                         
                                                                                
       shortcut : Keras layer                                                   
           Input skip connection.                                               
                                                                                
       filters : int                                                            
           Feature maps to define on the Conv layers.                           
                                                                                
       batch_norm : bool, optional                                              
           To use batch normalization.                                          
                                                                                
       Returns                                                                  
       -------                                                                  
       out : Keras layer                                                        
           Last layer of the Attention block.                                   
    """                                                                         
                                                                                
    g1 = Conv3D(filters, kernel_size = 1)(shortcut)                             
    g1 = BatchNormalization() (g1) if batch_norm else g1                        
    x1 = Conv3D(filters, kernel_size = 1)(x)                                    
    x1 = BatchNormalization() (x1) if batch_norm else x1                        
                                                                                
    g1_x1 = Add()([g1,x1])                                                      
    psi = Activation('relu')(g1_x1)                                             
    psi = Conv3D(1, kernel_size = 1)(psi)                                       
    psi = BatchNormalization() (psi) if batch_norm else psi                     
    psi = Activation('sigmoid')(psi)                                           
    x = Multiply()([x,psi])                                                     
    return x              
