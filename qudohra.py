from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


import cgi
import os
import urllib
import webapp2
import jinja2
import re

def replaceWithImages(string):
	ans = re.sub(r"(((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)(.jpg|.png|.gif|.jpeg))", r"<img src='\1'> </img>",  string)
	return ans

def replaceWithLinks(string):
	finalans = "" 
	ans = re.findall(r"((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)", string)
	i = 0
	while i < len(ans):
		curr = ans[i][0]
		if not re.match(r"(((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)(.jpg|.png|.gif|.jpeg))", curr):
			print curr + " does not match"
			finalans = re.sub(curr, "<a href='" + curr + "'>" + curr + "</a>", string)
		i+=1 
	if not finalans:
		return string
	else:
		return finalans


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
JINJA_ENVIRONMENT.globals['replaceWithImages'] = replaceWithImages 
JINJA_ENVIRONMENT.globals['replaceWithLinks'] = replaceWithLinks 

#### MODELS ####

class UserModel(ndb.Model):
	user = ndb.UserProperty(indexed=True)
	qvotesup = ndb.StringProperty(repeated=True)
	qvotesdown = ndb.StringProperty(repeated=True)
	avotesup = ndb.StringProperty(repeated=True)
	avotesdown = ndb.StringProperty(repeated=True)

class Answer(ndb.Model):

	user = ndb.UserProperty()
	questionid = ndb.StringProperty(indexed=True)
	content = ndb.StringProperty(indexed=False)
	dateCreated = ndb.DateTimeProperty(auto_now_add=True)
	dateModified = ndb.DateTimeProperty(auto_now=True)
	vote = ndb.IntegerProperty(default=0)
	ukey = ndb.KeyProperty()

class Question(ndb.Model):

	user = ndb.UserProperty()
	content = ndb.StringProperty(indexed=False)
	dateCreated = ndb.DateTimeProperty(auto_now_add=True)
	dateModified = ndb.DateTimeProperty(auto_now=True)
	tags = ndb.StringProperty(repeated=True)
	answers = ndb.StructuredProperty(Answer, repeated=True)	
	vote = ndb.IntegerProperty(default=0)




#### /MODELS ####

class QuestionList(webapp2.RequestHandler):
	def method(self):
		return

def questionListKey(name="QuestionList"):
	return ndb.Key('QuestionList', name)

def getUserModel(user):
	q = UserModel.query(UserModel.user == user)
	usermodel = q.get()

	if not usermodel:
		usermodel = UserModel()
		usermodel.user = user
		usermodel.put()
	return usermodel 


def renderIfLoggedIn(me, template, templateValues={}):
	self = me
	user = users.get_current_user()
	
	if user:
		usermodel = getUserModel(user)
		templateValues['usermodel'] = usermodel

		try:
			val = templateValues["user"]
		except KeyError:
			templateValues["user"] = user 

		template = JINJA_ENVIRONMENT.get_template('templates/' + template)
		self.response.write(template.render(templateValues))
	else:
		self.redirect(users.create_login_url(self.request.uri))



def quicksort(array):
	less = []
	equal = []
	greater = []

	if len(array) > 1:
		pivot = abs(array[0].vote)
		for x in array:
		    if abs(x.vote) < pivot:
		        less.append(x)
		    if abs(x.vote) == pivot:
		        equal.append(x)
		    if abs(x.vote) > pivot:
		        greater.append(x)
		return quicksort(greater)+equal+quicksort(less) 
	else:  
		return array

#### PAGES ####

class HomePage(webapp2.RequestHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('templates/home.html')
		self.response.write(template.render({}))

class IndexPage(webapp2.RequestHandler):

    def get(self):
    	page_num = self.request.get('page_num')
    	if page_num:
    		offset = (int(page_num)-1)* 10;
    	else:
    		page_num = 1
    		offset = 0

    	sort = self.request.get('sort')

    	if sort:
    		questionQuery = Question.query(ancestor=questionListKey()).filter(ndb.StringProperty('tags') == sort).order(-Question.dateModified)
    	else:
    		questionQuery = Question.query(ancestor=questionListKey()).order(-Question.dateModified)

    	if questionQuery.count() <= page_num * 10:
    		page_num = 0

    	questionsList = questionQuery.fetch(10, offset=offset)

        renderIfLoggedIn(self,'index.html', {'questions': questionsList, 'sort' : sort, 'page': str(page_num)})



class AddQuestionPage(webapp2.RequestHandler):

	def get(self):
		renderIfLoggedIn(self, 'addquestion.html')

	def post(self):
		user = users.get_current_user()

		if user:
			question = Question(parent=questionListKey())
			question.user = user
			question.content = cgi.escape(self.request.get('question'))
			question.tags = cgi.escape(self.request.get('tags')).split()
			question.answers = []
			question.put()
			self.redirect("/index")
			#Add question, redirect to index



class AddAnswerPage(webapp2.RequestHandler):

	def get(self):
		qid = self.request.get('questionid')
		qKey = ndb.Key(urlsafe=qid)
		question = qKey.get()
		renderIfLoggedIn(self, 'addanswer.html', {'question': question})


	def post(self):
		user = users.get_current_user()

		if user:
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)
			question = qKey.get()

			answer = Answer()
			answer.questionid = qid
			answer.content = cgi.escape(self.request.get('content'))
			answer.user = user
			answer.put()
			answer.ukey = answer.key
			answer.put()

			i = 0
			while i < len(question.answers):
				if 0 > question.answers[i].vote:
					question.answers.insert(i+1, answer)
				else: 
					i+=1
			if i == len(question.answers):
				question.answers.append(answer)

			question.put()
			self.redirect('/index')

		else:
			self.redirect('/index')



