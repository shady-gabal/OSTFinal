import re

def replaceWithImages(string):
	ans = re.sub(r"(((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)(.jpg|.png|.gif|.jpeg))", r"<img src='\1'> \1 </img>",  string)
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

print replaceWithLinks("apple banana https://google.com/apple.jpg cucumber")
print replaceWithLinks("apple banana https://google.com/apple.jpg cucumber https://google.com/apple.pg https://applele.com/apple.jpg ")