import numpy as np
import os
import math
from tqdm import tqdm
from tensorflow.keras.preprocessing.image import ImageDataGenerator as kerasDA
from util import do_save_wm, make_weight_map
from data_2D_manipulation import random_crop

def keras_da_generator(X_train=None, Y_train=None, X_val=None, Y_val=None, 
                       ld_img_from_disk=False, data_paths=None, target_size=None, 
                       c_target_size=None, batch_size_value=1, val=True, 
                       save_examples=True, out_dir='aug', hflip=False,
                       vflip=False, seedValue=42, rotation_range=180, 
                       fill_mode='reflect', preproc_function=False, 
                       featurewise_center=False, brightness_range=None, 
                       channel_shift_range=0.0, shuffle_train=True,
                       shuffle_val=False, featurewise_std_normalization=False, 
                       zoom=0.0, w_shift_r=0.0, h_shift_r=0.0, shear_range=0,
                       random_crops_in_DA=False, crop_length=0,
                       weights_on_data=False, weights_path=None):             
                                                                                
    """Makes data augmentation of the given input data based on Keras 
       ``ImageDataGenerator`` class.                         
                                                                                
       Parameters
       ----------                                                                    
       X_train : 4D Numpy array, optional
           Train data. If provided ``data_paths`` arg value will be avoided.
           E.g. ``(num_of_images, x, y, channels)``.

       Y_train : 4D Numpy array, optional
           Train mask data. E.g. ``(num_of_images, x, y, channels)``.

       X_val : 4D Numpy array, optional
           Validation data. E.g. ``(num_of_images, x, y, channels)``.

       Y_val : 4D Numpy array, optional
           Validation mask data. E.g. ``(num_of_images, x, y, channels)``.

       ld_img_from_disk : bool, optional
           To make the generator with images loaded form disk instead of use
           ``X_train``, ``Y_train``, ``X_val`` and ``Y_val``.

       data_paths : list of str, optional
           List of paths where the data is stored. Use this instead of ``X_train``
           and ``Y_train`` args to do not charge the data in memory and make a
           generator over the paths instead. The path order is this: 1) train
           images path 2) train masks path 3) validation images path 4) validation
           masks path 5) test images path 6) test masks path 7) complete images
           path (this last useful to make the smoothing post processing, as it
           requires the reconstructed data) 8) complete mask path. To provide the
           validation data val must be set to ``True``. If no validation data
           provided the order of the paths is the same avoiding validation ones.

       target_size : 2D int tuple, optional
           Size where the images will be resized if data_paths is defined. 

       c_target_size : 2D int tuple, optional
           Size where complete images will be resized if data_paths is defined. 

       batch_size_value : int, optional
           Batch size value.

       val : bool, optional
           If ``True`` validation data generator will be returned.

       save_examples : bool, optional
           If ``True`` 5 examples of DA are stored.

       out_dir : string, optional
           Save directory suffix.                  

       hflip : bool, optional
           If ``True`` horizontal flips are made.          

       vflip : bool, optional
           If ``True`` vertical flip are made.             

       seedValue : int, optional
           Seed value.                              

       rotation_range : int, optional
           Range of rotation degrees.

       fill_mode : str, optional
           ``ImageDataGenerator`` of Keras fill mode values.

       preproc_function : function, optional
           Preprocessing function to apply.

       featurewise_center : bool, optional
           Set input mean to 0 over the dataset, feature-wise.

       brightness_range : 2D float tuple, optional
           Range for picking a brightness shift value from.

       channel_shift_range : float, optional
           Range for random channel shifts.

       shuffle_train : bool, optional
           Randomize the training data on each epoch.

       shuffle_val : bool, optional
           Randomize the validation data on each epoch.

       featurewise_std_normalization : bool, optional
           Divide inputs by std of the dataset, feature-wise.                                       

       zoom : float, optional
           Range for random zoom.

       w_shift_r : float, optional
           Width shift range.

       h_shift_r : float, optional
           Height shift range.

       shear_range : float, optional
           Range to apply shearing transformations. 

       random_crops_in_DA : bool, optional
           Decide to make random crops in DA (after transformations).                                           

       crop_length : int, optional
           Length of the random crop before DA. 

       weights_on_data : bool, optional
           To make a weights generator for the weighted loss. 

       Returns
       -------                                                                 
       train_generator : Iterator
           Train data iterator.                                                           

       val_generator : Iterator, optional
           Validation data iterator.

       X_test_aug : Iterator, optional
           Test data iterator.

       Y_test_aug : Iterator, optional
           Test masks iterator.

       W_test_aug : Iterator, optional
           Test weight maps iterator.

       X_complete_aug : Iterator, optional
           Original data iterator useful to make the smoothing post processing,
           as it requires the reconstructed data.
       
       Y_complete_aug : Iterator, optional
           Original mask iterator.

       W_complete_aug : Iterator, optional
           Original weight maps iterator.

       n_train_samples : int, optional
           Number of training samples.  

       n_val_samples : int, optional
           Number of validation samples.

       n_test_samples : int, optional
           Number of test samples.

       
       Examples
       --------
       ::
        
           # EXAMPLE 1
           # Create a train and val data generators making random rotations between
           # 0 and 180 degrees and vertical/horizontal flips. 

           X_train = np.zeros((1776, 256, 256, 1))
           Y_train = np.zeros((1776, 256, 256, 1))
           X_val = np.zeros((204, 256, 256, 1))
           Y_val = np.zeros((204, 256, 256, 1))

           train_generator, val_generator = keras_da_generator(
               X_train=X_train, Y_train=Y_train, X_val=X_val, Y_val=Y_val, 
               batch_size_value=6, save_examples=True, out_dir='da_out',
               shuffle_train=True, shuffle_val=False, rotation_range=180,
               vflip=True, hflip=True)


           # EXAMPLE 2
           # Generate random crops on DA-time. To allow that notice that the
           # data in this case is bigger in width and height than example 1, to
           # allow a (256, 256) random crop extraction
           X_train = np.zeros((148, 768, 1024, 1))
           Y_train = np.zeros((148, 768, 1024, 1))
           X_val = np.zeros((17, 768, 1024, 1))
           Y_val = np.zeros((17, 768, 1024, 1))
 
           train_generator, 
           val_generator = keras_da_generator(
               X_train=X_train, Y_train=Y_train, X_val=X_val, Y_val=Y_val, 
               batch_size_value=6, save_examples=True, out_dir='da_out',
               shuffle_train=True, shuffle_val=False, rotation_range=180,
               random_crops_in_DA=True, crop_length=256, vflip=True, hflip=True)
    """                                                                         

    if X_train is None and not ld_img_from_disk:
        raise ValueError("One between X_train or ld_img_from_disk must be selected")

    if ld_img_from_disk and (target_size is None or c_target_size is None):
        raise ValueError("target_size and c_target_size must be specified when "
                         "ld_img_from_disk is selected")

    if ld_img_from_disk and len(data_paths) != 8: 
        raise ValueError(
            "data_paths must contain the following paths: 1) train path ; 2) "
            "train masks path ; 3) validation path ; 4) validation masks path ; "
            "5) test path ; 6) test masks path ; 7) complete images path 8) "
            "complete image mask path")

    if weights_on_data and weights_path is None:
       raise ValueError(
           "'weights_path' must be provided when weights is selected")

    data_gen_args1 = dict(
        horizontal_flip=hflip, vertical_flip=vflip, fill_mode=fill_mode, 
        rotation_range=rotation_range, featurewise_center=featurewise_center,            
        featurewise_std_normalization=featurewise_std_normalization, 
        zoom_range=zoom, width_shift_range=w_shift_r,
        height_shift_range=h_shift_r, shear_range=shear_range,
        channel_shift_range=channel_shift_range,
        brightness_range=brightness_range, rescale=1./255)
    data_gen_args2 = dict(
        horizontal_flip=hflip, vertical_flip=vflip, fill_mode=fill_mode, 
        rotation_range=rotation_range, zoom_range=zoom, 
        width_shift_range=w_shift_r, height_shift_range=h_shift_r, 
        shear_range=shear_range, rescale=1./255)                              

    # Obtaining the path where the data is stored                                                                                 
    if ld_img_from_disk == True:
        train_path = data_paths[0]
        train_mask_path = data_paths[1]
        val_path = data_paths[2]
        val_mask_path = data_paths[3]
        test_path = data_paths[4]
        test_mask_path = data_paths[5]
        complete_path = data_paths[6]
        complete_mask_path = data_paths[7]
                            
    # Generators
    X_datagen_train = kerasDA(**data_gen_args1)
    Y_datagen_train = kerasDA(**data_gen_args2)                                 
    X_datagen_test = kerasDA(rescale=1./255)
    Y_datagen_test = kerasDA(rescale=1./255)                                 
    if ld_img_from_disk == True:
        complete_datagen = kerasDA(rescale=1./255)
        complete_mask_datagen = kerasDA(rescale=1./255)                                 
    if val == True:
        X_datagen_val = kerasDA(rescale=1./255)
        Y_datagen_val = kerasDA(rescale=1./255)                                                   
    if weights_on_data == True:
        w_datagen = kerasDA(**data_gen_args2)

    # Save a few examples 
    if save_examples == True:
        print("Saving some samples of the train generator . . .")        
        os.makedirs(out_dir, exist_ok=True)
        
        if random_crops_in_DA:
            print("WARNING: aug samples generated will not have the shape "
                  "specified by crop_length, as it is not implemented")

        if not ld_img_from_disk:
            i = 0
            for batch in X_datagen_train.flow(
                X_train, save_to_dir=out_dir, batch_size=batch_size_value,
                shuffle=True, seed=seedValue, save_prefix='x', save_format='png'):
                i = i + 1
                if i > 2:
                    break
            i = 0
            for batch in Y_datagen_train.flow(
                Y_train, save_to_dir=out_dir, batch_size=batch_size_value,
                shuffle=True, seed=seedValue, save_prefix='y', save_format='png'):
                i = i + 1
                if i > 2:
                    break
        else:
            i = 0
            for batch in X_datagen_train.flow_from_directory(
                train_path, save_to_dir=out_dir, target_size=target_size,
                batch_size=batch_size_value, shuffle=True, seed=seedValue,
                save_prefix='x', save_format='png'):
                i = i + 1
                if i > 2:
                    break
            i = 0
            for batch in Y_datagen_train.flow_from_directory(
                train_mask_path, save_to_dir=out_dir, target_size=target_size,
                batch_size=batch_size_value, shuffle=True, seed=seedValue,
                save_prefix='y', save_format='png'):
                i = i + 1
                if i > 2:
                    break
  
    # Create the generators with the provided data
    if not ld_img_from_disk:
        X_train_aug = X_datagen_train.flow(X_train, batch_size=batch_size_value,       
                                           shuffle=shuffle_train, seed=seedValue)
        Y_train_aug = Y_datagen_train.flow(Y_train, batch_size=batch_size_value,       
                                           shuffle=shuffle_train, seed=seedValue)

    # Create the generator loading images directly from disk
    else:
        print("Train data loaded from directory: {}".format(train_path))
        X_train_aug = X_datagen_train.flow_from_directory(
            train_path, target_size=target_size, class_mode=None, 
            color_mode="grayscale", batch_size=batch_size_value,
            shuffle=shuffle_train, seed=seedValue)
        Y_train_aug = Y_datagen_train.flow_from_directory(
            train_mask_path, target_size=target_size, class_mode=None,
            color_mode="grayscale", batch_size=batch_size_value,
            shuffle=shuffle_train, seed=seedValue)
        n_train_samples = X_train_aug.n 
        
        print("Test data loaded from directory: {}".format(test_path))
        X_test_aug = X_datagen_test.flow_from_directory(
            test_path, target_size=target_size, class_mode=None, 
            color_mode="grayscale", batch_size=batch_size_value, shuffle=False, 
            seed=seedValue)
        Y_test_aug = Y_datagen_test.flow_from_directory(
            test_mask_path, target_size=target_size, class_mode=None,
            color_mode="grayscale", batch_size=batch_size_value, shuffle=False, 
            seed=seedValue)

        n_test_samples = X_test_aug.n

        print("Complete data loaded from directory: {}".format(complete_path))
        X_complete_aug = complete_datagen.flow_from_directory(
            complete_path, target_size=c_target_size, class_mode=None,
            color_mode="grayscale", batch_size=batch_size_value, shuffle=False)
        Y_complete_aug = complete_datagen.flow_from_directory(
            complete_mask_path, target_size=c_target_size, class_mode=None,
            color_mode="grayscale", batch_size=batch_size_value, shuffle=False)

    # Create the validation generator
    if not ld_img_from_disk:
        if val == True:
            X_val_aug = X_datagen_val.flow(X_val, batch_size=batch_size_value,
                                           shuffle=shuffle_val, seed=seedValue)
            Y_val_aug = Y_datagen_val.flow(Y_val, batch_size=batch_size_value,
                                           shuffle=shuffle_val, seed=seedValue)
    else:
        print("Validation data loaded from directory: {}".format(val_path))
        X_val_aug = X_datagen_val.flow_from_directory(
            val_path, target_size=target_size, batch_size=batch_size_value,
            class_mode=None, color_mode="grayscale", shuffle=shuffle_val, 
            seed=seedValue)
        Y_val_aug = Y_datagen_val.flow_from_directory(
            val_mask_path, target_size=target_size, batch_size=batch_size_value,
            class_mode=None, color_mode="grayscale", shuffle=shuffle_val, 
            seed=seedValue)
        n_val_samples = X_val_aug.n

    # Create the weight map generator
    if weights_on_data == True:
        train_w_path = os.path.join(weights_path, 'train')
        val_w_path = os.path.join(weights_path, 'val')
        test_w_path = os.path.join(weights_path, 'test')
        if ld_img_from_disk == True:
            complete_w_path = os.path.join(weights_path, 'complete')            
        
        # Create generator from disk
        if ld_img_from_disk == True:
   
            # Create train maks generator without augmentation
            print("Create train mask generator in case we need it to create the"
                  " map weigths" )
            Y_train_no_aug = kerasDA().flow_from_directory(
                train_mask_path, target_size=target_size, class_mode=None,
                color_mode="grayscale", batch_size=batch_size_value, 
                shuffle=False)

            prepare_weight_maps(
                train_w_path, val_w_path, test_w_path, c_w_path=complete_w_path, 
                ld_img_from_disk=True, Y_train_aug=Y_train_no_aug, 
                Y_val_aug=Y_val_aug, Y_test_aug=Y_test_aug, 
                Y_cmp_aug=Y_complete_aug, batch_size_value=batch_size_value)

        # Create generator from data
        else:
            prepare_weight_maps(
                train_w_path, val_w_path, test_w_path, Y_train=Y_train, 
                Y_val=Y_val, Y_test=Y_test, batch_size_value=batch_size_value)

        # Retrieve weight-maps
        t_filelist = sorted(next(os.walk(train_w_path))[2])
        v_filelist = sorted(next(os.walk(val_w_path))[2])
        te_filelist = sorted(next(os.walk(test_w_path))[2])
        if ld_img_from_disk == True:
            c_filelist = sorted(next(os.walk(complete_w_path))[2])
        
        # Loads all weight-map images in a list
        t_weights = [np.load(os.path.join(train_w_path, fname)) for fname in t_filelist]
        t_weights = np.array(t_weights, dtype=np.float32)
        t_weights = t_weights.reshape((len(t_weights),target_size[0],
                                       target_size[1],1))
        v_weights = [np.load(os.path.join(val_w_path, fname)) for fname in v_filelist]
        v_weights = np.array(v_weights, dtype=np.float32)
        v_weights = v_weights.reshape((len(v_weights),target_size[0],
                                       target_size[1],1))
        te_weights = [np.load(os.path.join(test_w_path, fname)) for fname in te_filelist]
        te_weights = np.array(te_weights, dtype=np.float32)                       
        te_weights = te_weights.reshape((len(te_weights),target_size[0],           
                                       target_size[1],1))
        if ld_img_from_disk == True:
            c_weights = [np.load(os.path.join(complete_w_path, fname)) for fname in c_filelist]
            c_weights = np.array(c_weights, dtype=np.float32)                     
            c_weights = c_weights.reshape((len(c_weights),c_target_size[0],        
                                          c_target_size[1],1))

        # Create the weight generator 
        W_train_aug = w_datagen.flow(t_weights, batch_size=batch_size_value,
                                     shuffle=shuffle_train, seed=seedValue)
        W_val_aug = w_datagen.flow(v_weights, batch_size=batch_size_value,
                                   shuffle=shuffle_val, seed=seedValue)
        W_test_aug = w_datagen.flow(te_weights, batch_size=batch_size_value,
                                    shuffle=False)
        if ld_img_from_disk == True:
            W_cmp_aug = w_datagen.flow(c_weights, batch_size=batch_size_value,    
                                       shuffle=False)
    else:
        W_train_aug = W_val_aug = W_test_aug = None

        if ld_img_from_disk == True:
            W_cmp_aug = None
        

    # Combine generators into one which yields image, masks and weights (if used)
    train_generator = combine_generators(X_train_aug, Y_train_aug, W_train_aug)                 
    if val == True:
        val_generator = combine_generators(X_val_aug, Y_val_aug, W_val_aug)
    
    # Make random crops over the generators                                                               
    if random_crops_in_DA == True:                                                
        train_generator = crop_generator(train_generator, crop_length, 
                                         weights_on_data=weights_on_data)
                          
        if val == True:
            val_generator = crop_generator(val_generator, crop_length, val=True,
                                           weights_on_data=weights_on_data)
 
    if ld_img_from_disk == True:
        return train_generator, val_generator, X_test_aug, Y_test_aug, \
               W_test_aug, X_complete_aug, Y_complete_aug, W_cmp_aug, \
               n_train_samples, n_val_samples, n_test_samples
    else:
        if val == True:
            return train_generator, val_generator
        else:
            return train_generator


