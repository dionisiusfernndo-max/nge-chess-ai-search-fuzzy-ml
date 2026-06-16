import os
os.environ['SDL_RENDER_SCALE_QUALITY'] = '1'

import pygame as p
import ChessEngine, ChessSmartMoveFinder

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
START_TIME_SECONDS = 10 * 60
IMAGES = {}
CURRENT_AI_MODE = "alphabeta_ml"

game_surf: p.Surface = None


def squareName(row, col):
    files = "abcdefgh"
    return files[col] + str(8 - row)


def formatTimer(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def drawPieceBadge(screen, piece, x, y, size=22):
    if piece not in IMAGES:
        return
    piece_img = p.transform.smoothscale(IMAGES[piece], (size, size))
    if piece[0] == 'w':
        bg_fill = (8, 8, 8)
        border_color = (120, 100, 55)
    else:
        bg_fill = (245, 245, 245)
        border_color = (120, 120, 120)
    badge_rect = p.Rect(x - 2, y - 1, size + 4, size + 4)
    p.draw.rect(screen, bg_fill, badge_rect, border_radius=3)
    p.draw.rect(screen, border_color, badge_rect, 1, border_radius=3)
    screen.blit(piece_img, (x, y))


def getCapturedPieces(gs):
    captured_by_white = []
    captured_by_black = []
    for move in gs.moveLog:
        captured = move.pieceCaptured
        if captured == "--":
            continue
        if captured[0] == "b":
            captured_by_white.append(captured)
        elif captured[0] == "w":
            captured_by_black.append(captured)
    return captured_by_white, captured_by_black


def drawCapturedPiecesBox(screen, x, y, w, title, pieces, is_white_owner=True):
    box_h = 74
    if is_white_owner:
        bg = (235, 235, 225)
        inner_bg = (250, 248, 238)
        border = (230, 210, 140)
        text_col = (25, 25, 25)
        muted_col = (90, 80, 60)
    else:
        bg = (18, 18, 18)
        inner_bg = (28, 28, 28)
        border = (120, 90, 45)
        text_col = (235, 235, 235)
        muted_col = (175, 160, 130)
    box_rect = p.Rect(x, y, w, box_h)
    p.draw.rect(screen, bg, box_rect, border_radius=8)
    p.draw.rect(screen, border, box_rect, 2, border_radius=8)
    p.draw.rect(screen, inner_bg, p.Rect(x + 7, y + 7, w - 14, box_h - 14), border_radius=6)
    title_font = p.font.SysFont("helvetica", 12, True)
    count_font = p.font.SysFont("helvetica", 11, True)
    empty_font = p.font.SysFont("helvetica", 11, False)
    title_surf = title_font.render(title, True, text_col)
    screen.blit(title_surf, (x + 12, y + 10))
    if len(pieces) == 0:
        empty = empty_font.render("No captured pieces", True, muted_col)
        screen.blit(empty, (x + 12, y + 38))
        return
    piece_counts = {}
    for piece in pieces:
        piece_counts[piece] = piece_counts.get(piece, 0) + 1
    piece_order = ["Q", "R", "B", "N", "p"]
    color_prefix = pieces[0][0]
    grouped_pieces = []
    for piece_type in piece_order:
        piece_key = color_prefix + piece_type
        if piece_key in piece_counts:
            grouped_pieces.append((piece_key, piece_counts[piece_key]))
    icon_size = 18
    start_x = x + 12
    start_y = y + 33
    item_w = 54
    max_per_row = max(1, (w - 24) // item_w)
    for idx, (piece, count) in enumerate(grouped_pieces):
        row = idx // max_per_row
        col = idx % max_per_row
        px = start_x + col * item_w
        py = start_y + row * 22
        if row >= 2:
            more = count_font.render("...", True, muted_col)
            screen.blit(more, (px, py))
            break
        drawPieceBadge(screen, piece, px, py, size=icon_size)
        count_text = f"x{count}"
        count_surf = count_font.render(count_text, True, text_col)
        screen.blit(count_surf, (px + icon_size + 7, py + 3))


def getBotDisplayName(aiMode):
    if aiMode == "pvp":
        return "Player 2"
    if aiMode == "rl":
        return "RL Bot"
    elif aiMode == "hard":
        return "Hard ML Bot"
    elif aiMode == "dynamic":
        return "Fuzzy Dynamic Bot"
    else:
        return "Medium ML Bot"


def drawTimerBox(screen, x, y, w, label, seconds, is_white=True, is_active=False):
    box_h = 50
    if is_white:
        bg = (235, 235, 225)
        inner_bg = (250, 248, 238)
        border = (230, 210, 140)
        active_border = (255, 220, 60)
        text_col = (20, 20, 20)
        time_col = (10, 10, 10)
    else:
        bg = (18, 18, 18)
        inner_bg = (28, 28, 28)
        border = (120, 90, 45)
        active_border = (255, 190, 40)
        text_col = (235, 235, 235)
        time_col = (255, 255, 255)
    if seconds <= 30:
        time_col = (230, 70, 60)
    box_rect = p.Rect(x, y, w, box_h)
    p.draw.rect(screen, bg, box_rect, border_radius=8)
    p.draw.rect(
        screen,
        active_border if is_active else border,
        box_rect, 2, border_radius=8
    )
    p.draw.rect(screen, inner_bg, p.Rect(x + 7, y + 7, w - 14, box_h - 14), border_radius=6)
    label_font = p.font.SysFont("helvetica", 12, True)
    time_font = p.font.SysFont("helvetica", 24, True)
    label_surf = label_font.render(label, True, text_col)
    time_surf = time_font.render(formatTimer(seconds), True, time_col)
    screen.blit(label_surf, (x + 12, y + 8))
    screen.blit(time_surf, (x + w - time_surf.get_width() - 14, y + 15))


def drawProfileCard(screen, x, y, w, h, name, role, piece, is_white=True):
    if is_white:
        card_bg = (235, 235, 225)
        card_inner = (250, 248, 238)
        border = (230, 210, 140)
        text_main = (20, 20, 20)
        text_sub = (90, 80, 60)
        avatar_bg = (18, 18, 18)
        avatar_border = (230, 210, 140)
    else:
        card_bg = (18, 18, 18)
        card_inner = (28, 28, 28)
        border = (120, 90, 45)
        text_main = (235, 235, 235)
        text_sub = (175, 160, 130)
        avatar_bg = (245, 245, 245)
        avatar_border = (120, 120, 120)
    card_rect = p.Rect(x, y, w, h)
    p.draw.rect(screen, card_bg, card_rect, border_radius=10)
    p.draw.rect(screen, border, card_rect, 2, border_radius=10)
    p.draw.rect(screen, card_inner, p.Rect(x + 8, y + 8, w - 16, h - 16), border_radius=8)
    avatar_size = 54
    avatar_x = x + 16
    avatar_y = y + h // 2 - avatar_size // 2
    avatar_rect = p.Rect(avatar_x, avatar_y, avatar_size, avatar_size)
    p.draw.rect(screen, avatar_bg, avatar_rect, border_radius=8)
    p.draw.rect(screen, avatar_border, avatar_rect, 2, border_radius=8)
    if piece in IMAGES:
        piece_img = p.transform.smoothscale(IMAGES[piece], (44, 44))
        screen.blit(piece_img, (avatar_x + 5, avatar_y + 5))
    name_font = p.font.SysFont("helvetica", 18, True)
    role_font = p.font.SysFont("helvetica", 12, False)
    side_font = p.font.SysFont("helvetica", 11, True)
    name_surf = name_font.render(name, True, text_main)
    role_surf = role_font.render(role, True, text_sub)
    screen.blit(name_surf, (x + 82, y + 18))
    screen.blit(role_surf, (x + 82, y + 43))
    side_text = "WHITE PIECES" if is_white else "BLACK PIECES"
    side_surf = side_font.render(side_text, True, text_sub)
    screen.blit(side_surf, (x + 82, y + 64))


def drawPlayerProfilesPanel(screen: p.Surface, gs, board_rect: p.Rect, aiMode, white_time, black_time):
    sw, sh = screen.get_size()
    panel_x = 0
    panel_y = 0
    panel_w = board_rect.left
    panel_h = sh
    if panel_w < 190:
        return
    p.draw.rect(screen, (8, 8, 8), p.Rect(panel_x, panel_y, panel_w, panel_h))
    p.draw.line(screen, (180, 140, 40), (board_rect.left - 1, 0), (board_rect.left - 1, sh), 2)
    margin_x = 18
    gap = 8
    card_w = min(270, panel_w - (margin_x * 2))
    profile_h = 92
    captured_h = 74
    timer_h = 50
    card_x = panel_x + margin_x
    captured_by_white, captured_by_black = getCapturedPieces(gs)
    black_top_y = 28
    black_profile_y = black_top_y
    black_captured_y = black_profile_y + profile_h + gap
    black_timer_y = black_captured_y + captured_h + gap
    bot_name = getBotDisplayName(aiMode)
    drawProfileCard(
        screen=screen, x=card_x, y=black_profile_y, w=card_w, h=profile_h,
        name=bot_name,
        role="Machine Learning Bot" if aiMode != "pvp" else "Human Player",
        piece="bp", is_white=False
    )
    drawCapturedPiecesBox(
        screen=screen, x=card_x, y=black_captured_y, w=card_w,
        title="Captured by Black", pieces=captured_by_black, is_white_owner=False
    )
    drawTimerBox(
        screen=screen, x=card_x, y=black_timer_y, w=card_w,
        label="BLACK TIMER", seconds=black_time, is_white=False, is_active=not gs.whiteToMove
    )
    white_profile_y = sh - 28 - profile_h
    white_captured_y = white_profile_y - gap - captured_h
    white_timer_y = white_captured_y - gap - timer_h
    drawTimerBox(
        screen=screen, x=card_x, y=white_timer_y, w=card_w,
        label="WHITE TIMER", seconds=white_time, is_white=True, is_active=gs.whiteToMove
    )
    drawCapturedPiecesBox(
        screen=screen, x=card_x, y=white_captured_y, w=card_w,
        title="Captured by White", pieces=captured_by_white, is_white_owner=True
    )
    drawProfileCard(
        screen=screen, x=card_x, y=white_profile_y, w=card_w, h=profile_h,
        name="Guest", role="Human Player", piece="wp", is_white=True
    )
    center_top = black_timer_y + timer_h + 16
    center_bottom = white_timer_y - 16
    if center_bottom > center_top:
        mid_x = panel_x + panel_w // 2
        p.draw.line(screen, (70, 55, 25), (mid_x, center_top), (mid_x, center_bottom), 1)
        p.draw.circle(screen, (130, 95, 35), (mid_x, center_top), 3)
        p.draw.circle(screen, (130, 95, 35), (mid_x, center_bottom), 3)


def drawMoveHistoryPanel(screen: p.Surface, gs, board_rect: p.Rect):
    sw, sh = screen.get_size()
    panel_x = board_rect.right
    panel_y = 0
    panel_w = sw - board_rect.right
    panel_h = sh
    if panel_w < 170:
        return
    panel_rect = p.Rect(panel_x, panel_y, panel_w, panel_h)
    p.draw.rect(screen, (12, 12, 12), panel_rect)
    p.draw.line(screen, (180, 140, 40), (panel_x, 0), (panel_x, sh), 2)
    title_font = p.font.SysFont("helvetica", 22, True)
    move_font = p.font.SysFont("helvetica", 16, True)
    small_font = p.font.SysFont("helvetica", 12, False)
    title = title_font.render("MOVE HISTORY", True, p.Color("Gold"))
    screen.blit(title, (panel_x + 18, 24))
    subtitle = small_font.render("Piece  Start  >  Piece End", True, (170, 170, 170))
    screen.blit(subtitle, (panel_x + 18, 52))
    p.draw.line(screen, (90, 70, 25), (panel_x + 15, 75), (panel_x + panel_w - 15, 75), 1)
    move_log = gs.moveLog
    if len(move_log) == 0:
        empty = small_font.render("No moves yet", True, (150, 150, 150))
        screen.blit(empty, (panel_x + 18, 95))
        return
    row_h = 34
    start_y = 92
    max_rows = max(1, (panel_h - start_y - 20) // row_h)
    visible_moves = move_log[-max_rows:]
    END_TEXT_X = 114
    EXTRA_INFO_X = 168
    CAPTURE_ICON_OFFSET = 74
    AFTER_CAPTURE_GAP = 108
    CHECK_GAP = 10
    for i, move in enumerate(visible_moves):
        actual_index = len(move_log) - len(visible_moves) + i
        move_number = actual_index + 1
        is_white_move = actual_index % 2 == 0
        y = start_y + i * row_h
        if is_white_move:
            row_bg = (24, 24, 24)
            accent_color = (245, 220, 120)
            text_color = (235, 235, 235)
            number_color = (230, 230, 230)
        else:
            row_bg = (38, 30, 22)
            accent_color = (180, 120, 55)
            text_color = (235, 235, 235)
            number_color = (210, 190, 160)
        row_rect = p.Rect(panel_x + 10, y - 4, panel_w - 20, row_h)
        p.draw.rect(screen, row_bg, row_rect)
        p.draw.rect(screen, accent_color, p.Rect(panel_x + 10, y - 4, 4, row_h))
        prefix = f"{move_number}."
        prefix_surf = small_font.render(prefix, True, number_color)
        screen.blit(prefix_surf, (panel_x + 18, y + 5))
        piece = move.pieceMoved
        start_sq = squareName(move.startRow, move.startCol)
        end_sq = squareName(move.endRow, move.endCol)
        x0 = panel_x + 58
        PIECE_SIZE = 22
        START_TEXT_X = 26
        ARROW_X = 64
        END_PIECE_X = 86
        END_TEXT_X = 112
        STATUS_X = x0 + 166
        CAPTURE_ICON_X = panel_x + panel_w - 48
        is_capture = move.pieceCaptured != "--"
        is_check = getattr(move, "givesCheck", False)
        drawPieceBadge(screen, piece, x0, y, size=PIECE_SIZE)
        start_surf = move_font.render(start_sq, True, text_color)
        screen.blit(start_surf, (x0 + START_TEXT_X, y + 3))
        arrow_color = p.Color("Gold")
        arrow_surf = move_font.render("→", True, arrow_color)
        screen.blit(arrow_surf, (x0 + ARROW_X, y + 3))
        drawPieceBadge(screen, piece, x0 + 18 + END_PIECE_X, y, size=PIECE_SIZE)
        end_surf = move_font.render(end_sq, True, text_color)
        screen.blit(end_surf, (x0 + 18 + END_TEXT_X, y + 3))
        if is_capture and is_check:
            captures_y = y - 3
            check_y = y + 13
            captures_surf = small_font.render("Captures", True, (235, 120, 90))
            screen.blit(captures_surf, (STATUS_X, captures_y))
            check_surf = small_font.render("Check", True, (255, 215, 0))
            screen.blit(check_surf, (STATUS_X, check_y))
            captured_piece = move.pieceCaptured
            drawPieceBadge(screen, captured_piece, CAPTURE_ICON_X, y, size=22)
        elif is_capture:
            captures_y = y + 7
            captures_surf = small_font.render("Captures", True, (235, 120, 90))
            screen.blit(captures_surf, (STATUS_X, captures_y))
            captured_piece = move.pieceCaptured
            drawPieceBadge(screen, captured_piece, CAPTURE_ICON_X, y, size=22)
        elif is_check:
            check_y = y + 7
            check_surf = small_font.render("Check", True, (255, 215, 0))
            screen.blit(check_surf, (STATUS_X, check_y))


def presentFrame(screen: p.Surface, gs=None, show_history=False, white_time=None, black_time=None):
    sw, sh = screen.get_size()
    if sw == WIDTH and sh == HEIGHT:
        board_rect = p.Rect(0, 0, WIDTH, HEIGHT)
        screen.blit(game_surf, board_rect)
    else:
        scale = min(sw / WIDTH, sh / HEIGHT)
        nw = int(WIDTH * scale)
        nh = int(HEIGHT * scale)
        ox = (sw - nw) // 2
        oy = (sh - nh) // 2
        scaled = p.transform.smoothscale(game_surf, (nw, nh))
        screen.fill((0, 0, 0))
        board_rect = p.Rect(ox, oy, nw, nh)
        screen.blit(scaled, board_rect)
    if show_history and gs is not None:
        current_ai_mode = globals().get("CURRENT_AI_MODE", "alphabeta_ml")
        drawPlayerProfilesPanel(
            screen, gs, board_rect, current_ai_mode,
            white_time if white_time is not None else START_TIME_SECONDS,
            black_time if black_time is not None else START_TIME_SECONDS
        )
        drawMoveHistoryPanel(screen, gs, board_rect)
    p.display.flip()


def screenToGame(mouse_pos, screen: p.Surface):
    sw, sh = screen.get_size()
    if sw == WIDTH and sh == HEIGHT:
        return mouse_pos
    scale = min(sw / WIDTH, sh / HEIGHT)
    nw = int(WIDTH * scale)
    nh = int(HEIGHT * scale)
    ox = (sw - nw) // 2
    oy = (sh - nh) // 2
    gx = (mouse_pos[0] - ox) / scale
    gy = (mouse_pos[1] - oy) / scale
    gx = max(0, min(WIDTH - 1, gx))
    gy = max(0, min(HEIGHT - 1, gy))
    return (int(gx), int(gy))


def setFullscreen():
    info = p.display.Info()
    mw, mh = info.current_w, info.current_h
    screen = p.display.set_mode((mw, mh), p.NOFRAME)
    return screen


def loadImages():
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK', 'wQ',
              'bp', 'bR', 'bN', 'bB', 'bQ', 'bK']
    for piece in pieces:
        IMAGES[piece] = p.transform.smoothscale(
            p.image.load("images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


colors = [p.Color("#F0D9B5"), p.Color("#B58863")]


def drawBoard():
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[(r + c) % 2]
            p.draw.rect(game_surf, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def drawPieces(board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                game_surf.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def animateMove(move, screen, board, clock):
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    frameCount = (abs(dR) + abs(dC)) * 10
    for frame in range(frameCount + 1):
        r = move.startRow + dR * frame / frameCount
        c = move.startCol + dC * frame / frameCount
        drawBoard()
        drawPieces(board)
        color = colors[(move.endRow + move.endCol) % 2]
        endSq = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(game_surf, color, endSq)
        if move.pieceCaptured != '--':
            game_surf.blit(IMAGES[move.pieceCaptured], endSq)
        game_surf.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        presentFrame(screen)
        clock.tick(240)


def highlightLastMove(gs):
    if len(gs.moveLog) == 0:
        return
    lastMove = gs.moveLog[-1]
    start_surface = p.Surface((SQ_SIZE, SQ_SIZE))
    start_surface.set_alpha(180)
    start_surface.fill(p.Color("#FFFF00"))
    end_surface = p.Surface((SQ_SIZE, SQ_SIZE))
    end_surface.set_alpha(220)
    end_surface.fill(p.Color("#FFC107"))
    game_surf.blit(start_surface, (lastMove.startCol * SQ_SIZE, lastMove.startRow * SQ_SIZE))
    game_surf.blit(end_surface, (lastMove.endCol * SQ_SIZE, lastMove.endRow * SQ_SIZE))


def highlightSquares(gs, validMoves, sqSelected):
    if sqSelected != ():
        r, c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color("#F7F769"))
            game_surf.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            s.fill(p.Color("#F5F682"))
            for move in validMoves:
                if move.startRow == r and move.startCol == c:
                    game_surf.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))


def drawGameState(gs, validMoves, sqSelected):
    drawBoard()
    highlightLastMove(gs)
    highlightSquares(gs, validMoves, sqSelected)
    drawPieces(gs.board)


def drawText(text):
    font = p.font.SysFont("helvetica", 32, True, False)
    obj = font.render(text, True, p.Color('Gray'))
    loc = p.Rect(0, 0, WIDTH, HEIGHT).move(
        WIDTH / 2 - obj.get_width() / 2,
        HEIGHT / 2 - obj.get_height() / 2)
    game_surf.blit(obj, loc)
    game_surf.blit(font.render(text, True, p.Color('Black')), loc.move(2, 2))


def drawResignDialog():
    panel_w, panel_h = 320, 140
    px = (WIDTH - panel_w) // 2
    py = (HEIGHT - panel_h) // 2
    dim = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    game_surf.blit(dim, (0, 0))
    p.draw.rect(game_surf, (30, 25, 20), p.Rect(px, py, panel_w, panel_h))
    p.draw.rect(game_surf, (180, 140, 40), p.Rect(px, py, panel_w, panel_h), 2)
    font_q = p.font.SysFont("helvetica", 17, True)
    q1 = font_q.render("Apakah Anda ingin", True, (230, 230, 230))
    q2 = font_q.render("Resign & kembali ke Menu?", True, (230, 230, 230))
    game_surf.blit(q1, (px + panel_w // 2 - q1.get_width() // 2, py + 18))
    game_surf.blit(q2, (px + panel_w // 2 - q2.get_width() // 2, py + 40))
    yes_rect = p.Rect(px + 40, py + 88, 100, 34)
    p.draw.rect(game_surf, (160, 30, 30), yes_rect)
    p.draw.rect(game_surf, (220, 80, 80), yes_rect, 1)
    font_b = p.font.SysFont("helvetica", 16, True)
    yt = font_b.render("Ya, Resign", True, p.Color("white"))
    game_surf.blit(yt, (yes_rect.centerx - yt.get_width() // 2, yes_rect.centery - yt.get_height() // 2))
    no_rect = p.Rect(px + 180, py + 88, 100, 34)
    p.draw.rect(game_surf, (30, 100, 30), no_rect)
    p.draw.rect(game_surf, (80, 200, 80), no_rect, 1)
    nt = font_b.render("Tidak", True, p.Color("white"))
    game_surf.blit(nt, (no_rect.centerx - nt.get_width() // 2, no_rect.centery - nt.get_height() // 2))
    return yes_rect, no_rect


bg_cache = None


def buildMenuBackground():
    surf = p.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        p.draw.line(surf,
                    (int(45 - 35 * ratio), int(28 - 22 * ratio), int(12 - 10 * ratio)),
                    (0, y), (WIDTH, y))
    tile = 32
    overlay = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    for row in range(HEIGHT // tile + 1):
        for col in range(WIDTH // tile + 1):
            clr = (255, 215, 100, 18) if (row + col) % 2 == 0 else (0, 0, 0, 8)
            p.draw.rect(overlay, clr, p.Rect(col * tile, row * tile, tile, tile))
    surf.blit(overlay, (0, 0))
    vig = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    cx, cy = WIDTH // 2, HEIGHT // 2
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            a = int(min(1.0, (dx * dx + dy * dy) ** 0.5) ** 2 * 150)
            if a > 0:
                for px, py in ((x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)):
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        vig.set_at((px, py), (0, 0, 0, a))
    surf.blit(vig, (0, 0))
    light = p.Surface((WIDTH, HEIGHT), p.SRCALPHA)
    for a in [12, 7, 4]:
        p.draw.polygon(light, (255, 240, 190, a),
                       [(0, 0), (WIDTH, 0), (WIDTH - 80, HEIGHT), (-80, HEIGHT)])
    surf.blit(light, (0, 0))
    p.draw.rect(surf, (180, 140, 40), p.Rect(12, 12, WIDTH - 24, HEIGHT - 24), 2)
    p.draw.rect(surf, (100, 75, 20), p.Rect(18, 18, WIDTH - 36, HEIGHT - 36), 1)
    return surf


def drawMenu():
    global bg_cache
    if bg_cache is None:
        bg_cache = buildMenuBackground()
    game_surf.blit(bg_cache, (0, 0))
    font_title = p.font.SysFont("Georgia", 42, True, False)
    font_sub = p.font.SysFont("Helvetica", 13, False, False)
    font_btn = p.font.SysFont("Helvetica", 20, True, False)
    font_note = p.font.SysFont("Helvetica", 11, False, True)
    shadow = font_title.render("Nge-Chess", True, (0, 0, 0))
    title = font_title.render("Nge-Chess", True, p.Color("Gold"))
    tx = WIDTH // 2 - title.get_width() // 2
    game_surf.blit(shadow, (tx + 2, 82))
    game_surf.blit(title, (tx, 80))
    lw, lx = 200, WIDTH // 2 - 100
    p.draw.line(game_surf, (180, 140, 40), (lx, 132), (lx + lw, 132), 1)
    p.draw.line(game_surf, (100, 75, 20), (lx + 10, 135), (lx + lw - 10, 135), 1)
    sub = font_sub.render(
        "Supervised  |  Unsupervised  |  Reinforcement Learning",
        True, (200, 185, 140))
    game_surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 144))

    def drawBtn(y, h, top_rgb, bot_rgb, label, note="",
                lbl_col=p.Color("White"), note_col=(170, 210, 255),
                border_col=(180, 140, 40)):
        bx = WIDTH // 2 - 155
        for dy in range(h):
            ratio = dy / h
            rc = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * ratio)
            gc = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * ratio)
            bc = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * ratio)
            p.draw.line(game_surf, (rc, gc, bc), (bx, y + dy), (bx + 310, y + dy))
        p.draw.rect(game_surf, border_col, p.Rect(bx, y, 310, h), 1)
        lsurf = font_btn.render(label, True, lbl_col)
        ty = y + h // 2 - lsurf.get_height() // 2 - (5 if note else 0)
        game_surf.blit(lsurf, (WIDTH // 2 - lsurf.get_width() // 2, ty))
        if note:
            nsurf = font_note.render(note, True, note_col)
            game_surf.blit(nsurf, (WIDTH // 2 - nsurf.get_width() // 2,
                                   ty + lsurf.get_height() + 3))

    drawBtn(170, 44, (80, 80, 80), (50, 50, 50), "vs Player  (PvP)", lbl_col=(230, 230, 230))
    drawBtn(225, 48, (110, 45, 130), (75, 28, 95),
            "Easy  —  Reinforcement Learning",
            note="TD-Learning Self-Play Agent", note_col=(220, 175, 255))
    drawBtn(285, 48, (42, 82, 155), (28, 55, 110),
            "Medium  —  Alpha-Beta + ML",
            note="Supervised NN + K-Means + Alpha-Beta", note_col=(170, 205, 255))
    drawBtn(345, 48, (130, 25, 25), (90, 15, 15),
            "Hard  —  Enhanced Alpha-Beta + ML",
            note="Supervised NN + K-Means + Alpha-Beta + tactical evaluation",
            note_col=(255, 180, 180))
    drawBtn(405, 48, (160, 105, 20), (105, 65, 15),
            "Dynamic  —  Fuzzy AI Controller",
            note="Fuzzy selects Easy / Medium / Hard based on game state",
            note_col=(255, 220, 150))
    ctrl = font_sub.render(
        "Z = Undo   |   R = Restart   |   M = Menu   |   ESC = Quit",
        True, (110, 95, 70))
    game_surf.blit(ctrl, (WIDTH // 2 - ctrl.get_width() // 2, 470))


def resetGame():
    gs = ChessEngine.GameState()
    return gs, gs.getValidMoves()


def main():
    global game_surf, CURRENT_AI_MODE
    p.init()
    p.display.set_caption("Nge-Chess")
    game_surf = p.Surface((WIDTH, HEIGHT))
    screen = setFullscreen()
    clock = p.time.Clock()
    gs, validMoves = resetGame()
    moveMade = False
    animate = False
    loadImages()
    running = True
    sqSelected = ()
    playerClicks = []
    gameOver = False
    showMenu = True
    showResign = False
    playerOne = True
    playerTwo = False
    humanTurn = False
    aiMode = "alphabeta_ml"
    white_time = START_TIME_SECONDS
    black_time = START_TIME_SECONDS
    last_tick = p.time.get_ticks()

    while running:
        if showMenu:
            drawMenu()
            presentFrame(screen)
            for e in p.event.get():
                if e.type == p.QUIT:
                    running = False
                elif e.type == p.MOUSEBUTTONDOWN:
                    mx, my = screenToGame(p.mouse.get_pos(), screen)
                    bx1, bx2 = WIDTH // 2 - 155, WIDTH // 2 + 155
                    if bx1 <= mx <= bx2:
                        if 170 <= my <= 214:
                            gs, validMoves = resetGame()
                            white_time = START_TIME_SECONDS
                            black_time = START_TIME_SECONDS
                            last_tick = p.time.get_ticks()
                            sqSelected = (); playerClicks = []
                            moveMade = False; animate = False; gameOver = False
                            playerTwo = True
                            CURRENT_AI_MODE = "pvp"
                            showMenu = False
                        elif 225 <= my <= 273:
                            gs, validMoves = resetGame()
                            white_time = START_TIME_SECONDS
                            black_time = START_TIME_SECONDS
                            last_tick = p.time.get_ticks()
                            sqSelected = (); playerClicks = []
                            moveMade = False; animate = False; gameOver = False
                            playerTwo = False
                            aiMode = "rl"
                            CURRENT_AI_MODE = aiMode
                            showMenu = False
                        elif 285 <= my <= 333:
                            gs, validMoves = resetGame()
                            white_time = START_TIME_SECONDS
                            black_time = START_TIME_SECONDS
                            last_tick = p.time.get_ticks()
                            sqSelected = (); playerClicks = []
                            moveMade = False; animate = False; gameOver = False
                            playerTwo = False
                            aiMode = "alphabeta_ml"
                            CURRENT_AI_MODE = aiMode
                            showMenu = False
                        elif 345 <= my <= 393:
                            gs, validMoves = resetGame()
                            white_time = START_TIME_SECONDS
                            black_time = START_TIME_SECONDS
                            last_tick = p.time.get_ticks()
                            sqSelected = (); playerClicks = []
                            moveMade = False; animate = False; gameOver = False
                            playerTwo = False
                            aiMode = "hard"
                            CURRENT_AI_MODE = aiMode
                            showMenu =False
                        elif 405 <= my <= 453:
                            gs, validMoves = resetGame()
                            white_time = START_TIME_SECONDS
                            black_time = START_TIME_SECONDS
                            last_tick = p.time.get_ticks()

                            sqSelected = ()
                            playerClicks = []
                            moveMade = False
                            animate = False
                            gameOver = False

                            playerTwo = False
                            aiMode = "dynamic"
                            CURRENT_AI_MODE = aiMode
                            showMenu = False
                elif e.type == p.KEYDOWN:
                    if e.key == p.K_ESCAPE:
                        running = False
        else:
            humanTurn = (gs.whiteToMove and playerOne) or \
                        (not gs.whiteToMove and playerTwo)
            now = p.time.get_ticks()
            dt = (now - last_tick) / 1000.0
            last_tick = now
            if not gameOver and not showResign:
                if gs.whiteToMove:
                    white_time -= dt
                    if white_time <= 0:
                        white_time = 0
                        gameOver = True
                else:
                    black_time -= dt
                    if black_time <= 0:
                        black_time = 0
                        gameOver = True
            for e in p.event.get():
                if e.type == p.QUIT:
                    running = False
                elif e.type == p.MOUSEBUTTONDOWN:
                    gx, gy = screenToGame(p.mouse.get_pos(), screen)
                    if showResign:
                        drawGameState(gs, validMoves, sqSelected)
                        yes_rect, no_rect = drawResignDialog()
                        click = p.Rect(gx, gy, 1, 1)
                        if click.colliderect(yes_rect):
                            showResign = False
                            showMenu = True
                        elif click.colliderect(no_rect):
                            showResign = False
                        continue
                    if not gameOver and humanTurn:
                        col = gx // SQ_SIZE
                        row = gy // SQ_SIZE
                        if sqSelected == (row, col):
                            sqSelected = (); playerClicks = []
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)
                        if len(playerClicks) == 2:
                            move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    moveMade = True; animate = True
                                    sqSelected = (); playerClicks = []
                            if not moveMade:
                                playerClicks = [sqSelected]
                elif e.type == p.KEYDOWN:
                    if e.key == p.K_ESCAPE:
                        running = False
                        continue
                    if showResign:
                        continue
                    if e.key == p.K_z:
                        sqSelected = (); playerClicks = []; gameOver = False
                        if not playerTwo:
                            if humanTurn:
                                if len(gs.moveLog) >= 2:
                                    gs.undoMove(); gs.undoMove()
                                elif len(gs.moveLog) == 1:
                                    gs.undoMove()
                            else:
                                if len(gs.moveLog) >= 1:
                                    gs.undoMove()
                        else:
                            if len(gs.moveLog) >= 1:
                                gs.undoMove()
                        validMoves = gs.getValidMoves()
                        moveMade = False; animate = False
                    elif e.key == p.K_r:
                        gs, validMoves = resetGame()
                        white_time = START_TIME_SECONDS
                        black_time = START_TIME_SECONDS
                        last_tick = p.time.get_ticks()
                        sqSelected = (); playerClicks = []
                        moveMade = False; animate = False; gameOver = False
                    elif e.key == p.K_m:
                        if not gameOver and len(gs.moveLog) > 0:
                            showResign = True
                        else:
                            showMenu = True
            if not gameOver and not humanTurn and not showResign:
                ai_start_tick = p.time.get_ticks()

                drawGameState(gs, validMoves, sqSelected)
                presentFrame(screen, gs, show_history=True, white_time=white_time, black_time=black_time)
                p.event.pump()

                if aiMode == "rl":
                    AIMove = ChessSmartMoveFinder.findBestMoveRL(gs, validMoves)

                elif aiMode == "dynamic":
                    AIMove = ChessSmartMoveFinder.findBestMoveDynamic(
                        gs,
                        validMoves,
                        white_time=white_time,
                        black_time=black_time
                    )

                elif aiMode == "hard":
                    AIMove = ChessSmartMoveFinder.findBestMoveHard(
                        gs,
                        validMoves,
                        white_time=white_time,
                        black_time=black_time
                    )

                else:
                    AIMove = ChessSmartMoveFinder.findBestMoveAlphaBeta(gs, validMoves)

                ai_end_tick = p.time.get_ticks()
                ai_think_seconds = (ai_end_tick - ai_start_tick) / 1000.0

                black_time -= ai_think_seconds
                if black_time <= 0:
                    black_time = 0
                    gameOver = True

                last_tick = p.time.get_ticks()

                if not gameOver:
                    if AIMove is None:
                        AIMove = ChessSmartMoveFinder.findRandomMove(validMoves)

                    gs.makeMove(AIMove)
                    moveMade = True
                    animate = True
                
            if moveMade:
                if animate:
                    animateMove(gs.moveLog[-1], screen, gs.board, clock)
                validMoves = gs.getValidMoves()
                moveMade = False; animate = False
            drawGameState(gs, validMoves, sqSelected)
            if white_time <= 0:
                gameOver = True
                drawText('Black Wins on Time')
            elif black_time <= 0:
                gameOver = True
                drawText('White Wins on Time')
            elif gs.checkmate:
                gameOver = True
                drawText('Black Wins' if gs.whiteToMove else 'White Wins')
            elif gs.stalemate:
                gameOver = True
                drawText('Stalemate')
            elif gs.repetitionDraw:
                gameOver = True
                drawText('Draw by Repetition')
            if showResign:
                drawResignDialog()
            presentFrame(screen, gs, show_history=True, white_time=white_time, black_time=black_time)
        clock.tick(MAX_FPS)
    p.quit()


if __name__ == "__main__":
    main()
