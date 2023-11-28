import chess
import chess.svg
import chess.polyglot
import traceback
import chess.pgn
import chess.engine
import datetime
from flask import Flask, Response, request, render_template
import webbrowser
from negamax_engine import NegamaxEngine
from stockfish_engine import StockfishEngine

app = Flask(__name__, template_folder='../templates', static_folder="../static")


def play_game(white, black):
    game = chess.pgn.Game()
    while not board.is_game_over(claim_draw=True):
        curr_move = white.selectmove(board) if board.turn == chess.WHITE else black.selectmove(board)
        add_move_to_history(curr_move)
        board.push(curr_move)
        print(board, end='\n\n')
    # game.add_line(movehistory)
    print(movehistory)
    game.headers["Event"] = "Self Tournament 2020"
    game.headers["Site"] = "Pune"
    game.headers["Date"] = str(datetime.datetime.now().date())
    game.headers["Round"] = 1
    game.headers["White"] = "Ai"
    game.headers["Black"] = "Ai"
    game.headers["Result"] = str(board.result(claim_draw=True))
    print(game)
    return chess.svg.board(board=board, size=400)


def add_move_to_history(move):
    move = board.san(chess.Move.from_uci(str(move)))
    if board.turn == chess.WHITE:
        movehistory[0].append(move)
        movehistory[1].append("")
    else:
        movehistory[1][-1] = move


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
                           result=check_result())


# Display Board
@app.route("/board.svg/")
def board():
    return Response(chess.svg.board(board=board, size=700), mimetype='image/svg+xml')


# Human Move
@app.route("/move/")
def move():
    try:
        move = request.args.get('move', default="")
        add_move_to_history(move)
        board.push_san(move)
    except Exception:
        traceback.print_exc()
    return main()


def get_engine(engine_name):
    match (engine_name.lower()):
        case "negamax" | "n":
            return negamax_engine
        case "stockfish" | "s":
            return stockfish_engine
        case "human":
            return None
        case _:
            return None


@app.route("/ai_game/")
def play_ai_game():
    try:
        white_engine = get_engine(request.args.get('whiteplayer', default=""))
        black_engine = get_engine(request.args.get('blackplayer', default=""))
        play_game(white_engine, black_engine)
    except Exception:
        traceback.print_exc()
    return main()


# Make UCI Compatible engine's move
@app.route("/stockfish_engine/", methods=['POST'])
def stockfish_engine_endpoint():
    try:
        move = stockfish_engine.selectmove(board)
        add_move_to_history(move)
        board.push(move)
    except Exception:
        traceback.print_exc()
    return main()


# Make UCI Compatible engine's move
@app.route("/negamax_engine/", methods=['POST'])
def negamax_engine_endpoint():
    try:
        move = negamax_engine.selectmove(board)
        add_move_to_history(move)
        board.push(move)
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
    stockfish_engine = StockfishEngine()

    # start webserver
    webbrowser.open("http://127.0.0.1:5000/")
    app.run()
