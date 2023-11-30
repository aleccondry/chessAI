import chess
import chess.svg
import chess.polyglot
import chess.pgn
import chess.engine


class StockfishEngine:
    def __init__(self, stockfish_num=9):
        if stockfish_num == 9:
            self.engine = chess.engine.SimpleEngine.popen_uci("../engines/stockfish.exe")
        else:
            self.engine = chess.engine.SimpleEngine.popen_uci("../engines/stockfish-windows-x86-64-avx2.exe")

    def selectmove(self, board, timelimit=0.1, ):
        move = self.engine.play(board, chess.engine.Limit(time=timelimit))
        return move.move
