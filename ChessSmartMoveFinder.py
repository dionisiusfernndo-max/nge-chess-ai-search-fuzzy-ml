import random
import os
import pickle
import warnings

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')

pieceScore = {"K": 0, "Q": 90, "R": 50, "B": 30, "N": 30, "p": 10}

piece_to_int = {
    '--': 0,
    'wp':  1, 'wN':  2, 'wB':  3, 'wR':  4, 'wQ':  5, 'wK':  6,
    'bp': -1, 'bN': -2, 'bB': -3, 'bR': -4, 'bQ': -5, 'bK': -6
}

knightWeights = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 3, 3, 3, 2, 1],
    [1, 2, 2, 2, 2, 2, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]
bishopWeights = [
    [4, 3, 2, 1, 1, 2, 3, 4],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [2, 3, 4, 3, 3, 4, 3, 2],
    [3, 4, 3, 2, 2, 3, 4, 3],
    [4, 3, 2, 1, 1, 2, 3, 4],
]
queenWeights = [
    [1, 1, 1, 3, 1, 1, 1, 1],
    [1, 2, 3, 3, 3, 1, 1, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 2, 3, 3, 3, 2, 2, 1],
    [1, 4, 3, 3, 3, 4, 2, 1],
    [1, 1, 2, 3, 3, 1, 1, 1],
    [1, 1, 1, 3, 1, 1, 1, 1],
]
rookWeights = [
    [4, 3, 4, 4, 4, 4, 3, 4],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 2, 3, 4, 4, 3, 2, 1],
    [1, 1, 2, 2, 2, 2, 1, 1],
    [4, 4, 4, 4, 4, 4, 4, 4],
    [4, 3, 4, 4, 4, 4, 3, 4],
]
pawnWeights = [
    [8,  8,  8,  8,  8,  8,  8,  8],
    [7,  7,  7,  7,  7,  7,  7,  7],
    [3,  3,  4,  5,  5,  4,  3,  3],
    [2,  2,  3,  4,  4,  3,  2,  2],
    [1,  1,  2,  3,  3,  2,  1,  1],
    [1,  1,  1,  0,  0,  1,  1,  1],
    [0,  0,  0, -2, -2,  0,  0,  0],
    [0,  0,  0,  0,  0,  0,  0,  0],
]
kingWeights = [
    [1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [2, 2, 2, 1, 1, 2, 2, 2],
]
pieceWeights = {
    "N": knightWeights, "B": bishopWeights, "Q": queenWeights,
    "R": rookWeights,   "p": pawnWeights,   "K": kingWeights
}

CHECKMATE = 10000
STALEMATE = -50
DEPTH = 3

def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def get_material_balance(gs):
    score = 0

    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]

            if piece == '--':
                continue

            value = pieceScore.get(piece[1], 0)

            if piece[0] == 'w':
                score += value
            else:
                score -= value

    return score

def fuzzy_membership_material(material_diff, ai_is_white):
    ai_material = material_diff if ai_is_white else -material_diff

    losing = clamp(-ai_material / 40.0)
    balanced = clamp(1.0 - abs(ai_material) / 35.0)
    winning = clamp(ai_material / 40.0)

    return losing, balanced, winning

def fuzzy_membership_phase(move_count):
    opening = clamp((20 - move_count) / 20.0)
    middlegame = clamp(1.0 - abs(move_count - 35) / 25.0)
    endgame = clamp((move_count - 45) / 35.0)

    return opening, middlegame, endgame

def fuzzy_membership_time(ai_time):
    low_time = clamp((90 - ai_time) / 90.0)
    normal_time = clamp(1.0 - abs(ai_time - 300) / 240.0)
    high_time = clamp((ai_time - 240) / 360.0)

    return low_time, normal_time, high_time

