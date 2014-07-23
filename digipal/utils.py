from django.utils.html import conditional_escape, escape
import re
#_nsre = re.compile(ur'(?iu)([0-9]+|(?:\b[mdclxvi]+\b))')
_nsre_romans = re.compile(ur'(?iu)(?:\.\s*)([ivxlcdm]+\b)')
_nsre = re.compile(ur'(?iu)([0-9]+)')

def sorted_natural(l, roman_numbers=False):
    '''Sorts l and returns it. Natural sorting is applied.'''
    return sorted(l, key=lambda e: natural_sort_key(e, roman_numbers))

def natural_sort_key(s, roman_numbers=False):
    '''
        Returns a list of tokens from a string.
        This list of tokens can be feed into a sorting function to come up with a natural sorting.
        Natural sorting is number-aware: e.g. 'word 2' < 'word 100'.
        
        If roman_numbers is True, roman numbers will be converted to ints.
        Note that there is no fool-proof was to detect roman numerals
        e.g. MS A; MS B; MS C. In this case C is a letter and not 500. 
            MS A.ix In this case ix is a number
        So as a heuristic we only consider roman number if preceded by '.'  
    '''
    
    if roman_numbers:
        while True:
            m = _nsre_romans.search(s)
            if m is None: break
            # convert the roman number into base 10 number
            number = get_int_from_roman_number(m.group(1))
            if number:
                # substition
                s = s[:m.start(1)] + str(number) + s[m.end(1):]
                
    return [int(text) if text.isdigit() else text.lower() for text in re.split(_nsre, s)]

def plural(value, count=2):
    '''
    Usage: 
            {{ var|plural }}
            {{ var|plural:count }}
            
            If [count] > 1 or [count] is not specified, the filter returns the plural form of [var].
            Plural form is generated by sequentially applying the following rules:
                * convert 'y' at the end into 'ie'               (contry -> contrie)
                * convert 'ss' at the end into 'e'               (witness -> witnesse)
                * add a 's' at the end is none already there     (nation -> nations)
    '''
    
    if count is not None:
        try:
            count = int(float(count))
        except ValueError:
            pass
        except TypeError:
            pass
        try:
            count = len(count)
        except TypeError:
            pass
    
    words = value.split(' ')
    if len(words) > 1:
        # We got a phrase. Pluralise each word separately.
        ret = ' '.join([plural(word, count) for word in words])
    else:
        ret = value
        if ret in ['of']: return ret
        if count != 1:
            if ret in ['a', 'an']: return ''
            if ret[-1:] == 'y': 
                ret = ret[:-1] + 'ie'
            if ret[-2:] == 'ss': 
                ret = ret + 'e'
            if not ret[-1:] == 's':
                ret = ret + 's'
    return ret

def update_query_string(url, updates, url_wins=False):
    '''
        Replace parameter values in the query string of the given URL.
        If url_wins is True, the query string values in [url] will always supersede the values from [updates].
        
        E.g.
        
        >> _update_query_string('http://www.mysite.com/about?category=staff&country=UK', 'who=bill&country=US')
        'http://www.mysite.com/about?category=staff&who=bill&country=US'

        >> _update_query_string('http://www.mysite.com/about?category=staff&country=UK', {'who': ['bill'], 'country': ['US']})
        'http://www.mysite.com/about?category=staff&who=bill&country=US'
        
    '''
    show = url == '?page=2&amp;terms=%C3%86thelstan&amp;repository=&amp;ordering=&amp;years=&amp;place=&amp;basic_search_type=hands&amp;date=&amp;scribes=&amp;result_type=' and updates == 'result_type=manuscripts'
    
    ret = url.strip()
    if ret and ret[0] == '#': return ret

    from urlparse import urlparse, urlunparse, parse_qs
    
    # Convert string format into a dictionary
    if isinstance(updates, basestring):
        updates_dict = parse_qs(updates, True)
    else:
        from copy import deepcopy
        updates_dict = deepcopy(updates)
        
    # Merge the two query strings (url and updates)
    # note that urlparse preserves the url encoding (%, &amp;)
    parts = [p for p in urlparse(url)]
    # note that parse_qs converts u'terms=%C3%86thelstan' into u'\xc3\x86thelstan'
    # See http://stackoverflow.com/questions/16614695/python-urlparse-parse-qs-unicode-url
    # for the reaon behind the call to encode('ASCII') 
    query_dict = parse_qs(parts[4].encode('ASCII'))
    if url_wins:
        updates_dict.update(query_dict)
        query_dict = updates_dict
    else:
        query_dict.update(updates_dict)
    
    # Now query_dict is our updated query string as a dictionary 
    # Parse and unparse it again to remove the empty values
    query_dict = parse_qs(urlencode(query_dict, True))
    
    # Convert back into a string    
    parts[4] = urlencode(query_dict, True)
    
    # Place the query string back into the URL
    ret = urlunparse(parts)
    
    ret = escape(ret)
    
    if len(ret) == 0:
        ret = '?'
    
    return ret

