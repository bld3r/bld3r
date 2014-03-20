from __future__ import with_statement
import os
import webapp2
import jinja2
import hashlib
import hmac
import string
import random
import time
import datetime
import logging
import urllib
import urllib2
import mimetypes
import markdown2
import cgi
import re
import uuid
import json
#import struct
#import matplotlib # this breaks the dev tools
from fake_names import fake_names
#from pystltoolkit import stlparser
from do_not_copy import data
from urlparse import urlparse
from pybcrypt import bcrypt
from pyemailcheck import emailcheck
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api import mail
from google.appengine.api import images
from google.appengine.api import files
from google.appengine.api import urlfetch
from google.appengine.ext import deferred
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app
#########################################################
####################### Global Variables #######################
TRUSTED_USERS = ["piercet", "maxumx", "aoeu", "noob"]
URL_SAFE_CHARS = [
	"a","A","b","B","c","C","d","D","e","E","f","F","g","G","h","H","i","I",
	"j","J","k","K","l","L","m","M","n","N","o","O","p","P","q","Q","r","R",
	"s","S","t","T","u","U","v","V","w","W","x","X","y","Y","z","Z",
	"0","1","2","3","4","5","6","7","8","9","_","-"]
page_url = data.page_url()
URL_CHECK_HEADERS = {
	'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
	}
ALLOWED_IMAGE_EXTENTIONS = ['png','jpg','jpeg','bmp']
ALLOWED_ALTERNATE_FILE_EXTENTIONS = ['stl', 'scad']
MAX_FILE_SIZE_FOR_OBJECTS = 5242880
NUMBER_OF_MINUTES_BETWEEN_FRONT_PAGE_UPDATES = 15
mkd = markdown2.Markdown()
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(extensions=['jinja2.ext.with_'],
	loader = jinja2.FileSystemLoader(template_dir), 
	autoescape = True)
upload_url = blobstore.create_upload_url('/upload')
#########################################################
####################### Primary Class Objects #######################
class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))
		#Need to set expires to last longer than browser open

	def set_secure_cookie_with_expiration(self, name, val):
		cookie_val = make_secure_val(val)
		expiration_time = (datetime.datetime.now() + datetime.timedelta(weeks=2)).strftime('%a, %d %b %Y %H:%M:%S GMT')
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; expires=%s; Path=/' % (name, cookie_val, expiration_time)
			)		

	def read_secure_cookie(self, cookie_name):
		cookie_val = self.request.cookies.get(cookie_name)
		if cookie_val and check_secure_val(cookie_val):
			return cookie_val
		else:
			return None

	def check_cookie_return_val(self, cookie_name):
		cookie_val = self.request.cookies.get(cookie_name)

		if cookie_val and check_secure_val(cookie_val):
			val = cookie_val.split('|')[0]
			return val
		else:
			if cookie_val:
				self.logout()
			return None

	def return_user_if_cookie(self):
		id_hash = self.request.cookies.get('user_id')
		if id_hash:
			valid = check_secure_val(id_hash)
			if valid:
				user_id = int(check_secure_val(id_hash))
				user_var = return_thing_by_id(user_id, "Users")
				if user_var:
					return user_var
				else:
					logging.warning("User does not exist even though hash is correct, probably local server issues (deleteing a user, but not the cookie")
					return None
			else:
				self.logout()
				return None
		else:
			return None

	def return_has_cookie(self):
		cookie_list = []
		cookie_types = ['user_id', 'username', 'over18']
		for i in cookie_types:
			cookie_val = self.check_cookie_return_val(i)
			cookie_list.append(cookie_val)
		has_cookie = True
		for i in cookie_list:
			if i is None:
				has_cookie = None
				break
		return has_cookie

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))
		self.set_secure_cookie('username', str(user.username))
		self.set_secure_cookie('over18', str(user.over18))

	def login_and_remember(self, user):
		self.set_secure_cookie_with_expiration('user_id', str(user.key().id()))
		self.set_secure_cookie_with_expiration('username', str(user.username))
		self.set_secure_cookie_with_expiration('over18', str(user.over18))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
		self.response.headers.add_header('Set-Cookie', 'username=; Path=/')
		self.response.headers.add_header('Set-Cookie', 'over18=; Path=/')

	def inline_404(self):
		self.error(404)
		handle_404(self.request, self.response, 404)
class ObjectUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))
		#Need to set expires to last longer than browser open

	def set_secure_cookie_with_expiration(self, name, val):
		cookie_val = make_secure_val(val)
		expiration_time = (datetime.datetime.now() + datetime.timedelta(weeks=2)).strftime('%a, %d %b %Y %H:%M:%S GMT')
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; expires=%s; Path=/' % (name, cookie_val, expiration_time)
			)		

	def read_secure_cookie(self, cookie_name):
		cookie_val = self.request.cookies.get(cookie_name)
		if cookie_val and check_secure_val(cookie_val):
			return cookie_val
		else:
			return None

	def check_cookie_return_val(self, cookie_name):
		cookie_val = self.request.cookies.get(cookie_name)

		if cookie_val and check_secure_val(cookie_val):
			val = cookie_val.split('|')[0]
			return val
		else:
			self.logout()
			return None

	def return_user_if_cookie(self):
		id_hash = self.request.cookies.get('user_id')
		if id_hash:
			valid = check_secure_val(id_hash)
			if valid:
				user_id = int(check_secure_val(id_hash))
				user_var = return_thing_by_id(user_id, "Users")
				if user_var:
					return user_var
				else:
					logging.warning("User does not exist even though hash is correct, probably local server issues (deleteing a user, but not the cookie")
					return None
			else:
				self.logout()
				return None
		else:
			return None

	def return_has_cookie(self):
		cookie_list = []
		cookie_types = ['user_id', 'username', 'over18']
		for i in cookie_types:
			cookie_val = self.check_cookie_return_val(i)
			cookie_list.append(cookie_val)
		has_cookie = True
		for i in cookie_list:
			if i is None:
				has_cookie = None
				break
		return has_cookie

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))
		self.set_secure_cookie('username', str(user.username))
		self.set_secure_cookie('over18', str(user.over18))

	def login_and_remember(self, user):
		self.set_secure_cookie_with_expiration('user_id', str(user.key().id()))
		self.set_secure_cookie_with_expiration('username', str(user.username))
		self.set_secure_cookie_with_expiration('over18', str(user.over18))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
		self.response.headers.add_header('Set-Cookie', 'username=; Path=/')
		self.response.headers.add_header('Set-Cookie', 'over18=; Path=/')
#########################################################
def random_string_generator(size = random.randint(15, 20),
			chars = string.ascii_letters + string.digits):
	return ''.join(random.choice(chars) for x in range(size))
####################### DB Models #######################
# do not use functions as defaults
DB_TYPE_LIST = [
	"Users", 
	"Objects", 
	"Comments", 
	"Messages", 
	"UserBlob", 
	"ObjectBlob", 
	"WikiEntry"]
DAY_SCALE = 2 # 2 days
DAYS_TIL_DECLINE = 4 #also again below
class Users(db.Model):
	db_type			= db.StringProperty(required = True, default = "Users")
	username 		= db.StringProperty(required = True)
	username_lower 	= db.StringProperty()
	hashed_password = db.StringProperty(required = True)
	random_string 	= db.StringProperty()
	created 		= db.DateTimeProperty(auto_now_add = True)
	epoch			= db.FloatProperty()
	time_since 		= db.StringProperty() # this var should stay empty, and is generated only on page load, but never put to db.

	summary			= db.TextProperty(default = "")
	location		= db.StringProperty(default = "")
	printer			= db.StringProperty(default = "")
	slicer			= db.StringProperty(default = "")
	software		= db.StringProperty(default = "")

	no_infinite_scroll = db.BooleanProperty(default= False)

	# gamification
	rate_rep 		= db.IntegerProperty(default = 0)
	# rate_rep should be king. It works like this: 
	# it's the sum of all rates -3, so that a rate of 1=-2, 2=-1, 3=0, 4=1, 5=2
	obj_rep			= db.IntegerProperty(default = 0)
	com_rep			= db.IntegerProperty(default = 0)
	wiki_rep		= db.IntegerProperty(default = 0)
	awards			= db.StringListProperty()
	# awards list:
	#				'email' = confirmed email

	#prints
	to_print_list		= db.StringListProperty()
	has_printed_list	= db.StringListProperty()

	#friends
	follower_list		= db.StringListProperty()
	block_list 			= db.StringListProperty()
	blocked_by_list 	= db.StringListProperty()

	#abuse reporting
	## in progress
	been_flagged		= db.BooleanProperty(default = False)
	# flagsum here should be the sum of the length of both of the lists below
	flagsum 			= db.IntegerProperty(default = 0)
	#
	flagged_obj			= db.ListProperty(int)
	flagged_com 		= db.ListProperty(int)

	#notifications
	has_note 			= db.BooleanProperty(default = False)
	new_note_list		= db.StringListProperty()
	note_list_all		= db.StringListProperty()

	#exists?
	deleted 			= db.BooleanProperty(default = False)
	#over18?
	over18				= db.BooleanProperty(default = False)
	
	upvotes 			= db.IntegerProperty(default = 0)
	downvotes 			= db.IntegerProperty(default = 0)
	num_of_rates 		= db.IntegerProperty(default = 0)
	#objects 			= db.ListProperty(default = None)
	#comments 			= db.ListProperty(default = None)

	net_votes 			= db.IntegerProperty()
	user_email			= db.StringProperty()
	unconfirmed_email	= db.StringProperty()

	#photo
	main_img_link 		= db.StringProperty()
	main_img_filename 	= db.StringProperty()
	main_img_blobkey 	= blobstore.BlobReferenceProperty()

	# to be deleted 
	main_img_blob_key	= db.StringProperty()
	#

	imgs_on_others_objects = db.StringListProperty()


	@classmethod
	def by_id(cls, uid):
		logging.warning('DB Query User Login -- @classmethod by_id ')
		return cls.get_by_id(uid, parent = users_key())


	@classmethod
	def by_name(cls, name):
		#Users class only

		u = db.GqlQuery("SELECT * FROM  Users WHERE username = :1", name).get()
		logging.warning('DB Query User Login -- @classmethod by_name ')
		return u

	@classmethod
	def register(cls, name, pw, email = None):
		pw_hash = make_pw_hash(name, pw)
		return cls(parent = users_key,
					username = name,
					hashed_password = pw_hash,
					user_email = email)

	@classmethod
	def logsin(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.hashed_password):
			return u
		else:
			pass
class Objects(db.Model):
	db_type			= db.StringProperty(required = True, default = "Objects")
	title 			= db.StringProperty(required = True)
	uuid 			= db.StringProperty(default = None)
	author_id		= db.IntegerProperty() 					# no longer require to allow deletion
	author_name		= db.StringProperty()
	obj_type		= db.StringProperty(required = True) 	# 'upload', 'link', 'tor', 'learn', 'ask', or 'news'.

	created 		= db.DateTimeProperty(auto_now_add = True)
	epoch			= db.FloatProperty()
	time_since 		= db.StringProperty() # this var should stay empty, and is generated only on page load, but never put to db.

	most_recent_comment_epoch = db.FloatProperty(default=0.00)
	total_num_of_comments = db.IntegerProperty(default = 0)
	
	# someone else's work?
	original_creator	= db.StringProperty()

	# exists?
	deleted 			= db.BooleanProperty(default = False)
	under_review 		= db.BooleanProperty(default = False)

	# printable object?
	printable 			= db.BooleanProperty(default = False)

	# learn type object?
	learn 				= db.BooleanProperty(default = False)
	learn_subject 		= db.StringProperty()
	learn_skill			= db.StringProperty(default = None) # Beginner/Intermediate/Advanced

	# news type object?
	news 				= db.BooleanProperty(default = False)

	# type
	okay_for_kids		= db.BooleanProperty(default = True)
	nsfw				= db.BooleanProperty(default = False)
	food_related		= db.BooleanProperty(default = False)
	# for Uploaded Objects
	stl_file_link 		= db.StringProperty(default = None)
	stl_file_blob_key 	= blobstore.BlobReferenceProperty()
	stl_filename		= db.TextProperty()
	file_link_2			= db.StringProperty(default = None)
	file_blob_key_2		= blobstore.BlobReferenceProperty()
	file_blob_filename_2= db.TextProperty()
	file_link_3			= db.StringProperty(default = None)
	file_blob_key_3		= blobstore.BlobReferenceProperty()
	file_blob_filename_3= db.TextProperty()
	file_link_4			= db.StringProperty(default = None)
	file_blob_key_4		= blobstore.BlobReferenceProperty()
	file_blob_filename_4= db.TextProperty()
	file_link_5			= db.StringProperty(default = None)
	file_blob_key_5		= blobstore.BlobReferenceProperty()
	file_blob_filename_5= db.TextProperty()
	file_link_5			= db.StringProperty(default = None)
	file_blob_key_5		= blobstore.BlobReferenceProperty()
	file_blob_filename_5= db.TextProperty()
	file_link_6			= db.StringProperty(default = None)
	file_blob_key_6		= blobstore.BlobReferenceProperty()
	file_blob_filename_6= db.TextProperty()
	file_link_7			= db.StringProperty(default = None)
	file_blob_key_7		= blobstore.BlobReferenceProperty()
	file_blob_filename_7= db.TextProperty()
	file_link_8			= db.StringProperty(default = None)
	file_blob_key_8		= blobstore.BlobReferenceProperty()
	file_blob_filename_8= db.TextProperty()
	file_link_9			= db.StringProperty(default = None)
	file_blob_key_9		= blobstore.BlobReferenceProperty()
	file_blob_filename_9	= db.TextProperty()
	file_link_10			= db.StringProperty(default = None)
	file_blob_key_10		= blobstore.BlobReferenceProperty()
	file_blob_filename_10	= db.TextProperty()
	file_link_11			= db.StringProperty(default = None)
	file_blob_key_11		= blobstore.BlobReferenceProperty()
	file_blob_filename_11	= db.TextProperty()
	file_link_12			= db.StringProperty(default = None)
	file_blob_key_12		= blobstore.BlobReferenceProperty()
	file_blob_filename_12	= db.TextProperty()
	file_link_13			= db.StringProperty(default = None)
	file_blob_key_13		= blobstore.BlobReferenceProperty()
	file_blob_filename_13	= db.TextProperty()
	file_link_14			= db.StringProperty(default = None)
	file_blob_key_14		= blobstore.BlobReferenceProperty()
	file_blob_filename_14	= db.TextProperty()
	file_link_15			= db.StringProperty(default = None)
	file_blob_key_15		= blobstore.BlobReferenceProperty()
	file_blob_filename_15	= db.TextProperty()

	main_img_link 		= db.StringProperty(default = None)
	main_img_blob_key	= blobstore.BlobReferenceProperty()
	main_img_filename 	= db.TextProperty()

	img_link_2			= db.StringProperty(default = None)
	img_blob_key_2		= blobstore.BlobReferenceProperty()
	img_blob_filename_2 = db.TextProperty()

	img_link_3			= db.StringProperty(default = None)
	img_blob_key_3		= blobstore.BlobReferenceProperty()
	img_blob_filename_3 = db.TextProperty()

	img_link_4			= db.StringProperty(default = None)
	img_blob_key_4		= blobstore.BlobReferenceProperty()
	img_blob_filename_4 = db.TextProperty()

	img_link_5			= db.StringProperty(default = None)
	img_blob_key_5		= blobstore.BlobReferenceProperty()
	img_blob_filename_5 = db.TextProperty()

	visitor_img_list	= db.StringListProperty() # items take form ["user_id|username|img_url|blob_key"]

	licence				= db.StringProperty() # spelling: license (american) licence (rest of world)
	license 			= db.StringProperty()
	# for Link/Tor Objects
	obj_link			= db.StringProperty() 

	# optional
	description 			= db.TextProperty()
	markdown 				= db.TextProperty()
	
	# tags
	tags 					= db.StringListProperty()
	author_tags				= db.StringListProperty()
	public_tags				= db.StringListProperty()
	
	upvotes 				= db.IntegerProperty(default = 1)
	downvotes 				= db.IntegerProperty(default = 0)
	netvotes 				= db.IntegerProperty()
	hotness_var 			= db.FloatProperty()
	rating 					= db.FloatProperty()
	total_ratings 			= db.IntegerProperty()
	other_file1_link 		= db.StringProperty()
	other_img1_link 		= db.StringProperty()

	# voting section:
	##### keep
	global DAY_SCALE
	rank					= db.StringProperty()	
	votesum					= db.IntegerProperty(default = 1)
	#####
	#creation_order			= db.StringProperty(default=" ")
	#created_int				= db.IntegerProperty(default=0)
	num_user_when_created 	= db.IntegerProperty()
	
	# chached vote/rate/flag section:
	voter_list				= db.ListProperty(int)
	voter_vote				= db.StringListProperty()
	rater_list				= db.ListProperty(int)
	rater_rate				= db.StringListProperty()
	flagger_list			= db.ListProperty(int)
	flagger_flag			= db.StringListProperty()

	# rating section:
	been_rated 				= db.BooleanProperty(default=False)
	rate_avg				= db.FloatProperty(default = 0.0)
	##### keep
	ratesum					= db.IntegerProperty(default = 0)
	num_ratings				= db.IntegerProperty(default = 0)
	#####
	#creation_order_rate		= db.StringProperty(default=" ")
	#created_int_rate		= db.IntegerProperty(default=0)
	
	# flagging section:
	been_flagged 			= db.BooleanProperty(default=False)
	flagsum					= db.IntegerProperty(default = 0)
	#creation_order_flag		= db.StringProperty(default=" ")
	#created_int_flag		= db.IntegerProperty(default=0)
class Comments(db.Model):
	db_type			= db.StringProperty(required = True, default = "Comments")
	created			= db.DateTimeProperty(auto_now_add = True)
	epoch			= db.FloatProperty()
	time_since 		= db.StringProperty() # this var should stay empty, and is generated only on page load, but never put to db.

	author_id		= db.IntegerProperty() 		#no longer required to allow deletion
	author_name		= db.StringProperty()
	# exists?
	deleted 		= db.BooleanProperty(default = False)
	washed			= db.BooleanProperty(default = False)
	
	# comment fundimentals
	text			= db.TextProperty(required = True)
	markdown		= db.TextProperty()
	
	obj_parent		= db.IntegerProperty()
	com_parent		= db.IntegerProperty()
	#children		= db.ListProperty(db.Key)
	has_children	= db.BooleanProperty(default=False)
	ranked_children	= db.ListProperty(int)

	obj_ref_id				= db.IntegerProperty()
	obj_ref_nsfw			= db.BooleanProperty()
	obj_ref_okay_for_kids	= db.BooleanProperty()

	upvotes 				= db.IntegerProperty(default = 0)
	downvotes 				= db.IntegerProperty(default = 0)
	netvotes 				= db.IntegerProperty()

	# chached vote/flag section:
	voter_list				= db.ListProperty(int)
	voter_vote				= db.StringListProperty()

	flagger_list			= db.ListProperty(int)
	flagger_flag			= db.StringListProperty()

	# voting section:
	rank					= db.StringProperty(default = "%020d" % (DAY_SCALE))	
	votesum					= db.IntegerProperty(default=0)
	
	# flagging section:
	been_flagged 			= db.BooleanProperty(default=False)
	flagsum					= db.IntegerProperty(default = 0)
class Messages(db.Model):
	db_type			= db.StringProperty(required = True, default = "Messages")
	created			= db.DateTimeProperty(auto_now_add = True)
	epoch			= db.FloatProperty()
	time_since 		= db.StringProperty() # this var should stay empty, and is generated only on page load, but never put to db.

	author_id		= db.IntegerProperty() 		#no longer required to allow deletion
	author_name		= db.StringProperty()
	# exists?
	deleted 		= db.BooleanProperty(default = False)

	text 			= db.TextProperty()
	recipient_id	= db.IntegerProperty()
	recipient_name	= db.StringProperty()
#class WikiEntry(db.Model): in Wiki section
class UserBlob(db.Model):
	created 	= db.DateTimeProperty(auto_now_add = True)
	blob_type 	= db.StringProperty(required = True)
	# blob types:	'image'
	
	# etc. (to be determined)
	user_id 	= db.IntegerProperty()
	uploader 	= db.IntegerProperty() # this is the user_id
	blob_key 	= blobstore.BlobReferenceProperty() 
	filename	= db.StringProperty()

	deleted 	= db.BooleanProperty(default = False)
class ObjectBlob(db.Model):
	created 	= db.DateTimeProperty(auto_now_add = True)
	blob_type 	= db.StringProperty(required = True)
	# blob types:	'image'
	#				'data'
	priority 	= db.IntegerProperty()
	# priorities:	0 = primary data file
	# 				1 = primary image file
	# etc. (to be determined)
	obj_id 		= db.IntegerProperty()
	uploader 	= db.IntegerProperty() # this is the user_id
	blob_key 	= blobstore.BlobReferenceProperty() 
	filename	= db.StringProperty()

	deleted 	= db.BooleanProperty(default = False)
#########################################################
####################### Fake Names #######################
ADMIN_USERNAMES = [
	"scoofy","matt","aoeu","aoeuaoeu",
	"thong", "barf"
	]
FAKE_NAME_LIST = fake_names.return_names()
#########################################################
####################### Tasks #######################
#class Task():
# 20 sec delay needed after a purge for a new task to be created
# countdown = blah is a time delay before task execution
# add.(transactional=True) is a way to make it run in transaction.
# default task queue url is /_ah/queue/(queue_name_here)
#########################################################
####################### Pages #######################
class AdminPage(Handler):
	def render_front(self):
		user = self.return_user_if_cookie()
		if not user:
			self.redirect('/')
			return
		#logging.warning(has_cookie)
		if user.username not in ['aeou', 'barf', 'thong', 'matt', 'scoofy']:
			self.redirect('/')
			return
		# check for admin here: either by name, or id, or both

		# if not admin:
		# 	self.error(404)

		self.render('admin_check.html',
					name = user.username)

	def get(self):
		self.render_front()

	def post(self):
		password = data.return_admin_password()

		user = self.return_user_if_cookie()
		has_cookie = self.return_has_cookie()
		#logging.warning(has_cookie)

		# check for admin here: either by name, or id, or both

		# if not admin:
		# 	self.error(404)

		check = self.request.get('password')
		if not check:
			self.redirect('/admin')
			return
		elif check != password:
			self.redirect('/admin')
			return
		else:
			pass

		user_id = self.check_cookie_return_val("user_id")
		active_username = None
		if user:
			active_username = user.username

		the_list = []
		the_dict = []
		the_objects = []
		the_users = []
		the_comments = []
		the_list = admin_page_query()
		if the_list:
			the_objects = the_list[0]
			the_users = the_list[1]
			the_comments = the_list[2]

			the_dict = cached_vote_data_for_masonry(the_objects, user_id)

		# Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		self.render("admin.html", 
					user = user,
					
					username=active_username, 
					user_id = user_id,
					the_objects=the_objects, 
					the_users=the_users, 
					the_comments=the_comments, 
					has_cookie=has_cookie,
					the_dict = the_dict)
def admin_page_query():
	the_objects = db.GqlQuery('SELECT * FROM Objects WHERE deleted = FALSE AND been_flagged = True ORDER BY flagsum DESC')
	the_users = db.GqlQuery('SELECT * FROM Users WHERE deleted = FALSE AND been_flagged = True ORDER BY flagsum DESC')
	the_comments = db.GqlQuery('SELECT * FROM Comments WHERE deleted = FALSE AND been_flagged = True ORDER BY flagsum DESC')
	logging.warning("DB Query admin page")
	# Turn gql objects to lists
	if the_objects:
		the_objects = list(the_objects)
	if the_users:
		the_users = list(the_users)
	if the_comments:
		the_comments = list(the_comments)
	# make one big list
	the_list = [the_objects, the_users, the_comments]
	logging.warning(the_list)
	return the_list
class AdminObjPage(Handler):
	def render_front(self, obj_num):
		obj_id = int(obj_num)
		user = self.return_user_if_cookie()
		if not user:
			self.redirect('/')
			return
		#logging.warning(has_cookie)

		# check for admin here: either by name, or id, or both
		if user.username not in ['aeou', 'barf', 'thong', 'matt']:
			self.redirect('/')
			return
		# if not admin:
		# 	self.error(404)

		self.render('admin_check.html',
					name = user.username)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_front(obj_id)

	def post(self, obj_num):
		obj_id = int(obj_num)
		password = 'indeedly'

		user = self.return_user_if_cookie()
		has_cookie = self.return_has_cookie()
		#logging.warning(has_cookie)

		# check for admin here: either by name, or id, or both

		# if not admin:
		# 	self.error(404)

		check = self.request.get('password')
		if not check:
			self.redirect('/admin')
			return
		elif check != password:
			self.redirect('/admin')
			return
		else:
			pass

		the_obj = object_page_cache(obj_id)
		the_comments = obj_comment_cache(obj_id)

		# This section checks the cookie and sets the html style accordingly.
		has_cookie = True

		# This section check if the user is the author and can delete the object.
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)
		else:
			pass
			
		if has_cookie:
			user_rate = return_user_rate_from_tuple(obj_id, user_id)
			flagged_by_user = return_user_flag_from_tuple(obj_id, user_id)
		else:
			user_rate = 0
			flagged_by_user = 0

		username = self.check_cookie_return_val("username")

		blob_ref = return_object_blob_by_obj_id_and_priority(obj_id, 0)
		file1_filename = None
		if blob_ref:
			file1_filename = blob_ref.filename
		else:
			pass

		flagsum = the_obj.flagsum
		deleted = the_obj.deleted
		rate_avg = the_obj.rate_avg
		num_ratings = the_obj.num_ratings

		title_var = the_obj.title
		author_name_var = the_obj.author_name
		author_id_var = the_obj.author_id
		created_var = the_obj.created
		epoch_var = the_obj.epoch
		time_since_made = time_since_creation(epoch_var)
		obj_type_var = the_obj.obj_type

		file1_var = the_obj.stl_file_link
		img1_var = the_obj.main_img_link
		license_var = the_obj.license
		obj_link_var = the_obj.obj_link

		description_var = the_obj.description
		tag_var = the_obj.tags
		ups = the_obj.upvotes
		downs = the_obj.downvotes
		net = the_obj.netvotes
		hot = the_obj.hotness_var
		rating = the_obj.rating
		total_ratings = the_obj.total_ratings
		file2 = the_obj.other_file1_link
		img2 = the_obj.other_img1_link

		votesum = the_obj.votesum
		if has_cookie:
			#voted_var = voted(the_obj, user_id)
			# changed to new caching system
			voted_var = return_cached_vote(obj_id, user_id)
		else:
			voted_var = None # this shouldn't even render anyway

		# comment tuples:
		comment_triplet_list = []
		for comment in the_comments:
			comment_triplet_list.append(return_comment_vote_flag_triplet(comment, user_id))
			#this takes the form (comment, vote_int, flag_int)
			#logging.warning(comment_triplet_list)
		
		self.render('adminobjpage.html', 
					user = user,

					obj_id = obj_id,
					deleted = deleted,
					rate_avg = rate_avg,
					num_ratings = num_ratings,
					the_comments = the_comments,
					has_cookie = has_cookie,
					user_rate = user_rate,
					flagged_by_user = flagged_by_user,
					flagsum = flagsum,

					username = username,
					user_id = user_id,

					file1_filename = file1_filename,

					title = title_var,
					author_name = author_name_var,
					author_id = author_id_var,
					obj_type = obj_type_var,
					created = created_var,
					epoch = epoch_var,
					time_since_made = time_since_made,

					file1 = file1_var,
					img1 = img1_var,
					license = license_var,
					obj_link = obj_link_var,

					description = description_var,
					tags = tag_var,
					ups = ups,
					downs = downs,
					net = net,
					hot = hot,
					rating = rating,
					total_ratings = total_ratings,
					file2 = file2,
					img2 = img2,

					votesum = votesum,
					voted = voted_var,
					comment_triplet_list = comment_triplet_list)
class AdminDelHandler(Handler):
	def post(self):
		pass

NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT = 999
def load_front_pages_from_memcache_else_query(page_type, page_num, content_type, update=False):
	if page_type == "/":
		key = "front_page_%s_%s" % (content_type, page_num)
		#print "\n", "loading:", key, "\n"
	else:
		# i will add other pages later
		self.error("load_front_pages_from_memcache_else_query error. Improper page_type.")
		return []

	page_time_list_tuple = memcache.get(key)
	if page_time_list_tuple is None:
		update = True
	elif len(page_time_list_tuple) > 0:
		last_update = page_time_list_tuple[0]

		current_time = time.time()
		global NUMBER_OF_MINUTES_BETWEEN_FRONT_PAGE_UPDATES
		time_gap_between_cache_updates = current_time - (NUMBER_OF_MINUTES_BETWEEN_FRONT_PAGE_UPDATES * 60)

		if time_gap_between_cache_updates > last_update:
			update = True
	
	if update == True:
		current_time = time.time()

		page_num = int(page_num)
		next_page_num = page_num + 1
		number_of_items_to_fetch = 30

		object_query = all_objects_query(content_type)
		logging.warning("DB query all_objects_query(%s)" % content_type) 
		object_list = list(object_query)

		for obj in object_list:
			obj.rank = return_rank(obj)
		object_list.sort(key = lambda x: (int(x.rank), x.epoch), reverse=True)

		#print "\n", "full object list:", object_list, "\n"
		end_of_content = False

		# Since a memcache set doesn't cost money, we will cache 50 pages past the current page when it's setting a new cache.
		page_num_plus_fifty = page_num + 50

		page_time_list_tuple_to_return = None

		for this_pages_number in range(page_num_plus_fifty + 1): # add 1 to page number to include page number in range, then skip zero, so there isn't any ordinal confusion.
			# this_pages_number "1" will be page 1
			if this_pages_number == 0:
				continue
			#print "\n", "this page's number:", this_pages_number, "\n"
			
			# now back to normal counting
			the_objects = object_list[( (this_pages_number -1) * number_of_items_to_fetch) : (this_pages_number * number_of_items_to_fetch)]
			
			#print "\n", the_objects, "\n"
			
			if not the_objects: # If the objects is an empty list
				end_of_content = True

			page_time_list_tuple = [current_time, the_objects]

			if page_type == "/":
				new_key = "front_page_%s_%d" % (content_type, this_pages_number)
				#print "\n", "\n", "new key:", new_key
			else:
				self.error("load_front_pages_from_memcache_else_query error. Improper page_type.")

			memcache.set(new_key, page_time_list_tuple)

			if this_pages_number == page_num:
				page_time_list_tuple_to_return = page_time_list_tuple # this saves the current page which will be set to return below
				#print "\n", "returning this page"

			if end_of_content:
				break

		if page_time_list_tuple_to_return:
			page_time_list_tuple = page_time_list_tuple_to_return

	#print "\n", page_time_list_tuple[1], "\n"
	return page_time_list_tuple[1] # This should always be the current page.
class FrontHandler(Handler):
	def render_front_page(self, page_type, page_num="1"):
		global ADMIN_USERNAMES
		global FAKE_NAME_LIST
		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")
		current_time = time.time()
		#print "The time is:", current_time
		
		content_type = "kids"
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
			content_type = "sfw"

		if page_type == "/":
			the_objects = load_front_pages_from_memcache_else_query(page_type=page_type, page_num=page_num, content_type=content_type)

			page_num = int(page_num)
			next_page_num = page_num + 1

			the_dict = cached_vote_data_for_masonry(the_objects, user_id)

			end_of_content = None
			if len(the_dict) == 0:
				end_of_content = True

			self.render("front_infinite.html", 
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = None,
						cursor_url = None,
						end_of_content = end_of_content,

						page_num = page_num,
						next_page_num = next_page_num,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return
		object_query = all_objects_query(content_type)		
		object_pages = ["/objects"]

		cursor_url = None
		if page_type in object_pages:
			object_query = object_query.filter('printable =', True)

		### obj list method ###
		use_object_list = False
		if page_type =="/":
			use_object_list = True
			object_list = list(object_query)
		###

		if page_type == "/":
			cursor_url = "/?cursor="
			# sort by rank, then epoch if a tie
			object_query.order('-rank').order('-epoch')

			###
			for obj in object_list:
				obj.rank = return_rank(obj)
			object_list.sort(key = lambda x: (int(x.rank), x.epoch), reverse=True)
			###

		elif page_type == "/objects":
			cursor_url = "/objects?cursor="
			# sort by rank, then epoch if a tie
			object_query.order('-rank').order('-epoch')

		elif page_type == "/recentcommentsmain":
			cursor_url = "/recentcommentsmain?cursor="
			object_query.order('-most_recent_comment_epoch')

		elif page_type == "/newmain":
			cursor_url = "/newmain?cursor="
			object_query.order('-epoch')

		elif page_type == "/topmain":
			cursor_url = "/topmain?cursor="
			object_query.order('-votesum')

		elif page_type == "/news":
			object_query = object_query.filter('news =', True)
			cursor_url = "/news?cursor="
			object_query.order('-rank').order('-epoch')

		elif page_type == "/newnews":
			object_query = object_query.filter('news =', True)
			cursor_url = "/newnews?cursor="
			object_query.order('-epoch')

		elif page_type == "/topnews":
			object_query = object_query.filter('news =', True)
			cursor_url = "/topnews?cursor="
			object_query.order('-votesum')

		elif page_type == "/university":
			object_query = object_query.filter('learn =', True)
			cursor_url = "/university?cursor="
			object_query.order('-rank').order('-epoch')

		elif page_type == "/newuniversity":
			object_query = object_query.filter('learn =', True)
			cursor_url = "/newuniversity?cursor="
			object_query.order('-epoch')

		elif page_type == "/topuniversity":
			object_query = object_query.filter('learn =', True)
			cursor_url = "/topuniversity?cursor="
			object_query.order('-votesum')

		elif page_type == "/video":
			object_query = object_query.filter('learn =', True)
			cursor_url = "/video?cursor="
			object_query.order('-rank').order('-epoch')

		cursor = self.request.get("cursor")
		if cursor:
			object_query.with_cursor(cursor)

		page_num = int(page_num)
		next_page_num = page_num + 1
		number_of_items_to_fetch = 30

		# this is for using the object list style of page loading, which we are currently using for the index page
		if use_object_list:
			the_objects = object_list[( (page_num -1) * number_of_items_to_fetch) : (page_num * number_of_items_to_fetch)]
		else:
			the_objects = object_query.fetch(number_of_items_to_fetch, offset = max((page_num - 1) * number_of_items_to_fetch, 0))
		cursor = object_query.cursor()

		if page_type in ["/", "/news", "/newnews", "/topnews", "/university", "/newuniverisy", "topuniversity", "/objects"]:
			# resort with live updating rankings
			for obj in the_objects:
				obj.rank = return_rank(obj)
			the_objects.sort(key = lambda x: (int(x.rank), x.epoch), reverse=True)

		the_dict = cached_vote_data_for_masonry(the_objects, user_id)
		#if page_type == "/news":
			#for obj in the_dict:
				#print obj
		#logging.warning(the_dict)
		end_of_content = None
		if len(the_dict) == 0:
			#logging.warning("empty")
			end_of_content = True
		#logging.warning('loading front_infinite')

		everything_pages = ["/", "/recentcommentsmain", "/newmain", "/topmain"]
		if page_type in everything_pages:
			self.render("front_infinite.html", 
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						page_num = page_num,
						next_page_num = next_page_num,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return
		elif page_type == "/objects":
			self.render("front.html", 
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						page_num = page_num,
						next_page_num = next_page_num,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return
		elif page_type == "/news":
			self.render("news_front.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return

		elif page_type == "/newnews":
			self.render("news_front.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return

		elif page_type == "/topnews":
			self.render("news_front.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return			

		elif page_type == "/university":
			self.render("uni_front.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return

		elif page_type == "/newuniversity":
			self.render("uni_front.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return

		elif page_type == "/topuniversity":
			self.render("uni_front.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return			

		elif page_type == "/video":
			self.render("uni_front_video.html",
						user = user,
						user_id = user_id,

						the_dict = the_dict,
						cursor = cursor,
						cursor_url = cursor_url,
						end_of_content = end_of_content,

						ADMIN_USERNAMES = ADMIN_USERNAMES,
						FAKE_NAME_LIST = FAKE_NAME_LIST,
						)
			return	
class MainEverything(FrontHandler):
	def get(self, page_num = "1"):
		self.render_front_page('/', page_num = page_num)
class MainPageObjects(FrontHandler):
	def render_front(self):
		pass
		# user = self.return_user_if_cookie()
		# has_cookie = self.return_has_cookie()
		# #logging.warning(has_cookie)
		# user_id = self.check_cookie_return_val("user_id")
		# active_username = None
		# if user:
		# 	active_username = user.username

		# content_type = "kids"
		# over18 = self.check_cookie_return_val("over18")
		# logging.warning(over18)
		# if over18 == "True":
		# 	over18 = True
		# 	content_type = "sfw"
		
		# object_query = front_page_cache(content_type)
		# cursor = self.request.get("cursor")
		# if cursor:
		# 	object_query.with_cursor(cursor)
		# the_objects = object_query.fetch(30)
		# cursor = object_query.cursor()
		# cursor_url = "/?cursor="

		# the_users = users_cache()
		# the_comments = comments_cache()
		
		# # reset rank for live adjustment
		# for obj in the_objects:
		# 	obj.rank = return_rank(obj)
		# the_objects.sort(key = lambda x: x.rank, reverse=True)

		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)
		# #logging.warning(the_dict)
		# end_of_content = None
		# if len(the_dict) == 0:
		# 	#logging.warning("empty")
		# 	end_of_content = True

		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# logging.warning(random_string_generator())
		# self.render("front.html", 
		# 			user = user,
					
		# 			username=active_username, 
		# 			user_id = user_id,
		# 			the_objects=the_objects, 
		# 			the_users=the_users, 
		# 			the_comments=the_comments, 
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict,
		# 			cursor = cursor,
		# 			cursor_url = cursor_url,
		# 			end_of_content = end_of_content,
		# 			)

	def get(self, page_num = "1"):
		#logging.warning(page_num)
		#logging.warning(type(page_num))
		self.render_front_page('/objects', page_num = page_num)

	def post(self, page_num):
		pass
class MainPageRecentComments(FrontHandler):
	def render_front(self):
		pass
		# user = self.return_user_if_cookie()
		# has_cookie = self.return_has_cookie()
		# #logging.warning(has_cookie)
		# user_id = self.check_cookie_return_val("user_id")
		# active_username = None
		# if user:
		# 	active_username = user.username

		# content_type = "kids"
		# over18 = self.check_cookie_return_val("over18")
		# logging.warning(over18)
		# if over18 == "True":
		# 	over18 = True
		# 	content_type = "sfw"
		
		# object_query = front_page_cache(content_type)
		# cursor = self.request.get("cursor")
		# if cursor:
		# 	object_query.with_cursor(cursor)
		# the_objects = object_query.fetch(30)
		# cursor = object_query.cursor()
		# cursor_url = "/recentcommentsmain?cursor="

		# the_users = users_cache()
		# the_comments = comments_cache()
		
		# # reset rank for live adjustment
		# for obj in the_objects:
		# 	obj.rank = return_rank(obj)
		# the_objects.sort(key = lambda x: x.most_recent_comment_epoch, reverse=True)

		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)
		# #logging.warning(the_dict)
		# end_of_content = None
		# if len(the_dict) == 0:
		# 	#logging.warning("empty")
		# 	end_of_content = True

		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# logging.warning(random_string_generator())
		# self.render("front.html", 
		# 			user = user,
					
		# 			username=active_username, 
		# 			user_id = user_id,
		# 			the_objects=the_objects, 
		# 			the_users=the_users, 
		# 			the_comments=the_comments, 
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict,
		# 			cursor = cursor,
		# 			cursor_url = cursor_url,
		# 			end_of_content = end_of_content,
		# 			)

	def get(self):
		self.render_front_page("/recentcommentsmain")

	def post(self):
		pass

class MainPageNew(FrontHandler):
	def render_front(self):
		pass
		# user = self.return_user_if_cookie()
		# has_cookie = self.return_has_cookie()
		# #logging.warning(has_cookie)
		# user_id = self.check_cookie_return_val("user_id")
		# active_username = None
		# if user:
		# 	active_username = user.username

		# content_type = "kids"
		# over18 = self.check_cookie_return_val("over18")
		# logging.warning(over18)
		# if over18 == "True":
		# 	over18 = True
		# 	content_type = "sfw"
		
		# object_query = front_page_cache_new(content_type)
		# cursor = self.request.get("cursor")
		# if cursor:
		# 	object_query.with_cursor(cursor)
		# the_objects = object_query.fetch(30)
		# cursor = object_query.cursor()
		# cursor_url = "/newmain?cursor="

		# the_users = users_cache()
		# the_comments = comments_cache()
		

		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)
		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# logging.warning(random_string_generator())
		# self.render("front.html", 
		# 			user = user,
					
		# 			username=active_username, 
		# 			user_id = user_id,
		# 			the_objects=the_objects, 
		# 			the_users=the_users, 
		# 			the_comments=the_comments, 
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict,
		# 			cursor = cursor,
		# 			cursor_url = cursor_url,
		# 			)

	def get(self):
		self.render_front_page("/newmain")

	def post(self):
		pass
class MainPageTop(FrontHandler):
	def render_front(self):
		pass
		# user = self.return_user_if_cookie()
		# has_cookie = self.return_has_cookie()
		# #logging.warning(has_cookie)
		# user_id = self.check_cookie_return_val("user_id")
		# active_username = None
		# if user:
		# 	active_username = user.username

		# content_type = "kids"
		# over18 = self.check_cookie_return_val("over18")
		# logging.warning(over18)
		# if over18 == "True":
		# 	over18 = True
		# 	content_type = "sfw"
		
		# object_query = front_page_cache_top(content_type)
		# cursor = self.request.get("cursor")
		# if cursor:
		# 	object_query.with_cursor(cursor)
		# the_objects = object_query.fetch(30)
		# cursor = object_query.cursor()
		# cursor_url = "/topmain?cursor="

		# the_users = users_cache()
		# the_comments = comments_cache()
		

		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)
		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# logging.warning(random_string_generator())
		# self.render("front.html", 
		# 			user = user,
					
		# 			username=active_username, 
		# 			user_id = user_id,
		# 			the_objects=the_objects, 
		# 			the_users=the_users, 
		# 			the_comments=the_comments, 
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict,
		# 			cursor = cursor,
		# 			)

	def get(self):
		self.render_front_page("/topmain")

	def post(self):
		pass		


class ThingTracker(Handler):
	def get(self):
		object_query = all_objects_query("all")
		object_query = object_query.filter("obj_type =", "upload").order('-epoch')
		obj_list = list(object_query)
		list_length = len(obj_list)
		global page_url
		self.response.headers['Content-Type'] = 'application/json'
		json_things = []
		for obj in obj_list:
			the_author = obj.author_name
			if obj.original_creator:
				the_author = obj.original_creator
			all_tags = obj.tags
			print all_tags
			json_things.append(
				{
					"id": str(obj.uuid),
					"title": str(obj.title),
					"author": str(the_author),
					"license": str(obj.license),
					"tags": all_tags,
					"thumbnailURL": "http://bld3r.com%s" % obj.main_img_link,
					"description": obj.description,
					"ref-url":page_url + "/obj/" + str(obj.key().id()) + ".json",
					"metadata" : {
							"created" : str(obj.created)
						}
				}
			)
		json_obj = {
			"specification-version" : 0.02,
			"url" : "http://www.bld3r.com/thingtracker",
			"description" : "Thingtracker for bld3r.com",
			"updated" : "2014-02-03T14:40:00-06:00",
			"things-count" : list_length,
			"maintainers" : [
				{"name" : "Matthew Schoolfield"},
				{"name" : "Thong Nguyen"}
			],
			"things" : json_things
		}
		self.response.out.write(json.dumps(json_obj))

class ObjectPage(Handler):		
	def render_page(self, obj_num, error=""):
		user = self.return_user_if_cookie()

		photo_upload_url = blobstore.create_upload_url('/object_img_upload')
		visitor_upload_url = blobstore.create_upload_url('/visitor_img_upload')
		show_3d_model = self.request.get("webgl")

		obj_id = int(obj_num)
		the_obj = return_thing_by_id(obj_id, "Objects")
		if not the_obj:
			self.inline_404()
			return
		author = return_thing_by_id(the_obj.author_id, "Users")
		the_comments = obj_comment_cache(obj_id)
		# head_comments = []
		# for comment in the_comments:
		# 	if comment.obj_parent is not None:
		# 		#logging.warning(comment.key().id())
		# 		head_comments.append(comment)
		# #logging.warning(head_comments)

		okay_for_kids = the_obj.okay_for_kids
		if okay_for_kids != True:
			over18 = self.check_cookie_return_val("over18")
			if over18 != "True":
				self.redirect('/')
			else:
				pass
		else:
			pass

		# This section checks the cookie and sets the html style accordingly.
		has_cookie = None
		logged_in = self.check_cookie_return_val("user_id")
		if not logged_in:
			pass
		else:
			has_cookie = "Hell Yes!!!!!"

		# This section check if the user is the author and can delete the object.
		user_is_author = False
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)
			user_id_str = str(user_id)
		else:
			user_id_str = ""

		author_tag_str = ""
		public_tag_str = ""
		visitor_has_added_img = False
		if user and (the_obj.author_id == user.key().id()):
			# User is object author
			user_is_author = True
			if the_obj.author_tags:
				if "None" in the_obj.author_tags:
					the_obj.author_tags.remove("None")
					if the_obj.author_tags is None:
						the_obj.author_tags = [""]
				author_tag_str = ", ".join(the_obj.author_tags)
		elif user:
			if str(the_obj.key().id()) in user.imgs_on_others_objects:
				visitor_has_added_img = True

		user_hash = None
		if has_cookie:
			user_rate = return_user_rate_from_tuple(obj_id, user_id)
			flagged_by_user = return_user_flag_from_tuple(obj_id, user_id)
			# set edit tags section
			if the_obj.public_tags:
				if "None" in the_obj.public_tags:
					the_obj.public_tags.remove("None")
					if the_obj.public_tags is None:
						the_obj.public_tags = [""]
				public_tag_str = ", ".join(the_obj.public_tags)
			if user:
				user_hash = hashlib.sha256(user.random_string).hexdigest()
				# This is used in sub.html, so if you change this, you will break subcomments

		else:
			user_rate = 0
			flagged_by_user = 0

		username = self.check_cookie_return_val("username")


		file_upload_error = self.request.get('file_upload_error')
		#print file_upload_error


		#blob_ref = return_object_blob_by_obj_id_and_priority(obj_id, 0)
		file1_filename = the_obj.stl_filename
		#if blob_ref:
		#	file1_filename = blob_ref.filename
		#else:
		#	pass

		if the_obj.deleted == True or the_obj.under_review == True:
			removed = True
		else:
			removed = False

		flagsum = the_obj.flagsum
		deleted = the_obj.deleted
		rate_avg = the_obj.rate_avg
		num_ratings = the_obj.num_ratings

		title_var = the_obj.title
		author_name_var = the_obj.author_name
		author_id_var = the_obj.author_id
		created_var = the_obj.created
		epoch_var = the_obj.epoch
		time_since_made = time_since_creation(epoch_var)
		obj_type_var = the_obj.obj_type

		file1_var = the_obj.stl_file_link
		img1_var = the_obj.main_img_link
		license_var = the_obj.license
		obj_link_var = the_obj.obj_link
		short_url_var = None
		if obj_link_var:
			parse = urlparse(obj_link_var)
			short_url_var = parse[1]
		else:
			pass		

		description_var = the_obj.description
		
		description_exists = False
		long_description = False
		if the_obj:
			if the_obj.description:
				if len(the_obj.description) > 0:
					description_exists = True
					if len(the_obj.description) > 500:
						long_description = True
		tag_var = the_obj.tags
		ups = the_obj.upvotes
		downs = the_obj.downvotes
		net = the_obj.netvotes
		hot = the_obj.hotness_var
		rating = the_obj.rating
		total_ratings = the_obj.total_ratings
		file2 = the_obj.other_file1_link
		img2 = the_obj.other_img1_link

		other_img_list = []
		img_list_full = False
		if the_obj.img_link_2:
			other_img_list.append(the_obj.img_link_2)
		if the_obj.img_link_3:
			other_img_list.append(the_obj.img_link_3)
		if the_obj.img_link_4:
			other_img_list.append(the_obj.img_link_4)
		if the_obj.img_link_5:
			other_img_list.append(the_obj.img_link_5)
		if len(other_img_list) >= 4:
			img_list_full = True

		other_file_list = []
		file_list_full = False
		if the_obj.file_link_2:
			other_file_list.append(the_obj.file_link_2)
		if the_obj.file_link_3:
			other_file_list.append(the_obj.file_link_3)
		if the_obj.file_link_4:
			other_file_list.append(the_obj.file_link_4)
		if the_obj.file_link_5:
			other_file_list.append(the_obj.file_link_5)
		if the_obj.file_link_6:
			other_file_list.append(the_obj.file_link_6)
		if the_obj.file_link_7:
			other_file_list.append(the_obj.file_link_7)
		if the_obj.file_link_8:
			other_file_list.append(the_obj.file_link_8)
		if the_obj.file_link_9:
			other_file_list.append(the_obj.file_link_9)
		if the_obj.file_link_10:
			other_file_list.append(the_obj.file_link_10)
		if the_obj.file_link_11:
			other_file_list.append(the_obj.file_link_11)
		if the_obj.file_link_12:
			other_file_list.append(the_obj.file_link_12)
		if the_obj.file_link_13:
			other_file_list.append(the_obj.file_link_13)
		if the_obj.file_link_14:
			other_file_list.append(the_obj.file_link_14)
		if the_obj.file_link_15:
			other_file_list.append(the_obj.file_link_15)

		if len(other_file_list) >= 14:
			file_list_full = True

		visitor_img_quad_list = []
		for a_tuple in the_obj.visitor_img_list:
			# quads are of the form ["user_id|username|img_url_path|blob_key"]
			if a_tuple != "None":
				visitor_img_quad_list.append(a_tuple.split("|"))
				logging.warning(visitor_img_quad_list)


		votesum = the_obj.votesum
		if has_cookie:
			#voted_var = voted(the_obj, user_id)
			# changed to new caching system
			voted_var = return_cached_vote(obj_id, user_id)
		else:
			voted_var = None # this shouldn't even render anyway

		# comment tuples:
		comment_triplet_list = []
		for comment in the_comments:
			comment.time_since =  time_since_creation(comment.epoch)
			the_com_trip = return_comment_vote_flag_triplet(comment, user_id)
			#logging.warning('com_trip')
			#this takes the form (comment, vote_int, flag_int)
			if user:
				#####
				if str(the_com_trip[0].author_id) in user.block_list:
					the_com_trip[0].text = "You have blocked this user's content."
			comment_triplet_list.append(the_com_trip)
		
		printed_by_list = return_printed_by_list(obj_id)
		#logging.warning(printed_by_list)

		global ADMIN_USERNAMES
		global FAKE_NAME_LIST
		
		self.render('objectpage.html', 
					user = user,
					
					user_hash = user_hash,
					# This is used in sub.html, so if you change this, you will break subcomments
					# Also used for other image upload
					photo_upload_url = photo_upload_url,
					visitor_upload_url = visitor_upload_url,
					other_img_list = other_img_list,
					img_list_full = img_list_full,
					file_list_full = file_list_full,
					visitor_has_added_img = visitor_has_added_img,
					visitor_img_quad_list = visitor_img_quad_list,

					removed = removed,

					obj_id = obj_id,
					obj_id_str = str(obj_id),
					deleted = deleted,
					rate_avg = rate_avg,
					num_ratings = num_ratings,
					the_comments = the_comments,
					has_cookie = has_cookie,
					user_is_author = user_is_author,
					user_rate = user_rate,
					flagged_by_user = flagged_by_user,
					flagsum = flagsum,
					long_description = long_description,
					description_exists = description_exists,

					the_obj = the_obj,
					author = author,

					username = username,
					user_id = user_id,
					user_id_str = user_id_str,
					error = error,

					file1_filename = file1_filename,

					title = title_var,
					author_name = author_name_var,
					author_id = author_id_var,
					obj_type = obj_type_var,
					created = created_var,
					epoch = epoch_var,
					time_since_made = time_since_made,

					file1 = file1_var,
					img1 = img1_var,
					license = license_var,
					obj_link = obj_link_var,
					short_url = short_url_var,

					description = description_var,
					tags = tag_var,
					ups = ups,
					downs = downs,
					net = net,
					hot = hot,
					rating = rating,
					total_ratings = total_ratings,
					file2 = file2,
					img2 = img2,

					votesum = votesum,
					voted = voted_var,
					comment_triplet_list = comment_triplet_list,
					printed_by_list = printed_by_list,
					author_tag_str  = author_tag_str,
					public_tag_str = public_tag_str,

					show_3d_model = show_3d_model,

					file_upload_error = file_upload_error,

					ADMIN_USERNAMES = ADMIN_USERNAMES,
					FAKE_NAME_LIST = FAKE_NAME_LIST,
					)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)
	
	def post(self, obj_num):
		'''
		This section posts a new comment
		'''
		the_comments = obj_comment_cache(int(obj_num))
		comment_var = self.request.get("obj_comment_form")
		subcomment_var = None
		parent_id = None

		obj_author = None
		note = None
		for i in the_comments:
			val = i.key().id()
			subcomment_var = self.request.get("subcomment_form%d" % val)
			if subcomment_var:
				parent_id = val
				parent_comment = i
				logging.warning(parent_id)
				logging.warning(subcomment_var)
				break

		if not (comment_var or subcomment_var):
			# Empty comment submitted
			obj_id = int(obj_num)
			#error_var = "Please do not submit an empty comment."
			self.redirect('/obj/%d' % obj_id)
		else:
			# Check if logged in again (to prevent delete cookies after page load)
			user_id = self.check_cookie_return_val("user_id")
			username_var = self.check_cookie_return_val("username")
			if not (user_id and username_var):
				self.redirect('/obj/%d' % int(obj_num))
			else:
				verify_hash = self.request.get("verify")
				user_id = int(user_id)
				user = return_thing_by_id(user_id, "Users")
				if user is None:
					self.error(404)
					return
				user_hash = hashlib.sha256(user.random_string).hexdigest()
				logging.warning(user_hash)
				logging.warning(verify_hash)
				if user_hash != verify_hash:
					logging.error("Someone is trying to hack the comments")
					self.error(400)
					return

				# Success!
	
				# markdown2 for clean comments
				escaped_comment_text = None
				if comment_var:
					escaped_comment_text = cgi.escape(comment_var)
				elif subcomment_var:
					escaped_comment_text = cgi.escape(subcomment_var)
				mkd_converted_comment = mkd.convert(escaped_comment_text)
	
				obj_id = int(obj_num)
				the_object = object_page_cache(obj_id)
				nsfw_bool = the_object.nsfw
				kids_bool = the_object.okay_for_kids

				if comment_var:
					obj_author_name = the_object.author_name
					obj_author_id = the_object.author_id
					logging.warning(obj_author_id)
					obj_title = the_object.title

					new_comment = Comments(
											author_id = user_id,
											author_name = username_var,
											epoch = float(time.time()),
											text = comment_var,
											markdown = mkd_converted_comment,

											obj_parent = obj_id,

											obj_ref_id = obj_id,
											obj_ref_nsfw = nsfw_bool,
											obj_ref_okay_for_kids = kids_bool)
					new_comment.put()
					logging.warning('New Comment Created')
					if int(obj_author_id) != int(user_id):
						if str(obj_author_id) not in user.blocked_by_list:
							logging.warning('should sleep here')
							new_note(int(obj_author_id),
								"Comments|%d|%s| <a href='/user/%s'>%s</a> commented on <a href='/obj/%s'>%s</a>" % (
										int(new_comment.key().id()),
											str(time.time()),
																str(user_id),
																	str(cgi.escape(username_var)),
																									str(obj_id),
																										str(cgi.escape(obj_title))),
								delay=6)
						else:
							# user blocked
							logging.warning('user blocked, no notification / fake sleep')
							time.sleep(6)
							# fake sleep

					else:
						logging.warning('6 second sleep for new comment by author')
						time.sleep(6)
				
				elif subcomment_var:
					logging.warning('db query -- get parent_comment by id')
					logging.warning(parent_id)
					logging.warning(parent_comment)
					new_subcomment = Comments(
											author_id = user_id,
											author_name = username_var,
											epoch = float(time.time()),
											text = subcomment_var,
											markdown = mkd_converted_comment,

											com_parent = parent_comment.key().id(),
											#parent = parent_comment.key(),

											obj_ref_id = obj_id,
											obj_ref_nsfw = nsfw_bool,
											obj_ref_okay_for_kids = kids_bool)
					new_subcomment.put()
					#parent_comment.children.append(new_subcomment.key())
					if parent_comment.has_children == False:
						parent_comment.has_children = True
					parent_comment.ranked_children.append(int(new_subcomment.key().id()))
					if len(parent_comment.ranked_children) > 1:
						parent_comment.ranked_children = sort_comment_child_ranks(parent_comment.ranked_children, delay = 6)
					parent_comment.put()
					memcache.set('Comments_%d' % parent_comment.key().id(), [parent_comment])
					logging.warning('New Subcomment Created')
					if int(parent_comment.author_id) != int(user_id):
						if str(parent_comment.author_id) not in user.blocked_by_list:
							logging.warning('should sleep here')
							new_note(parent_comment.author_id,
								"Comments|%d|%s| <a href='/user/%s'>%s</a> has replied to your <a href='/com/%s'>comment</a>" % (
										int(new_subcomment.key().id()),
											str(time.time()),
																str(user_id),
																	str(cgi.escape(username_var)),
																											str(parent_comment.key().id())),
								# there should be a permelink for comments here (ugh, yet another pages to write)
								delay=6)
						else:
							# user blocked
							logging.warning('user blocked, no notification / fake sleep')
							time.sleep(6)
							# fake sleep
					else:
						logging.warning('6 second sleep for new subcomment by same previous comment author')
						time.sleep(6)

				obj_comments = obj_comment_cache(obj_id, update=True)
				the_object.total_num_of_comments = len(obj_comments)

				the_object.most_recent_comment_epoch = float(time.time())
				the_object.put()
				memcache.set("Objects_%d" % obj_id, [the_object])

				if nsfw_bool == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update=True)



				user_page_comment_cache(user_id, update=True) # no longer needed really...
				user_page_obj_com_cache(user_id, update=True)
				if kids_bool == True:
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass
				self.redirect('/obj/%d' % obj_id)
class ObjectEdit(Handler):
	def render_page(self, obj_num, error=""):
		obj_id = int(obj_num)
		the_obj = object_page_cache(obj_id)

		# This section check if the user is the author and can delete the object.
		user_is_author = False
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)

		if user_id and (the_obj.author_id == user_id):
			# User is object author
			user_is_author = True

		if user_is_author == False:
			self.redirect('/obj/%d' % obj_id)
			return

		okay_for_kids = the_obj.okay_for_kids
		if okay_for_kids != True:
			over18 = self.check_cookie_return_val("over18")
			if over18 != "True":
				self.redirect('/')
			else:
				pass
		else:
			pass

		# This section checks the cookie and sets the html style accordingly.
		has_cookie = None
		logged_in = self.check_cookie_return_val("user_id")
		if not logged_in:
			pass
		else:
			has_cookie = "Hell Yes!!!!!"

		if has_cookie:
			user_rate = return_user_rate_from_tuple(obj_id, user_id)
			flagged_by_user = return_user_flag_from_tuple(obj_id, user_id)
		else:
			user_rate = 0
			flagged_by_user = 0

		username = self.check_cookie_return_val("username")

		blob_ref = return_object_blob_by_obj_id_and_priority(obj_id, 0)
		file1_filename = None
		if blob_ref:
			file1_filename = blob_ref.filename
		else:
			pass

		flagsum = the_obj.flagsum
		deleted = the_obj.deleted
		rate_avg = the_obj.rate_avg
		num_ratings = the_obj.num_ratings

		title_var = the_obj.title
		author_name_var = the_obj.author_name
		author_id_var = the_obj.author_id
		created_var = the_obj.created
		epoch_var = the_obj.epoch
		obj_type_var = the_obj.obj_type

		file1_var = the_obj.stl_file_link
		img1_var = the_obj.main_img_link
		license_var = the_obj.license
		obj_link_var = the_obj.obj_link

		description_var = the_obj.description
		tag_var = the_obj.tags
		ups = the_obj.upvotes
		downs = the_obj.downvotes
		net = the_obj.netvotes
		hot = the_obj.hotness_var
		rating = the_obj.rating
		total_ratings = the_obj.total_ratings
		file2 = the_obj.other_file1_link
		img2 = the_obj.other_img1_link

		votesum = the_obj.votesum
		if has_cookie:
			#voted_var = voted(the_obj, user_id)
			# changed to new caching system
			voted_var = return_cached_vote(obj_id, user_id)
		else:
			voted_var = None # this shouldn't even render anyway

		tag_str = ', '.join(tag_var)
		
		self.render('objectedit.html', 
					obj_id = obj_id,
					deleted = deleted,
					rate_avg = rate_avg,
					num_ratings = num_ratings,
					has_cookie = has_cookie,
					user_is_author = user_is_author,
					user_rate = user_rate,
					flagged_by_user = flagged_by_user,
					flagsum = flagsum,
					username = username,
					error = error,

					file1_filename = file1_filename,

					title = title_var,
					author_name = author_name_var,
					author_id = author_id_var,
					obj_type = obj_type_var,
					created = created_var,
					epoch = epoch_var,

					file1 = file1_var,
					img1 = img1_var,
					license = license_var,
					obj_link = obj_link_var,

					description = description_var,
					tags = tag_var,
					tag_str = tag_str,
					ups = ups,
					downs = downs,
					net = net,
					hot = hot,
					rating = rating,
					total_ratings = total_ratings,
					file2 = file2,
					img2 = img2,

					votesum = votesum,
					voted = voted_var,
					)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)

	def post(self, obj_num):
		obj_id = int(obj_num)
		desc_var = self.request.get('description')

		if not desc_var:
			logging.error('something fucked up')
			self.redirect('/obj/edit/%d' % obj_id)
			return
		#logging.warning('well we got this far')
		
		# Now we know we have one form submission and only one.		
		if desc_var:
			obj = Objects.get_by_id(obj_id)
			logging.warning('db query -- object edit post descripiton')
			obj.description = desc_var
			obj.put()
			object_page_cache(obj_id, update=True, delay = 6)
		else:
			# something broke
			logging.error("ERROR -- in object edit post request")

		self.redirect('/obj/%d' % obj_id)
class ObjectTagEdit(Handler):
	def render_page(self, obj_num, error=""):
		obj_id = int(obj_num)
		the_obj = return_thing_by_id(obj_id, "Objects")

		# This section check if the user is the author and can delete the object.
		user_is_author = False
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)

		if user_id and (the_obj.author_id == user_id):
			# User is object author
			user_is_author = True

		okay_for_kids = the_obj.okay_for_kids
		if okay_for_kids != True:
			over18 = self.check_cookie_return_val("over18")
			if over18 != "True":
				self.redirect('/')
			else:
				pass
		else:
			pass

		# This section checks the cookie and sets the html style accordingly.
		has_cookie = None
		name_check = self.check_cookie_return_val("username")
		id_check = self.check_cookie_return_val("user_id")
		if not (name_check and id_check):
			pass
		else:
			has_cookie = "Hell Yes!!!!!"

		if has_cookie:
			user_rate = return_user_rate_from_tuple(obj_id, user_id)
			flagged_by_user = return_user_flag_from_tuple(obj_id, user_id)
		else:
			user_rate = 0
			flagged_by_user = 0

		username = self.check_cookie_return_val("username")

		blob_ref = return_object_blob_by_obj_id_and_priority(obj_id, 0)
		file1_filename = None
		if blob_ref:
			file1_filename = blob_ref.filename
		else:
			pass

		flagsum = the_obj.flagsum
		deleted = the_obj.deleted
		rate_avg = the_obj.rate_avg
		num_ratings = the_obj.num_ratings

		title_var = the_obj.title
		author_name_var = the_obj.author_name
		author_id_var = the_obj.author_id
		created_var = the_obj.created
		epoch_var = the_obj.epoch
		obj_type_var = the_obj.obj_type

		file1_var = the_obj.stl_file_link
		img1_var = the_obj.main_img_link
		license_var = the_obj.license
		obj_link_var = the_obj.obj_link

		description_var = the_obj.description
		tag_var = the_obj.tags
		ups = the_obj.upvotes
		downs = the_obj.downvotes
		net = the_obj.netvotes
		hot = the_obj.hotness_var
		rating = the_obj.rating
		total_ratings = the_obj.total_ratings
		file2 = the_obj.other_file1_link
		img2 = the_obj.other_img1_link

		votesum = the_obj.votesum
		if has_cookie:
			#voted_var = voted(the_obj, user_id)
			# changed to new caching system
			voted_var = return_cached_vote(obj_id, user_id)
		else:
			voted_var = None # this shouldn't even render anyway

		tag_str = ', '.join(tag_var)
		author_tag_str = ', '.join(the_obj.author_tags)
		public_tag_str = ', '.join(the_obj.public_tags)
		
		self.render('object_tag_edit.html', 
					obj_id = obj_id,
					deleted = deleted,
					rate_avg = rate_avg,
					num_ratings = num_ratings,
					has_cookie = has_cookie,
					user_is_author = user_is_author,
					user_rate = user_rate,
					flagged_by_user = flagged_by_user,
					flagsum = flagsum,
					username = username,
					error = error,

					file1_filename = file1_filename,

					title = title_var,
					author_name = author_name_var,
					author_id = author_id_var,
					obj_type = obj_type_var,
					created = created_var,
					epoch = epoch_var,

					file1 = file1_var,
					img1 = img1_var,
					license = license_var,
					obj_link = obj_link_var,

					description = description_var,
					tags = tag_var,
					tag_str = tag_str,
					author_tag_str = author_tag_str,
					public_tag_str = public_tag_str,
					ups = ups,
					downs = downs,
					net = net,
					hot = hot,
					rating = rating,
					total_ratings = total_ratings,
					file2 = file2,
					img2 = img2,

					votesum = votesum,
					voted = voted_var,
					)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)

	def post(self, obj_num):
		obj_id = int(obj_num)
		username = self.check_cookie_return_val('username')
		user_id = self.check_cookie_return_val('user_id')
		if not (username and user_id):
			logging.error('something fucked up')
			self.error(404)
			return
		author_tag_str = self.request.get('author_tags')
		public_tag_str = self.request.get('public_tags')
		if author_tag_str and public_tag_str:
			self.error(404)
			return
		if not (author_tag_str or public_tag_str):
			logging.error('something fucked up')
			self.redirect('/obj/edit/%d' % obj_id)
			return
		#logging.warning('well we got this far')
		
		# Now we know we have one form submission and only one.		
		if author_tag_str:
			tag_list = author_tag_str.split(', ')
			tag_list = remove_list_duplicates(tag_list)
			tag_list = strip_list_whitespace(tag_list)
			obj = return_thing_by_id(obj_id, "Objects")
			if tag_list == obj.author_tags:
				return
			obj.author_tags = tag_list
			all_tags = obj.author_tags + obj.public_tags
			all_tags = remove_list_duplicates(all_tags)
			obj.tags = all_tags
			obj.put()
			memcache.set("Objects_%d" % int(obj_id), [obj])
		elif public_tag_str:
			tag_list = public_tag_str.split(',')
			tag_list = remove_list_duplicates(tag_list)
			tag_list = strip_list_whitespace(tag_list)
			obj = return_thing_by_id(obj_id, "Objects")
			if tag_list == obj.public_tags:
				return
			obj.public_tags = tag_list
			all_tags = obj.author_tags + obj.public_tags
			all_tags = remove_list_duplicates(all_tags)
			obj.tags = all_tags
			obj.put()
			memcache.set("Objects_%d" % int(obj_id), [obj])
			if int(user_id) == obj.author_id:
				pass
			else:
				new_note(obj.author_id, 
						"NA| |%s| <a href='/user/%s'>%s</a> edited the public tags on <a href='/obj/%s'>%s</a>" % (
						str(time.time()),
											str(user_id),
												str(cgi.escape(username)),
																					str(obj_id),
																						str(cgi.escape(obj.title))),
						delay=6)
		else:
			# something broke
			logging.error("ERROR -- in object edit post request")

		taskqueue.add(url ='/tagupdateworker', 
					  countdown = 6
					 )
					

		self.redirect('/obj/%d' % obj_id)
class AjaxDescriptionEdit(Handler):
	def post(self):
		obj_num = self.request.get("description_obj_id")
		logging.warning(obj_num)
		user_id = self.request.get("description_user_id")
		verify = self.request.get("verify")

		if not obj_num and user_id:
			logging.warning('no obj_num and user_id')
			self.error(400)
			return

		obj_id = int(obj_num)

		user = return_thing_by_id(user_id, "Users")
		logging.warning(verify)
		user_hash = gen_verify_hash(user)
		logging.warning(user_hash)
		if verify != user_hash:
			logging.warning('someone is attempting to hack a description')
			self.error(400)
			return
		obj = return_thing_by_id(obj_id, "Objects")
		user_is_author = False
		if int(user_id) == obj.author_id:
			user_is_author = True

		if not user:
			logging.error('this is not the user')
			self.error(400)
			return	

		desc_var = self.request.get('description_text')

		if not desc_var:
			logging.error('no desc_var, setting it to None')
			desc_var = None
		#logging.warning('well we got this far')
		
		# Now we know we have one form submission and only one.		
		obj = return_thing_by_id(obj_id, "Objects")
		if obj.description == desc_var:
			logging.warning("No change to description")
			return
		obj.description = desc_var
		# Now escape, and save as markdown text
		escaped_description_text = cgi.escape(desc_var)
		mkd_converted_description = mkd.convert(escaped_description_text)
		obj.markdown = mkd_converted_description
		obj.put()
		memcache.set("Objects_%d" % int(obj_id), [obj])
class AjaxTagEdit(Handler):
	def post(self):
		obj_num = self.request.get("obj_num")
		user_id = self.request.get("user_id")
		if not obj_num and user_id:
			logging.error('something fucked up')
			self.error(400)
			return

		obj_id = int(obj_num)			

		user = return_thing_by_id(user_id, "Users")
		obj = return_thing_by_id(obj_id, "Objects")
		old_tags = obj.tags

		user_is_author = False
		if int(user_id) == obj.author_id:
			user_is_author = True
		
		if not user:
			logging.error('something fucked up')
			self.error(400)
			return
		
		author_tag_str = None
		if user_is_author:
			author_tag_str = self.request.get('author_tags')
		
		public_tag_str = self.request.get('public_tags')

		#logging.warning('well we got this far')
		
		obj = None # reset so obj doesn't reset itself ... maybe unnecessary
		# Now we know we have one form submission and only one.		
		if user_is_author:
			tag_list = author_tag_str.split(', ')
			tag_list = remove_list_duplicates(tag_list)
			tag_list = strip_list_whitespace(tag_list)
			tag_list = remove_unsafe_chars_from_tags(tag_list)
			tag_list.sort()
			if not tag_list:
				tag_list = ["None"]
			obj = return_thing_by_id(obj_id, "Objects")
			#logging.warning(tag_list)
			#logging.warning(obj.author_tags)
			if tag_list == obj.author_tags:
				logging.warning('author tags did not change')
			else:
				obj.author_tags = tag_list
				all_tags = obj.author_tags + obj.public_tags
				all_tags = remove_list_duplicates(all_tags)
				all_tags.sort()
				if "None" in all_tags:
					all_tags.remove("None")
				obj.tags = all_tags
				obj.put()
				memcache.set("Objects_%d" % int(obj_id), [obj])
				tag_list = None
		# public tag string section
		logging.warning(public_tag_str)
		tag_list = public_tag_str.split(', ')
		logging.warning(tag_list)
		tag_list = remove_list_duplicates(tag_list)
		logging.warning(tag_list)
		tag_list = strip_list_whitespace(tag_list)
		tag_list = remove_unsafe_chars_from_tags(tag_list)
		tag_list.sort()
		if not tag_list:
			tag_list = ["None"]
			logging.warning("public tag list set to None")
		if not obj:
			obj = return_thing_by_id(obj_id, "Objects")
		#logging.warning(tag_list)
		#logging.warning(obj.public_tags)
		if tag_list == obj.public_tags:
			logging.warning('public tags did not change')
		else:
			obj.public_tags = tag_list
			all_tags = obj.author_tags + obj.public_tags
			all_tags = remove_list_duplicates(all_tags)
			all_tags.sort()
			if "None" in all_tags:
				all_tags.remove("None")
			obj.tags = all_tags
			obj.put()
			memcache.set("Objects_%d" % int(obj_id), [obj])
			if int(user_id) == obj.author_id:
				pass
			else:
				username = user.username
				new_note(obj.author_id, 
						"NA| |%s| <a href='/user/%s'>%s</a> edited the public tags on <a href='/obj/%s'>%s</a>" % (
						str(time.time()),
											str(user_id),
												str(cgi.escape(username)),
																					str(obj_id),
																						str(cgi.escape(obj.title))),
						)
			#taskqueue.add(url ='/tagupdateworker', 
			#			  countdown = 6
			#			 )
		eliminated_tags = []
		for tag in obj.tags:
			if tag not in old_tags:
				store_page_cache_kids(tag, update=True) # tag page
				store_page_cache_sfw(tag, update=True) # tag page
				store_page_cache_nsfw(tag, update=True) # tag page
		for tag in old_tags:
			if tag not in obj.tags:
				eliminated_tags.append(tag)
		if eliminated_tags:
			logging.warning('updating eliminated tag search pages, sleep 6')
			time.sleep(6)
			for tag in eliminated_tags:
				store_page_cache_kids(tag, update=True) # tag page
				store_page_cache_sfw(tag, update=True) # tag page
				store_page_cache_nsfw(tag, update=True) # tag page
class ObjectImgUpload(ObjectUploadHandler):
	def post(self):
		user_id = self.check_cookie_return_val("user_id")
		username = self.check_cookie_return_val("username")
		if not (user_id and username):
			self.error(400)
			return
		user_id = int(user_id)

		obj_id = self.request.get("obj_id")
		if obj_id:
			obj_id = int(obj_id)
		obj = return_thing_by_id(obj_id, "Objects")
		if obj is None:
			logging.error("Object not found")
			self.error(400)
			return

		rights = self.request.get("rights")
		logging.warning(rights)
		if rights != "yes":
			self.redirect("/obj/%d?file_upload_error=%s" % (obj_id, "Eek, I think you missed the checkbox for uploading photos. You must agree to the terms when uploading photos.")) 
			return


		verify_hash = self.request.get("verify")
		author = return_thing_by_id(obj.author_id, "Users")
		author_hash = hashlib.sha256(author.random_string).hexdigest()
		logging.warning(verify_hash)
		logging.warning(author_hash)

		if verify_hash is None:
			logging.error("No verify hash")
			self.error(400)
			return

		if author_hash != verify_hash:
			logging.error("Someone is trying to hack user img")
			self.error(400)
			return

		if not (user_id and username):
			# should have these cookies even to see the upload html
			self.redirect('/')
			return
		else:
			pass

		# Check for image
		img_upload = None
		img_blob_key = None
		img_url = None

		try:
			img_upload = self.get_uploads()[0]
		except:
			pass

		if img_upload:
			img_url = '/serve_obj/%s' % img_upload.key()
			img_blob_key = str(img_upload.key())
			filename_full = img_upload.filename
			filename = filename_full.split('.')
			logging.warning(filename)
			if filename[-1].lower() not in ['png','jpg','jpeg','bmp']:
				logging.error('not "image" filetype, redirect')
				img_upload.delete()
				self.redirect('/obj/%d?file_upload_error=%s' % (obj_id, "You may only upload an image file of the types: .png, .jpg,.jpeg, .bmp."))
				return
			# size limit
			global MAX_FILE_SIZE_FOR_OBJECTS
			if img_upload.size > MAX_FILE_SIZE_FOR_OBJECTS:
				logging.warning(img_upload)
				logging.warning(img_upload.size)
				img_upload.delete()
				self.redirect("/obj/%d?file_upload_error=%s" % (obj_id, "That image was too large. Our maximum file size is 5MB. We're very sorry, but currently, hosting exceptionally large files is prohibitively expensive for us. Please upload a smaller version, preferably < 1MB.")) 
				return

			logging.warning(img_upload.size)
			if img_upload.size > 100000:
				logging.warning(img_upload)
				logging.warning(img_upload.size)
				resize_ratio = int(100*(float(100000)/float(img_upload.size)))
				logging.warning(resize_ratio)
				# Resize the image
				logging.warning('db query img_upload blobinfo')
				logging.warning(img_upload.key())
				resized = images.Image(blob_key=img_upload)
				resized.horizontal_flip()
				resized.horizontal_flip()
				thumbnail = resized.execute_transforms(output_encoding=images.JPEG, 
													 quality = resize_ratio,
													)
				# Save Resized Image back to blobstore
				new_file = files.blobstore.create(mime_type='image/jpeg',
												  _blobinfo_uploaded_filename=filename_full)
				with files.open(new_file, 'a') as f:
					f.write(thumbnail)
				files.finalize(new_file)
				logging.warning(new_file)
				new_key = files.blobstore.get_blob_key(new_file)   
				# Remove the original image
				img_upload.delete()
				# Reset img_upload variable
				img_upload = blobstore.BlobInfo.get(new_key)
				logging.warning('db query get blobinfo')
				img_url = '/serve_obj/%s' % img_upload.key()
				img_blob_key = str(img_upload.key())
		else:
			pass
		
		## If here, the user will be registered:

		if img_upload:
			the_object = Objects.get_by_id(obj_id)
			logging.warning('db query ObjectImgUpload')
	
			if the_object.main_img_link is None:
				the_object.main_img_link = img_url
				the_object.main_img_blob_key = img_blob_key
				the_object.main_img_filename = str(img_upload.filename)
			elif the_object.img_link_2 is None:
				the_object.img_link_2 = img_url
				the_object.img_blob_key_2 = img_blob_key
				the_object.img_blob_filename_2 = str(img_upload.filename)
			elif the_object.img_link_3 is None:
				the_object.img_link_3 = img_url
				the_object.img_blob_key_3 = img_blob_key
				the_object.img_blob_filename_3 = str(img_upload.filename)
			elif the_object.img_link_4 is None:
				the_object.img_link_4 = img_url
				the_object.img_blob_key_4 = img_blob_key
				the_object.img_blob_filename_4 = str(img_upload.filename)
			elif the_object.img_link_5 is None:
				the_object.img_link_5 = img_url
				the_object.img_blob_key_5 = img_blob_key
				the_object.img_blob_filename_5 = str(img_upload.filename)
			else:
				logging.warning("No available image slots")
				self.error(400)
				return
			the_object.put()

		if img_upload:
			memcache.set("Objects_%s" % str(obj_id), [the_object])
		self.redirect('/obj/%d' % obj_id)
class ObjectImgDelete(Handler):
	def post(self):
		user = self.return_user_if_cookie()
		if user is None:
			logging.error("No cookie when trying to delete a photo")
			self.error(400)
			return
		obj_id = self.request.get("obj_id")
	
		logging.warning(obj_id)
		if obj_id:
			obj_id = int(obj_id)
		else:
			self.error(400)
			return

		obj = return_thing_by_id(obj_id, "Objects")
		if obj is None:
			self.error(400)
			return
		author = return_thing_by_id(obj.author_id, "Users")
		author_hash = gen_verify_hash(author)
		verify_hash = self.request.get("verify") 
		if author_hash != verify_hash:
			logging.error("Someone appears to be trying to hack the site by deleting a photo they shouldn't be able to")
			self.error(400)
			return

		# Okay, security is out of the way, let's delete that photo!
		check = self.request.get("check")
		if check:
			img_url = self.request.get("image_url")
			if img_url is None:
				self.error(400)
				return
			blob_key = None
			if img_url == obj.main_img_link:
				blob_key = obj.main_img_blob_key
				if obj.img_link_2:
					obj.main_img_link = obj.img_link_2
					obj.img_link_2 = None
					obj.main_img_blob_key = obj.img_blob_key_2
					obj.img_blob_key_2 = None
					obj.main_img_filename = obj.img_blob_filename_2
					obj.img_blob_filename_2 = None
				elif obj.img_link_3:
					obj.main_img_link = obj.img_link_3
					obj.img_link_3 = None
					obj.main_img_blob_key = obj.img_blob_key_3
					obj.img_blob_key_3 = None
					obj.main_img_filename = obj.img_blob_filename_3
					obj.img_blob_filename_3 = None
				elif obj.img_link_4:
					obj.main_img_link = obj.img_link_4
					obj.img_link_4 = None
					obj.main_img_blob_key = obj.img_blob_key_4
					obj.img_blob_key_4 = None
					obj.main_img_filename = obj.img_blob_filename_4
					obj.img_blob_filename_4 = None
				elif obj.img_link_5:
					obj.main_img_link = obj.img_link_5
					obj.img_link_5 = None
					obj.main_img_blob_key = obj.img_blob_key_5
					obj.img_blob_key_5 = None
					obj.main_img_filename = obj.img_blob_filename_5
					obj.img_blob_filename_5 = None
				else:
					obj.main_img_link = None
					obj.main_img_blob_key = None
					obj.main_img_filename = None

			elif img_url == obj.img_link_2:
				blob_key = obj.img_blob_key_2
				obj.img_link_2 = None
				obj.img_blob_key_2 = None
				obj.img_blob_filename_2 = None
			elif img_url == obj.img_link_3:
				blob_key = obj.img_blob_key_3
				obj.img_link_3 = None
				obj.img_blob_key_3 = None
				obj.img_blob_filename_3 = None
			elif img_url == obj.img_link_4:
				blob_key = obj.img_blob_key_4
				obj.img_link_4 = None
				obj.img_blob_key_4 = None
				obj.img_blob_filename_4 = None
			elif img_url == obj.img_link_5:
				blob_key = obj.img_blob_key_5
				obj.img_link_5 = None
				obj.img_blob_key_5 = None
				obj.img_blob_filename_5 = None

			if blob_key:
				# deleting obj blob shouldn't actually be necessary anymore
				obj_blob_ref = db.GqlQuery("SELECT * FROM ObjectBlob WHERE obj_id = :1", obj_id)
				logging.warning('db query: deleting obj img from db and blobstore')
				logging.warning(obj_blob_ref)
				if obj_blob_ref:
					obj_blob_ref = list(obj_blob_ref)
					for ref in obj_blob_ref:
						if ref.blob_key == blob_key:
							obj_blob_ref = ref
							break
					logging.warning(obj_blob_ref)
					db.delete(obj_blob_ref)
				blob_key.delete()
				obj.put()
				memcache.set("Objects_%d" % obj_id, [obj])

		self.redirect("/obj/%d" % obj_id)

class ObjectSpecificImgDelete(Handler):
	def post(self):
		obj_id = self.request.get("obj_id")

		print "\n", obj_id, "\n"

		if obj_id:
			next_url = "/obj/%d" % int(obj_id)
		else:
			print "\nNo object id\n"
			self.error(400)
			return

		check = self.request.get("check")
		print check
		if check != "yes":
			self.redirect(next_url)
			return

		user_id = self.request.get("user_id")
		user_hash = self.request.get("user_hash")
		print "\nuser_hash:", user_hash

		user = return_thing_by_id(user_id, "Users")
		if not user:
			print "\nNo user\n"
			self.error(400)
			return
		verify_hash = gen_verify_hash(user)
		print "\nhash_hash: %s" % verify_hash

		if user_hash != verify_hash:
			print "\nNo hash match\n"
			self.error(400)
			return

		# user verified
		allowed_to_delete = False

		user_is_author = False
		obj = return_thing_by_id(obj_id, "Objects")
		author_id = obj.author_id

		if str(user_id) == str(author_id):
			user_is_author = True
			allowed_to_delete = True
		
		photo_id = self.request.get("photo_id")
		if not photo_id:
			print "\nNo photo id\n"
			self.error(400)
			return

		for data in obj.visitor_img_list:
			quad = data.split("|")
			if photo_id == quad[2]:
				img_uploader_id = quad[0]

		if img_uploader_id:
			if user_id == img_uploader_id:
				allowed_to_delete = True

		if not allowed_to_delete:
			print "\nNot allowed to delete\n"
			self.error(400)
			return

		# allowed to delete, now time to delete
		
		# check if visitor photo
		quad_to_delete = None
		count = 0
		for data in obj.visitor_img_list:
			quad = data.split("|")
			if photo_id == quad[2]:
				#delete
				quad_to_delete = quad
				quad_to_delete_position = count
			count += 1
		if quad_to_delete:
			# delete photo
			obj.visitor_img_list.pop(quad_to_delete_position)
			blob_key = quad_to_delete[3]
			blob_key = str(blob_key)
			print "\nblob key:", blob_key
			print "\ntype:", type(blob_key)
			print ""
			if blob_key:
				blob_key = blobstore.BlobInfo.get(blob_key)
				print "\n", blob_key
				print "\ntype:", type(blob_key)
				# deleting obj blob shouldn't actually be necessary anymore
				obj_blob_ref = db.GqlQuery("SELECT * FROM ObjectBlob WHERE obj_id = :1", obj_id)
				logging.warning('db query: deleting obj img from db and blobstore')
				logging.warning(obj_blob_ref)
				if obj_blob_ref:
					obj_blob_ref = list(obj_blob_ref)
					for ref in obj_blob_ref:
						if ref.blob_key == blob_key:
							obj_blob_ref = ref
							break
					logging.warning(obj_blob_ref)
					db.delete(obj_blob_ref)
				### above should not actually be necessary anymore
				blob_key.delete()
				obj.put()
				memcache.set("Objects_%s" % obj_id, [obj])

			# delete user's reference to this object in img list
			#print "\n", user.imgs_on_others_objects
			#print ""
			for obj_ref in user.imgs_on_others_objects:
				if str(obj_ref) == str(obj_id):
					user.imgs_on_others_objects.remove(obj_ref)
					#print "\nRemoving:", obj_ref
			
			#print "\n", user.imgs_on_others_objects
			#print ""
			user.put()
			memcache.set("Users_%s" % user_id, [user])

		self.redirect(next_url)
		return

class ObjectAltFile(Handler):
	def render_page(self, obj_num):
		obj_id = int(obj_num)
		file_upload_url = blobstore.create_upload_url("/altfileupload/")

		user = self.return_user_if_cookie()
		if not user:
			self.redirect('/obj/%d' % obj_id)
		obj = return_thing_by_id(obj_id, "Objects")
		if not obj:
			self.error(404)
			return
		elif obj.obj_type != "upload":
			self.error(400)
			self.redirect('/obj/%d' % obj_id)
			return
		if user.key().id() != obj.author_id:
			logging.warning('user %d is attempting to edit object %d' %(user.key().id(), obj_id))
			self.redirect('/obj/%d' % obj_id)
			return

		redirect = self.request.get("redirect")
		error = None
		if redirect:
			if redirect == "filetype":
				error = self.request.get("file_type_error")



		user_hash = gen_verify_hash(user)

		self.render('altfile.html', 
					file_upload_url = file_upload_url,
					user = user,
					obj = obj,
					user_hash = user_hash,
					error = error,
					)



	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)

	def post(self, obj_num):
		obj_id = int(obj_num)
		obj = return_thing_by_id(obj_id, "Objects")
		if not obj:
			self.error(400)
			return
		elif obj.obj_type != "upload":
			self.error(400)
			self.redirect('/obj/%d' % obj_id)
			return
		user = self.return_user_if_cookie()
		if not user:
			self.redirect('/obj/%d' % obj_id)
			return
		if user.key().id() != obj.author_id:
			self.redirect('/obj/%d' % obj_id)
			return

		file_2 = self.request.get('file_2')
		file_3 = self.request.get('file_3')
		file_4 = self.request.get('file_4')
		file_5 = self.request.get('file_5')
		file_6 = self.request.get('file_6')
		file_7 = self.request.get('file_7')
		file_8 = self.request.get('file_8')
		file_9 = self.request.get('file_9')
		file_10 = self.request.get('file_10')
		file_11 = self.request.get('file_11')
		file_12 = self.request.get('file_12')
		file_13 = self.request.get('file_13')
		file_14 = self.request.get('file_14')
		file_15 = self.request.get('file_15')
		files_to_delete = [file_2, file_3, file_4, file_5, file_6, file_7, file_8, file_9, file_10, file_11, file_12, file_13, file_14, file_15]

		if file_2:
			blob = obj.file_blob_key_2
			blob.delete()
			obj.file_link_2 = None
			obj.file_blob_filename_2 = None
		if file_3:
			blob = obj.file_blob_key_3
			blob.delete()
			obj.file_link_3 = None
			obj.file_blob_filename_3 = None
		if file_4:
			blob = obj.file_blob_key_4
			blob.delete()
			obj.file_link_4 = None
			obj.file_blob_filename_4 = None
		if file_5:
			blob = obj.file_blob_key_5
			blob.delete()
			obj.file_link_5 = None
			obj.file_blob_filename_5 = None
		if file_6:
			blob = obj.file_blob_key_6
			blob.delete()
			obj.file_link_6 = None
			obj.file_blob_filename_6 = None
		if file_7:
			blob = obj.file_blob_key_7
			blob.delete()
			obj.file_link_7 = None
			obj.file_blob_filename_7 = None
		if file_8:
			blob = obj.file_blob_key_8
			blob.delete()
			obj.file_link_8 = None
			obj.file_blob_filename_8 = None
		if file_9:
			blob = obj.file_blob_key_9
			blob.delete()
			obj.file_link_9 = None
			obj.file_blob_filename_9 = None
		if file_10:
			blob = obj.file_blob_key_10
			blob.delete()
			obj.file_link_10 = None
			obj.file_blob_filename_10 = None
		if file_11:
			blob = obj.file_blob_key_11
			blob.delete()
			obj.file_link_11 = None
			obj.file_blob_filename_11 = None
		if file_12:
			blob = obj.file_blob_key_12
			blob.delete()
			obj.file_link_12 = None
			obj.file_blob_filename_12 = None
		if file_13:
			blob = obj.file_blob_key_13
			blob.delete()
			obj.file_link_13 = None
			obj.file_blob_filename_13 = None
		if file_14:
			blob = obj.file_blob_key_14
			blob.delete()
			obj.file_link_14 = None
			obj.file_blob_filename_14 = None
		if file_15:
			blob = obj.file_blob_key_15
			blob.delete()
			obj.file_link_15 = None
			obj.file_blob_filename_15 = None			
		memcache.set("Objects_%d" % obj_id, [obj])
		obj.put()
		self.redirect("/altfile/%d" % obj_id)
# ALLOWED_ALTERNATE_FILE_EXTENTIONS = ['stl', 'scad']
class ObjectAltFileUpload(ObjectUploadHandler):
	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			self.redirect("/login")
			return

		# User is signed in
		user_id = int(user_var)
		user = return_thing_by_id(user_id, "Users")
		trusted_user = False
		if user.username in TRUSTED_USERS:
			trusted_user = True

		verify_hash = self.request.get("verify")
		user_hash = "This string is not valid but not None"
		if user:
			user_hash = gen_verify_hash(user)
		logging.warning(verify_hash)
		logging.warning(user_hash)

		if verify_hash is None:
			logging.error("No verify hash")
			self.error(400)
			return

		if user_hash != verify_hash:
			logging.error("Someone is trying to hack user img")
			self.error(400)
			return

		obj_id = self.request.get("obj_id")
		if obj_id:
			obj_id = int(obj_id)
		else:
			self.error(400)
			return

		main_file_var = self.request.get("file")
		logging.warning(main_file_var)
		rights = self.request.get("rights")
		if not (main_file_var and rights):
			logging.warning('something went wrong')
			if not main_file_var:

				self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (
				obj_id, 
				"It appears you have not submitted a file for upload."
				)) # this should return to an error version of the upload page
			else:
				self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (
				obj_id, 
				"You must confirm your agreement with the license and terms."
				)) # this should return to an error version of the upload page
			return				

		# Success
		# try:
		if 1==1:
			file_data = None
			file_blob_key = None
			file_url = None

			# this is a problem:
			# if only one file is uploaded, it will default to img...
			# hmm... how to fix

			try:
				file_data = self.get_uploads()[0]
			except:
				pass

			if file_data:
				# size limit
				global MAX_FILE_SIZE_FOR_OBJECTS
				if not trusted_user: # trusted users can upload larger files
					if file_data.size > MAX_FILE_SIZE_FOR_OBJECTS:
						logging.warning(file_data)
						logging.warning(file_data.size)
						file_data.delete()
						self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (obj_id, "Unfortunately, this file is too large. We have a maximum file size of 5mb. Hosting large files is prohibitively expensive for us, if you need to host a larger file, please link to it instead.")) # this should return to an error version of the upload page
						return

				file_url = '/serve_obj/%s' % file_data.key()
				file_blob_key = file_data.key()
				filename = file_data.filename
				filename = filename.split('.')
				logging.warning(filename)
				global ALLOWED_ALTERNATE_FILE_EXTENTIONS
				if filename[-1].lower() not in ALLOWED_ALTERNATE_FILE_EXTENTIONS:
					logging.warning('disallowed filetype, redirect')
					file_data.delete()
					self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (obj_id, "That file was not an allowed filetype.")) # this should return to an error version of the upload page
					return
				if not trusted_user: # trusted users can upload binaries
					if filename[-1].lower() == "stl" and not is_ascii_stl(file_data):
						logging.warning('stl does not parse, redirect')
						file_data.delete()
						self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (obj_id, "That file did not seem to be a proper ascii .stl or it may be corrupt. If the problem persists, and you believe this is an acceptable ascii .stl file, please contact us.")) # this should return to an error version of the upload page
						return				


				### this section should parse the file type
				#if not is_ascii_stl(file_data):
				#	logging.warning('not "ascii stl" after parse, redirect')
				#	file_data.delete()
				#	self.redirect("/altfileupload?redirect=filetype&file_type_error=%s" % "This file must be a ascii stereo lithography filetype (.stl). We had a problem parsing your file. It may be binary, or not actually an ascii stl filetype.") # this should return to an error version of the upload page
				#	return
			else:
				self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (obj_id, "Your file upload appears to have failed. Please try again. If the problem persists please contact us.")) # this should return to an error version of the upload page
				return


			if file_data:
				the_object = Objects.get_by_id(obj_id)
				if not the_object:
					self.error(400)
					return
				logging.warning('db query ObjectAltFileUpload')
		
				if the_object.file_link_2 is None:
					the_object.file_link_2 = file_url
					the_object.file_blob_key_2 = file_blob_key
					the_object.file_blob_filename_2 = str(file_data.filename)
				elif the_object.file_link_3 is None:
					the_object.file_link_3 = file_url
					the_object.file_blob_key_3 = file_blob_key
					the_object.file_blob_filename_3 = str(file_data.filename)
				elif the_object.file_link_4 is None:
					the_object.file_link_4 = file_url
					the_object.file_blob_key_4 = file_blob_key
					the_object.file_blob_filename_4 = str(file_data.filename)
				elif the_object.file_link_5 is None:
					the_object.file_link_5 = file_url
					the_object.file_blob_key_5 = file_blob_key
					the_object.file_blob_filename_5 = str(file_data.filename)
				elif the_object.file_link_5 is None:
					the_object.file_link_5 = file_url
					the_object.file_blob_key_5 = file_blob_key
					the_object.file_blob_filename_5 = str(file_data.filename)
				elif the_object.file_link_6 is None:
					the_object.file_link_6 = file_url
					the_object.file_blob_key_6 = file_blob_key
					the_object.file_blob_filename_6 = str(file_data.filename)
				elif the_object.file_link_7 is None:
					the_object.file_link_7 = file_url
					the_object.file_blob_key_7 = file_blob_key
					the_object.file_blob_filename_7 = str(file_data.filename)
				elif the_object.file_link_8 is None:
					the_object.file_link_8 = file_url
					the_object.file_blob_key_8 = file_blob_key
					the_object.file_blob_filename_8 = str(file_data.filename)
				elif the_object.file_link_9 is None:
					the_object.file_link_9 = file_url
					the_object.file_blob_key_9 = file_blob_key
					the_object.file_blob_filename_9 = str(file_data.filename)
				elif the_object.file_link_10 is None:
					the_object.file_link_10 = file_url
					the_object.file_blob_key_10 = file_blob_key
					the_object.file_blob_filename_10 = str(file_data.filename)
				elif the_object.file_link_11 is None:
					the_object.file_link_11 = file_url
					the_object.file_blob_key_11 = file_blob_key
					the_object.file_blob_filename_11 = str(file_data.filename)
				elif the_object.file_link_12 is None:
					the_object.file_link_12 = file_url
					the_object.file_blob_key_12 = file_blob_key
					the_object.file_blob_filename_12 = str(file_data.filename)
				elif the_object.file_link_13 is None:
					the_object.file_link_13 = file_url
					the_object.file_blob_key_13 = file_blob_key
					the_object.file_blob_filename_13 = str(file_data.filename)
				elif the_object.file_link_14 is None:
					the_object.file_link_14 = file_url
					the_object.file_blob_key_14 = file_blob_key
					the_object.file_blob_filename_14 = str(file_data.filename)
				elif the_object.file_link_15 is None:
					the_object.file_link_15 = file_url
					the_object.file_blob_key_15 = file_blob_key
					the_object.file_blob_filename_15 = str(file_data.filename)										
				else:
					logging.warning("No available image slots")
					self.redirect("/altfile/%d?redirect=filetype&file_type_error=%s" % (
						obj_id, 
						"There are too many files uploaded already. You must delete some."
						)) # this should return to an error version of the upload page
					return
				the_object.put()

			if file_data:
				memcache.set("Objects_%s" % str(obj_id), [the_object])
			self.redirect('/obj/%d' % obj_id)

		#except:
		else:
			self.redirect('/upload_failure.html')
class VisitorImgUpload(ObjectUploadHandler):
	def post(self):
		logging.warning("Here we go!")
		user_id = self.check_cookie_return_val("user_id")
		username = self.check_cookie_return_val("username")
		if not (user_id and username):
			self.error(400)
			return
		user_id = int(user_id)
		user = return_thing_by_id(user_id, "Users")
		if user is None:
			self.error(400)
			logging.warning("no user???")
			return

		rights = self.request.get("rights")
		logging.warning(rights)
		if rights != "yes":
			self.error(400)
			logging.warning("no rights!")
			return
		obj_id = self.request.get("obj_id")
		if obj_id:
			obj_id = int(obj_id)
		obj = return_thing_by_id(obj_id, "Objects")
		if obj is None:
			logging.error("Object not found")
			self.error(400)
			return

		verify_hash = self.request.get("verify")
		visitor = return_thing_by_id(user_id, "Users")
		visitor_hash = "This string is not valid but not None"
		if visitor:
			visitor_hash = gen_verify_hash(visitor)
		logging.warning(verify_hash)
		logging.warning(visitor_hash)

		if verify_hash is None:
			logging.error("No verify hash")
			self.error(400)
			return

		if visitor_hash != verify_hash:
			logging.error("Someone is trying to hack user img")
			self.error(400)
			return

		if not (user_id and username):
			# should have these cookies even to see the upload html
			self.error(400)
			return

		# Check for image
		img_upload = None
		img_blob_key = None
		img_url = None

		try:
			img_upload = self.get_uploads()[0]
		except:
			pass

		if img_upload:
			img_url = '/serve_obj/%s' % img_upload.key()
			img_blob_key = str(img_upload.key())
			filename_full = img_upload.filename
			filename = filename_full.split('.')
			logging.warning(filename)
			if filename[-1].lower() not in ['png','jpg','jpeg','bmp']:
				logging.error('not "image" filetype, redirect')
				img_upload.delete()
				self.redirect('/obj/%d?file_upload_error=%s' % (obj_id, "You may only upload an image file of the types: .png, .jpg,.jpeg, .bmp."))
				return

			# size limit
			global MAX_FILE_SIZE_FOR_OBJECTS
			if img_upload.size > MAX_FILE_SIZE_FOR_OBJECTS:
				logging.warning(img_upload)
				logging.warning(img_upload.size)
				img_upload.delete()
				self.redirect("/obj/%d?file_upload_error=%s" % (obj_id, "That image was too large. Our maximum file size is 5MB. We're very sorry, but currently, hosting exceptionally large files is prohibitively expensive for us. Please upload a smaller version, preferably < 1MB.")) 
				return

			logging.warning(img_upload.size)
			if img_upload.size > 100000:
				logging.warning(img_upload)
				logging.warning(img_upload.size)
				resize_ratio = int(100*(float(100000)/float(img_upload.size)))
				logging.warning(resize_ratio)
				# Resize the image
				logging.warning('db query img_upload blobinfo')
				logging.warning(img_upload.key())
				resized = images.Image(blob_key=img_upload)
				resized.horizontal_flip()
				resized.horizontal_flip()
				thumbnail = resized.execute_transforms(output_encoding=images.JPEG, 
													 quality = resize_ratio,
													)
				# Save Resized Image back to blobstore
				new_file = files.blobstore.create(mime_type='image/jpeg',
												  _blobinfo_uploaded_filename=filename_full)
				with files.open(new_file, 'a') as f:
					f.write(thumbnail)
				files.finalize(new_file)
				logging.warning(new_file)
				new_key = files.blobstore.get_blob_key(new_file)   
				# Remove the original image
				img_upload.delete()
				# Reset img_upload variable
				img_upload = blobstore.BlobInfo.get(new_key)
				logging.warning('db query get blobinfo')
				img_url = '/serve_obj/%s' % img_upload.key()
				img_blob_key = str(img_upload.key())
		else:
			pass
		
		## If here, the user will be registered:

		if img_upload:
			the_object = Objects.get_by_id(obj_id)
			logging.warning('db query ObjectImgUpload')
	
			visitor_has_already_submitted_img = False
			counter = 0
			for a_tuple in the_object.visitor_img_list:
				if a_tuple != "None":
					tuple_copy = a_tuple.split("|")
					logging.warning(str(user_id))
					logging.warning(tuple_copy)
					if str(user_id) == str(tuple_copy[0]):
						visitor_has_already_submitted_img = True
						break
					else:
						counter += 1
				else: 
					# list is None
					break
			logging.warning(visitor_has_already_submitted_img)
			if visitor_has_already_submitted_img:
				old_blob_key = the_object.visitor_img_list[counter].split("|")[3]
				old_blob_key = blobstore.BlobKey(old_blob_key)
				logging.warning(old_blob_key)
				old_blob_info = blobstore.BlobInfo.get(old_blob_key)
				logging.warning(old_blob_info)
				obj_blob_ref = db.GqlQuery("SELECT * FROM ObjectBlob WHERE obj_id = :1", obj_id)
				logging.warning('db query: deleting obj img from db and blobstore')
				logging.warning(obj_blob_ref)
				if obj_blob_ref:
					obj_blob_ref = list(obj_blob_ref)
					for ref in obj_blob_ref:
						if ref.blob_key == old_blob_key:
							obj_blob_ref = ref
							break
					logging.warning(obj_blob_ref)
					db.delete(obj_blob_ref)
				if old_blob_info:
					old_blob_info.delete()
				else:
					logging.error("Broken")


				logging.warning('counter')
				logging.warning(counter)
				logging.warning(the_object.visitor_img_list)
				the_object.visitor_img_list[counter] = "%s|%s|%s|%s|" % (user_id, username, img_url, img_blob_key)
				logging.warning(the_object.visitor_img_list)

			else:
				# visitor has NOT already submitted an img
				if "None" in the_object.visitor_img_list:
					the_object.visitors_img_list.remove("None")
				the_object.visitor_img_list.append("%s|%s|%s|%s" % (user_id, username, img_url, img_blob_key))

			the_object.put()

		if img_upload:
			new_object_photo = ObjectBlob(blob_type = 'image',
										obj_id = int(the_object.key().id()),
										uploader = int(the_object.key().id()),
										blob_key = img_upload.key(),
										filename = str(img_upload.filename),

										key_name = "blob|%s" % str(img_upload.key())
										)
											
			new_object_photo.put()
			memcache.set("objectblob|%s" % str(new_object_photo.blob_key), new_object_photo)
		else:
			pass

		#This is only for current front page, if front page no longer has users, then remove this line
		if img_upload:
			if "None" in user.imgs_on_others_objects:
				user.imgs_on_others_objects.remove("None")
			user.imgs_on_others_objects.append(str(obj_id))
			user.put()
			logging.warning("Successfully created visitor img")
			memcache.set("Objects_%s" % str(obj_id), [the_object])
			memcache.set("Users_%s" % str(user_id), [user])
		self.redirect('/obj/%d' % obj_id)

class ObjectJSON(Handler):
	def get(self, obj_num):
		obj_id = int(obj_num.split('.')[0])
		obj = return_thing_by_id(obj_id, "Objects")
		if not obj:
			self.inline_404()
			return

		if obj.obj_type != "upload":
			self.inline_404()
			return
		elif obj.deleted == True or obj.under_review == True:
			self.inline_404()
			return
		global page_url
		obj_url = page_url + "/obj/%d" % obj_id
		author_url = page_url + "/user/%d" % obj.author_id
		
		obj_author = obj.author_name
		if obj.original_creator:
			obj_author = obj.original_creator
		
		thumbnail_urls = []
		if obj.main_img_link:
			thumbnail_urls.append(page_url + obj.main_img_link)
		if obj.img_link_2:
			thumbnail_urls.append(page_url + obj.img_link_2)
		if obj.img_link_3:
			thumbnail_urls.append(page_url + obj.img_link_3)
		if obj.img_link_4:
			thumbnail_urls.append(page_url + obj.img_link_4)
		if obj.img_link_5:
			thumbnail_urls.append(page_url + obj.img_link_5)

		obj_description = ""
		if obj.description:
			obj_description = obj.description

		obj_filename = ""
		if obj.stl_filename:
			obj_filename = obj.stl_filename
		obj_file_url = ""
		if obj.stl_file_link:
			obj_file_url = page_url + obj.stl_file_link
		
		# write logic here for other mimetypes
		mimetype = ""
		if obj.stl_filename:
			mimetype = "application/sla"
		
		json_obj = {
			"uuid":obj.uuid,
			"title":obj.title,
			"url":obj_url,
			"authors":[
				{
					"name" : obj_author,
					"url" : author_url
				}
			],
			"licenses":[
				obj.license
			],
			"tags":[
				tag for tag in obj.tags
			],
			"thumbnail-urls": thumbnail_urls,
			"description": obj_description,
			"bill-of-materials":[
				{
					"description": obj_filename,
					"url": obj_file_url,
					"mimetype": mimetype,
				}
			]
		}

		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(json.dumps(json_obj))

class ObjDelPage(Handler):
	def render_page(self, obj_num, error=""):

		# should add a hash to this page to better protect the form
		
		obj_id = int(obj_num)
		the_obj = object_page_cache(obj_id)
		the_comments = obj_comment_cache(obj_id)

		user_id = int(self.check_cookie_return_val("user_id"))
		if the_obj.author_id != user_id:
			# User is not authorized to delete
			self.redirect('/obj/%d' % obj_id)
		else:
			# User is object author
			pass

		okay_for_kids = the_obj.okay_for_kids
		if okay_for_kids != True:
			over18 = self.check_cookie_return_val("over18")
			if over18 != "True":
				self.redirect('/')
			else:
				pass
		else:
			pass

		title_var = the_obj.title
		author_name_var = the_obj.author_name
		author_id_var = the_obj.author_id
		created_var = the_obj.created
		epoch_var = the_obj.epoch
		obj_type_var = the_obj.obj_type

		file1_var = the_obj.stl_file_link
		img1_var = the_obj.main_img_link
		license_var = the_obj.license
		obj_link_var = the_obj.obj_link

		description_var = the_obj.description
		tag_var = the_obj.tags
		ups = the_obj.upvotes
		downs = the_obj.downvotes
		net = the_obj.netvotes
		hot = the_obj.hotness_var
		rating = the_obj.rating
		total_ratings = the_obj.total_ratings
		file2 = the_obj.other_file1_link
		img2 = the_obj.other_img1_link
		
		self.render('deleteobjectpage.html', 
					obj_id = obj_id,
					the_comments = the_comments,
					error = error,

					title = title_var,
					author_name = author_name_var,
					author_id = author_id_var,
					obj_type = obj_type_var,
					created = created_var,
					epoch = epoch_var,

					file1 = file1_var,
					img1 = img1_var,
					license = license_var,
					obj_link = obj_link_var,

					description = description_var,
					tags = tag_var,
					ups = ups,
					downs = downs,
					net = net,
					hot = hot,
					rating = rating,
					total_ratings = total_ratings,
					file2 = file2,
					img2 = img2)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)

	
	def post(self, obj_num):
		obj_id = int(obj_num)
		the_obj = object_page_cache(obj_id)
		news_var = the_obj.news
		learn_var = the_obj.learn

		user_id = int(self.check_cookie_return_val("user_id"))
		if the_obj.author_id != user_id:
			# User is not authorized to delete
			self.redirect('/obj/%d' % obj_id)
		else:
			# User is object author
			pass

		delete_var = self.request.get("delete")
		if not delete_var:
			# Do not delete
			self.redirect('/obj/%d' % obj_id)
		else:
			# delete object function
			delete_obj(obj_id)
			if news_var == True:
				self.redirect('/news')
			elif learn_var == True:
				self.redirect('/university')
			else:
				self.redirect('/')

class UserPage(Handler):
	def render_page(self, user_num, page_num, error=""):
		user = self.return_user_if_cookie()
		photo_upload_url = blobstore.create_upload_url('/user_page_img_upload')

		userpage_id = int(user_num)
		the_user = return_thing_by_id(userpage_id, "Users")
		has_cookie = self.return_has_cookie()

		if not the_user:
			self.error(404)
		else:
			over18 = self.check_cookie_return_val("over18")
			user_id = self.check_cookie_return_val("user_id")

			# the list will be the list of all content created by this user
			the_list = []
			if over18 != "True":
				# under 18 or no cookie
				the_list = user_page_obj_com_cache_kids(userpage_id)
			else:
				# over 18
				the_list = user_page_obj_com_cache(userpage_id)



			page_num = int(page_num)
			next_page_num = page_num + 1
			number_of_items_to_fetch = 30

			# this is for using the object list style of page loading, which we are currently using for the index page
			the_list = the_list[( (page_num -1) * number_of_items_to_fetch) : (page_num * number_of_items_to_fetch)]	

			print the_list
			if the_list:
				end_of_content = False
			else:
				end_of_content = True
			print end_of_content

			the_list = masonry_format_for_userpage(the_list, user_id)



			for com in the_list:
				#logging.warning(type(com))
				#logging.warning(isinstance(com, dict))
				if not isinstance(com, dict):
					com.time_since = time_since_creation(com.epoch)

			user_is_user = False
			logged_in = None
			if user_id:
				user_id = int(user_id)
				logged_in = "This guy is logged in"
			else:
				pass
			if the_user.key().id() == user_id:
				# User is object author
				user_is_user = True
			else:
				pass

			img = the_user.main_img_link

			user_since = time_since_creation(the_user.epoch)

			user_hash = None
			if user:
				user_hash = hashlib.sha256(user.random_string).hexdigest()
			has_cookie = self.return_has_cookie()

			is_blocked = None
			is_followed = None
			if user:
				if str(user.key().id()) in the_user.blocked_by_list:
					is_blocked = "Nobody likes this guy!"
				if str(user.key().id()) in the_user.follower_list:
					is_followed = "This guy is your friend!"
					logging.warning(is_followed)

			logging.warning(img)

			self.render('userpage.html', 
						error=error,
						has_cookie = has_cookie,
						user = user,
						user_hash = user_hash,
						# userpage user is the_user
						the_user = the_user,
						is_blocked = is_blocked,
						is_followed = is_followed,

						the_list = the_list,
						user_id = user_id,
						user_since = user_since,

						userpage_id = userpage_id,
						user_is_user = user_is_user,
						logged_in = logged_in,
						
						img = img,

						next_page_num = next_page_num,
						end_of_content = end_of_content,

						photo_upload_url = photo_upload_url)
	def get(self, user_num, page_num="1"):
		user_id = int(user_num)
		self.render_page(user_num=user_id, page_num = page_num)
class SendMessageHandler(Handler):	# This was part of UserPage, but seperated it to make it stop redirecting.
	def post(self): #, user_num):
		message = self.request.get("message")
		userpage_id = self.request.get("userpage_num") #int(user_num)
		if not userpage_id:
			logging.error('userpage_num was None')
			self.error(400)
			return
		userpage_id = int(userpage_id)
		
		if not message:
			user_id = self.check_cookie_return_val("user_id")
			logged_in = None
			if user_id:
				logged_in = "Troy and Abed in the Morning!"
			the_user = user_page_cache(userpage_id)
			username_var = the_user.username
			created_var = the_user.created
			img = the_user.main_img_link
			summary = the_user.summary
			location = the_user.location
			printer = the_user.printer
			slicer = the_user.slicer
			software = the_user.software

			user_is_user = False
			if the_user.key().id() == user_id:
				# User is object author
				user_is_user = True
			over18 = self.check_cookie_return_val("over18")
			the_list = []
			if over18 != "True":
				# under 18 or no cookie
				the_list = user_page_obj_com_cache_kids(userpage_id)
			else:
				# over 18
				the_list = user_page_obj_com_cache(userpage_id)
			photo_upload_url = blobstore.create_upload_url('/user_page_img_upload')
			error = "Oops, it appears you've sent an empty message"
			self.render('userpage.html', 
						error=error,
						username=username_var, 
						created=created_var, 
						the_list = the_list,
						user_id = user_id,
						userpage_id = userpage_id,
						user_is_user = user_is_user,
						logged_in = logged_in,
						img = img,
						summary = summary,
						location = location,
						printer = printer,
						slicer = slicer,
						software = software,
						photo_upload_url = photo_upload_url
						)
		else:
			recipient = user_page_cache(userpage_id)
			sender_id = int(self.check_cookie_return_val("user_id"))
			sender_username = self.check_cookie_return_val("username")
			sender = return_thing_by_id(sender_id, "Users")

			if str(recipient.key().id()) in sender.blocked_by_list:
				# user is blocked
				logging.warning('blockee attempting to message blocker')
				# fake the 6 second sleep
				time.sleep(6)
				self.redirect("/user/%d" % recipient.key().id())
				return
			# else message is welcome
			new_message = Messages(epoch = float(time.time()),
									text = message,
									author_id = sender_id,
									author_name = sender_username,
									recipient_id = recipient.key().id(),
									recipient_name = recipient.username,
									)
			new_message.put()
			logging.warning('new message -- write')
			taskqueue.add(url ='/newmessageworker', 
						  params = {'recipient_id' : recipient.key().id(),
						  			'sender_id' : sender_id
						  		   },
						  countdown = 6
						 )
			#user_messages_cache(recipient.key().id(), update=True, delay = 6)
			#user_messages_cache(sender_id, update=True)
			new_note(recipient.key().id(),
					"Messages|%d|%s| <a href='/user/%s'>%s</a> has sent you a <a href='/user/messages/%s'>message</a>" % (
							int(new_message.key().id()),
								str(time.time()),
													str(sender_id),
														str(cgi.escape(sender_username)),
																									str(recipient.key().id()))
								)
			#self.redirect("/user/%d" % recipient.key().id())
class NewMessageWorker(Handler):
	def post(self):
		recipient_id = int(self.request.get('recipient_id'))
		sender_id = int(self.request.get('sender_id'))
		user_messages_cache(recipient_id, update=True)
		user_messages_cache(sender_id, update=True)
		#for i in range(10):
		#	logging.warning("Our first timesaver!")
class UserPrintshelf(Handler):
	def render_page(self, user_num):
		user_id = int(user_num)
		visitor_id = self.check_cookie_return_val('user_id')
		if visitor_id:
			visitor_id = int(visitor_id)
		#user is the term for visitor for header.html
		user = return_thing_by_id(visitor_id, "Users")
		the_user = return_thing_by_id(user_id, "Users")
		if the_user is None:
			self.inline_404()
			return
		visitor_is_user = None
		if user_id == visitor_id:
			visitor_is_user = True

		to_print_list_exists = None
		has_printed_list_exists = None
		if len(the_user.to_print_list) > 0:
			if len(the_user.to_print_list) == 1:
				if the_user.to_print_list[0] == "None":
					pass
				else:
					to_print_list_exists = "One object?!?!"
			else:
				to_print_list_exists = "Hey, this guy right here has hopes and dreams!"
		logging.info("to print list")
		logging.info(to_print_list_exists)
		if len(the_user.has_printed_list) > 0:
			if len(the_user.has_printed_list) == 1:
				if the_user.has_printed_list[0] == "None":
					pass
				else:
					has_printed_list_exists = "Printed one object. Hell, yea!"
			else:			
				has_printed_list_exists = "I print, therefore, I am."
		to_print_obj_list = []
		if to_print_list_exists:
			for i in the_user.to_print_list:
				if i.isdigit():
					to_print_obj_list.append(return_thing_by_id(int(i),"Objects"))
		has_printed_obj_list = []
		if has_printed_list_exists:
			for i in the_user.has_printed_list:
				if i.isdigit():
					has_printed_obj_list.append(return_thing_by_id(int(i),"Objects"))

		logging.warning(the_user.to_print_list)
		logging.warning(to_print_obj_list)
		logging.warning(the_user.has_printed_list)
		logging.warning(has_printed_obj_list)

		self.render("user_printshelf.html",
					user = user,
					visitor_is_user = visitor_is_user,
					the_user = the_user,
					to_print_list_exists = to_print_list_exists,
					has_printed_list_exists = has_printed_list_exists,
					to_print_obj_list = to_print_obj_list,
					has_printed_obj_list = has_printed_obj_list,
					)

	def get(self, user_num):
		user_id = int(user_num)
		self.render_page(user_num=user_id)
class UserMessagePage(Handler):
	def render_page(self, user_num):
		userpage_id = int(user_num)
		visitor_id = self.check_cookie_return_val('user_id')
		if visitor_id:
			visitor_id = int(visitor_id)
		else:
			self.redirect('/user/%d' % userpage_id)
			return			
		user = self.return_user_if_cookie()
		if userpage_id != visitor_id:
			logging.warning(userpage_id + " , " + visitor_id)
			self.redirect('/user/%d' % userpage_id)
		else:
			the_user = user_page_cache(userpage_id)
			message_list = user_messages_cache(userpage_id)
			are_messages = None
			if message_list:
				if len(message_list) > 0:
					are_messages = "Look at this douchebag ---- Hey, we get it, you're soooo popular!"
				for message in message_list:
					if str(message.author_id) in the_user.block_list:
						message.text = "You have blocked this user's content."
			self.render("usermessages.html",
						are_messages = are_messages,
						the_user = the_user,
						message_list = message_list,
						user=user,
						)

	def get(self, user_num):
		user_id = int(user_num)
		self.render_page(user_num=user_id)
class UserNotePage(Handler):
	def render_page(self, user_num, error=""):
		user_id = int(user_num)
		user = self.return_user_if_cookie()
		has_cookie = self.return_has_cookie()

		if not (user and has_cookie):
			self.redirect('/user/%d' % user_id)
			return
		elif user.key().id() != user_id:
			self.redirect('/user/%d' % user_id)
			return			
		else:
			has_new_note = None
			notelist = []
			if user.has_note == True:
				has_new_note = "Truth"
			logging.warning(has_new_note)
			if has_new_note:
				#taskqueue.add(url="/checknotesworker", params={ "user_id": user_id })
				#logging.warning('This taskqueue needs to be deleted')
				notelist = user.new_note_list
				user.has_note = False
				user.new_note_list = []
				user.put()
				logging.warning('User just checked message -- .put() to reset has_note and new_note_list')
				memcache.set("Users_%d" % int(user.key().id()), [user])
			else:
				notelist = user.note_list_all
			formatted_list = []
			# pure note format is: 					"db type 			| id 		|epoch_at_creation	| <html></html> " 
			# formatted list will be of this type 	[time_since_creation, note html, note contents, 	the type 		]
			if notelist is not None:
				for note in notelist:
					if not "|" in note:
						pass
					else:
						the_quad = note.split("|", 3)
						the_type = the_quad[0]
						global DB_TYPE_LIST
						the_thing = None
						if the_quad[0] in DB_TYPE_LIST:
							# will not happen if "NA" (not applicable): Awards, Tag edits, etc.
							the_thing = return_thing_by_id(the_quad[1],the_quad[0])
						note_tuple = [time_since_creation(float(the_quad[2])), the_quad[3], the_thing, the_type]
						if note_tuple[3] == "Objects":
							if the_thing.main_img_link:
								#logging.warning('its working')
								note_tuple[2] = "<img src='" + the_thing.main_img_link + "'>"
							else:
								logging.warning('no img but working')
								note_tuple[2] = "no image available"
						logging.warning(note_tuple[1])
						formatted_list.append(note_tuple)
				formatted_list.reverse()
			else:
				formatted_list = None
			self.render('usernotes.html',
						user = user, 
						user_id = user_id,
						notelist = formatted_list,
						has_new_note = has_new_note,
						)

	def get(self, user_num):
		user_id = int(user_num)
		self.render_page(user_num=user_id)

	def post(self, user_num):
		user_id = int(user_num)
		user = self.return_user_if_cookie()
		has_cookie = self.return_has_cookie()

		if not (user and has_cookie):
			self.redirect('/user/%d' % user_id)
			return
		elif user.key().id() != user_id:
			self.redirect('/user/%d' % user_id)
			return			
		else:
			the_type = self.request.get('type')
			logging.warning(the_type)
			the_text = self.request.get('text')
			if the_type == "Comments":
				# this will be a subcomment
				obj_num = self.request.get('obj_id')
				parent_id = int(self.request.get('parent_id'))
				parent_comment = return_thing_by_id(parent_id, "Comments")
				if parent_comment is None:
					self.error(404)
					return
				obj_id = int(obj_num)
				the_object = object_page_cache(obj_id)
				nsfw_bool = the_object.nsfw
				kids_bool = the_object.okay_for_kids

				logging.warning('db query -- get parent_comment by id')
				logging.warning(parent_id)
				new_subcomment = Comments(
										author_id = user_id,
										author_name = user.username,
										epoch = float(time.time()),
										text = the_text,

										com_parent = parent_id,
										#parent = parent_comment.key(),

										obj_ref_id = obj_id,
										obj_ref_nsfw = nsfw_bool,
										obj_ref_okay_for_kids = kids_bool)
				new_subcomment.put()
				#parent_comment.children.append(new_subcomment.key())
				if parent_comment.has_children == False:
					parent_comment.has_children = True
				parent_comment.ranked_children.append(int(new_subcomment.key().id()))
				if len(parent_comment.ranked_children) > 1:
					parent_comment.ranked_children = sort_comment_child_ranks(parent_comment.ranked_children, delay = 6)
				parent_comment.put()
				memcache.set('Comments_%d' % parent_comment.key().id(), [parent_comment])
				logging.warning('New Subcomment Created')
				if int(parent_comment.author_id) != int(user_id):
					if str(parent_comment.author_id) not in user.blocked_by_list:
						logging.warning('should sleep here')
						new_note(parent_comment.author_id,
							"Comments|%d|%s| <a href='/user/%s'>%s</a> has replied to your <a href='/com/%s'>comment</a>" % (
									int(new_subcomment.key().id()),
										str(time.time()),
															str(user_id),
																str(cgi.escape(user.username)),
																										str(parent_comment.key().id())),
							# there should be a permelink for comments here (ugh, yet another pages to write)
							delay=6)
					else:
						# fake the sleep
						time.sleep(6)
						logging.warning('no note because blocked')
				else:
					# this should never happen if in notification page
					logging.warning('6 second sleep for new subcomment by same previous comment author')
					time.sleep(6)

				if nsfw_bool == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update=True)

				object_page_cache(obj_id, update=True)
				obj_comment_cache(obj_id, update=True)
				user_page_comment_cache(user_id, update=True) # no longer needed really...
				user_page_obj_com_cache(user_id, update=True)
				if kids_bool == True:
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass

			elif the_type == "Messages":
				recipient_id = int(self.request.get('recipient_id'))
				recipient_name = self.request.get('recipient_name')
				sender_id = user_id
				sender_username = user.username
				if str(recipient_id) not in user.blocked_by_list:
					new_message = Messages(epoch = float(time.time()),
											text = the_text,
											author_id = sender_id,
											author_name = sender_username,
											recipient_id = recipient_id,
											recipient_name = recipient_name,
											)
					new_message.put()
					logging.warning('new message -- write')
					user_messages_cache(recipient_id, update=True, delay = 6)
					user_messages_cache(sender_id, update=True)

					new_note(recipient_id,
							"Messages|%d|%s| <a href='/user/%s'>%s</a> has sent you a <a href='/user_messages/%s'>message</a>" % (
									int(new_message.key().id()),
										str(time.time()),
															str(sender_id),
																str(cgi.escape(sender_username)),
																											str(recipient_id)	)
							)
				else:
					# fake the sleep
					logging.warning('no message because this user has been blocked')					
					time.sleep(6)
			else:
				self.error(404)
				return
			self.redirect('/user/note/%d' % user_id)
class UserEdit(Handler):
	def render_page(self, user_num, error=""):
		userpage_id = int(user_num)
		the_user = user_page_cache(userpage_id)

		if not the_user:
			self.error(404)
		else:
			user_hash = hashlib.sha256(the_user.random_string).hexdigest()
			over18 = self.check_cookie_return_val("over18")
			the_list = []
			if over18 != "True":
				# under 18 or no cookie
				the_list = user_page_obj_com_cache_kids(userpage_id)
			else:
				# over 18
				the_list = user_page_obj_com_cache(userpage_id)

			user_is_user = False
			user_id = self.check_cookie_return_val("user_id")
			logged_in = None
			if user_id:
				user_id = int(user_id)
				logged_in = "This guy is logged in"
			else:
				pass
			if the_user.key().id() == user_id:
				# User is object author
				user_is_user = True
			else:
				pass
			if user_is_user == False:
				self.redirect('/user/%d' % userpage_id)

			username_var = the_user.username
			created_var = the_user.created
			img = the_user.main_img_link
			summary = the_user.summary
			location = the_user.location
			printer = the_user.printer
			slicer = the_user.slicer
			software = the_user.software
			email = None
			emailnote = ""
			if the_user.user_email:
				email = the_user.user_email
			elif the_user.unconfirmed_email:
				emailnote = "You have not yet confirmed your email address: "
				email = the_user.unconfirmed_email
			else:
				email = ""

			self.render('useredit.html', 
						user = the_user,
						error=error,
						username=username_var, 
						created=created_var, 
						the_list = the_list,
						user_id = user_id,
						userpage_id = userpage_id,
						user_is_user = user_is_user,
						logged_in = logged_in,
						img = img,
						email = email,
						emailnote = emailnote,
						summary = summary,
						location = location,
						printer = printer,
						slicer = slicer,
						software = software,
						user_hash = user_hash,
						)

	def get(self, user_num):
		user_id = int(user_num)
		self.render_page(user_num=user_id)

	def post(self, user_num):
		user_id = int(user_num)
		user = return_thing_by_id(user_id, "Users")
		if not user:
			self.error(400)
			return
		verify_hash = self.request.get('verify')
		user_id_hash = hashlib.sha256(user.random_string).hexdigest()
		if verify_hash != user_id_hash:
			logging.error("Someone is trying to hack our user profiles")
			self.error(400)
			return
		logging.warning(verify_hash)
		logging.warning(user_id_hash)

		#hopefully this takes care of it
		infinite_var = self.request.get('infinite_scroll')
		infitite_scroll_form_submitted = self.request.get('infinite_verify')
		email_var = self.request.get('email')
		summary_var = self.request.get('summary')
		location_var = self.request.get('location')
		printer_var = self.request.get('printer')
		slicer_var = self.request.get('slicer')
		software_var = self.request.get('software')

		edit_list = [infitite_scroll_form_submitted, email_var, summary_var, location_var, printer_var, slicer_var, software_var]
		item_count = 0
		for item in edit_list:
			if len(item) > 0:
				item_count += 1


		if item_count > 1:
			logging.error(edit_list)
			logging.error('user edit page: more than one form submitted')
			self.error(404)
			return
		if item_count == 0:
			logging.error('something fucked up, empty forms submitted')
			self.redirect('/user/edit/%d' % user_id)
			return
		#logging.warning('well we got this far')
		
		# Now we know we have one form submission and only one.
		if (infinite_var and user.no_infinite_scroll) or (not infinite_var and not user.no_infinite_scroll):
			if infinite_var:
				user.no_infinite_scroll = False
			elif not infinite_var:
				user.no_infinite_scroll = True
			else:
				logging.error("problem with editing infinite scroll")
				self.error(400)
				return
			memcache.set("Users_%s" % str(user_id), [user])
			user.put()

		if email_var:
			if emailcheck.isValidEmailAddress(email_var):
				user = Users.get_by_id(user_id)
				logging.warning('db query -- object edit post descripiton')
				user.unconfirmed_email = email_var
				user.put()
				user_page_cache(user_id, update=True, delay = 6)
				confirmation_email(email_var)
			else:
				error = '"' + email_var + '" did not appear to be a valid email address.'
				self.render_page(user_num = user_num, error = error)
				return


		if summary_var:
			user = Users.get_by_id(user_id)
			logging.warning('db query -- object edit post descripiton')
			user.summary = summary_var
			user.put()
			user_page_cache(user_id, update=True, delay = 6)

		elif location_var:
			user = Users.get_by_id(user_id)
			logging.warning('db query -- object edit post descripiton')
			user.location = location_var
			user.put()
			user_page_cache(user_id, update=True, delay = 6)
			
		elif printer_var:
			user = Users.get_by_id(user_id)
			logging.warning('db query -- object edit post descripiton')
			user.printer = printer_var
			user.put()
			user_page_cache(user_id, update=True, delay = 6)
			
		elif slicer_var:
			user = Users.get_by_id(user_id)
			logging.warning('db query -- object edit post descripiton')
			user.slicer = slicer_var
			user.put()
			user_page_cache(user_id, update=True, delay = 6)
			
		elif software_var:
			user = Users.get_by_id(user_id)
			logging.warning('db query -- object edit post descripiton')
			user.software = software_var
			user.put()
			user_page_cache(user_id, update=True, delay = 6)
			
		else:
			# something broke
			logging.warning("ERROR -- in object edit post request")

		self.redirect('/user/%d' % user_id)
class UserDelPage(Handler):
	def render_page(self, user_num):
		user_id = int(user_num)
		the_user = user_page_cache(user_id)

		if not the_user:
			self.error(404)
		else:
			pass
		user_is_user = False
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)
		
		if the_user.key().id() != user_id:
			# User deleted cookie after loading page
			self.redirect('/user/%d' % the_user.key().id())
		else:
			pass

		over18 = self.check_cookie_return_val("over18")
		the_list = []
		if over18 != "True":
			# under 18 or no cookie
			the_list = user_page_obj_com_cache_kids(user_id)
		else:
			# over 18
			the_list = user_page_obj_com_cache(user_id)

		username_var = the_user.username
		created_var = the_user.created

		user = return_thing_by_id(user_id, "Users")
		user_hash = None
		if user:
			user_hash = hashlib.sha256(user.random_string).hexdigest()
		else:
			logging.error('User not returned by return_thing_by_id function')
			self.error(404)
			return

		self.render('deleteuserpage.html', 
					username=username_var, 
					user_hash = user_hash,
					created=created_var, 
					the_list = the_list)

	def get(self, user_num):
		user_id = int(user_num)
		self.render_page(user_num=user_id)

	def post(self, user_num):
		user_page_id = int(user_num)
		the_user = user_page_cache(user_page_id)
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)

		if the_user.key().id() != user_id:
			# User deleted cookie after loading page
			self.redirect('/user/%d' % user_page_id)
		else:
			pass

		delete_var = self.request.get("delete")
		
		if not delete_var:
			# Do not delete
			self.redirect('/user/%d' % user_page_id)
		else:
			user_page_user = return_thing_by_id(user_page_id, "Users")
			if not user_page_user:
				logging.error("User page delete did not return a user on return_thing_by_id")
				self.error(400)
				return
			user_page_hash = hashlib.sha256(user_page_user.random_string).hexdigest()
			verify_hash = self.request.get("verify")
			if user_page_hash != verify_hash:
				logging.error("Some hacker is trying to delete users")
				self.error(400)
				return

			author = the_user.key().id()

			all_comments = db.GqlQuery("SELECT * FROM Comments WHERE author_id = :1 ORDER BY created DESC", author)
			all_objects = db.GqlQuery("SELECT * FROM Objects WHERE author_id = :1 ORDER BY created DESC", author)

			# Delete all iteratively
			########################
			# Delete all comments
			for comment in all_comments:
				# Step 1: --this was removed when Thing DB was eliminated.
				# Step 2: delete every aspect of each comment
				
				comment.text 			= " "
				comment.author_id		= None
				comment.author_name		= " "

				# Step 3: mark deleted
				comment.deleted 			= True

				# Step 4: put voided object
				comment.put()
				logging.warning('Comment "Deleted"')

			# Delete all objects
			for the_object in all_objects:
				delete_obj(the_object.key().id())

			# Delete all UserBlobs

			all_UserBlobs = db.GqlQuery("SELECT * FROM UserBlob WHERE uploader = :1 ORDER BY created DESC", author)
			if all_UserBlobs:
				all_UserBlobs = list(all_UserBlobs)
				for userblob in all_UserBlobs:
					if userblob.blob_key:
						this_blob = userblob.blob_key
						this_blob.delete()
					userblob.delete()

			if user.main_img_blobkey:
				blob = user.main_img_blobkey
				blob.delete()
				if user.main_img_blobkey:
					user.main_img_blobkey = None

			# Delete User
			user = Users.get_by_id(user_page_id)

			user.username 			= " "
			user.hashed_password 	= " "
			user.over18				= False

			user.summary 			= None
			user.location 			= None
			user.printer 			= None
			user.slicer 			= None
			user.software 			= None

			user.rate_rep 			= 0
			user.obj_rep			= 0
			user.com_rep			= 0
			user.wiki_rep			= 0
			user.awards 			= ["None"]

			user.to_print_list 		= ["None"]
			user.has_printed_list 	= ["None"]

			user.follower_list 		= ["None"]
			user.block_list 		= ["None"]

			user.new_note_list 		= ["None"]
			user.note_list_all 		= ["None"]

			user.upvotes 			= 0
			user.downvotes 			= 0
			user.num_of_rates 		= 0
			#objects 				= db.ListProperty(default = None)
			#comments 				= db.ListProperty(default = None)

			user.net_votes 			= None
			user.user_email			= None	
			user.unconfirmed_email	= None	

			user.main_img_link		= None	
			user.main_img_filename	= None
			# user blob ref above

			# not redundant yet
			user.main_img_blob_key	= None	

			# finally mark user deleted
			user.deleted 			= True	
			user.put()
			logging.warning('User "Deleted"')
			memcache.set("Users_%d" % user_id, [user])

			all_objects_query("kids", update = True, delay = 6)
			all_objects_query("sfw", update=True)
			all_objects_query("nsfw", update=True)
			user_page_comment_cache(user_id, update=True) # no longer needed really...
			user_page_obj_com_cache_kids(user_id, update = True)
			user_page_obj_com_cache(user_id, update=True)
			self.redirect('/logout')
class UserPageImgUpload(ObjectUploadHandler):
	def post(self):
		user_id = self.check_cookie_return_val("user_id")
		username = self.check_cookie_return_val("username")
		if not (user_id and username):
			self.error(400)
			return
		user_id = int(user_id)
		verify_hash = self.request.get("verify")
		user = return_thing_by_id(user_id, "Users")
		user_hash = hashlib.sha256(user.random_string).hexdigest()
		logging.warning(verify_hash)
		logging.warning(user_hash)
		if user_hash != verify_hash:
			logging.error("Someone is trying to hack user img")
			self.error(400)
			return

		if not (user_id and username):
			# should have these cookies even to see the upload html
			self.redirect('/')
			return
		else:
			pass

		# Check for image
		img_upload = None
		img_blob_key = None
		img_url = None

		delete_var = self.request.get("delete")
		img_var = self.request.get("img")
		if delete_var and not img_var:
			the_user = Users.get_by_id(user_id)
			logging.warning("just deleting img")

			the_user.main_img_link = None
			the_user.main_img_filename = None
			# delete previous blob
			if the_user.main_img_blobkey:
				logging.warning('deleting previous image')
				this_blob = the_user.main_img_blobkey
				this_blob.delete()
				the_user.main_img_blobkey = None

			the_user.put()
			memcache.set("Users_%d" % user_id, [the_user])

			self.redirect('/user/%d' % user_id)
			return

		try:
			img_upload = self.get_uploads()[0]
		except:
			logging.error("failed img upload")
			self.redirect('/user/%d' % user_id)
			return

		if img_upload:
			img_url = '/serve_obj/%s' % img_upload.key()
			img_blob_key = str(img_upload.key())
			filename_full = img_upload.filename
			filename = filename_full.split('.')
			logging.warning(filename)
			if filename[-1].lower() not in ['png','jpg','jpeg','bmp']:
				logging.error('not "image" filetype, redirect')
				img_upload.delete()
				self.redirect('/user/%d' % user_id)
				return
			logging.warning(img_upload.size)
			if img_upload.size > 100000:
				logging.warning(img_upload)
				logging.warning(img_upload.size)
				resize_ratio = int(100*(float(100000)/float(img_upload.size)))
				logging.warning(resize_ratio)
				# Resize the image
				logging.warning('db query img_upload blobinfo')
				logging.warning(img_upload.key())
				resized = images.Image(blob_key=img_upload)
				resized.horizontal_flip()
				resized.horizontal_flip()
				thumbnail = resized.execute_transforms(output_encoding=images.JPEG, 
													 quality = resize_ratio,
													)
				# Save Resized Image back to blobstore
				new_file = files.blobstore.create(mime_type='image/jpeg',
												  _blobinfo_uploaded_filename=filename_full)
				with files.open(new_file, 'a') as f:
					f.write(thumbnail)
				files.finalize(new_file)
				logging.warning(new_file)
				new_key = files.blobstore.get_blob_key(new_file)   
				# Remove the original image
				img_upload.delete()
				# Reset img_upload variable
				img_upload = blobstore.BlobInfo.get(new_key)
				logging.warning('db query get blobinfo')
				img_url = '/serve_obj/%s' % img_upload.key()
		else:
			logging.error("failed img upload")
			self.error(500)
			return

		## If here, the user will be registered:
		the_user = Users.get_by_id(user_id)
		logging.warning('db query UserPageImgUpload')

		# delete previous blob
		if the_user.main_img_blobkey:
			logging.warning('deleting previous image')
			this_blob = the_user.main_img_blobkey
			this_blob.delete()

		# attach new blob to user
		if img_upload:
			the_user.main_img_link = img_url
			the_user.main_img_blobkey = img_upload.key()
			the_user.main_img_filename = str(img_upload.filename)
	
		memcache.set("Users_%d" % int(user_id), [the_user])
		the_user.put()
		self.redirect('/user/%d' % user_id)

class CommentPage(Handler):
	def render_page(self, com_num, error=""):
		user = self.return_user_if_cookie()

		com_id = int(com_num)
		com = return_thing_by_id(com_id, "Comments")

		if com is None:
			self.error(404)
			return

		okay_for_kids = com.obj_ref_okay_for_kids
		if okay_for_kids != True:
			over18 = self.check_cookie_return_val("over18")
			if over18 != "True":
				self.redirect('/')
			else:
				pass
		else:
			pass

		# This section checks the cookie and sets the html style accordingly.
		has_cookie = self.return_has_cookie()

		# This section check if the user is the author and can delete the object.
		user_is_author = False
		user_id = self.check_cookie_return_val("user_id")
		if user_id:
			user_id = int(user_id)
		else:
			pass
			
		if user_id and (com.author_id == user_id):
			# User is object author
			user_is_author = True
		else:
			pass

		top_comment_singleton = [return_comment_vote_flag_triplet(com, user_id)]
		# comment tuples:
		the_comments = obj_comment_cache(com.obj_ref_id)
		comment_triplet_list = []
		for comment in the_comments:
			comment_triplet_list.append(return_comment_vote_flag_triplet(comment, user_id))
		#this takes the form (comment, vote_int, flag_int)
		#logging.warning(comment_triplet_list)
		self.render("comment_permalink.html",
					user = user,
					com = com,
					has_cookie = has_cookie,
					user_is_author = user_is_author,
					top_comment_singleton = top_comment_singleton,
					comment_triplet_list = comment_triplet_list,
					)

	def get(self, com_num):
		com_id = int(com_num)
		self.render_page(com_num=com_id)

	def post(self, com_num):
		com_id = int(com_num)
		com = return_thing_by_id(com_id, "Comments")
		if com is None:
			self.error(404)
			return
		the_object = return_thing_by_id(com.obj_ref_id, "Objects")
		if the_object is None:
			self.error(404)
			return
		obj_id = int(the_object.key().id())
		the_comments = obj_comment_cache(obj_id)
		subcomment_var = None
		parent_comment = None
		parent_id = None
		obj_author = None
		note = None
		for i in the_comments:
			val = i.key().id()
			subcomment_var = self.request.get("subcomment_form%d" % val)
			if subcomment_var:
				parent_id = val
				parent_comment = i
				logging.warning(parent_id)
				logging.warning(subcomment_var)
				break

		if not subcomment_var:
			# Empty comment submitted
			#error_var = "Please do not submit an empty comment."
			self.redirect('/com/%d' % com_id)
		else:
			# Check if logged in again (to prevent delete cookies after page load)
			user_id = self.check_cookie_return_val("user_id")
			username_var = self.check_cookie_return_val("username")
			if not (user_id and username_var):
				self.redirect('/com/%d' % com_id)
			else:
				# Success!
				user_id = int(user_id)
				nsfw_bool = the_object.nsfw
				kids_bool = the_object.okay_for_kids
				
				if subcomment_var:

					# Markdown escape
					escaped_comment_text = cgi.escape(subcomment_var)
					mkd_converted_comment = mkd.convert(escaped_comment_text)

					#logging.warning('db query -- get parent_comment by id')
					logging.warning(parent_id)
					logging.warning(parent_comment)
					new_subcomment = Comments(
											author_id = user_id,
											author_name = username_var,
											epoch = float(time.time()),
											text = subcomment_var,
											markdown = mkd_converted_comment,

											com_parent = parent_comment.key().id(),

											obj_ref_id = the_object.key().id(),
											obj_ref_nsfw = nsfw_bool,
											obj_ref_okay_for_kids = kids_bool)
					new_subcomment.put()
					logging.warning('new_subcomment.put()')
					#parent_comment.children.append(new_subcomment.key())
					if parent_comment.has_children == False:
						parent_comment.has_children = True
					parent_comment.ranked_children.append(int(new_subcomment.key().id()))
					logging.warning(parent_comment.ranked_children)
					if len(parent_comment.ranked_children) > 1:
						parent_comment.ranked_children = sort_comment_child_ranks(parent_comment.ranked_children, delay = 6)
					parent_comment.put()
					logging.warning('New Subcomment Complete')
					if int(parent_comment.author_id) != int(user_id):
						logging.warning('should sleep here')
						new_note(parent_comment.author_id,
							"%s| <a href='/user/%s'>%s</a> has replied to your <a href='/com/%s'>comment</a>" % (
							str(time.time()),
												str(user_id),
													str(cgi.escape(username_var)),
																							str(parent_comment.key().id())),
							# there should be a permelink for comments here (ugh, yet another pages to write)
							delay=6)
					else:
						#logging.warning('6 second sleep for new subcomment by same previous comment author')
						time.sleep(6)
				else:
					self.error(404)
					return


				return_thing_by_id(parent_comment.key().id(), "Comments", update=True)
				if nsfw_bool == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update=True)

				object_page_cache(obj_id, update=True)
				obj_comments = obj_comment_cache(obj_id, update=True)

				the_object.total_num_of_comments = len(obj_comments)
				the_object.put()
				memcache.set("Objects_%s" % str(obj_id), [the_object])

				user_page_comment_cache(user_id, update=True) # no longer needed really...
				user_page_obj_com_cache(user_id, update=True)
				if kids_bool == True:
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass
				self.redirect('/com/%d' % com_id)

class NewPage(Handler):
	def get(self):
		#header3 takes user_id and not user for the link to the user page
		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")
		self.render("new.html", user=user, user_id=user_id)
class NewObjectPage(Handler):
	def render_page(self):
		user_id = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		user = return_thing_by_id(user_id, "Users")

		photo_upload_url = blobstore.create_upload_url('/upload_obj1')
		title_var = ""
		license_var = None
		rights = None
		audience_var = None
		error_1 = ""
		error_2 = ""
		error_3 = ""
		file_error = ""

		cc_pd = None
		cc_a = None
		cc_a_sa = None
		cc_a_nc = None
		cc_a_sa_nc = None
		cc_lgpl = None
		bsd = None
		not_author = None

		need_license = ""
		kids = "default"
		sfw = None
		nsfw = None
		food = None

		file_type_error = ""
		
		# redirect variables
		redirect = self.request.get("redirect")
		if redirect == "True":
			error_1 = self.request.get("error_1")
			error_2 = self.request.get("error_2")
			error_3 = self.request.get("error_3")
			file_error = self.request.get("file_error")
			title_var = self.request.get("title")
			license_var = self.request.get("license")
			rights = self.request.get("rights")
			audience_var = self.request.get("audience")
			food_related = self.request.get("food")
			
			logging.warning(license_var)
			if license_var == "cc_pd":
				need_license = ""
				cc_pd = "cc_pd"
			elif license_var == "cc_a":
				need_license = ""
				cc_a = "cc_a"
			elif license_var == "cc_a_sa":
				need_license = ""
				cc_a_sa = "cc_a_sa"
			elif license_var == "cc_a_nc":
				need_license = ""
				cc_a_nc = "cc_a_nc"
			elif license_var == "cc_a_sa_nc":
				need_license = ""
				cc_a_sa_nc = "cc_a_sa_nc"
			elif license_var == "cc_lgpl":
				need_license = ""
				cc_lgpl = "cc_lgpl"
			elif license_var == "bsd":
				need_license = ""
				bsd = "bsd"
			elif license_var == "not_author":
				need_license = ""
				not_author = "not_author"
			else:
				need_license = "You must select a license."

			if audience_var == "sfw":
				kids = None
				sfw = "cool!"
			elif audience_var == "nsfw":
				kids = None
				nsfw = "gross"
			if food_related == "True":
				food = "Yum!"
		elif redirect == "filetype":
			file_type_error = self.request.get("file_type_error")

		if not_author:
			creator_license = self.request.get("creator_license")
			creator_license = strip_string_whitespace(creator_license)
			if not creator_license:
				need_license = "You must enter the object's license."
			elif creator_license in ["cc_a", "cc_a_sa", "cc_a_nc", "cc_a_sa_nc", "cc_lgpl", "bsd"]:
				if error_2:
					need_license = error_2


		
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False

		if not (user_id or author_name):
			self.redirect("/")
		else:
			self.render("newobject1.html", 
						upload_url=upload_url,
						photo_upload_url = photo_upload_url,
						over18 = over18,
						user = user,
						user_id = user_id,

						title = title_var,
						license = license_var,
						rights = rights,
						error_1 = error_1,
						error_2 = error_2,
						error_3 = error_3,
						file_error = file_error,
						need_license = need_license,
						nsfw = nsfw,
						sfw = sfw,
						kids = kids,
						food = food,
						file_type_error = file_type_error,
						)

	def get(self):
		self.render_page()
class NewObjectUpload1(ObjectUploadHandler):
	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			self.redirect("/login")
		else:
			# User is signed in
			user_id = int(user_var)
			user = return_thing_by_id(user_id, "Users")
			global TRUSTED_USERS
			trusted_user = False
			if user.username in TRUSTED_USERS:
				trusted_user = True

			# Required fields
			title_var = self.request.get("title")
			main_file_var = self.request.get("file")
			logging.warning(main_file_var)
			license_var = self.request.get("license")
			rights = self.request.get("rights")
			food_related = self.request.get("food_related")
			if food_related:
				food_related = True
			else:
				food_related = False
			
			# Kids and NSFW entries (if available)
			# Here, defaults are okay-for-kids/sfw, because no entry if kids online:
			okay_for_kids_var = True
			nsfw_var = False
			audience_var = self.request.get("audience")
			if audience_var: 
				if audience_var == "kids":
					pass
				elif audience_var == "sfw":
					okay_for_kids_var = False
				elif audience_var == "nsfw":
					okay_for_kids_var = False
					nsfw_var = True
				else:
					logging.warning("New Object -- nsfw parser not working properly")
			else:
				pass
			
			if not (title_var and license_var and rights and main_file_var): #main_file_var and main_img_var and license_var):
				# Unsuccessful
				error_1 = ""
				error_2 = ""
				error_3 = ""
				file_error = ""
				if not title_var:
					error_1 = "You must include a title."
				if not license_var:
					error_2 = "You must select a license."
				if not rights:
					error_3 = "It must be legal for you to share this model."
				if not main_file_var:
					file_error = "Hmm, it looks like you forgot to select a file to upload."
				self.redirect("/newobject?redirect=True&error_1=%s&error_2=%s&error_3=%s&file_error=%s&title=%s&license=%s&rights=%s&audience=%s&food=%s" % (error_1, error_2, error_3, file_error, title_var, license_var, rights, audience_var, str(food_related)))
			else:
				if license_var == "not_author":
					sublicense = self.request.get("creator_license")
					if sublicense in ["cc_pd", "cc_a", "cc_a_sa", "cc_lgpl", "bsd"]:
						if sublicense in ["cc_a", "cc_a_sa", "cc_lgpl", "bsd"]:
							creator = self.request.get("creator")
							creator = strip_string_whitespace(creator)
							if not creator:
								error_2 = "That license requires you to give attribution."
								self.redirect("/newobject?redirect=True&error_2=%s&title=%s&license=%s&rights=%s&audience=%s&food=%s&creator_license=%s" % (error_2, title_var, license_var, rights, audience_var, str(food_related), sublicense))
								return
						else:
							creator = None
					else:
						error_2 = "You must select the author's license."
						self.redirect("/newobject?redirect=True&error_2=%s&title=%s&license=%s&rights=%s&audience=%s&food=%s&creator_license=%s" % (error_2, title_var, license_var, rights, audience_var, str(food_related), sublicense))
						return

					license_var = sublicense
				else:
					creator = None

				# Success

				if license_var == "cc_pd":
					license_var = "Creative Commons: Public Domain Dedication"
				elif license_var == "cc_a":
					license_var = "Creative Commons: Attribution"
				elif license_var == "cc_a_sa":
					license_var = "Creative Commons: Attribution, Share Alike"
				elif license_var == "cc_a_nc":
					license_var = "Creative Commons: Attribution, Non-Commercial"
				elif license_var == "cc_a_sa_nc":
					license_var = "Creative Commons: Attribution, Share Alike, Non-Commercial"
				elif license_var == "cc_lgpl":
					license_var = "GNU Lesser General Public License"
				elif license_var == "bsd":
					license_var = "BSD License"

				# try:
				if 1==1:
					file_data = None
					file_blob_key = None
					file_url = None

					# this is a problem:
					# if only one file is uploaded, it will default to img...
					# hmm... how to fix
					try:
						file_data = self.get_uploads()[0]
					except:
						pass

					if file_data:
						# size limit
						global MAX_FILE_SIZE_FOR_OBJECTS
						if not trusted_user: # trusted users can upload larger files
							if file_data.size > MAX_FILE_SIZE_FOR_OBJECTS:
								logging.warning(file_data)
								logging.warning(file_data.size)
								file_data.delete()
								self.redirect("/newobject?redirect=filetype&file_type_error=%s" % "This file is too large. Our maximum file size is 5MB. We're very sorry, but currently, hosting exceptionally large files is prohibitively expensive for us. Please upload your file to an alternative host and link to it instead.") 
								return

						file_url = '/serve_obj/%s' % file_data.key()
						file_blob_key = file_data.key()
						filename = file_data.filename
						filename_full = filename
						filename = filename.split('.')
						logging.warning(filename)
						if filename[-1].lower() not in ["stl"]:
							logging.warning('not "stl" filetype, redirect')
							file_data.delete()
							self.redirect("/newobject?redirect=filetype&file_type_error=%s" % "This file must be a stereo lithography filetype (.stl).") # this should return to an error version of the upload page
							return
						if not trusted_user: # trusted users can upload binaries
							if not is_ascii_stl(file_data):
								logging.warning('not "ascii stl" after parse, redirect')
								file_data.delete()
								self.redirect("/newobject?redirect=filetype&file_type_error=%s" % "This file must be a ASCII stereo lithography filetype (.stl). We had a problem parsing your file. It may be a binary .stl, which we do not currently support (if you open the file in a text editor an it is only numbers, this is the problem). However, it may be corrupt, contain questionable content, or not actually be an ascii .stl filetype.") # this should return to an error version of the upload page
								return

						### future parser to rewrite would go here, but this is diminished and will be removed in the future
						
						# if 1 != 1:
						# 	parsed_stl = 'put parsed stl here'

						# 	# Save parsed_stl back to blobstore
						# 	new_file = files.blobstore.create(mime_type='application/octet-stream',
						# 									  _blobinfo_uploaded_filename=filename_full)
						# 	with files.open(new_file, 'a') as f:
						# 		f.write(parsed_stl)
						# 	files.finalize(new_file)
						# 	logging.warning(new_file)
						# 	new_key = files.blobstore.get_blob_key(new_file)   
						# 	# Remove the original file
						# 	file_data.delete()
						# 	# Reset file_data variable
						# 	file_data = blobstore.BlobInfo.get(new_key)
						# 	logging.warning('db query get blobinfo')
						# 	file_url = '/serve_obj/%s' % file_data.key()
						# 	file_blob_key = str(file_data.key())

					else:
						self.redirect("/newobject?redirect=filetype&file_type_error=%s" % "Your file upload appears to have failed. Please try again. If the problem persists please contact us.") # this should return to an error version of the upload page
						return

					new_object = Objects(title = title_var, 
										author_id = user_id, # Not sure how file uploads will work, so below are default links for an object
										author_name = author_name,
										obj_type = 'upload',
										epoch = float(time.time()),

										okay_for_kids = okay_for_kids_var,
										nsfw = nsfw_var,
										food_related = food_related,

										stl_file_link = file_url, # main_img_var, # main_file_var,
										stl_file_blob_key = file_data.key(),
										stl_filename = str(file_data.filename),

										license = license_var,
										printable = True,
										original_creator = creator,
										rank = new_rank(),
										num_user_when_created = num_users_now(),
										voter_list = [user_id],
										voter_vote = ["%s|1" % str(user_id)],

										uuid = str(uuid.uuid4()),
										)
					new_object.put()

					# if file_data:
					# 	new_object_data = ObjectBlob(blob_type = "data",
					# 								priority = 0,
					# 								obj_id = int(new_object.key().id()),
					# 								uploader = int(new_object.author_id),
					# 								blob_key = file_data.key(),
					# 								filename = str(file_data.filename),

					# 								key_name = "blob|%s" % str(file_data.key())
					# 								) 

					# 	new_object_data.put()
					# 	memcache.set("objectblob|%s" % str(new_object_data.blob_key), new_object_data)
					# 	return_object_blob_by_obj_id_and_priority(new_object.key().id(), 0, update=True)
					# else:
					# 	pass

					if nsfw_var == True:
						all_objects_query("nsfw", update = True, delay = 6)
					else:
						all_objects_query("sfw", update = True, delay = 6)

					if okay_for_kids_var == True:
						all_objects_query("kids", update = True)
						user_page_obj_com_cache_kids(user_id, update = True)
					else:
						pass

					object_page_cache(new_object.key().id(),update=True)
					user_page_object_cache(user_id, update=True) # No longer needed really...
					user_page_obj_com_cache(user_id, update=True)


					# Update all front pages using the load_front_pages_from_memcache_else_query function
					global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
					if nsfw_var == True:
						# currently no other page types supported beyond "/"
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
					else:
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
					if okay_for_kids_var == True:
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)


					if user:
						for follower_id in user.follower_list:
							logging.warning('should sleep here')
							new_note(int(follower_id),
								"Objects|%d|%s| <a href='/user/%s'>%s</a> uploaded <a href='/obj/%s'>%s</a>" % (
										int(new_object.key().id()),
											str(time.time()),
																str(user.key().id()),
																	str(cgi.escape(user.username)),
																									str(new_object.key().id()),
																										str(cgi.escape(new_object.title))),
								)
					self.redirect('/newobject2/%d' % new_object.key().id())

				#except:
				else:
					self.redirect('/upload_failure.html')
class NewObjectPage2(Handler):
	def render_page(self, obj_num):
		obj_id = int(obj_num)
		user_id = self.check_cookie_return_val("user_id")		
		user = return_thing_by_id(user_id, "Users")
		if not user:
			self.error(400)
			return
		query_args = self.request.arguments()
		querystring = None
		logging.warning(query_args)		
		if query_args:
			redirect = self.request.get('redirect')
			if redirect == "True":
				querystring = "?redirect=%s&error_1=%s&error_2=%s&rights_checked=%s" % (query_args[0],query_args[1],query_args[2],query_args[3])
			elif redirect == "filetype":
				querystring = "?redirect=%s&file_type_error=%s" % (query_args[0],query_args[1])
		if query_args:
			photo_upload_url = blobstore.create_upload_url('/upload_obj2/%d%s' % (obj_id, querystring))
		else:
			photo_upload_url = blobstore.create_upload_url('/upload_obj2/%d' % obj_id)

		error_1 = "" # checkbox
		error_2 = "" # image input
		rights = None
		file_type_error = ""
		redirect = self.request.get('redirect')
		if redirect == "True":
			error_1 = self.request.get('error_1')
			error_2 = self.request.get('error_2')
			rights = self.request.get('rights_checked')
			if error_2:
				rights = None
				error_1 = ""
		elif redirect == "filetype":
			file_type_error = self.request.get("file_type_error")

		the_obj = object_page_cache(obj_id)
		title_var = the_obj.title

		user_id = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False
		# check whether user is author:

		if not (user_id and author_name):
			self.redirect("/")
			return

		if (the_obj.author_id != int(user_id)) or (the_obj.author_name != author_name):
			self.redirect("/")
			return

		else:
			self.render("newobject2.html", 
						photo_upload_url = photo_upload_url,
						over18 = over18,
						user=user,
						user_id=user_id,

						title=title_var,
						obj_id=obj_id, 
						error_1 = error_1,
						error_2 = error_2,
						rights = rights,
						file_type_error = file_type_error,
						)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)
class NewObjectUpload2(ObjectUploadHandler):
	def post(self, obj_num):
		obj_id = int(obj_num)

		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			self.redirect("/login")
		else:
			# User is signed in
			user_id = int(user_var)

			# Required fields
			main_img_var = self.request.get("img")
			rights = self.request.get("rights")
			logging.warning(main_img_var)
			
			if not (rights and main_img_var): #main_file_var and main_img_var and license_var):
				# Unsuccessful
				logging.warning(rights)
				logging.warning(main_img_var)
				error_1 = ""
				error_2 = ""
				if not rights:
					logging.warning("yep")
					error_1 = "It must be legal for you to share this image."
				if not main_img_var:
					logging.warning("yep2")
					error_2 = "Hmm, it looks like you forgot to select a image to upload."
				self.redirect("/newobject2/%d?redirect=True&error_1=%s&error_2=%s&rights_checked=%s" % (obj_id, error_1, error_2, rights))
				return

			else: 
				# Success

				# try:
				if 1==1:
					img_upload = None
					img_blob_key = None
					img_url = None
					guess_type = None
					# this is a problem:
					# if only one file is uploaded, it will default to img...
					# hmm... how to fix
					try:
						img_upload = self.get_uploads()[0]
					except:
						self.redirect("/newobject2/%d" % obj_id)


					if img_upload:
						img_url = '/serve_obj/%s' % img_upload.key()
						img_blob_key = str(img_upload.key())
						filename_full = img_upload.filename
						filename = filename_full.split('.')
						logging.warning(filename)
						
						#blob_info = blobstore.BlobInfo.get(img_upload)
						#img_size = blob_info.size
						#logging.warning(img_size)
						
						if filename[-1].lower() not in ['png','jpg','jpeg','bmp']:
							logging.error('not "image" filetype, redirect')
							img_upload.delete()
							self.redirect("/newobject2/%d?redirect=filetype&file_type_error=%s" % (obj_id, "That file did not appear to be an allowed image filetype.")) # this should return to an error version of the upload page
							return

						global MAX_FILE_SIZE_FOR_OBJECTS
						if img_upload.size > MAX_FILE_SIZE_FOR_OBJECTS:
							logging.warning(img_upload)
							logging.warning(img_upload.size)
							img_upload.delete()
							self.redirect("/newobject2/%d?redirect=filetype&file_type_error=%s" % (obj_id, "This image is too large. Our maximum file size is 5MB. We're very sorry, but currently, hosting exceptionally large files is prohibitively expensive for us. Please upload a smaller version, preferably < 1MB. We are currently working on integrating imgur, but have not completed it.")) 
							return

						if img_upload.size > 100000:
							logging.warning(img_upload)
							logging.warning(img_upload.size)
							resize_ratio = int(100*(float(100000)/float(img_upload.size)))
							logging.warning(resize_ratio)
							# Resize the image
							logging.warning('db query img_upload blobinfo')
							logging.warning(img_upload.key())
							resized = images.Image(blob_key=img_upload)
							resized.horizontal_flip()
							resized.horizontal_flip()
							thumbnail = resized.execute_transforms(output_encoding=images.JPEG, 
																 quality = resize_ratio,
																)
							# Save Resized Image back to blobstore
							new_file = files.blobstore.create(mime_type='image/jpeg',
															  _blobinfo_uploaded_filename=filename_full)
							with files.open(new_file, 'a') as f:
								f.write(thumbnail)
							files.finalize(new_file)
							logging.warning(new_file)
							new_key = files.blobstore.get_blob_key(new_file)   
							# Remove the original image
							img_upload.delete()
							# Reset img_upload variable
							img_upload = blobstore.BlobInfo.get(new_key)
							logging.warning('db query get blobinfo')
							img_url = '/serve_obj/%s' % img_upload.key()
							img_blob_key = str(img_upload.key())
					else:
						self.redirect("/newobject2/%d" % obj_id)

					new_object = Objects.get_by_id(obj_id)

					if new_object.main_img_blob_key:
						logging.warning('deleting old blob')
						old_blob = new_object.main_img_blob_key
						old_blob.delete()

					new_object.main_img_link = img_url
					new_object.main_img_blob_key = img_upload.key()
					new_object.main_img_filename = str(img_upload.filename)

					new_object.put()

					# if img_upload:
					# 	new_object_photo = ObjectBlob(blob_type = 'image',
					# 									priority = 1,
					# 									obj_id = int(new_object.key().id()),
					# 									uploader = int(new_object.author_id),
					# 									blob_key = img_upload.key(),
					# 									filename = str(img_upload.filename),

					# 									key_name = "blob|%s" % str(img_upload.key())
					# 									)			
					# 	new_object_photo.put()
					# else:
					# 	pass
					
					object_page_cache(new_object.key().id(),update=True, delay = 6)

					# if img_upload:
					# 	return_object_blob_by_obj_id_and_priority(obj_id, 1, update=True)
					# 	memcache.set("objectblob|%s" % str(new_object_photo.blob_key), new_object_photo)
					# else:
					# 	pass

					if new_object.nsfw == True:
						all_objects_query("nsfw", update = True)
					else:
						all_objects_query("sfw", update = True)

					if new_object.okay_for_kids == True:
						all_objects_query("kids", update = True)
						user_page_obj_com_cache_kids(user_id, update = True)
					else:
						pass

					user_page_object_cache(user_id, update=True) # No longer needed really...
					user_page_obj_com_cache(user_id, update=True)

					# Update all front pages using the load_front_pages_from_memcache_else_query function
					global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
					if new_object.nsfw == True:
						# currently no other page types supported beyond "/"
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
					else:
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
					if new_object.okay_for_kids == True:
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)

					self.redirect('/newobject3/%d' % new_object.key().id())

				#except:
				else:
					self.redirect('/upload_failure.html')
class NewObjectPage3(Handler):
	def render_page(self, obj_num):
		obj_id = int(obj_num)
		user_id = self.check_cookie_return_val("user_id")
		user = return_thing_by_id(user_id, "Users")

		the_obj = object_page_cache(obj_id)
		main_img = the_obj.main_img_link

		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False

		if not (user_var and author_name):
			self.redirect("/")
			return

		if (the_obj.author_id != int(user_var)) or (the_obj.author_name != author_name):
			self.redirect("/")
			return
		else:
			self.render("newobject3.html", 
						user = user,
						user_id = user_id,
						the_obj = the_obj,


						over18 = over18,
						obj_id = obj_id,
						author_name = author_name,

						)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)

	def post(self, obj_num):
		obj_id = int(obj_num)

		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			self.redirect("/login")
		else:
			# User is signed in
			user_id = int(user_var)

			# Fields
			description_var = self.request.get("description")
			tag_var = self.request.get("tags")
			the_tags = None
			if tag_var:
				the_tags = tag_var.split(', ')
				# tag string section
				tag_list = the_tags
				logging.warning(tag_list)
				tag_list = remove_list_duplicates(tag_list)
				logging.warning(tag_list)
				tag_list = strip_list_whitespace(tag_list)
				logging.warning(tag_list)
				tag_list = remove_unsafe_chars_from_tags(tag_list)
				tag_list.sort()
				if not tag_list:
					tag_list = ["None"]
					logging.warning("public tag list set to None")
				the_tags = tag_list
			if not (description_var and tag_var):
				self.redirect('/obj/%d' % obj_id)
				return
			
			# else: Success!
			new_object = Objects.get_by_id(obj_id)

			if description_var:
				new_object.description = description_var
				# Now escape, and save as markdown text
				escaped_description_text = cgi.escape(description_var)
				mkd_converted_description = mkd.convert(escaped_description_text)
				new_object.markdown = mkd_converted_description
			else:
				pass
			if the_tags:
				for tag in the_tags:
					new_object.tags.append(tag)
					new_object.author_tags.append(tag)
			else:
				pass

			new_object.put()

			#db_set_delay
			time.sleep(6)
			if the_tags:
				for tag in the_tags:
					if new_object.okay_for_kids == True:
						store_page_cache_kids(tag, update=True)
					if new_object.nsfw == True:
						store_page_cache_nsfw(tag, update=True)
					else:
						store_page_cache_sfw(tag, update=True)
				taskqueue.add(url ='/tagupdateworker', 
							  countdown = 6
							 )

			if new_object.nsfw == True:
				all_objects_query("nsfw",update = True)
			else:
				all_objects_query("sfw", update = True)

			if new_object.okay_for_kids == True:
				all_objects_query("kids", update = True)
				user_page_obj_com_cache_kids(user_id, update = True)
			else:
				pass

			object_page_cache(new_object.key().id(),update=True)
			user_page_object_cache(user_id, update=True) # No longer needed really...
			user_page_obj_com_cache(user_id, update=True)
			self.redirect('/obj/%d' % new_object.key().id())
class NewLinkPage(Handler):
	def render_page(self):
		
		user_id = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False
		if not (user_id or author_name or over18):
			self.redirect("/login")
			return
		user = return_thing_by_id(user_id, "Users")
		if not user:
			self.error(400)
			return
		else:
			audience = "kids"
			self.render("newlink.html", 
						user = user,
						user_id = user_id,
						over18 = over18,
						audience = audience,	
						)

	def get(self):
		self.render_page()

	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			error_var = "Sorry, but you need to be logged in to upload an object."
			self.render("newlink.html", error = error_var)
		else:
			# User is signed in.
			user_id = int(user_var)
			if over18 == "True":
				over18 = True
			else:
				over18 = False

			# Required fields
			title_var = self.request.get("title")
			link_var = self.request.get("link")

			rights = self.request.get('rights')

			food_related = self.request.get("food_related")
			if food_related:
				food_related = True
			else:
				food_related = False

			# Kids and NSFW entries (if available)
			# Here, defaults are okay-for-kids/sfw, because no entry if kids online:
			okay_for_kids_var = True
			nsfw_var = False
			audience_var = self.request.get("audience")
			audience_for_redirect = audience_var
			if audience_var: 
				if audience_var == "kids":
					pass
				elif audience_var == "sfw":
					okay_for_kids_var = False
				elif audience_var == "nsfw":
					okay_for_kids_var = False
					nsfw_var = True
				else:
					logging.error("New Link -- nsfw parser not working properly")
			else:
				pass

			# Optional fields
			description_var = self.request.get("description")
			# Now escape, and save as markdown text
			escaped_description_text = cgi.escape(description_var)
			mkd_converted_description = mkd.convert(escaped_description_text)
			
			tag_var = self.request.get("tags")
			the_tags = None
			if tag_var:
				the_tags = tag_var.split(', ')
				# tag string section
				tag_list = the_tags
				logging.warning(tag_list)
				tag_list = remove_list_duplicates(tag_list)
				logging.warning(tag_list)
				tag_list = strip_list_whitespace(tag_list)
				logging.warning(tag_list)
				tag_list = remove_unsafe_chars_from_tags(tag_list)
				tag_list.sort()
				if not tag_list:
					tag_list = ["None"]
					logging.warning("public tag list set to None")
				the_tags = tag_list

			# Check whether the url links to an actual site:
			# 3 tries:
			# 1st try: plain link (e.g. "http://www.google.com" = success!)
			# 2nd try: no http (e.g. "www.google.com" -> "http://www.google.com" = success!)
			# 3rd try: no www either (e.g. "google.com" -> "http://www.google.com" = success!)
			formatted_link_var = check_url(link_var)
			deadLinkFound = True
			if formatted_link_var:
				deadLinkFound = False
			
			if not (title_var and link_var):
				# Unsuccessful
				error_var = 'You must include a title and a link.'
				user = return_thing_by_id(user_id, "Users")
				self.render("newlink.html", 
							user = user,
							over18 = over18,
							title=title_var, 
							link=link_var, 
							description=description_var,
							tags=tag_var,
							audience = audience_for_redirect,
							error = error_var,
							food_related = food_related,
							)
			
			elif deadLinkFound == True:
				# Unsuccessful
				error_var = 'We are having trouble verifying the url you submitted.'
				user = return_thing_by_id(user_id, "Users")
				self.render("newlink.html", 
							user = user,
							over18 = over18,
							title=title_var, 
							link=link_var, 
							description=description_var,
							tags=tag_var,
							audience = audience_for_redirect,
							error = error_var,
							food_related = food_related,
							)

			else:
				# Success
				user = return_thing_by_id(user_id, "Users")

				new_object = Objects(title= title_var, 
									author_id= user_id, 			# Not sure how file uploads will work, so below are default links for an object
									author_name= author_name,
									epoch = float(time.time()),
									obj_type= 'link',

									obj_link= formatted_link_var,

									okay_for_kids = okay_for_kids_var,
									nsfw = nsfw_var,
									food_related = food_related,

									description=description_var,
									markdown = mkd_converted_description,
									printable = True,
									rank = new_rank(),
									num_user_when_created = num_users_now(),
									voter_list = [user_id],
									voter_vote = ["%s|1" % str(user_id)],
									)
				if the_tags:
					for tag in the_tags:
						logging.warning('adding tag %s' % tag)
						new_object.tags.append(tag)
						new_object.author_tags.append(tag)
				
				new_object.put()
				# db set delay:
				time.sleep(6)

				if the_tags:
					for tag in the_tags:
						if new_object.okay_for_kids == True:
							store_page_cache_kids(tag, update=True)
						if new_object.nsfw == True:
							store_page_cache_nsfw(tag, update=True)
						else:
							store_page_cache_sfw(tag, update=True)
					taskqueue.add(url ='/tagupdateworker', 
								  countdown = 6
								 )

				if nsfw_var == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update = True)

				if okay_for_kids_var == True:
					all_objects_query("kids", update = True)
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass

				object_page_cache(new_object.key().id(),update=True)

				# Update all front pages using the load_front_pages_from_memcache_else_query function
				global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
				if nsfw_var == True:
					# currently no other page types supported beyond "/"
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
				else:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
				if okay_for_kids_var == True:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)


				user_page_obj_com_cache(user_id, update=True)
				if user:
					for follower_id in user.follower_list:
						logging.warning('should sleep here')
						new_note(int(follower_id),
							"Objects|%d|%s| <a href='/user/%s'>%s</a> submitted <a href='/obj/%s'>%s</a>" % (
									int(new_object.key().id()),
										str(time.time()),
															str(user.key().id()),
																str(cgi.escape(user.username)),
																								str(new_object.key().id()),
																									str(cgi.escape(new_object.title))),
							)

				self.redirect('/newlink2/%d' % new_object.key().id())
class NewLinkPage2(Handler):
	def render_page(self, obj_num, error="",title="", main_img=""):
		obj_id = int(obj_num)

		query_args = self.request.arguments()
		querystring = None
		logging.warning(query_args)		
		if query_args:
			redirect = self.request.get('redirect')
			if redirect == "True":
				querystring = "?redirect=%s&error_1=%s&error_2=%s&rights_checked=%s" % (query_args[0],query_args[1],query_args[2],query_args[3])
			elif redirect == "filetype":
				querystring = "?redirect=%s&file_type_error=%s" % (query_args[0],query_args[1])
		if query_args:
			photo_upload_url = blobstore.create_upload_url('/upload_link_photo/%d%s' % (obj_id, querystring))
		else:
			photo_upload_url = blobstore.create_upload_url('/upload_link_photo/%d' % obj_id)

		error_1 = "" # checkbox
		error_2 = "" # image input
		rights = None
		file_type_error = ""
		redirect = self.request.get('redirect')
		if redirect == "True":
			error_1 = self.request.get('error_1')
			error_2 = self.request.get('error_2')
			rights = self.request.get('rights_checked')
			if error_2:
				rights = None
				error_1 = ""
		elif redirect == "filetype":
			file_type_error = self.request.get("file_type_error")
			error_2 = file_type_error

		the_obj = object_page_cache(obj_id)
		title_var = the_obj.title

		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		main_img_var = self.request.get('img')
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False

		if not (user_var and author_name):
			self.redirect("/")
			return

		if (the_obj.author_id != int(user_var)) or (the_obj.author_name != author_name):
			self.redirect("/")
			return
		else:
			user = return_thing_by_id(user_var, "Users")
			self.render("newlink2.html", 
						user = user,
						user_id = user_var,
						photo_upload_url = photo_upload_url,
						
						title=title_var,
						obj_id=obj_id, 
						error_1 = error_1,
						error_2 = error_2,
						rights = rights,
						)

	def get(self, obj_num):
		obj_id = int(obj_num)
		self.render_page(obj_num=obj_id)
class NewLinkUpload(ObjectUploadHandler):	
	def post(self, obj_num):
		obj_id = int(obj_num)

		the_obj = object_page_cache(obj_id)
		title_var = the_obj.title
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			self.redirect("/login")
		else:
			# User is signed in
			user_id = int(user_var)

			# Required fields
			main_img_var = self.request.get("img")
			rights = self.request.get("rights")
			
			if not (rights and main_img_var): #main_file_var and main_img_var and license_var):
				# Unsuccessful
				logging.warning(rights)
				logging.warning(main_img_var)
				error_1 = ""
				error_2 = ""
				if not rights:
					logging.warning("yep")
					error_1 = "It must be legal for you to share this image."
				if not main_img_var:
					logging.warning("yep2")
					error_2 = "Hmm, it looks like you forgot to select a image to upload."
				self.redirect("/newlink2/%d?redirect=True&error_1=%s&error_2=%s&rights_checked=%s" % (obj_id, error_1, error_2, rights))
				return

			else: 
				# Success

				# try:
				if 1==1:
					img_upload = None
					img_blob_key = None
					img_url = None

					try:
						img_upload = self.get_uploads()[0]
					except:
						self.redirect("/newlink2/%d" % obj_id)

					if img_upload:
						img_url = '/serve_obj/%s' % img_upload.key()
						img_blob_key = str(img_upload.key())
						filename_full = img_upload.filename
						filename = filename_full.split('.')
						#logging.warning(filename)
						if filename[-1].lower() not in ['png','jpg','jpeg','bmp']:
							logging.error('not "image" filetype, redirect')
							img_upload.delete()
							self.redirect("/newlink2/%d?redirect=filetype&file_type_error=%s" % (obj_id, "This file must be an allowed image filetype."))
							return

						# size limit
						global MAX_FILE_SIZE_FOR_OBJECTS
						if img_upload.size > MAX_FILE_SIZE_FOR_OBJECTS:
							logging.warning(img_upload)
							logging.warning(img_upload.size)
							img_upload.delete()
							self.redirect("/newlink2/%d?redirect=filetype&file_type_error=%s" % (obj_id, "This image is too large. Our maximum file size is 5MB. We're very sorry, but currently, hosting exceptionally large files is prohibitively expensive for us. Please upload a smaller version, preferably < 1MB. We are currently working on integrating imgur, but have not completed it.")) 
							return

						if img_upload.size > 100000:
							logging.warning(img_upload)
							logging.warning(img_upload.size)
							resize_ratio = int(100*(float(100000)/float(img_upload.size)))
							logging.warning(resize_ratio)
							# Resize the image
							logging.warning('db query img_upload blobinfo')
							logging.warning(img_upload.key())
							resized = images.Image(blob_key=img_upload)
							resized.horizontal_flip()
							resized.horizontal_flip()
							thumbnail = resized.execute_transforms(output_encoding=images.JPEG, 
																 quality = resize_ratio,
																)
							# Save Resized Image back to blobstore
							new_file = files.blobstore.create(mime_type='image/jpeg',
															  _blobinfo_uploaded_filename=filename_full)
							with files.open(new_file, 'a') as f:
								f.write(thumbnail)
							files.finalize(new_file)
							logging.warning(new_file)
							new_key = files.blobstore.get_blob_key(new_file)   
							# Remove the original image
							img_upload.delete()
							# Reset img_upload variable
							img_upload = blobstore.BlobInfo.get(new_key)
							logging.warning('db query get blobinfo')
							img_url = '/serve_obj/%s' % img_upload.key()
							img_blob_key = str(img_upload.key())
					else:
						self.redirect("/newlink2/%d" % obj_id)

					new_object = Objects.get_by_id(obj_id)

					new_object.main_img_link = img_url
					new_object.main_img_blob_key = img_upload.key()
					new_object.main_img_filename = str(img_upload.filename)

					new_object.put()

					# if img_upload:
					# 	new_object_photo = ObjectBlob(blob_type = 'image',
					# 									priority = 1,
					# 									obj_id = int(new_object.key().id()),
					# 									uploader = int(new_object.author_id), 
					# 									blob_key = img_upload.key(),
					# 									filename = str(img_upload.filename),

					# 									key_name = "blob|%s" % str(img_upload.key())
					# 									)
					# 	new_object_photo.put()
					# 	memcache.set("objectblob|%s" % str(new_object_photo.blob_key), new_object_photo)
					# else:
					# 	pass

					if new_object.nsfw == True:
						all_objects_query("nsfw", update = True, delay = 6)
					else:
						all_objects_query("sfw", update = True, delay = 6)

					if new_object.okay_for_kids == True:
						all_objects_query("kids", update = True)
						user_page_obj_com_cache_kids(user_id, update = True)
					else:
						pass

					object_page_cache(new_object.key().id(),update=True)
					user_page_object_cache(user_id, update=True) # No longer needed really...
					user_page_obj_com_cache(user_id, update=True)
					
					# Update all front pages using the load_front_pages_from_memcache_else_query function
					global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
					if new_object.nsfw == True:
						# currently no other page types supported beyond "/"
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
					else:
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
					if new_object.okay_for_kids == True:
						load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)

					self.redirect('/obj/%d' % new_object.key().id())

				#except:
				else:
					self.redirect('/upload_failure.html')
class NewTorPage(Handler):
	def render_page(self, error="", over18 = False, link="", title="", description="", tags=""):
		
		user_id = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False
		if not (user_id or author_name or over18):
			self.redirect("/login")
			return
		user = return_thing_by_id(user_id, "Users")
		if not user:
			self.error(400)
			return
		else:
			audience = "kids"
			self.render("newtor.html", 
						user = user,
						user_id = user_id,
						over18 = over18,
						audience = audience,	
						)

	def get(self):
		self.render_page()

	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			error_var = "Sorry, but you need to be logged in to upload an object."
			self.render("newtor.html", error = error_var)
		else:
			# User is signed in.
			user_id = int(user_var)
			if over18 == "True":
				over18 = True
			else:
				over18 = False

			# Required fields
			title_var = self.request.get("title")
			link_var = self.request.get("link")

			rights = self.request.get('rights')

			food_related = self.request.get("food_related")
			if food_related:
				food_related = True
			else:
				food_related = False

			# Kids and NSFW entries (if available)
			# Here, defaults are okay-for-kids/sfw, because no entry if kids online:
			okay_for_kids_var = True
			nsfw_var = False
			audience_var = self.request.get("audience")
			audience_for_redirect = audience_var
			if audience_var: 
				if audience_var == "kids":
					pass
				elif audience_var == "sfw":
					okay_for_kids_var = False
				elif audience_var == "nsfw":
					okay_for_kids_var = False
					nsfw_var = True
				else:
					logging.error("New Tor -- nsfw parser not working properly")
			else:
				pass

			# Optional fields
			description_var = self.request.get("description")
			markdown_var = convert_text_to_markdown(description_var)
			tag_var = self.request.get("tags")
			the_tags = None
			if tag_var:
				the_tags = tag_var.split(', ')
				# tag string section
				tag_list = the_tags
				logging.warning(tag_list)
				tag_list = remove_list_duplicates(tag_list)
				logging.warning(tag_list)
				tag_list = strip_list_whitespace(tag_list)
				logging.warning(tag_list)
				tag_list = remove_unsafe_chars_from_tags(tag_list)
				tag_list.sort()
				if not tag_list:
					tag_list = ["None"]
					logging.warning("public tag list set to None")
				the_tags = tag_list

			# Check whether the url links to an actual site:
			# 3 tries:
			# 1st try: plain link (e.g. "http://www.google.com" = success!)
			# 2nd try: no http (e.g. "www.google.com" -> "http://www.google.com" = success!)
			# 3rd try: no www either (e.g. "google.com" -> "http://www.google.com" = success!)
			formatted_link_var = check_url(link_var)
			deadLinkFound = True
			if formatted_link_var:
				deadLinkFound = False

			if not (title_var and link_var):
				# Unsuccessful
				error_var = 'You must include a title and a link.'
				user = return_thing_by_id(user_id, "Users")
				self.render("newtor.html", 
							user = user,
							user_id = user_id,
							over18 = over18,
							title=title_var, 
							link=link_var, 
							description=description_var,
							tags=tag_var,
							audience = audience_for_redirect,
							error = error_var,
							food_related = food_related,
							)
			
			elif deadLinkFound == True:
				# Unsuccessful
				error_var = 'We are having trouble verifying the url you submitted.'
				user = return_thing_by_id(user_id, "Users")
				self.render("newtor.html", 
							user = user,
							user_id = user_id,
							over18 = over18,
							title=title_var, 
							link=link_var, 
							description=description_var,
							tags=tag_var,
							audience = audience_for_redirect,
							error = error_var,
							food_related = food_related,
							)


			else: # Success
				user = return_thing_by_id(user_id, "Users")
				new_object = Objects(title= title_var, 
									author_id= user_id, 			# Not sure how file uploads will work, so below are default links for an object
									author_name= author_name,
									obj_type= 'tor',
									epoch = float(time.time()),

									obj_link= formatted_link_var,

									okay_for_kids = okay_for_kids_var,
									nsfw = nsfw_var,
									food_related= food_related,

									description=description_var,
									markdown = markdown_var,
									printable = True,
									rank = new_rank(),
									num_user_when_created = num_users_now(),
									voter_list = [user_id],
									voter_vote = ["%s|1" % str(user_id)],
									)
				if the_tags:
					for tag in the_tags:
						new_object.tags.append(tag)

				new_object.put()

				# db set delay
				time.sleep(6)

				if the_tags:
					for tag in the_tags:
						if new_object.okay_for_kids == True:
							store_page_cache_kids(tag, update=True)
						if new_object.nsfw == True:
							store_page_cache_nsfw(tag, update=True)
						else:
							store_page_cache_sfw(tag, update=True)
					taskqueue.add(url ='/tagupdateworker', 
								  countdown = 6
								 )

				if nsfw_var == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update = True)

				if okay_for_kids_var == True:
					all_objects_query("kids", update = True)
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass

				object_page_cache(new_object.key().id(),update=True)

				# Update all front pages using the load_front_pages_from_memcache_else_query function
				global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
				if nsfw_var == True:
					# currently no other page types supported beyond "/"
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
				else:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
				if okay_for_kids_var == True:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)


				user_page_obj_com_cache(user_id, update=True)
				if user:
					for follower_id in user.follower_list:
						logging.warning('should sleep here')
						new_note(int(follower_id),
							"Objects|%d|%s| <a href='/user/%s'>%s</a> summitted a torrent for <a href='/obj/%s'>%s</a>." % (
									int(new_object.key().id()),
										str(time.time()),
															str(user.key().id()),
																str(cgi.escape(user.username)),
																								str(new_object.key().id()),
																									str(cgi.escape(new_object.title))),
							)

				self.redirect('/newlink2/%d' % new_object.key().id())

class SignUpPage(Handler):
	def render_page(self, username="", password="", verify="", email="", error="", img_file=""):
		#photo_upload_url = blobstore.create_upload_url('/user_img_upload')
		logging.warning(username)
		next_url = self.request.headers.get('referer', '/')
		no_search_bar = True
		self.render("signup.html", 
					username=username, 
					password=password, 
					verify=verify, 
					email=email, 
					error=error, 
					img_file=img_file, 
					#photo_upload_url=photo_upload_url,
					next_url = next_url,

					no_search_bar = no_search_bar,
					)
	def get(self):
		self.render_page()

	def post(self):
		next_url = str(self.request.get('next_url'))
		if not next_url or is_blacklisted_referer(next_url):
			next_url = '/'

		name_var = self.request.get("username")
		password_plain = self.request.get("password")
		verify_var = self.request.get("verify")
		email_var = self.request.get("email")			
		over18_var = self.request.get("over18")
		tos_var = self.request.get("tos")
		infinite_scroll_input = self.request.get("infinite")
		
		no_infinite_scroll_var = False
		if not infinite_scroll_input:
			no_infinite_scroll_var = True

		# over18_var string, 'True', converted to boolean
		if over18_var:
			over18_var = False
		else:
			over18_var = True

		# check the username
		username_already_exists = False
		same_names = Users.all().filter("username_lower =", name_var.lower())
		for user in same_names:
			if user.username_lower == name_var.lower():
				username_already_exists = True
				break

		# add global fake names to list to make sure people don't accidentally pick a fake name the admins use
		global FAKE_NAME_LIST
		fake_names = []
		for name in FAKE_NAME_LIST:
			fake_names.append(name.lower())
		if name_var.lower() in fake_names:
			username_already_exists = True

		logging.warning("User signup hits DB every time here")
		
		if username_already_exists:
			# name not unique
			error_var = "That name is already taken."
			self.render_page(email=email_var, error=error_var, username="")
			return

		#must have unique name to proceed
		if not (name_var and password_plain):
			# User did not enter both a name and password
			error_var = "You must fill in a name and password"
			self.render_page(username=name_var, email=email_var, error=error_var)
			return

		#must have entered both a name and password
		if not (password_plain == verify_var):
			# User's password and verified passwords did not match
			error_var = "Passwords did not match"
			self.render_page(username=name_var, error=error_var, email = email_var)
			return

		if (len(password_plain) < 6) or (len(name_var) < 4):
			if (len(password_plain) < 6) and (len(name_var) < 4):
				error_var = "Your name and password are too short. Names must be at least 4 characters and passwords must be at least 6 characters."
				self.render_page(error=error_var, email = email_var)
				return
			elif (len(name_var) < 4):
				error_var = "Your name is too short. Names must be at least 4 characters."
				self.render_page(error=error_var, email = email_var)
				return
			elif (len(password_plain) < 6):
				error_var = "Your password is too short. Passwords must be at least 6 characters."
				self.render_page(username=name_var, error=error_var, email = email_var)
				return
			else:
				logging.error('something in the name/password stuff went wrong.')
				self.error(400)
				return

		#check for unsafe chars
		global URL_SAFE_CHARS
		for i in name_var:
			if i not in URL_SAFE_CHARS:
				error_var = 'Your name contains disallowed characters. Please only use letters, numbers, "-" and "_".'
				self.render_page(error=error_var, email = email_var)
				return

		#password must equal the verified password to proceed
		if email_var and (not emailcheck.isValidEmailAddress(email_var)):
			# user entered an email, but it was invalid
			error_var = "That doesn't seem to be a valid email address"
			self.render_page(username=name_var, error=error_var, email = email_var)
			return

		if not tos_var:
			# user has not accepted terms
			error_var = "You must be an adult and accept our terms of service."
			self.render_page(username=name_var, error=error_var, email = email_var)
			return

		# Success!
		## If here, the user will be registered:
		new_user = Users(username = name_var,
						username_lower = name_var.lower(), 
						hashed_password = '%s' % (make_pw_hash(name_var, password_plain)), 
						unconfirmed_email= email_var,
						over18=over18_var,
						epoch=float(time.time()),
						random_string = random_string_generator(),
						no_infinite_scroll = no_infinite_scroll_var,
						)
		new_user.put()
		self.login(new_user)

		user_page_cache(new_user.key().id(), update = True)

		if email_var:
			confirmation_email(email_var)

		self.redirect('/welcome')

class TermsPage(Handler):
	def get(self):
		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")
		self.render("tos.html", user=user, user_id = user_id)

class LoginPage(Handler):

	def get(self):
		next_url = self.request.headers.get('referer', '/')
		logging.warning(next_url)
		no_search_bar = True
		self.render("login.html", 
					next_url = next_url,
					no_search_bar = no_search_bar,
					)

	def post(self):
		next_url = str(self.request.get('next_url'))
		logging.warning(next_url)
		if (not next_url) or is_blacklisted_referer(next_url):
			next_url = '/'
		logging.warning(next_url)

		name_var = self.request.get("username")
		password_var = self.request.get("password")
		remember_var = self.request.get("remember")	

		u = Users.logsin(name_var, password_var)

		if u:
			if remember_var:
				self.login_and_remember(u)
			else:
				self.login(u)
			self.redirect(next_url)
		else:
			error_var = "Invalid login information."
			self.render('login.html', error = error_var, next_url = next_url)
class WelcomePage(Handler):
	def render_page(self):
		user = self.return_user_if_cookie()
		user_id = None
		if user:
			user_id = user.key().id()
		logging.warning('db query on WelcomePage')
		self.render("welcome.html",
					 user = user, 
					 user_id = user_id
					 )

	def get(self):
		self.render_page()

class ContactPage(Handler):
	def render_page(self):
		user = self.return_user_if_cookie()
		user_id = None
		if user:
			user_id = user.key().id()
		logging.warning('db query on ContactPage')
		self.render("contact.html",
					 user = user, 
					 user_id = user_id
					 )

	def get(self):
		self.render_page()

class LogoutPage(Handler):
	def get(self):
		next_url = self.request.headers.get('referer', '/')
		self.logout()
		self.redirect(next_url)
class NsfwPage(Handler):
	def render_front(self):
		over18 = self.check_cookie_return_val("over18")
		the_list = []
		if over18 != "True":
			self.redirect('/')
		user = self.return_user_if_cookie()
		object_query = all_objects_query("nsfw")
		cursor = self.request.get("cursor")
		if cursor:
			object_query.with_cursor(cursor)
		the_objects = object_query.fetch(10)
		cursor = object_query.cursor()

		the_users = users_cache()
		the_comments = comments_cache()

		has_cookie = None
		active_username = "No Valid Cookie"
		active_user = self.check_cookie_return_val("username")
		user_id = self.check_cookie_return_val("user_id")
		if active_user and user_id:
			active_username = active_user
			has_cookie = "This adult of questionable taste right here has a valid cookie."
		else:
			pass

		the_dict = cached_vote_data_for_masonry(the_objects, user_id)


		# Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		self.render("nsfw.html",
					user=user, 
					username=active_username, 
					user_id = user_id,
					the_objects=the_objects, 
					the_users=the_users, 
					the_comments=the_comments, 
					has_cookie=has_cookie,
					the_dict = the_dict,
					cursor = cursor,
					)

	def get(self):
		over18 = self.check_cookie_return_val("over18")
		if over18 != "True":
			self.redirect('/')
		else:
			self.render_front()

	def post(self):
		pass

class ObjFileServe(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, blob_key):
		if not blobstore.get(blob_key):
			self.error(404)
			return
		else:
			# blob_type = None
			# obj_blob = return_object_blob_by_key_name(blob_key)
			# if obj_blob:
			# 	blob_type = obj_blob.blob_type
			# else:
			# 	pass
			# if blob_type is not None and (blob_type == "data"):
			# 	#resource = str(urllib.unquote(blob_key))
			# 	#blob_info = blobstore.BlobInfo.get(resource)
			# 	logging.warning("download")
			# 	self.send_blob(blob_key, save_as = obj_blob.filename)
			# else:
			# 	self.send_blob(blob_key)
			resource = str(urllib.unquote(blob_key))
			blob = blobstore.BlobInfo.get(resource)
			blob_filename = blob.filename
			if blob_filename.split('.')[-1] not in ALLOWED_IMAGE_EXTENTIONS:
				logging.warning("download")
				self.send_blob(blob_key, save_as = blob.filename)
			else:
				self.send_blob(blob_key)
class VoteHandler(Handler):
	"""Handles js vote requests."""
	#borrowed from danholevoet on github, appengine-overheard-python, give attribution (apache license)

	def post(self):
		"""Add or change a vote for a user."""
		user_id = self.check_cookie_return_val('user_id')
		if not user_id:
		  self.response.set_status(403, 'Forbidden')
		  self.error(403)
		  return
		obj_id = self.request.get('obj_id')
		vote = self.request.get('vote')
		if (not vote in ['1', '0', '-1']) or (not obj_id):
		  self.response.set_status(400, 'Bad Request')
		  self.error(403)
		  return
		vote = int(vote)
		# trying cached version
		one_long_vote_function(obj_id, user_id, vote)
		#set_vote(int(obj_id), user_id, vote)
class CommentVoteHandler(Handler):
	def post(self):
		"""Add or change a vote on a comment."""
		user_id = self.check_cookie_return_val('user_id')
		if not user_id:
		  self.response.set_status(403, 'Forbidden')
		  return
		com_id = self.request.get('com_id')
		logging.warning('com_id')
		vote = self.request.get('votecom')
		if not vote in ['1', '0', '-1']:
		  self.response.set_status(400, 'Bad Request')
		  return
		vote = int(vote)
		logging.warning(vote)

		# trying cached version
		one_long_comment_vote_function(int(com_id), user_id, vote)
class RateHandler(Handler):
	"""Handles js rate requests."""

	def post(self):
		"""Add or change a rate for a user."""
		user_id = self.check_cookie_return_val('user_id')
		if not user_id:
		  self.response.set_status(403, 'Forbidden')
		  return
		obj_id = self.request.get('obj_id')
		rate = self.request.get('rate')
		if not rate in ['1', '2', '3', '4', '5']:
		  self.response.set_status(400, 'Bad Request')
		  return
		rate = int(rate)
		one_long_rate_function(int(obj_id), user_id, rate)	
class FlagHandler(Handler):
	"""Handles js flag requests."""

	def post(self):
		"""Add or change a flag for a user."""
		user_id = self.check_cookie_return_val('user_id')
		if not user_id:
		  self.response.set_status(403, 'Forbidden')
		  return
		obj_id = self.request.get('obj_id')
		flag = self.request.get('flag')
		if not flag in ['0', '1']:
		  self.response.set_status(400, 'Bad Request')
		  return
		flag = int(flag)
		#set_flag(int(obj_id), user_id, flag)
		one_long_flag_function(int(obj_id), user_id, flag)
class CommentFlagHandler(Handler):
	"""Handles js flag requests for comments."""

	def post(self):
		"""Add or change a flag for a user."""
		user_id = self.check_cookie_return_val('user_id')
		if not user_id:
		  self.response.set_status(403, 'Forbidden')
		  return
		com_id = self.request.get('com_id')
		flag = self.request.get('flagcom')
		if not flag in ['0', '1']:
		  self.response.set_status(400, 'Bad Request')
		  return
		flag = int(flag)
		#set_flag(int(obj_id), user_id, flag)
		one_long_comment_flag_function(int(com_id), user_id, flag)
class DeleteCommentHandler(Handler):
	def post(self):
		user_id = self.check_cookie_return_val('user_id')
		user_id = int(user_id)
		com_id = self.request.get('com_id')
		com = return_com_by_id(com_id)
		# regardless of children, these will change
		com.author_id = None
		com.author_name = None
		com.washed = True	
		if com.has_children == False:
			com.text = " "
			com.upvotes = None
			com.downvotes = None
			com.netvotes = None
			com.voter_list = []
			com.voter_vote = []
			com.flagger_list = []
			com.flagger_flag = []
			com.rank = None
			com.votesum = None
			com.flagsum = None

			com.deleted = True
		else:
			com.text = "deleted"
		com.put()
		logging.warning('db put -- comment deleted')
		
		obj_comments = obj_comment_cache(com.obj_ref_id, update=True, delay = 6)
		the_object = return_obj_by_id(com.obj_ref_id)
		the_object.total_num_of_comments = len(obj_comments)
		the_object.put()
		memcache.set("Objects_%s" % str(com.obj_ref_id), [the_object])

		user_page_comment_cache(user_id, update=True)
		user_page_obj_com_cache(user_id, update=True)
		user_page_obj_com_cache_kids(user_id, update=True)
class BlockHandler(Handler):
	# an interesting problem, when the user makes repeated
	# block requests without leaving they page,
	# it adds an extra post request each time... not an
	# overt problem, but something to be concerned about
	def post(self):
		blocker_id = int(self.check_cookie_return_val('user_id'))
		blockee_id = int(self.request.get('blockee_id'))
		block = self.request.get('block')
		unblock = self.request.get('unblock')
		if not (block or unblock):
			logging.error('neither block nor unblock')
			self.error(404)
			return
		elif block and unblock:
			logging.error('both block and unblock')
			logging.warning(block)
			logging.warning(unblock)
			self.error(404)
			return
		if blocker_id is None or blockee_id is None:
			self.error(404)
			return
		blocker = return_thing_by_id(blocker_id, "Users")
		blockee = return_thing_by_id(blockee_id, "Users")
		blocked = False
		if str(blocker_id) in blockee.blocked_by_list:
			if str(blockee_id) not in blocker.block_list:
				logging.error('block lists are not matching')
				self.error(404)
				return
			else:
				blocked = True

		if blocked is True:
			if block:
				logging.warning('user has already been blocked')
				return
			elif unblock:
				# blocked_by_list update
				blockee.blocked_by_list.remove(str(blocker_id))
				logging.warning(blockee.blocked_by_list)
				if len(blockee.blocked_by_list) == 0:
					blockee.blocked_by_list.append("None")
				logging.warning(blockee.blocked_by_list)
				blockee.put()
				memcache.set("Users_%d" % int(blockee_id), [blockee])
				# block_list update
				blocker.block_list.remove(str(blockee_id))
				logging.warning(blocker.block_list)
				if len(blocker.block_list) == 0:
					blocker.block_list.append("None")
				logging.warning(blocker.block_list)
				blocker.put()
				memcache.set("Users_%d" % int(blocker_id), [blocker])
			else:
				self.error(404)
				return
		else:
			if block:
				logging.warning('blocking this user')

				# blocked_by_list update
				if "None" in blockee.blocked_by_list:
					blockee.blocked_by_list.remove("None")
				blockee.blocked_by_list.append(str(blocker_id))
				logging.warning(blockee.blocked_by_list)
				the_list = list(blockee.blocked_by_list)
				the_set = set(the_list)
				the_list = list(the_set)
				blockee.blocked_by_list = []
				blockee.blocked_by_list = the_list
				blockee.put()
				memcache.set("Users_%d" % int(blockee_id), [blockee])

				# block_list update
				if "None" in blocker.block_list:
					blocker.block_list.remove("None")
				blocker.block_list.append(str(blockee_id))
				logging.warning(blocker.block_list)
				the_list = list(blocker.block_list)
				the_set = set(the_list)
				the_list = list(the_set)
				blocker.block_list = []
				blocker.block_list = the_list
				blocker.put()
				memcache.set("Users_%d" % int(blocker_id), [blocker])				
			elif unblock:
				logging.warning('user is not blocked')
				return
			else:
				self.error(404)
				return
class FollowHandler(Handler):
	def post(self):
		followee_id = int(self.request.get("followee_id"))
		follower_id = int(self.check_cookie_return_val("user_id"))
		follow = self.request.get('follow')
		unfollow = self.request.get('unfollow')

		if not (follow or unfollow):
			logging.error('neither follow nor unfollow')
			self.error(404)
			return
		elif follow and unfollow:
			logging.error('both follow and unfollow')
			logging.warning(follow)
			logging.warning(unfollow)
			self.error(404)
			return
		if not (followee_id and follower_id):
			logging.error('not both')
			self.error(404)
			return

		followee = return_thing_by_id(followee_id, "Users")
		if followee is None:
			self.error(404)
			return

		if follow:
			if str(follower_id) in followee.follower_list:
				logging.warning('already a follower')
				return
			logging.warning('following user')
			if "None" in followee.follower_list:
				followee.follower_list.remove("None")
			followee.follower_list.append(str(follower_id))
			the_list = followee.follower_list
			the_set = set(the_list)
			the_list = list(the_set)
			followee.follower_list = []
			followee.follower_list = the_list
			logging.warning(followee.follower_list)
			followee.put()
			memcache.set("Users_%d" % followee.key().id(), [followee])

		elif unfollow:
			if str(follower_id) not in followee.follower_list:
				logging.warning('not actually following')
				return
			logging.warning('unfollowing user')
			followee.follower_list.remove(str(follower_id))
			if len(followee.follower_list) == 0:
				followee.follower_list.append("None")
			the_list = followee.follower_list
			the_set = set(the_list)
			the_list = list(the_set)
			followee.follower_list = []
			followee.follower_list = the_list
			logging.warning(followee.follower_list)
			followee.put()
			memcache.set("Users_%d" % followee.key().id(), [followee])	

		else:
			#this shouldn't happen
			self.error(404)
			return
class PrintshelfAddHandler(Handler):
	def post(self):
		obj_id = int(self.request.get("obj_id"))
		user_id = int(self.check_cookie_return_val("user_id"))
		to_print = self.request.get('to_print')
		printed = self.request.get('printed')

		if not (to_print or printed):
			logging.error('neither to print nor printed')
			self.error(404)
			return
		elif to_print and printed:
			logging.error('both to print and printed')
			logging.warning(to_print)
			logging.warning(printed)
			self.error(404)
			return
		if not (obj_id and user_id):
			logging.error('not both obj and user')
			self.error(404)
			return

		user = return_thing_by_id(user_id, "Users")
		if user is None:
			logging.warning('not both obj and user from return_thing_by_id')
			self.error(404)
			return
		if to_print:
			if str(obj_id) in user.to_print_list:
				logging.warning('already in to print list')
				return
			logging.warning('adding this to print')
			if "None" in user.to_print_list:
				user.to_print_list.remove("None")
			was_in_printed_list = False
			if str(obj_id) in user.has_printed_list:
				was_in_printed_list = True
				logging.warning('removing from has printed list')
				user.has_printed_list.remove(str(obj_id))
			user.to_print_list.append(str(obj_id))
			the_list = user.to_print_list
			the_set = set(the_list)
			the_list = list(the_set)
			user.to_print_list = []
			user.to_print_list = the_list
			logging.warning(user.to_print_list)
			user.put()
			memcache.set("Users_%d" % user.key().id(), [user])
			if was_in_printed_list == True:
				return_printed_by_list(obj_id, update=True, delay=6)


		elif printed:
			if str(obj_id) in user.has_printed_list:
				logging.warning('already in has printed list')
				return
			logging.warning('adding this to has printed list')
			if "None" in user.has_printed_list:
				user.has_printed_list.remove("None")
			if str(obj_id) in user.to_print_list:
				logging.warning('removing from to print list')
				user.to_print_list.remove(str(obj_id))
			user.has_printed_list.append(str(obj_id))
			the_list = user.has_printed_list
			the_set = set(the_list)
			the_list = list(the_set)
			user.has_printed_list = []
			user.has_printed_list = the_list
			logging.warning(user.has_printed_list)
			user.put()
			memcache.set("Users_%d" % user.key().id(), [user])
			return_printed_by_list(obj_id, update=True, delay=6)

		else:
			#this shouldn't happen
			self.error(404)
			return
class PrintshelfRemoveHandler(Handler):
	def post(self):
		user_id = int(self.check_cookie_return_val("user_id"))
		obj_id = int(self.request.get("obj_id"))
		remove = self.request.get('remove')
		printshelf_id = self.request.get('printshelf_id')

		if remove not in ['to_print', 'has_printed']:
			logging.error('bad request')
			self.error(404)
			return
		user = return_thing_by_id(user_id, "Users")
		if user is None:
			logging.error("no user found")
			self.error(404)
			return
		logging.warning(user_id)
		logging.warning(printshelf_id)
		if printshelf_id is None:
			logging.error('no printshelf_id')
			self.error(404)
			return
		if int(user_id) != int(printshelf_id):
			logging.error('user is not author')
			self.error(404)
			return
		if remove == 'to_print':
			logging.warning('removing to_print item')
			logging.warning(user.to_print_list)
			if str(obj_id) not in user.to_print_list:
				logging.warning("obj no in to print list")
				return
			user.to_print_list.remove(str(obj_id))
			if len(user.to_print_list) == 0:
				user.to_print_list.append("None")
			logging.warning(user.to_print_list)
			user.put()
			memcache.set("Users_%d" % user_id, [user])
		else:
			# remove == 'has_printed'
			logging.warning('removing has_printed item')
			logging.warning(user.has_printed_list)
			if str(obj_id) not in user.has_printed_list:
				logging.warning("obj no in has printed list")
				return
			user.has_printed_list.remove(str(obj_id))
			if len(user.has_printed_list) == 0:
				user.has_printed_list.append("None")
			logging.warning(user.has_printed_list)
			user.put()
			memcache.set("Users_%d" % user_id, [user])
			return_printed_by_list(obj_id, update=True, delay=6)

class EditCommentHandler(Handler):
	def post(self):
		user_id = self.check_cookie_return_val('user_id')
		logging.warning(user_id)
		user_id = int(user_id)
		user = return_thing_by_id(user_id, "Users")
		submitted_hash = self.request.get("verify")
		logging.warning(submitted_hash)
		user_hash = hashlib.sha256(user.random_string).hexdigest()
		logging.warning(user_hash)
		if submitted_hash != user_hash:
			logging.warning("User is attempting to hack our comment edits")
			return
		new_text = self.request.get('text')
		logging.warning(new_text)
		com_id = self.request.get('save_id')
		com = return_com_by_id(com_id)
		com_author = return_thing_by_id(com.author_id, "Users")
		com_author_hash = hashlib.sha256(com_author.random_string).hexdigest()
		if submitted_hash != com_author_hash:
			logging.warning("User is attempting to hack our comment edits")
			return
		
		# convert to markdown2
		escaped_comment_text = cgi.escape(new_text)
		mkd_converted_comment = mkd.convert(escaped_comment_text)

		com.text = new_text
		com.markdown = mkd_converted_comment
		com.put()
		logging.warning('db put -- comment edited')
		obj_comment_cache(com.obj_ref_id, update=True, delay = 6)
		user_page_comment_cache(user_id, update=True)
		user_page_obj_com_cache(user_id, update=True)
		user_page_obj_com_cache_kids(user_id, update=True)

class UniMain(FrontHandler):
	def render_front(self):
		pass
		# user=self.return_user_if_cookie()
		# over18 = self.check_cookie_return_val("over18")
		# the_list = []
		# if over18 != "True":
		# 	over18 = False
		# else:
		# 	over18 = True
		# the_list = learn_front_cache()
		# the_objects = the_list[0]

		# has_cookie = None
		# active_username = "No Valid Cookie"
		# active_user = self.check_cookie_return_val("username")
		# user_id = self.check_cookie_return_val("user_id")
		# if active_user and user_id:
		# 	active_username = active_user
		# 	has_cookie = "This guy right here has a valid cookie for realz."
		# else:
		# 	pass
		
		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)


		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# self.render("uni_front.html", 
		# 			the_objects=the_objects, 
					
		# 			user=user, 
		# 			user_id = user_id,
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict)

	def get(self):
		self.render_front_page("/university")

	def post(self):
		pass

class UniMainNew(FrontHandler):
	def render_front(self):
		pass
	def get(self):
		self.render_front_page("/newuniversity")

	def post(self):
		pass

class UniMainTop(FrontHandler):
	def render_front(self):
		pass
	def get(self):
		self.render_front_page("/topuniversity")

	def post(self):
		pass		

class UniMainVideo(FrontHandler):
	def render_front(self):
		pass
		# user=self.return_user_if_cookie()
		# over18 = self.check_cookie_return_val("over18")
		# the_list = []
		# if over18 != "True":
		# 	over18 = False
		# else:
		# 	over18 = True
		# the_list = learn_front_cache()
		# the_objects = the_list[0]

		# has_cookie = None
		# active_username = "No Valid Cookie"
		# active_user = self.check_cookie_return_val("username")
		# user_id = self.check_cookie_return_val("user_id")
		# if active_user and user_id:
		# 	active_username = active_user
		# 	has_cookie = "This guy right here has a valid cookie for realz."
		# else:
		# 	pass
		
		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)


		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# self.render("uni_front.html", 
		# 			the_objects=the_objects, 
					
		# 			user=user, 
		# 			user_id = user_id,
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict)

	def get(self):
		self.render_front_page("/video")

	def post(self):
		pass		
class NewLessonPage(Handler):
	def render_page(self, error="", link="", title="", subject="", description="", tags=""):
		user = self.return_user_if_cookie()
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False
		if not (user_var or author_name or over18):
			self.redirect("/")
		else:
			self.render("newlesson.html", 
						user = user,
						user_id = user_var,
						error=error,
						over18 = over18,

						link = link,
						title=title, 
						subject=subject,
						description=description,
						tags=tags)

	def get(self):
		self.render_page()

	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			error_var = "Sorry, but you need to be logged in to submit a lesson."
			self.render("newlesson.html", error = error_var)
		else:
			# User is signed in.
			user_id = int(user_var)

			# Required fields
			title_var = self.request.get("title")
			subject_var = self.request.get("subject")
			link_var = self.request.get("link")
			skill_var = self.request.get("skill")
			if skill_var == "None":
				skill_var = None
			else:
				pass

			# Kids and NSFW entries (if available)
			# Here, defaults are okay-for-kids/sfw, because no entry if kids online:
			okay_for_kids_var = True
			nsfw_var = False
			audience_var = self.request.get("audience")
			if audience_var: 
				if audience_var == "kids":
					pass
				elif audience_var == "sfw":
					okay_for_kids_var = False
				elif audience_var == "nsfw":
					okay_for_kids_var = False
					nsfw_var = True
				else:
					logging.error("New Link -- nsfw parser not working properly")
			else:
				pass

			# Optional fields
			description_var = self.request.get("description")
			markdown_var = convert_text_to_markdown(description_var)
			tag_var = self.request.get("tags")
			the_tags = None
			if tag_var:
				the_tags = tag_var.split(', ')
				# tag string section
				tag_list = the_tags
				logging.warning(tag_list)
				tag_list = remove_list_duplicates(tag_list)
				logging.warning(tag_list)
				tag_list = strip_list_whitespace(tag_list)
				logging.warning(tag_list)
				tag_list = remove_unsafe_chars_from_tags(tag_list)
				tag_list.sort()
				if not tag_list:
					tag_list = ["None"]
					logging.warning("public tag list set to None")
				the_tags = tag_list

			# Check whether the url links to an actual site:
			# 3 tries:
			# 1st try: plain link (e.g. "http://www.google.com" = success!)
			# 2nd try: no http (e.g. "www.google.com" -> "http://www.google.com" = success!)
			# 3rd try: no www either (e.g. "google.com" -> "http://www.google.com" = success!)
			formatted_link_var = check_url(link_var)
			deadLinkFound = True
			if formatted_link_var:
				deadLinkFound = False
				
			if not (title_var and link_var):
				# Unsuccessful
				error_var = "Please complete all required information"
				self.render("newlesson.html", 
							error=error_var, 
							title=title_var, 
							subject=subject_var,
							link=link_var, 
							description=description_var,
							tags=tag_var)
			
			elif deadLinkFound == True:
				# Unsuccessful
				error_var = 'We are having trouble verifying the url you submitted. Please paste in the full url (including the "http://").'
				self.render("newlesson.html", 
							error=error_var, 
							title=title_var, 
							subject=subject_var,
							link="", 
							description=description_var,
							tags=tag_var)

			else:
				# Success
				user = return_thing_by_id(user_id, "Users")
				new_object = Objects(title= title_var, 
									author_id= user_id, 			# Not sure how file uploads will work, so below are default links for an object
									author_name= author_name,
									obj_type= 'learn',
									epoch = float(time.time()),

									obj_link= formatted_link_var,

									okay_for_kids = okay_for_kids_var,
									nsfw = nsfw_var,

									learn = True,
									learn_subject = subject_var,
									learn_skill = skill_var,

									description=description_var,
									markdown = markdown_var,
									rank = new_rank(),
									num_user_when_created = num_users_now(),
									voter_list = [user_id],
									voter_vote = ["%s|1" % str(user_id)],
									)
				if the_tags:
					for tag in the_tags:
						new_object.tags.append(tag)
						new_object.author_tags.append(tag)

				new_object.put()

				# db set delay:
				time.sleep(6)

				if the_tags:
					for tag in the_tags:
						if new_object.okay_for_kids == True:
							store_page_cache_kids(tag, update=True)
						if new_object.nsfw == True:
							store_page_cache_nsfw(tag, update=True)
						else:
							store_page_cache_sfw(tag, update=True)
					taskqueue.add(url ='/tagupdateworker', 
								  countdown = 6
								 )

				if nsfw_var == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update = True)
				logging.warning('made it this far')
				if okay_for_kids_var == True:
					all_objects_query("kids", update = True)
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass
				#learn_front_cache(update = True)
				object_page_cache(new_object.key().id(),update=True)
				user_page_obj_com_cache(user_id, update=True)

				# Update all front pages using the load_front_pages_from_memcache_else_query function
				global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
				if nsfw_var == True:
					# currently no other page types supported beyond "/"
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
				else:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
				if okay_for_kids_var == True:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)


				if user:
					for follower_id in user.follower_list:
						logging.warning('should sleep here')
						new_note(int(follower_id),
							"Objects|%d|%s| <a href='/user/%s'>%s</a> summitted a new tutorial: <a href='/obj/%s'>%s</a>." % (
									int(new_object.key().id()),
										str(time.time()),
															str(user.key().id()),
																str(cgi.escape(user.username)),
																								str(new_object.key().id()),
																									str(cgi.escape(new_object.title))),
							)
				self.redirect('/obj/%d' % new_object.key().id())
class NewAskPage(Handler):
	def render_page(self, error="", text="", title="", tags=""):
		user = self.return_user_if_cookie()
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False
		if not (user_var or author_name or over18):
			self.redirect("/")
		else:
			self.render("newask.html", 
						user = user,
						user_id = user_var,
						error=error,
						over18 = over18,

						title=title, 
						text=text,
						tags=tags)

	def get(self):
		self.render_page()

	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			error_var = "Sorry, but you need to be logged in to ask a question."
			self.render("newlesson.html", error = error_var)
		else:
			# User is signed in.
			user_id = int(user_var)

			# Required fields
			title_var = self.request.get("title")
			full_question_var = self.request.get("text")
			markdown_var = convert_text_to_markdown(full_question_var)

			# Kids and NSFW entries (if available)
			# Here, defaults are okay-for-kids/sfw, because no entry if kids online:
			okay_for_kids_var = True
			nsfw_var = False
			audience_var = self.request.get("audience")
			if audience_var: 
				if audience_var == "kids":
					pass
				elif audience_var == "sfw":
					okay_for_kids_var = False
				elif audience_var == "nsfw":
					okay_for_kids_var = False
					nsfw_var = True
				else:
					logging.error("New Link -- nsfw parser not working properly")
			else:
				pass

			# Optional fields
			tag_var = self.request.get("tags")
			the_tags = None
			if tag_var:
				the_tags = tag_var.split(', ')
				# tag string section
				tag_list = the_tags
				logging.warning(tag_list)
				tag_list = remove_list_duplicates(tag_list)
				logging.warning(tag_list)
				tag_list = strip_list_whitespace(tag_list)
				logging.warning(tag_list)
				tag_list = remove_unsafe_chars_from_tags(tag_list)
				tag_list.sort()
				if not tag_list:
					tag_list = ["None"]
					logging.warning("public tag list set to None")
				the_tags = tag_list


			if not (title_var and full_question_var):
				# Unsuccessful
				error_var = "Please complete all required information"
				self.render("newask.html", 
							error=error_var, 
							title=title_var, 
							text=full_question_var,
							tags=tag_var)
				return

			else:
				# Success
				user = return_thing_by_id(user_id, "Users")
				new_object = Objects(title= title_var, 
									author_id= user_id, 			# Not sure how file uploads will work, so below are default links for an object
									author_name= author_name,
									obj_type= 'ask',
									epoch = float(time.time()),

									okay_for_kids = okay_for_kids_var,
									nsfw = nsfw_var,

									learn = True,
									description = full_question_var,
									markdown = markdown_var,
									rank = new_rank(),
									num_user_when_created = num_users_now(),
									voter_list = [user_id],
									voter_vote = ["%s|1" % str(user_id)],
									)
				if the_tags:
					for tag in the_tags:
						new_object.tags.append(tag)
						new_object.author_tags.append(tag)

				new_object.put()

				# db set delay:
				time.sleep(6)

				if the_tags:
					for tag in the_tags:
						if new_object.okay_for_kids == True:
							store_page_cache_kids(tag, update=True)
						if new_object.nsfw == True:
							store_page_cache_nsfw(tag, update=True)
						else:
							store_page_cache_sfw(tag, update=True)
					taskqueue.add(url ='/tagupdateworker', 
								  countdown = 6
								 )

				if nsfw_var == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update = True)
				#logging.warning('made it this far')
				if okay_for_kids_var == True:
					all_objects_query("kids", update = True)
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass
				#learn_front_cache(update = True)
				object_page_cache(new_object.key().id(),update=True)
				user_page_obj_com_cache(user_id, update=True)

				# Update all front pages using the load_front_pages_from_memcache_else_query function
				global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
				if nsfw_var == True:
					# currently no other page types supported beyond "/"
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
				else:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
				if okay_for_kids_var == True:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)


				if user:
					for follower_id in user.follower_list:
						logging.warning('should sleep here')
						new_note(int(follower_id),
							"Objects|%d|%s| <a href='/user/%s'>%s</a> summitted a question: <a href='/obj/%s'>%s</a>." % (
									int(new_object.key().id()),
										str(time.time()),
															str(user.key().id()),
																str(cgi.escape(user.username)),
																								str(new_object.key().id()),
																									str(cgi.escape(new_object.title))),
							)
				self.redirect('/obj/%d' % new_object.key().id())

class NewsPage(FrontHandler):
	def render_front(self):
		pass
		# user=self.return_user_if_cookie()
		# over18 = self.check_cookie_return_val("over18")
		# the_list = []
		# if over18 != "True":
		# 	over18 = False
		# else:
		# 	over18 = True
		# the_list = news_front_cache()
		# the_objects = the_list[0]

		# has_cookie = None
		# active_username = "No Valid Cookie"
		# active_user = self.check_cookie_return_val("username")
		# user_id = self.check_cookie_return_val("user_id")
		# if active_user and user_id:
		# 	active_username = active_user
		# 	has_cookie = "This guy right here has a valid cookie for realz."
		# else:
		# 	pass
		
		# the_dict = cached_vote_data_for_masonry(the_objects, user_id)


		# # Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		# self.render("news_front.html", 
		# 			the_objects=the_objects, 
					
		# 			user=user, 
		# 			user_id = user_id,
		# 			has_cookie=has_cookie,
		# 			over18 = over18,
		# 			the_dict = the_dict)

	def get(self):
		self.render_front_page("/news")

	def post(self):
		pass

class NewsPageNew(FrontHandler):
	def render_front(self):
		pass
	def get(self):
		self.render_front_page("/newnews")

	def post(self):
		pass

class NewsPageTop(FrontHandler):
	def render_front(self):
		pass
	def get(self):
		self.render_front_page("/topnews")

	def post(self):
		pass		

class NewArticlePage(Handler):
	def render_page(self):
		
		user_id = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if over18 == "True":
			over18 = True
		else:
			over18 = False
		if not (user_id or author_name or over18):
			self.redirect("/login")
			return
		user = return_thing_by_id(user_id, "Users")
		if not user:
			self.error(400)
			return
		else:
			audience = "kids"
			self.render("new_article.html", 
						user = user,
						user_id = user_id,
						over18 = over18,
						audience = audience,	
						)

	def get(self):
		self.render_page()

	def post(self):
		user_var = self.check_cookie_return_val("user_id")
		author_name = self.check_cookie_return_val("username")
		over18 = self.check_cookie_return_val("over18")
		if not (user_var or author_name or over18):
			error_var = "Sorry, but you need to be logged in to upload an object."
			self.render("newlink.html", error = error_var)
		else:
			# User is signed in.
			user_id = int(user_var)
			if over18 == "True":
				over18 = True
			else:
				over18 = False

			# Required fields
			title_var = self.request.get("title")
			link_var = self.request.get("link")

			# this will always be false for news
			food_related = self.request.get("food_related")
			if food_related:
				food_related = True
			else:
				food_related = False

			# Kids and NSFW entries (if available)
			# Here, defaults are okay-for-kids/sfw, because no entry if kids online:
			# News will always be okay for kids
			okay_for_kids_var = True
			nsfw_var = False
			audience_var = self.request.get("audience")
			audience_for_redirect = audience_var
			if audience_var: 
				if audience_var == "kids":
					pass
				elif audience_var == "sfw":
					okay_for_kids_var = False
				elif audience_var == "nsfw":
					okay_for_kids_var = False
					nsfw_var = True
				else:
					logging.error("New Link -- nsfw parser not working properly")

			# Optional fields
			description_var = self.request.get("description")
			markdown_var = convert_text_to_markdown(description_var)
			tag_var = self.request.get("tags")
			the_tags = None
			if tag_var:
				the_tags = tag_var.split(', ')
				# tag string section
				tag_list = the_tags
				logging.warning(tag_list)
				tag_list = remove_list_duplicates(tag_list)
				logging.warning(tag_list)
				tag_list = strip_list_whitespace(tag_list)
				logging.warning(tag_list)
				tag_list = remove_unsafe_chars_from_tags(tag_list)
				tag_list.sort()
				if not tag_list:
					tag_list = ["None"]
					logging.warning("public tag list set to None")
				the_tags = tag_list

			# Check whether the url links to an actual site:
			# 3 tries:
			# 1st try: plain link (e.g. "http://www.google.com" = success!)
			# 2nd try: no http (e.g. "www.google.com" -> "http://www.google.com" = success!)
			# 3rd try: no www either (e.g. "google.com" -> "http://www.google.com" = success!)
			formatted_link_var = check_url(link_var)
			deadLinkFound = True
			if formatted_link_var:
				deadLinkFound = False
			#logging.warning(deadLinkFound)
			
			if not (title_var and link_var):
				# Unsuccessful
				error_var = 'You must include a title and a link.'
				user = return_thing_by_id(user_id, "Users")
				self.render("new_article.html", 
							user = user,
							user_id = user_id,
							over18 = over18,
							title=title_var, 
							link=link_var, 
							description=description_var,
							tags=tag_var,
							audience = audience_for_redirect,
							error = error_var,
							food_related = food_related,
							)
				return
			
			elif deadLinkFound:
				# Unsuccessful
				error_var = 'We are having trouble verifying the url you submitted.'
				user = return_thing_by_id(user_id, "Users")
				self.render("new_article.html", 
							user = user,
							user_id = user_id,
							over18 = over18,
							title=title_var, 
							link=link_var, 
							description=description_var,
							tags=tag_var,
							audience = audience_for_redirect,
							error = error_var,
							food_related = food_related,
							)
				return

			else:
				# Success
				user = return_thing_by_id(user_id, "Users")

				new_object = Objects(title= title_var, 
									author_id= user_id, 			# Not sure how file uploads will work, so below are default links for an object
									author_name= author_name,
									epoch = float(time.time()),
									obj_type= 'news',

									obj_link= formatted_link_var,

									okay_for_kids = okay_for_kids_var,
									nsfw = nsfw_var,
									food_related = food_related,

									description=description_var,
									markdown = markdown_var,
									news = True,
									rank = new_rank(),
									num_user_when_created = num_users_now(),
									voter_list = [user_id],
									voter_vote = ["%s|1" % str(user_id)],
									)
				if the_tags:
					for tag in the_tags:
						logging.warning('adding tag %s' % tag)
						new_object.tags.append(tag)
						new_object.author_tags.append(tag)
				
				new_object.put()
				# db set delay:

				time.sleep(6)

				if the_tags:
					for tag in the_tags:
						if new_object.okay_for_kids == True:
							store_page_cache_kids(tag, update=True)
						if new_object.nsfw == True:
							store_page_cache_nsfw(tag, update=True)
						else:
							store_page_cache_sfw(tag, update=True)
					taskqueue.add(url ='/tagupdateworker', 
								  countdown = 6
								 )

				if nsfw_var == True:
					all_objects_query("nsfw", update = True)
				else:
					all_objects_query("sfw", update = True)
				#logging.warning('made it this far')
				if okay_for_kids_var == True:
					all_objects_query("kids", update = True)
					user_page_obj_com_cache_kids(user_id, update = True)
				else:
					pass

				object_page_cache(new_object.key().id(),update=True)
				user_page_obj_com_cache(user_id, update=True)

				# Update all front pages using the load_front_pages_from_memcache_else_query function
				global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
				if nsfw_var == True:
					# currently no other page types supported beyond "/"
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
				else:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
				if okay_for_kids_var == True:
					load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)

				if user:
					for follower_id in user.follower_list:
						logging.warning('should sleep here')
						new_note(int(follower_id),
							"Objects|%d|%s| <a href='/user/%s'>%s</a> submitted <a href='/obj/%s'>%s</a>" % (
									int(new_object.key().id()),
										str(time.time()),
															str(user.key().id()),
																str(cgi.escape(user.username)),
																								str(new_object.key().id()),
																									str(cgi.escape(new_object.title))),
							)

				#news_front_cache(update=True, delay=0) # delay above
				self.redirect('/obj/%d' % new_object.key().id())	

class RepRapTypesPage(Handler):
	def render_page(self):
		user = self.return_user_if_cookie()

		self.render("parts.html", 
					user = user,
					)
	def get(self):
		self.render_page()	

class TagSearchMain(Handler):
	def render_page(self, error="", tag_searched=""):
		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")
		tag_list = return_top_x_tags()
		#logging.warning(tag_list)
		tag_searched = self.request.get("tag_searched")
		error_type = self.request.get("error")
		if error_type == "does_not_exist":
			error = 'It appears the object tag "%s" you were looking for does not exist.' % tag_searched

		self.render('tag_search_main.html',
					user = user,
					user_id = user_id,
					error=error,
					tag_list = tag_list,
					tag_searched = tag_searched,
					)
	def get(self):
		self.render_page()
	def post(self):
		search_var = self.request.get('search')
		global URL_SAFE_CHARS
		dummy_var = ""
		for i in search_var:
			if i in URL_SAFE_CHARS:
				dummy_var += i
			else:
				if i == " ":
					dummy_var += "_"
				else:
					pass
		search_var = dummy_var

		if not search_var:
			self.redirect('/tag')
			return
		else:
			self.redirect('/tag/%s' % search_var)
			return
class TagMainError(Handler):
	pass
	# def render_page(self, error="It appears the object tag you were looking for does not exist."):
	# 	self.render('tag_search_main.html', error=error)
	# def get(self):
	# 	self.render_page()
	# def post(self):
	# 	search_var = self.request.get('search')
	# 	logging.warning(search_var)
	# 	if not search_var:
	# 		logging.warning('empty search')
	# 		self.redirect('/tag')
	# 		return
	# 	else:
	# 		logging.warning('win')
	# 		self.redirect('/tag/%s' % search_var)
	# 		return	
class TagPage(Handler):
	def render_front(self, search_term):
		if search_term == "None":
			self.redirect("/tag")
			return
		user = self.return_user_if_cookie()
		over18 = self.check_cookie_return_val("over18")
		the_list = None
		if over18 != "True":
			over18 = False
			the_list = store_page_cache_kids(search_term)
		else:
			over18 = True
			the_list = store_page_cache_sfw(search_term)
		if len(the_list) == 0:
			# i should be able to use a query string in the url to throw 
			# this back to the tag search page instead of an independent error page
			error = "does_not_exist"
			self.redirect('/tag?tag_searched=%s&error=%s' % (search_term, error))
			return

		the_objects = the_list
		times_tag_used = len(the_list)

		rated_objects = []
		unrated_objects = []
		for obj in the_objects:
			if obj.num_ratings > 1:
				rated_objects.append(obj)
			else:
				unrated_objects.append(obj)
		
		if len(unrated_objects) > 0:
			unrated_objects.sort(key = lambda x: x.votesum, reverse=True)

		has_rated_objects = None
		has_rated_and_unrated = None
		if len(rated_objects) > 0:
			has_rated_objects = "Well hey, hi, howdy; it look's like we got some rated object here..."
			if len(unrated_objects) > 0:
				has_rated_and_unrated = "Yeppers"
		else:
			the_list.sort(key = lambda x: x.votesum, reverse=True)


		has_cookie = None
		active_username = "No Valid Cookie"
		active_user = self.check_cookie_return_val("username")
		user_id = self.check_cookie_return_val("user_id")
		if active_user and user_id:
			active_username = active_user
			has_cookie = "This guy right here has a valid cookie for realz."
		else:
			pass
		
		# Tag's wiki entry first 140 chars:
		wiki_entry = return_current_wiki_page(search_term)
		wiki_entry_first_lines = None
		if wiki_entry:
			if wiki_entry.markdown:
				logging.warning(wiki_entry.markdown)
				stripped_wiki_entry = re.sub('<[^>]*>', '', wiki_entry.markdown)
				stripped_wiki_entry = re.sub('\\n', ' ', stripped_wiki_entry)
				stripped_wiki_entry = stripped_wiki_entry.strip()
				logging.warning(stripped_wiki_entry)

				if len(stripped_wiki_entry) > 140:						
					wiki_entry_first_lines = stripped_wiki_entry[:141]
					if wiki_entry_first_lines[-1] == "<":
						wiki_entry_first_lines = wiki_entry_first_lines[:-1]
				else:
					wiki_entry_first_lines = stripped_wiki_entry			

		#the_dict = vote_data_for_masonry(the_objects, user_id)
		# trying cached version
		the_dict = cached_vote_data_for_masonry(the_objects, user_id)
		rated_dict = cached_vote_data_for_masonry(rated_objects, user_id)
		unrated_dict = cached_vote_data_for_masonry(unrated_objects, user_id)

		# Note that front page updates when new users sign up now, that can be removed (from the signup handler) when all users is no longer a parameter here.
		self.render("tag_search_results.html", 
					user = user,
					username=active_username, 
					user_id = user_id,
					the_objects=the_objects, 
					has_cookie=has_cookie,
					over18 = over18,
					the_dict = the_dict,
					
					unrated_dict = unrated_dict,
					rated_dict = rated_dict,
					search_term = search_term,
					wiki_entry_first_lines = wiki_entry_first_lines,
					has_rated_objects = has_rated_objects,
					has_rated_and_unrated = has_rated_and_unrated,

					times_tag_used = times_tag_used
					)

	def get(self, search_term):
		self.render_front(search_term=search_term)

	def post(self, search_term):
		pass
class TagUpdateWorker(Handler):
	def post(self):
		logging.warning("tags just updated")

class EmailConfirmationHandler(Handler):
	def get(self, url_hash):
		message = None
		no_email = None
		user_id = self.check_cookie_return_val("user_id")
		if user_id and user_id.isdigit():
			user_id = int(user_id)
		else:
			no_email = "nope"
			message = None
			self.render('emailconfirmation.html',
						no_email = no_email,
						message = message
						)
			return
		user = return_thing_by_id(user_id, "Users")

		# this should have a secret token

		user_hash = hashlib.sha256(user.unconfirmed_email).hexdigest()
		if url_hash == user_hash:
			user.user_email = user.unconfirmed_email
			if "email" not in user.awards:
				# must use .insert(0th position, variable) here to put most recent awards first
				user.awards.insert(0, "email")
				logging.info(user.awards)
				logging.info('db put new note be created')
				user.put()
				memcache.set("Users_%d" % user_id, [user])
				new_note(user.key().id(),
						"NA| |%s|<span style='font-size:20px;'>You have received an award! <br>All your awesome email checking has won you this sweet badge: <img src='/img/email_award.png' height=15px />. <br>Check out all the first class goodness on your <a href='/user/%s'>user page</a></span>"
							% ( str(time.time()),
								str(user.key().id())
								)
						)
			else:
				user.put()
				memcache.set("Users_%d" % user_id, [user])
			message = "You have successfully confirmed your email!"
			self.render("emailconfirmation.html",
						message = message,
						no_email = no_email,
						)
		else:
			message = "Oops, something went wrong, we were unable to confirm your email."
			self.render("emailconfirmation.html",
						message = message,
						no_email = no_email,
						)

class PasswordResetHandler(Handler):
	def get(self):
		#user = self.return_user_if_cookie()
		#if user:
		#	self.redirect("/user/%d" % int(user.key().id()))
		self.render("password_lost.html",
					)
	def post(self):
		username = self.request.get('username')
		username = username.lower()
		email = self.request.get('email')
		# include an email check

		logging.warning(username)
		logging.warning(email)

		user_query = Users.all().filter("username_lower =", username)
		user_query = list(user_query)
		if user_query and (len(user_query) == 1):
			the_user = user_query[0]
			if the_user.user_email and (the_user.user_email == email):
				# Username and confiremed email are correct. Send email to reset password
				#logging.warning("Success!")

				time_var = str(int(time.time()))
				logging.warning(time_var)
				# 17 minutes ~ 999 sec
				# remove 3 smallest digits to secure a valid hash
				time_var = time_var[:-3]
				# i must increase the var by 1 to allow for 15mins - 30mins reset time
				time_var = int(time_var)
				time_var += 1
				time_var = str(time_var)
				logging.warning(time_var)

				global page_url
				global secret

				info_str = the_user.random_string+secret+time_var
				
				# why use email and username here... 
				# it would be much better to have a large string generated on user signup
				# that way the passed hash would be much more secure

				reset_hash = hashlib.sha256(info_str).hexdigest() #make_pw_reset_hash(info_str)
				# this should be bcrypt --^
				logging.warning(reset_hash)
				#reset_hash = reset_hash.replace(".","_")
				#logging.warning(reset_hash)
				#reset_hash_url_safe = urllib.quote(reset_hash) #second parameter sets no char from being skipped because "/" is in bcrypt
				#logging.warning(reset_hash_url_safe)

				#email_safe = email.replace("@", "$")
				#email_safe = urllib.quote(email_safe, " ")

				reset_url = page_url+"/password_reset_confirmation/" + reset_hash + "-" + str(the_user.key().id())
				logging.warning(reset_url)
				
				email_address = email
				sender_address = data.password_reset_sender_address()
				subject = "Reset your password"
				body = """
				We have recieved a request to reset your password.
				If you have forgotten your password,
				you may reset it by clicking on the link below.
				This link is valid for around 15 minutes:

				%s

				If you did not request to reset your password,
				please contact us immediately.
				""" % reset_url
				mail.send_mail(sender_address, email_address, subject, body)
		self.redirect('/password_reset_acknowledgement')

class PasswordResetAcknowledgement(Handler):
	def get(self):
		self.render("password_lost2.html")
class PasswordResetConfirmationHandler(Handler):
	def render_page(self, url, error=""):
		path_hash = url
		logging.warning(path_hash)
		path_hash = path_hash.split("-", 1)
		logging.warning(path_hash)
		user = return_thing_by_id(path_hash[1], "Users")
		logging.warning(user)
		if not user:
			time.sleep(15)
			self.redirect('/')
			return
		path_hash = path_hash[0]
		logging.warning(path_hash)

		time_var = str(int(time.time()))
		logging.warning(time_var)
		# 17 minutes ~ 999 sec
		# remove 3 smallest digits to secure a valid hash
		time_var = time_var[:-3]
		logging.warning(time_var)

		logging.warning(user.username)
		logging.warning(user.random_string)
		global secret
		user_hash = hashlib.sha256(user.random_string + secret + time_var).hexdigest()
		#path_hash = valid_pw_reset_string()

		# here i must make a new hash in case the hash is checked too early
		time_var_plus_one = int(time_var)
		time_var_plus_one += 1
		time_var_plus_one = str(time_var_plus_one)
		user_hash_plus_one = hashlib.sha256(user.random_string + secret + time_var_plus_one).hexdigest()
		###

		if user_hash == path_hash or user_hash_plus_one == path_hash:
			time.sleep(10)
			self.render('password_change.html')
		else:
			time.sleep(15)
			self.redirect('/')
	def get(self, url):
		self.render_page(url = url)
	def post(self, url):
		path_hash = url
		password = self.request.get("password")
		verify = self.request.get("verify")

		if not (password and verify):
			error = "Both forms must filled in."
			self.render('password_change.html',
							 error = error,
							 )
			return
		if password != verify:
			error = "The passwords did not match."
			self.render('password_change.html',
							 error = error,
							 )
			return
		if len(password) < 6:
			error = "Your passwords is too short."
			self.render('password_change.html',
							 error = error,
							 )
			return

		path_hash = path_hash.split("-", 1)
		user_id = path_hash[1]
		logging.warning(user_id)
		user = return_thing_by_id(user_id, "Users")
		logging.warning(user)
		if user is None or (user.deleted == True):
			error = "This user does not appear to exist anymore... or somthing may have gone wrong."
			self.render_page('password_change.html',
							 error = error,
							 )
			return

		# okay, now to recheck the hash

		path_hash = path_hash[0]
		time_var = str(int(time.time()))
		logging.warning(time_var)
		# 17 minutes ~ 999 sec
		# remove 3 smallest digits to secure a valid hash
		time_var = time_var[:-3]
		logging.warning(time_var)

		logging.warning(user.random_string)
		global secret
		user_hash = hashlib.sha256(user.random_string + secret + time_var).hexdigest()
		#path_hash = valid_pw_reset_string()

		# here i must make a new hash in case the hash is checked too early
		time_var_plus_one = int(time_var)
		time_var_plus_one += 1
		time_var_plus_one = str(time_var_plus_one)
		user_hash_plus_one = hashlib.sha256(user.random_string + secret + time_var_plus_one).hexdigest()
		###

		if user_hash == path_hash or user_hash_plus_one == path_hash:
			#Success!
			user.password = '%s' % (make_pw_hash(user.username, password)), 
			self.login(user)
			pass
		self.redirect('/')

class Robots(Handler):
	def get(self):
		pass

#########################################################
####################### Wiki #######################

class WikiEntry(db.Model):
	title 			= db.StringProperty()
	content 		= db.TextProperty()
	markdown 		= db.TextProperty()
	created 		= db.DateTimeProperty(auto_now_add = True)
	original_epoch 	= db.FloatProperty()	
	author_id 		= db.IntegerProperty()
	author_name 	= db.StringProperty()

	time_since 		= db.StringProperty() # this var should stay empty, and is generated only on page load, but never put to db.

	epoch 			= db.FloatProperty()
	reverter_id 	= db.IntegerProperty()
	reverter_name 	= db.StringProperty()

	is_newest 		= db.BooleanProperty()
	version 		= db.IntegerProperty()
#####
mkd = markdown2.Markdown()
#####
class WikiMain(Handler):
	def get(self):
		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")
		self.render('wiki_home.html',
					user = user,
					user_id = user_id
					)
class WikiPage(Handler):
	def get(self, url):
		page_title = url[1:] # this drops the first '/'
		if page_title == '':
			page_title = 'home'
		if page_title == 'home':
			self.redirect('/w_home')
			return
		if page_title == 'index':
			self.redirect('/w_index')
			return

		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")		
		has_cookie = self.return_has_cookie()
		logging.warning(user)
		logging.warning(has_cookie)

		pages = return_all_wiki_pages_from_cache()
		page = None
		for p in pages:
			# this sucks, come up with a better way of doing this
			if p.title == page_title:
				page = p
				break
		if page:
			page = return_current_wiki_page(page_title)
			# all_pages = return_one_wiki_page_history_from_cache(page_title)
			# if all_pages:
			# 	#logging.warning('getting page')
			# 	page = all_pages[0]
			title = page.title
			self.render('wiki_page.html', 
						user = user,
						user_id = user_id,
						has_cookie = has_cookie,
						page = page, 
						)
		else:
			if has_cookie is None:
				self.redirect('/w/')
				return
			self.redirect('/_edit/' + page_title)
class EditPage(Handler):
	def get(self, url):
		page_title = url[1:] # this drops the first '/'
		if page_title == '' or page_title == 'None':
			page_title = 'index'
		
		next_url = self.request.headers.get('referer', '/w/%s' % str(page_title))
		logging.warning(next_url)

		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")		
		has_cookie = self.return_has_cookie()
		logging.warning(user)
		logging.warning(has_cookie)
		if (user is None) or (has_cookie is None):
			if "/_edit/" in next_url:
				next_url = "/w/%s" % str(page_title)
			self.redirect(next_url)
			return
		pages = return_all_wiki_pages_from_cache()
		page = None
		for p in pages:
			# This needs to be changed
			if p.title == page_title:
				page = p
				break
		if page == None:
			page = WikiEntry(title = page_title, 
							content = 'Enter the new content in here',
							user = user,
							has_cookie = has_cookie,
							)
		self.render('wiki_edit.html', 
					page = page,
					user = user,
					user_id = user_id,
					has_cookie = has_cookie,
					)

	def post(self, url):
		title = url[1:] # this drops the first '/'
		if title == "":
			title = 'home'
		
		next_url = self.request.headers.get('referer', '/w/%s' % str(title))
		logging.warning(next_url)

		user = self.return_user_if_cookie()
		has_cookie = self.return_has_cookie()
		logging.warning(user)
		logging.warning(has_cookie)
		if (user is None) or (has_cookie is None):
			self.redirect(next_url)
			return
		user_id = int(self.check_cookie_return_val('user_id'))
		username = str(self.check_cookie_return_val('username'))

		content = self.request.get('content')
		no_whitespace_content = strip_string_whitespace(content)

		current_page = return_current_wiki_page(title)
		if current_page:
			if no_whitespace_content == "" or no_whitespace_content == current_page.content:
				logging.warning("No change to WikiEntry")
				self.redirect('/w/%s' % str(title))
				return		 
		safe_content = cgi.escape(content)
		markdown = mkd.convert(safe_content)

		page = WikiEntry(title = title, 
						content = content,
						markdown = markdown,
						author_id = user_id,
						author_name = username,
						original_epoch = float(time.time()),
						epoch = float(time.time()),
						)
		logging.warning('db wikientry put')
		page.put()

		return_current_wiki_page(title, update = True, delay = 6)
		return_all_wiki_pages_from_cache(update = True)
		return_one_wiki_page_history_from_cache(title, update = True)
		return_wiki_history_from_cache(title, update = True, delay = 0)
		self.redirect('/w/' + title)
class HistoryPage(Handler):
	def get(self, url):
		page_title = url[1:] # this drops the first '/'
		if page_title == '':
			page_title = 'index'
		
		next_url = self.request.headers.get('referer', '/w/%s' % str(page_title))
		logging.warning(next_url)

		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")		
		has_cookie = self.return_has_cookie()
		logging.warning(user)
		logging.warning(has_cookie)

		pages = return_one_wiki_page_history_from_cache(page_title)
		for page in pages:
			page.time_since = time_since_creation(page.epoch)
		if len(pages) == 0:
			self.redirect('/_edit/' + page_title)
			return
		self.render('wiki_history.html', 
					pages = pages, 
					title = page_title,
					user = user,
					user_id = user_id,
					has_cookie = has_cookie,
					)
	def post(self, url):
		page_title = url[1:] # this drops the first '/'
		
		user = self.return_user_if_cookie()
		has_cookie = self.return_has_cookie()
		logging.warning(user)
		logging.warning(has_cookie)

		if has_cookie is None:
			self.error(404)
			return

		old_id = self.request.get('old_id')
		user_id = int(self.check_cookie_return_val('user_id'))
		username = str(self.check_cookie_return_val('username'))

		old_page = return_thing_by_id(old_id, "WikiEntry")
		if (old_page is None):
			self.error(404)
			return
		else:
			old_page.epoch = float(time.time())
			old_page.reverter_id = user_id
			old_page.reverter_name = username

			old_page.put()
			
			return_current_wiki_page(page_title, update = True, delay = 6)
			return_all_wiki_pages_from_cache(update = True)
			return_one_wiki_page_history_from_cache(page_title, update = True)
			return_wiki_history_from_cache(page_title, update = True, delay = 0)
			self.redirect('/w/' + page_title)

class WikiIndex(Handler):
	def get(self):
		user = self.return_user_if_cookie()
		user_id = self.check_cookie_return_val("user_id")		
		has_cookie = self.return_has_cookie()
		unfiltered_pages = return_all_wiki_pages_from_cache()
		unfiltered_pages.sort(key = lambda x: x.created, reverse=True)
		pages = []
		for uf_p in unfiltered_pages:
			old = False
			for filtered in pages:
				if uf_p.title == filtered.title:
					old = True
					break
			if old == False:
				pages.append(uf_p)
			else:
				pass
		self.render('wiki_all.html', 
					pages = pages,
					user = user,
					user_id = user_id,
					has_cookie = has_cookie,
					)

def return_current_wiki_page(title, update=False, delay = 0):
	key = "wiki_entry_%s" % str(title)
	logging.warning(key)
	page = memcache.get(key)
	logging.warning(page)
	if page is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		page = db.GqlQuery('SELECT * FROM WikiEntry WHERE title = :1 ORDER BY epoch DESC', title)
		if page:
			page = list(page)
			if len(page) > 0:
				page = page[0]
			page = [page]
		try:
			memcache.set(key, page)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return page[0]
def return_all_wiki_pages_from_cache(update = False, delay = 0):
	key = 'all_wiki_pages'
	pages = memcache.get(key)
	if pages is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning('db query wikientry get all')
		pages = WikiEntry.all()
		pages = list(pages)
		pages.sort(key = lambda x: x.epoch, reverse=True)
		try:
			memcache.set(key, pages)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return pages
def return_one_wiki_page_history_from_cache(title, update = False, delay = 0):
	key = 'wiki/' + str(title)
	pages = memcache.get(key)
	if pages is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		pages = db.GqlQuery('SELECT * FROM WikiEntry WHERE title = :1 ORDER BY epoch DESC', title)
		if pages is not None:
			pages = list(pages)
		try:
			memcache.set(key, pages)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return pages
def return_wiki_history_from_cache(title, update = False, delay = 0):
	key = 'history/' + str(title)
	history = memcache.get(key)
	if history is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning('db query wiki history')
		history = db.GqlQuery('SELECT * FROM WikiEntry WHERE title = :1 ORDER BY epoch DESC', title)
		if history is not None:
			history = list(history)
		try:
			memcache.set(key, history)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return history


#########################################################

####################### vote/rate/flag in cache #######################
#DAY_SCALE =  0.25 # approximately 6 hours
def one_long_vote_function(obj_id, user_id, newvote):
	"""
	Record 'user' casting a 'vote' for a quote with an id of 'quote_id'.
	The 'newvote' is usually an integer in [-1, 0, 1].
	"""
	user_id = int(user_id)
	obj_id = int(obj_id)
	if user_id is None:
		return
	obj = return_obj_by_id(obj_id)
	if obj is None:
		return
	if newvote not in [-1,0,1]:
		return
	oldvote = 0 #default
	# find and oldvote if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)
	
	if user_id in obj.voter_list:
		counter = 0
		for a_vote in obj.voter_vote:
			logging.warning(a_vote)
			vote_tuple = a_vote.split("|")
			logging.warning(vote_tuple)
			the_voter = int(vote_tuple[0])
			logging.warning(the_voter)
			if the_voter != user_id:
				logging.warning('Iteration #%d' % counter)
				counter += 1
				pass
			else:
				oldvote = int(vote_tuple[1])
				logging.warning(oldvote)
				if oldvote == newvote:
					return
				else:
					if int(oldvote) == 1:
						obj.upvotes -= 1
						if newvote == -1:
							obj.downvotes += 1
					elif int(oldvote) == -1:
						obj.downvotes -= 1
						if newvote == 1:
							obj.upvotes += 1
					elif int(oldvote) == 0:
						if int(newvote) == 1:
							obj.upvotes += 1
						elif int(newvote) == -1:
							obj.downvotes += 1
				break

		if oldvote == None:
			logging.error('Error -- object %d voter_list and voter_vote lists do not match' % int(obj_id))
		else:
			pass
		change = obj.voter_vote
		change[counter] = "%d|%d" % (int(user_id), int(newvote))
		obj.voter_vote = change
	else:
		logging.warning('user %d just voted on %d for the first time' % (int(user_id), int(obj_id)))
		if int(newvote) == 1:
			obj.upvotes += 1
		elif int(newvote) == -1:
			obj.downvotes += 1
		else:
			logging.error('problem with newvote value')
		obj.voter_list.append(int(user_id))
		obj.voter_vote.append("%d|%d" % (int(user_id), int(newvote)))

	obj.votesum = obj.votesum - oldvote + newvote

	obj.rank = return_rank(obj)


	# set the object memcache (object must be a singleton for some reason)
	logging.warning("db.put in voting function")
	memcache.set("Objects_%d" % int(obj_id), [obj])
	# putting but uncomment changed list if upgrading to temporal puts
	db.put(obj)
	reset_front_page_memcache_after_vote(obj)
	
	#update_objects_changed_list_cache(obj_id)
	#put_objects_in_changed_list_to_db()

	#update_front_style_memcache_after_vote(obj, "front_page_cache_sfw")
	#update_front_style_memcache_after_vote(obj, "front_page_cache_kids")
	#update_front_style_memcache_after_vote(obj, "front_page_cache_nsfw")
	#update_object_page_memcache_after_vote(obj, obj_id)

	for tag in obj.tags:
		if obj.nsfw == False:
			update_store_style_memcache_after_vote(obj, tag, "store_page_cache_sfw")
		else:
			update_store_style_memcache_after_vote(obj, tag, "store_page_cache_nsfw")
		if obj.okay_for_kids == True:
			update_store_style_memcache_after_vote(obj, tag, "store_page_cache_kids")


	# update user reputation
	user = return_thing_by_id(obj.author_id, "Users")
	logging.warning('user obj_rep')
	logging.warning(user.obj_rep)
	user.obj_rep = user.obj_rep - oldvote + newvote
	logging.warning(user.obj_rep)
	memcache.set("%s_%d" % ("Users", obj.author_id), [user])
	user.put()

def reset_front_page_memcache_after_vote(voted_object):
	obj = voted_object

	# set content type
	if obj.nsfw == True:
		content_type = 'nsfw'
	else:
		content_type = 'sfw'

	for i in range(999):
		if i == 0: # this memcache starts at "1" to keep page num == memcache key
			continue
		key = "front_page_%s_%d" % (content_type, i)
		obj_tuple = memcache.get(key)
		if obj_tuple:
			time_set_var = obj_tuple[0]
			obj_list = obj_tuple[1]

			set_memcache_now = False
			dummy_list = []
			time_set_var = obj_list[0]
			for this_obj in obj_list:
				#print "\n", this_obj
				if this_obj.key().id() == obj.key().id():
					dummy_list.append(obj)
					set_memcache_now = True
				else:
					dummy_list.append(this_obj)
			if set_memcache_now == True:
				new_obj_list = dummy_list
				for this_obj in new_obj_list:
					this_obj.rank = return_rank(this_obj)
				new_obj_list.sort(key = lambda x: (int(x.rank), x.epoch), reverse=True)
				memcache.set(key, [time_set_var, new_obj_list])
				break
		else:
			logging.warning("\n","\n","empty front page content","\n")

	#print "\n","\n","first section finished","\n", "\n"

	if obj.okay_for_kids == True:
		content_type = 'kids'
		for i in range(999):
			if i == 0: # this memcache starts at "1" to keep page num == memcache key
				continue
			key = "front_page_%s_%d" % (content_type, i)
			obj_tuple = memcache.get(key)
			if obj_tuple:
				time_set_var = obj_tuple[0]
				obj_list = obj_tuple[1]

				set_memcache_now = False
				dummy_list = []
				time_set_var = obj_list[0]
				for this_obj in obj_list:
					#print "\n", this_obj
					if this_obj.key().id() == obj.key().id():
						dummy_list.append(obj)
						set_memcache_now = True
					else:
						dummy_list.append(this_obj)
				if set_memcache_now == True:
					new_obj_list = dummy_list
					for this_obj in new_obj_list:
						this_obj.rank = return_rank(this_obj)
					new_obj_list.sort(key = lambda x: (int(x.rank), x.epoch), reverse=True)

					memcache.set(key, [time_set_var, new_obj_list])
					break
			else:
				logging.warning("\n","\n","empty front page content","\n")

	#print "\n","\n","second section finished","\n", "\n"


def return_rank(obj_or_com):
	global DAY_SCALE
	# day scale =  2 days
	global DAYS_TIL_DECLINE
	# days til decline = 4
	days_til_decline = DAYS_TIL_DECLINE

	one_day = 86400 #seconds

	time_now = float(time.time())
	birth = obj_or_com.epoch
	seconds_alive = time_now - birth
	days_alive = float(seconds_alive) / float(one_day)
	#logging.warning("days_alive")
	#logging.warning(days_alive)
	if days_alive < 0.01: # approx 15 minutes
		days_alive = 0.01

	inverse_votesum = float(1.00/max(float(obj_or_com.votesum), 1))

	decay = 0
	if days_alive > days_til_decline:
		# decay equation is 2/3 of days alive + votesum factor for every day it has been alive
		decay = float(float(2/3)*(days_alive-days_til_decline)) + (inverse_votesum*(days_alive-days_til_decline))

	rank = "%020d" % (
		# changing this to use epoch not 'com.created_int'
		round(
			float(obj_or_com.votesum)
			+ float(DAY_SCALE / days_alive) 
			- decay
		)
	)
	return rank
def new_rank():
	global DAY_SCALE
	rank = "%020d" % (
		# changing this to use epoch not 'com.created_int'
		float(
			1 # = obj_or_com.votesum 
			+ float(DAY_SCALE / .01) # initial days_alive is counted as 0.01
		)
	)
	return rank
def one_long_comment_vote_function(com_id, user_id, newvote):
	"""
	Record 'user' casting a 'vote' for a quote with an id of 'quote_id'.
	The 'newvote' is usually an integer in [-1, 0, 1].
	"""
	user_id = int(user_id)
	com_id = int(com_id)

	if user_id is None:
		return
	logging.warning('now to get the comment by id')
	com = return_thing_by_id(com_id, "Comments")
	if com is None:
		return
	if newvote not in [-1,0,1]:
		return
	logging.warning(com)
	logging.warning('got this far')
	oldvote = 0 #default
	# find and oldvote if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)
	
	if user_id in com.voter_list:
		counter = 0
		for a_vote in com.voter_vote:
			logging.warning(a_vote)
			vote_tuple = a_vote.split("|")
			logging.warning(vote_tuple)
			the_voter = int(vote_tuple[0])
			logging.warning(the_voter)
			if the_voter != user_id:
				logging.warning('Iteration #%d' % counter)
				counter += 1
				pass
			else:
				oldvote = int(vote_tuple[1])
				logging.warning(oldvote)
				if oldvote == newvote:
					return
				else:
					if int(oldvote) == 1:
						com.upvotes -= 1
						if newvote == -1:
							com.downvotes += 1
					elif int(oldvote) == -1:
						com.downvotes -= 1
						if newvote == 1:
							com.upvotes += 1
					elif int(oldvote) == 0:
						if int(newvote) == 1:
							com.upvotes += 1
						elif int(newvote) == -1:
							com.downvotes += 1
				break

		if oldvote == None:
			logging.error('Error -- object %d voter_list and voter_vote lists do not match' % int(com_id))
		else:
			pass
		change = com.voter_vote
		change[counter] = "%d|%d" % (int(user_id), int(newvote))
		com.voter_vote = change
	else:
		logging.warning('user %d just voted on %d for the first time' % (int(user_id), int(com_id)))
		if int(newvote) == 1:
			com.upvotes += 1
		elif int(newvote) == -1:
			com.downvotes += 1
		else:
			logging.warning('problem with newvote value')
		com.voter_list.append(int(user_id))
		com.voter_vote.append("%d|%d" % (int(user_id), int(newvote)))


	com.votesum = com.votesum - oldvote + newvote

	com.rank = return_rank(com)


	


	# set the object memcache (object must be a singleton for some reason)
	memcache.set("Comments_%d" % com_id, [com])
	# putting but uncomment changed list if upgrading to temporal puts
	db.put(com)
	logging.warning("db.put in comment voting function")

	#update_comments_changed_list_cache(com.key().id())

	delay_if_no_subcomment = 6
	if com.com_parent is not None:
		delay_if_no_subcomment = 0
		the_parent = return_com_by_id(com.com_parent)
		the_parent.ranked_children = sort_comment_child_rank_after_vote(com.com_parent, update=True, delay = 6)
		memcache.set("Comments_%d" % com.com_parent, [the_parent])
		#update_comments_changed_list_cache(the_parent.key().id())		
		# putting but uncomment changed list if upgrading to temporal puts
		the_parent.put()

	#put_comments_in_changed_list_to_db()

	obj_comment_cache(com.obj_ref_id, update=True, delay = delay_if_no_subcomment)

	# update user reputation
	user = return_thing_by_id(com.author_id, "Users")
	user.com_rep = user.com_rep - oldvote + newvote
	memcache.set("%s_%d" % ("Users", com.author_id), [user])
	user.put()
def one_long_rate_function(obj_id, user_id, newrate):
	"""
	Record 'user' casting a 'rate'.
	The 'newrate' is usually an integer in [1,2,3,4,5].
	"""
	user_id = int(user_id)
	obj_id = int(obj_id)
	if user_id is None:
		return
	obj = return_thing_by_id(obj_id, "Objects")
	logging.warning(obj)
	if obj is None:
		return
	if newrate not in [1,2,3,4,5]:
		return
	oldrate = 0 #default
	# find and oldrate if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)	
	logging.warning(obj.rater_list)
	logging.warning(user_id)
	if user_id in obj.rater_list:
		counter = 0
		for a_rate in obj.rater_rate:
			logging.warning(a_rate)
			rate_tuple = a_rate.split("|")
			logging.warning(rate_tuple)
			the_rater = int(rate_tuple[0])
			logging.warning(the_rater)
			if the_rater != user_id:
				logging.warning('Iteration #%d' % counter)
				counter += 1
				pass
			else:
				oldrate = int(rate_tuple[1])
				logging.warning(oldrate)
				if oldrate == newrate:
					return
				break

		if oldrate == None:
			logging.error('Error -- object %d rater_list and rater_rate lists do not match' % int(obj_id))
		else:
			pass
		change = obj.rater_rate
		change[counter] = "%d|%d" % (int(user_id), int(newrate))
		obj.rater_rate = change
	else:
		logging.warning('user %d just rated on %d for the first time' % (int(user_id), int(obj_id)))		
		obj.rater_list.append(int(user_id))
		logging.warning(obj.rater_list)
		if obj.rater_list is None:
			logging.error("user_id not appended")
		if obj.been_rated == False:
			obj.been_rated = True
		obj.num_ratings += 1
		obj.rater_rate.append("%d|%d" % (int(user_id), int(newrate)))

	obj.ratesum = obj.ratesum - oldrate + newrate
	obj.rate_avg = float(obj.ratesum / obj.num_ratings)

	# set the object memcache (object must be a singleton for some reason)
	memcache.set("Objects_%s" % str(obj_id), [obj])
	memcache.set("rate_val_tuple|" + str(user_id) + "|" + str(obj_id), (int(user_id), int(newrate)))

	update_objects_changed_list_cache(obj_id)
	
	# db.put is optional at this point
	db.put(obj)

	logging.warning('6 sec sleep')
	time.sleep(6)
	
	logging.warning("db.put in rating function")
	put_objects_in_changed_list_to_db()

	#update_front_style_memcache_after_rate(obj, "front_page_cache_sfw")
	#update_front_style_memcache_after_rate(obj, "front_page_cache_kids")
	#update_front_style_memcache_after_rate(obj, "front_page_cache_nsfw")
	#update_object_page_memcache_after_rate(obj, obj_id)
	
	for tag in obj.tags:
		if obj.nsfw == False:
			update_store_style_memcache_after_rate(obj, tag, "store_page_cache_sfw")
		else:
			update_store_style_memcache_after_rate(obj, tag, "store_page_cache_nsfw")
		if obj.okay_for_kids == True:
			update_store_style_memcache_after_rate(obj, tag, "store_page_cache_kids")
	
	# update user reputation
	user = return_thing_by_id(obj.author_id, "Users")
	logging.warning(oldrate)
	logging.warning(newrate)
	logging.warning(obj.num_ratings)
	if oldrate != 0:
		logging.warning(user.rate_rep)
		logging.warning(oldrate)
		logging.warning(newrate)
		logging.warning('newrate - 3 =')
		logging.warning(newrate - 3)
		user.rate_rep = user.rate_rep - (oldrate - 3) + (newrate - 3)
		logging.warning("------")
		logging.warning(user.rate_rep)

	else:
		logging.warning('new rate')
		logging.warning(obj.rater_list)
		# oldrate is nothing
		user.rate_rep = user.rate_rep + (newrate - 3)
	user.put()
	memcache.set("%s_%d" % ("Users", user.key().id()), [user])
	logging.warning('rate_rep set')
def one_long_flag_function(obj_id, user_id, newflag):
	"""
	Record 'user' casting a 'flag'.
	The 'newflag' is usually an integer in [0, 1].
	"""
	user_id = int(user_id)
	obj_id = int(obj_id)
	if user_id is None:
		return
	obj = return_thing_by_id(obj_id, "Objects")
	if obj is None:
		return
	if newflag not in [0,1]:
		return
	oldflag = 0 #default
	# find and oldflag if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)
	
	if user_id in obj.flagger_list:
		counter = 0
		for a_flag in obj.flagger_flag:
			logging.warning(a_flag)
			flag_tuple = a_flag.split("|")
			logging.warning(flag_tuple)
			the_flagger = int(flag_tuple[0])
			logging.warning(the_flagger)
			if the_flagger != user_id:
				logging.warning('Iteration #%d' % counter)
				counter += 1
				pass
			else:
				oldflag = int(flag_tuple[1])
				logging.warning(oldflag)
				if oldflag == newflag:
					return
				break

		if oldflag == None:
			logging.error('Error -- object %d flagger_list and flagger_flag lists do not match' % int(obj_id))
		else:
			pass
		change = obj.flagger_flag
		change[counter] = "%d|%d" % (int(user_id), int(newflag))
		obj.flagger_flag = change
	else:
		logging.warning('user %d just flagged on %d for the first time' % (int(user_id), int(obj_id)))
		if obj.been_flagged == False:
			obj.been_flagged = True
		obj.flagger_list.append(int(user_id))
		obj.flagger_flag.append("%d|%d" % (int(user_id), int(newflag)))


	obj.flagsum = obj.flagsum - oldflag + newflag

	if obj.flagsum >= 5:
		obj.under_review = True

	# set the object memcache (object must be a singleton for some reason)
	memcache.set("Objects_%d" % int(obj_id), [obj])
	memcache.set("flag_tuple|" + str(user_id) + "|" + str(obj_id), (int(user_id), int(newflag)))
	
	update_objects_changed_list_cache(obj_id)

	# db.put is optional at this point
	db.put(obj)
	logging.warning('sleep 6')
	time.sleep(6)
	logging.warning("db.put in flagging function")
	put_objects_in_changed_list_to_db()

	update_object_page_memcache_after_flag(obj, obj_id)

	# update user reputation
	user = return_thing_by_id(obj.author_id, "Users")
	if user.been_flagged == False:
		user.been_flagged = True
	user.flagsum = user.flagsum - oldflag + newflag
	if user.flagsum == 0:
		user.been_flagged = False
	user.flagged_obj.append(obj.key().id())
	filter_list = set(user.flagged_obj)
	filter_list = list(filter_list)
	user.flagged_obj = filter_list
	user.put()
	memcache.set("%s_%d" % ("Users", obj.author_id), [user])
def one_long_comment_flag_function(com_id, user_id, newflag):
	"""
	Record 'user' casting a 'flag'.
	The 'newflag' is usually an integer in [0, 1].
	"""
	user_id = int(user_id)
	com_id = int(com_id)
	if user_id is None:
		return
	com = return_thing_by_id(com_id, "Comments")
	if com is None:
		return
	if newflag not in [0,1]:
		return
	oldflag = 0 #default
	# find and oldflag if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)
	
	if user_id in com.flagger_list:
		counter = 0
		for a_flag in com.flagger_flag:
			logging.warning(a_flag)
			flag_tuple = a_flag.split("|")
			logging.warning(flag_tuple)
			the_flagger = int(flag_tuple[0])
			logging.warning(the_flagger)
			if the_flagger != user_id:
				logging.warning('Iteration #%d' % counter)
				counter += 1
				pass
			else:
				oldflag = int(flag_tuple[1])
				logging.warning(oldflag)
				if oldflag == newflag:
					return
				break

		if oldflag == None:
			logging.error('Error -- comment %d flagger_list and flagger_flag lists do not match' % int(com_id))
		else:
			pass
		change = com.flagger_flag
		change[counter] = "%d|%d" % (int(user_id), int(newflag))
		com.flagger_flag = change
	else:
		logging.warning('user %d just flagged on %d for the first time' % (int(user_id), int(com_id)))
		if com.been_flagged == False:
			com.been_flagged = True
		com.flagger_list.append(int(user_id))
		com.flagger_flag.append("%d|%d" % (int(user_id), int(newflag)))


	com.flagsum = com.flagsum - oldflag + newflag

	# set the object memcache (object must be a singleton for some reason)
	memcache.set("Comments_%d" % int(com_id), [com])
	
	update_comments_changed_list_cache(com.key().id())

	# db.put is optional at this point
	db.put(com)
	logging.warning("db.put in comment flagging function")
	put_comments_in_changed_list_to_db()

	obj_comment_cache(com.obj_ref_id, update=True)

	# update user reputation
	user = return_thing_by_id(com.author_id, "Users")
	if user.been_flagged == False:
		user.been_flagged = True
	user.flagsum = user.flagsum - oldflag + newflag
	user.flagged_com.append(com.key().id())
	memcache.set("%s_%d" % ("Users", com.author_id), [user])
	user.put()

def cached_vote_data_for_masonry(obj_list, user_id): 
	#, page=0): #previously called 'quote_for_template(q,u,p=0)'
	"""Convert a Quote object into a suitable dictionary for 
	a template. Does some processing on parameters and adds
	an index for paging.

	Args
	quotes:  A list of Quote objects.

	Returns
	A list of dictionaries, one per Quote object.
	"""
	obj_dict = []
	#index = 1 + page * models.PAGE_SIZE
	for obj in obj_list:
		obj_link = obj.obj_link
		this_obj_id = obj.key().id()
		short_url = None
		if obj_link:
			parse = urlparse(obj_link)
			#logging.warning(parse)
			short_url = parse[1]
		number_of_comments = obj.total_num_of_comments
		if number_of_comments > 0:
			number_of_comments = "(%d)" % number_of_comments
		else:
			number_of_comments = ""

		obj_dict.append({
			'db_type': obj.db_type,
			'id': obj.key().id(),
			'obj_id': obj.key().id(), #this is redundent but is causing problems
			'obj_type':obj.obj_type,
			'title':obj.title,
			'author_id':obj.author_id,
			'author_name':obj.author_name,
			'created':obj.created,
			'epoch':obj.epoch,
			'obj_link':obj.obj_link,
			'main_img_link':obj.main_img_link,
			'short_url': short_url,
			'voted': return_cached_vote(this_obj_id, user_id),
			#Thong added upvotes to the dict.  Not sure if votesum was the net vote or the product of the algorithm. The cacheing function in MainPage uses votesum to sort.
			'upvotes': obj.upvotes,
			'votesum': obj.votesum,
			'num_ratings':obj.num_ratings,
			'rate_avg':obj.rate_avg,
			'learn_skill':obj.learn_skill,
			'learn_subject':obj.learn_subject,

			'flagged_by_user':return_user_flag_from_tuple(this_obj_id, user_id),
			'time_since': time_since_creation(obj.epoch),
			'num_comments': number_of_comments,


			#'quote': quote.quote,
			#'creator': quote.creator,
			#'created': obj.creation_order[:10],
			#'created_long': obj.creation_order[:19],
			#'index':  index        
		})
	#index += 1
	return obj_dict

### num_comments_of_obj has been replaced in it's main usage, but not certain if completely gone
def num_comments_of_obj(obj_id):
	#no longer used that i know of, but check
	num = len(obj_comment_cache(obj_id))
	if num > 0:
		return "(%d)" % num
	else:
		return ""
def sort_comment_child_rank_after_vote(parent_id, update=False, delay = 0):
	key = "sort_ranked_children_for_com_%d" % int(parent_id)
	ranked_list = memcache.get(key)
	if ranked_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		par = return_com_by_id(parent_id)
		ranked_list = par.ranked_children
	tuple_list = []
	for com_id in ranked_list:
		com = return_com_by_id(com_id)
		tuple_list.append("%s|%d" % (str(com.rank), int(com_id)))
	logging.warning(tuple_list)
	tuple_list.sort(key = lambda x: x.split('|')[0], reverse=True)
	logging.warning(tuple_list)
	sorted_list = []
	for com_tuple in tuple_list:
		sorted_list.append(int(com_tuple.split('|')[1]))
		logging.warning(sorted_list)
	ranked_list = sorted_list
	try:
		memcache.set(key, ranked_list)
	except Exception as exception:
		logging.error("memcache set error")
		print exception
	logging.warning(ranked_list)
	return ranked_list
def return_comment_vote_flag_triplet(comment, user_id=None):
	"""Returns the value of a users vote on the specified comment, a value in [-1, 0, 1]."""
	if not (comment):
		return
	#logging.warning('return_comment_vote_flag_triplet')
	#logging.warning(comment)
	comment_triplet = [None,None,None]
	if user_id:
		user_id = int(user_id)
	com = comment
	#logging.warning(com.voter_list)
	comment_triplet[0] = com
	#logging.warning(obj)
	oldvote = None # default

	# find an oldvote if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)
	if user_id in com.voter_list:
		#logging.warning('user has voted on this comment')
		for a_vote in com.voter_vote:
			#logging.warning(a_vote)
			vote_tuple = a_vote.split("|")
			#logging.warning(vote_tuple)
			the_voter = int(vote_tuple[0])
			#logging.warning(the_voter)
			if the_voter != user_id:
				pass
			else:
				#logging.warning('Success the voter id is %s and the vote value is %s' % (vote_tuple[0],vote_tuple[1]))
				oldvote = int(vote_tuple[1])
				break

		if oldvote == None:
			logging.error('Error -- object %d voter_list and voter_vote lists do not match' % int(obj_id))
		else:
			pass
	else:
		oldvote = 0
	comment_triplet[1] = oldvote

	# flagging section
	oldflag = None
	if user_id in com.flagger_list:
		for a_flag in com.flagger_flag:
			#logging.warning(a_vote)
			flag_tuple = a_flag.split("|")
			#logging.warning(vote_tuple)
			the_flagger = int(flag_tuple[0])
			#logging.warning(the_voter)
			if the_flagger != user_id:
				pass
			else:
				#logging.warning('Success the voter id is %s and the vote value is %s' % (vote_tuple[0],vote_tuple[1]))
				oldflag = int(flag_tuple[1])
				break

		if oldflag == None:
			logging.error('Error -- object %d flaggerr_list and flagger_flag lists do not match' % int(com.key().id()))
		else:
			pass
	else:
		oldflag = 0
	comment_triplet[2] = oldflag
	if comment_triplet[0] is None or comment_triplet[1] is None or comment_triplet[2] is None:
		logging.error('ERROR -- problem in return_cached_comment_vote')
	return comment_triplet
def return_cached_vote(obj_id, user_id):
	"""Returns the value of a users vote on the specified quote, a value in [-1, 0, 1]."""
	if not (user_id and obj_id):
		return
	obj_id = int(obj_id)
	user_id = int(user_id)
	obj = return_obj_by_id(obj_id)
	#logging.warning(obj)
	oldvote = None # default
	# find and oldvote if one exists by iteration (if i can find this faster that'd be good... maybe a lambda function)
	if user_id in obj.voter_list:
		for a_vote in obj.voter_vote:
			#logging.warning(a_vote)
			vote_tuple = a_vote.split("|")
			#logging.warning(vote_tuple)
			the_voter = int(vote_tuple[0])
			#logging.warning(the_voter)
			if the_voter != user_id:
				pass
			else:
				#logging.warning('Success the voter id is %s and the vote value is %s' % (vote_tuple[0],vote_tuple[1]))
				oldvote = int(vote_tuple[1])
				break

		if oldvote == None:
			logging.error('Error -- object %d voter_list and voter_vote lists do not match' % int(obj_id))
		else:
			pass
	#if oldvote:
	#	logging.warning('returning vote value: %d' % int(oldvote))
	return oldvote
#########################################################
####################### Caching functions #######################

#DB_TYPE_LIST = ["Users", "Objects", "Comments", "Messages", "UserBlob", "ObjectBlob", "WikiEntry"]

def return_thing_by_id(thing_id, db_model_name, update=False, delay = 0):
	global DB_TYPE_LIST
	if db_model_name not in DB_TYPE_LIST:
		logging.error("return_thing_by_id, failed because model doesn't exist")
		return
	if thing_id is None:
		logging.error("return_thing_by_id, failed because thing_id is None")
		return
	key = "%s_%d" % (str(db_model_name), int(thing_id))
	#logging.warning(db_model_name)
	thing = memcache.get(key)
	#logging.warning(thing)
	if thing is None or update:
		logging.warning('db query get_by_id -- return_thing_by_id')
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		if db_model_name == "Users":
			thing = Users.get_by_id(int(thing_id))
		elif db_model_name == "Objects":
			thing = Objects.get_by_id(int(thing_id))
		elif db_model_name == "Comments":
			thing = Comments.get_by_id(int(thing_id))
		elif db_model_name == "Messages":
			thing = Messages.get_by_id(int(thing_id))
		elif db_model_name == "UserBlob":
			thing = UserBlob.get_by_id(int(thing_id))
		elif db_model_name == "ObjectBlob":
			thing = ObjectBlob.get_by_id(int(thing_id))
		elif db_model_name == "WikiEntry":
			thing = WikiEntry.get_by_id(int(thing_id))
		else:
			logging.error('model not in return_thing_by_id')
		#logging.warning(thing)
		if thing is not None:
			thing = [thing]
		else:
			thing = [[]]
		logging.warning(thing)
		try:
			memcache.set(key, thing)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return thing[0]

def update_objects_changed_list_cache(obj_id):
	key = "objects_changed_list"
	cache_list = memcache.get(key)
	if cache_list is None:
		cache_list = [[]]
		logging.warning('the_list was None')
	the_list = cache_list[0]
	if str(obj_id) in the_list:
		logging.warning('obj already in list:')
		logging.warning(the_list)
		return
	else:
		logging.warning('adding obj %s to list:' % str(obj_id))
		logging.warning(the_list)
		the_list.append(obj_id)
		logging.warning(the_list)
		cache_list = [the_list]
		try:
			memcache.set(key, cache_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
def update_comments_changed_list_cache(com_id):
	key = "comments_changed_list"
	cache_list = memcache.get(key)
	if cache_list is None:
		cache_list = [[]]
		logging.warning('the_list was None')
	the_list = cache_list[0]
	if str(com_id) in the_list:
		logging.warning('com already in list:')
		logging.warning(the_list)
		return
	else:
		logging.warning('adding id to list:')
		logging.warning(com_id)
		logging.warning(the_list)
		the_list.append(com_id)
		logging.warning(the_list)
		cache_list = [the_list]
		try:
			memcache.set(key, cache_list)	
		except Exception as exception:
			logging.error("memcache set error")
			print exception
def put_objects_in_changed_list_to_db():
	key = "objects_changed_list"
	cache_list = memcache.get(key)
	the_list = None
	if cache_list:
		the_list = cache_list[0]
	if (the_list is None) or (the_list == []):
		return
	else:
		for obj_id in the_list:
			obj = return_obj_by_id(obj_id)
			logging.warning("putting obj %s to db" % str(obj_id))
			db.put(obj)
		the_list = []
		cache_list = [the_list]
		try:
			memcache.set(key, cache_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
def put_comments_in_changed_list_to_db():
	key = "comments_changed_list"
	cache_list = memcache.get(key)
	the_list = None
	if cache_list:
		the_list = cache_list[0]
	if (the_list is None) or (the_list == []):
		return
	else:
		for com_id in the_list:
			com = return_com_by_id(com_id)
			logging.warning("putting com to db")
			logging.warning(com_id)
			db.put(com)
		the_list = []
		cache_list = [the_list]
		try:
			memcache.set(key, cache_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception

def update_front_style_memcache_after_vote(changed_obj, cache_key):
	# this will reset front_page_cache(_*) style caches
	the_list = memcache.get(cache_key)
	if the_list is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % str(cache_key))
		return
	else:
		pass
	the_list = list(the_list)
	the_objects = the_list[0]
	if the_objects and (type(the_objects) == list):
		for mem_obj in the_objects:
			if mem_obj.key().id() != changed_obj.key().id():
				pass
			else:
				mem_obj.rank = changed_obj.rank
				break
		the_objects.sort(key = lambda x: x.rank, reverse=True)

		memcache.set(cache_key, the_list)
	else:
		return
def update_front_style_memcache_after_rate(changed_obj, cache_key):
	# this will reset front_page_cache(_*) style caches
	the_list = memcache.get(cache_key)
	if the_list is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % str(cache_key))
		return
	else:
		pass
	the_list = list(the_list)
	the_objects = the_list[0]
	if the_objects and (type(the_objects) == list):
		for mem_obj in the_objects:
			if mem_obj.key().id() != changed_obj.key().id():
				pass
			else:
				mem_obj.rate_avg = changed_obj.rate_avg
				mem_obj.num_ratings = changed_obj.num_ratings
				break
		the_objects.sort(key = lambda x: x.votesum, reverse=True)

		memcache.set(cache_key, the_list)
	else:
		return
def update_store_style_memcache_after_vote(changed_obj, tag, cache_key):
	# this will reset front_page_cache(_*) style caches
	key = cache_key + "|" + tag
	the_list = memcache.get(cache_key)
	if the_list is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % str(cache_key))
		cache_sub = cache_key[-4:-1]
		if cache_sub == '_swf':
			store_page_cache_sfw(tag, update=True)
		elif cache_sub == 'kids':
			store_page_cache_kids(tag, update=True)
		elif cache_sub == 'nsfw':
			store_page_cache_nsfw(tag, update=True)
		else:
			logging.error('error in update_store_style_memcache_after_vote')
		return
	else:
		pass
	the_list = list(the_list)
	the_objects = the_list[0]
	if the_objects and (type(the_objects) == list):
		for mem_obj in the_objects:
			if mem_obj.key().id() != changed_obj.key().id():
				pass
			else:
				mem_obj.votesum = changed_obj.votesum
				break
		the_objects.sort(key = lambda x: x.rate_avg, reverse=True)

		try:
			memcache.set(key, the_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	else:
		return
def update_store_style_memcache_after_rate(changed_obj, tag, cache_key):
	# this will reset front_page_cache(_*) style caches
	key = cache_key + "|" + tag
	the_list = memcache.get(cache_key)
	if the_list is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % str(cache_key))
		cache_sub = cache_key[-4:-1]
		if cache_sub == '_swf':
			store_page_cache_sfw(tag, update=True)
		elif cache_sub == 'kids':
			store_page_cache_kids(tag, update=True)
		elif cache_sub == 'nsfw':
			store_page_cache_nsfw(tag, update=True)
		else:
			logging.error('error in update_store_style_memcache_after_vote')
		return
	else:
		pass
	the_list = list(the_list)
	the_objects = the_list[0]
	if the_objects and (type(the_objects) == list):
		for mem_obj in the_objects:
			if mem_obj.key().id() != changed_obj.key().id():
				pass
			else:
				mem_obj.rate_avg = changed_obj.rate_avg
				mem_obj.num_ratings = changed_obj.num_ratings
				break
		the_objects.sort(key = lambda x: x.rate_avg, reverse=True)

		try:
			memcache.set(key, the_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	else:
		return
def update_object_page_memcache_after_vote(changed_obj, obj_id):
	key = "object" + str(obj_id)	
	obj_singleton = memcache.get(key)
	if obj_singleton is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % key)
		return
	else:
		pass
	the_object = obj_singleton[0]
	the_object.votesum = changed_obj.votesum

	try:
		memcache.set(key, obj_singleton)
	except Exception as exception:
		logging.error("memcache set error")
		print exception
def update_object_page_memcache_after_rate(changed_obj, obj_id):
	key = "object" + str(obj_id)	
	obj_singleton = memcache.get(key)
	if obj_singleton is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % key)
		return
	else:
		pass
	the_object = obj_singleton[0]
	the_object.rate_avg = changed_obj.rate_avg
	the_object.been_rated = changed_obj.been_rated
	the_object.num_ratings = changed_obj.num_ratings
	try:
		memcache.set(key, obj_singleton)
	except Exception as exception:
		logging.error("memcache set error")
		print exception
def update_object_page_memcache_after_flag(changed_obj, obj_id):
	key = "object" + str(obj_id)	
	obj_singleton = memcache.get(key)
	if obj_singleton is None:
		logging.warning("Two problems may have occured. Either memcache %s is either cold (this is probably the case) or does not exist, or the cache updated does conform with this function." % key)
		return
	else:
		pass
	the_object = obj_singleton[0]
	the_object.flagsum = changed_obj.flagsum
	the_object.been_flagged = changed_obj.been_flagged
	try:
		memcache.set(key, obj_singleton)
	except Exception as exception:
		logging.error("memcache set error")
		print exception

def return_user_rate_from_tuple(obj_id, user_id):
	key = "rate_val_tuple|" + str(user_id) + "|" + str(obj_id)
	user_rate = memcache.get(key)
	if not user_rate:
		oldrate = 0 #default
		logging.warning('db query reset user and user_rate tuple')
		obj = Objects.get_by_id(obj_id)
		if int(user_id) in obj.rater_list:
			counter = 0
			for a_rate in obj.rater_rate:
				logging.warning(a_rate)
				rate_tuple = a_rate.split("|")
				logging.warning(rate_tuple)
				the_rater = int(rate_tuple[0])
				logging.warning(the_rater)
				if the_rater != user_id:
					logging.warning('Iteration #%d' % counter)
					counter += 1
					pass
				else:
					oldrate = int(rate_tuple[1])
					logging.warning(oldrate)
					break

			if oldrate == 0:
				logging.error('Error -- object %d rater_list and rater_rate lists do not match' % int(obj_id))
			user_rate = (user_id, oldrate)
			try:
				memcache.set(key, user_rate)
			except Exception as exception:
				logging.error("memcache set error")
				print exception		
			return user_rate[1]

		else:
			# This user has not rated before
			# oldrate set to 0 by default above
			user_rate = (user_id, oldrate)
			try:
				memcache.set(key, user_rate)
			except Exception as exception:
				logging.error("memcache set error")
				print exception
			return user_rate[1]
		
	else:
		rate = user_rate[1]
		return rate
def return_user_flag_from_tuple(obj_id, user_id):
	key = "flag_tuple|" + str(user_id) + "|" + str(obj_id)
	user_flag = memcache.get(key)
	if not user_flag:
		oldflag = 0
		obj = Objects.get_by_id(obj_id)
		if user_id in obj.flagger_list:
			counter = 0
			for a_flag in obj.flagger_flag:
				logging.warning(a_flag)
				flag_tuple = a_flag.split("|")
				logging.warning(flag_tuple)
				the_flagger = int(flag_tuple[0])
				logging.warning(the_flagger)
				if the_flagger != user_id:
					logging.warning('Iteration #%d' % counter)
					counter += 1
					pass
				else:
					oldflag = int(flag_tuple[1])
					logging.warning(oldflag)
					break

			if oldflag == 0:
				logging.error('Error -- object %d flagger_list and flagger_flag lists do not match' % int(obj_id))
			user_flag = (user_id, oldflag)
			try:
				memcache.set(key, user_flag)
			except Exception as exception:
				logging.error("memcache set error")
				print exception
			return user_flag[1]
			
		else:
			# This user has not flagged before
			# oldflag set to 0 by default above
			user_flag = (user_id, oldflag)
			try:
				memcache.set(key, user_flag)
			except Exception as exception:
				logging.error("memcache set error")
				print exception
			return user_flag[1]
	else:
		flag = user_flag[1]
		return flag

### not really used anymore
def front_page_cache(content_type, cursor_count = 0, update = False, delay = 0):
	key = 'front_page_cache_%s' % content_type
	logging.warning(content_type)
	the_objects_singlton = memcache.get(key)
	if the_objects_singlton is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = None
		if content_type == "sfw":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE nsfw = FALSE AND deleted = FALSE AND printable = True ORDER BY rank DESC')
		elif content_type == "kids":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE okay_for_kids = TRUE AND deleted = FALSE AND printable = True ORDER BY rank DESC')
		elif content_type == "nsfw":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE nsfw = TRUE AND deleted = FALSE AND printable = True ORDER BY rank DESC')
		else:
			self.error(400)
			logging.error('front_page_cache no content_type specified')
			return
		logging.warning("DB Query front_page_cache %s" % content_type)
		the_objects_singlton = [the_objects]
		# set memcache
		try:
			memcache.set(key, the_objects_singlton)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_objects_singlton[0]
# These second two are superfluous, i'll just use a lambda function to sort
def front_page_cache_new(content_type, cursor_count = 0, update = False, delay = 0):
	key = 'front_page_cache_new_%s' % content_type
	logging.warning(content_type)
	the_objects_singlton_new = memcache.get(key)
	if the_objects_singlton_new is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = None
		if content_type == "sfw":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE nsfw = FALSE AND deleted = FALSE AND printable = True ORDER BY created DESC')
		elif content_type == "kids":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE okay_for_kids = TRUE AND deleted = FALSE AND printable = True ORDER BY created DESC')
		elif content_type == "nsfw":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE nsfw = TRUE AND deleted = FALSE AND printable = True ORDER BY created DESC')
		else:
			self.error(400)
			logging.error('front_page_cache_new no content_type specified')
			return
		logging.warning("DB Query front_page_cache_new_ %s" % content_type)
		the_objects_singlton_new = [the_objects]
		# set memcache
		try:
			memcache.set(key, the_objects_singlton_new)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_objects_singlton_new[0]
def front_page_cache_top(content_type, cursor_count = 0, update = False, delay = 0):
	key = 'front_page_cache_top_%s' % content_type
	logging.warning(content_type)
	the_objects_singlton_top = memcache.get(key)
	if the_objects_singlton_top is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = None
		if content_type == "sfw":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE nsfw = FALSE AND deleted = FALSE AND printable = True ORDER BY votesum DESC')
		elif content_type == "kids":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE okay_for_kids = TRUE AND deleted = FALSE AND printable = True ORDER BY votesum DESC')
		elif content_type == "nsfw":
			the_objects = db.GqlQuery('SELECT * FROM Objects WHERE nsfw = TRUE AND deleted = FALSE AND printable = True ORDER BY votesum DESC')
		else:
			self.error(400)
			logging.error('front_page_cache_top no content_type specified')
			return
		logging.warning("DB Query front_page_cache_top_ %s" % content_type)
		the_objects_singlton_top = [the_objects]
		# set memcache
		try:
			memcache.set(key, the_objects_singlton_top)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_objects_singlton_top[0]
###

# these should all be called tag_page_etc...
def store_page_cache(search_term, update = False, delay = 0):
	key = 'store_page_cache|%s' % search_term
	the_list = memcache.get(key)
	if the_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = db.GqlQuery('SELECT * FROM Objects WHERE tags = :1 AND deleted = FALSE ORDER BY rate_avg DESC', search_term)
		logging.warning("DB Query store_page_cache")
		# Turn gql objects to lists
		the_list = list(the_objects)
		# set memcache
		try:
			memcache.set(key, the_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_list
def store_page_cache_kids(search_term, update = False, delay = 0):
	key = 'store_page_cache_kids|%s' % search_term
	the_list = memcache.get(key)
	if the_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = db.GqlQuery('SELECT * FROM Objects WHERE tags = :1 AND okay_for_kids = TRUE AND deleted = FALSE ORDER BY rate_avg DESC', search_term)
		logging.warning("DB Query store_page_cache_kids")
		# Turn gql objects to lists
		the_list = list(the_objects)
		# set memcache
		try:
			memcache.set(key, the_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_list
def store_page_cache_sfw(search_term, update = False, delay = 0):
	key = 'store_page_cache_sfw|%s' % search_term
	the_list = memcache.get(key)
	if the_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = db.GqlQuery('SELECT * FROM Objects WHERE tags = :1 AND nsfw=FALSE AND deleted = FALSE ORDER BY rate_avg DESC', search_term)
		logging.warning("DB Query store_page_cache_sfw")
		# Turn gql objects to lists
		the_list = list(the_objects)
		# set memcache
		try:
			memcache.set(key, the_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_list
def store_page_cache_nsfw(search_term, update = False, delay = 0):
	key = 'store_page_cache_nsfw|%s' % search_term
	the_list = memcache.get(key)
	if the_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		the_objects = db.GqlQuery('SELECT * FROM Objects WHERE tags = :1 AND nsfw = TRUE AND deleted = FALSE ORDER BY rate_avg DESC', search_term)
		logging.warning("DB Query store_page_cache_nsfw")
		# Turn gql objects to lists
		the_list = list(the_objects)
		# set memcache
		try:
			memcache.set(key, the_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return the_list

def object_page_cache(obj_id, update=False, delay = 0):
	# changed key to be same a thing
	key = "Objects_%s" % str(obj_id)
	obj_in_cache = memcache.get(key)
	if obj_in_cache is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Page Query -- object_page_cache")
		obj_in_cache = Objects.get_by_id(obj_id)
		# remove duplicate tags
		if len(list(obj_in_cache.tags)) != len(set(obj_in_cache.tags)):
			obj_in_cache.tags = remove_tag_duplicates_return_list(obj_in_cache)
			obj_in_cache.put()
			logging.warning('db put object_page_cache remove duplicate tags')
		obj_in_cache = [obj_in_cache]
		try:
			memcache.set(key, obj_in_cache)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return obj_in_cache[0]

def return_obj_by_id(obj_id, update=False, delay = 0):
	obj_id = int(obj_id)
	if update == True:
		return object_page_cache(obj_id, update=True, delay = int(delay))
	else:
		return object_page_cache(obj_id)
def return_com_by_id(com_id, update=True, delay = 0):
	com_id = int(com_id)
	key = "Comments_%d" % com_id
	comment = memcache.get(key)
	if comment is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		comment = Comments.get_by_id(com_id)
		comment = [comment]
		try:
			memcache.set(key, comment)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return comment[0]

def obj_comment_cache(obj_id, update=False, delay = 0):
	key = "comment"+str(obj_id)
	comments_in_cache = memcache.get(key)
	if comments_in_cache is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Query -- obj_comment_cache")
		comments_in_cache = db.GqlQuery("SELECT * FROM Comments WHERE obj_ref_id = :1 AND deleted = FALSE ORDER BY rank DESC", obj_id)
		if comments_in_cache:
			comments_in_cache = list(comments_in_cache)
		else:
			comments_in_cache = []
		try:
			memcache.set(key, comments_in_cache)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return comments_in_cache

def objects_cache(update=False, delay=0):
	key = 'all_objects'
	object_list = memcache.get(key)
	if object_list is None or update:
		#all_objects = Objects.all()
		#all_objects = all_objects.filter("deleted =", "FALSE")
		all_objects = db.GqlQuery("SELECT * FROM Objects WHERE deleted = FALSE ORDER BY created DESC")
		object_list = list(all_objects)
		logging.warning(object_list)
		try:
			memcache.set(key, object_list)
		except Exception as exception:
			logging.error("There is an issue with memcache on the tag search page.")
			print exception
	return object_list
def all_objects_query(content_type, update=False, delay = 0):
	key = 'all_objects_query_%s' % content_type
	object_query = memcache.get(key)
	if (object_query is None) or update:
		if update:
			logging.warning('all_objects_query sleep %d' % delay)
			time.sleep(int(delay))
		object_query = Objects.all()
		logging.warning("db query: all_objects_query Objects.all()")
		object_query = object_query.filter('deleted =', False)
		if content_type == "all":
			pass
		elif content_type == "sfw":
			object_query = object_query.filter('nsfw =', False)
		elif content_type == "kids":
			object_query = object_query.filter('okay_for_kids =', True)
		elif content_type == "nsfw":
			object_query = object_query.filter('nsfw =', True)
		else:
			self.error(400)
			logging.error('all_objects_query no content_type specified')
			return
		try:
			memcache.set(key, object_query)
		except Exception as exception:
			logging.error("all_objects_query failed to set memcache... probably due to too large a size")
			print exception

	return object_query

def users_cache(update = False, delay = 0):
	key = 'all_users'
	user_list = memcache.get(key)
	if user_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Users Query")
		all_users = db.GqlQuery("SELECT * FROM Users WHERE deleted = FALSE ORDER BY created DESC")
		user_list = list(all_users)
		try:
			memcache.set(key, user_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return user_list
def comments_cache(update = False, delay = 0):
	key = 'all_comments'
	com_list = memcache.get(key)
	if com_list is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Users Query")
		all_com = db.GqlQuery("SELECT * FROM Comments WHERE deleted = FALSE ORDER BY created DESC")
		com_list = list(all_com)
		try:
			memcache.set(key, com_list)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return com_list
def user_page_cache(user_id, update=False, delay = 0):
	# changed key to be identical key to return_thing_by_id for a user
	key = "Users_%s" % str(user_id)
	user_in_db = memcache.get(key)
	if user_in_db is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Page Query -- user_page_cache")
		user_in_db = Users.get_by_id(user_id)
		user_in_db = [user_in_db]
		try:
			memcache.set(key, user_in_db)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return user_in_db[0]
def user_page_object_cache(author_id, update=False, delay = 0):
	key = 'user_object_by_id' + str(author_id)
	user_objects_in_db = memcache.get(key)
	if user_objects_in_db is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Query -- user_page_object_cache")
		the_objects = db.GqlQuery("SELECT * FROM Objects WHERE author_id = :1 AND deleted = FALSE ORDER BY created DESC", author_id)
		the_objects = list(the_objects)
		user_objects_in_db = the_objects
		try:
			memcache.set(key, user_objects_in_db)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return user_objects_in_db
def user_page_comment_cache(author_id, update=False, delay = 0):
	key = 'user_comments_by_id' + str(author_id)
	user_comments_in_db = memcache.get(key)
	if user_comments_in_db is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Query -- user_page_comment_cache")
		the_comments = db.GqlQuery("SELECT * FROM Comments WHERE author_id = :1 AND deleted = FALSE ORDER BY created DESC", author_id)
		the_comments = list(the_comments)
		user_comments_in_db = the_comments
		try:
			memcache.set(key, user_comments_in_db)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return user_comments_in_db
def user_page_obj_com_cache(author_id, update=False, delay = 0):
	key = 'user_obj_com_cache'+str(author_id)
	in_db = memcache.get(key)
	if in_db is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Query -- user_page_obj_com_cache")
		the_objects = db.GqlQuery("SELECT * FROM Objects WHERE author_id = :1 AND deleted = FALSE ORDER BY created DESC", author_id)
		the_comments = db.GqlQuery("SELECT * FROM Comments WHERE author_id = :1 AND deleted = FALSE ORDER BY created DESC", author_id)
		the_objects = list(the_objects)
		the_comments = list(the_comments)
		# the_comments.append('end')
		the_list = the_objects + the_comments
		the_list.sort(key = lambda x: x.epoch, reverse=True)
		# # The following is a complicated series adding all comments and object by epoch
		# for com in the_comments:
		# 	# creates com_age if com is a comment object
		# 	if com == 'end':
		# 		pass
		# 	else:
		# 		com_age = com.epoch
			
		# 	comment_added = False
		# 	no_more_objects = False

		# 	# if the_objects list is not empty, else no_more_objecs = True
		# 	if len(the_objects) > 0:
		# 		# there are objects to iterate over
		# 		for obj in the_objects:
		# 			obj_age = obj.epoch
		# 			if com == 'end':
		# 				# just add all objects left
		# 				the_list.append(obj)
		# 				the_objects.remove(obj)
		# 			elif com_age < obj_age:
		# 				# if comment is smaller, it is older
		# 				the_list.append(com)
		# 				comment_added = True
		# 				break
		# 			elif com_age >= obj_age:
		# 				# if comment is larger, object is older
		# 				the_list.append(obj)
		# 				the_objects.remove(obj)
		# 			else:
		# 				logging.error('ERROR: user_page_obj_com_cache')
		# 	else:
		# 		no_more_objects = True
			
		# 	if comment_added == True:
		# 		#the_comments.remove(com)
		# 		pass
		# 	else:
		# 		pass
			
		# 	if no_more_objects == False:
		# 		pass
		# 	else:
		# 		if com == 'end':
		# 			pass
		# 		else:
		# 			the_list.append(com)
		# 			#the_comments.remove(com)
		# the_list.append(len(the_list))
		in_db = the_list
		try:
			memcache.set(key, in_db)
		except Exception as exception:
			logging.error("There is an issue with memcache on the user pages who upload a lot.")
			print exception
	return in_db
def user_page_obj_com_cache_kids(author_id, update=False, delay = 0):
	key = 'user_obj_com_cache_kids'+str(author_id)
	in_db = memcache.get(key)
	if in_db is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("DB Query -- user_page_obj_com_cache_kids")
		the_objects = db.GqlQuery("SELECT * FROM Objects WHERE author_id = :1 AND okay_for_kids = TRUE AND deleted = FALSE ORDER BY created DESC", author_id)
		the_comments = db.GqlQuery("SELECT * FROM Comments WHERE author_id = :1 AND obj_ref_okay_for_kids = TRUE AND deleted = FALSE ORDER BY created DESC", author_id)
		the_objects = list(the_objects)
		the_comments = list(the_comments)
		the_list = the_objects + the_comments
		the_list.sort(key = lambda x: x.epoch, reverse=True)
		in_db = the_list
		try:
			memcache.set(key, in_db)
		except Exception as exception:
			logging.error("There is an issue with memcache on the user pages")
			print exception
	return in_db

def user_messages_cache(recipient_id, update=False, delay = 0):
	key = "messages_for_%d" % recipient_id
	messages = memcache.get(key)
	#logging.warning(messages)
	if messages is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning('db query -- user_messages_cache')
		received = db.GqlQuery('SELECT * FROM Messages WHERE recipient_id = :1 AND deleted = False ORDER BY epoch DESC', recipient_id)
		received = list(received)		
		sent = db.GqlQuery('SELECT * FROM Messages WHERE author_id = :1 AND deleted = False ORDER BY epoch DESC', recipient_id)
		received = list(received)
		sent = list(sent)
		messages = received + sent
		messages.sort(key = lambda x: x.epoch, reverse=True)
		try:
			memcache.set(key, messages)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return messages

def learn_front_cache(update = False, delay = 0): # no longer used
	pass
	# key = 'learn_front_cache'
	# the_list = memcache.get(key)
	# if the_list is None or update:
	# 	if update:
	# 		logging.warning('db query sleep')
	# 		time.sleep(int(delay))
	# 	the_objects = db.GqlQuery('SELECT * FROM Objects WHERE deleted = FALSE AND learn = True ORDER BY rank DESC')
	# 	logging.warning("DB Query learn_front_cache")
	# 	# Turn gql objects to lists
	# 	the_objects = list(the_objects)
	# 	# make one big list
	# 	the_list = [the_objects]
	# 	# set memcache
	# 	memcache.set(key, the_list)
	# return the_list

def news_front_cache(update = False, delay = 0): # no longer used
	pass
	# key = 'news_front_cache'
	# the_list = memcache.get(key)
	# if the_list is None or update:
	# 	if update:
	# 		logging.warning('db query sleep')
	# 		time.sleep(int(delay))
	# 	the_objects = db.GqlQuery('SELECT * FROM Objects WHERE deleted = FALSE AND news = TRUE ORDER BY rank DESC')
	# 	logging.warning("DB Query news_front_cache")
	# 	# Turn gql objects to lists
	# 	the_objects = list(the_objects)
	# 	# make one big list
	# 	the_list = [the_objects]
	# 	# set memcache
	# 	memcache.set(key, the_list)
	# return the_list

def return_object_blob_by_key_name(referenced_blob_key, update=False, delay = 0):
	key = "objectblobkey|%s" % str(referenced_blob_key)
	blob_ref = memcache.get(key)
	if blob_ref is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		logging.warning("db query -- return_object_blob_by_key_name")
		object_blob_key = "blob|%s" % str(referenced_blob_key)
		logging.warning(object_blob_key)
		new_blob_ref = ObjectBlob.get_by_key_name(object_blob_key)
		logging.warning(new_blob_ref)
		if new_blob_ref is None:
			logging.warning('query returned NoneType -- return_object_blob_by_key_name')
			blob_ref = None
			blob_ref = [blob_ref]
			try:
				memcache.set(key, blob_ref)
			except Exception as exception:
				logging.error("memcache set error")
				print exception
		else:
			blob_ref = new_blob_ref
			blob_ref = [blob_ref]
			try:
				memcache.set(key, blob_ref)
			except Exception as exception:
				logging.error("memcache set error")
				print exception
	return blob_ref[0]
def return_object_blob_by_obj_id_and_priority(obj_id, priority, update = False, delay = 0):
	key = "object_%d_blob_priority_%d" % (int(obj_id), int(priority))
	blob_ref = memcache.get(key)
	if blob_ref is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		blob_ref = db.GqlQuery('SELECT * FROM ObjectBlob WHERE deleted = False AND obj_id = :1 AND priority = :2', obj_id, priority)
		logging.warning('db query objectblob by obj_id')
		logging.warning(blob_ref)
		blob_ref = blob_ref.get()
		blob_ref = [blob_ref]
		logging.warning(blob_ref)

		if len(blob_ref) == 0:
			logging.error('Object blob doesnt exist -- return_object_blob_by_obj_id_and_priority')
			return
		try:
			memcache.set(key, blob_ref)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	else:
		#logging.warning('cached ObjectBlob')
		pass
	return blob_ref[0]

#########################################################
####################### Hashing Functions #######################

####################### Cookies
secret = data.secret()
def make_secure_val(val):
	return "%s|%s" %(val, hmac.new(secret,val).hexdigest())
def check_secure_val(secure_val):
	val = secure_val.split("|")[0]
	if secure_val == make_secure_val(val):
		return val
	else:
		return None
def check_secure_bool(secure_val):
	val = secure_val.split("|")[0]
	if secure_val == make_secure_val(val):
		return True
	else:
		return False
####################### Bcrypt
def make_pw_hash(name, pw, salt=None):
	name = name.lower()
	if not salt:
		salt = bcrypt.gensalt(4) # this should be 10-12
	pw_hashed = bcrypt.hashpw(name + pw, salt)
	return '%s|%s' % (pw_hashed, salt)
def valid_pw(name, pw, h):
	name = name.lower()
	return h == make_pw_hash(name, pw, h.split('|')[1])
def make_pw_reset_hash(the_string, salt=None):
	if not salt:
		salt = bcrypt.gensalt(2) # this should be 10-12
	pw_hashed = bcrypt.hashpw(the_string, salt)
	return '%s|%s' % (pw_hashed, salt)
def valid_pw_reset_string(the_string, h):
	return h == make_pw_hash(the_string, h.split('|')[1])
def get_verified_user(username, password):
	query = User.gql('WHERE username=:username', username=username)
	user = query.get()
	if user:
		if valid_pw(username, password, user.password):
			return user
####################### Misc Hash
def users_key(group = "default"):
	return db.Key.from_path('users', group)
def gen_verify_hash(user):
	user_hash = hashlib.sha256(user.random_string).hexdigest()
	return user_hash
#########################################################
####################### Time functions #######################
start_time = None
time_since_cache = None
def check_time():
	global start_time
	global time_since_cache
	if start_time is None:
		logging.warning("Time Started")
		start_time = time.time()
	time_since_cache = time.time() - start_time
def reset_time():
	global start_time
	if time_since_cache is None:
		check_time()
	else:
		start_time = time.time()
		logging.warning("Time Reset")
#########################################################
####################### Utility functions #######################
def confirmation_email(email_address):
	global page_url
	confirmation_url = page_url+"/emailconfirmation/"+hashlib.sha256(email_address).hexdigest()
	sender_address = data.email_confirmation_sender_address()
	subject = "Confirm your registration"
	body = """
	Thank you for creating an account on bld3r.com! Please confirm your email address by
	clicking on the link below:

	%s
	""" % confirmation_url
	mail.send_mail(sender_address, email_address, subject, body)
def masonry_format_for_userpage(obj_list, user_id): 
	#, page=0): #previously called 'quote_for_template(q,u,p=0)'
	"""Convert a Quote object into a suitable dictionary for 
	a template. Does some processing on parameters and adds
	an index for paging.

	Args
	quotes:  A list of Quote objects.

	Returns
	A list of dictionaries, one per Quote object.
	"""
	obj_dict = []
	#index = 1 + page * models.PAGE_SIZE
	for obj in obj_list:
		#logging.warning(obj.db_type)
		if str(obj.db_type) == "Objects":
			obj_link = obj.obj_link
			this_obj_id = obj.key().id()
			short_url = None
			if obj_link:
				parse = urlparse(obj_link)
				short_url = parse[1]
			else:
				pass
			obj_dict.append({
				'db_type': obj.db_type,
				'id': obj.key().id(),
				'obj_id': obj.key().id(), #this is redundent but is causing problems
				'obj_type':obj.obj_type,
				'title':obj.title,
				'author_id':obj.author_id,
				'author_name':obj.author_name,
				'created':obj.created,
				'epoch':obj.epoch,
				'obj_link':obj.obj_link,
				'main_img_link':obj.main_img_link,
				'short_url': short_url,
				#'uri': quote.uri,
				'voted': return_cached_vote(this_obj_id, user_id),
				#Thong added upvotes to the dict.  Not sure if votesum was the net vote or the product of the algorithm. The cacheing function in MainPage uses votesum to sort.
				'upvotes': obj.upvotes,
				'votesum': obj.votesum,
				'num_ratings':obj.num_ratings,
				'rate_avg':obj.rate_avg,
				'learn_skill':obj.learn_skill,
				'learn_subject':obj.learn_subject,

				'flagged_by_user':return_user_flag_from_tuple(this_obj_id, user_id),
				'time_since': time_since_creation(obj.epoch),
				'num_comments': num_comments_of_obj(obj.key().id()),      
			})
		else:
			obj_dict.append(obj)
	#logging.warning(obj_dict)
	return obj_dict
def remove_tag_duplicates_return_list(obj):
	the_list = obj.tags
	the_set = set(the_list)
	new_list = list(the_set)
	return new_list
def remove_list_duplicates(some_list):
	the_set = set(some_list)
	new_list = list(the_set)
	return new_list
def strip_list_whitespace(some_list):
	tag_list = some_list
	#logging.warning(tag_list)
	new_list = []
	for tag in tag_list:
		tag = " ".join(tag.split())
		new_list.append(tag)
	tag_list = new_list
	new_list = []
	for tag in tag_list:
		if tag:
			new_list.append(tag)
	return new_list
def sort_comment_child_ranks(com_ranked_children, delay=0):
	ranked_list = com_ranked_children
	tuple_list = []
	time.sleep(int(delay))
	for com_id in ranked_list:
		com = return_com_by_id(com_id)
		tuple_list.append("%s|%d" % (str(com.rank), int(com_id)))
	logging.warning(tuple_list)
	tuple_list.sort(key = lambda x: x.split('|')[0], reverse=True)
	logging.warning(tuple_list)
	sorted_list = []
	for com_tuple in tuple_list:
		sorted_list.append(int(com_tuple.split('|')[1]))
		logging.warning(sorted_list)
	ranked_list = sorted_list
	logging.warning(ranked_list)
	return ranked_list
def strip_string_whitespace(some_string):
	stripped_string = " ".join(some_string.split())
	return stripped_string
def return_top_x_tags(x_value=50, return_all_tags=False):
	big_list = [] # all list items will take the form [tag_term, times_found (int), first lines of wikipage (if exists)]
	#logging.warning("------------------------------")
	all_objects = objects_cache()
	for obj in all_objects:
		for tag in obj.tags:
			tag_found = False

			if len(big_list) > 0:
				for item in big_list:
					if tag == item[0]:
						tag_found = True
						item[1] += 1
						#logging.warning(item[0])
						#logging.warning(item[1])
						#logging.warning("------")
				if tag_found == False:
					big_list.append([tag, 1, None])
			else:
				big_list.append([tag, 1, None])

		#logging.warning(big_list)
	big_list.sort(key = lambda x: x[1], reverse=True)

	if (return_all_tags == True) or (len(big_list) <= int(x_value)):
		pass
	else:
		logging.warning('returning only x_value')
		big_list = big_list[:(int(x_value) + 1)]

	list_with_excerpts = []
	for i in big_list:
		wiki_entry = return_current_wiki_page(i[0])
		wiki_entry_first_lines = None
		if wiki_entry:
			if wiki_entry.markdown:
				logging.warning(wiki_entry.markdown)
				stripped_wiki_entry = re.sub('<[^>]*>', '', wiki_entry.markdown)
				stripped_wiki_entry = re.sub('\\n', ' ', stripped_wiki_entry)
				stripped_wiki_entry = stripped_wiki_entry.strip()
				logging.warning(stripped_wiki_entry)

				if len(stripped_wiki_entry) > 140:						
					wiki_entry_first_lines = stripped_wiki_entry[:141]
					if wiki_entry_first_lines[-1] == "<":
						wiki_entry_first_lines = wiki_entry_first_lines[:-1]
				else:
					wiki_entry_first_lines = stripped_wiki_entry
		list_with_excerpts.append([i[0], i[1], wiki_entry_first_lines])
	return list_with_excerpts
def time_since_creation(item_epoch_var):
	raw_secs = round(time.time())-round(item_epoch_var)
	#logging.warning(raw_secs)
	raw_secs = int(raw_secs)
	time_str = None
	if raw_secs < 60:
		seconds = raw_secs
		if seconds > 1:
			time_str = "%d seconds" % seconds
		else:
			time_str = "%d second" % seconds
	elif (raw_secs >= 60) and (raw_secs < (60 * 60)):
		minutes = (raw_secs/60)
		if minutes > 1:
			time_str = "%d minutes" % minutes
		else:
			time_str = "%d minute" % minutes
	elif (raw_secs >= (60*60) and (raw_secs < (60 * 60 * 24))):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		if hours > 1:
			time_str = "%d hours" % hours
		else:
			time_str = "%d hour" % hours
	elif (raw_secs >= (60*60*24) and (raw_secs < (60*60*24*30))):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		if days > 1:
			time_str = "%d days" % days
		else:
			time_str = "%d day" % days
	elif (raw_secs >=(60*60*24*30)) and (raw_secs < (60*60*24*365)):		
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		months = (days/30)
		if months > 1:
			time_str = "%d months" % months
		else:
			time_str = "%d month" % months
	elif raw_secs >= (60*60*24*365):
		minutes = (raw_secs/60)
		hours = (minutes/60)
		days = (hours/24)
		years = (days/365)
		if years > 1:
			time_str = "%d years" % years
		else:
			time_str = "%d year" % years
	else:
		logging.error("something wrong with time_since_creation function")
		time_str = None
	return time_str		
def check_url(url_str):
	link_var = url_str
	deadLinkFound = check_url_instance(link_var)
	if deadLinkFound:
		link_var = "http://" + link_var
		deadLinkFound = check_url_instance(link_var)
		if deadLinkFound:
			link_var = "http://www." + link_var
			deadLinkFound = check_url_instance(link_var)
			if deadLinkFound:
				link_var = None
	return link_var
def check_url_instance(url_str):
	link_var = url_str
	logging.warning(link_var)
	deadLinkFound = True
	try:
		f = urlfetch.fetch(url=link_var, deadline=30)
		if f.status_code == 200:
  			#logging.warning(f.content)
  			pass
		deadLinkFound = False
	except Exception as e:
		logging.warning('that failed')
		logging.warning(e)
	logging.warning(deadLinkFound)
	return deadLinkFound
def is_ascii_stl(blobinfo_instance):
	is_stl = False #default

	input_file = blobinfo_instance.open()

	################## from stlparser.py ############################
	f = input_file
	name = f.readline().split()
	if not name[0] == "solid":
		logging.warning("No 'solid' on first line")
		# raise IOError("Expecting first input as \"solid\" [name]")
		is_stl = False
		return is_stl

	if len(name) == 2:
		title = name[1]
	elif len(name) == 1:
		title = None
	else:
		is_stl = False
		return is_stl
		#raise IOError("Too many inputs to first line")
	
	triangles = []
	norms = []

	clean = True
	for line in f:
		params = line.split()
		if params:
			#logging.warning("checking 'params'")
			cmd = params[0]
			if cmd == "endsolid":
				if name and params[1] == name:
					#break
					continue
				else: #TODO: inform that name needs to be there
					#break
					continue
			elif cmd == "facet":
				try:
					norm = map(float, params[2:5])
					continue
					#norms.append(tuple(norm))
				except:
					logging.warning("Parse failed here:")
					logging.warning(params)
					clean = False
					is_stl = False
					return is_stl
			elif cmd == "outer":
				continue
				#triangle = []
			elif cmd == "vertex":
				try:
					vertex = map(float, params[1:4])
					continue
				except:
					logging.warning("Parse failed here:")
					logging.warning(params)
					clean = False
					is_stl = False
					return is_stl
				#triangle.append(tuple(vertex))
			elif cmd == "endloop":
				continue
			elif cmd == "endfacet":
				continue
				#triangles.append(tuple(triangle)) #TODO: Check IO formatting
				#triangle = []

			else:
				logging.warning("Parse failed here:")
				logging.warning(params)
				clean = False
				is_stl = False
				return is_stl

	if clean:
		is_stl = True
	return is_stl
	#return SolidSTL(title, triangles, norms)
	##############################################
	
	# #old version
	# input_file_list = input_file.readlines()
	# for line in input_file_list:
	# 	if line.strip():
	# 		if "solid" in line:
	# 			logging.warning(line)
	# 			first_line_list = line.split(' ')
	# 			if first_line_list[0] != "solid":
	# 				break
	# 			stl_name = first_line_list[1]
	# 			logging.warning(first_line_list[0])
	# 			logging.warning(stl_name)

	# 			for last_line in reversed(input_file_list):
	# 				if last_line.strip():
	# 					if "endsolid" in last_line:
	# 						logging.warning(last_line)
	# 						last_line_list = last_line.split(" ")
	# 						counter = -1
	# 						for last_word in reversed(last_line_list):
	# 							if last_word:
	# 								logging.warning(counter)
	# 								logging.warning(last_word)
	# 								if last_word != stl_name:
	# 									break
	# 								else:
	# 									if last_line_list[counter-1] == "endsolid":
	# 										is_stl = True
	# 									logging.warning(last_line_list[counter-1])
	# 									break
	# 							logging.warning(counter)
	# 							counter -= 1
	# 					else:
	# 						break
	# 		else:
	# 			break
	# logging.warning("-------------------------")
	# logging.warning("This file is an stl file:")
	# logging.warning("-------------------------")
	# logging.warning(is_stl)
	# logging.warning("-------------------------")
	# return is_stl
def remove_unsafe_chars_from_tags(tag_list):
	escaped_list = []
	for tag in tag_list:
		escaped_string = []
		for char in tag:
			if char in URL_SAFE_CHARS:
				escaped_string.append(char)
			else:
				if char == " ":
					escaped_string.append("_")
		tag = "".join(escaped_string)
		escaped_list.append(tag)
	new_tag_list = escaped_list
	return new_tag_list 
def return_printed_by_list(obj_id, update=False, delay=0):
	key = 'printed_by_list_%d' % int(obj_id)
	users_who_have_printed = memcache.get(key)
	if users_who_have_printed is None or update:
		if update:
			logging.warning('db query sleep')
			time.sleep(int(delay))
		users_who_have_printed = Users.all().filter('has_printed_list =', str(obj_id))
		logging.warning("db query users_who_have_printed")
		logging.warning(users_who_have_printed)
		users_who_have_printed = list(users_who_have_printed)
		logging.warning(users_who_have_printed)
		if len(users_who_have_printed) > 1:
			users_who_have_printed.sort(key = lambda x: x.obj_rep, reverse=True)
		# set memcache
		try:
			memcache.set(key, users_who_have_printed)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
	return users_who_have_printed
def new_note(recipient_id, note_text, delay=0):
	user = return_thing_by_id(int(recipient_id), "Users", delay=int(delay))
	if user.has_note == False:
		user.has_note = True
	#note_text = mkd.convert(note_text)
	if user is None:
		logging.error('ERROR: user to recieve note no longer exists')
		return
	#logging.warning(note_text)
	user.new_note_list.append(note_text)
	#logging.warning(user.new_note_list)
	user.note_list_all.append(note_text)
	#logging.warning(user.new_note_list)
	user.put()
	# This here is a big problem for follower lists
	# each time a popular contributer makes a post, 
	# every follower (active or not) will get a write.
	# my alternative idea now, is to have a new user following list
	# and then another "last checked" date. It would then load notes
	# for every post from a user followed on page visit.
	# this however, would also cause massive amounts of queries.
	# Potentially more than the writes would cost.
	# This is a very interesting problem.
	logging.warning('new note put()')
	time.sleep(int(delay))
	key = "%s_%d" % ("Users", int(recipient_id))
	user = [user]
	try:
		memcache.set(key ,user)
	except Exception as exception:
		logging.error("memcache set error")
		print exception
def is_blacklisted_referer(referer):
	global REFERER_BLACKLIST
	blacklist = REFERER_BLACKLIST
	is_blacklisted = False
	for i in blacklist:
		if referer.endswith(i):
			is_blacklisted = True
			break
	return is_blacklisted
def delete_obj(obj_id):
	obj_str = str(obj_id)
	if not obj_str.isdigit():
		self.error(400)
		return
	obj_id = int(obj_id)
	# Delete
	the_object = Objects.get_by_id(obj_id)
	user_id = the_object.author_id

	are_blobs = False

	# if stl
	stl_file_blob_key 	= the_object.stl_file_blob_key
	file_blob_key_2 	= the_object.file_blob_key_2
	file_blob_key_3 	= the_object.file_blob_key_3
	file_blob_key_4 	= the_object.file_blob_key_4
	file_blob_key_5 	= the_object.file_blob_key_5
	file_blob_key_6 	= the_object.file_blob_key_6
	file_blob_key_7 	= the_object.file_blob_key_7
	file_blob_key_8 	= the_object.file_blob_key_8
	file_blob_key_9 	= the_object.file_blob_key_9
	file_blob_key_10 	= the_object.file_blob_key_10
	file_blob_key_11 	= the_object.file_blob_key_11
	file_blob_key_12 	= the_object.file_blob_key_12
	file_blob_key_13 	= the_object.file_blob_key_13
	file_blob_key_14 	= the_object.file_blob_key_14
	file_blob_key_15 	= the_object.file_blob_key_15
	if stl_file_blob_key is not None:
		are_blobs = True
		stl_file_blob_key.delete()
	if file_blob_key_2 is not None:
		are_blobs = True
		file_blob_key_2.delete()
	if file_blob_key_3 is not None:
		are_blobs = True
		file_blob_key_3.delete()				
	if file_blob_key_4 is not None:
		are_blobs = True
		file_blob_key_4.delete()
	if file_blob_key_5 is not None:
		are_blobs = True
		file_blob_key_5.delete()
	if file_blob_key_6 is not None:
		are_blobs = True
		file_blob_key_6.delete()
	if file_blob_key_7 is not None:
		are_blobs = True
		file_blob_key_7.delete()
	if file_blob_key_8 is not None:
		are_blobs = True
		file_blob_key_8.delete()
	if file_blob_key_9 is not None:
		are_blobs = True
		file_blob_key_9.delete()
	if file_blob_key_10 is not None:
		are_blobs = True
		file_blob_key_10.delete()
	if file_blob_key_11 is not None:
		are_blobs = True
		file_blob_key_11.delete()
	if file_blob_key_12 is not None:
		are_blobs = True
		file_blob_key_12.delete()
	if file_blob_key_13 is not None:
		are_blobs = True
		file_blob_key_13.delete()
	if file_blob_key_14 is not None:
		are_blobs = True
		file_blob_key_14.delete()
	if file_blob_key_15 is not None:
		are_blobs = True
		file_blob_key_15.delete()
	# if main_img
	main_img_blob_key = the_object.main_img_blob_key
	if main_img_blob_key is not None:
		are_blobs = True
		main_img_blob_key.delete()

	if are_blobs is True:
		all_blob_refs = db.GqlQuery("SELECT * FROM ObjectBlob WHERE obj_id = :1", obj_id)
		db.delete(all_blob_refs)

	kids_bool = the_object.okay_for_kids
	nsfw_bool = the_object.nsfw

	the_object.title 			= " "
	the_object.author_id		= None
	the_object.author_name		= " "
	the_object.food_related		= False
	the_object.learn_skill		= None
	the_object.stl_file_link 	= None
	the_object.stl_file_blob_key= None
	the_object.stl_filename		= None
	the_object.main_img_link 	= None
	the_object.main_img_blob_key= None
	the_object.license			= None
	the_object.obj_link			= None
	the_object.description 		= ""
	the_object.markdown			= ""
	the_object.tags 			= ["None"]
	the_object.author_tags		= ["None"]
	the_object.public_tags 		= ["None"]
	the_object.other_file1_link = None
	the_object.other_img1_link 	= None
	the_object.file_link_2 		= None
	the_object.file_blob_key_2 	= None
	the_object.file_blob_filename_2		= None
	the_object.file_link_3 		= None
	the_object.file_blob_key_3 	= None
	the_object.file_blob_filename_3		= None
	the_object.file_link_4 		= None
	the_object.file_blob_key_4 	= None
	the_object.file_blob_filename_4		= None
	the_object.file_link_5 		= None
	the_object.file_blob_key_5 	= None
	the_object.file_blob_filename_5		= None
	the_object.file_link_6 		= None
	the_object.file_blob_key_6 	= None
	the_object.file_blob_filename_6		= None
	the_object.file_link_7 		= None
	the_object.file_blob_key_7 	= None
	the_object.file_blob_filename_7		= None
	the_object.file_link_8 		= None
	the_object.file_blob_key_8 	= None
	the_object.file_blob_filename_8		= None
	the_object.file_link_9 		= None
	the_object.file_blob_key_9 	= None
	the_object.file_blob_filename_9		= None
	the_object.file_link_10 	= None
	the_object.file_blob_key_10 = None
	the_object.file_blob_filename_10	= None
	the_object.file_link_11 	= None
	the_object.file_blob_key_11 = None
	the_object.file_blob_filename_11	= None
	the_object.file_link_12 	= None
	the_object.file_blob_key_12 = None
	the_object.file_blob_filename_12	= None
	the_object.file_link_13 	= None
	the_object.file_blob_key_13 = None
	the_object.file_blob_filename_13	= None
	the_object.file_link_14 	= None
	the_object.file_blob_key_14 = None
	the_object.file_blob_filename_14	= None
	the_object.file_link_15 	= None
	the_object.file_blob_key_15 = None
	the_object.file_blob_filename_15	= None

	the_object.deleted 			= True

	the_object.put()
	logging.warning('Object "Deleted"')
	
	object_page_cache(obj_id, update=True, delay = 6)

	if kids_bool == True:
		user_page_obj_com_cache_kids(user_id, update = True)
	else:
		pass

	if nsfw_bool == True:
		all_objects_query("nsfw", update = True)
	else:
		all_objects_query("sfw",update=True)

	# reset front page cache
	global NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT
	if nsfw_bool == True:
		# currently no other page types supported beyond "/"
		load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "nsfw", update=True)
	else:
		load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "sfw", update=True)
	if kids_bool == True:
		load_front_pages_from_memcache_else_query("/", NUMBER_OF_PAGES_TO_UPDATE_WHEN_NEW_OBJECT, "kids", update=True)


	obj_comment_cache(obj_id, update=True)
	user_page_comment_cache(user_id, update=True) # no longer needed really...
	user_page_obj_com_cache(user_id, update=True)
	#if the_object.news == True:
	#	news_front_cache(update = True)
	# elif the_object.learn == True:
	#	learn_front_cache(update = True)
def num_users_now():
	all_users = users_cache()
	if all_users:
		return len(all_users)
	else:
		return 0
def convert_text_to_markdown(string):
	'''escape, and save as markdown text'''
	escaped_text = cgi.escape(string)
	mkd_converted_string = mkd.convert(escaped_text)
	return mkd_converted_string
			

#########################################################
def user_update(update=False):
	if update:
		userlist = Users.all()
		logging.warning(userlist)
		userlist = list(userlist)
		logging.warning(userlist)
		counter = 1
		for user in userlist:
			user.username_lower = user.username.lower()
			logging.warning('putting user %d', counter)
			user.put()
			counter += 1
#user_update(update = True)
def obj_update(update=False):
	if update:
		objlist = Objects.all()
		logging.warning(objlist)
		objlist = list(objlist)
		logging.warning(objlist)
		counter = 1
		for obj in objlist:
			num_of_comments = len(obj_comment_cache(obj.key().id()))
			obj.total_num_of_comments = num_of_comments
			logging.warning('putting object %d', counter)
			obj.put()
			counter += 1
#obj_update(update = True)
def wikipage_update(update=False):
	if update:
		wiki_page_list = WikiEntry.all()
		logging.warning(wiki_page_list)
		wiki_page_list = list(wiki_page_list)
		logging.warning(wiki_page_list)
		counter = 1
		for entry in wiki_page_list:
			# some entry.blah = blah shit
			logging.warning('putting wiki entry %d', counter)
			entry.put()
			counter += 1
#wikipage_update(update = True)
def comments_update(update=False):
	if update:
		comment_list = Comments.all()
		logging.warning(comment_list)
		comment_list = list(comment_list)
		logging.warning(comment_list)
		counter = 1
		for comment in comment_list:
			# convert to markdown2
			escaped_comment_text = cgi.escape(comment.text)
			mkd_converted_comment = mkd.convert(escaped_comment_text)
			comment.markdown = mkd_converted_comment

			# some entry.blah = blah shit
			logging.warning('putting comment entry %d', counter)
			comment.put()
			counter += 1
#comments_update(update = True)
def message_update(update=False):
	if update:
		message_list = Messages.all()
		logging.warning(message_list)
		message_list = list(message_list)
		logging.warning(message_list)
		counter = 1
		for msg in message_list:
			# some entry.blah = blah shit
			logging.warning('putting message entry %d', counter)
			msg.put()
			counter += 1
#message_update(update = True)
def wikientry_update(update=False):
	if update:
		entry_list = WikiEntry.all()
		logging.warning(entry_list)
		entry_list = list(entry_list)
		logging.warning(entry_list)
		counter = 1
		for entry in entry_list:
			# convert to markdown2
			escaped_wikientry_text = cgi.escape(entry.content)
			mkd_converted_entry = mkd.convert(escaped_wikientry_text)
			entry.markdown = mkd_converted_entry

			# some entry.blah = blah shit
			logging.warning('putting wikientry entry %d', counter)
			entry.put()
			counter += 1
#wikientry_update(update = True)
#########################################################
## if db is empty, this creates default db entries and cache 
## to prevent unnessisary querys ##
def app_start_cache(update = False):
	# Disregard for the most part. This is only run to make sure there are default objects for all models. 
	key = 'app_start_cache'
	default_db_entries = memcache.get(key)
	if default_db_entries is None or update:
		user_var = db.GqlQuery("SELECT * FROM Users").get()
		logging.warning("DB initilization Query Users")
		if user_var == None:

			default_repo_entry = Users(username="Default_User",
										hashed_password= '%s' % (make_pw_hash("Default_User", "aoeu")))
			default_repo_entry.put()

		else:
			pass
		
		obj_var = db.GqlQuery("SELECT * FROM Objects").get()
		logging.warning("DB initilization Query Objects")
		if obj_var == None:

			default_repo_entry = Objects(title="Default_Object",
										author_id=0,
										author_name="Default_User",
										obj_type='upload',

										stl_file_link="http://www.example.com",
										main_img_link="http://www.example.com")
			default_repo_entry.description = "This is a default discription entry for testing purposes."
			default_repo_entry.put()
		else:
			pass

		comments_var = db.GqlQuery("SELECT * FROM Comments").get()
		logging.warning("DB initilization Query Comments")
		if comments_var == None:

			default_repo_entry = Comments(text="Default comment to prevent errors",
										author_name="Default_User",
										author_id=0,
										referent_id=0)
			default_repo_entry.put()

		else:
			pass
		
		# vote_var = db.GqlQuery("SELECT * FROM Vote").get()
		# logging.warning("DB initilization Query Vote")
		# if vote_var == None:
		# 	default_repo_entry = Vote()
		# 	default_repo_entry.put()
		# else:
		# 	pass

		# voter_var = db.GqlQuery("SELECT * FROM Voter").get()
		# logging.warning("DB initilization Query Voter")
		# if voter_var == None:
		# 	default_repo_entry = Voter()
		# 	default_repo_entry.put()
		# else:
		# 	pass

		default_db_entries = "Default objects created %d seconds from epoch." % int(round(time.time()))
		try:
			memcache.set(key, default_db_entries)
		except Exception as exception:
			logging.error("memcache set error")
			print exception
#app_start_cache()
#########################################################
#########################################################
#########################################################
REFERER_BLACKLIST = [
	'/login', 
	'/logout', 
	'/signup', 
	'/welcome', 
	'/user_page_img_upload',
	'/object_img_upload',
	'/object_img_delete',
	'/visitor_img_upload']
REG_EX = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
		('/', MainEverything),
		(r'/page/(\d+)', MainEverything),

		('/newmain', MainPageNew),
		('/topmain', MainPageTop),
		('/recentcommentsmain', MainPageRecentComments),
		('/objects', MainPageObjects),

		('/signup', SignUpPage),
		('/welcome', WelcomePage),
		('/contact', ContactPage),	
		('/login', LoginPage),
		('/logout', LogoutPage),

		(r'/user/(\d+)', UserPage),
		(r'/user/(\d+)/page/(\d+)', UserPage),
		(r'/user/printshelf/(\d+)', UserPrintshelf),
		(r'/user/messages/(\d+)', UserMessagePage),
		(r'/user/note/(\d+)', UserNotePage),
		(r'/user/edit/(\d+)', UserEdit),
		(r'/user/del/(\d+)', UserDelPage),
		('/user_page_img_upload', UserPageImgUpload),

		(r'/obj/(\d+)', ObjectPage),
		(r'/obj/edit/(\d+)', ObjectEdit),
		(r'/obj/tags/(\d+)', ObjectTagEdit),
		('/ajaxdescription/', AjaxDescriptionEdit),
		('/ajaxtag/', AjaxTagEdit),
		(r'/obj/del/(\d+)', ObjDelPage),
		('/object_img_upload', ObjectImgUpload),
		('/object_img_delete', ObjectImgDelete),
		('/object_page_specific_img_delete', ObjectSpecificImgDelete),
		('/visitor_img_upload', VisitorImgUpload),
		(r'/altfile/(\d+)', ObjectAltFile),
		('/altfileupload/', ObjectAltFileUpload),
		(r'/obj/(\d+)'+'.json', ObjectJSON),

		('/thingtracker', ThingTracker),

		(r'/com/(\d+)', CommentPage),

		('/university', UniMain),
		('/newuniversity', UniMainNew),
		('/topuniversity', UniMainTop),	
		('/video', UniMainVideo),
		('/newlesson', NewLessonPage),
		('/ask', NewAskPage),

		('/news', NewsPage),
		('/newnews', NewsPageNew),
		('/topnews', NewsPageTop),	
		('/newarticle', NewArticlePage),

		('/parts', RepRapTypesPage),

		('/tag', TagSearchMain),
		### tag_error is commented out above ###
		('/tag_error', TagMainError),
		###
		(r'/tag/([a-zA-Z0-9_-]+)', TagPage),
		
		('/nsfw', NsfwPage),

		('/new', NewPage),

		('/newobject', NewObjectPage),
		('/upload_obj1', NewObjectUpload1),
		(r'/newobject2/(\d+)', NewObjectPage2),
		(r'/upload_obj2/(\d+)', NewObjectUpload2),
		(r'/newobject3/(\d+)', NewObjectPage3),

		('/newlink', NewLinkPage),
		(r'/newlink2/(\d+)', NewLinkPage2),
		(r'/upload_link_photo/(\d+)', NewLinkUpload),
		('/newtor', NewTorPage),

		('/w_home', WikiMain),
		('/w' + REG_EX, WikiPage),
		('/_edit' + REG_EX, EditPage),
		('/_history' + REG_EX, HistoryPage),
		('/w_index', WikiIndex),

		('/vote/', VoteHandler),
		('/votecom/', CommentVoteHandler),
		('/rate/', RateHandler),
		('/flag/', FlagHandler),
		('/flagcom/', CommentFlagHandler),
		('/delcom/', DeleteCommentHandler),
		('/editcom/', EditCommentHandler),
		('/admin_del/', AdminDelHandler),
		('/block/', BlockHandler),
		('/follow/', FollowHandler),
		('/printshelf_add/', PrintshelfAddHandler),
		('/printshelf_remove/', PrintshelfRemoveHandler),
		('/sendmessage/', SendMessageHandler),

		('/newmessageworker', NewMessageWorker),
		('/tagupdateworker', TagUpdateWorker),

		('/admin', AdminPage),
		(r'/admin/(\d+)', AdminObjPage),
		(r'/emailconfirmation/([a-z0-9]+)', EmailConfirmationHandler),
		('/password_reset_request', PasswordResetHandler),
		('/password_reset_acknowledgement', PasswordResetAcknowledgement),
		(r'/password_reset_confirmation/([a-z0-9_-]+)', PasswordResetConfirmationHandler),

		('/tos', TermsPage),
		('/robots.txt', Robots),

		('/serve_obj/([^/]+)?', ObjFileServe),
		], debug=True)
################## Error Handlers #######################
def handle_404(request, response, exception):
	logging.exception(exception)
	response.write('''
		<style>
			* {
				margin:0px auto;
				font-family:Trebuchet MS,Liberation Sans,DejaVu Sans,sans-serif;
				//border:solid #999 1px;
			}
			* a{
				text-decoration: none;
				color:#0077cc;
			}

			* a:visited{
				color:#0077cc;
			}
		</style>
		<div>
			<div style="
				float:left;
				width:100%; 
				text-decoration:none; 
				background: white;
				color:#777;
				">
				<span style="float:left;">
					<a href="/" style="
						text-decoration:none; 
						font-weight:bold; 
						font-size:120%; 
						">
						<span style="
							color: #0077cc; 
							float: left;
							margin-left: 10px;
							margin-top: 3px;
							margin-right: 40px;			
							">
							<img src="/img/glassesprint.png" height="18px"/>
							Bld3r
						</span>
					</a>
					<span style="margin-top:5px; float:left;">
						<span  style="margin-right:5px;" title="New to 3d printing? Learn at Bld3r university.">
							<a href="/university">	
								learn
							</a>
						</span>
						|
						<span  style="margin-right:5px;" title="News about 3d printing.">
							<a href="/news">	
								news
							</a>
						</span>
						|
						<span  style="margin-right:5px; margin-left:5px;" title="Bld3r's wiki.">
							<a href="/w/home">
								community
							</a>
						</span>
						|
						<span  style="margin-right:5px;  margin-left:5px;" title="Search for an object.">
							<a style="text-decoration:none;" href="/tag">
								search
							</a>
						</span>
					</span>
				</span>
			</div>
			<div style="clear:both;height:1px">
			</div>

			<div style="
				width: 920px; 
				display: block; 
				margin-right: auto; 
				margin-left: auto;
				">
				<img src="/img/404_2.png" />
			</div>
		</div>
		''')
	response.set_status(404)
app.error_handlers[404] = handle_404
def handle_500(request, response, exception):
	logging.exception(exception)
	response.write('''
		<style>
			* {
				margin:0px auto;
				font-family:Trebuchet MS,Liberation Sans,DejaVu Sans,sans-serif;
				//border:solid #333 1px;
			}
			* a{
				text-decoration: none;
				color:#333;
			}

			* a:visited{
				color:#333;
			}
		</style>
		<div>
			<div style="
				float:left;
				width:100%; 
				text-decoration:none; 
				background: white;
				color:#333;
				">
				<span style="float:left;">
					<a href="/" style="
						text-decoration:none; 
						font-weight:bold; 
						font-size:120%; 
						">
						<span style="
							color: #333; 
							float: left;
							margin-left: 10px;
							margin-top: 3px;
							margin-right: 40px;			
							">
							<img src="/img/empty_white_favicon.png" height="18px"/>
							Bld3r
						</span>
					</a>
					<span style="margin-top:5px; float:left;">
						<span  style="margin-right:5px;" title="New to 3d printing? Learn at Bld3r university.">
							<a href="/university">	
								learn
							</a>
						</span>
						|
						<span  style="margin-right:5px;" title="News about 3d printing.">
							<a href="/news">	
								news
							</a>
						</span>
						|
						<span  style="margin-right:5px; margin-left:5px;" title="Bld3r's wiki.">
							<a href="/w/home">
								community
							</a>
						</span>
						|
						<span  style="margin-right:5px;  margin-left:5px;" title="Search for an object.">
							<a style="text-decoration:none;" href="/tag">
								search
							</a>
						</span>
					</span>
				</span>
			</div>
			<div style="clear:both;height:1px">
			</div>

			<div style="
				width: 920px; 
				display: block; 
				margin-right: auto; 
				margin-left: auto;
				">
				<img src="/img/500.png" />
			</div>
		</div>
		''')
	response.set_status(500)
app.error_handlers[500] = handle_500