def fuzzy_dynamic_difficulty(gs, white_time=None, black_time=None):
    material_diff = get_material_balance(gs)
    move_count = len(gs.moveLog)

    ai_is_white = gs.whiteToMove

    if white_time is None:
        white_time = 600

    if black_time is None:
        black_time = 600

    ai_time = white_time if ai_is_white else black_time

    losing, balanced, winning = fuzzy_membership_material(material_diff, ai_is_white)
    opening, middlegame, endgame = fuzzy_membership_phase(move_count)
    low_time, normal_time, high_time = fuzzy_membership_time(ai_time)

    # Rule 1: Jika AI kalah material, AI perlu lebih agresif.
    hard_rule_1 = losing

    # Rule 2: Jika endgame dan posisi seimbang, AI perlu lebih presisi.
    hard_rule_2 = min(endgame, balanced)

    # Rule 3: Jika waktu AI rendah, jangan terlalu dalam berpikir.
    easy_rule_1 = low_time

    # Rule 4: Opening dibuat normal agar tidak terlalu ekstrem.
    medium_rule_1 = opening

    # Rule 5: Jika posisi seimbang dan waktu normal, main normal.
    medium_rule_2 = min(balanced, normal_time)

    # Rule 6: Jika AI unggul, tetap cukup kuat tapi tidak perlu over-search.
    medium_rule_3 = winning * 0.7

    easy_strength = easy_rule_1
    medium_strength = max(medium_rule_1, medium_rule_2, medium_rule_3)
    hard_strength = max(hard_rule_1, hard_rule_2)

    numerator = (
        easy_strength * 30 +
        medium_strength * 60 +
        hard_strength * 85
    )

    denominator = easy_strength + medium_strength + hard_strength

    if denominator == 0:
        return 60

    return numerator / denominator

def fuzzy_search_limits(gs, white_time=None, black_time=None):
    score = fuzzy_dynamic_difficulty(gs, white_time, black_time)

    if score < 45:
        return {
            "score": score,
            "root_limit": 10,
            "node_limit": 14,
            "aggression": 0.8
        }

    elif score < 70:
        return {
            "score": score,
            "root_limit": 14,
            "node_limit": 18,
            "aggression": 1.0
        }

    else:
        return {
            "score": score,
            "root_limit": 18,
            "node_limit": 24,
            "aggression": 1.2
        }

def board_to_matrix(board):
    return np.array([piece_to_int[sq] for row in board for sq in row], dtype=float)

def extract_features(gs):
    board_feat = board_to_matrix(gs.board)

    w_mat    = sum(pieceScore.get(p[1], 0) for r in gs.board for p in r if p[0] == 'w')
    b_mat    = sum(pieceScore.get(p[1], 0) for r in gs.board for p in r if p[0] == 'b')
    w_pieces = sum(1 for r in gs.board for p in r if p[0] == 'w')
    b_pieces = sum(1 for r in gs.board for p in r if p[0] == 'b')
    w_pawns  = sum(1 for r in gs.board for p in r if p == 'wp')
    b_pawns  = sum(1 for r in gs.board for p in r if p == 'bp')

    extra = np.array([
        float(w_mat),
        float(b_mat),
        float(w_mat - b_mat),
        float(w_pieces),
        float(b_pieces),
        float(w_pawns),
        float(b_pawns),
        1.0 if gs.whiteToMove else -1.0
    ])
    return np.concatenate([board_feat, extra])

def heuristic_score(gs):
    if gs.checkmate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE
    if gs.stalemate:
        return STALEMATE

    score = 0.0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != '--':
                pt = piece[1]
                if piece[0] == 'w':
                    score += pieceScore[pt] + pieceWeights[pt][r][c] * 0.5
                else:
                    score -= pieceScore[pt] + pieceWeights[pt][7 - r][c] * 0.5
    return score

