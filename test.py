import re

def replaceWithImages(string):
	ans = re.sub(r"(((https?):((//)|(\\\\))+([\w\d:#@%/;$()~_?\+-=\\\.&](#!)?)*)(.jpg|.png|.gif|.jpeg))", r"<img src='\1'> \1 </img>",  string)
	return ans


def replaceWithLinks(string):
	ans = re.sub(r"(https?.+(?<![jpg])(?<![gif])(?<![png]))", r"<a href='\1'>Link</a>",  string)
	return ans


print replaceWithLinks("apple banana https://google.com/apple.jpg cucumber")