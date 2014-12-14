from google.appengine.api import users
from google.appengine.ext import ndb
from datetime import datetime

import cgi
import os
import webapp2
import jinja2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


#### MODELS ####

class Question(ndb.Model):

	user = ndb.UserProperty()
	content = ndb.StringProperty(indexed=False)
	dateCreated = ndb.DateProperty(auto_now_add=True)
	dateModified = ndb.DateProperty()
	tags = ndb.StringProperty(repeated=True)

class Answer(ndb.Model):
	user = ndb.UserProperty()
	questionid = ndb.StringProperty(indexed=True)
	content = ndb.StringProperty(indexed=False)
	dateCreated = ndb.DateProperty(auto_now_add=True)
	dateModified = ndb.DateProperty()

#### /MODELS ####


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


#### PAGES ####

class MainPage(webapp2.RequestHandler):

    def get(self):
    	questionQuery = Question.query(ancestor=None).order(-Question.dateModified)
    	self.response.write('test')
    	questionsList = questionQuery.fetch()
        renderIfLoggedIn(self,'index.html', {'questions': questionsList})



class AddQuestionPage(webapp2.RequestHandler):

	def get(self):
		renderIfLoggedIn(self, 'addquestion.html')

	def post(self):
		user = users.get_current_user()

		if user:
			question = Question()
			question.user = user
			question.content = cgi.escape(self.request.get('question'))
			question.tags = cgi.escape(self.request.get('tags')).split()
			question.dateModified = datetime.now()
			question.put()
			self.redirect("/")
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
		user = users.get_current_user

		if user:
			qid = self.request.get('questionid')
			
			answer = Answer()
			answer.questionid = qid
			answer.content = self.request.post('content')
			answer.user = user
			answer.dateModified = datetime.now()
			answer.put()
		else:
			self.redirect('/')

class ShowAnswerPage(webapp2.RequestHandler):

	def get(self):
		return


class EditQuestionPage(webapp2.RequestHandler):

	def get(self):
		return


class AddImagePage(webapp2.RequestHandler):

	def get(self):
		return



application = webapp2.WSGIApplication([
   	('/', MainPage),
    ('/addquestion', AddQuestionPage),
    ('/addanswer', AddAnswerPage)
], debug=True)
