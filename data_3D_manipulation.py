import numpy as np
import math
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from util import load_data_from_dir, load_3d_images_from_dir


def load_and_prepare_3D_data(train_path, train_mask_path, test_path, 
    test_mask_path, image_train_shape, image_test_shape, test_subvol_shape,
    train_subvol_shape, create_val=True, shuffle_val=True, val_split=0.1, 
    seedValue=42, random_subvolumes_in_DA=False, ov=(0,0,0), overlap_train=False,
    use_rest_train=True):         
    """Load train, validation and test images from the given paths to create a 
       3D data representation. All the test data will be used to create a 3D
       volume of ``test_subvol_shape`` shape (considering ``ov``).

       Parameters
       ----------                                                            
       train_path : str
           Path to the training data.                

       train_mask_path : str
           Path to the training data masks.     

       test_path : str                                                          
           Path to the test data.                                               
                                                                                
       test_mask_path : str                                                     
           Path to the test data masks.                                         
                                                                                
       image_train_shape : 3D tuple
           Dimensions of the images to load. E.g. ``(x, y, channels)``.
                                                                                
       image_test_shape : 3D tuple
           Dimensions of the images to load. E.g. ``(x, y, channels)``.

       train_subvol_shape : 4D tuple
            Shape of the train subvolumes to create. E.g. ``(x, y, z, channels)``.

       test_subvol_shape : 4D tuple
            Shape of the test subvolumes to create. E.g. ``(x, y, z, channels)``.

       create_val : bool, optional                                              
           If true validation data is created (from the train data).                                                    

       shuffle_val : bool, optional                                             
            Take random training examples to create validation data.
                                                                                
       val_split : float, optional                                              
            % of the train data used as validation (value between ``0`` and ``1``).
                                                                                
       seedValue : int, optional                                                
            Seed value.                                                     

       random_subvolumes_in_DA : bool, optional
           To advice the method that not preparation of the data must be done, 
           as random subvolumes will be created on DA, and the whole volume will 
           be used for that.

       ov : Tuple of 3 floats, optional                                         
           Amount of minimum overlap on x, y and z dimensions. The values must 
           be on range ``[0, 1)``, that is, ``0%`` or ``99%`` of overlap.      
           E. g. ``(x, y, z)``.   
  
       overlap_train : bool, optional
           To make training subvolumes as overlapping patches using ``ov``.

       use_rest_train : bool, optional
           Wheter to use the train data remainder when the subvolume shape
           selected has no exact division with it. More info at :func:`~crop_data`
           function.

       Returns
       -------                                                         
       X_train : 5D Numpy array                                                 
           Train images. E.g. ``(num_of_images, y, x, z, channels)``.               
                                                                                
       Y_train : 5D Numpy array                                                 
           Train images' mask. E.g. ``(num_of_images, y, x, z, channels)``.         
                                                                                
       X_val : 5D Numpy array, optional                                         
           Validation images (``create_val==True``). E.g. ``(num_of_images,      
           y, x, z, channels)``.                                                   
                                                                                
       Y_val : 5D Numpy array, optional                                         
           Validation images' mask (``create_val==True``). E.g. ``(num_of_images,
           y, x, z, channels)``.                                  
                                                                                
       X_test : 5D Numpy array                                                  
           Test images. E.g. ``(num_of_images, y, x, z, channels)``.                

       Y_test : 5D Numpy array      
           Test images' mask. E.g. ``(num_of_images, y, x, z, channels)``.  

       orig_test_shape : 4D int tuple
           Test data original shape. E.g. ``(num_of_images, x, y, channels)``.

       norm_value : int
           Normalization value calculated.

       Examples
       --------
       ::

           # EXAMPLE 1
           # Case where we need to load the data and creating a validation split
           train_path = "data/train/x"
           train_mask_path = "data/train/y"
           test_path = "data/test/y"
           test_mask_path = "data/test/y"

           # Data shape is (1024, 768, 165), so each image shape should be this:
           img_train_shape = (1024, 768, 1)
           img_test_shape = (1024, 768, 1)

           # 3D subvolume shape needed
           train_3d_shape = (80, 80, 80, 1)
           test_3d_shape = (80, 80, 80, 1)

           X_train, Y_train, X_val,
           Y_val, X_test, Y_test,
           orig_test_shape, norm_value = load_and_prepare_3D_data(
               train_path, train_mask_path, test_path, test_mask_path, img_train_shape,
               img_test_shape, val_split=0.1, create_val=True, shuffle_val=True,
               ov_=(0,0,0), train_subvol_shape=train_3d_shape,
               test_subvol_shape=test_3d_shape)

           # The function will print the shapes of the generated arrays. In this example:
           #     *** Loaded train data shape is: (194, 80, 80, 80, 1)
           #     *** Loaded validation data shape is: (22, 80, 80, 80, 1)
           #     *** Loaded test data shape is: (390, 80, 80, 80, 1)
           #
           # For the test data, 390 subvolumes have been created. As you may noticed, 
           # a minimum overlap is set (ov=(0,0,0)), leading to more subvolume
           # creation compared to train+val.

           # EXAMPLE 2                                                          
           # As the example 1 but defining a minimum overlap of 50% in both train
           # and test data. Notice how the number of subvolumes has been increased 
           #                                                                    
           X_train, Y_train, X_val,                                             
           Y_val, X_test, Y_test,                                               
           orig_test_shape, norm_value = load_and_prepare_3D_data(              
               train_path, train_mask_path, test_path, test_mask_path, img_train_shape,
               img_test_shape, val_split=0.1, create_val=True, shuffle_val=True,
               overlap_train=True, ov=(0.5,0.5,0.5), train_subvol_shape=train_3d_shape,              
               test_subvol_shape=test_3d_shape)                                 
                                                                                
           # The function will print the shapes of the generated arrays. In this example:
           #     *** Loaded train data shape is: (1710, 80, 80, 80, 1)
           #     *** Loaded validation data shape is: (190, 80, 80, 80, 1)       
           #     *** Loaded test data shape is: (1900, 80, 80, 80, 1)            
           #

           # EXAMPLE 3
           # As the example 1 but when random_subvolumes_in_DA is True and no validation data
           # needs to be created. The test data should be of the same shape as the example 1.
           # However, the returned train data will be the same but adding an extra dimension 
           # on the first axis. This is made to consider the entire data as a unique subvolume.
           # More information about this in 3D generator. 
           # 
           X_train, Y_train, X_val,
           Y_val, X_test, Y_test,
           orig_test_shape, norm_value = load_and_prepare_3D_data(
               train_path, train_mask_path, test_path, test_mask_path, img_train_shape,
               img_test_shape, create_val=False, random_subvolumes_in_DA=True, ov=(0,0,0),
               train_subvol_shape=train_3d_shape, test_subvol_shape=test_3d_shape)

           # The function will print the shapes of the generated arrays. In this example:
           #     *** Loaded train data shape is: (1, 768, 1024, 165, 1)
           #     *** Loaded test data shape is: (390, 80, 80, 80, 1)
           # Notice height and width swap because of Numpy ndarray terminology
    """      
   
    print("### LOAD ###")
                                                                        
    tr_shape = (image_train_shape[1], image_train_shape[0], image_train_shape[2])
    print("0) Loading train images . . .")
    X_train = load_data_from_dir(train_path, tr_shape)
    print("1) Loading train masks . . .")
    Y_train = load_data_from_dir(train_mask_path, tr_shape)

    te_shape = (image_test_shape[1], image_test_shape[0], image_test_shape[2])
    print("2) Loading test images . . .")
    X_test = load_data_from_dir(test_path, te_shape)
    print("3) Loading test masks . . .")
    Y_test = load_data_from_dir(test_mask_path, te_shape)

    if not random_subvolumes_in_DA:
        print("Cropping train data into 3D subvolumes . . .")
        if overlap_train:
            X_train, Y_train = crop_3D_data_with_overlap(
                X_train, train_subvol_shape, data_mask=Y_train, overlap=ov) 
        else:
            X_train, Y_train = crop_3D_data(
                X_train, train_subvol_shape, use_rest=use_rest_train,
                data_mask=Y_train)

    # Add zeros in test to match needed shape 
    if test_subvol_shape[2] > X_test.shape[0]:
        r = test_subvol_shape[2]-X_test.shape[0]
        s = (r, )+X_test.shape[1:]
        X_test = np.concatenate((X_test,np.zeros((s))), axis=0)
        Y_test = np.concatenate((Y_test,np.zeros((s))), axis=0)
    orig_test_shape = tuple(Y_test.shape[i] for i in [0, 1, 2, 3])
    
    print("Cropping test data into 3D subvolumes . . .")
    X_test, Y_test = crop_3D_data_with_overlap(
        X_test, test_subvol_shape, data_mask=Y_test, overlap=ov)
        
    # Create validation data splitting the train
    if create_val:
        X_train, X_val, \
        Y_train, Y_val = train_test_split(
            X_train, Y_train, test_size=val_split, shuffle=shuffle_val, 
            random_state=seedValue)

    # Convert the original volumes as they were a unique subvolume
    if random_subvolumes_in_DA and X_train.ndim == 4:
        X_train = np.expand_dims(np.transpose(X_train, (1,2,0,3)), axis=0)      
        Y_train = np.expand_dims(np.transpose(Y_train, (1,2,0,3)), axis=0)    
        if create_val:
            X_val = np.expand_dims(np.transpose(X_val, (1,2,0,3)), axis=0)
            Y_val = np.expand_dims(np.transpose(Y_val, (1,2,0,3)), axis=0)

    if create_val:
        print("*** Loaded train data shape is: {}".format(X_train.shape))
        print("*** Loaded validation data shape is: {}".format(X_val.shape))
        print("*** Loaded test data shape is: {}".format(X_test.shape))
        print("### END LOAD ###")

        # Calculate normalization value
        norm_value = np.mean(X_train)

        return X_train, Y_train, X_val, Y_val, X_test, Y_test, orig_test_shape, \
               norm_value
    else:                                                               
        print("*** Loaded train data shape is: {}".format(X_train.shape))
        print("*** Loaded test data shape is: {}".format(X_test.shape))
        print("### END LOAD ###")

        # Calculate normalization value
        norm_value = np.mean(X_train)

        return X_train, Y_train, X_test, Y_test, orig_test_shape, norm_value

