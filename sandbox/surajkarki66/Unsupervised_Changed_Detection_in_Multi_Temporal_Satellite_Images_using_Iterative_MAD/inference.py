import time
import numpy as np  
import imageio.v2 as imageio

from main import IRMAD, get_binary_change_map

if __name__ == '__main__':
    pre_change = './test_data/t1_rgb/0116.png'
    post_change = './test_data/t2_rgb/0116.png'

    # Load the images
    pre_change_image = np.array(imageio.imread(pre_change))
    post_change_image = np.array(imageio.imread(post_change))
    img_height, img_width, _ = pre_change_image.shape
   
    img_X = np.reshape(pre_change_image, (-1, img_height, img_width))
    img_Y = np.reshape(post_change_image, (-1, img_height, img_width))

    channel, img_height, img_width = img_X.shape

    tic = time.time()

    img_X = np.reshape(img_X, (channel, -1))
    img_Y = np.reshape(img_Y, (channel, -1))
    # when max_iter is set to 1, IRMAD becomes MAD
    mad, can_coo, mad_var, ev_1, ev_2, sigma_11, sigma_22, sigma_12, chi2, noc_weight = IRMAD(img_X, img_Y,
                                                                                              max_iter=10,
                                                                                              epsilon=1e-3)
    sqrt_chi2 = np.sqrt(chi2)

    k_means_bcm = get_binary_change_map(sqrt_chi2)
    k_means_bcm = np.reshape(k_means_bcm, (img_height, img_width)).astype(np.uint8)

    imageio.imwrite('./data/change_map.png', k_means_bcm)
    toc = time.time()
    print(toc - tic)

