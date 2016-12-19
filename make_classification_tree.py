#!/usr/bin/python
from extensions import db
import pdb

class QNode:
	'A question differentiating two animals and pointers to two child animals'
	def __init__(self, q=None, animal=None, leftchild=None, rightchild=None):
		self.question = q
		# leaf nodes will have animal attribute
		self.animal = animal
		self.left_QNode = None
		self.right_QNode = None

	def ask_question(self):
		'Returns \'y\' or \'n\' depending on user\'s answer to question.'
		if self.question:
			return raw_input(self.question)[0:1].lower()
		else:
			return None

	def set_question(self, q):
		'Sets classifier question for an animal.'
		cur = db.cursor()
		sql_cmd = 'UPDATE Tree SET question=\'' + q + '\' WHERE animal=' +\
				  '\'' + self.animal + '\''
		self.question = q

	def set_left_child(self, new_node):
		'Sets a new node as the left child of a given QNode.'
		# Insert new animal into Tree as a leaf node.
		cur = db.cursor()
		sql_cmd = 'INSERT INTO Tree VALUES (\'' + new_node + '\', NULL, NULL)'
		cur.execute(sql_cmd)
		# Make left child of current node new node just created and inserted.
		sql_cmd = 'UPDATE Tree SET leftchild=\'' + new_node+ ' WHERE animal=' +\
				  '\'' + self.animal + '\''
		cur.execute(sql_cmd)
		# Set the current node's left child in memory.
		self.left_QNode = new_node

	def set_right_child(self, new_node):
		'Sets a new node as the right child of a given QNode.'
		# Insert new animal into Tree as a leaf node.
		cur = db.cursor()
		sql_cmd = 'INSERT INTO Tree VALUES (\'' + new_node + '\', NULL, NULL)'
		cur.execute(sql_cmd)
		# Make right child of current node new node just created and inserted.
		sql_cmd = 'UPDATE Tree SET rightchild=\'' + new_node+' WHERE animal=' +\
				  '\'' + self.animal + '\''
		cur.execute(sql_cmd)
		# Set the current node's left child in memory.
		self.right_QNode = new_node

	def get_left_child(self):
		'Returns left child of a given QNode.'
		return self.left_QNode

	def get_right_child(self):
		'Returns right child of a given QNode.'
		return self.right_QNode

	def get_animal(self):
		'Returns string of animal for a given QNode.'
		return self.animal

	def is_leaf_node(self):
		'Returns boolean indicating whether a given QNode is a leaf node (' + \
		'has no children).'
		return self.left_QNode == None and self.right_QNode == None

def load_tree_preorder(current_animal):
	'Uses a preorder tree traversal to build out the phylogenetic tree from ' +\
	'the database.'
	if current_animal == None:
		return
	cur = db.cursor()
	sql_cmd = 'SELECT * FROM Tree WHERE animal = \'' + current_animal + '\''
	cur.execute(sql_cmd)
	result = cur.fetchall()[0]
	question = result['question']
	leftchild_animal = result['leftchild']
	rightchild_animal = result['rightchild']
	# Create new node from data retrieved on current_animal from the database
	current_node = QNode(q=question, animal=current_animal, 
					   	 leftchild=leftchild_animal, 
					   	 rightchild=rightchild_animal)
	current_node.left_QNode = load_tree_preorder(leftchild_animal)
	current_node.right_QNode = load_tree_preorder(rightchild_animal)
	return current_node

