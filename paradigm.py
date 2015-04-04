import yaml
import sys

class paradigm:
	
	def __init__(self, views, focus):
		self.eyes = []
		self.gaze = focus
		try:
			with open(views, 'r') as jar:
			
				for eye in yaml.safe_load_all(jar):
					self.eyes.append(eye)
			if len(self.eyes) == 0:
				sys.stderr.write("Check input file\n")
			if self.gaze > len(self.eyes) - 1:
				self.gaze = 0
				sys.stderr.write("Focus parameter out of range: Set automatically to Zero\n")

		except IOError as inst:
			sys.stderr.write("Perspective file not found\n")
	

		
	def new_eyes(self, views, gaze = 0):
		self.__init__(views, gaze)
	


	def add_eyes(self, views):
		try:
			with open(views, 'r') as f:
				for view in yaml.safe_load_all(f):
					self.eyes.extend(view)
		except IOError as inst:
			sys.stderr.write("Perspective file not found\n")

		
	def shift_focus(self, n_dir):
		if n_dir > len(self.views) - 1:
			sys.stderr.write("Invalid view shift operation\n")		
		else:
			self.gaze = n_dir

	def focus(self):
		
		return self.eyes[self.gaze]

	def jar(self):
		for eye in self.eyes:
			yield eye

