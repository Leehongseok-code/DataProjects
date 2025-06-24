import re
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
from gensim.models import Word2Vec

from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics.pairwise import cosine_similarity
from tensorflow.keras.preprocessing.text import Tokenizer
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from model import model
from tqdm import tqdm

from sklearn.manifold import TSNE

df = pd.read_csv('./DataFrame/MatchDatamaster.csv')

df = df[df["champion0damageRate"]>0]

categorical_features = ["winner"]
for i in range(10):
    categorical_features.append('champion' + str(i))
numeric_features = []
for i in range(10):
    numeric_features.append('champion' + str(i) + 'damageRate')
    numeric_features.append('champion' + str(i) + 'damageTakenRate')


train_df = df[categorical_features]
train_df = train_df.drop(labels = "winner", axis = 1)

train_df2 = df[numeric_features]


#print(train_df)
#drop한 데이터프레임을 문장으로 합치고, 공백으로 구분
sentenced_df = train_df.apply(lambda x: ' '.join(x), axis=1)

#print("sentenced:", sentenced_df)



# 데이터프레임 생성
df = sentenced_df

#print(df)

# 데이터 전처리: 문장 토큰화 및 정규화
normalized_text = []
for sentence in df:
    tokens = re.sub(r"[^a-z0-9]+", " ", sentence.lower())
    #print(tokens)
    normalized_text.append(word_tokenize(tokens))


#print("normalized:", df)
df['tokenized_sentences'] = normalized_text


# Word2Vec 모델 학습
model = Word2Vec(sentences=df['tokenized_sentences'], vector_size=100, window=5, min_count=1, workers=4, sg=0)

# 'tensorflow'에 대한 가장 유사한 단어 출력
model_result = model.wv.most_similar("yone")
print(model_result)


# t-SNE를 사용하여 전체 임베딩 시각화
words = list(model.wv.index_to_key)
vectors = model.wv[words]

tsne = TSNE(n_components=2, random_state=42)
vectors_2d = tsne.fit_transform(vectors)

# 시각화를 위한 데이터프레임 생성
df_tsne = pd.DataFrame(vectors_2d, columns=['x', 'y'])
df_tsne['word'] = words

# 시각화
plt.figure(figsize=(15, 10))
plt.scatter(df_tsne['x'], df_tsne['y'], s=5)
for i, word in enumerate(df_tsne['word']):
    plt.annotate(word, xy=(df_tsne.iloc[i]['x'], df_tsne.iloc[i]['y']), fontsize=8)



plt.title('t-SNE Visualization of Word Embeddings')
plt.show()