def urlencode(dict, doseq=0):
    ''' This is a unicode-compatible wrapper around urllib.urlencode()
        See http://stackoverflow.com/questions/3121186/error-with-urlencode-in-python
    '''
    import urllib
    d = {}
    for k,v in dict.iteritems():
        d[k] = []
        for v2 in dict[k]:
            if isinstance(v2, unicode):
                v2 = v2.encode('utf=8')
            d[k].append(v2)
    ret = urllib.urlencode(d, doseq)
    return ret

def get_json_response(data):
    '''Returns a HttpResponse with the given data variable encoded as json'''
    import json
    from django.http import HttpResponse 
    return HttpResponse(json.dumps(data), mimetype="application/json")

def get_tokens_from_phrase(phrase, lowercase=False):
    ''' Returns a list of tokens from a query phrase.
    
        Discard stop words (NOT, OR, AND)
        Detect quoted pieces ("two glosses")
        Remove field scopes. E.g. repository:London => London
    
        e.g. "ab cd" ef-yo NOT (gh)
        => ['ab cd', 'ef', 'yo', 'gh']
    '''
    ret = []
    
    if lowercase:
        phrase = phrase.lower()
        
    # Remove field scopes. E.g. repository:London => London
    phrase = re.sub(ur'(?u)\w+:', ur'', phrase)
    
    phrase = phrase.strip()
    
    # extract the quoted pieces
    for part in re.findall(ur'"([^"]+)"', phrase):
        ret.append(part)
    
    # remove them from the phrase
    phrase = re.sub(ur'"[^"]+"', '', phrase)
    
    # JIRA 358: search for 8558-8563 => no highlight if we don't remove non-characters before tokenising
    # * is for searches like 'digi*'
    phrase = re.sub(ur'(?u)[^\w*]', ' ', phrase)
    
    # add the remaining tokens
    if phrase:
        ret.extend([t for t in re.split(ur'\s+', phrase.lower().strip()) if t.lower() not in ['and', 'or', 'not']])
    
    return ret

def get_regexp_from_terms(terms, as_list=False):
    ''' input: list of query terms, e.g. ['ab', cd ef', 'gh']
        output: a regexp, e.g. '\bab\b|\bcd\b...
                if as_list is True: ['\bab\b', '\bcd\b']
    '''
    ret = []
    if terms:
        # create a regexp
        for t in terms:
            t = re.escape(t)

            if t[-1] == u's':
                t += u'?'
            else:
                t += u's?'
#             if len(t) > 1:
#                 t += ur'?'
#             t = ur'\b%ss?\b' % t
            t = ur'\b%s\b' % t
            
            # convert all \* into \W*
            # * is for searches like 'digi*'
            t = t.replace(ur'\*', ur'\w*')
            
            ret.append(t)

    if not as_list:
        ret = ur'|'.join(ret)
    
    return ret

def find_first(pattern, text, default=''):
    ret = default
    matches = re.findall(pattern, text)
    if matches: ret = matches[0]
    return ret

def get_int_from_roman_number(input):
    """
    From 
    http://code.activestate.com/recipes/81611-roman-numerals/
    
    Convert a roman numeral to an integer.
    
    >>> r = range(1, 4000)
    >>> nums = [int_to_roman(i) for i in r]
    >>> ints = [roman_to_int(n) for n in nums]
    >>> print r == ints
    1
    
    >>> roman_to_int('VVVIV')
    Traceback (most recent call last):
    ...
    ValueError: input is not a valid roman numeral: VVVIV
    >>> roman_to_int(1)
    Traceback (most recent call last):
    ...
    TypeError: expected string, got <type 'int'>
    >>> roman_to_int('a')
    Traceback (most recent call last):
    ...
    ValueError: input is not a valid roman numeral: A
    >>> roman_to_int('IL')
    Traceback (most recent call last):
    ...
    ValueError: input is not a valid roman numeral: IL
    """
    if not isinstance(input, basestring):
        return None
    input = input.upper()
    nums = ['M', 'D', 'C', 'L', 'X', 'V', 'I']
    ints = [1000, 500, 100, 50,  10,  5,   1]
    places = []
    for c in input:
        if not c in nums:
            #raise ValueError, "input is not a valid roman numeral: %s" % input
            return None
    for i in range(len(input)):
        c = input[i]
        value = ints[nums.index(c)]
        # If the next place holds a larger number, this value is negative.
        try:
            nextvalue = ints[nums.index(input[i +1])]
            if nextvalue > value:
                value *= -1
        except IndexError:
            # there is no next place.
            pass
        places.append(value)
    sum = 0
    for n in places: sum += n
    return sum