class ShowQuestionPage(webapp2.RequestHandler):

	def get(self):
		qid = self.request.get('questionid')
		qKey = ndb.Key(urlsafe=qid)
		question = qKey.get()
		template = JINJA_ENVIRONMENT.get_template('templates/showquestion.html')
		self.response.write(template.render({'question' : question}))
		return

class EditQuestionPage(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()
		if user:
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)
			question = qKey.get()

			if question.user == user:
				tags =  ' '.join(question.tags)
				renderIfLoggedIn(self, 'editquestion.html', {'question': question, 'tags' : tags})
			else:
				self.redirect('/index')
		else:
			self.redirect('/index')

			return

	def post(self):
		qid = self.request.get('questionid')
		qKey = ndb.Key(urlsafe=qid)
		question = qKey.get()
		question.content = cgi.escape(self.request.get('content'))
		question.tags = cgi.escape(self.request.get('tags')).split()
		question.put()
		self.redirect('/index')


class EditAnswerPage(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()
		if user:
			aid = self.request.get('answerid')
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)
			question = qKey.get()

			i = 0
			for ans in question.answers:
				if ans.ukey and ans.ukey.urlsafe() == aid:
					answer = ans

			if answer.user == user:
				renderIfLoggedIn(self, 'editanswer.html', {'question': question, 'answer' : answer})
			else:
				self.redirect('/index')
		else:
			self.redirect('/index')

		return

	def post(self):
		user = users.get_current_user()
		if user:
			aid = self.request.get('answerid')
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)
			question = qKey.get()

			i = 0
			for ans in question.answers:
				if ans.ukey and ans.ukey.urlsafe() == aid:
					answer = ans
			answer.content = cgi.escape(self.request.get('content'));
			answer.put()
			question.put()
			self.redirect('/index')
			return


class VoteQuestionPage(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()

		if user:
			usermodel = getUserModel(user)
			direction = self.request.get('direction').strip()
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)
			question = qKey.get()

			if direction == 'up':
				if qid not in usermodel.qvotesup:
					question.vote += 1
					question.put()
					usermodel.qvotesup.append(qid)
					usermodel.put()
					self.redirect('/index')
					self.response.write("Voted question down")
				else:
					self.redirect('/index')
			elif direction == 'down':
				if qid not in usermodel.qvotesdown:
					question.vote -= 1
					question.put()
					usermodel.qvotesdown.append(qid)
					usermodel.put()
					self.redirect('/index')
					self.response.write("Voted question down")
				else:
					self.redirect('/index')

			else:
				self.redirect('/index')

		else:
			self.redirect('/index')
		return

class VoteAnswerPage(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user()

		if user:
			usermodel = getUserModel(user)
			direction = self.request.get('direction').strip()
			aid = self.request.get('answerid')
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)
			question = qKey.get()

			i = 0
			for ans in question.answers:
				if ans.ukey and ans.ukey.urlsafe() == aid:
					answer = ans

			if direction == 'up':
				if aid not in usermodel.avotesup:
					answer.vote += 1
					question.answers = quicksort(question.answers)
					question.put()
					usermodel.avotesup.append(aid)
					usermodel.put()
					self.redirect('/index')
				else:
					self.redirect('/index')
			elif direction == 'down':
				if aid not in usermodel.avotesdown:
					answer.vote -= 1
					question.answers = quicksort(question.answers)
					question.put()
					usermodel.avotesdown.append(aid)
					usermodel.put()
					self.redirect(last_page)
				else:
					self.redirect('/index')

			else:
				self.redirect('/index')
		else:
			self.redirect('/index')
		return

class AddImagePage(webapp2.RequestHandler):

	def get(self):
		upload_url = blobstore.create_upload_url('/upload')
		renderIfLoggedIn(self, 'addimage.html', {'upload_url': upload_url})
		return

	def post(self):
		return

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
	def post(self):
		upload_files = self.get_uploads('file')  
		blob_info = upload_files[0]
		self.redirect('/serve/%s' % blob_info.key())

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
	def get(self, resource):
		resource = str(urllib.unquote(resource))
		blob_info = blobstore.BlobInfo.get(resource)
		self.send_blob(blob_info)


# class RSSPage(webapp2.RequestHandler):
# 	def get(self):
# 		questionQuery = Question.query(ancestor=questionListKey()).order(-Question.dateModified)
# 		questionsList = questionQuery.fetch()
# 		self.response.headers['Content-Type'] = 'text/rss+xml'
# 		self.response.write("""<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0"><channel><title>Qudo'hra</title><link>qudohra.appspot.com/index</link><description>Homer Simpson's Quora</description>""")
# 		for question in questionsList:
# 			anscontent = ""
# 			for ans in question.answers:
#  				anscontent += str(ans.user) + " answered: " + ans.content + ".  "
# 			self.response.write("""<item><title>{0}</title><link>{1}</link><description>{2}</description></item>""".format(question.content,("qudohra.appspot.com/showquestion/" + question.key.urlsafe()),anscontent))
# 	 	self.response.write('</channel></rss>')
# 	 	return

application = webapp2.WSGIApplication([
	('/', HomePage),
   	('/index', IndexPage),
    ('/addquestion', AddQuestionPage),
    ('/addanswer', AddAnswerPage),
    ('/editquestion', EditQuestionPage),
    ('/editanswer', EditAnswerPage),
    ('/votequestion', VoteQuestionPage),
	('/voteanswer', VoteAnswerPage),
	('/showquestion', ShowQuestionPage),
	('/addimage', AddImagePage),
	('/upload', UploadHandler),
	('/serve/([^/]+)?', ServeHandler),
	# ('/rss', RSSPage)

], debug=True)
