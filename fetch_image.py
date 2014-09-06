import urllib2, cookielib
import urllib
from sgmllib import SGMLParser
import os

url_head = 'http://www.chictopia.com'

def log(message, level = 'INFO'):
    print '[' + level + ']', message

class ItemParser(SGMLParser):
    start_get_urls = False
    start_get_tags = False
    start_get_num = False
    tags = []
    urls = []
    number = None

    def __Init__(self):
        SGMLParser.__init__(self)
        self.urls = []
        self.tags = []

    def convert_url(self, url):
        url = 'http://images' + self.number + url[14:]
        index = url.index('_sm.jpg')
        url = url[:index] + '_400.jpg'
        return url

    def start_div(self, attrs):
        for k,v in attrs:
            if k == 'class' and v == 'subphoto_items':
                self.start_get_urls = True
            if k == 'class' and v == 'left px10':
                self.start_get_tags = True
            if k == 'id' and v == 'image_wrap':
                self.start_get_num = True

    def end_div(self):
        self.start_get_urls = False
        self.start_get_num = False

    def start_img(self, attrs):
        if self.start_get_num:
            for k,v in attrs:
                if k == 'src':
                    self.number = v[13]
                    self.start_get_num = False
        if self.start_get_urls:
            for k,v in attrs:
                if k == 'src':
                    try:
                        self.urls.append(self.convert_url(v))
                    except:
                        log('convert url fail:' + v, 'ERROR')
    
    def handle_data(self, data):
        if self.start_get_tags == True:
            self.tags.append(data)
            self.start_get_tags = False
 
    def clean(self):
        self.urls = []
        self.tags = []
        ItemParser.urls = []
        ItemParser.tags = []

class Item:
    def __init__(self):
        self.tags = []
        self.new_tags = []
        self.image_urls = []
        self.url = ''
        self.images = []
    
    def add_tag(self, tag):
        self.tags.append(tag) 

    def set_url(self, url):
        self.url = url 

    def show(self):
        print self.url 
        print self.tags
        print self.new_tags 
        print self.image_urls

    def parse(self):
        try:
            log("start parsing " + self.url)
            content = urllib2.urlopen(self.url).read()
            parser = ItemParser()
            parser.feed(content)
            self.new_tags = parser.tags
            self.image_urls = parser.urls
            parser.clean()
            return True
        except:
            return False

    def get_images(self):
        if len(self.image_urls) <= 1:
            return False
        try:
            for url in self.image_urls:
                log('fetch image ' + url)
                content = urllib2.urlopen(url).read()
                self.images.append(content)
            return True    
        except:
            return False

    def clean_images(self):
        self.images = []

def convert_tag(tag):
    index = tag.index('/info')
    return tag[1:index]

class ItemListParser(SGMLParser):
    to_end = False
    start = False
    get_a = False
    to_end = True 
    start_get_tags = False
    items = [] 
    cur_item = None

    def __Init__(self):
        SGMLParser.__init__(self)
        self.items = []

    def start_div(self, attrs):
        for k,v in attrs:
            if k != 'class':
                continue
            if v == 'lg_photo photo_hover':
                self.start = True
                self.get_a = False
                self.to_end = False
                self.start_get_tags = False
                self.cur_item = Item()
                return
            if v == 'white px10 ellipsis':
                if not self.get_a:
                    return
                self.start_get_tags = True
                return
            if v == 'white px10':
                self.start_get_tags = False 
                self.to_end = True
    
    def start_a(self, attrs):
        if not self.start:
            return
        if not self.get_a:
            for k,v in attrs:
                if k == 'href':
                    self.get_a = True
                    self.cur_item.set_url(url_head + v)
                    self.items.append(self.cur_item)
        if self.start_get_tags:
            for k,v in attrs:
                if k == 'href':
                    try:
                        self.cur_item.add_tag(convert_tag(v))
                    except:
                        log('convert tag fail', 'ERROR')
    
    def end_div(self):
        if self.to_end:
            self.to_end = False

    def clean_items(self):
        self.items = []
        ItemListParser.items = []

#url1='http://www.chictopia.com/photo/show/1059006-Like+The+Cool+Kids-brown-winners-sandals-black-nina-ricci-bag-dark-brown-firmoo-sunglasses'
#url2='http://images2.chictopia.com/photos/KristaniA/4220878207/black-nina-ricci-bag-dark-brown-firmoo-sunglasses_400.jpg'

def get_new_id():
    global start_id 
    start_id += 1
    return start_id 

def complete_dir(dir):
    if dir[len(dir) - 1] != '/':
        dir += '/'
    return dir

def write_single_img(dir, filename, data):
    dir = complete_dir(dir)
    try:    
        img = open(dir + filename, 'wb')
        img.write(data)
        img.close()
    except:
        log('write image fail:' + dir + filename, 'ERROR')

def write_txt(dir, filename, elements):
    dir = complete_dir(dir)
    try:
        file = open(dir + filename, 'w')
        for i in range(len(elements)):
            file.write(str(i + 1) + ' ' + elements[i] + '\n')
        file.close()
    except:
        log('write txt fail:' + dir + filename, 'ERROR')

def write_images(dir, images):
    for i in range(len(images)):
        write_single_img(dir, str(i + 1), images[i])

def save_item(item):
    global save_path
    id = get_new_id() 
    dir = save_path + str(id)
    if not os.path.exists(dir):
        os.makedirs(dir)
    write_txt(dir, 'url.txt', item.image_urls)
    write_txt(dir, 'tag.txt', item.tags)
    write_txt(dir, 'ntag.txt', item.new_tags)
    write_images(dir, item.images)

def parse_and_save_item(item):
    if not item.parse():
        return
    if not item.get_images():
        return
    save_item(item)

def parse_and_save_all_item(items):
    for item in items:
        if already_fetched(item.url):
            log(item.url + ' is already fetched')
            continue
        parse_and_save_item(item)
        record_fetched(item.url)
        item.clean_images()

fetched = set()
url='http://www.chictopia.com/browse/people'

def load_fetched_urls():
    global fetched
    try:
        file = open('fetched', 'r')
        while True:
            url = file.readline()
            if url == '':
                break
                
            if url == None:
                break
            fetched.add(url[:len(url) - 1])
        file.close()
    except:
        pass

def save_fetched_url(url):
    try: 
        file = open('fetched', 'a+')
        file.write(url +'\n')
        file.close()
    except:
        pass

def record_fetched(url):
    global fetched
    save_fetched_url(url)
    fetched.add(url)
    
def already_fetched(url):
    global fetched
    if url in fetched:
        return True
    return False

def fetch():
    global url
    global start_page_index
    global end_page_index
    for i in range(start_page_index, end_page_index + 1):
        local_url = url + '/' + str(i)
        print '\nprocessing the page ' + str(i) 
        print 'url', local_url
        response = urllib2.urlopen(local_url).read()
        parser = ItemListParser()
        parser.feed(response)
        items = parser.items
        parser.clean_items()
        print 'elements number:', len(items), '\n'
        parse_and_save_all_item(items)

start_id = 0
def init_start_id():
    global start_id
    global max_id
    global save_path
    for i in range(max_id):
        if not os.path.exists(save_path + str(i + 1)):
            start_id = i
            return

save_path = './images/'
max_id = 10000
start_page_index = 1
end_page_index = 5
init_start_id()
load_fetched_urls()
fetch()
