class Test(object):
	@staticmethod
	def func(qid):
		print qid
		print "printed"

class Other(object):
	def otherFunc(arg, string):
		Test.func(string)

other = Other()

other.otherFunc("ss")