def keras_gen_samples(num_samples, X_data=None, Y_data=None, 
                      ld_img_from_disk=False, data_paths=None, target_size=None, 
                      batch_size_value=1, shuffle_data=True, hflip=True, 
                      vflip=True, seedValue=42, rotation_range=180, 
                      fill_mode='reflect', preproc_function=None,
                      featurewise_center=False, brightness_range=None,
                      channel_shift_range=0.0, featurewise_std_normalization=False,
                      zoom=0.0, w_shift_r=0.0, h_shift_r=0.0, shear_range=0):
    """Generates samples based on keras da generator.
    
       Parameters
       ----------
       num_samples : int
           Number of samples to create.

       X_data : 4D Numpy array, optional
           Data used to generate samples. E.g. ``(num_of_images, x, y, channels)``.

       Y_data : 4D Numpy array, optional
           Mask used to generate samples. E.g. ``(num_of_images, x, y, channels)``.

       ld_img_from_disk : bool, optional
           To advise the function to load images from disk instead of use 
           ``X_data`` and ``Y_data``.

       data_paths : list of str
           Path were the data and mask are stored to generate the new samples.

       target_size : 2D int tuple, optional
           Shape of the images to load from disk.

       batch_size_value : int, optional
           Batch size value.

       shuffle_data : bool, optional
           Shuffle the data while generating new samples. 

       hflip : bool, optional
           If ``True`` horizontal flips are made.

       vflip : bool, optional
           If ``True`` vertical flip are made.

       seedValue : int, optional
           Seed value.

       rotation_range : int, optional
           Range of rotation degrees.

       fill_mode : str, optional
           ``ImageDataGenerator`` of Keras fill mode values.

       preproc_function : function, optional                                    
           Preprocessing function to apply.                                     
                                                                                
       featurewise_center : bool, optional                                      
           Set input mean to 0 over the dataset, feature-wise.                  
                                                                                
       brightness_range : 2D float tuple, optional                              
           Range for picking a brightness shift value from.                     
                                                                                
       channel_shift_range : float, optional                                    
           Range for random channel shifts.                                     
                                                                                
       featurewise_std_normalization : bool, optional                           
           Divide inputs by std of the dataset, feature-wise.                                       
                                                                                
       zoom : float, optional                                                   
           Range for random zoom.                                               
                                                                                
       w_shift_r : float, optional                                              
           Width shift range.                                                   
                                                                                
       h_shift_r : float, optional                                              
           Height shift range.                                                  
                                                                                
       shear_range : float, optional                                            
           Range to apply shearing transformations.     

       Returns
       -------
       x_samples : 4D Numpy array
           Data new samples. E.g. ``(num_samples, x, y, channels)``.

       y_samples : 4D numpy array
           Mask new samples. E.g. ``(num_samples, x, y, channels)``.
    """

    if num_samples == 0:
        return None

    if X_data is None and not ld_img_from_disk:
        raise ValueError("One between X_data or ld_img_from_disk must be selected")

    if ld_img_from_disk == True and target_size is None:
        raise ValueError("target_size must be specified when ld_img_from_disk "
                         "is selected")

    if ld_img_from_disk == True and len(data_paths) != 2:
        raise ValueError("data_paths must contain the following paths: 1) data "
                         "path ; 2) data masks path")

    data_gen_args1 = dict(
        horizontal_flip=hflip, vertical_flip=vflip, fill_mode=fill_mode, 
        rotation_range=rotation_range, preprocessing_function=preproc_function,
        featurewise_center=featurewise_center, 
        featurewise_std_normalization=featurewise_std_normalization,
        zoom_range=zoom, width_shift_range=w_shift_r, 
        height_shift_range=h_shift_r, shear_range=shear_range, 
        channel_shift_range=channel_shift_range, 
        brightness_range=brightness_range, rescale=1./255)
    data_gen_args2 = dict(
        horizontal_flip=hflip, vertical_flip=vflip, fill_mode=fill_mode, 
        rotation_range=rotation_range, preprocessing_function=preproc_function,
        zoom_range=zoom, width_shift_range=w_shift_r, 
        height_shift_range=h_shift_r, shear_range=shear_range, rescale=1./255)

    X_datagen = kerasDA(**data_gen_args1)
    Y_datagen = kerasDA(**data_gen_args2)

    # Use X_data and Y_data to generate the samples 
    if not ld_img_from_disk:
        x_samples = np.zeros((num_samples,) + X_data.shape[1:], dtype=np.float32)
        y_samples = np.zeros((num_samples,) + Y_data.shape[1:], dtype=np.float32)

        n_batches = int(num_samples / batch_size_value) \
                    + (num_samples % batch_size_value > 0)

        print("Generating new data samples . . .")
        i = 0                                                                   
        c = 0                                                                   
        for batch in X_datagen.flow(X_data, batch_size=batch_size_value,        
                                    shuffle=shuffle_data, seed=seedValue):      
            for j in range(0, batch.shape[0]):                                  
                x_samples[c] = batch[j]                                         
                c += 1                                                          
            i = i + 1                                                           
            if i >= n_batches:                                                  
                break                                                           
        i = 0                                                                   
        c = 0                                                                   
        for batch in Y_datagen.flow(Y_data, batch_size=batch_size_value,        
                                    shuffle=shuffle_data, seed=seedValue):      
            for j in range(0, batch.shape[0]):                                  
                y_samples[c] = batch[j]                                         
                c += 1                                                          
            i = i + 1                                                           
            if i >= n_batches:                                                  
                break

    # Use data_paths to load images from disk to make more samples
    else:
        x_samples = np.zeros((num_samples, X_data.shape[1], X_data.shape[2],
                            X_data.shape[3]), dtype=np.float32)
        y_samples = np.zeros((num_samples, Y_data.shape[1], Y_data.shape[2],
                            Y_data.shape[3]), dtype=np.float32)

        n_batches = int(num_samples / batch_size_value) \
                    + (num_samples % batch_size_value > 0)

        print("Generating new data samples . . .")
        i = 0
        c = 0
        for batch in X_datagen.flow_from_directory(
            data_paths[0], target_size=target_size, batch_size=batch_size_value,    
            shuffle=shuffle_data, seed=seedValue):
            for j in range(0, batch_size_value):
                x_samples[c] = batch[j]
                c += 1
            i = i + 1
            if i >= n_batches:
                break
        i = 0
        c = 0
        for batch in Y_datagen.flow_from_directory(
            data_paths[1], target_size=target_size, batch_size=batch_size_value,
            shuffle=shuffle_data, seed=seedValue):
            for j in range(0, batch_size_value):
                y_samples[c] = batch[j]
                c += 1
            i = i + 1
            if i >= n_batches:
                break

    return x_samples, y_samples


