import cv2
import numpy as np
import imageio.v2 as imageio

from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from collections import Counter
from PIL import Image

def find_vector_set(diff_image, new_size):
    i = 0
    j = 0
    vector_set = np.zeros((int(new_size[0] * new_size[1] / 25), 25))

    print('\nvector_set shape', vector_set.shape)

    while i < vector_set.shape[0]:
        while j < new_size[0]:
            k = 0
            while k < new_size[1]:
                block = diff_image[j:j+5, k:k+5]
                feature = block.ravel()
                vector_set[i, :] = feature
                k = k + 5
            j = j + 5
        i = i + 1

    mean_vec = np.mean(vector_set, axis=0)
    vector_set = vector_set - mean_vec

    return vector_set, mean_vec

def find_FVS(EVS, diff_image, mean_vec, new):
    i = 2
    feature_vector_set = []

    while i < new[0] - 2:
        j = 2
        while j < new[1] - 2:
            block = diff_image[i-2:i+3, j-2:j+3]
            feature = block.flatten()
            feature_vector_set.append(feature)
            j = j + 1
        i = i + 1

    FVS = np.dot(feature_vector_set, EVS)
    FVS = FVS - mean_vec
    print("\nfeature vector space size", FVS.shape)
    return FVS

def clustering(FVS, components, new):
    kmeans = KMeans(components, verbose=0)
    kmeans.fit(FVS)
    output = kmeans.predict(FVS)
    count = Counter(output)

    least_index = min(count, key=count.get)
    print(new[0], new[1])
    change_map = np.reshape(output, (new[0] - 4, new[1] - 4))

    return least_index, change_map

def find_change_map(image1, image2):
    
    print(image1.shape, image2.shape)

    new_size = np.asarray(image1.shape) / 5
    new_size = new_size.astype(int) * 5

    image1 = np.array(Image.fromarray(image1).resize((new_size[1], new_size[0]), Image.BICUBIC)).astype(np.int16)
    image2 = np.array(Image.fromarray(image2).resize((new_size[1], new_size[0]), Image.BICUBIC)).astype(np.int16)

    diff_image = abs(image1 - image2)
    diff_image = (diff_image - diff_image.min()) / (diff_image.max() - diff_image.min()) * 255
    diff_image = diff_image.astype(np.uint8)
    
    print('\nBoth images resized to ', new_size)

    vector_set, mean_vec = find_vector_set(diff_image, new_size)

    pca = PCA()
    pca.fit(vector_set)
    EVS = pca.components_

    FVS = find_FVS(EVS, diff_image, mean_vec, new_size)

    print('\ncomputing k means')

    components = 3
    least_index, change_map = clustering(FVS, components, new_size)

    change_map[change_map == least_index] = 255
    change_map[change_map != 255] = 0

    change_map = change_map.astype(np.uint8)
    kernel = np.asarray(((0, 0, 1, 0, 0),
                         (0, 1, 1, 1, 0),
                         (1, 1, 1, 1, 1),
                         (0, 1, 1, 1, 0),
                         (0, 0, 1, 0, 0)), dtype=np.uint8)
    clean_change_map = cv2.erode(change_map, kernel)
    
    return change_map, clean_change_map

if __name__ == "__main__":
    pre_change = './data/CubbieStation_1987.jpg'
    post_change = './data/CubbieStation_2013.jpg'
    pre_change_image = np.array(imageio.imread(pre_change))
    post_change_image = np.array(imageio.imread(post_change))
    change_map, clean_change_map = find_change_map(pre_change_image, post_change_image)
    imageio.imwrite("./data/changemap.jpg", change_map)
    imageio.imwrite("./data/cleanchangemap.jpg", clean_change_map)