def load_and_prepare_3D_data_v2(train_path, train_mask_path, test_path, 
    test_mask_path, test_subvol_shape, train_subvol_shape, create_val=True, 
    shuffle_val=True, val_split=0.1, seedValue=42, random_subvolumes_in_DA=False, 
    ov=(0,0,0), padding=(0,0,0), median_padding=False):
    """Load train, validation and test images from the given paths to create a 
       3D data representation. All the test data will be used to create a 3D
       volume of ``test_subvol_shape`` shape (considering ``ov``).
    
       The difference between :func:`~load_and_prepare_3D_data` is that this 
       function loads 3D images directly from the given path.

       Parameters
       ----------                                                            
       train_path : str
           Path to the training data.                

       train_mask_path : str
           Path to the training data masks.     

       test_path : str                                                          
           Path to the test data.                                               
                                                                                
       test_mask_path : str                                                     
           Path to the test data masks.                                         
                                                                                
       train_subvol_shape : 4D tuple
            Shape of the train subvolumes to create. E.g. ``(x, y, z, channels)``.

       test_subvol_shape : 4D tuple
            Shape of the test subvolumes to create. E.g. ``(x, y, z, channels)``.

       create_val : bool, optional                                              
           If true validation data is created (from the train data).                                                    

       shuffle_val : bool, optional                                             
            Take random training examples to create validation data.
                                                                                
       val_split : float, optional                                              
            % of the train data used as validation (value between ``0`` and ``1``).
                                                                                
       seedValue : int, optional                                                
            Seed value.                                                     

       random_subvolumes_in_DA : bool, optional
           To advice the method that not preparation of the data must be done, 
           as random subvolumes will be created on DA, and the whole volume will 
           be used for that.

       ov : Tuple of 3 floats, optional                                         
           Amount of minimum overlap on x, y and z dimensions. The values must 
           be on range ``[0, 1)``, that is, ``0%`` or ``99%`` of overlap.      
           E. g. ``(x, y, z)``.  
           
       padding : tuple of ints, optional                                        
           Size of padding to be added on each axis ``(x, y, z)``. 
           E.g. ``(24, 24, 24)``.
           
       median_padding : bool, optional
           If ``True`` the padding value is the median value. If ``False``, the 
           added values are zeroes.   
  
       Returns
       -------                                                         
       X_train : 5D Numpy array                                                 
           Train images. E.g. ``(num_of_images, y, x, z, channels)``.               
                                                                                
       Y_train : 5D Numpy array                                                 
           Train images' mask. E.g. ``(num_of_images, y, x, z, channels)``.         
                                                                                
       X_val : 5D Numpy array, optional                                         
           Validation images (``create_val==True``). E.g. ``(num_of_images,      
           y, x, z, channels)``.                                                   
                                                                                
       Y_val : 5D Numpy array, optional                                         
           Validation images' mask (``create_val==True``). E.g. ``(num_of_images,
           y, x, z, channels)``.                                  
                                                                                
       X_test : 5D Numpy array                                                  
           Test images. E.g. ``(num_of_images, y, x, z, channels)``.                

       Y_test : 5D Numpy array      
           Test images' mask. E.g. ``(num_of_images, y, x, z, channels)``.  

       orig_test_img_shapes : List of tuples 
           List that contains the shapes of each test sample. This      
           variable and ``crop_test_img_shapes`` should be used to reconstruct
           the test original images from patches with :func:`~merge_3D_data_with_overlap`.

       crop_test_img_shapes : List of tuples
           List that contains the shapes of each test sample cropped. 

       filenames : List of str
           Loaded train and test filenames. ``filenames[0]`` are train filenames 
           and ``filenames[1]`` are test filenames.

       Examples
       --------
       ::

           # EXAMPLE 1
           # Case where we need to load the data and creating a validation split
           train_path = "data/train/x"
           train_mask_path = "data/train/y"
           test_path = "data/test/y"
           test_mask_path = "data/test/y"

           # Train data is (15, 1024, 1024, 91), and the test is (5, 1024, 1024, 91),
           # where (number_of_images, x, y, z), so each image shape should be this:
           img_train_shape = (1024, 1024, 91, 1)
           img_test_shape = (1024, 1024, 91, 1)

           # 3D subvolume shape needed
           train_3d_shape = (256, 256, 40, 1)
           test_3d_shape = (256, 256, 40, 1)

           X_train, Y_train, X_val,\
           Y_val, X_test, Y_test,\
           orig_test_shape, crop_test_shapes,\
           filenames = load_and_prepare_3D_data_v2(
               train_path, train_mask_path, test_path, test_mask_path, img_train_shape,
               img_test_shape, val_split=0.1, create_val=True, shuffle_val=True,
               test_subvol_shape=test_3d_shape, train_subvol_shape=train_3d_shape, 
               ov=(0,0,0))

           # The function will print the shapes of the generated arrays. In this example:
           #     *** Loaded train data shape is: (315, 256, 256, 40, 1)
           #     *** Loaded validation data shape is: (35, 256, 256, 40, 1)
           #     *** Loaded test data shape is: (178, 256, 256, 40, 1)
           #
    """      
   
    print("### LOAD ###")
                                                                        
    # Disable crops when random_subvolumes_in_DA is selected 
    crop = False if random_subvolumes_in_DA else True

    print("0) Loading train images . . .")
    X_train, _, _, t_filenames = load_3d_images_from_dir(train_path, crop=crop,
        crop_shape=train_subvol_shape, overlap=ov, return_filenames=True)

    print("1) Loading train masks . . .")
    Y_train, _, _ = load_3d_images_from_dir(
        train_mask_path, crop=crop, crop_shape=train_subvol_shape, overlap=ov)

    print("2) Loading test images . . .")
    X_test, orig_test_img_shapes, \
    crop_test_img_shapes, te_filenames = load_3d_images_from_dir(
        test_path, crop=True, crop_shape=test_subvol_shape, overlap=ov,
        return_filenames=True, padding=padding, median_padding=median_padding)
    print("3) Loading test masks . . .")
    Y_test, _, _ = load_3d_images_from_dir(test_mask_path, crop=True,            
        crop_shape=test_subvol_shape, overlap=ov, padding=padding,
        median_padding=median_padding)

    # Save train and test filenames
    filenames = []
    filenames.append(t_filenames)
    filenames.append(te_filenames)

    # Create validation data splitting the train
    if create_val:
        X_train, X_val, \
        Y_train, Y_val = train_test_split(
            X_train, Y_train, test_size=val_split, shuffle=shuffle_val, 
            random_state=seedValue)

    # Convert the original volumes as they were a unique subvolume
    if random_subvolumes_in_DA and X_train.ndim == 4:                                                 
        X_train = np.expand_dims(np.transpose(X_train, (1,2,0,3)), axis=0)      
        Y_train = np.expand_dims(np.transpose(Y_train, (1,2,0,3)), axis=0)    
        if create_val:
            X_val = np.expand_dims(np.transpose(X_val, (1,2,0,3)), axis=0)
            Y_val = np.expand_dims(np.transpose(Y_val, (1,2,0,3)), axis=0)

    if create_val:
        print("*** Loaded train data shape is: {}".format(X_train.shape))
        print("*** Loaded validation data shape is: {}".format(X_val.shape))
        print("*** Loaded test data shape is: {}".format(X_test.shape))
        print("### END LOAD ###")

        return X_train, Y_train, X_val, Y_val, X_test, Y_test, \
               orig_test_img_shapes, crop_test_img_shapes, filenames
    else:                                                               
        print("*** Loaded train data shape is: {}".format(X_train.shape))
        print("*** Loaded test data shape is: {}".format(X_test.shape))
        print("### END LOAD ###")

        return X_train, Y_train, X_test, Y_test, orig_test_img_shapes, \
               crop_test_img_shapes, filenames


