# General stuff
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy.fft import fft, ifft
import os
import pathlib


# Audio processing/tools import
import librosa
import librosa.display
from scipy.io.wavfile import read 
from IPython.display import Audio
#REMEMBER you need ffmpeg installed

# other imports
import glob #filesystem manipulation

# Define some decorator functions
import functools
import time

def timer(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'Calling {func.__name__!r}')
        startTime = time.perf_counter()
        value = func(*args, **kwargs)
        endTime = time.perf_counter()
        runTime = endTime - startTime
        print(f'Finished {func.__name__!r} in {runTime:.4f} secs')
        return value
    return wrapper

@timer
def init_data(relPathToFolder):
    # Read in the metadata

    metaData = pd.read_csv(relPathToFolder + 'metadata/UrbanSound8K.csv')

    #recursively add all .wave files to paths list
    paths = list(pathlib.Path(relPathToFolder + 'audio/').glob('**/*.wav'))
    fileNames = paths.copy()

    #remove path from fileNames leaving us just with the raw filename
    for i in range(len(fileNames)):
        fileNames[i] = os.path.basename(fileNames[i].name)

    #create dataframe from paths and filenames
    fileData = pd.DataFrame(list(zip(paths, fileNames)), 
                            columns =['path', 'slice_file_name']) 

    #merge metadata and fileData (the one we just created) dataframes
    fileData = fileData.join(metaData.set_index('slice_file_name'), 
                             on='slice_file_name')
    return fileData

@timer
def test_read_audio(filepath):
    audioFile, samplingRate = load_audio(filepath)

    # Plot librosa audio visualizations
    plt.figure(figsize=(12, 4))
    librosa.display.waveplot(audioFile, sr=samplingRate)

    #plt.figure(figsize=(12, 4))
    #librosa.display.specshow(audioFile)

    # Feature Engineering with Librosa

    #Mel-frequency cepstral coefficients (MFCCs)

    mfccs = librosa.feature.mfcc(y=audioFile, sr=samplingRate,  n_mfcc=40)

    plt.figure(figsize=(10, 4))
    librosa.display.specshow(mfccs, x_axis='time')
    plt.colorbar()
    plt.title('MFCC')
    plt.tight_layout()
    plt.show()

#Params:
# filepath = path to .wav audio file
# various "_exec" parameters = toggle specific feature generation
# flatten = transpose and take mean of (flatten) array
# normalize = normalize arrays
@timer
def generateFeatures(filepath, mfccs_exec, melSpec_exec, stft_exec, chroma_stft_exec, spectral_contrast_stft_exec, tonnetz_exec, 
visFFT_exec, mfccDelta_exec, flatten=True, normalize=True):
    audioFile, sampling_rate = load_audio(filepath)

    featuresDF = pd.DataFrame([filepath], columns=['path'])

    #featuresDF = pd.DataFrame()

    if (mfccs_exec == True):
        #generate mfccs features
        mfccs = mfccsEngineering(audioFile, sampling_rate)
        if(flatten == True):
            #transpose the array and take the mean along axis=0
             mfccs = np.mean(mfccs.T,axis=0)
        if (normalize == True):
            mfccs = norm_audio(mfccs)

        tempList = []
        tempList.append(mfccs)
        featuresDF['mfccs'] = tempList
        print("MFCCS done!")

    if (melSpec_exec == True):
        #generate melSpec features
        melSpec = melSpecEngineering(audioFile, sampling_rate)
        if(flatten == True):
            #transpose the array and take the mean along axis=0
            melSpec = np.mean(melSpec.T,axis=0)     
        if (normalize == True):
            melSpec = norm_audio(melSpec)

        tempList = []
        tempList.append(melSpec)
        featuresDF['melSpec'] = tempList
        print("Mel-scaled spectrogram done!")

    #all 3 of the STFT, chroma_STFT and spectral_contrast_STFT features are based on a STFT feature so it needs to be generated if any are requested
    if (stft_exec == True or chroma_stft_exec == True or spectral_contrast_stft_exec == True):
        #generate stft features
        stft = stftEngineering(audioFile, sampling_rate)
        # NOTE: no flattening (mean and transpose) for STFT. Not entirely sure why
        if (normalize == True):
            stft = norm_audio(stft)
        
        if (stft_exec == True):
            tempList = []
            tempList.append(stft)
            featuresDF['stft'] = tempList
            print("Short-time Fourier transform (STFT) done!")

    if (chroma_stft_exec == True):
        #generate chroma_stft features
        chroma_stft = chroma_stftEngineering(audioFile, sampling_rate, stft)
        if(flatten == True):
            #transpose the array and take the mean along axis=0
            chroma_stft = np.mean(chroma_stft.T,axis=0)
        if (normalize == True):
            chroma_stft = norm_audio(chroma_stft)
        
        tempList = []
        tempList.append(chroma_stft)
        featuresDF['chroma_stft'] = tempList
        print("Chromagram (STFT) done!")

    if (spectral_contrast_stft_exec == True):
        #generate spectral_contrast_stft features
        spectral_contrast_stft = spectral_contrast_stftEngineering(audioFile, sampling_rate, stft)
        if (flatten == True):
            #transpose the array and take the mean along axis=0
            spectral_contrast_stft = np.mean(spectral_contrast_stft.T,axis=0)
        if (normalize == True):
            spectral_contrast_stft = norm_audio(spectral_contrast_stft)
        
        tempList = []
        tempList.append(spectral_contrast_stft)
        featuresDF['spectral_contrast_stft'] = tempList
        print("Spectral contrast (STFT) done!")

    if (tonnetz_exec == True):
        #generate tonnetz features
        tonnetz = tonnetzEngineering(audioFile, sampling_rate)
        if (flatten == True):
            #transpose the array and take the mean along axis=0
            tonnetz = np.mean(tonnetz.T,axis=0)
        if (normalize == True):
            tonnetz = norm_audio(tonnetz)
        
        tempList = []
        tempList.append(tonnetz)
        featuresDF['tonnetz'] = tempList
        print("Tonal centroid features (tonnetz) done!")
    
    if (visFFT_exec == True):
    #generate Viswesh's custom FFT feature
        visFFT = visFFTEngineering(audioFile)
        # if (flatten == True):
        #     #transpose the array and take the mean along axis=0
        #     visFFT = np.mean(visFFT.T,axis=0)
        if (normalize == True):
            visFFT = norm_audio(visFFT)

        tempList = []
        tempList.append(visFFT)
        featuresDF['visFFT'] = tempList
        print("Viswesh's custom FFT feature done!")

    if (mfccDelta_exec == True):
    #generate mfcc Delta feature (3d mfccs thing by Tony)
        mfccDelta = mfccDeltaEngineering(audioFile)
        # if (flatten == True):
        #     #transpose the array and take the mean along axis=0
        #     visFFT = np.mean(visFFT.T,axis=0)
        # if (normalize == True):
        #     mfccDelta = norm_audio(mfccDelta)

        # tempList = []
        # tempList.append(mfccDelta)
        # featuresDF['mfccDelta'] = tempList
        featuresDF['mfccDelta'] = mfccDelta
        print("MFCC Delta feature custom FFT feature done!")

    return featuresDF


