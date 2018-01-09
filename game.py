#!/usr/bin/env python

import random
import functools
from itertools import compress

import sys
sys.path.append("../train")
import checkers


def memoize(func):
    ''' Decorator to cache results of a method '''
    # Ref: https://medium.com/@nkhaja/32f607439f84
    cache = func.cache = {}
    @functools.wraps(func)  # noqa
    def memoized_func(*args):
        key = tuple(args)
        if key not in cache:
            cache[key] = func(*args)
        return cache[key]
    return memoized_func


class Game:
    ''' Interface for a game used by alphazero '''
    def start(self):
        ''' Return a start state (player1 always starts) '''
        raise NotImplementedError()

    def valid(self, state):
        ''' Return a boolean array of action validity '''
        raise NotImplementedError()

    def step(self, state, action):
        '''
        Return a tuple of (next_state, next_player, outcome):
            next_state - next game state else None (if game is over)
            next_player - 1 if player1, -1 if player2 (None if game is over)
            outcome - None if game is not yet finished
                      0 if game is a draw
                      1 if first player won
                      -1 if first player lost
        '''
        raise NotImplementedError()

    def human(self, state):
        ''' Print out a human-readable state '''
        return str(state)


class Count(Game):
    '''
    Count up from 0
    State: last number counted (starts at 0)
    Action: next number to count
    '''
    def start(self):
        return (0,)

    def valid(self, state):
        return (True,) * 3

    def step(self, state, action):
        if state[0] + 1 == action:
            if action == 2:
                return None, None, +1  # Win
            return (action,), 1, None  # Next
        return None, None, -1  # Lose


class Narrow(Game):
    '''
    Fewer choices every step
    State: number of choices in this step
    Action: number of choices in the next step
    '''
    def start(self):
        return (3,)

    def valid(self, state):
        return tuple(i < state[0] for i in range(3))

    def step(self, state, action):
        assert action < state[0]
        if action == 0:
            return None, None, -1
        return (action,), 1, None


class Bandit(Game):
    '''
    Perfect-information slot machine:
    State: Action which wins (all other actions lose)
    Action: Which lever to pull
    '''
    def start(self):
        return (random.randint(0, 9),)

    def valid(self, state):
        return (True,) * 10

    def step(self, state, action):
        return None, None, +1 if state[0] == action else -1


class RockPaperScissors(Game):
    '''
    Turn-based Rock-Paper-Scissors (second player should always win)
    State: -1: First players turn, 0: rock, 1: paper, 2: scissors
    Actions: 0: rock, 1: paper, 2: scissors
    '''
    def start(self):
        return (-1,)

    def valid(self, state):
        return (True,) * 3

    def step(self, state, action):
        if state[0] < 0:
            return (action,), -1, None
        if state[0] == action:
            return None, None, 0  # Draw
        if state[0] == (action - 1) % 3:
            return None, None, -1  # P2 Wins
        if state[0] == (action + 1) % 3:
            return None, None, 1  # P1 Wins

    def human(self, state):
        return {-1: 'Start', 0: 'Rock', 1: 'Paper', 2: 'Scissors'}[state[0]]


class TicTacToe(Game):
    '''
    Tic-Tac-Toe
    State: 10 vector of all 9 positions in order, then player number
    Actions: Board position to play in
    '''
    START = (0,) * 9
    WINS = ((0, 1, 2), (0, 3, 6), (0, 4, 8), (1, 4, 7),
            (2, 4, 6), (2, 5, 8), (3, 4, 5), (6, 7, 8))

    def start(self):
        return self.START

    @memoize
    def valid(self, state):
        return tuple(s == 0 for s in state)

    @memoize
    def step(self, state, action):
        assert state[action] == 0, 'Bad step {} {}'.format(state, action)
        player = -1 if sum(state) else 1
        board = tuple(player if i == action else s for i, s in enumerate(state))
        for a, b, c in self.WINS:
            if board[a] == board[b] == board[c] == player:
                result = None, None, player
                break
        else:
            if 0 not in board:
                result = None, None, 0  # Draw, no more available moves
            else:
                result = board, -player, None
        return result

    def human(self, state):
        s = ''
        for i in range(0, 9, 3):
            s += '\n' + ' '.join(str(c) for c in state[i: i + 3])
        return s


class Checkers(Game):

    def start(self):
        return checkers.Board()

    def player_type(self, player):
        if player == 1:
            return 'white'
        elif player == -1:
            return 'black'

        raise ValueError('Invalid player value %s' % player)

    def valid(self, state):
        """Arguments:
            state: (player, board)
        """
        player, board = state
        return board.valid_moves(self.player_type(player))

    def step(self, state, action):
        """Arguments:
            FIXME(prattmic): These need to be the actual numpy planes.
            state: (player, board)
            action: (from, to) or None to pass
        """
        player, board = state

        # Don't mutate old board.
        board = board.copy()

        illegal = board.update(action, self.player_type(player))
        if illegal:
            raise ValueError('Illegal move %s on %s' % (action, board.state))


def play(game):
    print('Playing:', type(game))
    print('Doc:', game.__doc__)
    state = game.start()
    while state is not None:
        valid = game.valid(state)
        print('State:', game.human(state))
        print('Valid:', list(compress(range(len(valid)), valid)))
        action = int(input('Move:'))
        state, outcome = game.step(state, action)
    print('Outcome:', outcome)


games = [Count, Narrow, Bandit, RockPaperScissors, TicTacToe]


if __name__ == '__main__':
    play(Count())
