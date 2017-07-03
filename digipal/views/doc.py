from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404
import re

'''
TODO:

HTML -> MD

   get the big images 
   table of conent

md -> HTML

    

render
    
    headings with font size proportional to level
    image zoom
    image legend 
'''


def doc_view(request, path):
    template = 'digipal/doc_page.html'
    context = {}

    context['doc'] = get_doc_from_path(path, request)

    return render_to_response(template, context, context_instance=RequestContext(request))


def get_doc_from_path(path, request=None):
    # find the doc file from the given path
    file_path = get_doc_absolute_path(path)

    # read the raw doc
    from digipal.management.commands.utils import readFile
    md = readFile(file_path)

    # transform into HTML
    ret = get_doc_from_md(md, request)

    return ret


def get_doc_from_md(md, request=None):
    '''Returns the doc info structure from a mark down text (md)'''
    ret = {'title': 'Untitled'}

    # get the first main title
    for i in range(1, 4):
        pattern = ur'(?musi)^%s\s+(.*?)$' % ('#' * i)
        m = re.search(pattern, md)
        if m:
            ret['title'] = m.group(1)
            # If the doc starts with a main title, we remove it
            # as it will be preserved in the CMS Page title
            # Without this, the title would appear twice on the site.
            md = re.sub(ur'(?usi)^\s*', '', md)
            md = re.sub(ur'(?usi)\s*$', '', md)
            md = re.sub(ur'(?ui)^#\s+[^\n\r]*', '', md)
            break

    # convert the document to HTML
    import markdown2
    from django.utils.safestring import mark_safe

    md = preprocess_markdown(md, request)

    html = markdown2.markdown(md)

    html = postprocess_markdown(html, request)

    ret['content'] = mark_safe(html)

    return ret


def postprocess_markdown(html, request):
    ret = html
    #ret = re.sub('<code>', '<pre>', ret)
    #ret = re.sub('</code>', '</pre>', ret)

    # add anchor to each heading
    # <h1>My Heading</h1>
    # =>
    # <h1><a href="#my-heading" name="my-heading">My Heading</a></h1>
    #
    from django.utils.text import slugify
    pos = 1
    pattern = re.compile(ur'(<h\d>)([^<]*)(</h\d>)')
    while True:
        # pos-1 because we want to include the last > we've inserted in the previous loop.
        # without this we might miss occurrences
        m = pattern.search(ret, pos - 1)

        if not m:
            break

        anchor_name = slugify(m.group(2).strip())
        replacement = ur'%s<a href="#%s" id="%s">%s</a>%s' % (
            m.group(1), anchor_name, anchor_name, m.group(2), m.group(3))

        ret = ret[:m.start(0)] + replacement + ret[m.end(0):]

        pos = m.start(0) + len(replacement)

    # convert links to static files
    # <img href="/digipal/static/doc/april-boat.jpg?raw=true"/>
    # => <img href="/static/doc/april-boat.jpg?raw=true"/>
    # We have to make sure the URL is relative to this site (i.e. starts with /)
    # We assume that doc images are stored in a 'static' folder in the repo.
    # We also assume that the web path to static files starts with 'static'.
    ret = re.sub(ur'(href|src)="/[^"]*(/static/[^"]*)"', ur'\1="\2"', ret)

    return ret


def preprocess_markdown(md, request):
    ret = md

    # As opposed to github MD, python MD will parse the content of ` and ```
    # E.g. ```\n#test\n``` => <h1>test</h1>
    # So we convert ` and ``` to 4 space indent to produce the intended effect
    lines = ret.split('\n')
    in_code = False
    new_lines = []
    for line in lines:
        code_swicth = line.rstrip() in ['`', '```']
        if code_swicth:
            in_code = not in_code
            continue
        if in_code:
            line = '    ' + line
        new_lines.append(line)
    ret = '\n'.join(new_lines)

    # ~~test~~ => -test-
    ret = re.sub(ur'(?musi)~~(.*?)~~', ur'<del>\1</del>', ret)

    # convert link to another .md file
    # e.g. [See the other test document](test2.md)
    # => [See the other test document](test2)
