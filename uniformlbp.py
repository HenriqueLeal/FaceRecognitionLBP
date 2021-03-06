# Processamento de Imagens Digitais - PPGCC 2018

import cv2
import random
import os, sys
import argparse
import operator
import numpy as np
import scipy.spatial as sp
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from tqdm import tqdm
from algorithms import *
from skimage import feature

numOfClasses = 76
numOfSamplesPerClass = 4

# Função utilizada para dividir uma imagem de entrada
# em 4 sub-imagens;
def getSubImages(subImage):
    height, width = subImage.shape
    
    height = height // 2
    width = width // 2
    
    subImages = []
    subImages.append(subImage[:height, :width])
    subImages.append(subImage[:height, width:])
    subImages.append(subImage[height:, :width])
    subImages.append(subImage[height:, width:])
    return subImages

# Função utilizada para obter todas as imagens do dataset.
# (76 indivíduos (homens), apenas as imagens de 1 - 4);
def getDataset():
    dataset = []
    for i in range(1, 77):
        for j in range(1, 5):
            imgFilename = 'new_m-{0:0=3d}-{1}.bmp'.format(i, j)
            imgContent = cv2.imread(imgFilename)
            imgContent = cv2.cvtColor(imgContent, cv2.COLOR_BGR2GRAY)
            dataset.append(imgContent)
    return dataset

# Função utilizada para obter todas as imagens de teste do dataset.
# (76 indivíduos (homens), apenas as imagens de 14 - 17);
def getTestDataset():
    testDataset = []

    for i in range(1, 77):
        #randomSampleNumber = random.randint(14, 17)
        imgFilename = 'new_m-{0:0=3d}-{1}.bmp'.format(i, 14)
        imgContent = cv2.imread(imgFilename)
        imgContent = cv2.cvtColor(imgContent, cv2.COLOR_BGR2GRAY)
        testDataset.append(imgContent)
    return testDataset

# Função utilizada para calcular a distância de uma amostra ("base")
# em relação à todas as outras (com a func. euclidiana);
def getRelativeDistances(base, descriptors):
    relativeDistances = {}

    for i in range(0, descriptors.shape[0]):
        if i == base: continue
        relativeDistances[i] = cv2.compareHist(np.float32(descriptors[i]), np.float32(descriptors[base]), cv2.HISTCMP_CHISQR) 
        #relativeDistances[i] = sp.distance.cityblock(descriptors[i], descriptors[base])
        #relativeDistances[i] = sp.distance.euclidean(descriptors[i], descriptors[base])

    return relativeDistances

# Análogo ao método acima, porém leva em consideração os histogramas das amostras de teste
# para efetuar o cálculo do CMC posteriormente;
def getRelativeDistancesCMC(base, testHistograms, descriptors):
    relativeDistances = {}

    for i in range(0, descriptors.shape[0]):
        #relativeDistances[i] = cv2.compareHist(np.float32(descriptors[i]), np.float32(testHistograms[base]), cv2.HISTCMP_CHISQR)
        #relativeDistances[i] = sp.distance.cityblock(descriptors[i], testHistograms[base])
        relativeDistances[i] = sp.distance.euclidean(descriptors[i], testHistograms[base])
    return relativeDistances

