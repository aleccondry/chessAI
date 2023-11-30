import chess
import chess.svg
import chess.polyglot
import chess.pgn
import chess.engine
import random
import tensorflow as tf
from keras import layers, models, optimizers, callbacks
from keras.callbacks import ModelCheckpoint
import numpy as np
import os

squares_index = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}


def square_to_index(square):
    letter = chess.square_name(square)
    return 8 - int(letter[1]), squares_index[letter[0]]


def split_dims(board):
    # this is the 3d matrix
    board3d = np.zeros((14, 8, 8), dtype=np.int8)
    for piece in chess.PIECE_TYPES:
        for square in board.pieces(piece, chess.WHITE):
            idx = np.unravel_index(square, (8, 8))
            board3d[piece - 1][7 - idx[0]][idx[1]] = 1
        for square in board.pieces(piece, chess.BLACK):
            idx = np.unravel_index(square, (8, 8))
            board3d[piece + 5][7 - idx[0]][idx[1]] = 1
        aux = board.turn
        board.turn = chess.WHITE
        for move in board.legal_moves:
            i, j = square_to_index(move.to_square)
            board3d[12][i][j] = 1
        board.turn = chess.BLACK
        for move in board.legal_moves:
            i, j = square_to_index(move.to_square)
            board3d[13][i][j] = 1
    board.turn = aux
    return board3d


def analyze_stockfish(board, depth):
    with chess.engine.SimpleEngine.popen_uci('../engines/stockfish-windows-x86-64-avx2.exe') as sf:
        result = sf.analyse(board, chess.engine.Limit(depth=depth))
        score = result['score'].white().score()
        return score


def create_chess_model(conv_size, conv_depth):
    board3d = layers.Input(shape=(14, 8, 8))

    # adding the convolutional layers
    x = board3d
    for _ in range(conv_depth):
        x = layers.Conv2D(filters=conv_size, kernel_size=3, padding='same', activation='relu')(x)
    x = layers.Flatten()(x)
    x = layers.Dense(64, 'relu')(x)
    x = layers.Dense(1, 'sigmoid')(x)

    model = models.Model(inputs=board3d, outputs=x)
    return model


def get_dataset(new_data=False):
    if new_data or not os.path.exists("../data/board_data.npy") or not os.path.exists("../data/eval_data.npy"):
        print("Creating Dataset")
        x, y = create_dataset()
    else:
        x, y = load_dataset()
    return x, y


def create_dataset():
    pgns = open('../data/lichess_db_standard_rated_2017-02.pgn')
    board_arr = []
    eval_arr = []

    # checkpointing
    i = 0
    checkpoint = 10000
    while i < checkpoint:
        g = chess.pgn.read_game(pgns)
        i += 1
    print("Done checkpointing")
    i += checkpoint
    # TODO: FINISH CHECKPOINTING BEFORE RERUNNING
    while True:
        if i % 20 == 0:
            print(f'{i}')
            if i % 1000 == 0 and i != 0:
                print(f'{i}: Saving data')
                np.save(f"../data/neural_data/board_data{i}.npy", board_arr)
                save_eval_arr = np.asarray(np.array(eval_arr) / np.abs(eval_arr).max() / 2 + 0.5, dtype=np.float32)
                np.save(f"../data/neural_data/eval_data{i}.npy", save_eval_arr)
        g = chess.pgn.read_game(pgns)
        if g is None:
            break
        b = g.board()
        num_moves = sum(1 for _ in g.mainline_moves())
        if num_moves < 5:
            continue
        limit = random.randint(1, num_moves - 1)
        for idx, move in enumerate(g.mainline_moves()):
            b.push(move)
            if limit == idx:
                break
        e = analyze_stockfish(b, 3)
        if e is None:
            continue
        board_arr.append(split_dims(b))
        eval_arr.append(e)
        i += 1
    board_arr = np.array(board_arr)
    eval_arr = np.asarray(np.array(eval_arr) / np.abs(eval_arr).max() / 2 + 0.5, dtype=np.float32) # normalization
    np.save("../data/board_data.npy", board_arr)
    np.save("../data/eval_data.npy", eval_arr)
    return board_arr, eval_arr


def load_dataset():
    return np.load("../data/neural_data/board_data10000.npy", allow_pickle=True), \
           np.load("../data/neural_data/eval_data10000.npy", allow_pickle=True)


def train_model(model, x_train, y_train):
    model.compile(optimizer=optimizers.Adam(5e-4), loss='mean_squared_error')
    model.summary()
    checkpoint_filepath = '../engines/checkpoints/'
    model_checkpointing_callback = ModelCheckpoint(
        filepath=checkpoint_filepath,
        save_best_only=True,
    )
    model.fit(x_train, y_train,
              batch_size=256,
              epochs=20,
              verbose=1,
              validation_split=0.1,
              callbacks=[callbacks.ReduceLROnPlateau(monitor='loss', patience=10),
                         callbacks.EarlyStopping(monitor='loss', patience=15, min_delta=1e-4),
                         model_checkpointing_callback])
    model.save('../engines/nn_model.keras')


class NeuralEngine:
    def __init__(self, model):
        self.model = model

    def selectmove(self, board, depth=1):
        max_move = None
        max_eval = -np.inf
        for move in board.legal_moves:
            board.push(move)
            curr_eval = self.minimax(board, depth)
            board.pop()
            if curr_eval > max_eval:
                max_eval = curr_eval
                max_move = move
        return max_move

    def eval_board(self, board):
        board3d = split_dims(board)
        board3d = np.expand_dims(board3d, 0)
        return self.model(board3d)[0][0]

    def minimax(self, board, depth):
        if depth == 0 or board.is_game_over():
            return self.eval_board(board)

        if board.turn == chess.WHITE:
            max_eval = -np.inf
            for move in board.legal_moves:
                board.push(move)
                curr_eval = self.minimax(board, depth - 1)
                board.pop()
                max_eval = max(max_eval, curr_eval)
            return max_eval
        else:
            min_eval = np.inf
            for move in board.legal_moves:
                board.push(move)
                curr_eval = self.minimax(board, depth - 1)
                board.pop()
                min_eval = min(min_eval, curr_eval)
            return min_eval


def get_nn_engine(new_model=False, new_data=False):
    if new_model:
        X, y = get_dataset(new_data)
        print(X.shape)
        print(y.shape)
        train_model(create_chess_model(32, 4), X, y)
    model = models.load_model('../engines/nn_model.keras')
    engine = NeuralEngine(model)
    return engine


if __name__ == "__main__":
    print("hello world")
    nn_engine = get_nn_engine(True, False)
