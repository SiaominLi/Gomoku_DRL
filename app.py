from flask import Flask, jsonify, request, session, render_template
import torch
import random
import numpy as np
import math

app = Flask(__name__)
app.secret_key = 'vropese'  # 設置一個安全的密鑰

# MCTS參數
EXPLORATION_CONSTANT = 1.4  # 探索常數
SIMULATION_COUNT = 400  # 模擬次數


class State:
    def __init__(self, board, player):
        self.board = board
        self.player = player
        self.winner = None
        self.moves = self.get_available_actions()

    def get_available_actions(self):
        actions = []
        for i in range(15):
            for j in range(15):
                if self.board[i][j] == 0:
                    actions.append((i, j))
        return actions

    def take_action(self, action):
        i, j = action
        self.board[i][j] = self.player
        self.player = -self.player
        self.winner, _ = check_game_over(self.board)
        self.moves = self.get_available_actions()

    def is_terminal(self):
        return self.winner is not None or len(self.moves) == 0

    def simulate(self):
        state = State(np.copy(self.board), self.player)
        while not state.is_terminal():
            action = random.choice(state.moves)
            state.take_action(action)
        return state.winner


class Node:
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = []
        self.visits = 0
        self.value = 0

    def expand(self):
        for action in self.state.moves:
            new_state = State(np.copy(self.state.board), self.state.player)
            new_state.take_action(action)
            self.children.append(Node(new_state, self, action))

    def select_child(self):
        total_visits = sum(child.visits for child in self.children)
        log_total_visits = math.log(total_visits)

        best_score = -float('inf')
        best_child = None
        for child in self.children:
            if child.visits == 0:
                score = float('inf')
            else:
                exploitation = child.value / child.visits
                exploration = math.sqrt(log_total_visits / child.visits)
                score = exploitation + EXPLORATION_CONSTANT * exploration

            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def backpropagate(self, result):
        self.visits += 1
        self.value += result
        if self.parent:
            self.parent.backpropagate(result)


def mcts(state):
    root = Node(state)
    for _ in range(SIMULATION_COUNT):
        node = root
        while node.children:
            node = node.select_child()
        if not node.state.is_terminal():
            node.expand()
            node = random.choice(node.children)
        result = node.state.simulate()
        node.backpropagate(result)

    best_child = max(root.children, key=lambda child: child.visits)
    return best_child.action


def ai_move(board):
    state = State(np.array(board), -1)
    action = mcts(state)
    return action


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/result')
def result():
    return render_template('result.html')


@app.route('/api/start', methods=['POST'])
def start_game():
    session['game_state'] = {
        'board': [[0] * 15 for _ in range(15)],
        'player_turn': True,
        'game_over': False,
        'winner': None
    }
    return jsonify(session['game_state'])


@app.route('/api/play', methods=['POST'])
def play():
    game_state = session.get('game_state')

    if game_state and not game_state['game_over']:
        data = request.get_json()
        row, col = data['row'], data['col']
        if game_state['board'][row][col] == 0:
            game_state['board'][row][col] = 1 if game_state['player_turn'] else -1
            game_state['player_turn'] = not game_state['player_turn']

            winner, winning_cells = check_game_over(game_state['board'])
            if winner is not None:
                game_state['game_over'] = True
                game_state['winner'] = winner
                game_state['winning_cells'] = winning_cells
                return jsonify(game_state)


            # TODO: 在這裡添加AI落子的邏輯

            if not game_state['game_over'] and not game_state['player_turn']:
                ai_pos = ai_move(game_state['board'])
                if ai_pos:
                    ai_row, ai_col = ai_pos
                    game_state['board'][ai_row][ai_col] = -1
                    game_state['player_turn'] = True

                    winner, winning_cells = check_game_over(game_state['board'])
                    if winner is not None:
                        game_state['game_over'] = True
                        game_state['winner'] = winner
                        game_state['winning_cells'] = winning_cells
            else:
                return jsonify({'error': 'Invalid move'}), 400

    session['game_state'] = game_state

    return jsonify(game_state)


def check_game_over(board):

    # 檢查行
    for i in range(15):
        for j in range(11):
            if board[i][j] != 0 and board[i][j] == board[i][j + 1] == board[i][j + 2] == board[i][j + 3] == board[i][
                    j + 4]:
                return board[i][j], [(i, j), (i, j + 1), (i, j + 2), (i, j + 3), (i, j + 4)]

    # 檢查列
    for i in range(11):
        for j in range(15):
            if board[i][j] != 0 and board[i][j] == board[i + 1][j] == board[i + 2][j] == board[i + 3][j] == \
                    board[i + 4][j]:
                return board[i][j], [(i, j), (i + 1, j), (i + 2, j), (i + 3, j), (i + 4, j)]

    # 檢查主對角線
    for i in range(11):
        for j in range(11):
            if board[i][j] != 0 and board[i][j] == board[i + 1][j + 1] == board[i + 2][j + 2] == board[i + 3][j + 3] == \
                    board[i + 4][j + 4]:
                return board[i][j], [(i, j), (i + 1, j + 1), (i + 2, j + 2), (i + 3, j + 3), (i + 4, j + 4)]

    # 檢查副對角線
    for i in range(11):
        for j in range(4, 15):
            if board[i][j] != 0 and board[i][j] == board[i + 1][j - 1] == board[i + 2][j - 2] == board[i + 3][j - 3] == \
                    board[i + 4][j - 4]:
                return board[i][j], [(i, j), (i + 1, j - 1), (i + 2, j - 2), (i + 3, j - 3), (i + 4, j - 4)]

    # 檢查是否平局
    for i in range(15):
        for j in range(15):
            if board[i][j] == 0:
                return None, None

    return 0, None

if __name__ == '__main__':
    app.run(port=8000, debug=True)