# Função utilizada para calcular o vetor de PR de uma amostra ("i")
# levando em consideração seu vetor de distâncias relativas calculado
# anteriormente;
def getDescriptorPR(i, sortedRelativeDistances): 
    global numOfSamplesPerClass

    currentDescriptorClass = i // numOfSamplesPerClass
        
    retrievedInClass = 0
    totalRetrieved = 0
    totalInClass = numOfSamplesPerClass - 1
        
    currentDescriptorPR = [0] * (numOfSamplesPerClass - 1)
    for descriptorNumber, relativeDistance in sortedRelativeDistances:
        totalRetrieved += 1
        if (descriptorNumber // numOfSamplesPerClass) == currentDescriptorClass:
            retrievedInClass += 1
            currentDescriptorPR[retrievedInClass - 1] = retrievedInClass / totalRetrieved
    return currentDescriptorPR

if __name__ == '__main__':
    descriptors = []
    
    # Obtém as imagens do dataset.
    # (Apenas homens, 76 indivíduos, sub-imagens de 1 à 4 (luz ambiente));
    dataset = getDataset()
    
    # Para cada sub-imagem de um mesmo indivíduo,
    # cria um processo para calcular o respectivo histograma LBP;
    for i in tqdm(range(0, 304)):
        # Divide cada amostra em 4 sub-imagens para calcular os respectivos histogramas LBP.
        # (Lembrando que eles são concatenados posteriormente em um único histograma);
        subImages = getSubImages(dataset[i])

        concatenatedHistograms = []
        for subImage in subImages:
            # Calcula o LBP da sub-imagem, utilizando o método NRI UNIFORM.
            # São levados em consideração 8 vizinhos e um raio de distância 2.
            # (NRI UNIFORM: Non-Rotational Invariant Uniform);
            lbp = np.float32(feature.local_binary_pattern(subImage, 8, 2, method='nri_uniform'))
            _, histogram = np.unique(lbp, return_counts=True)
            concatenatedHistograms.extend(histogram)

        descriptors.append(concatenatedHistograms)

    descriptors = np.array(descriptors)

    # Realiza o cálculo do vetor PR de cada uma das amostras e,
    # consequentemente, calcula a média deles.
    descriptorsPR = []
    for i in tqdm(range(0, descriptors.shape[0])):
        relativeDistances = getRelativeDistances(i, descriptors)
        sortedRelativeDistances = sorted(relativeDistances.items(), key=operator.itemgetter(1))
        currentDescriptorPR = getDescriptorPR(i, sortedRelativeDistances) 
        descriptorsPR.append(currentDescriptorPR)

    descriptorsPR = np.array(descriptorsPR)
    descriptorsPR_mean = np.mean(descriptorsPR, axis=0)
    
    print('{}| Average Precision x Recall:'.format('LBP'))
    print(descriptorsPR_mean)
    
    # A partir deste ponto, a execução é bem semelhante ao código escrito até aqui.
    # A ideia é gerar um conjunto de teste, calcular os histogramas destas amostras de teste e
    # compará-los com os histogramas mais próximos de cada uma delas, calculando o CMC.

    testHistograms = []
    testRelativeDistances = []
    testDataset = getTestDataset()

    for testSample in tqdm(testDataset):
        subImages = getSubImages(testSample)

        concatenatedHistograms = []
        for subImage in subImages:
            lbp = np.float32(feature.local_binary_pattern(subImage, 8, 2, method='nri_uniform'))
            _, histogram = np.unique(lbp, return_counts=True)
            concatenatedHistograms.extend(histogram)
        
        testHistograms.append(concatenatedHistograms)

    testHistograms = np.array(testHistograms)
    
    for i in tqdm(range(0, testHistograms.shape[0])):
        relativeDistances = getRelativeDistancesCMC(i, testHistograms, descriptors)
        sortedRelativeDistances = sorted(relativeDistances.items(), key=operator.itemgetter(1))
        testRelativeDistances.append(sortedRelativeDistances)
    

    # O trecho de código abaixo calcula efetivamente a curva CMC.
    # Trata-se de um loop que fica iterando repetitivamente sobre as amostras de teste,
    # até que todas elas tenham finalmente encontrado o histograma (de mesma classe) mais próximo.

    isLooping = True
    
    cmcRankings = []
    cmcCurrentRanking = 1
    cmcControl = [False] * numOfClasses
    while isLooping:
        trueCounter = 0
        for i in range(0, numOfClasses):
            if cmcControl[i]:
                trueCounter += 1
                continue

            descriptorNumber, relativeDistance = testRelativeDistances[i][cmcCurrentRanking - 1]
            if (descriptorNumber // numOfSamplesPerClass) == i:
                cmcControl[i] = True
                trueCounter += 1

        if trueCounter == numOfClasses:
            isLooping = False
            cmcRankings.append(1.0)
        else:
            cmcCurrentRanking += 1
            cmcRankings.append(trueCounter / numOfClasses)

    print('{}| CMC Curve:'.format('LBP'))
    print('Total Rankings: {}'.format(cmcCurrentRanking))
    print(cmcRankings)