#!/usr/bin/env python

import numpy as np


def view2obs(view, player):
    full_view = view + (player,)
    obs = np.array(full_view, dtype=float)
    return obs


def softmax(x, mask=1):
    e = np.exp(x - x.max()) * mask
    s = e.sum()
    return e / s


def sample(logits, valid=1):
    probs = softmax(logits, valid)
    return np.random.choice(range(len(probs)), p=probs)
