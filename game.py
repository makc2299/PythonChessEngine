# 08.05.21

import numpy as np
import pygame
import random
import time
import sys
from interface import Interface, Timer
from ai import Ai, BoardState
from itertools import groupby
from collections import Counter
from functools import reduce
from table import mvv_lva, mvv_lva_const, piece_phase_const

# Board / piece constant (bitboards)
FILLED = 0xffffffffffffffff
EMPTY = 0
B_BOARD = int

H_FILE = 0x0101010101010101
G_FILE = H_FILE << 1
F_FILE = G_FILE << 1
E_FILE = F_FILE << 1
D_FILE = E_FILE << 1
C_FILE = D_FILE << 1
B_FILE = C_FILE << 1
A_FILE = B_FILE << 1

RANK_1 = 0xff
RANK_2 = RANK_1 << 8
RANK_3 = RANK_2 << 8
RANK_4 = RANK_3 << 8
RANK_5 = RANK_4 << 8
RANK_6 = RANK_5 << 8
RANK_7 = RANK_6 << 8
RANK_8 = RANK_7 << 8

PIECES = [KING, QUEEN, KNIGHT, BISHOP, ROOK, PAWN] = range(6)
PROMOTION = ['N', 'n', 'B', 'b', 'Q', 'q', 'R', 'r']

FIELDS = [
	A8, B8, C8, D8, E8, F8, G8, H8,
	A7, B7, C7, D7, E7, F7, G7, H7,
	A6, B6, C6, D6, E6, F6, G6, H6,
	A5, B5, C5, D5, E5, F5, G5, H5,
	A4, B4, C4, D4, E4, F4, G4, H4,
	A3, B3, C3, D3, E3, F3, G3, H3,
	A2, B2, C2, D2, E2, F2, G2, H2,
	A1, B1, C1, D1, E1, F1, G1, H1,
] = range(63, -1, -1)

SQ_NUM = {
	'a1': A1, 'a2': A2, 'a3': A3, 'a4': A4, 'a5': A5, 'a6': A6, 'a7': A7, 'a8': A8,
	'b1': B1, 'b2': B2, 'b3': B3, 'b4': B4, 'b5': B5, 'b6': B6, 'b7': B7, 'b8': B8,
	'c1': C1, 'c2': C2, 'c3': C3, 'c4': C4, 'c5': C5, 'c6': C6, 'c7': C7, 'c8': C8,
	'd1': D1, 'd2': D2, 'd3': D3, 'd4': D4, 'd5': D5, 'd6': D6, 'd7': D7, 'd8': D8,
	'e1': E1, 'e2': E2, 'e3': E3, 'e4': E4, 'e5': E5, 'e6': E6, 'e7': E7, 'e8': E8,
	'f1': F1, 'f2': F2, 'f3': F3, 'f4': F4, 'f5': F5, 'f6': F6, 'f7': F7, 'f8': F8,
	'g1': G1, 'g2': G2, 'g3': G3, 'g4': G4, 'g5': G5, 'g6': G6, 'g7': G7, 'g8': G8,
	'h1': H1, 'h2': H2, 'h3': H3, 'h4': H4, 'h5': H5, 'h6': H6, 'h7': H7, 'h8': H8,
}

F_NAME = dict([(v, k) for k, v in SQ_NUM.items()])
F_NUMB = dict([ (s, n) for n,s in enumerate('abcdefgh')])

SQUARE_MASK = [1 << sq for sq in range(64)]

SQUARE_NAMES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

BASEBOARD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
#"rnb2knr/pp1p1pp1/4p2p/2b4Q/4PP2/5N2/PqPB2PP/RN2KB1R b - - 0 1"
# rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 
# "RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbkqbnr w KQkq - 0 1"
BASEBOARD_BLACK = ' '.join([BASEBOARD.split(" ")[0][::-1]]+BASEBOARD.split(" ")[1:]) if BASEBOARD.split(" ")[3] == "-"  else \
				  ' '.join([BASEBOARD.split(" ")[0][::-1]]+BASEBOARD.split(" ")[1:3]+[ F_NAME[63-SQ_NUM[BASEBOARD.split(" ")[3]]] ]+BASEBOARD.split(" ")[4:])

zobrist_table = [[[random.randint(1,2**64 - 1) for i in range(12)]for j in range(8)]for k in range(8)]
indexing = {"P": 0, "N": 1, "B": 2, "R": 3, "Q": 4, "K": 5,
			"p": 6, "n": 7, "b": 8, "r": 9, "q": 10, "k": 11}

KSCR_W = 0x6
KSCR_B = 0x600000000000000

QSCR_W = 0x30
QSCR_B = 0x3000000000000000

BB_H1 = 1
BB_A1 = 0x80
BB_H8 = 0x100000000000000
BB_A8 = 0x8000000000000000

# SIMPLE MOVE METHODS

def _shift_down(b: B_BOARD):
	return b >> 8

def _shift_down_down(b: B_BOARD):
	return b >> 16

def _shift_up(b: B_BOARD):
	return (b << 8) & FILLED

def _shift_up_up(b: B_BOARD):
	return (b << 16) & FILLED

def _shift_right(b: B_BOARD):
	return ((b >> 1) & ~A_FILE) & FILLED

def _shift_right_right(b: B_BOARD):
	return ((b >> 2) & ~A_FILE & ~B_FILE) & FILLED

def _shift_left(b: B_BOARD):
	return ((b << 1) & ~H_FILE) & FILLED

def _shift_left_left(b: B_BOARD):
	return ((b << 2) & ~H_FILE & ~G_FILE) & FILLED

def _shift_right_up(b: B_BOARD):
	return (b & ~A_FILE) << 9 & FILLED

def _shift_right_down(b: B_BOARD):
	return (b & ~A_FILE) >> 7

def _shift_left_up(b: B_BOARD):
	return (b & ~H_FILE) << 7 & FILLED

def _shift_left_down(b: B_BOARD):
	return (b & ~H_FILE) >> 9

STEPS = [_shift_right, _shift_left, _shift_up, _shift_down]
SLIDES = [_shift_right_up, _shift_right_down, _shift_left_down, _shift_left_up]
DIRECTIONS = STEPS + SLIDES

# PRIVATE STATIC METHODS

def _mask(x):
	return SQUARE_MASK[x]

def _lsb(b):
	return (b & -b).bit_length() - 1

def _msb(b):
	return b.bit_length() - 1

def _scan_lsb_first(b):
	while b:
		r = b & -b
		yield r.bit_length() - 1
		b ^= r

def _scan_single_values(b):
	v = 1
	while b:
		if b & 1:
			yield v
		b = b >> 1
		v = v << 1

def _set_bit(b, index, x):
	mask = 1 << index
	b &= ~mask
	if x:
		b |= mask
	return b

def _put(b, v):
	return b | v

def _pop(b, v):
	return b & ~v

def from_board_cord_to_bit_shift(cord):
	return (7-cord[1])*8 + (7-cord[0])
	