#     link_prefix = ''
#     if request:
#         request_path = request.META['PATH_INFO']
#         if request_path[-1] == '/':
#             link_prefix = '../'
#
#     # we preserve the fragment (#...)
# ret = re.sub(ur'\]\(([^)]+).md/?(#?[^)]*)\)', ur'](%s\1\2)' %
# link_prefix, ret)

    pattern = re.compile(ur'\]\(([^)]+).md\b')
    pos = 1
    while True:
        m = pattern.search(ret, pos)
        if not m:
            break

        replacement = ''
        from digipal import utils
        end_slug = re.sub(ur'^/.*/', '', m.group(1))
        page = utils.get_cms_page_from_title(end_slug)
        # print end_slug
        if page:
            replacement = '](/%s/' % page.slug.strip('/')
            # print replacement

        if replacement:
            ret = ret[:m.start(0)] + replacement + ret[m.end(0):]

        pos = m.start(0) + len(replacement) + 1

    return ret


def get_doc_root_path(app_name):
    import os

    module = None

    import importlib
    try:
        module = importlib.import_module(app_name.lower())
    except ImportError:
        raise Http404(
            'Documentation page not found (no app with name "%s")' % app_name)

    ret = os.path.join(unicode(module.__path__[0]), 'doc')

    return ret


def get_doc_absolute_path(relative_path):
    path = relative_path.strip('/')
    parts = path.split('/')

    if len(parts) <= 1:
        raise Http404('Documentation page not found (path not specified)')

    import os

    app_name = parts[0]
    search_path = '/'.join(parts[1:])

    root_path = get_doc_root_path(app_name)

    file_path = os.path.join(root_path, unicode(search_path + '.md'))

    if not os.path.exists(file_path):
        raise Http404(
            'Documentation page not found (no doc with path "%s")' % path)

    return file_path


def test_bs4():
    s = '''
    <ul>
        <li><strong>item 1</strong>: definition</li>
        <li>item 2: definition</li>
    </ul>
    '''
    print s
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(s)

    for tag in soup.find_all('li'):
        # print tag
        tag.insert(0, '# ')
        pass

    s = unicode(soup)

    print '-' * 80

    print s

    exit()