class SupervisedEvaluator:

    MODEL_PATH = "model_supervised.pkl"

    def __init__(self):
        self.model = MLPRegressor(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            learning_rate_init=0.001,
            max_iter=300,
            random_state=42
        )
        self.scaler  = StandardScaler()
        self.trained = False

        self._weights    = None
        self._biases     = None
        self._feat_mean  = None
        self._feat_scale = None

        self.load_or_train()

    def generate_data(self, n_games=400):
        import ChessEngine
        X, y = [], []

        def explore(gs, depth=0):
            if depth > 15 or gs.checkmate or gs.stalemate:
                return
            moves = gs.getValidMoves()
            if not moves:
                return
            X.append(extract_features(gs))
            y.append(heuristic_score(gs))
            gs.makeMove(random.choice(moves))
            explore(gs, depth + 1)
            gs.undoMove()

        print("[Supervised] Generating training data...")
        for i in range(n_games):
            gs = ChessEngine.GameState()

            for _ in range(random.randint(0, 12)):
                mvs = gs.getValidMoves()
                if mvs:
                    gs.makeMove(random.choice(mvs))
            explore(gs)
            if (i + 1) % 75 == 0:
                print(f"  {i+1}/{n_games} games done...")

        return np.array(X), np.array(y)

    def train(self):
        X, y = self.generate_data()
        if len(X) < 20:
            print("[Supervised] Data tidak cukup, skip training.")
            return

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.trained = True
        self.cache_weights()

        with open(self.MODEL_PATH, 'wb') as f:
            pickle.dump({
                'model': self.model, 'scaler': self.scaler,
                'weights': self._weights, 'biases': self._biases,
                'mean': self._feat_mean, 'scale': self._feat_scale
            }, f)
        print(f"[Supervised] Model terlatih ({len(X)} samples), disimpan.")

    def cache_weights(self):
        self._weights    = [w.copy() for w in self.model.coefs_]
        self._biases     = [b.copy() for b in self.model.intercepts_]
        self._feat_mean  = self.scaler.mean_.copy()
        self._feat_scale = self.scaler.scale_.copy()

    def fast_predict(self, feat_vec):
        x = (feat_vec - self._feat_mean) / self._feat_scale
        for i, (w, b) in enumerate(zip(self._weights, self._biases)):
            x = x @ w + b
            if i < len(self._weights) - 1:
                x = np.maximum(0.0, x)
        return float(x[0])

    def load_or_train(self):
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.model       = data['model']
                self.scaler      = data['scaler']
                self._weights    = data.get('weights')
                self._biases     = data.get('biases')
                self._feat_mean  = data.get('mean')
                self._feat_scale = data.get('scale')
                self.trained     = True
                if self._weights is None:
                    self.cache_weights()
                print("[Supervised] Model dimuat dari file.")
                return
            except Exception as e:
                print(f"[Supervised] Gagal load: {e}")
        self.train()

    def evaluate(self, gs):
        if gs.checkmate:
            return -CHECKMATE if gs.whiteToMove else CHECKMATE
        if gs.stalemate:
            return STALEMATE
        if not self.trained:
            return heuristic_score(gs)
        feat = extract_features(gs)
        return self.fast_predict(feat)

