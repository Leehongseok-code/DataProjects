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


print(train_df)
#떨군 데이터프레임을 문장으로 합치고, 공백으로 구분
sentenced_df = train_df.apply(lambda x: ' '.join(x), axis=1)

print("sentenced:", sentenced_df)

#print(list(sentenced_df.values))
tokenizer = Tokenizer()
tokenizer.fit_on_texts(sentenced_df)
vocab_size = len(tokenizer.word_index) + 1 # 패딩을 고려하여 +1
print('단어 집합 :',vocab_size)
print('딕셔너리 집합 :', len(tokenizer.index_word.values()))
#각 문장들에 대해 정수 인코딩
encoded_df = tokenizer.texts_to_sequences(sentenced_df)
#print('정수 인코딩 결과 :',encoded_df)
train_x = np.array(encoded_df)


# 단어와 해당 단어의 정수 인덱스 매핑
word_index = tokenizer.word_index

target_index = 5

# 정수 인덱스를 다시 단어로 변환
if target_index is not None:
    original_word = [word for word, index in word_index.items() if index == target_index]
    print(f"The original word for index {target_index}: {original_word[0]}")
else:
    print(f"The word not found in the vocabulary.")



train_y = df[['winner']].values
le_answer = LabelEncoder()
le_answer.fit(train_y)
train_y = le_answer.transform(train_y)
print(train_y)


train_x2 = train_df2

#model = RandomForestClassifier(n_estimators=5, random_state=0)
#print(model)

model.fit([train_x, train_x2], train_y, epochs=100, batch_size=16, validation_split=0.1)
#model.fit(train_x, train_x2, epochs=50, batch_size=16, validation_split=0.1)

#print(model.predict(train_x)[:1])
embedding_map = model.get_layer('token_and_position_embedding').get_weights()[0]
#만약 툭정 input에 대한 임베딩 값을 얻고 싶다면, embedding_map의 인덱스로 넣어주면 된다.
#ex)45번은 제이스이고, 제이스의 임베딩 값을 얻고 싶다면, embedding_map[45]를 하면 된다.


target = embedding_map[target_index]
cos_sims = []
for i in tqdm(range(166)):
    cos_sim = cosine_similarity([target], [embedding_map[i]])
    cos_sims.append(float(np.squeeze(cos_sim)))
#print(cos_sims)
print(np.argsort(cos_sims))#자기자신제외하고 두 번째로 유사도 높은 챔피언 찾기 - 펼쳐서 넣자.
target_encoded_result = np.argsort(cos_sims)[-2]


# 정수 인덱스를 다시 단어로 변환
if target_index is not None:
    original_word = [word for word, index in word_index.items() if index == target_index]
    print(f"원본 챔피언 {target_index}: {original_word[0]}")
else:
    print(f"The word not found in the vocabulary.")

target_index = target_encoded_result
# 정수 인덱스를 다시 단어로 변환
if target_index is not None:
    original_word = [word for word, index in word_index.items() if index == target_index]
    print(f"가장 유사한 챔피언 {target_index}: {original_word[0]}")
else:
    print(f"The word not found in the vocabulary.")

'''
n_feature = 10
index = np.arange(n_feature, 0, -1)
plt.barh(index, model.feature_importances_, align='center')
plt.yticks(index, model.feature_names_in_)
plt.ylim(-1, n_feature)
plt.xlabel('feature importance', size=15)
plt.ylabel('feature', size=15)
plt.show()
'''

# 2차원 t-SNE 임베딩
tsne = TSNE(n_components=2, random_state=42)
tsne_np = tsne.fit_transform(embedding_map)


sentenced_df = sentenced_df.reset_index(drop=True)


# 시각화
plt.scatter(tsne_np[:, 0], tsne_np[:, 1])

tokens = tokenizer.index_word.values()
print(tokenizer.index_word)
#print(tokens)

for i, txt in enumerate(tokens):
    #print(txt)
    plt.annotate(txt, (tsne_np[i, 0], tsne_np[i, 1]))

plt.figure(figsize=(10, 10))
plt.show()