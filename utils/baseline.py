from sklearn.linear_model import LogisticRegression
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from nltk import word_tokenize, pos_tag, download
from nltk.data import load
from nltk.corpus import wordnet



class Baseline(object):

    def __init__(self, language):
        self.language = language
        # from 'Multilingual and Cross-Lingual Complex Word Identification' (Yimam et. al, 2017)
        if language == 'english':
            self.avg_word_length = 5.3
        else:  # spanish
            self.avg_word_length = 6.2

#        self.model = RandomForestClassifier(n_estimators = 20)
        self.model = LogisticRegression()
        
        # This one didn't seem to do anything.
        l_rarity = defaultdict(float, 
                               (
                                 ('z' , 0.074 ),
                                 ('q' , 0.095 ),
                                 ('x' , 0.150 ),
                                 ('j' , 0.153 ), 
                                 ('k' , 0.772 ), 
                                 ('v' , 0.978 ), 
                                 ('b' , 1.492 ), 
                                 ('p' , 1.929 ), 
                                 ('y' , 1.974 ), 
                                 ('g' , 2.015 ), 
                                 ('f' , 2.228 ), 
                                 ('w' , 2.360 ), 
                                 ('m' , 2.406 ), 
                                 ('u' , 2.758 ), 
                                 ('c' , 2.782 ), 
                                 ('l' , 4.025 ), 
                                 ('d' , 4.253 ), 
                                 ('r' , 5.987 ), 
                                 ('h' , 6.094 ), 
                                 ('s' , 6.327 ), 
                                 ('n' , 6.749 ), 
                                 ('i' , 6.966 ), 
                                 ('o' , 7.507 ), 
                                 ('a' , 8.167 ), 
                                 ('t' , 9.056 ), 
                                 ('e' , 12.702),
                                )
                               )
        for k in l_rarity:
            l_rarity[k] = 1/(l_rarity[k]**2)
            
        self.letter_rarity = l_rarity
        
        sp_consonants = set(("v", "ll", "h", "j", "r", "rr", "z", "ñ", "x"))
        
#        Vowel diagraphs: ou, ow, eigh, au, aw, oo
#        Consonant digraphs: sh, th, wh, ph
#        Consonant blends: sl, sm, sts, scr, spr, str
#        Initial sounds: kn, qu, wr, sk
#        Final sounds: ck, ng, gh
#        Endings: -ed (pronounced /d/ or /t/ or /ded/ or /ted/)
#        Endings: -s (pronounced /s/ or /z/ or /ez/ or /es/)
#        Endings without a vowel: -ps, -ts
#        Suffixes/prefixes: un-, over-, under-, -ly, -ness, -ful, -est
#        http://www.colorincolorado.org/article/capitalizing-similarities-and-differences-between-spanish-and-english
        
        eng_v_diagraphs = set(("ou", "ow", "eigh", "au", "aw", "oo"))
        eng_c_diagraphs = set(("sh", "th", "wh", "ph"))
        eng_c_blends = set(("sl", "sm", "sts", "scr", "spr", "str"))
        
        self.inside_check = list(sp_consonants | eng_v_diagraphs | eng_c_diagraphs | eng_c_blends)
        
        eng_init_sounds = set(("kn", "qu", "wr", "sk"))
        eng_prefixes = set(("un","over","under"))
        
        sp_prefixes = set()    
        with open("spprefixes.txt") as file:
            for line in file:
                for w in line.split():
                    sp_prefixes.add(w)
                    
        eng_prefixes_lat = set()
        with open("latinGreekPrefixes.txt") as file:
            for line in file:
                for w in line.split():
                    eng_prefixes_lat.add(w)
        
        self.prefix_check = list(eng_prefixes | eng_init_sounds | eng_prefixes | eng_prefixes_lat)
        
        eng_final_sounds = set(("ck", "ng", "gh"))
        eng_endings = set(("ed","s","ps","ts"))
        
        eng_suffixes = set()    
        with open("suffixes.txt") as file:
            for line in file:
                for w in line.split():
                    eng_suffixes.add(w)
                    
        sp_suffixes = set()    
        with open("spsuffixes.txt") as file:
            for line in file:
                for w in line.split():
                    sp_suffixes.add(w)
                    