class UnsupervisedPhaseDetector:

    MODEL_PATH = "model_unsupervised.pkl"
    PHASES = ["Opening", "Middlegame", "Endgame"]

    PHASE_MULTIPLIERS = {
        "Opening":    {"p": 1.0, "N": 1.8, "B": 1.8, "R": 0.6, "Q": 0.5, "K": 0.2},
        "Middlegame": {"p": 1.2, "N": 1.2, "B": 1.2, "R": 1.4, "Q": 1.8, "K": 0.3},
        "Endgame":    {"p": 2.5, "N": 0.8, "B": 0.9, "R": 1.5, "Q": 1.3, "K": 2.5},
    }

    def __init__(self):
        self.kmeans          = KMeans(n_clusters=3, random_state=42, n_init=10)
        self.scaler          = StandardScaler()
        self.fitted          = False
        self.cluster_to_phase = {}
        self.load_or_fit()

    def phase_features(self, gs):
        board = gs.board
        wQ = sum(1 for r in board for p in r if p == 'wQ')
        bQ = sum(1 for r in board for p in r if p == 'bQ')
        rooks  = sum(1 for r in board for p in r if p in ('wR', 'bR'))
        minors = sum(1 for r in board for p in r if p in ('wN', 'wB', 'bN', 'bB'))
        wP = sum(1 for r in board for p in r if p == 'wp')
        bP = sum(1 for r in board for p in r if p == 'bp')
        total  = sum(1 for r in board for p in r if p != '--')
        moves  = float(len(gs.moveLog))
        return np.array([wQ, bQ, rooks, minors, wP, bP, total, moves], dtype=float)

    def generate_samples(self, n_games=200):
        import ChessEngine
        samples = []
        print("[Unsupervised] Generating K-Means samples...")
        for i in range(n_games):
            gs = ChessEngine.GameState()
            n_moves = random.randint(0, 70)
            for _ in range(n_moves):
                mvs = gs.getValidMoves()
                if not mvs or gs.checkmate or gs.stalemate:
                    break
                gs.makeMove(random.choice(mvs))
                samples.append(self.phase_features(gs))
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{n_games} games done...")
        return np.array(samples)

    def fit(self, samples=None):
        if samples is None:
            samples = self.generate_samples()

        X_scaled = self.scaler.fit_transform(samples)
        self.kmeans.fit(X_scaled)

        centers      = self.scaler.inverse_transform(self.kmeans.cluster_centers_)
        piece_counts = centers[:, 6]
        sorted_idx   = np.argsort(piece_counts)[::-1]
        self.cluster_to_phase = {
            int(sorted_idx[0]): "Opening",
            int(sorted_idx[1]): "Middlegame",
            int(sorted_idx[2]): "Endgame",
        }
        self.fitted = True

        with open(self.MODEL_PATH, 'wb') as f:
            pickle.dump({
                'kmeans': self.kmeans, 'scaler': self.scaler,
                'mapping': self.cluster_to_phase
            }, f)
        print(f"[Unsupervised] K-Means fitted! Mapping: {self.cluster_to_phase}")

    def load_or_fit(self):
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.kmeans           = data['kmeans']
                self.scaler           = data['scaler']
                self.cluster_to_phase = data['mapping']
                self.fitted           = True
                print(f"[Unsupervised] K-Means dimuat dari file. Mapping: {self.cluster_to_phase}")
                return
            except Exception as e:
                print(f"[Unsupervised] Gagal load: {e}")
        self.fit()

    def predict_phase(self, gs):
        if not self.fitted:
            return self.fallback_phase(gs)
        feat        = self.phase_features(gs).reshape(1, -1)
        feat_scaled = self.scaler.transform(feat)
        cluster     = int(self.kmeans.predict(feat_scaled)[0])
        return self.cluster_to_phase.get(cluster, "Middlegame")

    def fallback_phase(self, gs):
        total = sum(1 for r in gs.board for p in r if p != '--')
        if total > 28: return "Opening"
        if total > 14: return "Middlegame"
        return "Endgame"

    def get_phase_multipliers(self, gs):
        phase = self.predict_phase(gs)
        return phase, self.PHASE_MULTIPLIERS[phase]