def crop_3D_data_with_overlap(data, vol_shape, data_mask=None, overlap=(0,0,0),
                              padding=(0,0,0), verbose=True, median_padding=False):
    """Crop 3D data into smaller volumes with a defined overlap.
       The opposite function is :func:`~merge_3D_data_with_overlap`.

       Parameters
       ----------
       data : 4D Numpy array
           Data to crop. E.g. ``(num_of_images, x, y, channels)``.

       vol_shape : 4D int tuple
           Shape of the volumes to create. E.g. ``(x, y, z, channels)``.
        
       data_mask : 4D Numpy array, optional
            Data mask to crop. E.g. ``(num_of_images, x, y, channels)``.
    
       overlap : Tuple of 3 floats, optional
            Amount of minimum overlap on x, y and z dimensions. The values must
            be on range ``[0, 1)``, that is, ``0%`` or ``99%`` of overlap. 
            E.g. ``(x, y, z)``.
                                                                                
       padding : tuple of ints, optional                                        
           Size of padding to be added on each axis ``(x, y, z)``.                
           E.g. ``(24, 24, 24)``.

       verbose : bool, optional
            To print information about the crop to be made.
            
       median_padding : bool, optional
           If ``True`` the padding value is the median value. If ``False``, the
           added values are zeroes.   
  
       Returns
       -------
       cropped_data : 5D Numpy array
           Cropped image data. E.g. ``(vol_number, x, y, z, channels)``.

       cropped_data_mask : 5D Numpy array, optional
           Cropped image data masks. E.g. ``(vol_number, x, y, z, channels)``.
        
       Examples
       --------
       ::
           # EXAMPLE 1   
           # Following the example introduced in load_and_prepare_3D_data function, the 
           # cropping of a volume with shape (165, 1024, 765) should be done by the 
           # following call: 
           X_train = np.ones((165, 768, 1024, 1))
           Y_train = np.ones((165, 768, 1024, 1))
           X_train, Y_train = crop_3D_data_with_overlap(
                X_train, (80, 80, 80, 1), data_mask=Y_train, overlap=(0.5,0.5,0.5))
           # The function will print the shape of the generated arrays. In this example:
           #     **** New data shape is: (2600, 80, 80, 80, 1)
       A visual explanation of the process:                                     
                                                                                
       .. image:: img/crop_3D_ov.png                                               
           :width: 80%                                                          
           :align: center
    
       Note: this image do not respect the proportions.
       ::  
           # EXAMPLE 2 
           # Same data crop but without overlap
          
           X_train, Y_train = crop_3D_data_with_overlap(                        
                X_train, (80, 80, 80, 1), data_mask=Y_train, overlap=(0,0,0))
           
           # The function will print the shape of the generated arrays. In this example:  
           #     **** New data shape is: (390, 80, 80, 80, 1)
           #
           # Notice how differs the amount of subvolumes created compared to the 
           # first example
           
           #EXAMPLE 2
           #In the same way, if the addition of (64,64,64) padding is required, the call
           #should be done as shown:
           X_train, Y_train = crop_3D_data_with_overlap(
                X_train, (80, 80, 80, 1), data_mask=Y_train, overlap=(0.5,0.5,0.5), padding=(64,64,64))
    """

    if verbose:
        print("### 3D-OV-CROP ###")
        print("Cropping {} images into {} with overlapping . . ."
              .format(data.shape, vol_shape))
        print("Minimum overlap selected: {}".format(overlap))
        print("Padding: {}".format(padding))
                         
    padded_data = np.zeros((data.shape[0]+2*padding[2], 
                            data.shape[1]+2*padding[0], 
                            data.shape[2]+2*padding[1], 
                            data.shape[3]), dtype=data.dtype)
    padded_data[padding[2]:padding[2]+data.shape[0], 
                padding[0]:padding[0]+data.shape[1],
                padding[1]:padding[1]+data.shape[2],:] = data 
    if data_mask is not None:
        padded_data_mask = np.zeros((data_mask.shape[0]+2*padding[2],
                                     data_mask.shape[1]+2*padding[0],
                                     data_mask.shape[2]+2*padding[1],
                                     data_mask.shape[3]), dtype=data_mask.dtype)
        padded_data_mask[padding[2]:padding[2]+data_mask.shape[0],
                         padding[0]:padding[0]+data_mask.shape[1],
                         padding[1]:padding[1]+data_mask.shape[2],:] = data_mask
    
    if median_padding:
    	padded_data[0:padding[2], :, :, :] = np.median(data[0, :, :, :])
    	padded_data[padding[2]+data.shape[0]:2*padding[2]+data.shape[0], :, :, :] = np.median(data[-1, :, :, :])
    	padded_data[:, 0:padding[0], :, :] = np.median(data[:, 0, :, :])
    	padded_data[:, padding[0]+data.shape[1]:2*padding[0]+data.shape[0], :, :] = np.median(data[:, -1, :, :])
    	padded_data[:, :, 0:padding[1], :] = np.median(data[:, :, 0, :])
    	padded_data[ :, :, padding[1]+data.shape[2]:2*padding[1]+data.shape[2], :] = np.median(data[:, :, -1, :])

    #Original vol shape (no padding)
    vol_shape = tuple(vol_shape[i] for i in [2, 0, 1, 3])
    padded_vol_shape = vol_shape
    vol_shape = (vol_shape[0]-2*padding[2],vol_shape[1]-2*padding[0],vol_shape[2]-2*padding[1],vol_shape[3])
    
    if (overlap[0] >= 1 or overlap[0] < 0)\
       and (overlap[1] >= 1 or overlap[1] < 0)\
       and (overlap[2] >= 1 or overlap[2] < 0): 
        raise ValueError("'overlap' values must be floats between range [0, 1)")
    if len(vol_shape) != 4:
        raise ValueError("'vol_shape' must be 4D int tuple")
    if vol_shape[0] > data.shape[0]:
        raise ValueError("'vol_shape[0]' {} greater than {}"
                         .format(vol_shape[0], data.shape[0]))
    if vol_shape[1] > data.shape[1]:
        raise ValueError("'vol_shape[1]' {} greater than {}"
                         .format(vol_shape[1], data.shape[1]))
    if vol_shape[2] > data.shape[2]:
        raise ValueError("'vol_shape[2]' {} greater than {}"
                         .format(vol_shape[2], data.shape[2]))
    # Calculate overlapping variables
    overlap_x = 1 if overlap[0] == 0 else 1-overlap[0]                       
    overlap_y = 1 if overlap[1] == 0 else 1-overlap[1]                       
    overlap_z = 1 if overlap[2] == 0 else 1-overlap[2]

    # X
    vols_per_x = math.ceil(data.shape[1]/(vol_shape[1]*overlap_x))
    excess_x = int((vols_per_x*vol_shape[1])-((vols_per_x-1)*overlap[0]*vol_shape[1]))-data.shape[1]
    ex = 0 if vols_per_x == 1 else int(excess_x/(vols_per_x-1))
    step_x = int(vol_shape[1]*overlap_x)-ex
    last_x = 0 if vols_per_x == 1 else excess_x%(vols_per_x-1)

    # Y
    vols_per_y = math.ceil(data.shape[2]/(vol_shape[2]*overlap_y))
    excess_y = int((vols_per_y*vol_shape[2])-((vols_per_y-1)*overlap[1]*vol_shape[2]))-data.shape[2]
    ex = 0 if vols_per_y == 1 else int(excess_y/(vols_per_y-1))
    step_y = int(vol_shape[2]*overlap_y)-ex
    last_y = 0 if vols_per_y == 1 else excess_y%(vols_per_y-1)

    # Z
    vols_per_z = math.ceil(data.shape[0]/(vol_shape[0]*overlap_z))              
    excess_z = int((vols_per_z*vol_shape[0])-((vols_per_z-1)*overlap[2]*vol_shape[0]))-data.shape[0]
    ex = 0 if vols_per_z == 1 else int(excess_z/(vols_per_z-1))
    step_z = int(vol_shape[0]*overlap_z)-ex
    last_z = 0 if vols_per_z == 1 else excess_z%(vols_per_z-1)
    
    # Real overlap calculation for printing 
    real_ov_x = (vol_shape[1]-step_x)/vol_shape[1]
    real_ov_y = (vol_shape[2]-step_y)/vol_shape[2]
    real_ov_z = (vol_shape[0]-step_z)/vol_shape[0]
    if verbose:
        print("Real overlapping (%): {}".format((real_ov_x,real_ov_y,real_ov_z)))
        print("Real overlapping (pixels): {}".format((vol_shape[1]*real_ov_x,
              vol_shape[2]*real_ov_y,vol_shape[0]*real_ov_z)))
    
        print("{} patches per (x,y,z) axis".format((vols_per_x,vols_per_y,vols_per_z)))

    total_vol = vols_per_z*vols_per_x*vols_per_y
    cropped_data = np.zeros((total_vol,) + padded_vol_shape, dtype=data.dtype)
    if data_mask is not None:
        cropped_data_mask = np.zeros((total_vol,) + padded_vol_shape[:3]+(data_mask.shape[-1],),
                                     dtype=data_mask.dtype)

    c = 0
    for z in range(vols_per_z):
        for x in range(vols_per_x):
            for y in range(vols_per_y):
                d_x = 0 if (x*step_x+vol_shape[1]) < data.shape[1] else last_x
                d_y = 0 if (y*step_y+vol_shape[2]) < data.shape[2] else last_y
                d_z = 0 if (z*step_z+vol_shape[0]) < data.shape[0] else last_z

                cropped_data[c] = \
                    padded_data[z*step_z-d_z:(z*step_z)+vol_shape[0]-d_z+2*padding[2],
                                x*step_x-d_x:x*step_x+vol_shape[1]-d_x+2*padding[0],
                                y*step_y-d_y:y*step_y+vol_shape[2]-d_y+2*padding[1]]
                if data_mask is not None:
                    cropped_data_mask[c] = \
                        padded_data_mask[z*step_z-d_z:(z*step_z)+vol_shape[0]-d_z+2*padding[2],
                                         x*step_x-d_x:x*step_x+vol_shape[1]-d_x+2*padding[0],   
                                         y*step_y-d_y:y*step_y+vol_shape[2]-d_y+2*padding[1]]
                c += 1

    cropped_data = cropped_data.transpose(0,2,3,1,4)

    if verbose:
        print("**** New data shape is: {}".format(cropped_data.shape))
        print("### END 3D-OV-CROP ###")

    if data_mask is not None:
        cropped_data_mask = cropped_data_mask.transpose(0,2,3,1,4)
        return cropped_data, cropped_data_mask
    else:
        return cropped_data
    

