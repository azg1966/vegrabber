from html.parser import HTMLParser
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime
import os, re, codecs, glob, pickle, socket




IMAGE_DIR = 'images'
HTML_DIR = 'html'
LINKS = {}
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:37.0) Gecko/20100101 Firefox/37.0'
TIMEOUT = 5

class ImgHost(HTMLParser):

    host = ''
    path = ''

    def __init__(self, page_url):
        self.page_url = page_url
        super(ImgHost, self).__init__()

    def grab_image(self):
        try:
            print('Load page', self.page_url)
            res = urlopen(self.page_url)
        except URLError as e:
            print('Connect timeout:{}'.format(self.page_url))
        except ConnectionResetError:
            print('ConnectionResetError')
        else:
            if res.status in (304, 200):
                html = res.read().decode()
                self.feed(html)
            else:
                print('Load page error: status={}'.\
                      format(res.status))

    def parse_filename(self, url):
        return urlparse(url).path.rsplit('/')[-1]

    def save_image(self, url, filename):
        try:
            print('Load image', url)
            res = urlopen(url)
        except URLError:
            print('Connect timeout:{}'.format(url))
        else:
            if res.status in (304, 200):
                filename = os.path.join(IMAGE_DIR, self.path, filename)
                if not os.path.exists(filename):
                    with open(filename, 'w+b') as f:
                        f.write(res.read())
            else:
                print('Save image {} error: status={}'.\
                      format(url, res.status))


class ImageVenue(ImgHost):
    host = 'imagevenue.com'
    path = 'imagevenue'

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            attrs = dict(attrs)
            if attrs.get('id', None) == 'thepic':
                parsed_url = urlparse(self.page_url)
                img_src = parsed_url.scheme+'://'+\
                          parsed_url.netloc+'/'+\
                          attrs.get('src', '')
                filename = self.parse_filename(img_src)
                self.save_image(img_src, filename)


class KingHost(ImgHost):
    host = 'kinghost.com'
    path = 'kinghost'

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs = dict(attrs)
            href = attrs.get('href', None)
            if href and href.find('.jpg') != -1:
                img_src = urljoin(self.page_url, href)
                filename = self.parse_filename(img_src)
                self.save_image(img_src, filename)

    def parse_filename(self, url):
        prefix, filename = url.rsplit('/', 2)[1:]
        return prefix + '_' + filename


class ImageBam(ImgHost):
    host = 'imagebam.com'
    path = 'imagebam'

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            attrs = dict(attrs)
            if attrs.get('alt', None) == 'loading':
                img_src = attrs['src']
                filename = self.parse_filename(img_src)
                self.save_image(img_src, filename)


class VintageForumParser(HTMLParser):

    def __init__(self):
        self.hosts = [cls.host for cls in ImgHost.__subclasses__()]
        self.links =[]
        super(VintageForumParser, self).__init__()

    def handle_starttag(self, tag, attrs):
        if tag !=  'a':
            return
        attrs = dict(attrs)
        href = attrs.get('href', None)
        if href:
            for host in self.hosts:
                if re.search(host, href):
                    self.links.append(href)

    def parse_file(self, filename):
        if not os.path.exists(filename):
            print('File not found')
        if os.path.isdir(filename):
            html_files = glob.glob(os.path.join(filename, '*.html'))
            for html_file in html_files:
                self.feed(self.get_html(html_file))
        else:
            self.feed(self.get_html(filename))

    @classmethod
    def get_html(cls, filename, encoding='cp1252'):
        with codecs.open(filename, 'r', encoding=encoding) as f:
            return f.read()


def  main():
    vp = VintageForumParser()
    vp.parse_file('html')
    print('Links count:', len(vp.links))
    # hosts = {}
    # for cls in ImgHost.__subclasses__():
    #     path = os.path.join(IMAGE_DIR, cls.path)
    #     if not os.path.exists(path):
    #         os.makedirs(path)
    #     hosts[cls.host] = cls

    # kh = KingHost('http://www7.kinghost.com/hardcore/hardashell/chessiexxx/21a/')
    # kh.grab_image()
    # iv = ImageVenue('http://img5.imagevenue.com/img.php?image=86260_CC158_001_orig_123_503lo.jpg')
    # iv.grab_image()

    # with open('links', 'r+b') as f:
    #     links = pickle.loads(f.read())

    # for host in links:
    #     loader = hosts[host]
    #     i = 1
    #     a = len(links[host])
    #     for link in links[host]:
    #         print('{}/{}'.format(i, a), end='')
    #         i += 1
    #         l = loader(link)
    #         l.grab_image()


if __name__ == '__main__':
    main()
