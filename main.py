import pygame
import sys
from itertools import cycle
from interface import *
from settings import *
from game import Game

"""

Must be used Python 3.7 or higher from correct work !!!

"""

def main(window_size):
	# sound, windows initialization
	pygame.init()
	pygame.mixer.pre_init(44100, -16, 2, 512)
	pygame.mixer.set_num_channels(64)
	screen = pygame.display.set_mode(window_size) # main canvas
	background = pygame.Surface(screen.get_size()) # rendering canvas
	pygame.display.set_caption('Сhess game')

	# Rendering canvas constant
	width, height = background.get_size()
	scaling_factor = (window_size[0]/WINDOW_SIZE_LIST[0][0],
					  window_size[1]/WINDOW_SIZE_LIST[0][1])

	# Sound
	click_sound = pygame.mixer.Sound('sounds/button_press.wav')
	
	#pygame.mouse.set_visible( False ) #makes mouse invisible
	# Class init
	interf = Interface(scaling_factor)
	cord_x = 145
	button_play = Button(scaling_factor,
							'images/interface/play.png',
							'images/interface/play_press.png',
							cord_x, 280)
	button_play_online = Button(scaling_factor,
							'images/interface/play_online.png',
							'images/interface/play_online_press.png',
							cord_x, 380)
	button_settings = Button(scaling_factor,
							'images/interface/settings.png',
							'images/interface/settings_press.png',
							cord_x, 480)
	button_about = Button(scaling_factor,
							'images/interface/about.png',
							'images/interface/about_press.png',
							cord_x, 580)
	button_exit = Button(scaling_factor,
							'images/interface/exit.png',
							'images/interface/exit_press.png',
							cord_x, 680)

	# main loop
	while True:
		for event in pygame.event.get():
			mouse_pos = pygame.mouse.get_pos()
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					sys.exit()
				if event.key == pygame.K_a:
					return 
			if event.type == pygame.MOUSEBUTTONDOWN:
					if button_play.isOver(mouse_pos):
						click_sound.play()
						play(screen,background,scaling_factor)
					if button_play_online.isOver(mouse_pos):
						click_sound.play()
						pass
					if button_settings.isOver(mouse_pos):
						click_sound.play()
						pass
					if button_about.isOver(mouse_pos):
						click_sound.play()
						pass
					if button_exit.isOver(mouse_pos):
						click_sound.play()
						pass
					if button_exit.isOver(mouse_pos):
						sys.exit()
			if event.type == pygame.MOUSEMOTION:
				if button_play.isOver(mouse_pos):
					button_play.show_image = 1
				else:
					button_play.show_image = 0
				if button_play_online.isOver(mouse_pos):
					button_play_online.show_image = 1
				else:
					button_play_online.show_image = 0
				if button_settings.isOver(mouse_pos):
					button_settings.show_image = 1
				else:
					button_settings.show_image = 0
				if button_about.isOver(mouse_pos):
					button_about.show_image = 1
				else:
					button_about.show_image = 0
				if button_exit.isOver(mouse_pos):
					button_exit.show_image = 1
				else:
					button_exit.show_image = 0

		interf.draw_background(background)
		button_play.draw(background)
		button_play_online.draw(background)
		button_settings.draw(background)
		button_about.draw(background)
		button_exit.draw(background)
		interf.draw_title(background)
		interf.scoreboard(background)
		#background.blit(interf.cursor_img, (mouse_pos[0], mouse_pos[1]))

		#screen.blit(pygame.transform.scale(background, window_size),(0,0)) # [1080,824]
		#pygame.display.flip()
		screen.blit(background, (0,0))
		pygame.display.update()

