from urllib.request import urlopen
import json

def get_blogs():
    url = 'https://skushagra.github.io/pvm/blog.json'
    blog = urlopen(url)
    blog = json.loads(blog.read().decode('utf-8'))
    return blog