@timer
def mfccsEngineering(audioFile, sampling_rate):

    #generate Mel-frequency cepstral coefficients (MFCCs)
    mfccs = librosa.feature.mfcc(y=audioFile, sr=sampling_rate,  n_mfcc=40)

    return mfccs

@timer
def melSpecEngineering(audioFile, sampling_rate):

    #generate a mel-scaled spectrogram
    melSpec = librosa.feature.melspectrogram(audioFile, sr=sampling_rate)

    return melSpec
    
@timer
def stftEngineering(audioFile, sampling_rate):

    #generate Short-time Fourier transform (STFT) feature
    stft = librosa.stft(audioFile)

    #take absolute value of array
    stft = np.abs(stft)

    return stft

@timer
def chroma_stftEngineering(audioFile, sampling_rate, stft):
   
    #generate a chromagram from a waveform or power spectrogram (STFT based)
    chroma_stft = librosa.feature.chroma_stft(S=stft, sr=sampling_rate)

    return chroma_stft

@timer
def spectral_contrast_stftEngineering(audioFile, sampling_rate, stft):
    
    #generate a spectral contrast (from a STFT)
    spectral_contrast_stft = librosa.feature.spectral_contrast(S=stft,sr=sampling_rate)

    return spectral_contrast_stft

@timer
def tonnetzEngineering(audioFile, sampling_rate):

    #Generate harmonic elements
    harmonic = librosa.effects.harmonic(audioFile)
    
    #generate tonal centroid features (tonnetz) from the harmonic component of a song
    tonnetz = librosa.feature.tonnetz(y=harmonic, sr=sampling_rate)

    return tonnetz

@timer
def mfccDeltaEngineering(audioFile):
    features = []
    melspec = librosa.feature.mfcc(audioFile, n_mfcc=40)
    deltas = librosa.feature.delta(melspec)
    combi = np.dstack((melspec, deltas))
    features.append(combi)
    return features

# # Function to plot the waveform (stereo)
# @timer
# def plt_orig_waveform(sampleRate, soundData, channels):
#     if channels == 'mono':
#         soundData = soundData[:,0]
#     clipLength = soundData.shape[0] / sampleRate
#     time = np.linspace(0, clipLength, soundData.shape[0])
#     plt.plot(time, soundData[:, 0], label="Left channel")
#     plt.plot(time, soundData[:, 1], label="Right channel")
#     plt.legend()
#     plt.xlabel("Time [s]")
#     plt.ylabel("Amplitude")
#     plt.show()
#     print(f'Sample rate = {sampleRate}')
#     print(f'Data points = {soundData.shape[0]}')
#     print(f'Number of channels = {soundData.shape[1]}')
#     print(f'Length = {clipLength}s')

