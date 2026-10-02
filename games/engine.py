"""Real chess rule enforcement (python-chess) and Stockfish bot integration."""
import chess
import chess.engine

from django.conf import settings

# Bot difficulty -> (search depth, skill level 0-20)
DIFFICULTY_SETTINGS = {
    1: {'depth': 1, 'skill': 0},
    2: {'depth': 3, 'skill': 5},
    3: {'depth': 6, 'skill': 10},
    4: {'depth': 10, 'skill': 15},
    5: {'depth': 14, 'skill': 20},
}


class IllegalMoveError(Exception):
    pass


def apply_move(fen: str, move_uci: str) -> dict:
    """Validate & apply a UCI move against a FEN position.

    Returns dict with new fen, san, whether the move ended the game, and why.
    Raises IllegalMoveError if the move is not legal in this position.
    """
    board = chess.Board(fen)
    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        raise IllegalMoveError('Noto\'g\'ri format')

    if move not in board.legal_moves:
        raise IllegalMoveError('Bu yurish qoidaga zid (illegal move)')

    san = board.san(move)
    board.push(move)

    outcome = board.outcome(claim_draw=True)
    result = None
    end_reason = ''
    if outcome is not None:
        if outcome.winner is True:
            result = 'white'
        elif outcome.winner is False:
            result = 'black'
        else:
            result = 'draw'
        end_reason = {
            chess.Termination.CHECKMATE: 'checkmate',
            chess.Termination.STALEMATE: 'stalemate',
            chess.Termination.INSUFFICIENT_MATERIAL: 'insufficient_material',
            chess.Termination.THREEFOLD_REPETITION: 'threefold',
            chess.Termination.FIFTY_MOVES: 'fifty_moves',
        }.get(outcome.termination, 'draw_agreement')

    return {
        'fen': board.fen(),
        'san': san,
        'uci': move.uci(),
        'is_check': board.is_check(),
        'game_over': outcome is not None,
        'result': result,
        'end_reason': end_reason,
    }


def legal_moves_for_square(fen: str, square: str) -> list:
    board = chess.Board(fen)
    sq = chess.parse_square(square)
    return [
        m.uci() for m in board.legal_moves if m.from_square == sq
    ]


def get_bot_move(fen: str, difficulty: int = 3) -> str:
    """Ask Stockfish for the best move at a given difficulty, return UCI string."""
    settings_ = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS[3])
    board = chess.Board(fen)
    with chess.engine.SimpleEngine.popen_uci(settings.STOCKFISH_PATH) as engine:
        engine.configure({'Skill Level': settings_['skill']})
        result = engine.play(board, chess.engine.Limit(depth=settings_['depth']))
        return result.move.uci()
