import librosa
import json
import tensorflow as tf
import joblib
import pandas as pd
import warnings
import numpy as np
from scipy import stats

def columns():
  feature_sizes = dict(
    chroma_cens=12,
    tonnetz=6,
    mfcc=20,
    zcr=1,
    spectral_centroid=1,
    spectral_contrast=7,
  )
  moments = ('mean', 'std', 'skew', 'kurtosis', 'median', 'min', 'max')

  columns = []
  for name, size in feature_sizes.items():
    for moment in moments:
      it = ((name, moment, '{:02d}'.format(i + 1)) for i in range(size))
      columns.extend(it)

  names = ('feature', 'statistics', 'number')
  columns = pd.MultiIndex.from_tuples(columns, names=names)

  return columns.sort_values()

def compute_features(x, sr):
    features = pd.Series(index=columns(), dtype=np.float32)
    warnings.filterwarnings('error', module='librosa')
        
    def feature_stats(name, values):
        features.loc[(name, 'mean')] = np.mean(values, axis=1)
        features.loc[(name, 'std')] = np.std(values, axis=1)
        features.loc[(name, 'skew')] = stats.skew(values, axis=1)
        features.loc[(name, 'kurtosis')] = stats.kurtosis(values, axis=1)
        features.loc[(name, 'median')] = np.median(values, axis=1)
        features.loc[(name, 'min')] = np.min(values, axis=1)
        features.loc[(name, 'max')] = np.max(values, axis=1)

    f = librosa.feature.zero_crossing_rate(x, frame_length=2048, hop_length=512)
    feature_stats('zcr', f)

    cqt = np.abs(librosa.cqt(x, sr=sr, hop_length=512, bins_per_octave=12,
                                n_bins=7*12, tuning=None))
    assert cqt.shape[0] == 7 * 12
    assert np.ceil(len(x)/512) <= cqt.shape[1] <= np.ceil(len(x)/512)+1

    f = librosa.feature.chroma_cens(C=cqt, n_chroma=12, n_octaves=7)
    feature_stats('chroma_cens', f)
    f = librosa.feature.tonnetz(chroma=f)
    feature_stats('tonnetz', f)
    cqt = None
    
    stft = np.abs(librosa.stft(x, n_fft=2048, hop_length=512))
    assert stft.shape[0] == 1 + 2048 // 2
    assert np.ceil(len(x)/512) <= stft.shape[1] <= np.ceil(len(x)/512)+1
    x = None

    f = librosa.feature.spectral_centroid(S=stft)
    feature_stats('spectral_centroid', f)
    f = librosa.feature.spectral_contrast(S=stft, n_bands=6)
    feature_stats('spectral_contrast', f)

    mel = librosa.feature.melspectrogram(sr=sr, S=stft**2)
    stft = None

    f = librosa.feature.mfcc(S=librosa.power_to_db(mel), n_mfcc=20)
    feature_stats('mfcc', f)
    
    f = None
    return (features)

def find_genre(y, sr):
    features = compute_features(y, sr)
    print(features)
    columns = ['mfcc', 'spectral_contrast', 'chroma_cens', 'spectral_centroid', 'zcr', 'tonnetz']
    features = features.loc[columns]
    transposed_df = pd.DataFrame(features.values.reshape(1, -1),
                                columns=features.index)
    features = pipe.transform(transposed_df)
    features = np.array(features, dtype=np.float32)

    input_shape = input_details[0]['index']
    interpreter.set_tensor(input_shape, features)

    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    preds = np.argsort(output_data.reshape(-1))
    features = None
    transposed_df = None
    return enc.inverse_transform(preds)[::-1]


# y, sr = librosa.load("/Users/kaavyamahajan/Downloads/Queen - I Want To Break Free (Official Video).mp3")
# print(y.tolist())