class RLAgent:

    MODEL_PATH   = "model_rl.pkl"
    BUFFER_SIZE  = 4000
    BATCH_SIZE   = 64

    def __init__(self, alpha=0.01, gamma=0.95, epsilon=0.15):
        self.alpha    = alpha
        self.gamma    = gamma
        self.epsilon  = epsilon

        self.value_net = MLPRegressor(
            hidden_layer_sizes=(64, 32),
            activation='relu',
            solver='adam',
            max_iter=1,
            warm_start=True,
            random_state=42
        )
        self.scaler         = StandardScaler()
        self.initialized    = False
        self.replay_buffer  = []

        self._weights    = None
        self._biases     = None
        self._feat_mean  = None
        self._feat_scale = None

        self.load_or_train()

    def get_reward(self, gs, move):
        r = 0.0
        if move.pieceCaptured != '--':
            r += pieceScore[move.pieceCaptured[1]] * 0.1
        if move.isPawnPromotion:
            r += 8.0
        if gs.checkmate:
            r += 100.0 if not gs.whiteToMove else -100.0
        elif gs.stalemate:
            r -= 5.0
        return r

    def cache_weights(self):
        self._weights    = [w.copy() for w in self.value_net.coefs_]
        self._biases     = [b.copy() for b in self.value_net.intercepts_]
        self._feat_mean  = self.scaler.mean_.copy()
        self._feat_scale = self.scaler.scale_.copy()

    def fast_predict(self, feat_vec):
        x = (feat_vec - self._feat_mean) / self._feat_scale
        for i, (w, b) in enumerate(zip(self._weights, self._biases)):
            x = x @ w + b
            if i < len(self._weights) - 1:
                x = np.maximum(0.0, x)
        return float(x[0])

    def get_value(self, gs):
        if not self.initialized:
            return heuristic_score(gs)
        try:
            return self.fast_predict(extract_features(gs))
        except Exception:
            return heuristic_score(gs)

    def update_network(self):
        if len(self.replay_buffer) < self.BATCH_SIZE:
            return

        batch    = random.sample(self.replay_buffer, self.BATCH_SIZE)
        X_train, y_train = [], []

        for (s_feat, reward, s_next_feat, done) in batch:
            if done or not self.initialized:
                td_target = reward
            else:
                try:
                    next_val  = self.fast_predict(s_next_feat)
                    td_target = reward + self.gamma * next_val
                except Exception:
                    td_target = reward
            X_train.append(s_feat)
            y_train.append(td_target)

        X_arr = np.array(X_train)
        y_arr = np.array(y_train)

        if not self.initialized:
            self.scaler.fit(X_arr)
            self.initialized = True

        X_scaled = self.scaler.transform(X_arr)
        self.value_net.fit(X_scaled, y_arr)
        self.cache_weights()

    def train_self_play(self, n_games=100):
        import ChessEngine
        print(f"[RL] Memulai self-play training ({n_games} games)...")

        for game_num in range(n_games):
            gs         = ChessEngine.GameState()
            move_count = 0

            while not gs.checkmate and not gs.stalemate and move_count < 90:
                moves = gs.getValidMoves()
                if not moves:
                    break

                s_feat = extract_features(gs)

                if random.random() < self.epsilon:
                    move = random.choice(moves)
                else:
                    move = self.greedy_select(gs, moves)

                gs.makeMove(move)
                reward      = self.get_reward(gs, move)
                s_next_feat = extract_features(gs)
                done        = gs.checkmate or gs.stalemate

                self.replay_buffer.append((s_feat, reward, s_next_feat, done))
                if len(self.replay_buffer) > self.BUFFER_SIZE:
                    self.replay_buffer.pop(0)

                self.update_network()
                move_count += 1

            if (game_num + 1) % 10 == 0:
                print(f"  [RL] Game {game_num+1}/{n_games} selesai.")

        self.epsilon = max(0.05, self.epsilon * 0.75)
        self.save()
        print(f"[RL] Training selesai! epsilon={self.epsilon:.3f}")

    def greedy_select(self, gs, moves):
        best_move = None
        best_val  = float('-inf') if gs.whiteToMove else float('inf')

        for move in moves:
            gs.makeMove(move)
            val = self.get_value(gs)
            gs.undoMove()
            if gs.whiteToMove and val > best_val:
                best_val, best_move = val, move
            elif not gs.whiteToMove and val < best_val:
                best_val, best_move = val, move

        return best_move if best_move else random.choice(moves)

    def select_move(self, gs, valid_moves):
        if not valid_moves:
            return None
        if not self.initialized:
            return findRandomMove(valid_moves)
        return self.greedy_select(gs, valid_moves)

    def save(self):
        if not self.initialized:
            return
        with open(self.MODEL_PATH, 'wb') as f:
            pickle.dump({
                'model': self.value_net, 'scaler': self.scaler,
                'epsilon': self.epsilon,
                'weights': self._weights, 'biases': self._biases,
                'mean': self._feat_mean, 'scale': self._feat_scale
            }, f)

    def load_or_train(self):
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.value_net   = data['model']
                self.scaler      = data['scaler']
                self.epsilon     = data.get('epsilon', 0.1)
                self._weights    = data.get('weights')
                self._biases     = data.get('biases')
                self._feat_mean  = data.get('mean')
                self._feat_scale = data.get('scale')
                self.initialized = True
                if self._weights is None:
                    self.cache_weights()
                print(f"[RL] Model dimuat dari file. epsilon={self.epsilon:.3f}")
                return
            except Exception as e:
                print(f"[RL] Gagal load: {e}")
        self.train_self_play()