def play(screen, background, scaling_factor):

	# Class init
	interf_play = InterfacePlay(scaling_factor)

	# Constant from input field clear
	clear = False
	clear_count = 0

	# main loop
	while True:
		for event in pygame.event.get():
			mouse_pos = pygame.mouse.get_pos()
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					return
				if event.key == pygame.K_RETURN:
					if interf_play.input_field_1_active:
						interf_play.input_field_1_active = False	
					elif interf_play.input_field_2_active:
						interf_play.input_field_2_active = False
					elif interf_play.input_field_3_active:
						interf_play.input_field_3_active = False
					elif interf_play.pc_input_field_active:
						interf_play.pc_input_field_active = False
				if interf_play.input_field_1_active:
					if event.unicode.isalpha() or event.unicode == ' ':
						if interf_play.text_width+round(16*scaling_factor[0]) < interf_play.name_input_field_1_rect[2]:
							interf_play.name_1 = interf_play.name_1[:-1] + event.unicode + interf_play.name_1[-1]
							interf_play.stick_counter = 20
					elif event.key == pygame.K_BACKSPACE:
						clear = True
				if interf_play.input_field_2_active:
					if event.unicode.isalpha() or event.unicode == ' ':
						if interf_play.text_width+round(16*scaling_factor[0]) < interf_play.name_input_field_2_rect[2]:
							interf_play.name_2 = interf_play.name_2[:-1] + event.unicode + interf_play.name_2[-1]
							interf_play.stick_counter = 20
					elif event.key == pygame.K_BACKSPACE:
						clear = True
				if interf_play.input_field_3_active:
					if event.unicode.isnumeric() :
						if interf_play.text_width+round(50*scaling_factor[0]) < interf_play.field_from_timer[2]:
							print (interf_play.text_cord_3)
							interf_play.text_cord_3[0] -= interf_play.font.render(event.unicode, 1, (37, 36, 56)).get_size()[0]*0.5
							print (interf_play.text_cord_3)
							interf_play.timer = interf_play.timer[:-1] + event.unicode + interf_play.timer[-1]
							interf_play.stick_counter = 20
					elif event.key == pygame.K_BACKSPACE:
						clear = True
				if interf_play.pc_input_field_active:
					if event.unicode.isalpha() or event.unicode == ' ':
						if interf_play.text_width+round(20*scaling_factor[0]) <  interf_play.pc_name_input_field_rect[2]:
							interf_play.name_3 = interf_play.name_3[:-1] + event.unicode + interf_play.name_3[-1]
							interf_play.stick_counter = 20
					elif event.key == pygame.K_BACKSPACE:
						clear = True

			if event.type == pygame.KEYUP:
				if event.key == pygame.K_BACKSPACE:
					clear = False
					
			if event.type == pygame.MOUSEBUTTONDOWN:
				if interf_play.isOver(mouse_pos) :
					interf_play.show_image = not interf_play.show_image
					interf_play.input_field_1_active = False
					interf_play.input_field_2_active = False
					interf_play.input_field_3_active = False
					interf_play.name_1 = '|'
					interf_play.name_2 = '|'
					interf_play.timer = '|'
					interf_play.current_state = 0
					interf_play.show_image_pc = False
					interf_play.show_fog = True
					interf_play.side_selection = True
					interf_play.drop_cords()
				if interf_play.pcb_isOver(mouse_pos) :
					interf_play.show_image_pc = not interf_play.show_image_pc
					interf_play.show_image = False
					interf_play.show_fog_pc = True
					interf_play.pc_input_field_active = False
					interf_play.circle1_activ = False
					interf_play.circle2_activ = False
					interf_play.circle3_activ = False
					interf_play.side_selection_2 = True
					interf_play.name_3 = '|'
					interf_play.drop_cords()
				if interf_play.button_isOver(mouse_pos) == 2:
					return
				if interf_play.button_isOver(mouse_pos) == 1:
					print (interf_play.create_info_package())
					game (screen, background, scaling_factor,						
							interf_play.create_info_package())
					interf_play.show_image = False
					interf_play.show_image_pc = False

			if event.type == pygame.MOUSEMOTION:
				if not interf_play.show_image:
					if interf_play.isOver(mouse_pos):
						interf_play.show_fog = False
					else:
						interf_play.show_fog = True
				if not interf_play.show_image_pc:
					if interf_play.pcb_isOver(mouse_pos):
						interf_play.show_fog_pc = False
					else:
						interf_play.show_fog_pc = True
				if interf_play.show_image:
					if interf_play.triangle_left_is_over(mouse_pos, interf_play.area_around_left_triangles_1,
								interf_play.left_triangle_area_1) == 1:
						interf_play.show_left_triangle_1 = True
					elif interf_play.triangle_right_is_over(mouse_pos, interf_play.area_around_right_triangles_1,
								interf_play.right_triangle_area_1) == 1:
						interf_play.show_right_triangle_1 = True
					elif interf_play.triangle_left_is_over(mouse_pos, interf_play.area_around_left_triangles_2,
								interf_play.left_triangle_area_2) == 1:
						interf_play.show_left_triangle_2 = True
					elif interf_play.triangle_right_is_over(mouse_pos, interf_play.area_around_right_triangles_2,
								interf_play.right_triangle_area_2) == 1:
						interf_play.show_right_triangle_2 = True
					else:
						interf_play.show_left_triangle_1 = False
						interf_play.show_right_triangle_1 = False
						interf_play.show_left_triangle_2 = False
						interf_play.show_right_triangle_2 = False
				if interf_play.show_image_pc:
					if interf_play.triangle_left_is_over(mouse_pos, interf_play.area_around_left_triangles_3,
								interf_play.left_triangle_area_3) == 1:
						interf_play.show_left_triangle_3 = True
					elif interf_play.triangle_right_is_over(mouse_pos, interf_play.area_around_right_triangles_3,
								interf_play.right_triangle_area_3) == 1:
						interf_play.show_right_triangle_3 = True
					else:
						interf_play.show_left_triangle_3 = False
						interf_play.show_right_triangle_3 = False
				if interf_play.button_isOver(mouse_pos) == 1:
					interf_play.show_button1 = True
				elif interf_play.button_isOver(mouse_pos) == 2:
					interf_play.show_button2 = True
				else:
					interf_play.show_button1 = False
					interf_play.show_button2 = False

		if clear and clear_count > 3:
			if interf_play.input_field_1_active:
				interf_play.name_1 = interf_play.name_1[:-2] + interf_play.name_1[-1]
				interf_play.stick_counter = 20
				clear_count = 0
			elif interf_play.input_field_2_active:
				interf_play.name_2 = interf_play.name_2[:-2] + interf_play.name_2[-1]
				interf_play.stick_counter = 20
				clear_count = 0
			elif interf_play.pc_input_field_active:
				interf_play.name_3 = interf_play.name_3[:-2] + interf_play.name_3[-1]
				interf_play.stick_counter = 20
				clear_count = 0
			elif interf_play.input_field_3_active:
				if interf_play.timer[-2:-1] != '':
					interf_play.text_cord_3[0] += interf_play.font.render(interf_play.timer[-2:-1], 1, (37, 36, 56)).get_size()[0]*0.5
					interf_play.timer = interf_play.timer[:-2] + interf_play.timer[-1]
					interf_play.stick_counter = 20
					clear_count = 0
		if clear:
			clear_count += 1

		interf_play.draw_background(background)
		interf_play.draw_tp_board(background)
		interf_play.draw_pc_board(background)
		interf_play.draw_button(background)

		screen.blit(background, (0,0))
		pygame.display.update()
	