def crop_3D_data(data, vol_shape, data_mask=None, use_rest=False, verbose=True):
    """Crop 3D data into smaller volumes without overlap. If there is no exact
       division between the data shape and ``vol_shape`` in a specific dimension
       it will be discarded or zeros will be added if ``use_rest`` is True.

       Parameters
       ----------
       data : Numpy 4D array
           Data. E.g. ``(num_of_images, x, y, channels)``.      
                                                                           
       vol_shape : 4D int tuple
           Shape of the volumes to create. E.g. ``(x, y, z, channels)``.

       data_mask : Numpy 4D array, optional
           Mask data. E.g. ``(num_of_images, x, y, channels)``.
        
       use_rest : bool, optional
           Controls how the rest data will be processed. When there is no exact
           division between the data shape and ``vol_shape`` in a specific
           dimension, the remainder data is not enough to create another 
           subvolume. If True, that data will be used completing the rest of the 
           subvolume with zeros. If ``False``, that remainder will be dropped 
           (notice that this option will make the data impossible to reconstruct 
           100% later on). See example 2 for more info. 
        
       verbose : bool, optional
            To print information about the crop to be made.

       Returns
       -------
       cropped_data : Numpy 5D array
           data data separated in different subvolumes with the provided shape. E.g.
           ``(subvolume_number, ) + shape``.
            
       cropped_data_mask : Numpy 5D array
           data_mask data separated in different subvolumes with the provided shape. E.g. 
           ``(subvolume_number, ) + shape``.

       Examples                                                                 
       --------                                                                 
       ::                                                                       
                                                                                
           # EXAMPLE 1                                                          
           # Crop into subvolumes a volume with shape (165, 1024, 765)
                                                                                
           X_train = np.ones((165, 768, 1024, 1))                               
           Y_train = np.ones((165, 768, 1024, 1))                               
                                                                                
           X_train, Y_train = crop_3D(X_train, (80, 80, 80, 1), data_mask=Y_train)
                                                                                
           # The function will print the shape of the generated arrays and the data
           # discarded on each axis ``(x,y,z)``, as use_rest is False 
           #       [...]
           #    Pixels dropped per dimension: (48,64,5)
           #       [...]
           #     **** New data shape is: (216, 80, 80, 80, 1)
                                                                                

           # EXAMPLE 2
           # As the first example but using all the data 
                                                                                
           X_train, Y_train = crop_3D(X_train, (80, 80, 80, 1), data_mask=Y_train, use_rest=True)
                                                                                
           # The function will print the shape of the generated arrays. In this example:
           #     **** New data shape is: (390, 80, 80, 80, 1)

       A visual explanation of example 2:
                                                                                
       .. image:: img/crop_3D.png                                               
           :width: 80%                                                          
           :align: center                                                       


       As you may noticed, as ``use_rest=True`` the last subvolume is filled with
       zeros (black) instead of been discarded. Thus, more subvolumes have been 
       created. 

       Adding zeros to all the axis when they do not have an exact division could not
       be the best approach in all cases. In example 2, the amount of pixels along x
       and y axis are not to much, however, for the z axis, that amount is high
       considering that we only have about 165 slices. To notify the user, the method
       also prints the number of zeros added per each axis ``(x,y,z)`` as follows:

       ::

          X_train, Y_train = crop_3D(X_train, (80, 80, 80, 1), data_mask=Y_train, use_rest=True)
          #       [...]
          #     Zeros added per dimension: (32,16,75)
          #       [...]
          #     **** New data shape is: (390, 80, 80, 80, 1)
    """
        
    if verbose:
        print("### 3D-CROP ###")
        print("Cropping {} images into {} . . .".format(data.shape, vol_shape))

    if len(vol_shape) != 4:
        raise ValueError("'vol_shape' must be 4D int tuple")
    if data.ndim != 4:
        raise ValueError("data must be a 4D Numpy array")
    if data_mask is not None:
        if data_mask.ndim != 4:                                              
            raise ValueError("data_mask must be a 4D Numpy array") 
    if vol_shape[0] > data.shape[1]:
        raise ValueError("'vol_shape[0]' {} greater than {}"
                         .format(vol_shape[0], data.shape[1]))
    if vol_shape[1] > data.shape[2]:
        raise ValueError("'vol_shape[1]' {} greater than {}"
                         .format(vol_shape[1], data.shape[2]))
    if vol_shape[2] > data.shape[0]:
        raise ValueError("'vol_shape[2]' {} greater than {}"
                         .format(vol_shape[2], data.shape[0]))

    # Calculate crops per axis                                      
    vols_per_x = math.ceil(data.shape[1]/vol_shape[0])
    vols_per_y = math.ceil(data.shape[2]/vol_shape[1])
    vols_per_z = math.ceil(data.shape[0]/vol_shape[2])
    
    _d_x = 1 if data.shape[1]%vol_shape[0] and not use_rest else 0
    _d_y = 1 if data.shape[2]%vol_shape[1] and not use_rest else 0
    _d_z = 1 if data.shape[0]%vol_shape[2] and not use_rest else 0
    
    num_sub_volum = (vols_per_x-_d_x)*(vols_per_y-_d_y)*(vols_per_z-_d_z)

    # Calculate the excess
    last_x = vols_per_x*vol_shape[0]-data.shape[1]
    last_y = vols_per_y*vol_shape[1]-data.shape[2]
    last_z = vols_per_z*vol_shape[2]-data.shape[0]
    if use_rest:
        if verbose:
            print("Zeros added per dimension: ({},{},{})"
                  .format(last_x,last_y,last_z))
    else:
        drop_x = 0 if last_x == 0 else vol_shape[0]-last_x
        drop_y = 0 if last_y == 0 else vol_shape[1]-last_y
        drop_z = 0 if last_z == 0 else vol_shape[2]-last_z
        if verbose:
            print("Pixels dropped per dimension: ({},{},{})"
                  .format(drop_x,drop_y,drop_z))
                                                                                
    cropped_data = np.zeros((num_sub_volum, ) + vol_shape, dtype=data.dtype)
    if data_mask is not None:
        cropped_data_mask = np.zeros((num_sub_volum, ) + vol_shape[:3]+(data_mask.shape[-1],),
                                     dtype=data_mask.dtype)
                                                                                
    if verbose:
        print("{},{},{} patches per x,y,z axis"
              .format((vols_per_x),(vols_per_y),(vols_per_z)))

    # Reshape the data to generate needed 3D subvolumes                        
    c = 0
    for z in range(vols_per_z):
        for x in range(vols_per_x):                                                  
            for y in range(vols_per_y):
                d_x = 0 if (((x+1)*vol_shape[0])) < data.shape[1] else last_x
                d_y = 0 if (((y+1)*vol_shape[1])) < data.shape[2] else last_y
                d_z = 0 if (((z+1)*vol_shape[2])) < data.shape[0] else last_z

                if d_x != 0 and not use_rest: break
                if d_y != 0 and not use_rest: break
                if d_z != 0 and not use_rest: break

                cropped_data[c,0:vol_shape[0]-d_x,
                               0:vol_shape[1]-d_y,
                               0:vol_shape[2]-d_z] = \
                    data[(z*vol_shape[2]):((z+1)*vol_shape[2])-d_z,
                         (x*vol_shape[0]):((x+1)*vol_shape[0])-d_x,
                         (y*vol_shape[1]):((y+1)*vol_shape[1])-d_y].transpose(1,2,0,3)
                if data_mask is not None:
                    cropped_data_mask[c,0:vol_shape[0]-d_x,                              
                                        0:vol_shape[1]-d_y,
                                        0:vol_shape[2]-d_z] = \
                        data_mask[(z*vol_shape[2]):((z+1)*vol_shape[2])-d_z,                 
                                  (x*vol_shape[0]):((x+1)*vol_shape[0])-d_x,                 
                                  (y*vol_shape[1]):((y+1)*vol_shape[1])-d_y].transpose(1,2,0,3)
                c += 1                                                                

    if verbose:
        print("**** New data shape is: {}".format(cropped_data.shape))
        print("### END 3D-CROP ###")

    if data_mask is not None:
        return cropped_data, cropped_data_mask
    else:
        return cropped_data


