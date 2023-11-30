import chess
import chess.svg
import chess.polyglot
import traceback
import chess.pgn
import chess.engine
import datetime
from flask import Flask, Response, request, render_template, redirect
import webbrowser
from negamax_engine import NegamaxEngine
from stockfish_engine import StockfishEngine
from pynput import keyboard
from pynput.keyboard import Key
import threading
from neural_engine import get_nn_engine

app = Flask(__name__, template_folder='../templates', static_folder="../static")


def play_game(white, black):
    while not board.is_game_over(claim_draw=True):
        curr_move = white.selectmove(board) if board.turn == chess.WHITE else black.selectmove(board)
        add_move_to_history(curr_move)
        board.push(curr_move)
        print(board, end='\n\n')
    return chess.svg.board(board=board, size=400)


def add_move_to_history(move):
    try:
        move = board.san(chess.Move.from_uci(str(move)))
    except chess.InvalidMoveError:
        pass
    if board.turn == chess.WHITE:
        movehistory[0].append(move)
        movehistory[1].append("")
    else:
        movehistory[1][-1] = move


def remove_move_from_history():
    if board.turn == chess.WHITE:
        movehistory[1][-1] = ""
    else:
        movehistory[0].pop()
        movehistory[1].pop()


def check_result():
    result = "In progress"
    if board.is_stalemate():
        result = "Its a draw by stalemate"
    elif board.is_checkmate():
        result = "Checkmate"
    elif board.is_insufficient_material():
        result = "Its a draw by insufficient material"
    elif board.is_check():
        result = "Check"
    return result


# Front Page of the Flask Web Page
@app.route("/")
def main():
    return render_template('index.html',
                           white_moves=movehistory[0],
                           black_moves=movehistory[1],
                           zip=zip,
                           enumerate=enumerate,
                           result=check_result(),
                           player_turn=board.turn)


# Display Board
@app.route("/board.svg/")
def board():
    return Response(chess.svg.board(board=board, size=700), mimetype='image/svg+xml')


# Human Move
@app.route("/move/")
def move():
    try:
        h_move = request.args.get('move', default="")
        add_move_to_history(h_move)
        board.push_san(h_move)
    except Exception:
        traceback.print_exc()
    return main()


def get_engine(engine_name):
    match (engine_name.lower()):
        case "negamax" | "n":
            return negamax_engine
        case "stockfish" | "s":
            return stockfish_engine9
        case "stockfish16" | "s16":
            return stockfish_engine16
        case "neural" | "nn":
            return neural_engine
        case "human":
            return None
        case _:
            return None


@app.route("/ai_game/")
def play_ai_game():
    global white_engine, black_engine
    try:
        wp = request.args.get('whiteplayer', default="")
        bp = request.args.get('blackplayer', default="")
        white_engine = white_engine if get_engine(wp) is None else get_engine(wp)
        black_engine = black_engine if get_engine(bp) is None else get_engine(bp)
        play_game(white_engine, black_engine)
    except Exception:
        traceback.print_exc()
    return main()


# Make UCI Compatible engine's move
@app.route("/stockfish_engine/", methods=['POST'])
def stockfish_engine_endpoint():
    try:
        s_move = stockfish_engine9.selectmove(board)
        add_move_to_history(s_move)
        board.push(s_move)
    except Exception:
        traceback.print_exc()
    return main()


# Make UCI Compatible engine's move
@app.route("/negamax_engine/", methods=['POST'])
def negamax_engine_endpoint():
    try:
        n_move = negamax_engine.selectmove(board)
        add_move_to_history(n_move)
        board.push(n_move)
    except Exception:
        traceback.print_exc()
    return main()


@app.route("/neural_engine/", methods=['POST'])
def neural_engine_endpoint():
    try:
        print("Making neural move")
        nn_move = neural_engine.selectmove(board)
        print(f"neural move: {nn_move}")
        add_move_to_history(nn_move)
        board.push(nn_move)
    except Exception:
        traceback.print_exc()
    return main()


# New Game
@app.route("/game/", methods=['POST'])
def reset_game():
    global movehistory
    board.reset()
    movehistory = [[], []]
    return main()


# Undo
@app.route("/undo/", methods=['POST'])
def undo():
    try:
        remove_move_from_history()
        board.pop()
    except Exception:
        traceback.print_exc()
    return main()


# Main Function
if __name__ == '__main__':
    # create board and engines
    board = chess.Board()
    movehistory = [[], []]

    negamax_engine = NegamaxEngine()
    stockfish_engine9 = StockfishEngine(9)
    stockfish_engine16 = StockfishEngine(16)
    neural_engine = get_nn_engine()

    white_engine = None
    black_engine = None

    # start webserver
    webbrowser.open("http://127.0.0.1:5000/")
    app.run()