supervised_eval  = SupervisedEvaluator()
phase_detector   = UnsupervisedPhaseDetector()
rl_agent         = RLAgent()

print("\nML Chess Engine siap!\n")

def scoreBoard(gs):
    if gs.checkmate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE
    if gs.stalemate:
        return STALEMATE

    base_score = supervised_eval.evaluate(gs)

    phase, multipliers = phase_detector.get_phase_multipliers(gs)
    phase_bonus = 0.0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece != '--':
                pt     = piece[1]
                mult   = multipliers.get(pt, 1.0)
                pos_w  = pieceWeights[pt][r][c] if piece[0] == 'w' else pieceWeights[pt][7 - r][c]
                if piece[0] == 'w':
                    phase_bonus += pos_w * mult * 0.1
                else:
                    phase_bonus -= pos_w * mult * 0.1

    return base_score + phase_bonus

def score_move(move):
    s = 0
    if move.pieceCaptured != '--':
        s = 10 * pieceScore[move.pieceCaptured[1]] - pieceScore[move.pieceMoved[1]]
    if move.isPawnPromotion:
        s += 100
    return s

HARD_DEPTH = 4

HARD_ROOT_MOVE_LIMIT = 14
HARD_NODE_MOVE_LIMIT = 18

HARD_TRANSPOSITION_TABLE = {}

hardNextMove = None

def king_safety_score(gs):
    def count_friendly_around_king(king_location, color):
        r, c = king_location
        count = 0

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue

                nr = r + dr
                nc = c + dc

                if 0 <= nr < 8 and 0 <= nc < 8:
                    piece = gs.board[nr][nc]

                    if piece != '--' and piece[0] == color:
                        count += 1

        return count

    white_protection = count_friendly_around_king(gs.whiteKingLocation, 'w')
    black_protection = count_friendly_around_king(gs.blackKingLocation, 'b')

    return (white_protection - black_protection) * 2

def hard_tactical_score(gs):
    if gs.checkmate:
        return -CHECKMATE if gs.whiteToMove else CHECKMATE

    if gs.stalemate:
        return STALEMATE

    base_score = scoreBoard(gs)
    material_bonus = get_material_balance(gs) * 0.10
    king_bonus = king_safety_score(gs) * 0.25

    return base_score + material_bonus + king_bonus

def hard_move_order_score(move):
    score = 0

    if move.pieceCaptured != '--':
        victim_value = pieceScore.get(move.pieceCaptured[1], 0)
        attacker_value = pieceScore.get(move.pieceMoved[1], 0)
        score += (victim_value * 20) - attacker_value

    if move.isPawnPromotion:
        score += 500

    center_squares = {
        (3, 3), (3, 4),
        (4, 3), (4, 4)
    }

    if (move.endRow, move.endCol) in center_squares:
        score += 10

    return score

def hard_board_key(gs, depth):
    board_tuple = tuple(tuple(row) for row in gs.board)

    return (
        board_tuple,
        gs.whiteToMove,
        depth,
        gs.enpassantPossible,
        gs.currentCastlingRight.wks,
        gs.currentCastlingRight.wqs,
        gs.currentCastlingRight.bks,
        gs.currentCastlingRight.bqs
    )

def findBestMoveHard(gs, validMoves, white_time=None, black_time=None):
    global hardNextMove
    global HARD_TRANSPOSITION_TABLE

    if not validMoves:
        return None

    hardNextMove = None
    HARD_TRANSPOSITION_TABLE.clear()

    moves = validMoves[:]

    random.shuffle(moves)
    moves.sort(key=hard_move_order_score, reverse=True)

    fuzzy_cfg = fuzzy_search_limits(gs, white_time, black_time)
    root_limit = fuzzy_cfg["root_limit"]

    moves = moves[:root_limit]

    run_hard_alphabeta(
        gs,
        moves,
        HARD_DEPTH,
        -CHECKMATE,
        CHECKMATE,
        gs.whiteToMove,
        fuzzy_cfg["node_limit"]
    )

    return hardNextMove if hardNextMove is not None else findRandomMove(validMoves)