def get_md_from_html(html_file_path):
    info = {'files': [], 'md': '', 'title': ''}
    from digipal.utils import read_file
    import os

    path = html_file_path

    html = read_file(path)

    # convert to HTML DOM
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html)

    # extract the main title
    title = 'untitled'
    if soup.head and soup.head.title:
        title = soup.head.title.string
        # special case for Confluence webpage
        title = title.replace(
            ' - DigiPal - Confluence - Digital Humanities', '').strip()

    # extract the body
    soup = soup.body
    # special case for Confluence webpage
    for e in soup.find_all('div', attrs={'class': 'wiki-content'}):
        soup = e
        break

    # remove any line breaks within the <ul>s
    for tag in soup.find_all('ul'):
        tag_markup = unicode(tag)
        tag_markup = re.sub(ur'(?musi)<p>|</p>', ur' ', tag_markup)
        tag_markup = re.sub(ur'(?musi)\s+', ur' ', tag_markup)
        tag.replace_with(BeautifulSoup(tag_markup).ul)

    # images
    # <img src="./collections_files/col-management.png">
    # ![](/digipal/static/doc/col-management.png?raw=true)
    # copy the image file
    # convert the tag
    import digipal
    import shutil
    static_path = os.path.join(digipal.__path__[0], 'static', 'doc')
    for tag in soup.find_all('img'):
        file_name = re.sub('.*?([^/?]*)($|\?|#)', ur'\1', tag['src'])
        img_src = os.path.join(os.path.dirname(path), tag['src'])
        img_dst = os.path.join(static_path, file_name)
        imgmd = '![](/static/doc/%s?raw=true)' % file_name
        tag.replace_with(imgmd)
        shutil.copyfile(img_src, img_dst)
        info['files'].append(img_dst)

    # convert <li>s
    for tag in soup.find_all('li'):
        prefix = ''
        for parent in tag.parents:
            if parent.name in ('ul', 'ol'):
                if not prefix:
                    if parent.name == 'ul':
                        prefix = '* '
                    if parent.name == 'ol':
                        prefix = '%s. ' % (
                            len([s for s in tag.previous_siblings if s.name == 'li']) + 1)
                else:
                    prefix = '#SPACE#' + prefix
        if prefix:
            tag.insert(0, prefix)

    # serialise into a string
    ret = unicode(soup)

    # print ret.encode('utf-8', 'ignore')

    # Preserve the spaces and line breaks in <pre> tags
    pattern = re.compile(ur'(?musi)<pre>(.*?)</pre>')
    pos = 1
    while True:
        m = pattern.search(ret, pos - 1)
        if not m:
            break

        replacement = '#CR#```#CR#%s#CR#```#CR#' % m.group(
            1).replace('\n', '#CR#').replace(' ', '#SPACE#')
        ret = ret[:m.start(0)] + replacement + ret[m.end(0):]
        pos = m.start(0) + len(replacement)

    # strip all unnecessary spaces
    #ret = re.sub(ur'(?musi)>\s+', ur'>', ret)
    #ret = re.sub(ur'(?musi)\s+<', ur'<', ret)
    ret = re.sub(ur'\s+', ur' ', ret)

    # convert <hx> to #
    for i in range(1, 5):
        ret = re.sub(ur'(?musi)<h%s[^>]*>(.*?)</h%s>' %
                     (i, i), ur'\n%s \1\n' % ('#' * i,), ret)

    if 1:
        # convert <p> to paragraphs
        ret = re.sub(ur'(?musi)<p>(.*?)</p>\s*', ur'\1\n\n', ret)

        # convert strike-through
        ret = re.sub(ur'(?musi)<s>(.*?)</s>', ur'~~\1~~', ret)

        # convert italics
        ret = re.sub(ur'(?musi)<em>(.*?)</em>', ur'_\1_', ret)

        # convert <strong>
        ret = re.sub(ur'(?musi)<strong>(.*?)</strong>', ur'**\1**', ret)

        # convert <a href="">
        #ret = re.sub(ur'(?musi)<a>(.*?)</a>', ur'[]()', ret)
        pattern = re.compile(ur'(?musi)<a.*?href="([^"]*)".*?>(.*?)</a>')
        pos = 1
        while True:
            m = pattern.search(ret, pos - 1)
            if not m:
                break

            replacement = ''
            if m.group(2):
                # if this is a link to a confluence page, convert it to a local
                # link
                href = get_local_doc_url(m.group(1))
                replacement = '[%s](%s)' % (m.group(2), href)

            ret = ret[:m.start(0)] + replacement + ret[m.end(0):]
            pos = m.start(0) + len(replacement)

        # convert <blockquote>
        #ret = re.sub(ur'(?musi)<blockquote>\s*(.*?)\s*</blockquote>', ur'\n> \1\n', ret)
        pattern = re.compile(ur'(?musi)<blockquote>\s*(.*?)\s*</blockquote>')
        pos = 1
        while True:
            m = pattern.search(ret, pos - 1)
            if not m:
                break

            replacement = '%s\n\n' % re.sub(
                ur'(?musi)^\s*', ur'> ', m.group(1))
            ret = ret[:m.start(0)] + replacement + ret[m.end(0):]
            pos = m.start(0) + len(replacement)

        # convert <pre>
        #ret = re.sub(ur'(?musi)<pre>\s*(.*?)\s*</pre>', ur'\n```\n\1\n```\n', ret)

        # add line break before bullet points
        ret = re.sub(ur'\s*<li>', ur'\n', ret)
        # add line break after block of bullet points
        # (only if not nested into another block)
        ret = re.sub(ur'\s*</ul>(?!\s*</li>)', ur'\n\n', ret)

        ret = re.sub(ur'#SPACE#', ur' ', ret)
        ret = re.sub(ur'#CR#', ur'\n', ret)

        # remove remaining tags
        ret = re.sub(ur'<[^>]*>', ur'', ret)

        ret = u'# %s\n%s' % (title, ret)

    info['md'] = ret
    info['title'] = title

    return info


def get_local_doc_url(href):
    '''Returns the url of a local MD with the same name as in href.
        Returns href if not found.
    '''
    import digipal
    import os
    from django.utils.text import slugify

    ret = href
    if 'confluence.dighum' in href.lower():
        import urllib
        file_name = urllib.unquote_plus(href)
        file_name = re.sub(ur'[#?].*$', '', file_name).strip('/')
        file_name = re.sub(ur'^.*/', '', file_name).lower()
        file_name = slugify(unicode(file_name))
        start_path = os.path.abspath(os.path.join(digipal.__path__[0], 'doc'))
        # print start_path, file_name
        for root, dirs, files in os.walk(start_path):
            for file in files:
                # print file
                if slugify(unicode(re.sub(ur'.md$', '', file))) == file_name:
                    ret = os.path.join(root, file).replace('\\', '/')
                    ret = '/digipal/doc/%s' % ret[len(start_path):].strip('/')
                    break
    return ret