#generate an FFT with custom code by Viswesh
@timer
def visFFTEngineering(audioFile):

    #FFT
    ftrans = abs(np.fft.fft(audioFile, n=88200)) #[:round((audio.size/2))])
    ftrans_pos = ftrans[:round(ftrans.size/2)]
    fr = np.fft.fftfreq(len(ftrans))

    # Steps to filter > 0 values in fr
    filter = [] #An empty list for filtering

    fr = fr[fr >= 0]
    #fr = fr.ravel()

    return fr

@timer
def load_audio(filepath):
    y, sr = librosa.load(filepath, sr=22050)
    return y, sr

def norm_audio(data):
    max_data = np.max(data)
    min_data = np.min(data)
    data = (data-min_data)/(max_data-min_data+1e-6)
    return data

def samplerate(filepath):
    x, samplerate = librosa.load(filepath)
    return samplerate

def featurePlot(filepath, fname, classID):
    audioFile, samplingRate = load_audio(filepath)

    # Plot librosa audio visualizations
    
    plt.figure(figsize=(8, 4))
    librosa.display.waveplot(audioFile, sr=samplingRate)
    plt.title('Waveplot')
    plt.tight_layout()
    #plt.show()
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_Waveplot.png')


    #plt.figure(figsize=(8, 4))
    #plt.savefig("./output/featurePlots/" + fname + '_Waveplot.png')

    #plt.figure(figsize=(12, 4))
    #librosa.display.specshow(audioFile)

    # Feature Engineering with Librosa

    #Mel-frequency cepstral coefficients (MFCCs)

    mfccs = mfccsEngineering(audioFile, samplingRate)

    plt.figure(figsize=(8, 4))
    librosa.display.specshow(mfccs, x_axis='time')
    plt.colorbar()
    plt.title('MFCC')
    plt.tight_layout()
    #plt.show()
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_MFCC.png')

    plt.figure(figsize=(8, 4))
 
    plt.figure(figsize=(10, 4))
    #melSpec = sonicboom.melSpecEngineering(audioFile, samplingRate)

    S = librosa.feature.melspectrogram(y=audioFile, sr=samplingRate, n_mels=128, fmax=8000)
    librosa.display.specshow(librosa.power_to_db(S, ref=np.max), y_axis='mel', fmax=8000, x_axis='time')
    plt.colorbar(format='%+2.0f dB')
    plt.title('Mel Spectrogram')
    plt.tight_layout()
    #plt.show()
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_MelSpec.png')


    stft = stftEngineering(audioFile, samplingRate)

    chroma_stft = chroma_stftEngineering(audioFile, samplingRate, stft)

    plt.figure(figsize=(8, 4))
    librosa.display.specshow(chroma_stft)
    plt.title('Chromagram (STFT)')
    #plt.show()
    librosa.display.specshow(chroma_stft, y_axis='chroma', x_axis='time')
    plt.title('Chromagram')
    plt.tight_layout()
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_Chroma_STFT.png')

    #VIS FFT PLOT
    plt.figure(figsize=(8, 4))
    ftrans = abs(np.fft.fft(audioFile, n=88200)) 
    ftrans_pos = ftrans[:round(ftrans.size/2)]
    #fig = plt.figure(frameon=False)
    #fig.set_size_inches(10,10)
    #ax = plt.Axes(fig,[0.,0.,1.,1.])
    #ax.set_axis_off()
    #fig.add_axes(ax)
    fig = plt.plot(ftrans_pos)
    #plt.savefig(img_path, dpi = 25.6)
    plt.title('Fourier Transform')
    plt.xlabel('Frequency')
    plt.tight_layout()
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_FFT.png')

    stft = stftEngineering(audioFile, samplingRate)
    spectral_contrast_stft = spectral_contrast_stftEngineering(audioFile, samplingRate, stft)

    plt.figure(figsize=(8, 4))
    librosa.display.specshow(spectral_contrast_stft, x_axis='time')
    plt.colorbar()
    plt.ylabel('Frequency bands')
    plt.title('Spectral contrast')
    plt.tight_layout()
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_Spec_Cont_STFT.png')

    tonnetz = tonnetzEngineering(audioFile, samplingRate)

    plt.figure(figsize=(8, 4))
    librosa.display.specshow(tonnetz, y_axis='tonnetz')
    plt.colorbar()
    plt.title('Tonal Centroids (Tonnetz)')
    plt.savefig("./output/featurePlots/" + str(classID) + "/" + fname + '_Tonnetz.png')
