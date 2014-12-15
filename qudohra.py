from google.appengine.api import users
from google.appengine.ext import ndb
from datetime import datetime

import cgi
import os
import webapp2
import jinja2
import re


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


# 1)The system should handle multiple users and each user should be able to create questions, answer them, or vote.
# 2)Users should be able to edit any questions or answers they have created, or change any votes. 
# 4)When viewing all questions, it will show at most 10 questions on a page, with a link to go to the next page of older questions (you don't need a "newer questions" link).
# 5)When viewing the answers to a question, answers should be sorted by largest difference between up and down votes to smallest difference.
# 6)Each question should support the notion of having tags. When creating or editing a question, the author can specify 0 or more tags. When viewing questions, the viewer can look at all questions (the default) or only questions with a specific tag.
# 7)When questions or answers contain links (text that begins with http:// or https://), they will be displayed as HTML links when viewed.  If a link ends with .jpg, .png, or .gif, it will be displayed inline rather than as a link.
# 8)Images can be uploaded.  These will be available via a permalink after uploaded, and can be referenced using links in the posts.
# 9)When multiple questions are shown on the same page (the default view), each question will display the content capped at 500 characters.  Each question will have a "permalink" that, when followed, shows the complete content of the post on its own page.
# 11)Each question will have an RSS link, that dumps all questions and answers in XML format (see wiki page for example).
#### MODELS ####

class User(ndb.Model):
	user = ndb.UserProperty(indexed=True)
	votes = 

	# use user def to create custom user class, retreive user and see their votes, when voting automatically add/subtract from qid in question

class VoteHolder(ndb.Model):
	date = ndb.DateTimeProperty(auto_now=True)
	questionid = ndb.StringProperty(indexed=True)
	answerid = ndb.StringProperty(indexed=True)
	votedup = ndb.StringProperty(repeated=True)
	voteddown = ndb.StringProperty(repeated=True)


class Answer(ndb.Model):

	user = ndb.UserProperty()
	questionid = ndb.StringProperty(indexed=True)
	content = ndb.StringProperty(indexed=False)
	dateCreated = ndb.DateTimeProperty(auto_now_add=True)
	dateModified = ndb.DateTimeProperty(auto_now=True)
	vote = ndb.IntegerProperty(default=0)

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

def renderIfLoggedIn(me, template, templateValues={}):
	self = me
	user = users.get_current_user()

	if user:
		try:
			val = templateValues["user"]
		except KeyError:
			templateValues["user"] = user 

		template = JINJA_ENVIRONMENT.get_template('templates/' + template)
		self.response.write(template.render(templateValues))
	else:
		self.redirect(users.create_login_url(self.request.uri))

def replaceWithImages(string):
	r = re.compile(r"@(https?|ftp)://(-\.)?([^\s/?\.#-]+\.?)+(/[^\s]*)?$@iS")
	print r.sub(string, "<img src='\1'/>")

#### PAGES ####

class HomePage(webapp2.RequestHandler):
	def get(self):
		template = JINJA_ENVIRONMENT.get_template('templates/home.html')
		self.response.write(template.render({}))

class IndexPage(webapp2.RequestHandler):

    def get(self):
    	questionQuery = Question.query(ancestor=questionListKey()).order(-Question.dateModified)
    	questionsList = questionQuery.fetch()
        renderIfLoggedIn(self,'index.html', {'questions': questionsList})



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



class ShowQuestionPage(webapp2.RequestHandler):

	def get(self):
		return


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
			answer.content = self.request.get('content')
			answer.user = user
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

class ShowAnswerPage(webapp2.RequestHandler):

	def get(self):
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
		qid = self.request.get('questionid')
		qKey = ndb.Key(urlsafe=qid)
		question = qKey.get()
		renderIfLoggedIn(self, 'editquestion.html', {'question': question})
		return

class VoteQuestionPage(webapp2.RequestHandler):

	def get(self):
		user = users.get_current_user
		if user:
			qid = self.request.get('questionid')
			qKey = ndb.Key(urlsafe=qid)

			query = VoteHolder.query(ancestor=qKey)
			voteholder = query.fetch(1)

			# if previous voteholder exists for this question
			if voteholder:
				if self.request.get('direction') == 'up':
					if str(user.key) in voteholder.votedup:
						self.redirect('/index')
					else:
						voteholder.votedup.append(str(user.key))
				else:
					if str(user.key) in voteholder.voteddown:
						self.redirect('/index')
					else:
						voteholder.voteddown.append(str(user.key))

			# else this is the first voteholder on this question
			else:
				voteholder = VoteHolder(parent=qKey)
				voteholder.questionid = qid

				if self.request.get('direction') == 'up':
					voteholder.votedup.append(str(user.user_id()))
				elif self.request.get('direction') == 'down':
					voteholder.voteddown.append(str(user.key))
				else:
					self.redirect('/index')
				voteholder.put()
		else:
			self.redirect('/index')
		return

# class VoteAnswerPage(webapp2.RequestHandler):

# 	def post(self):
# 		qid = self.request.get('questionid')
# 		qKey = ndb.Key(urlsafe=qid)
# 		voteholder = VoteHolder(parent=qkey)
# 			question.user = user
# 			question.content = cgi.escape(self.request.get('question'))
# 			question.tags = cgi.escape(self.request.get('tags')).split()
# 			question.answers = []
# 			question.put()
# 		return

class AddImagePage(webapp2.RequestHandler):

	def get(self):
		return

	def post(self):
		return



application = webapp2.WSGIApplication([
	('/', HomePage),
   	('/index', IndexPage),
    ('/addquestion', AddQuestionPage),
    ('/addanswer', AddAnswerPage),
    ('/editquestion', EditQuestionPage),
    ('/editanswer', EditAnswerPage),
    ('/votequestion', VoteQuestionPage)
], debug=True)