def prepare_weight_maps(train_w_path, val_w_path, test_w_path, c_w_path=None,
                        Y_train=None, Y_val=None, Y_test=None, 
                        ld_img_from_disk=False, Y_train_aug=None, Y_val_aug=None, 
                        Y_test_aug=None, Y_cmp_aug=None, batch_size_value=1):
    """Prepare weight maps saving them into a given path. When the paths exist
       it suposses that weight maps are already generated. Uses 
       :meth:`util.make_weight_map` and :meth:`util.do_save_wm`.

       Parameters
       ----------
       train_w_path : str
           Path where train images should be stored.

       val_w_path : str
           Path where validation images should be stored.

       test_w_path : str
           Path where test images should be stored.

       c_w_path : str
           Path where complete images should be stored. Ignored if 
           ``ld_img_from_disk`` is ``False``.

       Y_train : 4D Numpy array, optional
           Train mask data used to generate weight maps. 
           E.g.``(num_of_images, x, y, channels)``.

       Y_val : Numpy array, optional
           Validation mask data used to generate weight maps. 
           E.g. ``(num_of_images, x, y, channels)``.

       Y_test : Numpy array, optional
           Test mask data used to generate weight maps.
           E.g. ``(num_of_images, x, y, channels)``.

       ld_img_from_disk : bool, optional
           To advise the function to load images from disk instead of use 
           ``Y_train_aug``, ``Y_val_aug`` and ``Y_test_aug``.

       Y_train_aug : Keras ImageDataGenerator, optional
           Train mask generator used to produce weight maps.

       Y_val_aug : Keras ImageDataGenerator, optional
           Validation mask generator used to produce weight maps.

       Y_test_aug : Keras ImageDataGenerator, optional
           Test mask generator used to produce weight maps.

       Y_cmp_aug : Keras ImageDataGenerator, optional
           Complete image mask generator used to produce weight maps.

       batch_size_value : int, optional
           Batch size value. 
    """

    if Y_train is None and not ld_img_from_disk:
        raise ValueError("Y_train or ld_img_from_disk must be selected.")
    
    if ld_img_from_disk == True and (Y_train_aug is None or Y_val_aug is None\
        or Y_test_aug is None):
        raise ValueError("When ld_img_from_disk is selected Y_train_aug, "
                         "Y_val_aug and Y_test_aug must be provided")
    if c_w_path is not None and Y_cmp_aug is None:
        raise ValueError("'Y_cmp_aug' must be provided when c_w_path is provided")

    if ld_img_from_disk:
        if not os.path.exists(train_w_path):
            print("Constructing train weight maps with Y_train . . .")
            os.makedirs(train_w_path)
            do_save_wm(Y_train, train_w_path)

        if not os.path.exists(val_w_path):
            print("Constructing validation weight maps with Y_val . . .")
            os.makedirs(val_w_path)
            do_save_wm(Y_val, val_w_path)

        if not os.path.exists(test_w_path):
            print("Constructing test weight maps with Y_test . . .")
            os.makedirs(test_w_path)
            do_save_wm(Y_test, test_w_path)
    else:
        if not os.path.exists(train_w_path):
            print("Constructing train weight maps from disk . . .")
            os.makedirs(train_w_path)

            iterations = math.ceil(Y_train_aug.n/batch_size_value)
            
            # Count number of digits in n. This is important for the number
            # of leading zeros in the name of the maps
            d = len(str(Y_train_aug.n))

            cont = 0
            for i in tqdm(range(iterations)):
                batch = next(Y_train_aug)

                for j in range(0, batch.shape[0]):
                    if cont >= Y_train_aug.n:
                       break

                    img_map = make_weight_map(batch[j].copy())

                    # Resize correctly the maps so that it can be used in the model
                    rows, cols = img_map.shape
                    img_map = img_map.reshape((rows, cols, 1))

                    # Saving files as .npy files
                    np.save(os.path.join(
                                train_w_path, "w_" + str(cont).zfill(d)), img_map)

                    cont += 1

            Y_train_aug.reset()
        else:
            print("Train weight maps are already prepared!")
            
        if not os.path.exists(val_w_path):
            print("Constructing validation weight maps from disk . . .")
            os.makedirs(val_w_path)

            iterations = math.ceil(Y_val_aug.n/batch_size_value)

            # Count number of digits in n. This is important for the number
            # of leading zeros in the name of the maps
            d = len(str(Y_val_aug.n))

            cont = 0
            for i in tqdm(range(iterations)):
                batch = next(Y_val_aug)

                for j in range(0, batch.shape[0]):
                    if cont >= Y_val_aug.n:
                        break

                    img_map = make_weight_map(batch[j].copy())

                    # Resize correctly the maps so that it can be used in the model
                    rows, cols = img_map.shape
                    img_map = img_map.reshape((rows, cols, 1))

                    # Saving files as .npy files
                    np.save(os.path.join(
                                val_w_path, "w_" + str(cont).zfill(d)), img_map)

                    cont += 1

            Y_val_aug.reset()
        else:                                                                   
            print("Validation weight maps are already prepared!")

        if not os.path.exists(test_w_path):                                      
            print("Constructing test weight maps from disk . . .")        
            os.makedirs(test_w_path)                                             
                                                                                
            iterations = math.ceil(Y_test_aug.n/batch_size_value)                
                                                                                
            # Count number of digits in n. This is important for the number     
            # of leading zeros in the name of the maps                          
            d = len(str(Y_test_aug.n))                                           
                                                                                
            cont = 0                                                            
            for i in tqdm(range(iterations)):                                 
                batch = next(Y_test_aug)                                         
                for j in range(0, batch.shape[0]):                              
                    if cont >= Y_test_aug.n:                                     
                        break                                                   
                                                                                
                    img_map = make_weight_map(batch[j].copy())                  
                                                                                
                    # Resize correctly the maps so that it can be used in the model
                    rows, cols = img_map.shape                                  
                    img_map = img_map.reshape((rows, cols, 1))                  
                                                                                
                    # Saving files as .npy files                                
                    np.save(os.path.join(
                                test_w_path, "w_" + str(cont).zfill(d)), img_map)                     
                                                                                
                    cont += 1                                                   
                                                                                
            Y_test_aug.reset()
        else:                                                                   
            print("Test weight maps are already prepared!")

        if not os.path.exists(c_w_path):                                     
            print("Constructing complete image weight maps from disk . . .")              
            os.makedirs(c_w_path)                                            
                                                                                
            iterations = math.ceil(Y_cmp_aug.n/batch_size_value)               
                                                                                
            # Count number of digits in n. This is important for the number     
            # of leading zeros in the name of the maps                          
            d = len(str(Y_cmp_aug.n))                                          
                                                                                
            cont = 0                                                            
            for i in tqdm(range(iterations)):                                 
                batch = next(Y_cmp_aug)                                        
                for j in range(0, batch.shape[0]):                              
                    if cont >= Y_cmp_aug.n:                                    
                        break                                                   
                    
                    print("Making the map")                                                            
                    img_map = make_weight_map(batch[j].copy())                  
                    print("Map created")
                                                                                
                    # Resize correctly the maps so that it can be used in the model
                    rows, cols = img_map.shape                                  
                    img_map = img_map.reshape((rows, cols, 1))                  
                                                                                
                    # Saving files as .npy files                                
                    np.save(os.path.join(
                                c_w_path, "w_" + str(cont).zfill(d)), img_map)
                                                                                
                    cont += 1                                                   
                                                                                
            Y_cmp_aug.reset()
        else:                                                                   
            print("Complete image weight maps are already prepared!")

    print("Weight maps are prepared!")
    

