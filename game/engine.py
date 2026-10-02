"""Oddiy shaxmat boti: minimax + alpha-beta kesish, material va pozitsion baholash.
Tashqi dvigatel (Stockfish) talab qilinmaydi - toza python-chess ustida ishlaydi.
"""
import random
import chess

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Markazga intilish uchun soddalashtirilgan pozitsion jadvallar (oq nuqtai nazaridan)
PAWN_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]
KNIGHT_TABLE = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
BISHOP_TABLE = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
ROOK_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0,
]
QUEEN_TABLE = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]
KING_TABLE = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]
TABLES = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_TABLE,
}

DIFFICULTY_DEPTH = {"easy": 1, "medium": 2, "hard": 3}
DIFFICULTY_RANDOMNESS = {"easy": 0.35, "medium": 0.12, "hard": 0.0}


def evaluate(board: chess.Board) -> int:
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square, piece in board.piece_map().items():
        value = PIECE_VALUES[piece.piece_type]
        table = TABLES[piece.piece_type]
        idx = square if piece.color == chess.WHITE else chess.square_mirror(square)
        positional = table[idx]
        total = value + positional
        score += total if piece.color == chess.WHITE else -total

    # harakatchanlik (mobility) bonusi
    score += 3 * len(list(board.legal_moves)) if board.turn == chess.WHITE else -3 * len(list(board.legal_moves))
    return score


def _minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate(board), None

    best_move = None
    legal_moves = list(board.legal_moves)
    if maximizing:
        best_val = -float("inf")
        for move in legal_moves:
            board.push(move)
            val, _ = _minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = float("inf")
        for move in legal_moves:
            board.push(move)
            val, _ = _minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        return best_val, best_move


def choose_bot_move(fen: str, difficulty: str) -> str:
    """FEN holatidan botning navbatdagi yurishini (UCI) qaytaradi."""
    board = chess.Board(fen)
    if board.is_game_over():
        return None

    legal_moves = list(board.legal_moves)
    if not legal_moves:
        return None

    randomness = DIFFICULTY_RANDOMNESS.get(difficulty, 0.15)
    if random.random() < randomness:
        # Ba'zan tasodifiy (lekin qonuniy) yurish - kuchsizroq o'ynash uchun
        return random.choice(legal_moves).uci()

    depth = DIFFICULTY_DEPTH.get(difficulty, 2)
    maximizing = board.turn == chess.WHITE
    _, best_move = _minimax(board, depth, -float("inf"), float("inf"), maximizing)
    if best_move is None:
        best_move = random.choice(legal_moves)
    return best_move.uci()
