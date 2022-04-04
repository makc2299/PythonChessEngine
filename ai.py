import pygame
import pickle
import random
import sys
import time
import copy

import chess
from chess.polyglot import open_reader

import table

# The class that contains: evaluation function,
# searching algorithm 
class Ai:

	depth = 4

	board_caches = {}

	cache_hit = 0
	cache_miss = 0

	try:
		cache = open('data/cache.p', 'rb')
	except:
		cache = open('data/cache.p', 'wb')
		pickle.dump(board_caches, cache)
	else:
		board_caches = pickle.load(cache)
		cache.close()

	def __init__(self, board, is_player_white, complexity):
		self.board = board # my own board class 
		self.board_ = chess.Board() # class from chess library it needed to refer to opening books 
		self.is_ai_white = not is_player_white
		self.complexity = complexity
		self.moves_made = 0

		self.max_search_time = 200
		self.min_search_depth = 3
		# Null move parameter for depth
		self.R = 2

		# hash
		self.valid_moves_history = {}
		self.killer_moves = {}
		self.best_moves = {}

		# test
		self.evaluation_call = 0
		self.time_stamp = []
		self.tt_return = 0


	def try_take_from_opening_books(self, fen):
		self.board_.set_fen(fen)
		with open_reader('data/Perfect2021.bin') as reader:
			return [
				[str(entry.move), entry.weight] for entry in reader.find_all(self.board_)
			]

	# starts a recursive search tree
	def ai_move(self, fen, side):

		t = time.time()
		self.board.push_call = 0
		self.evaluation_call = 0
		self.tt_return = 0

		for depth in range(self.depth + 1):
			self.killer_moves[depth] = []
		self.valid_moves_history = {}
		
		# parameter that changes when the player hits reverse board button
		self.side = side

		# try thake move from opening book 
		if self.moves_made < 10:
			if side:
				opening_moves = self.try_take_from_opening_books(fen)
			else:
				fen = self.board.reverse_fen(fen)
				opening_moves = [ [self.board.mirror_move(move[0]), move[1]] for move in self.try_take_from_opening_books(fen)]
			if opening_moves:
				return sorted(opening_moves, key=lambda x: x[1], reverse=True)[0][0]
				#return sorted(opening_moves, key=lambda x: x[1], reverse=True)[0][0] if random.random() < 0.3 \
				#       else random.choice(opening_moves)[0]    

		# else start search procces
		# Init parameters for iterative deepening
		self.tt_entry = {'value': 0, 'flag': '', 'depth': 0, 'best move': None, 'valid moves': []}
		self.tt_entry_q = {'value': 0, 'flag': ''}
		self.best_moves = {}

		# Iterative deepening
		time_start = time.time()
		for depth in range(1, self.depth + 1):
			# ------------------------------------------------------------------> 1 if self.is_ai_white else -1 - right
			move, evaluation = self.negamax(depth, -float("inf"), float("inf"), -1 if self.is_ai_white else 1, False)
			self.best_moves[depth] = [move, evaluation]
			

			timer = time.time() - time_start

			if (timer > self.max_search_time and depth >= self.min_search_depth) or (evaluation / 100) > 100:
				break


		# increase the number of moves made
		self.moves_made += 1
		print ("Push call - "+str(self.board.push_call))
		print ("Evaluation call - "+ str(self.evaluation_call))
		print ("Tt return - "+str(self.tt_return))
		tt = time.time()-t
		self.time_stamp.append(tt)
		# if self.moves_made >= 10:
		#   print ("average time on 10 moves: {0}".format(sum(self.time_stamp) / len(self.time_stamp)) ) 
		#   sys.exit()
		print ("Time to calculate move - {0} for depth - {1}".format(tt, self.depth))
		
		# if len(self.best_moves) % 2 == 0:
		#   move = self.best_moves[-1][0]
		# else:
		#   move = self.best_moves[-2][0]
		print ("======================")
		print (self.best_moves)

		return move #self.best_moves[-1][0]

	def negamax(self, depth, alpha, beta, color, allow_nullmove):
		alpha_original = alpha

		# Transposition table lookup
		key = self.board.zobrist_key
		#key = self.board.to_fen()
		if key in self.tt_entry and self.tt_entry[key]['depth'] >= depth:
			if self.tt_entry[key]['flag'] == 'exact':
				self.tt_return += 1
				return self.tt_entry[key]['best move'], self.tt_entry[key]['value']
			elif self.tt_entry[key]['flag'] == 'lowerbound':
				alpha = max(alpha, self.tt_entry[key]['value'])
			elif self.tt_entry[key]['flag'] == 'upperbound':
				beta = min(beta, self.tt_entry[key]['value'])
			if alpha >= beta:
				self.tt_return += 1
				return self.tt_entry[key]['best move'], self.tt_entry[key]['value']

		# Depth with quiescence search
		# if depth == 0:
		# 	if self.board.move_stack[-1].is_capture:
		# 		#return None, self.quiescence(-beta, -alpha, -color, 0) # <- work as shit
		# 		return None, self.quiescence(alpha, beta, -color, 0) # <- classic
		# 	else:
		# 		return None, self.evaluation(depth) * color

		# reached the desired depth
		if depth == 0 or self.board.is_check_mate or self.board.is_stale_mate:
			return None, self.evaluation(depth) * color

		# Don't search valid moves again if it has been done in last iteration
		if key in self.valid_moves_history and self.valid_moves_history[key]:
			moves = self.valid_moves_history[key]
		else:
			moves = [*self.board.get_all_ligal_moves(self.side)]
			self.valid_moves_history[key] = moves

		# NOT !!!!!!!!!!!!!!!
		# if checkmate or stalemate 
		# if not [*self.board.get_all_ligal_moves(self.side)]:
		# 	return None, self.evaluation(depth) * color

		# Null move logic 
		if allow_nullmove and depth - 1 - self.R >= 0: 
			if not self.board.check():
				self.board.push_null_move()
				evaluation = -self.negamax(depth - 1 - self.R, -beta, -beta + 1, -color, False)[1]
				self.board.pop_null_move()

				if evaluation >= beta:
					print ("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
					return None, evaluation

		# Sort moves before Negamax
		moves = self.sort_moves(moves, depth)

		max_eval = -float("inf")
		# Principal Variation Search
		# pv_move_in_hash = False
		# if depth in self.best_moves:
		# 	pv_move_in_hash = True
		for i in range(len(moves)):
			#if i == 0 and pv_move_in_hash:
			self.board.push(moves[i], self.side)
		
			#local_score = self.minimax(depth - 1, alpha, beta, not is_maxing_white)
			score = -self.negamax(depth - 1, -beta, -alpha, -color, True)[1]

			self.board.pop()

			# else:
			# 	self.board.push(moves[i], self.side)
				
			# 	score = -self.negamax(depth - 1, -alpha - 1, -alpha, -color, True)[1]

			# 	self.board.pop()

			# 	if alpha < score < beta:
			# 		self.board.push(moves[i], self.side)
				
			# 		score = -self.negamax(depth - 1, -beta, -alpha, -color, True)[1]

			# 		self.board.pop()

			if score > max_eval:
				max_eval = score
				best_move = moves[i]
			alpha = max(alpha, max_eval)

			if beta <= alpha:

				# Killer moves
				if not self.board.is_capture(moves[i]):
					self.killer_moves[depth].append(moves[i])
					if len(self.killer_moves[depth]) == 2:  # Keep killer moves at a maximum of x per depth
						self.killer_moves[depth].pop(0)
				
				break

		# makes a call to the event queue so that the OS 
		# does not think that the application window is frozen
		pygame.event.pump()

		# Transposition table saving
		self.tt_entry[self.board.zobrist_key] = {'value': max_eval}
		if max_eval <= alpha_original:
			self.tt_entry[self.board.zobrist_key]['flag'] = 'upperbound'
		elif max_eval >= beta:
			self.tt_entry[self.board.zobrist_key]['flag'] = 'lowerbound'
		else:
			self.tt_entry[self.board.zobrist_key]['flag'] = 'exact'

		self.tt_entry[self.board.zobrist_key]['depth'] = depth
		self.tt_entry[self.board.zobrist_key]['best move'] = best_move

		# key = self.board.to_fen()
		# self.tt_entry[key] = {'value': max_eval}
		# if max_eval <= alpha_original:
		# 	self.tt_entry[key]['flag'] = 'upperbound'
		# elif max_eval >= beta:
		# 	self.tt_entry[key]['flag'] = 'lowerbound'
		# else:
		# 	self.tt_entry[key]['flag'] = 'exact'

		# self.tt_entry[key]['depth'] = depth
		# self.tt_entry[key]['best move'] = best_move

		return best_move, max_eval

	def sort_moves(self, moves, depth):

		# MVV / LVA sort
		moves = [ move[0] for move in sorted(moves, key=lambda x: x[1], reverse=True)]

		# Killer moves
		if self.killer_moves[depth]:
			for move in self.killer_moves[depth]:
				if move in moves:
					moves.remove(move)
					moves.insert(0, move)

		# Best move from previous iteration is picked as best guess for next iteration
		if self.board.zobrist_key in self.tt_entry:
			previous_best = self.tt_entry[self.board.zobrist_key]["best move"]
			if previous_best in moves:
				moves.remove(previous_best)
				moves.insert(0, previous_best)

		return moves

	def quiescence(self, alpha, beta, color, extra_depth):

		# recursion exit condition
		extra_depth += 1

		# Check if value is in table
		key = self.board.zobrist_key
		if key in self.tt_entry_q:
			if self.tt_entry_q[key]['flag'] == 'exact':
				score = self.tt_entry_q[key]['value']
			else:
				score = color * self.evaluation(0)
				self.tt_entry_q[key] = {'flag': 'exact'}
				self.tt_entry_q[key]['value'] = score
		else:
			score = self.evaluation(0)
			self.tt_entry_q[key] = {'flag': 'exact'}
			self.tt_entry_q[key]['value'] = score

		########### wtf ##############
		# big_delta = table.PEACE_VALUES[self.board.move_stack[-1].is_capture] + 200
		# if score < alpha - big_delta:
		# 	print ("I dont now what is it 1")
		# 	return alpha
		##############################
		if score >= beta:
			return beta
		if score > alpha:
			alpha = score

		# If having looked through 2 moves then stop and return value
		if extra_depth >= 3:
			return score

		# Don't search valid moves again if it has been done in last iteration
		if key in self.valid_moves_history and self.valid_moves_history[key]:
			moves = self.valid_moves_history[key]
		else:
			moves = [*self.board.get_all_ligal_moves(self.side)]
			self.valid_moves_history[key] = moves

		# Sort moves before Negamax
		moves = self.sort_moves(moves, 0)

		for move in moves:
			if not self.board.is_capture(move):
				continue

			self.board.push(move, self.side)        
			score = -self.quiescence(-beta, -alpha, -color, extra_depth)
			self.board.pop()

			if score >= beta:
				return beta
			if score > alpha:
				alpha = score

		return alpha

	def evaluation(self, depth):

		self.evaluation_call += 1
		# return the current board as [['.', '.', '.', 'K', ...], ['p', '.', '.', 'b', ...], ... ]
		current_board = self.board.board_as_array(wrapped=True)
		
		# Check if in checkmate or stalemate
		# !!! ATENTION TO SIGN
		if self.board.is_check_mate:
			# !!! these are the correct values for the parties 
			return 1e9+depth if self.board.active_player else -1e9-depth # <- it's right 
			#return 1e9 if self.board.active_player else -1e9
		if self.board.is_stale_mate:
			return 0

		# init score
		black_score = 0
		white_score = 0
		
		# separation of heuristics into until the endgame and after
		if not self.board.is_endgame:

			# # material and table position heuristic
			for key in self.board.PIECES:
				for shift in _scan_lsb_first(self.board.PIECES[key].position):
					if self.side:
						if key.islower():
							black_score += table.PEACE_VALUES[key] + table.TABLE[key][7-( 7-(shift//8) )%8][7-( 7-(shift%8) )%8]
						else:
							white_score += table.PEACE_VALUES[key.lower()] +  table.TABLE[key.lower()][7-(shift//8)][7-(shift%8)] 
					else:
						if key.isupper():
							white_score += table.PEACE_VALUES[key.lower()] + table.TABLE[key.lower()][7-( 7-(shift//8) )%8][7-( 7-(shift%8) )%8]
						else:
							black_score += table.PEACE_VALUES[key] + table.TABLE[key][7-(shift//8)][7-(shift%8)]

			# Castling bonus
			if self.board.move_done < 30:
				# bonus for the presence of castling rights
				if self.board.white_king_side_castle_right or self.board.white_queen_side_castle_right:
					white_score += table.castling_bonus

				if self.board.black_king_side_castle_right or self.board.black_queen_side_castle_right:
					black_score += table.castling_bonus

				# bonus for made castle
				if self.board.move_stack[-1].is_castling:
					# print ("cASTLING ")
					# print ("white score"+str(white_score))
					# print ("black score"+str(black_score))
					# print (self.board)

					if self.board.active_player:
						black_score += table.castling_made
					else:
						white_score += table.castling_made
					# print ("white score"+str(white_score))
					# print ("black score"+str(black_score))
					# input("input: ")

			# Bishop pair bonus
			# if sum([ x for x in _scan_lsb_first(self.board.PIECES['B'].position)]) == 2:
			#     white_score += table.bishop_pair_bonus
			# if sum([ x for x in _scan_lsb_first(self.board.PIECES['b'].position)]) == 2:
			#     black_score += table.bishop_pair_bonus

			# # If there are several pawns on the same file, the penalty it
			# white_pawns, black_pawns = set(self.board.pawn_columns_list[0]), \
			#  						   set(self.board.pawn_columns_list[1])
			# white_score += (len(self.board.pawn_columns_list[0]) - len(white_pawns)) * table.double_pawn_punishment
			# black_score += (len(self.board.pawn_columns_list[1]) - len(black_pawns)) * table.double_pawn_punishment

			# # # Isolated pawn punishment
			# white_score += len([i for i in white_pawns if i - 1 not in white_pawns and i + 1 not in white_pawns]) * table.isolated_pawn_punishment
			# black_score += len([i for i in black_pawns if i - 1 not in black_pawns and i + 1 not in black_pawns]) * table.isolated_pawn_punishment

			# Rook on open and semi-open file bonus
			# for rook in self.board.rook_columns_list[0]:
			# 	if rook not in white_pawns:
			# 		white_score += table.rook_on_semi_open_file_bonus
			# 		if rook not in black_pawns:
			# 			white_score += table.rook_on_open_file_bonus
			# for rook in self.board.rook_columns_list[1]:
			# 	if rook not in black_pawns:
			# 		black_score += table.rook_on_semi_open_file_bonus
			# 		if rook not in white_pawns:
			# 			black_score += table.rook_on_open_file_bonus

			# Penalise blocked pawns (penalizes a pawn if there is a piece in front of it)
			# Bonus to pawns protected by other pawns
			# side depending
			if self.side:
				for shift in _scan_lsb_first(self.board.PIECES["P"].position):
					# checks if there is a piece in front of a pawn
					if current_board[(8-(shift//8)) - 1][8-(shift%8)] != '.':
						white_score += table.blocked_pawn_penalty
					# checks if a pawn is protected by a pawn
					if current_board[(8-(shift//8)) + 1][(8-(shift%8)) - 1] == "P" or \
					   current_board[(8-(shift//8)) + 1][(8-(shift%8)) + 1] == "P":
						white_score += table.defended_pawn_bonus

				for shift in _scan_lsb_first(self.board.PIECES["p"].position):
					# checks if there is a piece in front of a pawn
					if current_board[(8-(shift//8)) + 1][8-(shift%8)] != '.':
						black_score += table.blocked_pawn_penalty
					# checks if a pawn is protected by a pawn
					if current_board[(8-(shift//8)) - 1][(8-(shift%8)) - 1] == "p" or \
					   current_board[(8-(shift//8)) - 1][(8-(shift%8)) + 1] == "p":
						black_score += table.defended_pawn_bonus
			else:
				for shift in _scan_lsb_first(self.board.PIECES["P"].position):
					# checks if there is a piece in front of a pawn
					if current_board[(8-(shift//8)) + 1][8-(shift%8)] != '.':
						white_score += table.blocked_pawn_penalty
					# checks if a pawn is protected by a pawn
					if current_board[(8-(shift//8)) - 1][(8-(shift%8)) - 1] == "P" or \
					   current_board[(8-(shift//8)) - 1][(8-(shift%8)) + 1] == "P":
						white_score += table.defended_pawn_bonus

				for shift in _scan_lsb_first(self.board.PIECES["p"].position):
					# checks if there is a piece in front of a pawn
					if current_board[(8-(shift//8)) - 1][8-(shift%8)] != '.':
						black_score += table.blocked_pawn_penalty
					# checks if a pawn is protected by a pawn
					if current_board[(8-(shift//8)) + 1][(8-(shift%8)) - 1] == "p" or \
					   current_board[(8-(shift//8)) + 1][(8-(shift%8)) + 1] == "p":
						white_score += table.defended_pawn_bonus


		# endgame heuristic
		else:

			# material and table position heuristic
			for key in self.board.PIECES:
				for shift in _scan_lsb_first(self.board.PIECES[key].position):
					if self.side:
						if key.islower():
							black_score += table.PEACE_VALUES_END[key] + table.LATE_GAME_TABLE[key][7-( 7-(shift//8) )%8][7-( 7-(shift%8) )%8 ]
						else:
							white_score += table.PEACE_VALUES_END[key.lower()] + table.LATE_GAME_TABLE[key.lower()][7-(shift//8)][7-(shift%8)]
					else:
						if key.isupper():
							white_score += table.PEACE_VALUES_END[key.lower()] + table.LATE_GAME_TABLE[key.lower()][7-( 7-(shift//8) )%8][7-( 7-(shift%8) )%8 ]
						else:
							black_score += table.PEACE_VALUES_END[key] + table.LATE_GAME_TABLE[key][7-(shift//8)][7-(shift%8)]


		print (self.board.is_endgame)
		# if self.board.is_endgame:
		# 	print ("endgame phase")
		# 	sys.exit()
		# print (score + material)
		# print (self)
		# sys.exit()
		# if (score + material) == -565:
		# 	print (score + material)
		# 	print (self)
		# 	sys.exit()

		# if self.board.active_player:
		# 	# при глубине в 3 последний узел будет ходом черных, тоесть active_player будет True
		# 	print (" black made a move")
		# else:
		# 	print ("Oyasumi Oyasumi ")


		return black_score - white_score

	def __str__(self):
		return str(self.board_)

	def clear_move_stack(self):
		pass
# a = Ai(1,2,3)
# #a.try_take_from_opening_books("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
# print(a.try_take_from_opening_books('rnbqkb1r/ppp1pppp/5n2/3p4/3P4/5NP1/PPP1PP1P/RNBQKB1R b KQkq - 0 3'))
# #a.try_take_from_opening_books('4k3/8/8/1b6/8/2pR4/4K3/8 w - - 0 1')
# print(list(a.board_.legal_moves))
# print (a)

class BoardState():

	#def __init__(self, board: object, move: str, from_key: str, from_bb: int, to_key: str, to_bb: int):
	def __init__(self, board: object, move: str, is_feasible_move_attack: str or bool,
												 pieces_key: str):
		# where the figure was taken from and where it was moved
		self.move = move
		# values for the validation three repetition rules
		self.is_pawn_moved = True if pieces_key in ["P","p"] else False
		self.pieces_key = pieces_key # the key of the piece that moves
		self.is_capture = is_feasible_move_attack
		self.is_castling = 0 # 1 - king side, 2 - queen side, 0 - not castling
		self.is_en_passant = False
		self.is_promotion = False # False - no promotion or "Q" - key of the selected piece
		self.is_check = False
		self.is_checkmate = False
		self.is_stalemate = False

		# SAVE PREVIOUS BOARD STATE
		# value bitboard for each pieces
		self.K = board.PIECES["K"].position
		self.Q = board.PIECES["Q"].position
		self.B = board.PIECES["B"].position
		self.R = board.PIECES["R"].position
		self.N = board.PIECES["N"].position
		self.P = board.PIECES["P"].position

		self.k = board.PIECES["k"].position
		self.q = board.PIECES["q"].position
		self.b = board.PIECES["b"].position
		self.r = board.PIECES["r"].position
		self.n = board.PIECES["n"].position
		self.p = board.PIECES["p"].position

		self.zobrist_key = board.zobrist_key
		self.pawn_columns_list = copy.deepcopy(board.pawn_columns_list)
		self.rook_columns_list = copy.deepcopy(board.rook_columns_list)
		# self.pawn_columns_list_w, self.pawn_columns_list_b = board.pawn_columns_list[0][:], \
		# 													board.pawn_columns_list[1][:]
		# self.rook_columns_list_w, self.rook_columns_list_b = board.rook_columns_list[0][:], \
		# 													board.rook_columns_list[1][:]

		# # board state parameters
		self.active_player = board.active_player 
		self.black_king_side_castle_right = board.black_king_side_castle_right
		self.black_queen_side_castle_right = board.black_queen_side_castle_right
		self.white_king_side_castle_right = board.white_king_side_castle_right
		self.white_queen_side_castle_right = board.white_queen_side_castle_right
		self.ep_move = board.ep_move
		self.half_move_clock = board.half_move_clock
		self.move_number = board.move_number

		# Did the perfect move put a checkmate or stalemate
		self.is_check_mate = board.is_check_mate 
		self.is_stale_mate = board.is_stale_mate

	def restore(self, board: object):
		# board.PIECES[self.peace_type].position = self.from_bb
		# board.PIECES[self.attacked_peace_type].position = self.to_bb
		board.PIECES["K"].position = self.K 
		board.PIECES["Q"].position = self.Q 
		board.PIECES["B"].position = self.B
		board.PIECES["R"].position = self.R
		board.PIECES["N"].position = self.N
		board.PIECES["P"].position = self.P

		board.PIECES["k"].position = self.k 
		board.PIECES["q"].position = self.q
		board.PIECES["b"].position = self.b
		board.PIECES["r"].position = self.r
		board.PIECES["n"].position = self.n
		board.PIECES["p"].position = self.p

		board.zobrist_key = self.zobrist_key
		# board.pawn_columns_list[0], board.pawn_columns_list[1] = self.pawn_columns_list_w[:], \
		# 													   self.pawn_columns_list_b[:]
		# board.rook_columns_list[0], board.rook_columns_list[1]  = self.rook_columns_list_w[:], \
		# 													   self.rook_columns_list_b[:]
		board.pawn_columns_list = copy.deepcopy(self.pawn_columns_list)
		board.rook_columns_list = copy.deepcopy(self.rook_columns_list)

		board.active_player = self.active_player 
		board.black_king_side_castle_right = self.black_king_side_castle_right
		board.black_queen_side_castle_right = self.black_queen_side_castle_right
		board.white_king_side_castle_right = self.white_king_side_castle_right
		board.white_queen_side_castle_right = self.white_queen_side_castle_right
		board.ep_move = self.ep_move
		board.half_move_clock = self.half_move_clock
		board.move_number = self.move_number

		board.is_check_mate = self.is_check_mate
		board.is_stale_mate = self.is_stale_mate 


	def get_algebraic_notation(self) -> str:
		if self.is_capture:
			if self.is_pawn_moved:
				if self.is_en_passant:
					if self.is_check:
						if self.is_checkmate:
							return self.move[0]+"×"+self.move[2:]+" e.p"+"++"

						return self.move[0]+"×"+self.move[2:]+" e.p"+"+"

					if self.is_stalemate:				
						return self.move[0]+"×"+self.move[2:]+" e.p"+"="

					return self.move[0]+"×"+self.move[2:]+" e.p"

				if self.is_promotion:
					if self.is_check:
						if self.is_checkmate:
							return self.move[2:]+self.is_promotion.upper()+"++"

						return self.move[2:]+self.is_promotion.upper()+"+"

					if self.is_stalemate:				
						return self.move[2:]+self.is_promotion.upper()+"="

					return self.move[2:]+self.is_promotion.upper()


				if self.is_check:
					if self.is_checkmate:
						return self.move[0]+"×"+self.move[2:]+"++"

					return self.move[0]+"×"+self.move[2:]+"+"

				if self.is_stalemate:				
					return self.move[0]+"×"+self.move[2:]+"="

				return self.move[0]+"×"+self.move[2:]

			if self.is_check:
				if self.is_checkmate:
					return self.pieces_key.upper()+"×"+self.move[2:]+"++"

				return self.pieces_key.upper()+"×"+self.move[2:]+"+"

				if self.is_stalemate:				
					return self.pieces_key.upper()+"×"+self.move[2:]+"="			

			return self.pieces_key.upper()+"×"+self.move[2:]

		else:
			if self.is_pawn_moved:
				if self.is_en_passant:
					if self.is_check:
						if self.is_checkmate:
							return self.move[0]+"×"+self.move[2:]+" e.p"+"++"

						return self.move[0]+"×"+self.move[2:]+" e.p"+"+"

					if self.is_stalemate:				
						return self.move[0]+"×"+self.move[2:]+" e.p"+"="

					return self.move[0]+"×"+self.move[2:]+" e.p"

				if self.is_promotion:
					if self.is_check:
						if self.is_checkmate:
							return self.move[2:]+self.is_promotion.upper()+"++"

						return self.move[2:]+self.is_promotion.upper()+"+"

					if self.is_stalemate:				
						return self.move[2:]+self.is_promotion.upper()+"="

					return self.move[2:]+self.is_promotion.upper()

				if self.is_check:
					if self.is_checkmate:
						return self.move[2:]+"++"

					return self.move[2:]+"+"

				if self.is_stalemate:				
					return self.move[2:]+"="

				return self.move[2:]
			# if castling done
			if self.is_castling:
				if self.is_check:
					if self.is_checkmate:
						return "0-0"+"++" if self.is_castling == 1 else "0-0-0"+"++"

					return "0-0"+"+" if self.is_castling == 1 else "0-0-0"+"+"

				if self.is_stalemate:				
					return "0-0"+"=" if self.is_castling == 1 else "0-0-0"+"="

				return "0-0" if self.is_castling == 1 else "0-0-0"

			# if common move done 
			if self.is_check:
				if self.is_checkmate:
					return self.pieces_key.upper()+self.move[2:]+"++"

				return self.pieces_key.upper()+self.move[2:]+"+"

			if self.is_stalemate:				
				return self.pieces_key.upper()+self.move[2:]+"="

			return self.pieces_key.upper()+self.move[2:]

		return None # should not be performed during normal operation

def b_board_to_str(b):
	return '\n'.join(['{0:064b}'.format(b)[i:i + 8] for i in range(0, 64, 8)])

def _scan_lsb_first(b):
	while b:
		r = b & -b
		yield r.bit_length() - 1
		b ^= r