def combine_generators(X_aug, Y_aug, W_aug=None):
    """Combine generators into one.
    
       Parameters
       ----------
       X_aug : Keras ImageDataGenerator
           Image generator.

       Y_aug : Keras ImageDataGenerator
           Mask generator.

       W_aug : Keras ImageDataGenerator, optional
           Weight map generator.
    
       Yields
       ------
       out : 2 element list 
           One batch of the generator.                                          
    """

    if W_aug is None:
        generator = zip(X_aug, Y_aug)

        for (img, label) in generator:
            yield (img, label)
    else:
        generator = zip(X_aug, Y_aug, W_aug)
        for (img, label, weight) in generator:
            yield ([img, weight], label) 
        
        
def crop_generator(generator, crop_length, val=False, weights_on_data=False):
    """Generate random crops of the images extracted from a generator. Uses
       :meth:`util.random_crop` to make the crop. 

       Parameters
       ----------
       generator : Keras ImageDataGenerator
           Generator to extract images from. 
        
       crop_length : int
           Size of the crop. Its shape will be square: 
           ``(crop_length, crop_length)``.
      
       val: bool, optional
           To advise the function that the given data is for validation, which 
           ensures that the crop choosen will be always the same: starting from
           (0,0) coords. 

       weights_on_data : bool, optional
           To advise the method that weights on data should be unpacked from the
           batches extracted from the generator.
     
       Yields
       ------
       out : 2 element list
           One batch of the generator. 
    """

    while True:
        batch_x, batch_y = next(generator)
        if weights_on_data:
            x, w = batch_x 
            y = batch_y
            batch_crops_w = np.zeros((x.shape[0], crop_length, crop_length, 1))
        else:
            x = batch_x
            y = batch_y

        batch_crops_x = np.zeros((x.shape[0], crop_length, crop_length, 1))
        batch_crops_y = np.zeros((x.shape[0], crop_length, crop_length, 1))

        for i in range(x.shape[0]):
            if weights_on_data:
                batch_crops_x[i],\
                batch_crops_y[i],\
                batch_crops_w[i] = random_crop(
                    x[i], y[i], (crop_length, crop_length), val=val, 
                    weight_map=w[i])

                yield ([batch_crops_x, batch_crops_w], batch_crops_y)
            
            else:
                batch_crops_x[i],\
                batch_crops_y[i] = random_crop(
                    batch_x[i], batch_y[i], (crop_length, crop_length), val=val)

                yield (batch_crops_x, batch_crops_y)

