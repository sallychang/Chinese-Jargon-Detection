import pandas as pd
import time
import jieba
import pickle
import pyprind
import numpy as np
import os
import tensorflow as tf
from keras.backend.tensorflow_backend import set_session
from bert4keras.snippets import to_array
from bert4keras.tokenizers import Tokenizer
from bert4keras.models import build_transformer_model
from bert4keras.backend import keras
config = tf.ConfigProto()
# A "Best-fit with coalescing" algorithm, simplified from a version of dlmalloc.
config.gpu_options.allocator_type = 'BFC'
set_session(tf.Session(config=config))
jieba.load_userdict("./userdict.txt")


def coSim(vec1, vec2):
    """
    cosine similarity comparison
    """
    num = vec1.dot(vec2.T)
    denom = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    sim = num / denom
    return sim


def search(corpus, pattern):
    """
    find the position of particular words in the corpus
    """
    positions = []
    col = 0
    for sentence in corpus:
        if pattern in sentence:
            row = sentence.index(pattern)
            pos = (col, row)
            positions.append(pos)
        col += 1
    return positions


def getRow(pos):
    """
    get word's row index from corpus
    """
    return pos[0]


def getColumn(pos):
    """
    get word's column index from corpus
    """
    return pos[1]


if __name__ == '__main__':
    """
    find seed keywords from corpus for relevant criminal
    the corpus and the embedding are one-to-one correspondence
    """

    # read from segmented corpus
    corpus = [line.split() for line in open(
        "./cut.csv", 'r', encoding='utf-8').readlines()]

    # read from contextual embeddings
    with open("./bert_final_emb.pickle", "rb") as f:
        emb = pickle.load(f)

    # load your pretrained model
    config_path = './DC-BERT/bert_config.json'
    checkpoint_path = './DC-BERT/bert_model.ckpt'
    dict_path = './DC-BERT/vocab.txt'

    tokenizer = Tokenizer(
        dict_path, pre_tokenize=lambda s: jieba.cut(s))  # load tokenizer
    model = build_transformer_model(
        config_path, checkpoint_path)  # build DC-BERT model

    # read from remain.txt(generated by filter.py)
    vocab = [line.strip() for line in open(
        "./remain.txt", 'r', encoding='utf-8').readlines()]

    # using an example of drug(毒品)
    KeyW = "毒品"
    token_ids, segment_ids = tokenizer.encode(KeyW)
    KeyV = model.predict([np.array([token_ids]), np.array([segment_ids])])

    pbar = pyprind.ProgBar(len(vocab[3:]), title='进度展示', monitor=True)

    # traverse the vocab and find most similar words for each criminal seed
    # try add them to Keywords.json for your own criminal category
    with open("./scores/dp_scores.txt", "w", encoding='utf-8') as f:
        for word in vocab[3:]:
            positions = search(corpus, word)

            sen_vec = []
            word_vec = []
            scores = []

            # find most semantic-related sentence with criminal seed
            for i in range(len(positions)):
                sentenceEmb = emb[getRow(positions[i])]
                col = getColumn(positions[i])
                if col + 1 >= 511:
                    scores.append(0)
                    continue
                else:
                    wordEmb = sentenceEmb[col + 1]
                    sim = coSim(wordEmb, KeyV[0][1])
                    # print(wordEmb.shape)
                    # print(KeyV[0,0,:].shape)
                    # print(sim)
                    scores.append(sim)
            f.write(word + " ")
            f.write(str(max(scores)) + " ")
            # save the position of the words
            f.write(str(getRow(positions[scores.index(max(scores))])) + "\n")
            pbar.update()
    print(pbar)
