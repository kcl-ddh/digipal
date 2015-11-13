# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from os.path import isdir
import os
import re
from optparse import make_option

# pm dpxml convert exon\source\rekeyed\converted\EXON-1-493-part1.xml exon\source\rekeyed\conversion\xml2word.xslt > exon\source\rekeyed\word\EXON-word.html
# pm extxt wordpre exon\source\rekeyed\word\EXON-word.html exon\source\rekeyed\word\EXON-word2.html
# pandoc "exon\source\rekeyed\word\EXON-word2.html" -o "exon\source\rekeyed\word\EXON-word.docx"

import unicodedata
def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

class Command(BaseCommand):
    help = """
Text conversion tool
    
Commands:
    wordpre PATH_TO_XHTML OUTPUT_PATH
        Preprocess the MS Word document

    pattern PATH_TO_XHTML PATTERN
        Test a regexp pattern on a XHTML file

    upload PATH_TO_XHTML CONTENTID
        Import XHTML file

"""
    
    args = 'locus|email'
    option_list = BaseCommand.option_list + (
        make_option('--db',
            action='store',
            dest='db',
            default='default',
            help='Name of the target database configuration (\'default\' if unspecified)'),
        make_option('--dry-run',
            action='store_true',
            dest='dry-run',
            default=False,
            help='Dry run, don\'t change any data.'),
        )

    def handle(self, *args, **options):
        
        self.log_level = 3
        
        self.options = options
        
        if len(args) < 1:
            print self.help
            exit()
        
        command = args[0]
        self.cargs = args[1:]
        
        known_command = False

        if command == 'wordpre':
            known_command = True
            self.word_preprocess()

        if command == 'pattern':
            known_command = True
            self.pattern()
        
        if command == 'upload':
            known_command = True
            self.upload()
        
        if known_command:
            print 'done'
            pass
        else:
            print self.help

    def get_unique_matches(self, pattern, content):
        ret = re.findall(pattern, content)
        
        import json

        print repr(pattern)

        matches = {}
        for match in ret:
            key = json.dumps(match)
            matches[key] = matches.get(key, 0) + 1
            
        for key, freq in sorted([(key, freq) for key, freq in matches.iteritems()], key=lambda item: item[1]):
            print '%3d %s' % (freq, key)
        
        print len(ret)
        
        return ret

    def pattern(self):
        input_path = self.cargs[0]
        pattern = self.cargs[1]
        
        from digipal.utils import read_file
        
        content = read_file(input_path)

        print
        self.get_unique_matches(pattern, content)
        
        print

    def upload(self):
        input_path = self.cargs[0]
        recordid = self.cargs[1]
        
        import regex
        from digipal.utils import re_sub_fct
        from digipal.utils import read_file
        content = read_file(input_path)
        
        # extract body
        l0 = len(content)
        content = regex.sub(ur'(?musi).*<body*?>(.*)</body>.*', ur'<p>\1</p>', content)
        if len(content) == l0:
            print 'ERROR: could not find <body> element'
            return

        # unescape XML tags coming from MS Word
        # E.g. &lt;margin&gt;Д‘ mМѓ&lt;/margin&gt;
        content = regex.sub(ur'(?musi)&lt;(/?[a-z]+)&gt;', ur'<\1>', content)

        # convert &amp; to #AMP#
        content = content.replace('&amp;', '#AMP#')
        
        # line breaks from MS
        content = regex.sub(ur'(?musi)\|', ur'<span data-dpt="lb" data-dpt-src="ms"></span>', content)

        # line breaks from editor
        content = regex.sub(ur'(?musi)<br/>', ur'<span data-dpt="lb" data-dpt-src="prj"></span>', content)

        # <st>p</st> => ṕ
        content = regex.sub(ur'(?musi)<st>\s*p\s*</st>', ur'ṕ', content)
        # <st>q</st> => ƣ
        content = regex.sub(ur'(?musi)<st>\s*q\s*</st>', ur'ƣ', content)

        # <del>de his</del> => 
        content = regex.sub(ur'(?musi)<del>(.*?)</del>', ur'', content)

        # Folio number
        # [fol. 1. b.] or [fol. 1.]
        # TODO: check for false pos. or make the rule more strict
        #content = re.sub(ur'(?musi)\[fol.\s(\d+)\.(\s*(b?)\.?)\]', ur'</p><span data-dpt="location" data-dpt-loctype="locus">\1\3</span><p>', content)
        self.sides = {'': 'r', 'b': 'v', 'a': 'r'}
        def get_side(m):
            side = self.sides.get(m.group(3), m.group(3))
            ret = ur'</p><span data-dpt="location" data-dpt-loctype="locus">%s%s</span><p>' % (m.group(1), side)
            return ret
        content = re_sub_fct(content, ur'(?musi)\[fol.\s(\d+)\.(\s*(b?)\.?)\]', get_side, regex)

        # Entry number
        # [1a3]
        # TODO: check for false pos. or make the rule more strict
        content = regex.sub(ur'(?musi)(§?)\[(\d+(a|b)\d+)]', ur'</p><p>\1<span data-dpt="location" data-dpt-loctype="entry">\2</span>', content)

        # <margin></margin>
        content = content.replace('<margin>', '<span data-dpt="note" data-dpt-place="margin">')
        content = content.replace('</margin>', '</span>')
         
        # to check which entities are left
        ##ocs = set(regex.findall(ur'(?musi)(&[#\w]+;)', content))

        self.c = 0

        def markup_expansions(match):
            m = match.group(0)
            ret = m

            #if '[' not in m: return m
            
            # don't convert if starts with digit as it's most likely a folio or entry number
            if m[0] <= '9' and m[0] >= '0':
                return m
            
            self.c += 1
            #if self.c > 100: exit()
            
            # ũ[ir]g̃[a]
            # abbr =
            
            # ABBR
            abbr = regex.sub(ur'\[.*?\]', ur'', m)
            
            # o<sup>o</sup> -> <sup>o</sup>
            abbr = regex.sub(ur'(\w)(<sup>\1</sup>|<sub>\1</sub>)', ur'\2', abbr)
            
            # EXP
            exp = regex.sub(ur'\[(.*?)\]', ur'<i>\1</i>', m)
            # b
            exp = regex.sub(ur'\u1d6c', ur'b', exp)
            # l/ -> l
            exp = regex.sub(ur'\u0142', ur'l', exp)
            # d- -> d
            exp = regex.sub(ur'\u0111', ur'd', exp)
            # h
            exp = regex.sub(ur'\u0127', ur'h', exp)
            # e.g. hid4as
            exp = regex.sub(ur'\d', ur'', exp)

            ##exp = regex.sub(ur'ṕ', ur'p', exp)
            exp = regex.sub(ur'ƣ', ur'q', exp)
            
            
            # Remove abbreviation signs
            # ! we must make sure that the content no longer contains entities!
            # E.g. &amp; => &
            # ;
            exp = regex.sub(ur';', ur'', exp)
            # :
            exp = regex.sub(ur':', ur'', exp)
            # ÷
            exp = regex.sub(ur'÷', ur'', exp)
            # ʇ
            exp = regex.sub(ur'ʇ', ur'', exp)
            # e.g. st~
            exp = remove_accents(exp)
            
            # remove sub/sup from the expanded form as it usually contains abbreviation mark
            # Exception: hiđ4[ae]ϛ {ϛ 7 dim̃[idia] uirga.}
            # here we keep ϛ because it is used as an insertion sign
            ###exp = regex.sub(ur'<su(p|b)>.*?</su(p|b)>', ur'', exp)
            # general removal
            exp = regex.sub(ur'<su(p|b)>.*?</su(p|b)>', ur'', exp)
            
            if abbr != exp and exp:
#                 if len(abbr) > len(exp):
#                     # potentially spurious expansions
#                     print repr(abbr), repr(exp)
                ret = ur'<span data-dpt="abbr">%s</span><span data-dpt="exp">%s</span>' % (abbr, exp)
            
            ##print repr(m), repr(ret)
            
            return ret
        
        content = re_sub_fct(content, ur'(?musi)(:|;|÷|\w|(<sup>.*?</sup>)|(<sub>.*?</sub>)|\[|\])+', markup_expansions, regex)

        # Bal〈dwini〉 =>
        content = regex.sub(ur'(?musi)(〈[^〈〉]{1,30}〉)', ur'<span data-dpt="exp">\1</span>', content)
        
        # sup
        content = regex.sub(ur'(?musi)<sup>', ur'<span data-dpt="hi" data-dpt-rend="sup">', content)

        # sub
        content = regex.sub(ur'(?musi)<sub>', ur'<span data-dpt="hi" data-dpt-rend="sub">', content)
        content = regex.sub(ur'(?musi)</sup>|</sub>', ur'</span>', content)

        # convert #AMP# to &amp;
        content = content.replace('#AMP#', '&amp;')

        # import
        from digipal_text.models import TextContentXML
        text_content_xml = TextContentXML.objects.get(id=recordid)
        text_content_xml.content = content
        
        #print repr(content)
        
        text_content_xml.save()

    def word_preprocess(self):
        input_path = self.cargs[0]
        output_path = self.cargs[1]
        
        from digipal.utils import write_file, read_file
        
        # regex will consider t̃ as \w, re as \W
        import regex as re
        
        content = read_file(input_path)
        
        # expansions
        # m_0 -> m[od]o_0
        #self.get_unique_matches(pattern, content)
        pattern = ur'(?mus)([^\w<>\[\]])(m<sup>0</sup>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'\1m[od]o<sup>o</sup>\3', content)

        pattern = ur'(?mus)([^\w<>\[\]])(uocat<sup>r</sup>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'\1uocat[u]r<sup>r</sup>\3', content)

        pattern = ur'(?mus)([^\w<>\[\]])(q<sup>1</sup>)([^\w<>\[&])'
        content = re.sub(pattern, ur'\1q[u]i<sup>i</sup>\3', content)
        
        # These involve the superscript 9s and 4s, with a few 2s caught up with
        # the fours and one recurrent subscript 4. 4 seems to be the commonest
        # number, and my suggested list will allow us to make inroads
        
        # -e<sub>4</sub> -> e cauda
        # ! rekeyers have somtimes used <sub> BEFORE the e (28 vs 3630)
        pattern = ur'(?mus)(e<sub>4</sub>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'ę\2', content)

        # he4c -> hęc
        pattern = ur'(?mus)([^\w<>\[\]/;](h|H))(e<sub>4</sub>)(c[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1ę\4', content)

        # e<sub>9</sub> ->
        # 6599 occurrences
        pattern = ur'(?mus)([\w<>\[\]/;]+)(<sup>9</sup>)([^\w<>\[\]&])'
        content = re.sub(pattern, ur'\1\2[us]\3', content)
        
        # most frequent 9 within word: nem9culi (199 out of 237 occurences)
        pattern = ur'(?mus)([^\w<>\[\]/;]nem)(<sup>9</sup>)((culi|cłi)[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[us]\3', content)

        # 2: stands for different symbols: u (-> ar / ra); a -> ua

        # q2drag4 -> q[ua]2drag4[enarias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>drag<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>drag<sup>4</sup>[enarias]\3', content)
        # q2drag̃ -> q[ua]2drag[enarias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>)(drag̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>\3[enarias]\4', content)
        # q2dragenar~ -> q[ua]2dragenar~[ias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>)(dragenar̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>\3[ias]\4', content)
        # q2dragenarias -> q[ua]2dragenarias
        pattern = ur'(?mus)([^\w<>\[\]/;])(q<sup>2</sup>)(dragenarias[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1q[u]a<sup>a</sup>\3', content)
        
        # q2ndo -> q[u]a2do
        pattern = ur'(?mus)([^\w<>\[\]/;]q)(<sup>2</sup>)(ndo[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]a<sup>a</sup>\3', content)

        # cap2s -> cap2[ra]s
        pattern = ur'(?mus)([^\w<>\[\]/;]cap)(<sup>2</sup>)(s[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)
        # cap2 -> cap[ra]a !?
        pattern = ur'(?mus)([^\w<>\[\]/;]cap)(<sup>2</sup>)([^\w<>\[\]/&])'
        #content = re.sub(pattern, ur'\1[r]a<sup>a</sup>\3', content)
        content = re.sub(pattern, ur'\1<sup>2</sup>[ra]\3', content)

        # p2ti -> p2[ra]ti
        pattern = ur'(?mus)([^\w<>\[\]/;]p)(<sup>2</sup>)(ti[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)

        # ext2 = ext[ra]
        pattern = ur'(?mus)([^\w<>\[\]/;]ext)(<sup>2</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)

        # eq2s = eq[u]a2s
        pattern = ur'(?mus)([^\w<>\[\]/;]eq)(<sup>2</sup>)(s[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]a<sup>a</sup>\3', content)

        # q2 = q[u]a2
        pattern = ur'(?mus)([^\w<>\[\]/;]q)(<sup>2</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]a<sup>a</sup>\3', content)

        # sup2dicta =
        pattern = ur'(?mus)([^\w<>\[\]/;]sup)(<sup>2</sup>)(dict(ã|a)s?[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ra]\3', content)

        # s;
        pattern = ur'(?mus)([^\w<>\[\]/;]s;)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[ed]\2', content)

        # 4: stands for bolt which is a very generic abbreviation

        # porc4 -> porc4[os]
        pattern = ur'(?mus)([^\w<>\[\]/;]porc)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[os]\3', content)

        # recep4 -> recep4[it]
        pattern = ur'(?mus)([^\w<>\[\]/;]rece)(p̃|p<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[it]\3', content)

        # ag4 -> ag[ros]
        pattern = ur'(?mus)([^\w<>\[\]/;]a)(g̃|g<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ros]\3', content)

        # hid4 -> hid[e<sup>e</sup>]
        pattern = ur'(?mus)([^\w<>\[\]/;]hid)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ę]\3', content)
        
        # den4 -> den4[arios]
        pattern = ur'(?mus)([^\w<>\[\]/;]den)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[arios]\3', content)

        # dim4 -> den4[idiam]
        pattern = ur'(?mus)([^\w<>\[\]/;]di)(m̃|m<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[idiam]\3', content)
        
        # inlong4 -> inlong4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]inlong)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[itudine]\3', content)

        # long4 -> long4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]long)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[itudine]\3', content)

        # longitud4 -> longitud4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]longitud)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ine]\3', content)

        # lat4 -> lat4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]lat)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[itudine]\3', content)

        # latit4 -> lat4[itudine]
        pattern = ur'(?mus)([^\w<>\[\]/;]latit)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[udine]\3', content)

        # nemor4 -> nemor4[is]
        pattern = ur'(?mus)([^\w<>\[\]/;]nemor)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[is]\3', content)

        # quadrag4 -> quadrag4[enarias]
        pattern = ur'(?mus)([^\w<>\[\]/;])(quadrag<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1quadrag<sup>4</sup>[enarias]\3', content)

        # seru4 -> seru4[um]
        pattern = ur'(?mus)([^\w<>\[\]/;]seru)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[um]\3', content)

        # ten -> ten4[uit]
        pattern = ur'(?mus)([^\w<>\[\]/;]ten)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[uit]\3', content)

        # carr4 -> carr4[ucas]
        pattern = ur'(?mus)([^\w<>\[\]/;]carr)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ucas]\3', content)
        # car4r -> carr4[ucas] (correct error from rekeyers)
        pattern = ur'(?mus)([^\w<>\[\]/;]car)(<sup>4</sup>)r([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1r\2[ucas]\3', content)
        # carr~ -> carr~[ucas]
        pattern = ur'(?mus)([^\w<>\[\]/;])(carr̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ucas]\3', content)

        # bord4 -> bord4[arios]
        pattern = ur'(?mus)([^\w<>\[\]/;]bord)(<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[arios]\3', content)

        # mans4 -> mans4[arios]
        pattern = ur'(?mus)([^\w<>\[\]/;]man)(s̃|s<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ionem]\3', content)

        # 9 1
        
        # un9qisq: / un9q1sq -> un9[us]q[u]1isq:[ue]
        pattern = ur'(?mus)([^\w<>\[\]/;])(un<sup>9</sup>)(q<sup>(i|1)</sup>)(sq:?)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[us]q[u]<sup>i</sup>i\5[ue]\6', content)

        # d-
        # d- -> denarios
        pattern = ur'(?mus)([^\w<>\[\]/;])(đ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[enarios]\3', content)

        # redđ -> redd[idit]
        pattern = ur'(?mus)([^\w<>\[\]/;]red)(đ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[idit]\3', content)

        # hiđ -> hiđ[as]
        pattern = ur'(?mus)([^\w<>\[\]/;]hi)(đ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[as]\3', content)

        # hunđ -> hunđ[reto]
        pattern = ur'(?musi)([^\w<>\[\]/;]hun)(đ|d<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[reto]\3', content)
        
        # d: -> q:[ui]
        pattern = ur'(?mus)([^\w<>\[\]/;]q)(:)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ui]\3', content)

        # ĩ -> ĩ[n]
        pattern = ur'(?mus)([^\w<>\[\]/;]ĩ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[n]\2', content)

        # st~
        # st~ -> s[un]t~
        pattern = ur'(?mus)([^\w<>\[\]/;]s)(t̃[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[un]\2', content)

        # rex E -> rex Edwardus
        pattern = ur'(?musi)([^\w<>\[\]/;])(rex\.? E)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[dwardus]\3', content)

        # regis E -> regis Edwardi
        pattern = ur'(?musi)([^\w<>\[\]/;])(regis\.? e)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[dwardi]\3', content)

        # E regis ->
        pattern = ur'(?musi)([^\w<>\[\]/;]e)\.?( regis[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[dwardi]\2', content)

        # rex G
        pattern = ur'(?musi)([^\w<>\[\]/;])(rex\.? G)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[ildum]\3', content)

        # viłł[anos]
        pattern = ur'(?musi)([^\w<>\[\]/;])(viłł|uiłł)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[anos]\3', content)
        
        # ũg̃ -> u[ir]g[as]
        pattern = ur'(?musi)([^\w<>\[\]/;]ũ)(g̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[ir]\2[as]\3', content)

        # uirg̃ -> u[ir]g[as]
        pattern = ur'(?musi)([^\w<>\[\]/;]uirg̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[as]\2', content)

        # ht̃ -> h[abe]t̃
        pattern = ur'(?musi)([^\w<>\[\]/;]h)(t̃|t<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[abe]\2\3', content)

        # hñt -> h[abe]ñt
        pattern = ur'(?musi)([^\w<>\[\]/;]h)(ñt|nt<sup>4</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[abe]\2\3', content)

        # borđ -> borđ[arios]
        pattern = ur'(?musi)([^\w<>\[\]/;]borđ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[arios]\2', content)

        # qñ -> q[ua]n[do]
        pattern = ur'(?musi)([^\w<>\[\]/;]q)(ñ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[ua]\2[do]\3', content)

        # dnĩo -> d[omi]nĩo
        pattern = ur'(?musi)([^\w<>\[\]/;]d)(nĩo[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[omi]\2', content)

        # ẽ -> ẽ[st]
        pattern = ur'(?musi)([^\w<>\[\]/;]ẽ)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[st]\2', content)
        
        # ep̃s ->
        pattern = ur'(?musi)([^\w<>\[\]/;])(ep̃|ep<sup>4</sup>)(s[^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1\2[iscopu]\3', content)
        
        # porc̃
        pattern = ur'(?musi)([^\w<>\[\]/;]porc̃)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[os]\2', content)

        # ep̃s ->
#         pattern = ur'(?musi)([^\w<>\[\]/;])(animł|aĩalia|ãalia)([^\w<>\[\]/&])'
#         content = re.sub(pattern, ur'\1\2[iscopu]\3', content)

        # r

        # nescit^r -> nescitur^r
        pattern = ur'(?mus)([^\w<>\[\]/;]nescit)(<sup>r</sup>)([^\w<>\[\]/&])'
        content = re.sub(pattern, ur'\1[u]r\2\3', content)

        # numbers
        pattern = ur'(?mus)\.?(\s*)(\b[IVXl]+)\.([^\w<>\[\]])'
        content = re.sub(pattern, lambda pat: ur'%s.%s.%s' % (pat.group(1), pat.group(2).lower(), pat.group(3)), content)

        # write result
        write_file(output_path, content)
        