def from_bit_shift_to_board_cord(shift):
	return (F_NUMB[F_NAME[shift][:1]], 7-shift//8)

def b_board_to_str(b):
	return '\n'.join(['{0:064b}'.format(b)[i:i + 8] for i in range(0, 64, 8)])

def _pad_with(vector, pad_width, iaxis, kwargs):
	pad_value = kwargs.get('padder', '.')
	vector[:pad_width[0]] = pad_value
	vector[-pad_width[1]:] = pad_value

# Declaration of a general class and classes 
# of chess pieces inherited from it
#-----------------------------------------------------------------------
class Piece:
	def __init__(self, position):
		self.position = position

	def get_pieces_cords(self, piece=None):
		piece = piece if piece else self.position
		for shift in _scan_lsb_first(piece):
			yield (F_NUMB[F_NAME[shift][:1]], 7-shift//8)

	def _movement_delta(self, square, delta, occupied, enemies):
		moves = 0
		sq = square

		while True:
			sq = delta(sq)
			if sq & occupied:
				return moves
			moves |= sq
			if sq & enemies or sq == 0:
				return moves


class King(Piece):
	def __init__(self, color, position, img):
		super().__init__(position)
		self.img = img
		self.side = color
		self.size = img.get_size()

	def get_moves(self, king, occupied, enemies):
		moves = 0
		for mov in DIRECTIONS:
			moves |= mov(king)
		return moves & ~(occupied | enemies)

	def get_attacks(self, king, *args):
		moves = 0
		for mov in DIRECTIONS:
			moves |= mov(king)
		return moves & args[1]

	def get_valid_moves(self, king, occupied, *args):
		moves = 0
		for mov in DIRECTIONS:
			moves |= mov(king)
		return moves & ~occupied

class Queen(Piece):
	def __init__(self, color, position, img):
		super().__init__(position)
		self.img = img
		self.side = color
		self.size = img.get_size()

	def get_moves(self, queen, occupied, enemies):
		moves = 0
		for mov in DIRECTIONS:
			moves |= self._movement_delta(queen, mov, occupied, enemies)
		return moves & ~enemies

	def get_attacks(self, queen, occupied, enemies):
		moves = 0
		for mov in DIRECTIONS:
			moves |= self._movement_delta(queen, mov, occupied, enemies)
		return moves & enemies

	def get_valid_moves(self, queen, occupied, enemies):
		moves = 0
		for mov in DIRECTIONS:
			moves |= self._movement_delta(queen, mov, occupied, enemies)
		return moves

	def check_direction(self, king: B_BOARD, queen: B_BOARD, occupied_cells: B_BOARD) -> B_BOARD:
		for mov in DIRECTIONS:
			move = queen
			sq = queen
			while True:
				sq = mov(sq)
				if sq == 0 or sq & occupied_cells:
					break
				if sq & king:
					return move 
				move |= sq
		return 0

class Bishops(Piece):
	def __init__(self, color, position, img):
		super().__init__(position)
		self.img = img
		self.side = color
		self.size = img.get_size()

	def get_moves(self, bishop, occupied, enemies):
		moves = 0
		for slide in SLIDES:
			moves |= self._movement_delta(bishop, slide, occupied, enemies)
		return moves & ~enemies

	def get_attacks(self, bishop, occupied, enemies):
		moves = 0
		for slide in SLIDES:
			moves |= self._movement_delta(bishop, slide, occupied, enemies)
		return moves & enemies

	def get_valid_moves(self, bishop, occupied, enemies):
		moves = 0
		for slide in SLIDES:
			moves |= self._movement_delta(bishop, slide, occupied, enemies)
		return moves

	def check_direction(self, king: B_BOARD, bishop: B_BOARD, occupied_cells: B_BOARD) -> B_BOARD:
		for mov in SLIDES:
			move = bishop
			sq = bishop
			while True:
				sq = mov(sq)
				if sq == 0 or sq & occupied_cells:
					break
				if sq & king:
					return move 
				move |= sq
		return 0


class Knights(Piece):
	def __init__(self, color, position, img):
		super().__init__(position)
		self.img = img
		self.side = color
		self.size = img.get_size()
		self.knight_moves = [
			lambda x: _shift_left(_shift_down_down(x)),
			lambda x: _shift_left(_shift_up_up(x)),
			lambda x: _shift_right(_shift_up_up(x)),
			lambda x: _shift_right(_shift_down_down(x)),
			lambda x: _shift_up(_shift_right_right(x)),
			lambda x: _shift_up(_shift_left_left(x)),
			lambda x: _shift_down(_shift_right_right(x)),
			lambda x: _shift_down(_shift_left_left(x)),
		]

	def get_moves(self, knight, occupied, enemies):
		moves = 0
		for move in self.knight_moves:
			moves |= move(knight)
		return moves & ~(occupied | enemies)

	def get_attacks(self, knight, *args):
		moves = 0
		for move in self.knight_moves:
			moves |= move(knight)
		return moves & args[1]

	def get_valid_moves(self, knight, occupied, *args):
		moves = 0
		for move in self.knight_moves:
			moves |= move(knight)
		return moves & ~occupied

	def check_direction(self, king: B_BOARD, knight: B_BOARD, occupied_cells: B_BOARD) -> B_BOARD:
		for move in self.knight_moves:
			if king & move(knight):
				return knight
		return 0 

class Rooks(Piece):
	def __init__(self, color, position, img):
		super().__init__(position)
		self.img = img
		self.side = color
		self.size = img.get_size()

	def get_moves(self, rook, occupied, enemies):
		moves = 0
		for step in STEPS:
			moves |= self._movement_delta(rook, step, occupied, enemies)
		return moves & ~enemies

	def get_attacks(self, rook, occupied, enemies):
		moves = 0
		for step in STEPS:
			moves |= self._movement_delta(rook, step, occupied, enemies)
		return moves & enemies

	def get_valid_moves(self, rook, occupied, enemies):
		moves = 0
		for step in STEPS:
			moves |= self._movement_delta(rook, step, occupied, enemies)
		return moves

	def check_direction(self, king: B_BOARD, rook: B_BOARD, occupied_cells: B_BOARD) -> B_BOARD:
		for mov in STEPS:
			move = rook
			sq = rook
			while True:
				sq = mov(sq)
				if sq == 0 or sq & occupied_cells:
					break
				if sq & king:
					return move 
				move |= sq
		return 0

class Pawns(Piece):
	def __init__(self, color, position, img):
		super().__init__(position)
		self.img = img
		self.side = color
		self.size = img.get_size()

	def get_moves(self, pawn, occupied, enemies):
		if self.side:
			return (_shift_up(pawn) | _shift_up_up(pawn & RANK_2)) & ~(occupied | enemies) \
					 if _shift_up(pawn) & ~(occupied | enemies) else 0
		return (_shift_down(pawn) | _shift_down_down(pawn & RANK_7)) & ~(occupied | enemies) \
					 if _shift_down(pawn) & ~(occupied | enemies) else 0

	def get_attacks(self, pawn, *args):
		if self.side:
			return (_shift_right_up(pawn) | _shift_left_up(pawn)) & args[1]
		return (_shift_right_down(pawn) | _shift_left_down(pawn)) & args[1]

	def get_valid_moves(self, pawn, occupied, enemies):
		if self.side:
			return _shift_right_up(pawn) | _shift_left_up(pawn)
		return _shift_right_down(pawn) | _shift_left_down(pawn)

	def check_direction(self, king: B_BOARD, pawn: B_BOARD, occupied_cells: B_BOARD) -> B_BOARD:
		if self.side:
			return pawn if (_shift_right_up(pawn) | _shift_left_up(pawn)) & king else 0
		return pawn if (_shift_right_down(pawn) | _shift_left_down(pawn)) & king else 0

#-----------------------------------------------------------------------
# I use the bitboard representation to represent the board as 64-bit word
class Board(Interface):

	def __init__(self, x, y, scaling_factor, side, piece_img_dict, board_img, board_reverse_img, fen=None):
		# INTERFACE
		super().__init__(scaling_factor)
		self.cord = (x*scaling_factor[0],y*scaling_factor[1])
		self.board_img = Interface.transfor_scale(self, board_img)
		self.board_reverse_img = Interface.transfor_scale(self, board_reverse_img)
		self.board_rect = pygame.Rect(self.cord[0]+3, self.cord[1]+3,
									  self.board_img.get_size()[0]-6*scaling_factor[0],
									  self.board_img.get_size()[1]-6*scaling_factor[1])
		self.dot_img = Interface.transfor_scale(self, pygame.image.load('images/pieces/dot.png'))
		self.dot_img_size = self.dot_img.get_size()
		self.ring_img = Interface.transfor_scale(self, pygame.image.load('images/pieces/ring.png'))
		self.ring_img_size = self.ring_img.get_size()
		self.from_cell_img = Interface.transfor_scale(self, pygame.image.load('images/pieces/from_cell.png'))
		self.from_cell_img_size = self.from_cell_img.get_size()
		self.check_warning_img = Interface.transfor_scale(self, pygame.image.load('images/pieces/check_warning.png'))
		self.single_cell_size = ((self.board_rect[2])/8, (self.board_rect[3])/8)
		self.board = self._set_image_from_piece(
				side, {key:Interface.transfor_scale(self, img) for key, img in piece_img_dict.items()})
		
		# FEN
		self.fen = BASEBOARD if fen is None else fen
		self.from_fen(self.fen)

		# STATE
		self.endgame_phase_limit = 14
		self.is_check_mate = None
		self.is_stale_mate = None
		self.move_done = 0
		self.update_game_phase()

		self.move_stack = []
		# Zobrist hashing
		self.zobrist_enpassant = [0]*8
		self.zobrist_castling = {'K': 0, 'Q': 0, 'k': 0, 'q': 0}
		self.zobrist_black_to_move = 0
		self.zobrist_key = self.compute_hash()

		# Keep track of where pawns are located on the board for evaluation
		self.init_piece_columns()

		self.push_call = 0


	def call_transfor_scale(self, img):
		return super(Board, self).transfor_scale(img)
		
	# Prints a representation figures on the board in the console
	def __str__(self):
		b = 64 * ['.']
		for key, piece in self.PIECES.items():
			for bb in _scan_lsb_first(piece.position):
				b[bb] = key
		b = ''.join(b[::-1])
		return '\n'.join([ b[i:i+8] for i in range(0,64,8)])

	# board = [
	# 	['.', '.', '.', 'K', '.', '.', '.', '.'],
	# 	['.', 'R', '.', '.', '.', '.', 'Q', '.'],
	# 	['.', '.', '.', '.', '.', '.', '.', '.'],
	# 	['.', 'P', '.', '.', '.', '.', 'p', '.'],
	# 	['.', '.', '.', '.', '.', 'p', '.', '.'],
	# 	['.', '.', '.', '.', '.', '.', '.', '.'],
	# 	['p', '.', '.', '.', 'b', '.', '.', 'q'],
	# 	['.', '.', '.', '.', 'n', '.', '.', 'k']
	# ]
	# return board in this ^ representation
	def board_as_array(self, wrapped=False):
		# wraps in dots
		if wrapped:
			b = np.array(64 * ['.'])
			for key, piece in self.PIECES.items():
				for bb in _scan_lsb_first(piece.position):
					b[bb] = key
			return np.pad(np.flip(np.reshape(b, (8,8))), 1, _pad_with) 
		else:
			b = 64 * ['.']
			for key, piece in self.PIECES.items():
				for bb in _scan_lsb_first(piece.position):
					b[bb] = key
			return [ b[i:i+8][::-1] for i in range(0,63,8)][::-1]

	def draw_board(self, background, reverse):
		if reverse:
			background.blit(self.board_img, self.cord)
		else:
			background.blit(self.board_reverse_img, self.cord)

	def draw_pieces(self, background):
		for piece in self.PIECES.values():
			for cord in piece.get_pieces_cords():
				background.blit(piece.img,
				 ((self.board_rect[0]+self.single_cell_size[0]*cord[0])+self.single_cell_size[0]/2-piece.size[0]/2,
				  (self.board_rect[1]+self.single_cell_size[1]*cord[1])+self.single_cell_size[1]/2-piece.size[1]/2))

	def _set_image_from_piece(self, side, piece_img_dict):
		print (piece_img_dict)
		self.PIECES = {
			'p': Pawns(not side, 0, piece_img_dict['bP']),
			'b': Bishops(not side, 0, piece_img_dict['bB']),
			'n': Knights(not side, 0, piece_img_dict['bN']),
			'k': King(not side, 0, piece_img_dict['bK']),
			'q': Queen(not side, 0, piece_img_dict['bQ']),
			'r': Rooks(not side, 0, piece_img_dict['bR']),
			'P': Pawns(side, 0, piece_img_dict['wP']),
			'B': Bishops(side, 0, piece_img_dict['wB']),
			'N': Knights(side, 0, piece_img_dict['wN']),
			'K': King(side, 0, piece_img_dict['wK']),
			'Q': Queen(side, 0, piece_img_dict['wQ']),
			'R': Rooks(side, 0, piece_img_dict['wR'])
		}

	def change_pawn_to(self, pawn_pos_bitboard, key):
		self.PIECES['P' if not self.active_player else 'p'].position &= ~pawn_pos_bitboard
		self.PIECES[key].position ^= pawn_pos_bitboard
		# if user pick rook add to rook columns 
		if key in ["R","r"]:
			self.rook_columns_list[self.active_player].append( 7-(_lsb(pawn_pos_bitboard)%8) )
	
	def from_fen(self, text):
		# reset all values
		self.reset()

		sq = 1 << 63

		text = text.split(' ')
		if len(text) != 6:
			raise ValueError("Invalid FEN string supplied")

		pieces = text[0]
		for symbol in pieces:
			if symbol.isdigit():
				sq = sq >> int(symbol)
			elif symbol in self.PIECES:
				self.PIECES[symbol].position |= sq
				sq = sq >> 1
		self.active_player = True if text[1] == 'w' else False
		self.black_king_side_castle_right = 'k' in text[2]
		self.black_queen_side_castle_right = 'q' in text[2]
		self.white_king_side_castle_right = 'K' in text[2]
		self.white_queen_side_castle_right = 'Q' in text[2]
		self.ep_move = text[3] if text[3] != "-" else None
		self.half_move_clock = int(text[4])
		self.move_number = int(text[5])

	def to_fen(self) -> str:
		s = 64 * ['.']

		# place all piece symbols
		for symbol, piece in self.PIECES.items():
			for k in _scan_lsb_first(piece.position):
				s[63 - k] = symbol

		# insert /
		for i in range(7):
			s.insert(8 + i * 8 + i, '/')

		# replace .
		s = [str(len(list(s))) if _ else ''.join(list(s)) for _, s in groupby(s, key=lambda x: x == '.')]

		# append additional state information
		s.append(' w ' if self.active_player else ' b ')
		s.append('K' if self.white_king_side_castle_right else '')
		s.append('Q' if self.white_queen_side_castle_right else '')
		s.append('k' if self.black_king_side_castle_right else '')
		s.append('q' if self.black_queen_side_castle_right else '')
		s.append('-' if not any((self.black_queen_side_castle_right,
								 self.black_king_side_castle_right,
								 self.white_queen_side_castle_right,
								 self.white_king_side_castle_right
								 )) else '')
		s.append(' {} '.format(self.ep_move if self.ep_move else '-'))
		s.append('{} '.format(self.half_move_clock))
		s.append('{}'.format(self.move_number))

		return ''.join(s)

	def to_uci(self, from_: int, to_: int) -> str:
		return F_NAME[from_]+F_NAME[to_]

	# form e2e4 -> d7d5
	def mirror_move(self, move: str) -> str:
		return F_NAME[63-SQ_NUM[move[:2]]]+F_NAME[63-SQ_NUM[move[2:]]]

	# unfolds fen when changing perspective
	def reverse_fen(self, fen:str) -> str:
		fen = fen.split(' ')
		if fen[3] == "-":
			return ' '.join([fen[0][::-1]]+fen[1:])
		else:
			return ' '.join([fen[0][::-1]]+fen[1:3]+[ F_NAME[63-SQ_NUM[fen[3]]] ]+fen[4:])

	def compute_hash(self):
		h = 0
		board = self.board_as_array()
		for i in range(8):
			for j in range(8):
				if board[i][j] != '.':
					piece = indexing[board[i][j]]
					h ^= zobrist_table[i][j][piece]

		# Enpassant, castling, black to move
		for col in range(8):
			self.zobrist_enpassant[col] = random.getrandbits(64)
			h ^= self.zobrist_enpassant[col]
		for castle_side in 'KQkq':
			self.zobrist_castling[castle_side] = random.getrandbits(64)
			h ^= self.zobrist_castling[castle_side]
		self.zobrist_black_to_move = random.getrandbits(64)
		h ^= self.zobrist_black_to_move

		return h

	def init_piece_columns(self):
		self.pawn_columns_list, self.rook_columns_list = [[], []], [[], []]
		# init pawns column list
		for shift in _scan_lsb_first(self.PIECES["P"].position):
			self.pawn_columns_list[0].append(7-(shift%8))
		for shift in _scan_lsb_first(self.PIECES["p"].position):
			self.pawn_columns_list[1].append(7-(shift%8))

		# init rook columns list
		for shift in _scan_lsb_first(self.PIECES["R"].position):
			self.rook_columns_list[0].append(7-(shift%8))
		for shift in _scan_lsb_first(self.PIECES["r"].position):
			self.rook_columns_list[1].append(7-(shift%8))

	def update_game_phase(self):
		# get pieces from the board and their number
		# Counter({'p': 1, 'b': 1, 'k': 1, 'P': 1, 'K': 1, 'R': 1})
		piece_dict = Counter([ key for key in self.PIECES for _ in _scan_lsb_first(self.PIECES[key].position) if self.PIECES[key].position != 0 ])
		gamestate_phase = sum([piece_phase_const[piece] * piece_dict[piece] for piece in piece_dict])
		self.is_endgame = min(1, int((24 - gamestate_phase) / (24 - self.endgame_phase_limit)))

	def reset(self):
		"""
		initialize default values
		"""
		for piece in self.PIECES.values():
			piece.position = 0

		# STATE
		self.active_player = 1
		self.black_king_side_castle_right = True
		self.black_queen_side_castle_right = True
		self.white_king_side_castle_right = True
		self.white_queen_side_castle_right = True
		self.ep_move = None
		self.half_move_clock = 0
		self.move_number = 0

	def all_white_pieces(self) -> int:
		pieces = 0
		for symbol, piece in self.PIECES.items():
			if symbol.isupper():
				pieces |= piece.position
		return pieces

	def all_black_pieces(self) -> int:
		pieces = 0
		for symbol, piece in self.PIECES.items():
			if symbol.islower():
				pieces |= piece.position
		return pieces

	def all_pieces(self) -> int:
		return self.all_black_pieces() | self.all_white_pieces()

	def filter_pieces_by_side(self, player):
		return [v for k, v in self.PIECES.items() if (k.isupper() if player else k.islower())]

	def attacked_fields(self, player, without=None) -> int:
		"""
		Returns every field that is currently under attack by the specified player
		"""
		attack_fields = 0
		occupied, enemies = (self.all_white_pieces(), self.all_black_pieces()) if player else (self.all_black_pieces(), self.all_white_pieces())
		"""
		also includes his own pieces that are on the battle line of their own pieces
		"""
		if without:
			occupied, enemies = enemies, occupied
		for key, piece in (list(self.PIECES.items())[6:] if player else list(self.PIECES.items())[:6]):
			for shift in _scan_lsb_first(piece.position):
				attack_fields |= piece.get_valid_moves(1<<shift, occupied, enemies)
		return attack_fields

	def make_move(self, shift, key, piece, side) -> "for taken figure return: move, attack, king coordinates for check warning, castling":
		"""
		- checking if move is legal
		- check for ep and castle
		- checks if a move is available when the king is under attack
		"""
		if key in ['K','k']:

			cell_under_attack = self.attacked_fields(not self.active_player, True)
			#occupied = self.all_white_pieces() if self.active_player else self.all_black_pieces()
			occupied, enemies = (self.all_white_pieces(), self.all_black_pieces()) if self.active_player \
								 else (self.all_black_pieces(), self.all_white_pieces())

			castling = self.castling(1<<shift, side, cell_under_attack, occupied, enemies)
			moves = piece.get_moves(1<<shift, occupied, enemies) & ~cell_under_attack
			attacks = piece.get_attacks(1<<shift, occupied, enemies) & ~cell_under_attack
			return moves | (1<<shift), attacks, False, castling
		
		# add ep move if it's admissible
		elif key in ['P','p']:
			occupied, enemies = (self.all_white_pieces(), self.all_black_pieces()) if self.active_player \
								 else (self.all_black_pieces(), self.all_white_pieces())
			moves = piece.get_moves(1<<shift, occupied, enemies)
			attacks = piece.get_attacks(1<<shift, occupied, enemies)
			if self.ep_move:
				taking = piece.get_valid_moves(1<<shift, 0, 0) & SQUARE_MASK[SQ_NUM[self.ep_move]]
				if taking:
					# check situation when king is under attack after ep move
					# do pseudo move
					sq = (1 << (SQ_NUM[self.ep_move] - 8) if self.active_player else 1 << (SQ_NUM[self.ep_move] + 8)) \
						if side else (1 << (SQ_NUM[self.ep_move] + 8) if self.active_player else 1 << (SQ_NUM[self.ep_move] - 8))
					self.PIECES['P' if self.active_player else 'p'].position ^= taking # put pawn
					self.PIECES['p' if self.active_player else 'P'].position ^= sq # extract enemy pawn
					if not self.check():
						attacks |= taking
					# undo pseudo move
					self.PIECES['P' if self.active_player else 'p'].position ^= taking # extract pawn
					self.PIECES['p' if self.active_player else 'P'].position ^= sq # return enemy pawn			
					
			if self.check():
				fight_directoins = self.find_fight_directions(occupied | enemies)
				# if the king is under several checks only he can hit and move
				direction, figure_pos, _ =  (0, 0, 0) if len(fight_directoins) > 1 else fight_directoins[0]
				return ((moves & direction) | (1<<shift), attacks & figure_pos, list(self.PIECES['K' if self.active_player else 'k'].get_pieces_cords())[0], 0)  
			else:
				return (moves | (1<<shift), attacks, None, 0)
		else: 
			occupied, enemies = (self.all_white_pieces(), self.all_black_pieces()) if self.active_player \
								 else (self.all_black_pieces(), self.all_white_pieces())
			moves = piece.get_moves(1<<shift, occupied, enemies)
			attacks = piece.get_attacks(1<<shift, occupied, enemies)
			if self.check():
				fight_directoins = self.find_fight_directions(occupied | enemies)
				# if the king is under several checks only he can hit and move
				direction, figure_pos, _ =  (0, 0, 0) if len(fight_directoins) > 1 else fight_directoins[0]
				return ((moves & direction) | (1<<shift), attacks & figure_pos, list(self.PIECES['K' if self.active_player else 'k'].get_pieces_cords())[0], 0)  
			else:
				return (moves | (1<<shift), attacks, None, 0)

		# self.moves = moves | (1 << shift)
		# self.attacks = piece.get_attacks(1<<shift, self.board.all_white_pieces(), self.board.all_black_pieces()) \
		# 								if self.board.active_player else piece.get_attacks(1<<shift, self.board.all_black_pieces(), self.board.all_white_pieces())
		# self.valid_move = self.moves | self.attacks | (1 << shift)

	def castling(self, king, side, cell_under_attack, occupied, enemies) -> B_BOARD:

		castling = 0

		# Castling 
		if side:
			if self.white_king_side_castle_right and (king & ~cell_under_attack):
				move = (_shift_right(king) | _shift_right_right(king)) & ~cell_under_attack & ~occupied
				if move == KSCR_W:
					castling |= (1<<_lsb(move))
			if self.white_queen_side_castle_right and (king & ~cell_under_attack):
				move = ((_shift_left(king) | _shift_left_left(king)) & ~cell_under_attack & ~occupied) | (_shift_left(_shift_left_left(king)) & occupied)
				if move == QSCR_W:
					castling |= (1<<_msb(move))
			if self.black_king_side_castle_right and (king & ~cell_under_attack):
				move = (_shift_right(king) | _shift_right_right(king)) & ~cell_under_attack & ~occupied
				if move == KSCR_B:
					castling |= (1<<_lsb(move))
			if self.black_queen_side_castle_right and (king & ~cell_under_attack):
				move = ((_shift_left(king) | _shift_left_left(king)) & ~cell_under_attack & ~occupied) | (_shift_left(_shift_left_left(king)) & occupied)
				if move == QSCR_B:
					castling |= (1<<_msb(move))
		else:
			if self.white_king_side_castle_right and (king & ~cell_under_attack):
				move = (_shift_left(king) | _shift_left_left(king)) & ~cell_under_attack & ~occupied
				if move == KSCR_B << 4:
					castling |= (1<<_msb(move))
			if self.white_queen_side_castle_right and (king & ~cell_under_attack):
				move = ((_shift_right(king) | _shift_right_right(king)) & ~cell_under_attack & ~occupied) | (_shift_right(_shift_right_right(king)) & occupied)
				if move == QSCR_B >> 2:
					castling |= (1<<_lsb(move))
			if self.black_king_side_castle_right and (king & ~cell_under_attack):
				move = (_shift_left(king) | _shift_left_left(king)) & ~cell_under_attack & ~occupied
				if move == KSCR_W << 4:
					castling |= (1<<_msb(move))
			if self.black_queen_side_castle_right and (king & ~cell_under_attack):
				move = ((_shift_right(king) | _shift_right_right(king)) & ~cell_under_attack & ~occupied) | (_shift_right(_shift_right_right(king)) & occupied)
				if move == QSCR_W >> 2:
					castling |= (1<<_lsb(move))
		
		return castling

	def check(self, player=None) -> B_BOARD:
		if player is None:
			player = self.active_player
		return self.attacked_fields(not player) & self.PIECES['K' if player else 'k'].position

	def stalemate(self, side) -> bool:
		for key in (['Q','B','N','R','P','K'] if self.active_player else ['q','b','n','r','p','k']):
			for shift in _scan_lsb_first(self.PIECES[key].position):
				self.PIECES[key].position ^= (1 << shift)
				move, attack, _, _ = self.make_move(shift, key, self.PIECES[key], side)
				self.PIECES[key].position ^= (1 << shift)
				if move ^ (1 << shift) != 0 or attack != 0:
					return False
		return True

	def checkmate(self) -> bool:
		occupied, enemies = (self.all_white_pieces(), self.all_black_pieces()) if self.active_player \
								 else (self.all_black_pieces(), self.all_white_pieces())
		king = self.PIECES['K' if self.active_player else 'k']
		shift = king.position
		king.position = 0

		# if king no move and king under attack
		if not (king.get_valid_moves(shift, occupied) \
				& ~self.attacked_fields(not self.active_player, True)):
			king.position = shift

			attack_line = self.find_fight_directions(occupied | enemies)

			# if double check and king cannot move then this is checkmate
			if len(attack_line) > 1:
				return True
			# if one check and king dont move, check if allied pieces can bring down the check
			for key in (['Q','B','N','R','P'] if self.active_player else ['q','b','n','r','p']):
				for shift in _scan_lsb_first(self.PIECES[key].position):
					if key in ['P', 'p']:
						if (self.PIECES[key].get_moves(1<<shift, occupied, enemies) | self.PIECES[key].get_attacks(1<<shift, occupied, enemies)) & attack_line[0][0]:
							# can this piece move without opening a new check ?
							self.PIECES[key].position ^= (1<<shift)
							self.PIECES[attack_line[0][2]].position ^= attack_line[0][1]
							self.PIECES[key].position ^= attack_line[0][1]
							if self.check():
								self.PIECES[key].position ^= attack_line[0][1]
								self.PIECES[key].position ^= (1<<shift)
								self.PIECES[attack_line[0][2]].position ^= attack_line[0][1]
								continue
							self.PIECES[key].position ^= attack_line[0][1]
							self.PIECES[key].position ^= (1<<shift)
							self.PIECES[attack_line[0][2]].position ^= attack_line[0][1]

							return False
					else:
						if self.PIECES[key].get_valid_moves(1<<shift, occupied, enemies) & attack_line[0][0]:
							# can this piece move without opening a new check ?
							self.PIECES[key].position ^= (1<<shift)
							self.PIECES[attack_line[0][2]].position ^= attack_line[0][1]
							self.PIECES[key].position ^= attack_line[0][1]
							if self.check():
								self.PIECES[key].position ^= attack_line[0][1]
								self.PIECES[key].position ^= (1<<shift)
								self.PIECES[attack_line[0][2]].position ^= attack_line[0][1]
								continue
							self.PIECES[key].position ^= attack_line[0][1]
							self.PIECES[key].position ^= (1<<shift)
							self.PIECES[attack_line[0][2]].position ^= attack_line[0][1]

							return False
			return True
		else:
			king.position = shift
			return False

	# checks the rule of three repetitions
	def is_three_fold(self) -> bool:
		cnt = 0
		for state in reversed(self.move_stack):
			if self.zobrist_key == state.zobrist_key:
				cnt += 1
			if cnt == 2:
				return True
			if state.is_capture or state.is_pawn_moved:
				return False

	# checks for insufficient material condition
	def is_insufficient_material(self) -> bool:
		# get pieces from the board and their number
		# Counter({'p': 1, 'b': 1, 'k': 1, 'P': 1, 'K': 1, 'R': 1})
		piece_dict = Counter([ key for key in self.PIECES for _ in _scan_lsb_first(self.PIECES[key].position) if self.PIECES[key].position != 0 ])
		
		# draw if K v kb, K v kn, KB v k, KN v k, KN v kb, KB v kn 
		if piece_dict['p'] == piece_dict['P'] == 0:
			if piece_dict['Q'] == piece_dict['R'] == piece_dict['q'] == piece_dict['r'] == 0:
				if piece_dict['N'] == piece_dict['B'] == 0 and piece_dict['b'] < 2 and (piece_dict['b'] + piece_dict['n']) < 2 or \
						piece_dict['n'] == piece_dict['b'] == 0 and piece_dict['B'] < 2 and (piece_dict['B'] + piece_dict['N']) < 2 or \
						piece_dict['N'] <= 2 and piece_dict['B'] == 0 and piece_dict['n'] <= 2 and piece_dict['n'] == 0 or \
						piece_dict['N'] == 1 and piece_dict['B'] == 0 and piece_dict['n'] == 0 and piece_dict['n'] == 1 or \
						piece_dict['N'] == 0 and piece_dict['B'] == 1 and piece_dict['n'] == 1 and piece_dict['B'] == 0:
						return True
		return False

	# return list of bitboard
	def find_fight_directions(self, occupied_cells):
		res = []
		king = self.PIECES['K' if self.active_player else 'k'].position
		for key in (['q','b','n','r','p'] if self.active_player else ['Q','B','N','R','P']):
			for shift in _scan_lsb_first(self.PIECES[key].position):
				fight_direction = self.PIECES[key].check_direction(king, 1<<shift, occupied_cells & ~king)
				if fight_direction:
					res.append((fight_direction, 1<<shift, key))
		return res

	# A function that returns all possible moves (return generator wich need to unpack)
	# first returns fight moves since they contribute pruning
	def get_all_ligal_moves(self, side):

		# from MVV / LVA values
		b_arr = self.board_as_array()

		for key in (['Q','B','N','R','P','K'] if self.active_player else ['q','b','n','r','p','k']):
		#for key in (['Q','B','P','N','R','K'] if self.active_player else ['q','b','p','n','r','k']):
			for shift in _scan_lsb_first(self.PIECES[key].position):
				self.PIECES[key].position ^= (1 << shift)
				move, attack, _, castling = self.make_move(shift, key, self.PIECES[key], side)
				self.PIECES[key].position ^= (1 << shift)
				for shift_ in _scan_lsb_first(attack):
					value = mvv_lva[ mvv_lva_const[ b_arr[7-(shift//8)][7-(shift%8)] ] ] \
								   [ mvv_lva_const[ b_arr[7-(shift_//8)][7-(shift_%8)] ] ]
					yield ( self.to_uci(shift, shift_), value )
				for shift_ in _scan_lsb_first(castling):
					yield ( self.to_uci(shift, shift_), 0 )
				for shift_ in _scan_lsb_first(move & ~(1<<shift)):
					yield ( self.to_uci(shift, shift_), 0 )
				# for shift_ in _scan_lsb_first(attack | castling | (move & ~(1<<shift)) ):
				# 	yield self.to_uci(shift, shift_)

	# Checks if the move is a capture
	def is_capture(self, move:str):
		for key in self.PIECES:
			if 1<<SQ_NUM[move[2:]] & self.PIECES[key].position:
				return key
		return False

	# Get move in uci notation and handel it 
	def push(self, move: str, side: bool, alg_not_permition=False):
		self.push_call += 1
		from_sq_shift, to_sq_shift = SQ_NUM[move[:2]], SQ_NUM[move[2:]]

		# Find wich peeace move
		for key in self.PIECES:
			if 1<<from_sq_shift & self.PIECES[key].position:
				piece_type = key
				from_bb = self.PIECES[key].position
				break
		# Find where the move was made and check attacks and on which piece
		for key in self.PIECES:
			# Find attacked piece type
			if 1<<to_sq_shift & self.PIECES[key].position:
				attacked_piece_type = key
				to_bb = self.PIECES[key].position
				break
		# if the move was not an attack
		else:
			attacked_piece_type = piece_type
			to_bb = from_bb

		# save board state before change 
		self.move_stack.append(BoardState(self, move if side else self.mirror_move(move), 
												attacked_piece_type if piece_type != attacked_piece_type else False,
												piece_type))

		# Make a move 
		# take bit from bitborad
		self.PIECES[piece_type].position &= ~(1<<from_sq_shift)
		##### update zobrist key #####
		self.zobrist_key ^= zobrist_table[7-(from_sq_shift//8)][7-(from_sq_shift%8)][indexing[piece_type]]
		# put bit into place of movement on bitborad
		if piece_type == attacked_piece_type:
			self.PIECES[attacked_piece_type].position ^= 1<<to_sq_shift 
			self.zobrist_key ^= zobrist_table[7-(to_sq_shift//8)][7-(to_sq_shift%8)][indexing[piece_type]]
		else:
			self.PIECES[attacked_piece_type].position ^= 1<<to_sq_shift 
			self.PIECES[piece_type].position ^= 1<<to_sq_shift 

			# if rook was beeten in her start position change castling permitions
			if attacked_piece_type in ["R", "r"]:
				if side:
					if (1 << to_sq_shift) & BB_H1:
						self.white_king_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["K"]
					elif (1 << to_sq_shift) & BB_A1:
						self.white_queen_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["Q"]
					elif (1 << to_sq_shift) & BB_H8:
						self.black_king_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["k"]
					elif (1 << to_sq_shift) & BB_A8:
						self.black_queen_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["q"]
				else:
					if (1 << to_sq_shift) & BB_A1:
						self.black_king_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["k"]
					elif (1 << to_sq_shift) & BB_H1:
						self.black_queen_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["q"]
					elif (1 << to_sq_shift) & BB_A8:
						self.white_king_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["K"]
					elif (1 << to_sq_shift) & BB_H8:
						self.white_queen_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["Q"]

				# Update rook columns list when rook was beaten 
				self.rook_columns_list[self.active_player].remove(7-(to_sq_shift%8))

			# Update pawn columns list if you take a pawn with another piece 
			if attacked_piece_type in ["P", "p"]:
				self.pawn_columns_list[self.active_player].remove(7-(to_sq_shift%8))

			self.zobrist_key ^= zobrist_table[7-(to_sq_shift//8)][7-(to_sq_shift%8)][indexing[attacked_piece_type]]
			self.zobrist_key ^= zobrist_table[7-(to_sq_shift//8)][7-(to_sq_shift%8)][indexing[piece_type]]

		# Reset en passant square.
		if self.ep_move:
			##### update zobrist key #####
			self.zobrist_key ^= self.zobrist_enpassant[7-(SQ_NUM[self.ep_move])%8]
		ep_square = self.ep_move
		self.ep_move = None

		# Checking all the rules
		if piece_type in ['P', 'p']:

			# hendling ep attack
			if ep_square and to_sq_shift == SQ_NUM[ep_square]:
				#if to_sq_shift == SQ_NUM[ep_square]:
				sq = (1 << (to_sq_shift - 8) if self.active_player else 1 << (to_sq_shift + 8)) \
					if side else (1 << (to_sq_shift + 8) if self.active_player else 1 << (to_sq_shift - 8))
				self.PIECES['p' if self.active_player else 'P'].position &= ~sq
				##### update zobrist key #####
				sq = _lsb(sq) # <- shift the position of the broken pawn
				self.zobrist_key ^= zobrist_table[7-(sq//8)][7-(sq%8)][indexing['p' if self.active_player else 'P']]
				# Update pawn columns 
				self.pawn_columns_list[ not self.active_player].remove(7-(from_sq_shift%8))
				self.pawn_columns_list[ not self.active_player].append(7-(to_sq_shift%8))
				self.pawn_columns_list[self.active_player].remove(7-(sq%8))

				# set en passant flag for algebraic notation
				self.move_stack[-1].is_en_passant = True

			# Update pawn columns list
			elif (from_sq_shift - to_sq_shift) % 8 > 0:
				self.pawn_columns_list[not self.active_player].remove(7 - (from_sq_shift % 8))
				self.pawn_columns_list[not self.active_player].append(7 - (to_sq_shift % 8))

			# add ep move 
			if abs(from_sq_shift - to_sq_shift) > 9:
				# self.ep_move = F_NAME[to_sq_shift - 8 if self.active_player else to_sq_shift + 8] if side \
				# 			else F_NAME[to_sq_shift + 8 if self.active_player else to_sq_shift - 8]
				self.ep_move = F_NAME[(from_sq_shift + to_sq_shift)//2]
				##### update zobrist key #####
				self.zobrist_key ^= self.zobrist_enpassant[7-(SQ_NUM[self.ep_move])%8]
			# if pawn was move drop 50 move rule counter
			self.move_number = -1

			# if the pawn has reached the opposite side, then we give the opportunity (promotion) to choose a piece
			if (1<<to_sq_shift) & (RANK_8 if (self.active_player if side else not self.active_player ) else RANK_1):
				# extract a pawn
				self.PIECES[piece_type].position ^= (1<<to_sq_shift)
				# put the queen
				self.PIECES['Q' if self.active_player else 'q'].position ^= (1<<to_sq_shift)

				##### update zobrist key #####
				self.zobrist_key ^= zobrist_table[7-(to_sq_shift//8)][7-(to_sq_shift%8)][indexing[piece_type]]
				self.zobrist_key ^= zobrist_table[7-(to_sq_shift//8)][7-(to_sq_shift%8)][indexing['Q' if self.active_player else 'q']]

				# Update pawn columns list
				self.pawn_columns_list[not self.active_player].remove(7 - (to_sq_shift % 8))

				# set promotion flag for algebraic notation
				self.move_stack[-1].is_promotion = "Q"

		# Handling castling move if it was done
		elif piece_type in ['K', 'k']:
			# checking if king moves more than one cell
			if all(map(lambda x: abs(from_sq_shift+x-to_sq_shift)>1, (0,8,-8))):
				# for king side 
				if from_sq_shift > to_sq_shift:
					if side:
						corner = BB_H1 if self.active_player else BB_H8
					else:
						corner = BB_H8 if self.active_player else BB_H1
					self.PIECES['R' if self.active_player else 'r'].position &= ~corner
					self.PIECES['R' if self.active_player else 'r'].position |= ((corner << 2) if side else (corner << 3))

					##### update zobrist key #####
					_shift1 = _lsb(corner)
					_shift2 = _lsb((corner << 2) if side else (corner << 3))
					self.zobrist_key ^= zobrist_table[7-(_shift1//8)][7-(_shift1%8)][indexing['R' if self.active_player else 'r']]
					self.zobrist_key ^= zobrist_table[7-(_shift2//8)][7-(_shift2%8)][indexing['R' if self.active_player else 'r']]

					# Update rook columns list when castling
					self.rook_columns_list[not self.active_player].remove(7-(_shift1%8))
					self.rook_columns_list[not self.active_player].append(7-(_shift2%8))

					# tracking castling in order to take this into evaluation 
					self.move_stack[-1].is_castling = 1 if side else 2

				# for queen side
				else:
					if side:
						corner = BB_A1 if self.active_player else BB_A8
					else:
						corner = BB_A8 if self.active_player else BB_A1
					self.PIECES['R' if self.active_player else 'r'].position &= ~corner
					self.PIECES['R' if self.active_player else 'r'].position |= ((corner >> 3) if side else (corner >> 2))

					##### update zobrist key #####
					_shift1 = _lsb(corner)
					_shift2 = _lsb((corner >> 3) if side else (corner >> 2))
					self.zobrist_key ^= zobrist_table[7-(_shift1//8)][7-(_shift1%8)][indexing['R' if self.active_player else 'r']]
					self.zobrist_key ^= zobrist_table[7-(_shift2//8)][7-(_shift2%8)][indexing['R' if self.active_player else 'r']]

					# Update rook columns list when castling
					self.rook_columns_list[not self.active_player].remove(7-(_shift1%8))
					self.rook_columns_list[not self.active_player].append(7-(_shift2%8))

					# tracking castling in order to take this into evaluation 
					self.move_stack[-1].is_castling = 2 if side else 1

		# Change castling permition if rook or king done move
		if piece_type in ['K', 'k', 'R', 'r']:
			# determine the type of figure
			if piece_type == 'R':
				# check that castling right has not been reset yet
				if self.white_queen_side_castle_right:
					# check from which cell the move was made
					if (1<<from_sq_shift) == (BB_A1 if side else BB_H8):
						self.white_queen_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["Q"]
				if self.white_king_side_castle_right:
					if (1<<from_sq_shift) == (BB_H1 if side else BB_A8):
						self.white_king_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["K"]

				# Update rook columns list when it move
				if (from_sq_shift - to_sq_shift) % 8 > 0:
					self.rook_columns_list[0].remove(7 - (from_sq_shift % 8))
					self.rook_columns_list[0].append(7 - (to_sq_shift % 8))

			elif piece_type == 'r':
				if self.black_queen_side_castle_right:
					if (1<<from_sq_shift) == (BB_A8 if side else BB_H1):
						self.black_queen_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["q"]
				if self.black_king_side_castle_right:
					if (1<<from_sq_shift) == (BB_H8 if side else BB_A1):
						self.black_king_side_castle_right = False
						self.zobrist_key ^= self.zobrist_castling["k"]

				# Update rook columns list when it move
				if (from_sq_shift - to_sq_shift) % 8 > 0:
					self.rook_columns_list[1].remove(7 - (from_sq_shift % 8))
					self.rook_columns_list[1].append(7 - (to_sq_shift % 8))

			elif piece_type == 'K':
				if self.white_king_side_castle_right or self.white_queen_side_castle_right:
					if (1<<from_sq_shift) == (BB_H1 << 3 if side else BB_A8 >> 3):
						self.white_king_side_castle_right, self.white_queen_side_castle_right = False, False
						self.zobrist_key ^= self.zobrist_castling["K"]
						self.zobrist_key ^= self.zobrist_castling["Q"]
			elif piece_type == 'k':
				if self.black_king_side_castle_right or self.black_queen_side_castle_right:
					if (1<<from_sq_shift) == (BB_H8 << 3 if side else BB_A1 >> 3):
						self.black_king_side_castle_right, self.black_queen_side_castle_right = False, False
						self.zobrist_key ^= self.zobrist_castling["k"]
						self.zobrist_key ^= self.zobrist_castling["q"]

		# increase 50 rule moves
		self.move_number += 1

		# Swap turn	
		self.active_player = not self.active_player
		self.zobrist_key ^= self.zobrist_black_to_move

		# check for check mate and draw after move
		if self.check():
			# change check flag if it was done
			if self.checkmate():
				self.is_check_mate = True
				return
		# check if stalemate is happend
		if self.stalemate(side):
			self.is_stale_mate = True
		# check 50 move rule
		elif self.move_number >= 100:
			self.is_stale_mate = True
		# check 3 fold repetition
		elif self.is_three_fold():
			self.is_stale_mate = True
		# Insufficient material
		elif self.is_insufficient_material():
			self.is_stale_mate = True

	def push_null_move(self):
		self.push_call += 1

		# save board state before change 
		self.move_stack.append(BoardState(self, '--', False, False))

		# Reset en passant square.
		if self.ep_move:
			##### update zobrist key #####
			self.zobrist_key ^= self.zobrist_enpassant[7-(SQ_NUM[self.ep_move])%8]
		self.ep_move = None

		# Swap turn	
		self.active_player = not self.active_player
		self.zobrist_key ^= self.zobrist_black_to_move


	# return the board to its previous position
	def pop(self):
		self.move_stack.pop().restore(self)

	def pop_null_move(self):
		self.move_stack.pop().restore(self)


class Game:
	
	def __init__(self, background, scaling_factor, game_info, piece_img_dict, board_img, board_reverse_img):
		self.game_mode, self.name1, self.name2, self.time, self.side = game_info.values()
		self.piece_img_dict = piece_img_dict
		self.board_img = board_img
		self.board_reverse_img = board_reverse_img

		self.scaling_factor = scaling_factor
		self.board = Board(375, 80, scaling_factor, self.side, piece_img_dict, board_img, board_reverse_img) if self.side else \
					 Board(375, 80, scaling_factor, self.side, piece_img_dict, board_img, board_reverse_img, BASEBOARD_BLACK)
		self.font = pygame.font.Font('KumbhSans-Regular.ttf', round(36*(scaling_factor[0]+scaling_factor[1])/2))
		self.started_side = game_info['side']
		self.dragging = None
		self.from_cell = None 
		self.game_outcome = None

		# interface img and things for them
		self.exchange_pawn = False
		self.figure_selection_img = self.board.call_transfor_scale(pygame.image.load('images/interface/figure_selection.png'))
		self.data_dict_wpawn_changing, self.data_dict_bpawn_changing = self._create_data_dict_from_pawn_changing(background)
		self.pawn_changing_over_state = [0]*4
		self.checkmate_back_buttons = self._create_img_imgpress_rect_tuple(background, back_b=True)
		self.checkmate_play_buttons = self._create_img_imgpress_rect_tuple(background, play_b=True)
		self.checkmate_buttons_state = [0,0]

		# reverse button img and rect
		self.reverse_button = self.board.call_transfor_scale(pygame.image.load('images/interface/reverse.png'))
		self.rect_reverse_button = pygame.Rect((self.board.cord[0]-self.reverse_button.get_size()[0]-10*scaling_factor[0],
												background.get_size()[1]/2-self.reverse_button.get_size()[1]/2,
												self.reverse_button.get_size()[0], self.reverse_button.get_size()[1]))
		# plate images and font from here 
		self.plate_font = pygame.font.Font('KumbhSans-Regular.ttf', round(28*(scaling_factor[0]+scaling_factor[1])/2))
		self.plate_1 = self.board.call_transfor_scale(pygame.image.load('images/interface/player_plate.png'))
		self.plate_2 = self.board.call_transfor_scale(pygame.image.load('images/interface/computer_plate.png')) if self.game_mode == 'pc' else self.plate_1

		# light bulb image
		self.lightbulb_off_img = self.board.call_transfor_scale(pygame.image.load('images/interface/lightbulb_off.png'))
		self.lightbulb_on_img = self.board.call_transfor_scale(pygame.image.load('images/interface/lightbulb_on.png'))
		
		# move log board img
		self.move_log_board = self.board.call_transfor_scale(pygame.image.load('images/interface/move_log_board1.png'))
		self.move_log_board_rect = pygame.Rect((self.rect_reverse_button[0] - \
												(self.board.cord[0]-(self.rect_reverse_button[0]+self.rect_reverse_button[2]))*2 - \
												self.move_log_board.get_size()[0],
												self.board.cord[1],
												self.move_log_board.get_size()[0],
												self.move_log_board.get_size()[1]
												))
		self.move_log_text_font = pygame.font.Font('KumbhSans-Regular.ttf', round(18*(scaling_factor[0]+scaling_factor[1])/2))
		self.specially_for_dot_font = pygame.font.Font('KumbhSans-Regular.ttf', round(22*(scaling_factor[0]+scaling_factor[1])/2))
		self.move_log_overflow_flag = False # changes when the board is full
		self.gap_x = 25*scaling_factor[0]
		self.gap_y = 29*scaling_factor[1]
		# start position of text output
		self.text_output_start_cord = [self.move_log_board_rect[0]+self.gap_x,
							  		   self.move_log_board_rect[1]+self.gap_y]
		self.text_output_end_cord = [None, None]
		self.dynamic_y = self.move_log_board_rect[1]+self.gap_y # level at which the text is located by y coordinate
		self.dynamic_x = self.move_log_board_rect[1]+self.gap_y # level at which the text is located by x coordinate
		# img and things for beaten piece
		self.beaten_piece_white = {name:0 for name in ['P','B','N','R','Q']}
		self.beaten_piece_black = {name:0 for name in ['p','b','n','r','q']}
		self.beaten_piece_img_dict = self._create_beaten_piece_img_dict()

		# displaying the board and additional interface
		self.board.draw_background(background)
		self._draw_figures_on_board(background, reverse=self.side)
		self.display_nickname_board(background)
		self.display_reverse_button(background)
		self.display_lightbulbs(background)
		self.display_move_log_board(background)

		# Sound init
		self.put_piece_sounds = [pygame.mixer.Sound('sounds/piece_move_1.wav'),
								 pygame.mixer.Sound('sounds/piece_move_2.wav'),
								 pygame.mixer.Sound('sounds/piece_move_3.wav')]
		self.attack_piece_sound = pygame.mixer.Sound('sounds/piece_attack.wav')

		# init timer
		if self.time:
			plate_img =  self.board.call_transfor_scale(pygame.image.load('images/interface/timer_plate.png'))
			x_cord = (self.board.cord[0]+self.plate_1.get_size()[0]+(((self.board.cord[0]+self.board.board_rect[2]/2) - (self.board.cord[0]+self.plate_1.get_size()[0]))/2)) \
			- plate_img.get_size()[0]/2
			y_up = (self.board.cord[1]-10*scaling_factor[0]-self.plate_2.get_size()[1])+self.plate_2.get_size()[1]/2-plate_img.get_size()[1]/2
			y_down = (self.board.cord[1]+self.board.board_rect[3]+10*scaling_factor[0])+self.plate_2.get_size()[1]/2-plate_img.get_size()[1]/2
			self.timer = Timer(scaling_factor, self.time, (x_cord,y_down), (x_cord,y_up), plate_img, background)
		else:
			self.timer = None
		
		if self.game_mode == "pc":
			# Side is indicates which side are white, bottom - True, up - False? player always
			# start on bottom side
			self.is_player_white = self.side
			self.ai = Ai(self.board, self.is_player_white, 3)
			#print(self.ai.ai_move(self.board.to_fen(), self.started_side))


	# makes and displays the calculated AI move
	def switch(self, background):
		if self.is_player_white != self.board.active_player: 
			ai_move = self.ai.ai_move(self.board.to_fen() if self.ai.moves_made < 10 else "", self.side)
			key = self.board.is_capture(ai_move)
			# if ai make captured
			if key:
				print (ai_move)
				#sys.exit()
				# play sound from attack piece
				self.attack_piece_sound.play()

				if key.islower():
					self.beaten_piece_black[key] += 1
					print (self.beaten_piece_black[key])
				else:
					self.beaten_piece_white[key] += 1
					print (self.beaten_piece_white[key])

				self.board.push(ai_move, self.side, True)
				self.board.update_game_phase()
				self.board.draw_background(background)
				self._draw_figures_on_board(background, reverse=self.side)
				self.display_nickname_board(background)
				self.display_reverse_button(background)
				self.display_beaten_piece(background)
			# if ai make move
			else:
				# play sound from put piece
				random.choice(self.put_piece_sounds).play()
				self.board.push(ai_move, self.side)
				self._draw_figures_on_board(background, reverse=self.side)

			print ("PAWN LIST")
			print (sorted(self.board.pawn_columns_list[0]), sorted(self.board.pawn_columns_list[1]))
			print ("ROOK LIST")
			print (self.board.rook_columns_list)

			# turn bulb replacement
			self.display_lightbulbs(background)

			# increase move counter
			self.board.move_done += 1
			self.check_endgame_conditions(background)
			# draws move log after check endgame conditions
			# because in this function, set flags for checkmate and stalemate
			self.update_move_log_board(background)

	def _draw_figures_on_board(self, background, ad=None, reverse=True):
		self.board.draw_board(background, reverse)
		if ad:
			self._additional_visualization(background)			
		self.board.draw_pieces(background)

	# highlights allowed moves and grips
	def _additional_visualization(self, background):
		# possible moves
		for cord in self.move_cords:
			background.blit(self.board.dot_img, ((self.board.board_rect[0]+self.board.single_cell_size[0]*cord[0])+self.board.single_cell_size[0]/2-self.board.dot_img_size[0]/2,
											   (self.board.board_rect[1]+self.board.single_cell_size[1]*cord[1])+self.board.single_cell_size[1]/2-self.board.dot_img_size[1]/2))
		# possible attacks
		for cord in self.attack_cords:
			background.blit(self.board.ring_img, ((self.board.board_rect[0]+self.board.single_cell_size[0]*cord[0])+self.board.single_cell_size[0]/2-self.board.ring_img_size[0]/2,
											   (self.board.board_rect[1]+self.board.single_cell_size[1]*cord[1])+self.board.single_cell_size[1]/2-self.board.ring_img_size[1]/2))
		# which cell is it from
		background.blit(self.board.from_cell_img, ((self.board.board_rect[0]+self.board.single_cell_size[0]*self.from_cell[0])+self.board.single_cell_size[0]/2-self.board.from_cell_img_size[0]/2,
											   (self.board.board_rect[1]+self.board.single_cell_size[1]*self.from_cell[1])+self.board.single_cell_size[1]/2-self.board.from_cell_img_size[1]/2))
		# check warning
		if self.check:
			background.blit(self.board.check_warning_img, ((self.board.board_rect[0]+self.board.single_cell_size[0]*self.check[0])+self.board.single_cell_size[0]/2-self.board.from_cell_img_size[0]/2,
											   (self.board.board_rect[1]+self.board.single_cell_size[1]*self.check[1])+self.board.single_cell_size[1]/2-self.board.from_cell_img_size[1]/2))

	def mouse_tracking(self, background, mouse_pos):
		if self.board.board_rect.collidepoint(mouse_pos):
			x = int((mouse_pos[0] - self.board.board_rect[0])/self.board.single_cell_size[0])
			y = int((mouse_pos[1] - self.board.board_rect[1])/self.board.single_cell_size[1])
			print (x, y)
			# Take a figure
			if not self.dragging:
				shift = from_board_cord_to_bit_shift((x,y))
				# Starting from Python 3.7, insertion order of Python dictionaries is guaranteed
				#self.board.filter_pieces_by_side(self.board.active_player)
				for key,piece in (list(self.board.PIECES.items())[6:] if self.board.active_player else list(self.board.PIECES.items())[:6]):
					if 1 << shift & piece.position:
						print (1 << shift & piece.position)
						print ('You click in piece in {0}'.format(F_NAME[shift]))
						piece.position ^= (1 << shift)

						##### update zorbist key #####
						self.board.zobrist_key ^= zobrist_table[7-(shift//8)][7-(shift%8)][indexing[key]]

						self.dragging, self.key = piece, key
						self.from_cell = from_bit_shift_to_board_cord(shift)
						
						self.moves, self.attacks, self.check, self.castling = self.board.make_move(shift, key, piece, self.side)
						self.move_cords = list(map(from_bit_shift_to_board_cord, _scan_lsb_first(self.moves|self.castling)))
						self.attack_cords = list(map(from_bit_shift_to_board_cord, _scan_lsb_first(self.attacks)))
						#self.valid_move = self.moves | self.attacks 
						print (self.move_cords, self.attack_cords)
						self._draw_figures_on_board(background, ad=True, reverse=self.side)

						# left up corner
						if mouse_pos[0] <= self.board.board_rect[0] + self.board.single_cell_size[0]*0.25 and \
						   mouse_pos[1] <= self.board.board_rect[1] + self.board.single_cell_size[1]*0.35:
							background.blit(self.dragging.img, (mouse_pos[0],
																mouse_pos[1]) )
						# left down corner
						elif mouse_pos[0] <= self.board.board_rect[0] + self.board.single_cell_size[0]*0.25 and \
						   mouse_pos[1] >= self.board.board_rect[1] + self.board.board_rect[3] - self.board.single_cell_size[1]*0.35:
							background.blit(self.dragging.img, (mouse_pos[0],
																mouse_pos[1]-self.dragging.size[1]) )
						# right up corner
						elif mouse_pos[0] >= self.board.board_rect[0] + self.board.board_rect[2] - self.board.single_cell_size[0]*0.35 and \
						   mouse_pos[1] <= self.board.board_rect[1] + self.board.single_cell_size[1]*0.35:
							background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0],
																mouse_pos[1]) )
						# right down corner
						elif mouse_pos[0] >= self.board.board_rect[0] + self.board.board_rect[2] - self.board.single_cell_size[0]*0.35 and \
						   mouse_pos[1] >= self.board.board_rect[1] + self.board.board_rect[3] - self.board.single_cell_size[1]*0.35:
							background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0],
																mouse_pos[1]-self.dragging.size[1]) )
						# left border
						elif mouse_pos[0] <= self.board.board_rect[0] + self.board.single_cell_size[0]*0.35:
							background.blit(self.dragging.img, (mouse_pos[0],
																mouse_pos[1]-self.dragging.size[1]/2) )

						# right border 
						elif mouse_pos[0] >= self.board.board_rect[0] + self.board.board_rect[2] - self.board.single_cell_size[0]*0.35:
							background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0],
																mouse_pos[1]-self.dragging.size[1]/2) )
						# up border 
						elif mouse_pos[1] <= self.board.board_rect[1] + self.board.single_cell_size[1]*0.35: 
							background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0]/2,
																mouse_pos[1]) )
						# down border 
						elif mouse_pos[1] >= self.board.board_rect[1] + self.board.board_rect[3] - self.board.single_cell_size[1]*0.35: 
							background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0]/2,
																mouse_pos[1]-self.dragging.size[1]) )
						else:
							background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0]/2,
																mouse_pos[1]-self.dragging.size[1]/2) )
						break
			# Put a figure
			else:
				# where do i go
				shift = from_board_cord_to_bit_shift((x,y))
				# where I'm going from
				from_shift = from_board_cord_to_bit_shift(self.from_cell)
				player_turn = self.board.active_player

				# update move log
				if from_shift != shift and (1<<shift) & (self.moves | self.attacks | self.castling):
					# return the piece to its original position
					# in order to save the board state before changes
					self.dragging.position ^= (1 << from_shift)
					##### update zorbist key #####
					self.board.zobrist_key ^= zobrist_table[7-(from_shift//8)][7-(from_shift%8)][indexing[self.key]]
					# safe board state
					uci_move = self.board.to_uci(from_shift, shift)
					self.board.move_stack.append( BoardState(self.board, uci_move if self.side else self.board.mirror_move(uci_move),
																		 True if (1 << shift & self.attacks) else False,
																		 self.key))
					# return to the state when the piece is removed from the board
					self.dragging.position ^= (1 << from_shift)
					self.board.zobrist_key ^= zobrist_table[7-(from_shift//8)][7-(from_shift%8)][indexing[self.key]]

				# Handling move
				if 1 << shift & self.moves:
					self.dragging.position ^= (1 << shift)

					##### update zorbist key #####
					self.board.zobrist_key ^= zobrist_table[7-(shift//8)][7-(shift%8)][indexing[self.key]]

					# drop ep permision if you don't use it in next step
					if from_shift != shift:
						self.board.ep_move = None
					# add ep move 
					if self.key in ['P','p']:
						if abs(from_shift - shift) > 8:
							# self.board.ep_move = F_NAME[shift - 8 if self.board.active_player else shift + 8] if self.side \
										# else F_NAME[shift + 8 if self.board.active_player else shift - 8]
							self.board.ep_move = F_NAME[(from_shift + shift)//2]
							##### update zobrist key #####
							self.board.zobrist_key ^= self.board.zobrist_enpassant[7-(SQ_NUM[self.board.ep_move])%8]

					self.dragging = None
					self.board.active_player = not self.board.active_player if from_shift != shift else self.board.active_player
					##### update zobrist key #####
					self.board.zobrist_key ^= self.board.zobrist_black_to_move
					# play sound from put piece
					random.choice(self.put_piece_sounds).play()
					self.display_lightbulbs(background)
					self._draw_figures_on_board(background, reverse=self.side)
					# increase 50 rule moves
					if from_shift != shift:
						self.board.move_number += 1

				# Handling attack
				elif 1 << shift & self.attacks:
					for key, piece in (list(self.board.PIECES.items())[:6] if self.board.active_player else list(self.board.PIECES.items())[6:]):
						if 1 << shift & piece.position:
							piece.position ^= (1 << shift)

							# if rook was beeten in her start position change castling permitions
							if key in ["R", "r"]:
								if self.side:
									if (1 << shift) & BB_H1:
										self.board.white_king_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["K"]
									elif (1 << shift) & BB_A1:
										self.board.white_queen_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["Q"]
									elif (1 << shift) & BB_H8:
										self.board.black_king_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["k"]
									elif (1 << shift) & BB_A8:
										self.board.black_queen_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["q"]
								else:
									if (1 << shift) & BB_A1:
										self.board.black_king_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["k"]
									elif (1 << shift) & BB_H1:
										self.board.black_queen_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["q"]
									elif (1 << shift) & BB_A8:
										self.board.white_king_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["K"]
									elif (1 << shift) & BB_H8:
										self.board.white_queen_side_castle_right = False
										self.board.zobrist_key ^= self.board.zobrist_castling["Q"]

								# Update rook columns when it was beeten
								self.board.rook_columns_list[player_turn].remove(7 - (shift % 8))

							# Update pawn columns list when pawn was beeten
							elif key in ["P", "p"]:
								self.board.pawn_columns_list[player_turn].remove(7 - (shift % 8))

							##### update zorbist key #####
							self.board.zobrist_key ^= zobrist_table[7-(shift//8)][7-(shift%8)][indexing[key]]
							self.board.zobrist_key ^= zobrist_table[7-(shift//8)][7-(shift%8)][indexing[self.key]]

							self.dragging.position ^= (1 << shift)
							self.dragging = None
							self.board.ep_move = None
							if key.islower():
								self.beaten_piece_black[key] += 1
							else:
								self.beaten_piece_white[key] += 1
							break
					# ep attack
					if self.board.ep_move and shift == SQ_NUM[self.board.ep_move]:
						sq = (1 << (shift - 8) if self.board.active_player else 1 << (shift + 8)) \
							if self.side else (1 << (shift + 8) if self.board.active_player else 1 << (shift - 8))
						self.board.PIECES['p' if self.board.active_player else 'P'].position &= ~sq
						self.dragging.position ^= (1 << shift)

						##### update zorbist key #####
						sq = _lsb(sq)
						self.board.zobrist_key ^= zobrist_table[7-(sq//8)][7-(sq%8)][indexing['p' if self.board.active_player else 'P']]
						self.board.zobrist_key ^= zobrist_table[7-(shift//8)][7-(shift%8)][indexing[self.key]]

						# Update pawn columns 
						self.board.pawn_columns_list[not player_turn].remove(7 - (from_shift % 8))
						self.board.pawn_columns_list[not player_turn].append(7 - (shift % 8))
						self.board.pawn_columns_list[player_turn].remove(7 - (sq % 8))

						# set en passant flag for algebraic notation
						self.board.move_stack[-1].is_en_passant = True

						self.dragging = None
						self.board.ep_move = None
						key = 'p' if not self.board.active_player else 'P'
						if key.islower():
							self.beaten_piece_black[key] += 1
						else:
							self.beaten_piece_white[key] += 1
					# Update pawn columns 
					elif self.key in ["P", "p"] and (from_shift - shift) % 8 > 0:
						self.board.pawn_columns_list[not player_turn].remove(7 - (from_shift % 8))
						self.board.pawn_columns_list[not player_turn].append(7 - (shift % 8))
					
					# change turn 
					self.board.active_player = not self.board.active_player
					##### update zobrist key #####
					self.board.zobrist_key ^= self.board.zobrist_black_to_move
					# since the piece was taken, we drop the rule of 50 moves
					self.board.move_number = 0
					# update screen
					self.board.draw_background(background)
					# play sound from attack piece
					self.attack_piece_sound.play()
					self._draw_figures_on_board(background, reverse=self.side)
					self.display_nickname_board(background)
					self.display_reverse_button(background)
					self.display_lightbulbs(background)
					self.display_beaten_piece(background)
					if self.time:
						self.timer.draw_timer(background, self.side)

				# Handling castling move
				elif 1 << shift & self.castling:
					# from king side
					if from_shift > shift:
						self.dragging.position ^= (1 << shift)
						if self.side:
							corner = BB_H1 if self.board.active_player else BB_H8
						else:
							corner = BB_H8 if self.board.active_player else BB_H1
						self.board.PIECES['R' if self.board.active_player else 'r'].position &= ~corner
						self.board.PIECES['R' if self.board.active_player else 'r'].position |= ((corner << 2) if self.side else (corner << 3))

						##### update zobrist key #####
						_shift1 = _lsb(corner)
						_shift2 = _lsb((corner << 2) if self.side else (corner << 3))
						self.board.zobrist_key ^= zobrist_table[7-(_shift1//8)][7-(_shift1%8)][indexing['R' if self.board.active_player else 'r']]
						self.board.zobrist_key ^= zobrist_table[7-(_shift2//8)][7-(_shift2%8)][indexing['R' if self.board.active_player else 'r']]

						# Update rook columns list when it move
						self.board.rook_columns_list[not player_turn].remove(7-(_shift1%8))
						self.board.rook_columns_list[not player_turn].append(7-(_shift2%8))

						# tracking castling in order to take this into move log board
						self.board.move_stack[-1].is_castling = 1 if self.side else 2

					# from queen side 
					else:
						self.dragging.position ^= (1 << shift)
						if self.side:
							corner = BB_A1 if self.board.active_player else BB_A8
						else:
							corner = BB_A8 if self.board.active_player else BB_A1
						self.board.PIECES['R' if self.board.active_player else 'r'].position &= ~corner
						self.board.PIECES['R' if self.board.active_player else 'r'].position |= ((corner >> 3) if self.side else (corner >> 2))

						##### update zobrist key #####
						_shift1 = _lsb(corner)
						_shift2 = _lsb((corner >> 3) if self.side else (corner >> 2))
						self.board.zobrist_key ^= zobrist_table[7-(_shift1//8)][7-(_shift1%8)][indexing['R' if self.board.active_player else 'r']]
						self.board.zobrist_key ^= zobrist_table[7-(_shift2//8)][7-(_shift2%8)][indexing['R' if self.board.active_player else 'r']]

						# Update rook columns list when it move
						self.board.rook_columns_list[not player_turn].remove(7-(_shift1%8))
						self.board.rook_columns_list[not player_turn].append(7-(_shift2%8))

						# tracking castling in order to take this into move log board
						self.board.move_stack[-1].is_castling = 2 if self.side else 1

					self.dragging = None
					self.board.ep_move = None
					self.board.active_player = not self.board.active_player
					##### update zobrist key #####
					self.board.zobrist_key ^= self.board.zobrist_black_to_move
					# play sound from put piece
					random.choice(self.put_piece_sounds).play()
					self._draw_figures_on_board(background, reverse=self.side)
					self.display_lightbulbs(background)
					# increase 50 rule moves
					self.board.move_number += 1

				# if there was a move to another cell
				if self.board.active_player != player_turn:
					# if a rook or king was moved, update castle rights
					if self.key == 'R':
						if self.board.white_queen_side_castle_right:
							if 1<<from_shift == (BB_A1 if self.side else BB_H8):
								self.board.white_queen_side_castle_right = False
								self.board.zobrist_key ^= self.board.zobrist_castling["Q"]
						if self.board.white_king_side_castle_right:
							if 1<<from_shift == (BB_H1 if self.side else BB_A8):
								self.board.white_king_side_castle_right = False
								self.board.zobrist_key ^= self.board.zobrist_castling["K"]
						# Update rook columns list when it move
						if (from_shift - shift) % 8 > 0:
							self.board.rook_columns_list[0].remove(7 - (from_shift % 8))
							self.board.rook_columns_list[0].append(7 - (shift % 8))

					elif self.key == 'r':
						if self.board.black_queen_side_castle_right:
							if 1<<from_shift == (BB_A8 if self.side else BB_H1):
								self.board.black_queen_side_castle_right = False
								self.board.zobrist_key ^= self.board.zobrist_castling["q"]
						if self.board.black_king_side_castle_right:
							if 1<<from_shift == (BB_H8 if self.side else BB_A1):
								self.board.black_king_side_castle_right = False
								self.board.zobrist_key ^= self.board.zobrist_castling["k"]
						# Update rook columns list when it move
						if (from_shift - shift) % 8 > 0:
							self.board.rook_columns_list[1].remove(7 - (from_shift % 8))
							self.board.rook_columns_list[1].append(7 - (shift % 8))

					elif self.key == 'K':
						if self.board.white_king_side_castle_right or self.board.white_queen_side_castle_right:
							if 1<<from_shift == (BB_H1 << 3 if self.side else BB_A8 >> 3):
								self.board.white_king_side_castle_right, self.board.white_queen_side_castle_right = False, False
								self.board.zobrist_key ^= self.board.zobrist_castling["K"]
								self.board.zobrist_key ^= self.board.zobrist_castling["Q"]
					elif self.key == 'k':
						if self.board.black_king_side_castle_right or self.board.black_queen_side_castle_right:
							if 1<<from_shift == (BB_H8 << 3 if self.side else BB_A1 >> 3):
								self.board.black_king_side_castle_right, self.board.black_queen_side_castle_right = False, False
								self.board.zobrist_key ^= self.board.zobrist_castling["k"]
								self.board.zobrist_key ^= self.board.zobrist_castling["q"]
			
					# if pawn was move drop 50 move rule counter
					elif self.key in ['P', 'p']:
						self.board.move_number = 0
						# if the pawn has reached the opposite side, then we give the opportunity to choose a piece
						if 1<<shift & (RANK_8 if (not self.board.active_player if self.side else self.board.active_player ) else RANK_1):
							self.exchange_pawn = (1<<shift)

							# Update pawn columns list
							self.board.pawn_columns_list[not player_turn].remove(7 - (shift % 8))

					# check mate, check, stalemate
					self.check_endgame_conditions(background)
					# draws move log after check endgame conditions
					# because in this function, set flags for checkmate and stalemate
					# promotion condition
					if not self.exchange_pawn:
						self.update_move_log_board(background)

					# increase move counter
					self.board.move_done += 1

					print ("ALGEBRAIC NOTATION")
					print (self.board.move_stack[-1].get_algebraic_notation())

	# function that checks the end condition of the game
	def check_endgame_conditions(self, background):
		# check if checkmate happened
		if self.board.check():
			print ("It's is check !!!")
			# change check flag if it was done
			self.board.move_stack[-1].is_check = True
			if self.board.checkmate():
				self.board.move_stack[-1].is_checkmate = True
				winner, loser = (self.name1, self.name2) if (not self.board.active_player if self.side else self.board.active_player) \
						 else (self.name2, self.name1) 
				self.end_game(background, winner, loser)
				return
		# check if stalemate is happend
		if self.board.stalemate(self.side) and self.game_outcome == None:
			# change stalemate flag if it was done
			self.board.move_stack[-1].is_stalemate = True

			self.end_game(background, draw=True)
		# check 50 move rule
		elif self.board.move_number >= 100:
			# change stalemate flag if it was done
			self.board.move_stack[-1].is_stalemate = True

			self.end_game(background, draw=True)
		# check 3 fold repetition
		elif self.board.is_three_fold():
			# change stalemate flag if it was done
			self.board.move_stack[-1].is_stalemate = True

			self.end_game(background, draw=True)
		# check insufficient material conditions
		elif self.board.is_insufficient_material():
			# change stalemate flag if it was done
			self.board.move_stack[-1].is_stalemate = True

			self.end_game(background, draw=True)

	# game ending function with text preparation and displaying
	def end_game(self, background, win=None, los=None, draw=None):
		textsurface = self.font.render('Draw', True, (0, 0, 0)) if draw else \
					  self.font.render('{} wins {}'.format(win, los), True, (0, 0, 0))			
		self.draw_checkmate_board(background, textsurface)					
		self.game_outcome = textsurface

	"""
	Functions for displaying nickname board
	"""
	def display_nickname_board(self, background):
		#p1, n1 = (self.plate_1, self.name1) if self.side else (self.plate_2, self.name2)
		#p2, n2 = (self.plate_2, self.name2) if self.side else (self.plate_1, self.name1)
		background.blit(self.plate_1, (self.board.cord[0], self.board.cord[1]+self.board.board_rect[3]+10*self.scaling_factor[0]))
		background.blit(self.plate_font.render(self.name1, True, (58, 58, 59)),  (self.board.cord[0]+75*self.scaling_factor[0],
														self.board.cord[1]+self.board.board_rect[3]+22*self.scaling_factor[0]) )

		background.blit(self.plate_2, (self.board.cord[0], self.board.cord[1]-10*self.scaling_factor[0]-self.plate_2.get_size()[1]))
		background.blit(self.plate_font.render(self.name2, True, (58, 58, 59)),  (self.board.cord[0]+75*self.scaling_factor[0],
														self.board.cord[1]-57*self.scaling_factor[0]) )

	"""
	Functions for displaying and handling the game completion window
	"""
	def draw_checkmate_board(self, background, text):
		background.blit(self.figure_selection_img, ((self.board.board_rect[0]+self.board.board_rect[2]/2)-self.figure_selection_img.get_size()[0]/2,
													(self.board.board_rect[1]+self.board.board_rect[3]/2)-self.figure_selection_img.get_size()[1]/2))
		background.blit(text, ((self.board.board_rect[0]+self.board.board_rect[2]/2)-text.get_size()[0]/2,
							   background.get_size()[1]/2-self.figure_selection_img.get_size()[1]/2+text.get_size()[1]/2))


	def _create_img_imgpress_rect_tuple(self, background, back_b=None, play_b=None):
		if back_b:
			img, img_press = self.board.call_transfor_scale(pygame.image.load('images/interface/checkmate_back.png')), \
							 self.board.call_transfor_scale(pygame.image.load('images/interface/checkmate_back_press.png'))							 	  
			return (img,img_press, pygame.Rect(((self.board.board_rect[0]+self.board.board_rect[2]/2)-2*img.get_size()[0],
														background.get_size()[1]/2,img.get_size()[0],img.get_size()[1])))
		if play_b:
			img, img_press = self.board.call_transfor_scale(pygame.image.load('images/interface/checkmate_play_again.png')), \
							 self.board.call_transfor_scale(pygame.image.load('images/interface/checkmate_play_again_press.png'))
			return (img, img_press, pygame.Rect(((self.board.board_rect[0]+self.board.board_rect[2]/2)+img.get_size()[0],
														background.get_size()[1]/2, img.get_size()[0], img.get_size()[1])))

	def draw_checkmate_button(self, background):
		self._draw_figures_on_board(background, reverse=self.side)
		self.draw_checkmate_board(background, self.game_outcome)
		background.blit(self.checkmate_back_buttons[self.checkmate_buttons_state[0]], 
						(self.checkmate_back_buttons[2][0], self.checkmate_back_buttons[2][1]))
		background.blit(self.checkmate_play_buttons[self.checkmate_buttons_state[1]], 
						(self.checkmate_play_buttons[2][0], self.checkmate_play_buttons[2][1]))

	def check_mouse_over_checkmate_button(self, mouse_pos):
		self.checkmate_buttons_state[0] = 1 if self.checkmate_back_buttons[2].collidepoint(mouse_pos) else 0
		self.checkmate_buttons_state[1] = 1 if self.checkmate_play_buttons[2].collidepoint(mouse_pos) else 0

	def check_click_on_checkmate_button(self, mouse_pos):
		if self.checkmate_back_buttons[2].collidepoint(mouse_pos):
			return 0
		if self.checkmate_play_buttons[2].collidepoint(mouse_pos):
			self.checkmate_buttons_state[1] = 0
			return 1

	######################################################

	"""
	Functions for working with the pawn swap interface
	"""
	def _create_data_dict_from_pawn_changing(self, background):
		w, h = self.figure_selection_img.get_size()
		w, h = w - (20+50) * self.scaling_factor[0], h - (10+33) * self.scaling_factor[1]
		indent = 40*self.scaling_factor[0]
		white_dict = {}
		black_dict = {}
		for idx, name in enumerate([['QW','qB'], ['BW','bB'], ['NW','nB'], ['RW','rB']]):
			wp = self.board.call_transfor_scale(pygame.image.load('images/interface/{}_rect.png'.format(name[0])))
			wpp = self.board.call_transfor_scale(pygame.image.load('images/interface/{}_rect_press.png'.format(name[0])))
			bp = self.board.call_transfor_scale(pygame.image.load('images/interface/{}_rect.png'.format(name[1])))
			bpp = self.board.call_transfor_scale(pygame.image.load('images/interface/{}_rect_press.png'.format(name[1])))
			rect = pygame.Rect(((self.board.board_rect[0]+self.board.board_rect[2]/2) - w/2 + (indent+wp.get_size()[0])*idx,
								(self.board.board_rect[1]+self.board.board_rect[3]/2) - h/2, wp.get_size()[0], wp.get_size()[1]))
			white_dict[name[0]] = (rect, wp, wpp)
			black_dict[name[1]] = (rect, bp, bpp)
		return white_dict, black_dict						

	def draw_pawn_change_button(self, background):
		self._draw_figures_on_board(background, reverse=self.side)
		background.blit(self.figure_selection_img, ((self.board.board_rect[0]+self.board.board_rect[2]/2)-self.figure_selection_img.get_size()[0]/2, \
													(self.board.board_rect[1]+self.board.board_rect[3]/2)-self.figure_selection_img.get_size()[1]/2))
		data = self.data_dict_wpawn_changing if not self.board.active_player else self.data_dict_bpawn_changing
		for idx, key in enumerate(data.keys()):
			background.blit(data[key][2] if self.pawn_changing_over_state[idx] else data[key][1], (data[key][0][0], data[key][0][1]))

	def check_mouse_over_pawn_change_window(self, mouse_pos):
		for idx, key in enumerate(self.data_dict_wpawn_changing):
			if self.data_dict_wpawn_changing[key][0].collidepoint(mouse_pos):
				self.pawn_changing_over_state[idx] = 1
			else:
				self.pawn_changing_over_state[idx] = 0

	def check_click_on_pawn_change_window(self, background, mouse_pos):
		data = self.data_dict_wpawn_changing if not self.board.active_player else self.data_dict_bpawn_changing
		for idx, key in enumerate(data):
			if data[key][0].collidepoint(mouse_pos):
				self.board.change_pawn_to(self.exchange_pawn, key[0])
				# set promotion flag for algebraic notation
				self.board.move_stack[-1].is_promotion = key[0]
				self.exchange_pawn = False
				self.pawn_changing_over_state[idx] = 0
				self._draw_figures_on_board(background, reverse=self.side)
				self.update_move_log_board(background)
				break
		# check checkmate when promotion hepend
		if self.board.checkmate():
			winner, loser = (self.name1, self.name2) if (not self.board.active_player if self.side else self.board.active_player) \
						 else (self.name2, self.name1) 
			self.end_game(background, winner, loser)
					
	######################################################

	"""
	Tracks clicking on reverse button and display it 
	"""
	def check_click_on_reverse_button(self, mouse_pos):
		return True if self.rect_reverse_button.collidepoint(mouse_pos) else False

	def display_reverse_button(self, background):
		background.blit(self.reverse_button, (self.rect_reverse_button[0], self.rect_reverse_button[1]))
	######################################################

	"""
	Processes the image of the turn queue light
	"""
	def display_lightbulbs(self, background):
		flag = (True if self.board.active_player else False) if self.side else (False if self.board.active_player else True)
		background.blit(self.lightbulb_on_img if flag else self.lightbulb_off_img,
				 (self.rect_reverse_button[0]+self.rect_reverse_button[2]//2-(self.lightbulb_off_img.get_size()[0]//2),
				 self.board.cord[1]+self.board.board_rect[3]+10*self.scaling_factor[0]+self.plate_2.get_size()[1]/2-self.lightbulb_off_img.get_size()[1]/2))
		
		background.blit(self.lightbulb_on_img if not flag else self.lightbulb_off_img,
				 (self.rect_reverse_button[0]+self.rect_reverse_button[2]//2-(self.lightbulb_off_img.get_size()[0]//2),
				 self.board.cord[1]-10*self.scaling_factor[0]-self.plate_2.get_size()[1]/2-self.lightbulb_off_img.get_size()[1]/2))

	######################################################

	"""
	Part responsible for processing move log board
	"""
	def display_move_log_board(self, background):
		background.blit(self.move_log_board, (self.move_log_board_rect[0], self.move_log_board_rect[1]))

	def update_move_log_board(self, background, full_board_reverse=False):
		background.blit(self.move_log_board, (self.move_log_board_rect[0], self.move_log_board_rect[1]))
		# if in the second if statement the "self.dynamic_y < ..."" condition is met
		# you will need to go to the first condition
		while True:
			if not self.move_log_overflow_flag:
				if self.dynamic_y >= (self.move_log_board_rect[1]+self.move_log_board_rect[3]-self.gap_y) and not full_board_reverse:
					self.move_log_overflow_flag = True
					textsurface = self.move_log_text_font.render(self.board.move_stack[-2].get_algebraic_notation(),
																		 True, (0, 0, 0))

					self.text_output_end_cord[0] = self.text_output_start_cord[0]
					self.text_output_end_cord[1] = self.dynamic_y - textsurface.get_size()[1]+self.gap_y//4
				else:
					x, y = self.text_output_start_cord[0], self.text_output_start_cord[1]
					for i in range(len(self.board.move_stack)):
						if i%2 == 1:
							textsurface = self.move_log_text_font.render(self.board.move_stack[i].get_algebraic_notation(),
																		 True, (0, 0, 0))
							background.blit(textsurface, (x,y))
							x -= (self.move_log_board_rect[2])//2
							y += textsurface.get_size()[1]+self.gap_y//4
							self.dynamic_y = y
							self.dynamic_x = x
						else:
							textsurface = self.move_log_text_font.render(str(i//2+1)+". "+self.board.move_stack[i].get_algebraic_notation(),
																 True, (0, 0, 0))
							background.blit(textsurface, (x,y))
							x += (self.move_log_board_rect[2])//2

					return

			if self.move_log_overflow_flag:
				if self.dynamic_y < (self.move_log_board_rect[1]+self.move_log_board_rect[3]-self.gap_y):
					self.move_log_overflow_flag = False
				else:
					idx = len(self.board.move_stack)-1
					if idx%2 == 0:
						x = self.text_output_end_cord[0]
						y = self.text_output_end_cord[1]
					else:
						x = self.text_output_end_cord[0] + (self.move_log_board_rect[2])//2
						y = self.text_output_end_cord[1]
					for i in range(len(self.board.move_stack)-1, 0, -1):
						if y <= (self.move_log_board_rect[1]+self.gap_y):
							textsurface = self.specially_for_dot_font.render("···", True, (0, 0, 0))
							x = self.move_log_board_rect[0]+self.move_log_board_rect[2]//2 - textsurface.get_size()[0]//2
							y = self.move_log_board_rect[1]+self.gap_y//2 - textsurface.get_size()[1]//2
							background.blit(textsurface, (x,y))
							break

						if i%2 == 1:
							textsurface = self.move_log_text_font.render(self.board.move_stack[i].get_algebraic_notation(),
																		 True, (0, 0, 0))
							background.blit(textsurface, (x,y))
							x -= (self.move_log_board_rect[2])//2
							self.dynamic_y += textsurface.get_size()[1]+self.gap_y//4

						else:
							pref = str(i//2+1)[:2]+".. " if len(str(i//2+1)) > 2 else str(i//2+1)+". "
							textsurface = self.move_log_text_font.render(pref+self.board.move_stack[i].get_algebraic_notation(),
																	 True, (0, 0, 0))
							background.blit(textsurface, (x,y))

							x += (self.move_log_board_rect[2])//2
							y -= textsurface.get_size()[1]+self.gap_y//4

				return

	######################################################

	"""
	Displaying and handling beaten pieces
	"""
	def _create_beaten_piece_img_dict(self):
		res = {}
		for white, black in [['wP','bP'],['wB','bB'],['wN','bN'],['wR','bR'],['wQ','bQ']]:
			res[white[1]] = self.board.call_transfor_scale(pygame.image.load('images/interface/{}_small.png'.format(white)))
			res[black[1].lower()] = self.board.call_transfor_scale(pygame.image.load('images/interface/{}_small.png'.format(black)))
		return res

	def display_beaten_piece(self, background):
		if self.side:
			x_pos = self.board.cord[0]+self.board.board_rect[2]/2
			for key, count in self.beaten_piece_white.items():
				indent = self.beaten_piece_img_dict[key].get_size()[0]/2 if count == 0 else \
				self.beaten_piece_img_dict[key].get_size()[0]/1.7 - self.beaten_piece_img_dict[key].get_size()[0]/(2*count) 
				x_pos -= indent
				for _ in range(count):
					x_pos += indent
					background.blit(self.beaten_piece_img_dict[key], (x_pos, self.board.cord[1]-self.beaten_piece_img_dict[key].get_size()[1]-self.plate_1.get_size()[1]/3))
				x_pos += self.beaten_piece_img_dict['Q'].get_size()[0]
			
			x_pos = self.board.cord[0]+self.board.board_rect[2]/2
			for key, count in self.beaten_piece_black.items():
				indent = self.beaten_piece_img_dict[key].get_size()[0]/2 if count == 0 else \
				self.beaten_piece_img_dict[key].get_size()[0]/1.7 - self.beaten_piece_img_dict[key].get_size()[0]/(2*count) 
				x_pos -= indent
				for _ in range(count):
					x_pos += indent
					background.blit(self.beaten_piece_img_dict[key], (x_pos, self.board.cord[1]+self.board.board_rect[3]+self.plate_1.get_size()[1]/3))
				x_pos += self.beaten_piece_img_dict['Q'].get_size()[0]
		else:
			x_pos = self.board.cord[0]+self.board.board_rect[2]/2
			for key, count in self.beaten_piece_white.items():
				indent = self.beaten_piece_img_dict[key].get_size()[0]/2 if count == 0 else \
				self.beaten_piece_img_dict[key].get_size()[0]/1.7 - self.beaten_piece_img_dict[key].get_size()[0]/(2*count) 
				x_pos -= indent
				for _ in range(count):
					x_pos += indent
					background.blit(self.beaten_piece_img_dict[key], (x_pos, self.board.cord[1]+self.board.board_rect[3]+self.plate_1.get_size()[1]/3))
				x_pos += self.beaten_piece_img_dict['Q'].get_size()[0]
			
			x_pos = self.board.cord[0]+self.board.board_rect[2]/2
			for key, count in self.beaten_piece_black.items():
				indent = self.beaten_piece_img_dict[key].get_size()[0]/2 if count == 0 else \
				self.beaten_piece_img_dict[key].get_size()[0]/1.7 - self.beaten_piece_img_dict[key].get_size()[0]/(2*count) 
				x_pos -= indent
				for _ in range(count):
					x_pos += indent
					background.blit(self.beaten_piece_img_dict[key], (x_pos, self.board.cord[1]-self.beaten_piece_img_dict[key].get_size()[1]-self.plate_1.get_size()[1]/3))
				x_pos += self.beaten_piece_img_dict['Q'].get_size()[0]
	
	######################################################	

	def visual_movement_of_figure(self, background, mouse_pos):
		if all([self.board.board_rect.collidepoint((mouse_pos[0]+x*self.dragging.size[0]/2, mouse_pos[1]+y*self.dragging.size[1]/2)) \
																 for x,y in [(-1,-1),(1,1)]]):
			self._draw_figures_on_board(background, ad=True, reverse=self.side)
			background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0]/2,
													mouse_pos[1]-self.dragging.size[1]/2) )

		elif all([self.board.board_rect[1] < mouse_pos[1]+y*self.dragging.size[1]/2 < (self.board.board_rect[3]+self.board.board_rect[1]) \
																  for y in [-1, 1] ]):
			if mouse_pos[0] <= self.board.board_rect[0]+self.dragging.size[0]/2:
				self._draw_figures_on_board(background, ad=True, reverse=self.side)
				background.blit(self.dragging.img, (self.board.board_rect[0]+3,
														mouse_pos[1]-self.dragging.size[1]/2) )
			elif mouse_pos[0] >= self.board.board_rect[0]+self.board.board_rect[2]-self.dragging.size[0]/2:
				self._draw_figures_on_board(background, ad=True, reverse=self.side)
				background.blit(self.dragging.img, (self.board.board_rect[0]+self.board.board_rect[2]-self.dragging.size[0]-6,
														mouse_pos[1]-self.dragging.size[1]/2) )

		elif all([self.board.board_rect[0] < mouse_pos[0]+x*self.dragging.size[0]/2 < (self.board.board_rect[0]+self.board.board_rect[2]) \
																  for x in [-1, 1] ]):
			if mouse_pos[1] <= self.board.board_rect[1]+self.dragging.size[1]/2:
				self._draw_figures_on_board(background, ad=True, reverse=self.side)
				background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0]/2,
																self.board.board_rect[1]+3) )
			elif mouse_pos[1] >= self.board.board_rect[1]+self.board.board_rect[3]-self.dragging.size[1]/2:
				self._draw_figures_on_board(background, ad=True, reverse=self.side)
				background.blit(self.dragging.img, (mouse_pos[0]-self.dragging.size[0]/2,
												self.board.board_rect[1]+self.board.board_rect[3]-self.dragging.size[1]-3) )
	
	def reverse_board(self, background):

		self.board.from_fen(self.board.reverse_fen(self.board.to_fen()))
		self.side = not self.side
		for piece in self.board.PIECES.values():
			piece.side = not piece.side
		self.board.init_piece_columns()
		self.plate_1, self.plate_2 = self.plate_2, self.plate_1 
		self.name1, self.name2 = self.name2, self.name1 
		self.board.draw_background(background)
		self._draw_figures_on_board(background, reverse=self.side)
		self.display_nickname_board(background)
		self.display_reverse_button(background)
		self.display_lightbulbs(background)
		self.update_move_log_board(background, True)
		self.display_beaten_piece(background)
		if self.time:
			self.timer.draw_timer(background, self.side)

	def restart(self, background, side):
		self.game_outcome = None
		if self.side != self.started_side:
			self.plate_1, self.plate_2 = self.plate_2, self.plate_1 
			self.name1, self.name2 = self.name2, self.name1 
		self.side = self.started_side
		for key, piece in self.board.PIECES.items():
			if key.islower():
				piece.side = not self.started_side	
			else:
				piece.side = self.started_side
		self.beaten_piece_white = {name:0 for name in ['P','B','N','R','Q']}
		self.beaten_piece_black = {name:0 for name in ['p','b','n','r','q']}
		self.pawn_changing_over_state = [0]*4

		self.board = Board(375, 80, self.scaling_factor, self.side, self.piece_img_dict, self.board_img, self.board_reverse_img) if self.side else \
					 Board(375, 80, self.scaling_factor, self.side, self.piece_img_dict, self.board_img, self.board_reverse_img, BASEBOARD_BLACK)
		if self.game_mode == "pc":
			# Side is indicates which side are white, bottom - True, up - False? player always
			# start on bottom side
			self.is_player_white = self.side
			self.ai = Ai(self.board, self.is_player_white, 3)

		self.board.draw_background(background)
		self._draw_figures_on_board(background, reverse=self.started_side)
		self.display_nickname_board(background)
		self.display_reverse_button(background)
		self.display_lightbulbs(background)
		self.display_move_log_board(background)
		if self.time:
			self.timer.timer_1, self.timer.timer_2 = self.time*60, self.time*60
			self.timer.draw_timer(background, self.side)

			