def get_plain_text_from_html(html):
    '''Returns the unencoded text from a HTML fragment. No tags, no entities, just plain utf-8 text.'''
    ret = html
    if ret:
        from django.utils.html import strip_tags
        import HTMLParser
        html_parser = HTMLParser.HTMLParser()
        ret = strip_tags(html_parser.unescape(ret))        
    else:
        ret = u''
    return ret

def set_left_joins_in_queryset(qs):
    qs.query.promote_joins(qs.query.alias_map.keys(), True)
    #pass
#     for alias in qs.query.alias_map:
#         qs.query.promote_alias(alias, True)

def get_str_from_queryset(queryset):
    ret = unicode(queryset.query)
    ret = re.sub(ur'(INNER|FROM|AND|OR|WHERE|GROUP|ORDER|LEFT|RIGHT|HAVING)', ur'\n\1', ret)
    ret = re.sub(ur'(INNER|AND|OR|LEFT|RIGHT)', ur'\t\1', ret)
    return ret.encode('ascii', 'ignore')

def remove_accents(input_str):
    '''Returns the input string without accented character. 
        This is useful for accent-insensitive matching (e.g. autocomplete).
        >> remove_accents(u'c\u0327   \u00c7')
        u'c   c'
    '''
    import unicodedata
    # use 'NFD' instead of 'NFKD'
    # Otherwise the ellipsis \u2026 is tranformed into '...' and the output string will have a different length
    #return remove_combining_marks(unicodedata.normalize('NFKD', unicode(input_str)))
    return remove_combining_marks(unicodedata.normalize('NFD', unicode(input_str)))

def remove_combining_marks(input_str):
    '''Returns the input unicode string without the combining marks found as 'individual character'
        >> remove_combining_marks(u'c\u0327   \u00c7')
        u'c   \u00c7'
    '''
    import unicodedata
    return u"".join([c for c in unicode(input_str) if not unicodedata.combining(c)])

def write_file(file_path, content):
    f = open(file_path, 'w')
    f.write(content.encode('utf8'))
    f.close()

def get_bool_from_string(string):
    ret = False
    if string in ['1', 'True', 'true']:
        ret = True
    return ret

def get_one2one_object(model, field_name):
    '''Returns model.field_name where field_name is a one2one relation.
        This function till return None if there no related object.
    '''
    ret = None
    
    if model:
        from django.core.exceptions import ObjectDoesNotExist
        try:
            getattr(model, field_name)
        except ObjectDoesNotExist, e:
            pass
    
    return ret

def get_xslt_transform(source, template, error=None):
    ret = source
    import lxml.etree as ET
    from io import BytesIO
    
    d = BytesIO(source.encode('utf-8'))
    dom = ET.parse(d)
    d = BytesIO(template.encode('utf-8'))
    xslt = ET.parse(d)
    transform = ET.XSLT(xslt)
    newdom = transform(dom)
    #print(ET.tostring(newdom, pretty_print=True))
    ret = newdom
            
    return ret

def recreate_whoosh_index(path, index_name, schema):
    import os.path
    from whoosh.index import create_in
    if not os.path.exists(path):
        os.mkdir(path)
    path = os.path.join(path, index_name)
    if os.path.exists(path):
        import shutil
        shutil.rmtree(path)
    os.mkdir(path)
    print '\tCreated index under "%s"' % path
    # TODO: check if this REcreate the existing index
    index = create_in(path, schema)
    
    return index

def get_int(obj, default=0):
    '''Returns an int from an obj (e.g. string)
        If the conversion fails, returns default.
    '''
    try:
        ret = int(obj)
    except:
        ret = default
    return ret
