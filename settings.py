import os
import pygame

# Setting constants from interface
#[(1024,600), (1200,720), (1280,960), (1600,768), (1600,900) ]
WINDOW_SIZE_LIST = [(1080, 820),(1200, 910), (1280,960)]
PATH_TO_INTERFACE = 'images/interface/'
PIECE_SET = 'set_test' # A set of shapes that are selected by default

# Settings functions from interface
def load_piece_and_board_img():
	piece_board_img_dict = {}
	path = os.getcwd()+'/images/pieces/'+PIECE_SET
	for name in os.listdir(path):
		piece_board_img_dict[name.split('.')[0]] = pygame.image.load(path+'/'+name)
	board_img = piece_board_img_dict.pop('board')
	board_reserse_img = pygame.image.load('images/pieces/board_reverse.png')
	return piece_board_img_dict, board_img, board_reserse_img

