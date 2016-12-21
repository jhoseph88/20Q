#!/usr/bin/python
from extensions import db
import pdb

class QNode:
	"""A question differentiating two animals and two child questions"""
	def __init__(self, data=None, leftchild=None, rightchild=None):
		# leaf nodes will have animal attribute
		self.data = data
		self.left_QNode = leftchild
		self.right_QNode = rightchild

	def ask_question(self):
		"""Returns \'y\' or \'n\' depending on user\'s answer to question."""
		if self.data:
			return raw_input(self.data + ' ')[0:1].lower()
		else:
			return None

	def get_data(self):
		"""Returns string of data for a given QNode."""
		return self.data

	def is_leaf_node(self):
		"""Returns boolean indicating whether a given QNode is a leaf node (' +\
		'has no children)."""
		return self.left_QNode == None and self.right_QNode == None

	def get_left_child(self):
		"""Returns left child of a node"""
		return self.left_QNode

	def get_right_child(self):
		"""Returns right child of a node."""
		return self.right_QNode

def load_tree_preorder(current_data):
	"""Uses a preorder tree traversal to build out the phylogenetic tree ' +\
	'from the database."""
	if current_data == None:
		return
	cur = db.cursor()
	sql_cmd = 'SELECT * FROM Tree WHERE data = \'' + current_data + '\''
	cur.execute(sql_cmd)
	result = cur.fetchall()
	# If called when tree is empty, just return (for starting condition)
	if len(result) == 0:
		return
	else:
		result = result[0]
	question = result['data']
	lchild = result['leftchild']
	rchild = result['rightchild']
	# Create new node from data retrieved on current_animal from the database
	current_node = QNode(data=current_data, leftchild=lchild, rightchild=rchild)
	current_node.left_QNode = load_tree_preorder(lchild)
	current_node.right_QNode = load_tree_preorder(rchild)
	return current_node

def add_animal_to_db(prev_question):
	"""Adds animal to database as a leaf node (a node with no children)."""
	new_animal = raw_input('Okay. I give up ... What was it (Please DO NOT use ' +
						   'any articles in the name of your animal.)? ').lower()
	classifier_question = raw_input('I see ... Well then what yes or no ' +
								    'question would distinguish a ' + 
									new_animal + ' from another animal? ')
	classifier_answer = raw_input('And what would the answer to that question' +
								  ' be if you were ' + 'thinking of a ' + 
								  new_animal + '? ')[0:1].lower()
	# Add to left of current if answer to question is false; right if true
	is_right_child = False
	if classifier_answer == 'y':
		is_right_child = True
	cur = db.cursor()
	# Add classifier question to the database
	sql_cmd = 'INSERT INTO Tree (data, leftchild, rightchild) VALUES (\'' + \
			  classifier_question + '\',' + ' NULL, NULL)'
	cur.execute(sql_cmd)
	# Insert new animal into tree as a leaf node
	sql_cmd = 'INSERT INTO Tree (data, leftchild, rightchild) VALUES (\'' + \
			  new_animal + '\', NULL, NULL)'
	cur.execute(sql_cmd)
	# If answer to classifier question was yes, add animal as right child of
	# question. If answer was no, add animal as left child of question.
	child_position = 'leftchild'
	if is_right_child:
		child_position = 'rightchild'
	sql_cmd = 'UPDATE Tree SET ' + child_position + '=\'' + new_animal + \
		  	  '\' WHERE data=' + '\'' + classifier_question + '\''
	cur.execute(sql_cmd)
	# Set new question as left child of previous question
	sql_cmd = 'UPDATE Tree SET leftchild =\'' + classifier_question + \
		  	  '\' WHERE data=' + '\'' + prev_question + '\''
	cur.execute(sql_cmd)
	"""Ask user if (s)he wants to play again"""
	play_again = raw_input('Want to play again? ' )[0:1].lower()
	# Load the updated database if user wants to play again
	if play_again == 'y':
		print('Okay. I\'m going to restart the game now...')
	else:
		print('Fair enough. I hope to play again with you soon! ' +
			  'Exiting...')
		exit(0)
	return classifier_question

def play_game():
	"""Builds classification tree so loops infinitely until receives SIGINT"""
	# Generate tree using root question for root node of tree
	root_question = 'Does it have wings?'
	current_node = load_tree_preorder(root_question)
	# Previous question will be stored and updated for tree building. When a new
	# question is added, it must be appended as a child of its parent question
	prev_question = ''
	while True:
		# If no value in tree for current_node, must add a question to the tree
		# and the user's animal as a child node of that question. Then, restart.
		if current_node == None:
			prev_question = add_animal_to_db(prev_question)
			current_node = load_tree_preorder(root_question)
			continue
		# If node is a leaf node, make a guess.
		if current_node.is_leaf_node():
			guess_veracity = raw_input('Is it a ' + current_node.get_data() + \
									   '? ')[0:1].lower()
			# If guess was correct, celebrate
			if guess_veracity == 'y':
				print('Fuck yes! I got it!')
				# Ask if user wants to play again
				play_again = raw_input('Want to play again? ')[0:1].lower()
				# If answer is yes, rebuild tree to update it and restart game
				if play_again == 'y':
					print('Okay. I\'m going to restart the game now...')
					current_node = load_tree_preorder(root_question)
					continue
				else:
					print('Fair enough. I hope to play again with you soon! ' +
						  'Exiting...')
					exit(0)
			# Otherwise, add a new node to tree based on user input
			else:
				# Add new question and new animal as a child of that question
				prev_question = add_animal_to_db(prev_question)
				current_node = load_tree_preorder(root_question)
				continue
		question_answer = current_node.ask_question()
		# Traverse right if answer is yes; left if answer is no
		if question_answer == 'y':
			current_node = current_node.get_right_child()
		else:
			current_node = current_node.get_left_child()

if __name__ == '__main__':
	# Start game
	play_game()