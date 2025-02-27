
import numpy as np

from sklearn.cluster import KMeans
from numpy.linalg import inv, eig
from scipy.stats import chi2

from utils import covw



def IRMAD(img_X, img_Y, max_iter=50, epsilon=1e-3):
    bands_count_X, num = img_X.shape

    weight = np.ones((1, num))  # (1, height * width)
    can_corr = 100 * np.ones((bands_count_X, 1))
    for _iter in range(max_iter):
        mean_X = np.sum(weight * img_X, axis=1, keepdims=True) / np.sum(weight)
        mean_Y = np.sum(weight * img_Y, axis=1, keepdims=True) / np.sum(weight)

        # centralization
        center_X = img_X - mean_X
        center_Y = img_Y - mean_Y

        # also can use np.cov, but the result would be sightly different with author' result acquired by MATLAB code
        cov_XY = covw(center_X, center_Y, weight)
        size = cov_XY.shape[0]
        sigma_11 = cov_XY[0:bands_count_X, 0:bands_count_X]  # + 1e-4 * np.identity(3)
        sigma_22 = cov_XY[bands_count_X:size, bands_count_X:size]  # + 1e-4 * np.identity(3)
        sigma_12 = cov_XY[0:bands_count_X, bands_count_X:size]  # + 1e-4 * np.identity(3)
        sigma_21 = sigma_12.T

        target_mat = np.dot(np.dot(np.dot(inv(sigma_11), sigma_12), inv(sigma_22)), sigma_21)
        eigenvalue, eigenvector_X = eig(target_mat)  # the eigenvalue and eigenvector of image X
        # sort eigenvector based on the size of eigenvalue
        eigenvalue = np.sqrt(eigenvalue)

        idx = eigenvalue.argsort()
        eigenvalue = eigenvalue[idx]

        if (_iter + 1) == 1:
            print('Canonical correlations')
        print(eigenvalue)

        eigenvector_X = eigenvector_X[:, idx]

        eigenvector_Y = np.dot(np.dot(inv(sigma_22), sigma_21), eigenvector_X)  # the eigenvector of image Y

        # tune the size of X and Y, so the constraint condition can be satisfied
        norm_X = np.sqrt(1 / np.diag(np.dot(eigenvector_X.T, np.dot(sigma_11, eigenvector_X))))
        norm_Y = np.sqrt(1 / np.diag(np.dot(eigenvector_Y.T, np.dot(sigma_22, eigenvector_Y))))
        eigenvector_X = norm_X * eigenvector_X
        eigenvector_Y = norm_Y * eigenvector_Y

        mad_variates = np.dot(eigenvector_X.T, center_X) - np.dot(eigenvector_Y.T, center_Y)  # (6, width * height)

        if np.max(np.abs(can_corr - eigenvalue)) < epsilon:
            break
        can_corr = eigenvalue
        # calculate chi-square distance and probability of unchanged
        mad_var = np.reshape(2 * (1 - can_corr), (bands_count_X, 1))
        chi_square_dis = np.sum(mad_variates * mad_variates / mad_var, axis=0, keepdims=True)
        weight = 1 - chi2.cdf(chi_square_dis, bands_count_X)

    if (_iter + 1) == max_iter:
        print('the canonical correlation may not be converged')
    else:
        print('the canonical correlation is converged, the iteration is %d' % (_iter + 1))

    return mad_variates, can_corr, mad_var, eigenvector_X, eigenvector_Y, \
           sigma_11, sigma_22, sigma_12, chi_square_dis, weight


def get_binary_change_map(data):
    """
    get binary change map
    :param data:
    :param method: cluster method
    :return: binary change map
    """

    cluster_center = KMeans(n_clusters=2, max_iter=1500, n_init='auto').fit(data.T).cluster_centers_.T  # shape: (1, 2)
    # cluster_center = k_means_cluster(weight, cluster_num=2)
    print('k-means cluster is done, the cluster center is ', cluster_center)
    dis_1 = np.linalg.norm(data - cluster_center[0, 0], axis=0, keepdims=True)
    dis_2 = np.linalg.norm(data - cluster_center[0, 1], axis=0, keepdims=True)

    bcm = np.copy(data)  # binary change map
    if cluster_center[0, 0] > cluster_center[0, 1]:
        bcm[dis_1 > dis_2] = 0
        bcm[dis_1 <= dis_2] = 255
    else:
        bcm[dis_1 > dis_2] = 255
        bcm[dis_1 <= dis_2] = 0

    return bcm