def merge_3D_data_with_overlap(data, orig_vol_shape, data_mask=None,
                               overlap=(0,0,0), padding=(0,0,0), verbose=True):
    """Merge 3D subvolumes in a 3D volume with a defined overlap.

       The opposite function is :func:`~crop_3D_data_with_overlap`.

       Parameters
       ----------
       data : 5D Numpy array
           Data to crop. E.g. ``(volume_number, x, y, z, channels)``.

       orig_vol_shape : 4D int tuple
           Shape of the volumes to create.

       data_mask : 4D Numpy array, optional
           Data mask to crop. E.g. ``(volume_number, x, y, z, channels)``.

       overlap : Tuple of 3 floats, optional                                    
            Amount of minimum overlap on x, y and z dimensions. Should be the 
            same as used in :func:`~crop_3D_data_with_overlap`. The values must 
            be on range ``[0, 1)``, that is, ``0%`` or ``99%`` of overlap.      
            E.g. ``(x, y, z)``. 

       padding : tuple of ints, optional                                        
           Size of padding to be added on each axis ``(x, y, z)``.                
           E.g. ``(24, 24, 24)``.

       verbose : bool, optional
            To print information about the crop to be made.
            
       Returns
       -------
       merged_data : 4D Numpy array
           Cropped image data. E.g. ``(num_of_images, x, y, channels)``.

       merged_data_mask : 5D Numpy array, optional
           Cropped image data masks. E.g. ``(num_of_images, x, y, channels)``.

       Examples                                                                 
       --------                                                                 
       ::                                                                       
                                                                                
           # EXAMPLE 1                                                          
           # Following the example introduced in crop_3D_data_with_overlap function, the 
           # merge after the cropping should be done as follows:
                                                                                
           X_train = np.ones((165, 768, 1024, 1))                               
           Y_train = np.ones((165, 768, 1024, 1))                               
                                                                                
           X_train, Y_train = crop_3D_data_with_overlap(                        
                X_train, (80, 80, 80, 1), data_mask=Y_train, overlap=(0.5,0.5,0.5))
           X_train, Y_train = merge_3D_data_with_overlap(
                X_train, (165, 768, 1024, 1), data_mask=Y_train, overlap=(0.5,0.5,0.5))
                                                                                
           # The function will print the shape of the generated arrays. In this example:
           #     **** New data shape is: (165, 768, 1024, 1)
                                                                                
           # EXAMPLE 2                                                          
           # In the same way, if no overlap in cropping was selected, the merge call
           # should be as follows:
                                                                                
           X_train, Y_train = merge_3D_data_with_overlap(
                X_train, (165, 768, 1024, 1), data_mask=Y_train, overlap=(0,0,0))   
                                                                                
           # The function will print the shape of the generated arrays. In this example:  
           #     **** New data shape is: (165, 768, 1024, 1)
                                                                                           
           # EXAMPLE 3                                                          
           # On the contrary, if no overlap in cropping was selected but a padding of shape
           # (64,64,64) is needed, the merge call should be as follows:
                                                                                
           X_train, Y_train = merge_3D_data_with_overlap(
                X_train, (165, 768, 1024, 1), data_mask=Y_train, overlap=(0,0,0), padding=(64,64,64))   
                                                                                
           # The function will print the shape of the generated arrays. In this example:  
           #     **** New data shape is: (165, 768, 1024, 1)
    """ 

    if verbose:
        print("### MERGE-3D-OV-CROP ###")
        print("Merging {} images into {} with overlapping . . ."               
              .format(data.shape, orig_vol_shape)) 
        print("Minimum overlap selected: {}".format(overlap))
        print("Padding: {}".format(padding))

    # Remove the padding
    data = data[:, padding[0]:data.shape[1]-padding[0],
                padding[1]:data.shape[2]-padding[1],
                padding[2]:data.shape[3]-padding[2], :]
    
    if (overlap[0] >= 1 or overlap[0] < 0)\
       and (overlap[1] >= 1 or overlap[1] < 0)\
       and (overlap[2] >= 1 or overlap[2] < 0):                                 
        raise ValueError("'overlap' values must be floats between range [0, 1)")

    merged_data = np.zeros((orig_vol_shape), dtype=data.dtype)
    if data_mask is not None:
        data_mask = data_mask[:, padding[0]:data_mask.shape[1]-padding[0],
                              padding[1]:data_mask.shape[2]-padding[1],
                              padding[2]:data_mask.shape[3]-padding[2], :]
        merged_data_mask = np.zeros(orig_vol_shape[:3]+(data_mask.shape[-1],),
                                    dtype=data_mask.dtype)

    ov_map_counter = np.zeros((orig_vol_shape))

    # Calculate overlapping variables                                           
    overlap_x = 1 if overlap[0] == 0 else 1-overlap[0]                          
    overlap_y = 1 if overlap[1] == 0 else 1-overlap[1]                          
    overlap_z = 1 if overlap[2] == 0 else 1-overlap[2]  

    # X
    vols_per_x = math.ceil(orig_vol_shape[1]/(data.shape[1]*overlap_x))
    excess_x = int((vols_per_x*data.shape[1])-((vols_per_x-1)*overlap[0]*data.shape[1]))-orig_vol_shape[1]
    ex = 0 if vols_per_x == 1 else int(excess_x/(vols_per_x-1))
    step_x = int(data.shape[1]*overlap_x)-ex
    last_x = 0 if vols_per_x == 1 else excess_x%(vols_per_x-1)

    # Y
    vols_per_y = math.ceil(orig_vol_shape[2]/(data.shape[2]*overlap_y))
    excess_y = int((vols_per_y*data.shape[2])-((vols_per_y-1)*overlap[1]*data.shape[2]))-orig_vol_shape[2]
    ex = 0 if vols_per_y == 1 else int(excess_y/(vols_per_y-1))
    step_y = int(data.shape[2]*overlap_y)-ex
    last_y = 0 if vols_per_y == 1 else excess_y%(vols_per_y-1)

    # Z
    vols_per_z = math.ceil(orig_vol_shape[0]/(data.shape[3]*overlap_z))
    excess_z = int((vols_per_z*data.shape[3])-((vols_per_z-1)*overlap[2]*data.shape[3]))-orig_vol_shape[0]
    ex = 0 if vols_per_z == 1 else int(excess_z/(vols_per_z-1))
    step_z = int(data.shape[3]*overlap_z)-ex
    last_z = 0 if vols_per_z == 1 else excess_z%(vols_per_z-1) 

    # Real overlap calculation for printing                                     
    real_ov_x = (data.shape[1]-step_x)/data.shape[1]                              
    real_ov_y = (data.shape[2]-step_y)/data.shape[2]                              
    real_ov_z = (data.shape[3]-step_z)/data.shape[3]                              
    if verbose:
        print("Real overlapping (%): {}".format((real_ov_x,real_ov_y,real_ov_z))) 
        print("Real overlapping (pixels): {}".format((data.shape[1]*real_ov_x,
              data.shape[2]*real_ov_y,data.shape[3]*real_ov_z)))

        print("{} patches per (x,y,z) axis".format((vols_per_x,vols_per_y,vols_per_z)))

	
    c = 0
    for z in range(vols_per_z):
        for x in range(vols_per_x):
            for y in range(vols_per_y):  
                d_x = 0 if (x*step_x+data.shape[1]) < orig_vol_shape[1] else last_x
                d_y = 0 if (y*step_y+data.shape[2]) < orig_vol_shape[2] else last_y
                d_z = 0 if (z*step_z+data.shape[3]) < orig_vol_shape[0] else last_z

                merged_data[z*step_z-d_z:(z*step_z)+data.shape[3]-d_z, 
                            x*step_x-d_x:x*step_x+data.shape[1]-d_x, 
                            y*step_y-d_y:y*step_y+data.shape[2]-d_y] += data[c].transpose(2,0,1,3)
   
                if data_mask is not None: 
                    merged_data_mask[z*step_z-d_z:(z*step_z)+data.shape[3]-d_z,
                                     x*step_x-d_x:x*step_x+data.shape[1]-d_x,
                                     y*step_y-d_y:y*step_y+data.shape[2]-d_y] += data_mask[c].transpose(2,0,1,3)

                ov_map_counter[z*step_z-d_z:(z*step_z)+data.shape[3]-d_z,
                               x*step_x-d_x:x*step_x+data.shape[1]-d_x,
                               y*step_y-d_y:y*step_y+data.shape[2]-d_y] += 1
                c += 1
                    
    merged_data = np.true_divide(merged_data, ov_map_counter)

    if verbose:
        print("**** New data shape is: {}".format(merged_data.shape))
        print("### END MERGE-3D-OV-CROP ###")        

    if data_mask is not None: 
        merged_data_mask = np.true_divide(merged_data_mask, ov_map_counter)
        return merged_data, merged_data_mask
    else:
        return merged_data
        