def run_hard_alphabeta(gs, validMoves, depth, alpha, beta, whiteToMove, node_limit=None):
    global hardNextMove
    global HARD_TRANSPOSITION_TABLE

    if depth == 0:
        return hard_tactical_score(gs)

    if not validMoves:
        return hard_tactical_score(gs)

    key = hard_board_key(gs, depth)

    if key in HARD_TRANSPOSITION_TABLE:
        return HARD_TRANSPOSITION_TABLE[key]

    moves = validMoves[:]
    moves.sort(key=hard_move_order_score, reverse=True)

    if node_limit is None:
        node_limit = HARD_NODE_MOVE_LIMIT

    if depth < HARD_DEPTH:
        moves = moves[:node_limit]

    if whiteToMove:
        maxScore = -CHECKMATE

        for move in moves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()

            score = run_hard_alphabeta(
                gs,
                nextMoves,
                depth - 1,
                alpha,
                beta,
                False,
                node_limit
            )

            gs.undoMove()

            if score > maxScore:
                maxScore = score

                if depth == HARD_DEPTH:
                    hardNextMove = move

            alpha = max(alpha, maxScore)

            if beta <= alpha:
                break

        HARD_TRANSPOSITION_TABLE[key] = maxScore
        return maxScore

    else:
        minScore = CHECKMATE

        for move in moves:
            gs.makeMove(move)
            nextMoves = gs.getValidMoves()

            score = run_hard_alphabeta(
                gs,
                nextMoves,
                depth - 1,
                alpha,
                beta,
                True,
                node_limit
            )

            gs.undoMove()

            if score < minScore:
                minScore = score

                if depth == HARD_DEPTH:
                    hardNextMove = move

            beta = min(beta, minScore)

            if beta <= alpha:
                break

        HARD_TRANSPOSITION_TABLE[key] = minScore
        return minScore

def findBestMoveDynamic(gs, validMoves, white_time=None, black_time=None):
    if not validMoves:
        return None

    fuzzy_score = fuzzy_dynamic_difficulty(gs, white_time, black_time)

    if fuzzy_score < 45:
        return findBestMoveRL(gs, validMoves)

    elif fuzzy_score < 70:
        return findBestMoveAlphaBeta(gs, validMoves)

    else:
        return findBestMoveHard(
            gs,
            validMoves,
            white_time=white_time,
            black_time=black_time
        )

def findRandomMove(validMoves):
    return validMoves[random.randint(0, len(validMoves) - 1)]

nextMove = None

def findBestMoveAlphaBeta(gs, validMoves):
    global nextMove
    nextMove = None
    random.shuffle(validMoves)
    validMoves.sort(key=lambda x: score_move(x), reverse=True)
    run_alphabeta(gs, validMoves, DEPTH, -CHECKMATE, CHECKMATE, gs.whiteToMove)
    return nextMove

def run_alphabeta(gs, validMoves, depth, alpha, beta, whiteToMove):
    global nextMove
    if depth == 0:
        return scoreBoard(gs)

    validMoves.sort(key=lambda x: score_move(x), reverse=True)

    if whiteToMove:
        maxScore = -CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            score = run_alphabeta(gs, gs.getValidMoves(), depth - 1, alpha, beta, False)
            if score > maxScore:
                maxScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
            alpha = max(alpha, maxScore)
            if beta <= alpha:
                break
        return maxScore
    else:
        minScore = CHECKMATE
        for move in validMoves:
            gs.makeMove(move)
            score = run_alphabeta(gs, gs.getValidMoves(), depth - 1, alpha, beta, True)
            if score < minScore:
                minScore = score
                if depth == DEPTH:
                    nextMove = move
            gs.undoMove()
            beta = min(beta, minScore)
            if beta <= alpha:
                break
        return minScore

def findBestMoveRL(gs, validMoves):
    return rl_agent.select_move(gs, validMoves)