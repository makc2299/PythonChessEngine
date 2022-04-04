import pygame
import os
import sys
import random
import time
from decorators import get_from_db
from settings import PATH_TO_INTERFACE

class Interface:

	# pygame.font.init()
	# font = pygame.font.Font('KumbhSans-Regular.ttf', 9)
	# board_text = None
	
	def __init__(self, scaling_factor):
		self.scaling_factor = scaling_factor 
		#self.cursor_img = pygame.image.load(PATH_TO_INTERFACE+'cursor_4.png')
		self.title_img = self.transfor_scale(pygame.image.load(PATH_TO_INTERFACE+'title.png'))
		self.background_img = self.transfor_scale(pygame.image.load(PATH_TO_INTERFACE+'background.png'))
		self.board_img = self.transfor_scale(pygame.image.load(PATH_TO_INTERFACE+'board.png'))
		self.board_text = self.__row_data_to_pygame_text_convert()

	
	def transfor_scale(self, img):
		return  pygame.transform.scale(img, (round(img.get_size()[0]*self.scaling_factor[0]),
											 round(img.get_size()[1]*self.scaling_factor[1])))

	@get_from_db
	def __row_data_to_pygame_text_convert(self, data=None):
		res = []
		self._space = 5 
		font = pygame.font.Font('KumbhSans-Regular.ttf', round(18*(self.scaling_factor[0]+self.scaling_factor[1])/2))
		if data:
			for row in data:
				name_1, name_2 = row[1], row[2]
				if len(row[1]) > 6:
					name_1 = row[1][:6] + '...'
				if len(row[2]) > 6:
					name_2 = row[2][:6] + '...'
				part_1 = font.render(row[0]+' - '+name_1+' vs '+name_2, 1, (37, 36, 56))
				if row[3].lower() == 'win':
					part_2 = font.render(row[3], 1, (0, 250, 0))
				else:
					part_2 = font.render(row[3], 1, (250, 0, 0))
				part_3 = font.render(row[4], 1, (37, 36, 56))
				x_from_center = (self.board_img.get_size()[0]-10)//2 - (sum(list(map(lambda x: x.get_size()[0], (part_1,part_2,part_3))))+2*self._space)//2
				res.append((part_1,part_2,part_3,x_from_center))
			if len(data) > 20:
				self._three_dots = font.render('...', 1, (37, 36, 56))
				self._three_dots_cord_x = (self.board_img.get_size()[0]-10)//2 - (self._three_dots.get_size()[0])//2
			return res
		else:
			font = pygame.font.Font('KumbhSans-Regular.ttf', round(20*(self.scaling_factor[0]+self.scaling_factor[1])/2))
			text = font.render('No games yet...', 1, (37, 36, 56))
			return [text]

	def draw_title(self,background):
		background.blit(self.title_img, (90*self.scaling_factor[0], 
										90*self.scaling_factor[1]))

	def draw_background(self, background):
		background.blit(self.background_img, (0,0))

	def scoreboard(self, background):
		background.blit(self.board_img, (2*330*self.scaling_factor[0], 
										2*140*self.scaling_factor[1]))
		indent = 5
		if type(self.board_text[0]) is tuple:
			for row in self.board_text[:20]:
				background.blit(row[0], (660*self.scaling_factor[0]+row[3]+self._space, 
										(330*self.scaling_factor[1]+indent)))
				background.blit(row[1], (660*self.scaling_factor[0]+row[3]+2*self._space+row[0].get_size()[0], 
										(330*self.scaling_factor[1]+indent)))
				background.blit(row[2], (660*self.scaling_factor[0]+row[3]+3*self._space+row[0].get_size()[0]+row[1].get_size()[0], 
										(330*self.scaling_factor[1]+indent)))
				indent += row[1].get_size()[1]
			if len(self.board_text) > 20:
				background.blit(self._three_dots, (660*self.scaling_factor[0]+self._space+self._three_dots_cord_x, 
												 (325*self.scaling_factor[1]+indent)))
		else:
			cord = ((2*350+self.board_img.get_size()[0]//2-self.board_text[0].get_size()[0]//2)*((self.scaling_factor[0]+self.scaling_factor[1])/2),
					(2*140+self.board_img.get_size()[1]//2-self.board_text[0].get_size()[1]//2)*((self.scaling_factor[0]+self.scaling_factor[1])/2))
			background.blit(self.board_text[0], cord)

# The class responsible for the interface in the game settings menu
class InterfacePlay(Interface):
	
	color = (37, 36, 56)

	def __init__(self, scaling_factor):
		super().__init__(scaling_factor)
		# Images, cords, rectangles from player vs player board
		self.tpb_x = 210*scaling_factor[0]
		self.tpb_y = 150*scaling_factor[1]
		self.fog_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'fog.png'))
		self.tp_board_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'two_player_board.png'))
		self.tp_board_press_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'two_player_board_press.png'))
		self.white_black_img = Interface.transfor_scale(self, 
								pygame.image.load(PATH_TO_INTERFACE+'white_black.png'))
		self.black_white_img = Interface.transfor_scale(self, 
								pygame.image.load(PATH_TO_INTERFACE+'black_white.png'))
		self.tp_board_rect = pygame.Rect(self.tpb_x, self.tpb_y,self.tp_board_img.get_size()[0],
										 self.tp_board_press_img.get_size()[1])
		self.tp_board_press_rect = pygame.Rect(self.tpb_x+5, self.tpb_y+6,self.tp_board_press_img.get_size()[0]-10,
										 self.tp_board_press_img.get_size()[1]-12)
		self.name_input_field_1_rect = pygame.Rect(241*scaling_factor[0],361*scaling_factor[1],
												   96*scaling_factor[0],26*scaling_factor[1])
		self.name_input_field_2_rect = pygame.Rect(400*scaling_factor[0],361*scaling_factor[1],
												   96*scaling_factor[0],26*scaling_factor[1])
		self.show_image = False
		self.show_fog = True
		self.input_field_1_active = False
		self.input_field_2_active = False
		self.input_field_3_active = False
		self.font = pygame.font.Font('KumbhSans-Regular.ttf', round(15*(self.scaling_factor[0]+self.scaling_factor[1])/2))
		self.name_1 = '|'
		self.text_cord_1 = (245*scaling_factor[0],367*scaling_factor[1])
		self.name_2 = '|'
		self.text_cord_2 = (404*scaling_factor[0],367*scaling_factor[1])
		self.timer = '|'
		self.default_timer = ['No timer', '10 m', '15 m', '20 m', '25 m', '30 m']
		self.current_state = 0

		self.field_from_timer = pygame.Rect(321*scaling_factor[0],432*scaling_factor[1],
										   96*scaling_factor[0],26*scaling_factor[1])
		self.text_cord_3 = [(self.field_from_timer[0]+self.field_from_timer[2]//2)-4, self.field_from_timer[1]+7]
		self.left_triangle_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'left_triangle.png'))
		self.right_triangle_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'right_triangle.png'))
		self.left_triangle_press_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'left_triangle_press.png'))
		self.right_triangle_press_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'right_triangle_press.png'))
		self.left_triangle_cord_1 = (round(293*scaling_factor[0]),round(429*scaling_factor[1]))
		self.right_triangle_cord_1 = (round(428*scaling_factor[0]),round(429*scaling_factor[1]))
		self.left_triangle_area_1, self.right_triangle_area_1 = self._calculate_triangle_area(self.left_triangle_cord_1,
												self.left_triangle_img, self.right_triangle_cord_1, self.right_triangle_img)								
		self.area_around_left_triangles_1 = pygame.Rect(288*scaling_factor[0],419*scaling_factor[1],
												32*scaling_factor[0],50*scaling_factor[1])
		self.area_around_right_triangles_1 = pygame.Rect(420*scaling_factor[0],419*scaling_factor[1],
												32*scaling_factor[0],50*scaling_factor[1])
		self.show_left_triangle_1 = False
		self.show_right_triangle_1 = False
		# =======================================================================

		# Images, cords, rectangles, triangles from player vs computer board
		self.pcb_x = self.tpb_x + self.tp_board_img.get_size()[0] + 30
		self.pcb_y = 150*scaling_factor[1]
		self.pc_board_img = Interface.transfor_scale(self, 
										pygame.image.load(PATH_TO_INTERFACE+'player_computer_board2.png'))
		self.pc_board_press_img = Interface.transfor_scale(self, 
										pygame.image.load(PATH_TO_INTERFACE+'player_computer_press_board.png'))
		self.pc_board_rect = pygame.Rect(self.pcb_x, self.pcb_y,self.pc_board_img.get_size()[0],
										 self.pc_board_press_img.get_size()[1])
		self.pc_board_press_rect = pygame.Rect(self.pcb_x+5, self.pcb_y+6,self.pc_board_press_img.get_size()[0]-10,
										 self.pc_board_press_img.get_size()[1]-12)
		self.circle_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'circle.png'))
		self.circle_press_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'circle_press.png'))
		self.show_image_pc = False
		self.show_fog_pc = True
		self.pc_name_input_field_rect = pygame.Rect(241*scaling_factor[0]+self.tp_board_img.get_size()[0]+30,
											361*scaling_factor[1],96*scaling_factor[0],26*scaling_factor[1])
		self.pc_input_field_active = False
		self.name_3 = '|'
		self.text_cord_4 = (245*scaling_factor[0]+self.tp_board_img.get_size()[0]+30,
							367*scaling_factor[1])
		self.circle_rect1 = pygame.Rect(735*scaling_factor[0], 394*scaling_factor[1],
										self.circle_img.get_size()[0], self.circle_img.get_size()[1])
		self.rect_around_circle1 = pygame.Rect(730*scaling_factor[0], 389*scaling_factor[1],
										self.circle_img.get_size()[0]+10*self.scaling_factor[0], 
										self.circle_img.get_size()[1]+10*self.scaling_factor[1])
		self.circle_rect2 = pygame.Rect(735*scaling_factor[0], 419*scaling_factor[1],
										self.circle_img.get_size()[0], self.circle_img.get_size()[1])
		self.rect_around_circle2 = pygame.Rect(730*scaling_factor[0], 414*scaling_factor[1],
										self.circle_img.get_size()[0]+10*self.scaling_factor[0],
										self.circle_img.get_size()[1]+10*self.scaling_factor[0])
		self.circle_rect3 = pygame.Rect(735*scaling_factor[0], 444*scaling_factor[1],
										self.circle_img.get_size()[0], self.circle_img.get_size()[1])
		self.rect_around_circle3 = pygame.Rect(730*scaling_factor[0], 439*scaling_factor[1],
										self.circle_img.get_size()[0]+10*self.scaling_factor[0], 
										self.circle_img.get_size()[1]+10*self.scaling_factor[1])
		self.circle1_activ = False
		self.circle2_activ = False
		self.circle3_activ = False

		self.left_triangle_cord_3 = (round(self.pcb_x+83*self.scaling_factor[0]),round(491*scaling_factor[1]))
		self.right_triangle_cord_3 = (round(self.pcb_x+218*self.scaling_factor[0]),round(491*scaling_factor[1]))
		self.left_triangle_area_3, self.right_triangle_area_3 = self._calculate_triangle_area(self.left_triangle_cord_3,
												self.left_triangle_img, self.right_triangle_cord_3, self.right_triangle_img)								
		self.area_around_left_triangles_3 = pygame.Rect(self.pcb_x+78*self.scaling_factor[0],481*scaling_factor[1],
												32*scaling_factor[0],50*scaling_factor[1])
		self.area_around_right_triangles_3 = pygame.Rect(self.pcb_x+210*self.scaling_factor[0],
												481*scaling_factor[1], 32*scaling_factor[0],50*scaling_factor[1])
		self.side_selection_cord_2 = ((self.pcb_x + self.pc_board_img.get_size()[0]//2) - self.white_black_img.get_size()[0]//2,
										480*self.scaling_factor[1])
		self.side_selection_2 = True
		self.show_left_triangle_3 = False
		self.show_right_triangle_3 = False
		# =======================================================================
		# Side selection
		self.side_selection_cord_1 = ((self.tpb_x + self.tp_board_img.get_size()[0]//2) - self.white_black_img.get_size()[0]//2,
										480*self.scaling_factor[1])
		self.left_triangle_cord_2 = (round(293*scaling_factor[0]),round(491*scaling_factor[1]))
		self.right_triangle_cord_2 = (round(428*scaling_factor[0]),round(491*scaling_factor[1]))
		self.left_triangle_area_2, self.right_triangle_area_2 = self._calculate_triangle_area(self.left_triangle_cord_2,
												self.left_triangle_img, self.right_triangle_cord_2, self.right_triangle_img)								
		self.area_around_left_triangles_2 = pygame.Rect(288*scaling_factor[0],481*scaling_factor[1],
												32*scaling_factor[0],50*scaling_factor[1])
		self.area_around_right_triangles_2 = pygame.Rect(420*scaling_factor[0],481*scaling_factor[1],
												32*scaling_factor[0],50*scaling_factor[1])
		self.show_left_triangle_2 = False
		self.show_right_triangle_2 = False
		self.side_selection = True
		# =======================================================================

		# Button imgs, rect, cords
		self.play_button = Interface.transfor_scale(self, 
								pygame.image.load(PATH_TO_INTERFACE+'small_play.png'))
		self.play_button_press = Interface.transfor_scale(self, 
								pygame.image.load(PATH_TO_INTERFACE+'small_play_press.png'))
		self.play_button_rect = pygame.Rect(820*scaling_factor[0], 700*scaling_factor[1],
								self.play_button.get_size()[0], self.play_button.get_size()[1])
		self.play_button_press_rect = pygame.Rect(820*scaling_factor[0], 700*scaling_factor[1],
								self.play_button.get_size()[0]-4, self.play_button.get_size()[1]-8)

		self.back_button = Interface.transfor_scale(self, 
								pygame.image.load(PATH_TO_INTERFACE+'back.png'))
		self.small_fog_img = Interface.transfor_scale(self, pygame.image.load(PATH_TO_INTERFACE+'small_fog.png'))
		self.back_button_press = Interface.transfor_scale(self, 
								pygame.image.load(PATH_TO_INTERFACE+'back_press.png'))
		self.back_button_rect = pygame.Rect(57*scaling_factor[0], 700*scaling_factor[1],
								self.back_button.get_size()[0], self.back_button.get_size()[1])
		self.back_button_press_rect = pygame.Rect(57*scaling_factor[0], 700*scaling_factor[1],
								self.back_button_press.get_size()[0]-4, self.back_button_press.get_size()[1]-8)
		self.show_button1 = False
		self.show_button2 = False

	def draw_tp_board(self, background):
		if not self.show_image:
			if self.show_fog:
				background.blit(self.tp_board_img, (self.tpb_x, self.tpb_y))
				background.blit(self.fog_img, (self.tpb_x+(10*self.scaling_factor[0]), self.tpb_y+(10*self.scaling_factor[1])))
			else:
				background.blit(self.tp_board_img, (self.tpb_x, self.tpb_y))
		else:
			background.blit(self.tp_board_press_img, (self.tpb_x, self.tpb_y))
			pygame.draw.rect(background, (223,220,220), self.name_input_field_1_rect, 3)
			pygame.draw.rect(background, (223,220,220), self.name_input_field_2_rect, 3)
			pygame.draw.rect(background, (223,220,220), self.field_from_timer, 3)
			if not self.show_left_triangle_1:
				background.blit(self.left_triangle_img, self.left_triangle_cord_1)
			else:
				background.blit(self.left_triangle_press_img, self.left_triangle_cord_1)
			if not self.show_right_triangle_1:
				background.blit(self.right_triangle_img, self.right_triangle_cord_1)
			else:
				background.blit(self.right_triangle_press_img, self.right_triangle_cord_1)

			if not self.show_left_triangle_2:
				background.blit(self.left_triangle_img, self.left_triangle_cord_2)
			else:
				background.blit(self.left_triangle_press_img, self.left_triangle_cord_2)
			if not self.show_right_triangle_2:
				background.blit(self.right_triangle_img, self.right_triangle_cord_2)
			else:
				background.blit(self.right_triangle_press_img, self.right_triangle_cord_2)			
			# pygame.draw.polygon(background, (255,0,0), self.left_triangle_area_1, 2)
			# pygame.draw.polygon(background, (255,0,0), self.right_triangle_area_1, 2)
			# pygame.draw.rect(background, (223,220,220), self.area_around_left_triangles_1, 2)
			# pygame.draw.rect(background, (223,220,220), self.area_around_right_triangles_1, 2)
			if self.side_selection:
				background.blit(self.white_black_img, self.side_selection_cord_1)
			else:
				background.blit(self.black_white_img, self.side_selection_cord_1)
			
			if self.input_field_1_active:
				text = self._text_update(self.name_1)
				self.text_width = text.get_size()[0]
				background.blit(text, (self.text_cord_1))
				text = self.font.render(self.name_2[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_2))
				if self.timer != '|':
					text = self.font.render(self.timer[:-1], 1, InterfacePlay.color)
					background.blit(text, (self.text_cord_3))
				else:
					text = self.font.render(self.default_timer[self.current_state], 1, (37, 36, 56))
					background.blit(text, (self.text_cord_3[0]+5-text.get_size()[0]//2, self.text_cord_3[1]))
				self.stick_counter += 1
			elif self.input_field_2_active:
				text = self._text_update(self.name_2)
				self.text_width = text.get_size()[0]
				background.blit(text, (self.text_cord_2))
				text = self.font.render(self.name_1[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_1))
				if self.timer != '|':
					text = self.font.render(self.timer[:-1], 1, InterfacePlay.color)
					background.blit(text, (self.text_cord_3))
				else:
					text = self.font.render(self.default_timer[self.current_state], 1, (37, 36, 56))
					background.blit(text, (self.text_cord_3[0]+5-text.get_size()[0]//2, self.text_cord_3[1]))
				self.stick_counter += 1
			elif self.input_field_3_active:
				text = self._text_update_middle(self.timer)
				self.text_width = text.get_size()[0]
				background.blit(text, (self.text_cord_3))
				text = self.font.render(self.name_1[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_1))
				text = self.font.render(self.name_2[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_2))
				self.stick_counter += 1
			else:
				text = self.font.render(self.name_1[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_1))
				text = self.font.render(self.name_2[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_2))
				if self.timer != '|':
					text = self.font.render(self.timer[:-1], 1, InterfacePlay.color)
					background.blit(text, (self.text_cord_3))
				else:
					text = self.font.render(self.default_timer[self.current_state], 1, InterfacePlay.color)
					background.blit(text, ((self.text_cord_3[0]+5-text.get_size()[0]//2), self.text_cord_3[1]))

	def draw_pc_board(self, background):
		if not self.show_image_pc:
			if self.show_fog_pc:
				background.blit(self.pc_board_img, (self.pcb_x, self.pcb_y))
				background.blit(self.fog_img, (self.pcb_x+(10*self.scaling_factor[0]), self.pcb_y+(10*self.scaling_factor[1])))
			else:
				background.blit(self.pc_board_img, (self.pcb_x, self.pcb_y))
		else:
			background.blit(self.pc_board_press_img, (self.pcb_x, self.pcb_y))	
			# background.blit(self.left_triangle_img, self.left_triangle_cord_3)
			# background.blit(self.right_triangle_img, self.right_triangle_cord_3)
			# pygame.draw.rect(background, (223,220,220), self.area_around_left_triangles_3, 2)
			# pygame.draw.rect(background, (223,220,220), self.area_around_right_triangles_3, 2)
			# background.blit(self.white_black_img, self.side_selection_cord_2)
			
			if self.circle1_activ:
				background.blit(self.circle_press_img, (self.circle_rect1[0], self.circle_rect1[1]))	
			else:
				background.blit(self.circle_img, (self.circle_rect1[0], self.circle_rect1[1]))
			if self.circle2_activ:
				background.blit(self.circle_press_img, (self.circle_rect2[0], self.circle_rect2[1]))
			else:
				background.blit(self.circle_img, (self.circle_rect2[0], self.circle_rect2[1]))
			if self.circle3_activ:
				background.blit(self.circle_press_img, (self.circle_rect3[0], self.circle_rect3[1]))
			else:
				background.blit(self.circle_img, (self.circle_rect3[0], self.circle_rect3[1]))
			
			if not self.show_left_triangle_3:
				background.blit(self.left_triangle_img, self.left_triangle_cord_3)
			else:
				background.blit(self.left_triangle_press_img, self.left_triangle_cord_3)
			if not self.show_right_triangle_3:
				background.blit(self.right_triangle_img, self.right_triangle_cord_3)
			else:
				background.blit(self.right_triangle_press_img, self.right_triangle_cord_3)

			if self.side_selection_2:
				background.blit(self.white_black_img, self.side_selection_cord_2)
			else:
				background.blit(self.black_white_img, self.side_selection_cord_2)

			if self.pc_input_field_active:
				text = self._text_update(self.name_3)
				self.text_width = text.get_size()[0]
				background.blit(text, (self.text_cord_4))
				self.stick_counter += 1
			else:
				text = self.font.render(self.name_3[:-1], 1, InterfacePlay.color)
				background.blit(text, (self.text_cord_4))

	def draw_button(self, background):
		if self.show_image or self.show_image_pc:
			if self.show_button1:
				background.blit(self.play_button_press, (self.play_button_press_rect[0], self.play_button_press_rect[1]))
			else:
				background.blit(self.play_button, (self.play_button_rect[0], self.play_button_rect[1]))
		else:
			background.blit(self.play_button, (self.play_button_rect[0], self.play_button_rect[1]))
			background.blit(self.small_fog_img, (self.play_button_rect[0]+(8.5*self.scaling_factor[0]),
												 self.play_button_rect[1]+(8.7*self.scaling_factor[1])))

		if self.show_button2:
			background.blit(self.back_button_press, (self.back_button_press_rect[0], self.back_button_press_rect[1]))
		else:
			background.blit(self.back_button, (self.back_button_rect[0], self.back_button_rect[1]))

	def isOver(self, mouse):
		if not self.show_image:
			if self.tp_board_rect.collidepoint(mouse):
				return True
			#return False
		else:
			if self.name_input_field_1_rect.collidepoint(mouse):
				self.input_field_1_active = not self.input_field_1_active 
				self.input_field_2_active = False
				self.input_field_3_active = False
				self.stick_counter = 0
				print ('left field click')
			elif self.name_input_field_2_rect.collidepoint(mouse):
				self.input_field_2_active = not self.input_field_2_active
				self.input_field_1_active = False
				self.input_field_3_active = False
				self.stick_counter = 0
				print ('right field click')
			elif self.triangle_left_is_over(mouse, self.area_around_left_triangles_1,
												self.left_triangle_area_1) == 1:
				self.current_state -= 1
				if self.current_state < 0:
					self.current_state = len(self.default_timer)-1
				self.timer = '|'
				self.input_field_3_active = False
				self.input_field_2_active = False
				self.input_field_1_active = False
				self.text_cord_3 = [(self.field_from_timer[0]+self.field_from_timer[2]//2)-4, self.field_from_timer[1]+7]
				print ('click left triangle 1')
			elif self.triangle_right_is_over(mouse, self.area_around_right_triangles_1,
												self.right_triangle_area_1) == 1:
				self.current_state += 1
				self.current_state = self.current_state%len(self.default_timer)
				self.timer = '|'
				self.input_field_3_active = False
				self.input_field_2_active = False
				self.input_field_1_active = False
				self.text_cord_3 = [(self.field_from_timer[0]+self.field_from_timer[2]//2)-4, self.field_from_timer[1]+7]
				print ('click right triangle 1')
			elif (self.triangle_left_is_over(mouse, self.area_around_left_triangles_1, self.left_triangle_area_1) or
							 self.triangle_right_is_over(mouse, self.area_around_right_triangles_1, self.right_triangle_area_1) == 2):
				print ('click in area around triangle first line')
			elif (self.triangle_left_is_over(mouse, self.area_around_left_triangles_2, self.left_triangle_area_2) == 1 or
							 self.triangle_right_is_over(mouse, self.area_around_right_triangles_2, self.right_triangle_area_2 )== 1):
				self.side_selection = not self.side_selection
				self.input_field_3_active = False
				self.input_field_2_active = False
				self.input_field_1_active = False
				print ('click left or right triangle 2')
			elif (self.triangle_left_is_over(mouse, self.area_around_left_triangles_2, self.left_triangle_area_2) or
							 self.triangle_right_is_over(mouse, self.area_around_right_triangles_2, self.right_triangle_area_2) == 2):
				print ('click in area around triangle second line')
			elif self.field_from_timer.collidepoint(mouse):
				self.input_field_3_active = not self.input_field_3_active
				self.input_field_1_active = False
				self.input_field_2_active = False
				self.stick_counter = 0
			elif self.tp_board_press_rect.collidepoint(mouse):
				#self.text_cord_3 = [(self.field_from_timer[0]+self.field_from_timer[2]//2)-4, self.field_from_timer[1]+7]
				return True
			#return False

	def pcb_isOver(self, mouse):
		if not self.show_image_pc:
			if self.pc_board_rect.collidepoint(mouse):
				return True
			#return False
		else:
			if self.pc_name_input_field_rect.collidepoint(mouse):
				self.pc_input_field_active = not self.pc_input_field_active 
				self.stick_counter = 0
			elif self.rect_around_circle1.collidepoint(mouse):
				if self.circle_rect1.collidepoint(mouse):
					self.circle1_activ = not self.circle1_activ
					self.circle2_activ = False
					self.circle3_activ = False
					self.pc_input_field_active = False
			elif self.rect_around_circle2.collidepoint(mouse):
				if self.circle_rect2.collidepoint(mouse):
					self.circle2_activ = not self.circle2_activ
					self.circle1_activ = False
					self.circle3_activ = False
					self.pc_input_field_active = False
			elif self.rect_around_circle3.collidepoint(mouse):
				if self.circle_rect3.collidepoint(mouse):
					self.circle3_activ = not self.circle3_activ
					self.circle1_activ = False
					self.circle2_activ = False
					self.pc_input_field_active = False
			elif (self.triangle_left_is_over(mouse, self.area_around_left_triangles_3,self.left_triangle_area_3) == 1 or
							 self.triangle_right_is_over(mouse, self.area_around_right_triangles_3, self.right_triangle_area_3 )== 1):
				self.side_selection_2 = not self.side_selection_2
				self.pc_input_field_active = False
				print ('click left or right triangle in pc board')
			elif (self.triangle_left_is_over(mouse, self.area_around_left_triangles_3, self.left_triangle_area_3) or
							 self.triangle_right_is_over(mouse, self.area_around_right_triangles_3, self.right_triangle_area_3) == 2):
				print ('click in area around triangle in pc board')
			elif self.pc_board_press_rect.collidepoint(mouse):
				return True
			#return False

	def button_isOver(self, mouse):
		if self.play_button_rect.collidepoint(mouse):
			if self.show_image or self.show_image_pc:
				return 1
		elif self.back_button_rect.collidepoint(mouse):
			return 2	
		else:
			return 0

	def triangle_left_is_over(self, mouse, area_around_left_triangles, left_triangle_area):
		if area_around_left_triangles.collidepoint(mouse):
			dot1, dot2, dot3 = left_triangle_area
			s = self._area(*dot1, *dot2, *dot3)
			s1 = self._area(*mouse, *dot2, *dot3)
			s2 = self._area(*dot1, *mouse, *dot3)
			s3 = self._area(*dot1, *dot2, *mouse)
			if int(s) == int(s1+s2+s3):
				return 1
			return 2 
		return 0

	def triangle_right_is_over(self, mouse, area_around_right_triangles, right_triangle_area):
		if area_around_right_triangles.collidepoint(mouse):
			dot1, dot2, dot3 = right_triangle_area
			s = self._area(*dot1, *dot2, *dot3)
			s1 = self._area(*mouse, *dot2, *dot3)
			s2 = self._area(*dot1, *mouse, *dot3)
			s3 = self._area(*dot1, *dot2, *mouse)
			if int(s) == int(s1+s2+s3):
				return 1
			return 2
		return 0

	def drop_cords(self):
		self.text_cord_3 = [(self.field_from_timer[0]+self.field_from_timer[2]//2)-4, self.field_from_timer[1]+7]

	def create_info_package(self):
		if self.show_image:
			name1 = 'Player 1' if self.name_1[:-1].strip() == '' else self.name_1[:-1].strip()
			name2 = 'Player 2' if self.name_2[:-1].strip() == '' else self.name_2[:-1].strip()

			if self.timer[:-1] == '':
				if self.current_state == 0:
					timer = False
				else:
					t = self.default_timer[self.current_state]
					timer = float(t[:-1])
			else:
				timer = float(self.timer[:-1])

			side = self.side_selection # if True p1 - white, p2 - black
			return {
					'game mode': 'pp',
					'name1': name1,
					'nmae2': name2,
					'timer': timer,
					'side': side
					}
		if self.show_image_pc:
			name1 = 'Player' if self.name_3[:-1].strip() == '' else self.name_3[:-1].strip()
			name2 = 'Bot Easy'
			if self.circle1_activ:
				name2 = 'Bot Easy'
			if self.circle2_activ:
				name2 = 'Bot Medium'
			if self.circle3_activ:
				name2 = 'Bot Hard'
			side = self.side_selection_2 # if True p1 - white, p2 - black
			return {
					'game mode': 'pc',
					'name1': name1,
					'name2': name2,
					'timer': None,
					'side': side
					}

	def _text_update(self, name):
		if self.stick_counter <= 40:
			return self.font.render(name, 1, (37, 36, 56))
		elif 80 >= self.stick_counter > 40:
			return self.font.render(name[:-1], 1, (37, 36, 56))
		elif self.stick_counter > 80:
			self.stick_counter = 0
			return self.font.render(name, 1, (37, 36, 56))

	def _text_update_middle(self, timer):
		if self.stick_counter <= 40:
			return self.font.render(timer+' m', 1, (37, 36, 56))
		elif 80 >= self.stick_counter > 40:
			return self.font.render(timer[:-1]+' m', 1, (37, 36, 56))
		elif self.stick_counter > 80:
			self.stick_counter = 0
			return self.font.render(timer+' m', 1, (37, 36, 56))		

	def _calculate_triangle_area(self, left_triangle_cord, left_triangle_img,
								right_triangle_cord, right_triangle_img):
		l_dot1 = (left_triangle_cord[0],left_triangle_cord[1]+left_triangle_img.get_size()[1]//2)
		l_dot2 = (left_triangle_cord[0]+left_triangle_img.get_size()[0], left_triangle_cord[1])
		l_dot3 = (left_triangle_cord[0]+left_triangle_img.get_size()[0],
				 left_triangle_cord[1]+left_triangle_img.get_size()[1])

		r_dot1 = (right_triangle_cord[0], right_triangle_cord[1])
		r_dot2 = (right_triangle_cord[0]+right_triangle_img.get_size()[0],
				 right_triangle_cord[1]+right_triangle_img.get_size()[1]//2)
		r_dot3 = (right_triangle_cord[0], right_triangle_cord[1]+right_triangle_img.get_size()[1])
		return (l_dot3, l_dot2, l_dot1), (r_dot1, r_dot2, r_dot3)

	def _area(self, x1, y1, x2, y2, x3, y3): 
		return abs((x1 * (y2 - y3) + x2 * (y3 - y1)  
					+ x3 * (y1 - y2)) / 2.0)


class Button(Interface):
	def __init__(self, scaling_factor, image, image_press, x, y):
		super().__init__(scaling_factor)
		self.cord = (x*scaling_factor[0], y*scaling_factor[1])
		self.image = Interface.transfor_scale(self, pygame.image.load(image))
		self.image_press = Interface.transfor_scale(self,pygame.image.load(image_press))
		self.button_rect = pygame.Rect((x*scaling_factor[0],y*scaling_factor[1],self.image.get_size()[0],self.image.get_size()[1]))
		self.show_image = 0

	def draw(self, background):
		if not self.show_image:
			background.blit(self.image, self.cord)
		else:
			background.blit(self.image_press, self.cord)

	def isOver(self, mouse):
		if self.button_rect.collidepoint(mouse):
			return True
		return False

class Timer(Interface):
	def __init__(self, scaling_factor, timer, pos1, pos2, plate_img, background):
		super().__init__(scaling_factor)
		self.timer_1, self.timer_2 = timer*60, timer*60
		self.timestamp = time.time()
		self.plate_img = plate_img
		self.font = pygame.font.Font('KumbhSans-Regular.ttf', round(15*(scaling_factor[0]+scaling_factor[1])/2))
		self.pos_1 = pos1
		self.pos_2 = pos2

		# add timers on screen 
		self.draw_timer(background)

	def update_timer(self, background, player, side):
		print (self.timestamp - time.time())
		if time.time() - self.timestamp >= 1:
			pos_1, pos_2 = (self.pos_1, self.pos_2) if side else (self.pos_2, self.pos_1)
			if player:
				self.timer_1 -= 1
				text = self.font.render(str(int(self.timer_1//60))+':'+str(int(self.timer_1%60)), False, (0, 0, 0))
				background.blit(self.plate_img, pos_1)
				background.blit(text, (pos_1[0]+self.plate_img.get_size()[0]/2-text.get_size()[0]/2,
										pos_1[1]+self.plate_img.get_size()[1]/2-text.get_size()[1]/2.5))
			else:
				self.timer_2 -= 1
				text = self.font.render(str(int(self.timer_2//60))+':'+str(int(self.timer_2%60)), False, (0, 0, 0))
				background.blit(self.plate_img, pos_2)
				background.blit(text, (pos_2[0]+self.plate_img.get_size()[0]/2-text.get_size()[0]/2,
										pos_2[1]+self.plate_img.get_size()[1]/2-text.get_size()[1]/2.5))
			self.timestamp = time.time()

	def draw_timer(self, background, side=True):
		pos_1, pos_2 = (self.pos_1, self.pos_2) if side else (self.pos_2, self.pos_1)
		text = self.font.render(str(int(self.timer_1//60))+':'+str(int(self.timer_1%60)), False, (0, 0, 0))
		background.blit(self.plate_img, pos_1)
		background.blit(text, (pos_1[0]+self.plate_img.get_size()[0]/2-text.get_size()[0]/2,
								pos_1[1]+self.plate_img.get_size()[1]/2-text.get_size()[1]/2.5))

		text = self.font.render(str(int(self.timer_2//60))+':'+str(int(self.timer_2%60)), False, (0, 0, 0))
		background.blit(self.plate_img, pos_2)
		background.blit(text, (pos_2[0]+self.plate_img.get_size()[0]/2-text.get_size()[0]/2,
								pos_2[1]+self.plate_img.get_size()[1]/2-text.get_size()[1]/2.5))