def random_3D_crop(vol, vol_mask, random_crop_size, val=False, vol_prob=None,
                   weight_map=None, draw_prob_map_points=False):
    """Extracts a random 3D patch from the given image and mask.

       Parameters
       ----------
       vol : 4D Numpy array
           Data to extract the patch from. E.g. ``(x, y, z, channels)``.

       vol_mask : 4D Numpy array
           Data mask to extract the patch from. E.g. ``(x, y, z, channels)``.

       random_crop_size : 3D int tuple
           Shape of the patches to create. E.g. ``(x, y, z)``.

       val : bool, optional
           If the image provided is going to be used in the validation data.
           This forces to crop from the origin, e.g. ``(0, 0)`` point.

       vol_prob : Numpy 3D array, optional
           Probability of each pixel to be chosen as the center of the crop.
           E. .g. ``(x, y, channels)``.

       weight_map : bool, optional
           Weight map of the given image. E.g. ``(x, y, channels)``.
    
       draw_prob_map_points : bool, optional
           To return the voxel chosen to be the center of the crop.

       Returns
       -------
       img : 4D Numpy array
           Crop of the given image. E.g. ``(x, y, z, channels)``.

       weight_map : 4D Numpy array, optional
           Crop of the given image's weigth map. E.g. ``(x, y, z, channels)``.

       ox : int, optional
           X coordinate in the complete image of the chose central pixel to
           make the crop.

       oy : int, optional
           Y coordinate in the complete image of the chose central pixel to
           make the crop.

       x : int, optional
           X coordinate in the complete image where the crop starts.

       y : int, optional
           Y coordinate in the complete image where the crop starts.
    """

    rows, cols, deep = vol.shape[0], vol.shape[1], vol.shape[2]
    dx, dy, dz = random_crop_size
    if val:
        x = 0
        y = 0
        z = 0
        ox = 0
        oy = 0
        oz = 0
    else:
        if vol_prob is not None:
            prob = vol_prob.ravel()

            # Generate the random coordinates based on the distribution
            choices = np.prod(vol_prob.shape)
            index = np.random.choice(choices, size=1, p=prob)
            coordinates = np.unravel_index(index, shape=vol_prob.shape)
            x = int(coordinates[0])
            y = int(coordinates[1])
            z = int(coordinates[2])
            ox = int(coordinates[0])
            oy = int(coordinates[1])
            oz = int(coordinates[2])

            # Adjust the coordinates to be the origin of the crop and control to
            # not be out of the volume
            if x < int(random_crop_size[0]/2):
                x = 0
            elif x > vol.shape[0] - int(random_crop_size[0]/2):
                x = vol.shape[0] - random_crop_size[0]
            else:
                x -= int(random_crop_size[0]/2)

            if y < int(random_crop_size[1]/2):
                y = 0
            elif y > vol.shape[1] - int(random_crop_size[1]/2):
                y = vol.shape[1] - random_crop_size[1]
            else:
                y -= int(random_crop_size[1]/2)

            if z < int(random_crop_size[2]/2):
                z = 0
            elif z > vol.shape[2] - int(random_crop_size[2]/2):
                z = vol.shape[2] - random_crop_size[2]
            else:
                z -= int(random_crop_size[2]/2)
        else:
            ox = 0
            oy = 0
            oz = 0
            x = np.random.randint(0, rows - dx + 1)
            y = np.random.randint(0, cols - dy + 1)
            z = np.random.randint(0, deep - dz + 1)

    if draw_prob_map_points:
        return vol[x:(x+dx), y:(y+dy), z:(z+dz), :], \
               vol_mask[x:(x+dx), y:(y+dy), z:(z+dz), :], ox, oy, oz, x, y, z
    else:
        if weight_map is not None:
            return vol[x:(x+dx), y:(y+dy), z:(z+dz), :], \
                   vol_mask[x:(x+dx), y:(y+dy), z:(z+dz), :],\
                   weight_map[x:(x+dx), y:(y+dy), z:(z+dz), :]
        else:
            return vol[x:(x+dx), y:(y+dy), z:(z+dz), :], \
                   vol_mask[x:(x+dx), y:(y+dy), z:(z+dz), :]

