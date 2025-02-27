﻿# Satellite Image Land Cover Segmentation using U-net (Modified for change detection - Stage 1 - Forest loss) [In progress]
## Forest Loss

The original idea is to perform change detection by predicting two images from different times but same location. Then the work will be split in two stages:
 - Part 1: detect forest loss from t1 to t2.
 This produces a change detection mask from forest to no forest, by extracting the predicted pixels that correspond to forest and obtaining the difference from t1 to t2.
 - Part 2: Detect multiple labels from places that used to have forest in t1 and don't have forest anyore in t2.
 [Not developed yet]

### To run Stage 1

#### Data
Arrange your folders like this

```
data/
├── images/
│   └── t1/
│   └── t2/
└── masks/
    └── change_masks_true/
```

Where t1 and t2 contain the images of the same areas at different time points, and change masks are our ground truth change masks.

#### Run
```
python predict.py --model checkpoints/CP_epoch30.pth --input data/images/t1 --output data/masks/t1/predictions/full --scale 1
python predict.py --model checkpoints/CP_epoch30.pth --input data/images/t2 --output data/masks/t2/predictions/full --scale 1
```
This will create two folder with the corresponding predictions, including all available labels (for this stage we will only use the forest label, but later on I'll try to use all of them, so it doesn't make sense to remove them right now).

Next, we will crete masks only for the forest predictions (again, this could be done easily but it's still in progress)
```
python extract_forest.py --input data/masks/t1/predictions/full --output data/masks/t1/predictions/forest
python extract_forest.py --input data/masks/t2/predictions/full --output data/masks/t2/predictions/forest
```

Now, we'll get only the places where t1 showed the existence of forest but it's not present in t2. This is the "Forest loss".
```
python detect_change_single_label.py --t1 data/masks/t1/predictions/forest --t2 data/masks/t2/predictions/forest --output data/masks/changes/forest_loss
```

Then we can evaluate against our ground truth, the change_masks.
```
python evaluate_change_detection.py --pred data/masks/changes/forest_loss --true data/masks/change_masks
```
This will create a metrics.txt file with the corresponding average metrics for these forest loss predictions.

Currently, the performance is not good but the ground truths we have at this point are not actually forest loss masks, but general change masks, so we can't knoe actually how well it works. We will try to use better datasets for the next part, and surely finetuning the model to get better results.



## Original

This GitHub repository is developed by Srimannarayana Baratam and Georgios Apostolides as a part of Computer Vision by Deep Learning (CS4245) course offered at TU Delft. The implementation of the code was done using PyTorch, it uses U-net architecture to perform multi-class semantic segmentation.  The repository from which our implementation has been derived can be found [[here]](https://github.com/milesial/Pytorch-UNet). A well articulated blog is also available [[here]](https://baratam-tarunkumar.medium.com/land-cover-classification-with-u-net-aa618ea64a1b) for the project by the authors of this repository.

## Google Colab Wrapper
For testing the repository, a google colab wrapper is also provided which explains in detail how to execute the code along with insights. Just download the "colab_wrapper.ipynb" file from the repository and open in your colab. Instructions are available there to clone this repository directly to your drive and train using GPU runtime.

## Dataset
The dataset we used is taken from the DeepGlobe Challenge of Land Cover Segmentation in 2018. [[DeepGlobeChallenges]](http://deepglobe.org/challenge.html)  However, the server for the challenge is no longer available for submission and evaluation of solutions. [[DeepGlobe2018 Server]](https://competitions.codalab.org/competitions/18468) and the validation and test set are not accompanied by labels. For this reason we are using **only the training set**  of the challenge and we are further splitting it into validation and test set to be able to evaluate our solution.  The original dataset can be downloaded from Kaggle [[DeepGLobe2018 Original Dataset]](https://www.kaggle.com/balraj98/deepglobe-land-cover-classification-dataset) here and the dataset we use can be downloaded from [[Link]](https://www.kaggle.com/geoap96/deepglobe2018-landcover-segmentation-traindataset) separated into the training/validation and test set we used for our model.

## Files Explanation
In this section we will present the different files inside the repository as well as an explanation about their functionality


|File Name| Explanation / Function |
|---------|------------|
|`U-net_markdown.ipynb`<img width=90/>| Used as a wrapper to run the train and predict scripts.|
|`train.py` | Used for the training of the network.  |
|`predict.py`|Used to perform a prediction on the test dataset. |
|`diceloss.py` | It's a function used to calculate the dice loss.|
|`classcount.py`| Calculates the weights to be used for the weighted cross entropy by counting the pixel number of each class in the train dataset.|
|`distribution.py`| Used to evaluate the pixel numbers of the validation and training set and visualize them via  bar chart.|
|`dataset.py`| Used as a data loader during the training phase.|

## Training

The following flags can be used while training the model.

<ins>_Guidelines_<ins>

`-f` : Used to load a model already stored in memory. \
`-e` : Used to specify the Number of training epochs. \
`-l` : Used to specify the learning rate to be used for training. \
`-b` : Used to specify the batch size. \
`-v` : Used to specify the percentage of the validation split (1-100). \
`-s` : Used to specify the scale of the image to be used for training.

<ins>_Example:_<ins/>

Training the model for 100 epochs using 20% of the data as a validation split, learning rate is 4x10^-5, batch size is 2 and image scale is 20%

`!python3 train.py -e 100 -v 20.0 -l 4e-5 -b 2 -s 0.2`

## Prediction
<ins>_Guidelines_<ins>

`-m` : Used to specify the directory to the model. \
`-i` : Used to specify the directory of the images to test the model on. \
`-o` : Used to specify the directory in which the predictions will be outputted. \
`-s` : Used to specify the scale of the images to be used for predictions. \
`--viz:` Saves the predictions in the form of an image. \
(For best results used the same scale you used for training the model)

_Note:_ Inference of scale 0.2 takes approximately 10 minutes.

<ins>_Example_<ins>

Making a prediction on the full test set dataset using 30 epoch model trained on full data using a scale of 20%. The script  outputs the IoU score of the model.

```
%%time
!python predict.py -m data/checkpoints/model_ep30_full_data.pth -i data/<test_set_directory>/* -o predictions/ -s 0.2 --viz
```