def game(screen, background, scaling_factor, game_info):
	# Class init
	piece_img_dict, board_img, board_reverse_img = load_piece_and_board_img()
	game = Game(background, scaling_factor, game_info, piece_img_dict, board_img, board_reverse_img)

	# first draw the board before counting the move for the bot
	screen.blit(background, (0,0))
	pygame.display.update()

	# main loop
	while True:
		
		# handles the version of the game against the computer
		if game.game_mode == "pc":
			if not game.exchange_pawn and not game.game_outcome:
				game.switch(background)

		for event in pygame.event.get():
			mouse_pos = pygame.mouse.get_pos()
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return 
					if event.key == pygame.K_f:
						if game.dragging == None:
							game.reverse_board(background)
					if event.key == pygame.K_g:
						print(game.board.pawn_columns_list)
						print(game.board.rook_columns_list)
					if event.key == pygame.K_h:
						print([*game.board.get_all_ligal_moves_2()])
			if event.type == pygame.MOUSEMOTION:
				if game.dragging:
					game.visual_movement_of_figure(background, mouse_pos)
				if game.exchange_pawn:
					game.check_mouse_over_pawn_change_window(mouse_pos)
				if game.game_outcome:
					game.check_mouse_over_checkmate_button(mouse_pos)
			if event.type == pygame.MOUSEBUTTONDOWN:
				if game.exchange_pawn:
					game.check_click_on_pawn_change_window(background, mouse_pos)
				elif game.game_outcome:
					choice = game.check_click_on_checkmate_button(mouse_pos)
					if choice == 0:
						return
					if choice == 1:
						game.restart(background, game_info['side'])
				elif game.check_click_on_reverse_button(mouse_pos):
					if game.dragging == None:
						game.reverse_board(background)
				else:
					game.mouse_tracking(background, mouse_pos)

		if game.exchange_pawn:
			game.draw_pawn_change_button(background)
		elif game.game_outcome:
			game.draw_checkmate_button(background)
		elif game.timer:
			game.timer.update_timer(background, game.board.active_player, game.side)
			if game.timer.timer_1 <= 0:
				win, los = (game.name2, game.name1) if game.side else (game.name1, game.name2)
				game.end_game(background, win, los)
			elif game.timer.timer_2 <= 0:
				win, los = (game.name1, game.name2) if game.side else (game.name2, game.name1)
				game.end_game(background, win, los)

		screen.blit(background, (0,0))
		pygame.display.update()


def settings():
	pass


def infinity_loop():
	for size in cycle(WINDOW_SIZE_LIST):
		main(size)




if __name__ == '__main__':
	infinity_loop()