#        Adding spanish suffixes made it worse!
        self.suffix_check = list(eng_suffixes | eng_final_sounds | eng_endings | sp_suffixes)
           
        self.prefix_vect = np.array(np.zeros(len(self.prefix_check)))          
        self.inside_vect = np.array(np.zeros(len(self.inside_check)))
        self.suffix_vect = np.array(np.zeros(len(self.suffix_check)))
        
        tag_keys = load('help/tagsets/upenn_tagset.pickle').keys()
        
        self.tag_vect_template = {}
        tag_id = 0
        for tag_key in tag_keys:
            self.tag_vect_template[tag_key] = tag_id
            tag_id += 1
            
        self.tag_vect = np.array(np.zeros(len(tag_keys)))

    def extract_features(self, word):
        len_chars = len(word) / self.avg_word_length
        len_tokens = len(word.split(' '))
        
        # Add all of the pre-processing to the init area
        
        
        r_score = 0.0
        vowels = ['a','e','i','o','u']

        # Maximum consecutive Vowels
        max_cons_v = 0
        max_cons_c = 0
        c_last_l = False
        v_last_l = False
        
        for l in word.lower():
            
            r_score += self.letter_rarity[l]
            
            if l in vowels:
                
                c_last_l = False
                
                if v_last_l == False:
                    cons_v = 1
                else:
                    cons_v += 1
                if cons_v > max_cons_v:
                    max_cons_v = cons_v
                    
                v_last_l = True
                
            elif l.isalpha():
                
                v_last_l = False
                
                if c_last_l == False:
                    cons_c = 1
                else:
                    cons_c += 1
                if cons_c > max_cons_c:
                    max_cons_c = cons_c
                    
                c_last_l = True
        
#        print(max_cons_v, max_cons_c, word)
                
        r_score_norm = r_score/len(word)
        
#        test_words = word.split(' ')
        test_words = word_tokenize(word)
        test_tags = [x[1] for x in pos_tag(test_words)]
        
        self.tag_vect.fill(0)
        
        for tag in test_tags:
            if tag not in self.tag_vect_template:
                print("Error! Didn't find tag! This shouldn't happen.")
            else:
                self.tag_vect[self.tag_vect_template[tag]] = 1
                
        self.prefix_vect.fill(0)
        self.inside_vect.fill(0)  
        self.suffix_vect.fill(0)
        
        for cased_word in test_words:
            
            word = cased_word.lower()
            
            num_synonyms = len(wordnet.synsets(word))
            
            prefix_index = 0
            for prefix in self.prefix_check:
                if word.startswith(prefix):
                    self.prefix_vect[prefix_index] = 1
                prefix_index += 1
                
            inside_index = 0
            for inside in self.inside_check:
                if inside in word:
                    self.inside_vect[inside_index] = 1
                inside_index += 1
            
            # So far, none of these features improve prediction.
            
            suffix_index = 0
            for suffix in self.suffix_check:
                if word.endswith(suffix):
                    self.suffix_vect[suffix_index] = 1
                suffix_index += 1
        
        result = []
        result.append(len_chars)
        result.append(len_tokens)
        result.append(r_score_norm)
        result.append(max_cons_v)
        result.append(max_cons_c)
        result.append(num_synonyms)
        
        result = np.hstack((result, self.suffix_vect, self.inside_vect, self.prefix_vect, self.tag_vect))
        
#        if word == "biology" or word == "neurons" or word == "disruption":
#            print(word)
#            
#            print("Suffixes:")
#            for i in range(len(self.suffix_check)):
#                if self.suffix_vect[i] == 1:
#                    print(self.suffix_check[i], self.suffix_vect[i])
#                
#            print("\nPrefixes:")    
#            for i in range(len(self.prefix_check)):
#                if self.prefix_vect[i] == 1:
#                    print(self.prefix_check[i], self.prefix_vect[i])
#            
#            print("\nInfixes:")    
#            for i in range(len(self.inside_check)):
#                if self.inside_vect[i] == 1:
#                    print(self.inside_check[i], self.inside_vect[i])

        return result

    def train(self, trainset):
        X = []
        y = []
        for sent in trainset:
            X.append(self.extract_features(sent['target_word']))
            y.append(sent['gold_label'])

        self.model.fit(X, y)

    def test(self, testset):
        X = []
        for sent in testset:
            X.append(self.extract_features(sent['target_word']))

        return self.model.predict(X)