def add_animal_to_db(animal, question, is_root, is_right_child, parent):
	'Adds animal to database as a leaf node (a node with no children).'
	cur = db.cursor()
	sql_cmd = 'SELECT * FROM Tree WHERE animal = ' + '\'' + animal + '\''
	cur.execute(sql_cmd)
	# Insert animal into the database if it doesn't already exist
	if len(cur.fetchall() ) == 0:
		# Insert NULL into the database if the 
		if question == None:
			sql_cmd = 'INSERT INTO Tree VALUES (\'' + animal + '\', NULL,' + \
			  	  	  'NULL, NULL)'
		else:
			sql_cmd = 'INSERT INTO Tree VALUES (\'' + animal + '\', \'' + \
					  question + '\', NULL, NULL)'
		cur.execute(sql_cmd)
		# If answer to classifier question was yes, add animal as right child
		# of parent. If answer was no, add animal as left child of parent.
		child_position = 'leftchild'
		if is_right_child:
			child_position = 'rightchild'
		# Don't add to parent if root.
		if not is_root:
			sql_cmd = 'UPDATE Tree SET ' + child_position + '=\'' + animal + \
			  	  	'\' WHERE animal=' + '\'' + parent + '\''
			cur.execute(sql_cmd)
	else:
		print('Animal with name ' + animal + ' already exists in database. ' +
			  'Exiting...')
		exit(1)

def build_tree(root):
	'Builds classification tree so loops infinitely until receives SIGINT'
	# Save root for future calls
	global_root = root
	current_node = root
	while True:
		# If node is a leaf node, make a guess.
		if current_node.is_leaf_node():
			guess_veracity = raw_input('Is it a ' + current_node.get_animal() +\
									   '? ')[0:1].lower()
			# If guess was correct, celebrate
			if guess_veracity == 'y':
				print('Fuck yes! I got it!')
				# Ask if user wants to play again
				play_again = raw_input('Want to play again? ')[0:1].lower()

				if play_again == 'y':
					print('Okay. I\'m going to restart the game now...')
					build_tree(global_root)
				else:
					print('Fair enough. I hope to play again with you soon! ' +
						  'Exiting...')
					exit(0)

			# Otherwise, add a new node to tree based on user input
			else:
				new_animal = raw_input('Okay. I give up ... What was it ' +
									   '(Please DO NOT use any articles in ' +
									   'the name of your animal.)? ').lower()
				classifier_question = raw_input('I see ... Well then what ' +
											'yes or no question would ' +
											'distinguish a ' + new_animal + 
											' from another animal? ' ) + ' '
				classifier_answer = raw_input('And what would the answer to ' +
										  	  'that question be if you were ' +
										 	  'thinking of a ' + new_animal + 
										 	  '? ')[0:1].lower()
				# Set the question of the current node to differentiate the new
				# new node from it.
				current_node.set_question(classifier_question)
				# Add to left of current if answer to classifier question is
				# false; right if true
				is_right_child = False
				if classifier_answer == 'y':
					is_right_child = True
				# Add the new animal as a leaf node
				add_animal_to_db(new_animal, classifier_question, False, 
								 is_right_child, current_node.animal)
				# Update database and exit 
				print('Okay, well I\'m gonna go update the classifier tree ' +
					  'now so I don\'t have to embarrass myself like I ' +
					  'just did with you...')
				play_again = raw_input('Want to play again? ' )[0:1].lower()
				# Load the updated database if user wants to play again.
				if play_again == 'y':
					print('Okay. I\'m going to restart the game now...')
					build_tree(load_tree_preorder(global_root.animal) )
				else:
					print('Fair enough. I hope to play again with you soon! ' +
						  'Exiting...')
					exit(0)
		question_answer = current_node.ask_question()
		# Traverse right if answer is yes; left if answer is no
		if question_answer == 'y':
			current_node = current_node.get_right_child()
		else:
			current_node = current_node.get_left_child()

if __name__ == '__main__':
	initial_question = 'Does it have legs? '
	initial_animal = 'bird'
	is_root = True
	is_right_child = False
	# Add bird as root node of tree, so pass in None for parent.
	cur = db.cursor()
	sql_cmd = 'SELECT * FROM Tree WHERE animal = \'bird\''
	cur.execute(sql_cmd)
	results = cur.fetchall()
	if len(results) == 0:
		add_animal_to_db(initial_animal, initial_question,
						 is_root, is_right_child, None)
	root = load_tree_preorder(initial_animal)
	build_tree(root)
