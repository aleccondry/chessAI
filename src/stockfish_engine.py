import chess
import chess.svg
import chess.polyglot
import chess.pgn
import chess.engine


class StockfishEngine:
    def __init__(self):
        self.engine = chess.engine.SimpleEngine.popen_uci("../engines/stockfish.exe")

    def selectmove(self, board, timelimit=0.1, ):
        move = self.engine.play(board, chess.engine.Limit(time=timelimit))
        return move.move
