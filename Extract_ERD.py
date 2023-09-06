#!/usr/bin/env python
# coding: utf-8

# In[1]:


from nlp_lab import pre_process_text


# In[2]:


import spacy
import inflect # to get plural 

nlp = spacy.load("en_core_web_sm")


# In[3]:


from experta import *
from word2number import w2n

class Token(Fact):
    pass

class Entity(Fact):
    pass 

class Attribute(Fact):
    pass

class Relation(Fact):
    pass

def check_sequential_ids(id1, id2, id3):
    return id2 == id1 + 1 and id3 == id2 + 1

def pluralize_word(word):
    doc = nlp(word)
    lemma = doc[0].lemma_

    if lemma.endswith("s") or lemma.endswith("x") or lemma.endswith("sh") or lemma.endswith("ch"):
        plural_form = lemma + "es"
    elif lemma.endswith("y") and lemma[-2] not in "aeiou":
        plural_form = lemma[:-1] + "ies"
    else:
        plural_form = lemma + "s"
    return plural_form


# In[4]:


class ExtractERD(KnowledgeEngine):

    def __init__(self, text):
        super().__init__()
        self.entities = []
        self.attributes = {}
        self.relations = [] 
        self.text = text
    
    def get_entities_and_attributes_and_relations(self):
        result = []
        for entity_name in self.entities:
            result.append(f"Entity: {entity_name}")
        for entity_name, attribute_name in self.attributes.items():
            result.append(f"Attributes of {entity_name}: {attribute_name}")
        for relation in self.relations:
            result.append(f"Relation: {relation['entity1']} is {relation['r']} with {relation['entity2']} ")
        return result
    
    def ends_with_s(self, word):
        if word.endswith('s'):
            return True
        return False
    

    @DefFacts()
    def extrant_ERD_info(self):
        id_counter = len(self.text)
        for token in reversed(self.text):
            id_counter -= 1
            yield Token(id=id_counter, token=token['word'], pos=token['pos'],tag=token['tag'] , coreference_resolver=token['coreference_resolver'])

    @Rule(
        OR(
            Token(token=MATCH.t1, pos='NOUN', id=MATCH.id1),
            Token(token='it', id=MATCH.id1, coreference_resolver=MATCH.t1),
            Token(token='he', id=MATCH.id1, coreference_resolver=MATCH.t1),
            Token(token='she', id=MATCH.id1, coreference_resolver=MATCH.t1),
            Token(token='they', id=MATCH.id1, coreference_resolver=MATCH.t1)
        ),
      Token(token=MATCH.t2, pos='VERB', id=MATCH.id2),
      Token(token=MATCH.t3, pos='NOUN', id=MATCH.id3),
      TEST(lambda id1, id2, id3, t2: check_sequential_ids(id1, id2, id3) and t2 not in ['has', 'have', 'contain', 'possess', 'own', 'include', 'includes', 'involve', 'consist', 'comprise', 'composed']))
    def extract_noun_verb_noun(self, id1, id2, id3, t1, t2, t3):
        if t1 not in self.entities and pluralize_word(t1) not in self.entities:
            self.declare(Entity(name=pluralize_word(t1)))
            self.entities.append(pluralize_word(t1))
        if t3 not in self.entities and pluralize_word(t3) not in self.entities:
            self.declare(Entity(name=pluralize_word(t3)))
            self.entities.append(pluralize_word(t3))

        if self.ends_with_s(t3):
            relation = Relation(entity1=pluralize_word(t1), r='OTM', entity2=pluralize_word(t3))
            #relation2 = Relation(entity1=t3, r='OTO', entity2=t1)

            if pluralize_word(t3) in self.attributes:
                self.attributes[pluralize_word(t3)].append(nlp(t1)[0].lemma_+'_id')
            else:
                self.attributes[pluralize_word(t3)] = [nlp(t1)[0].lemma_+'_id']
            
            self.declare(relation)
            #self.declare(relation2)
            #self.relations.extend([relation, relation2])
            self.relations.extend([relation])
            
        else:
            relation = Relation(entity1=pluralize_word(t1), r='OTO', entity2=pluralize_word(t3))
            if pluralize_word(t1) in self.attributes:
                self.attributes[pluralize_word(t1)].append(nlp(t3)[0].lemma_+'_id')
            else:
                self.attributes[pluralize_word(t1)] = [nlp(t3)[0].lemma_+'_id']
                
            if pluralize_word(t3) in self.attributes:
                self.attributes[pluralize_word(t3)].append(nlp(t1)[0].lemma_+'_id')
            else:
                self.attributes[pluralize_word(t3)] = [nlp(t1)[0].lemma_+'_id']
            self.declare(relation)
            self.relations.extend([relation])
                
        i = 1
        while id3 + i < len(self.text):
            token = self.text[id3 + i]
            if token['word'] == 'and':
                i += 1
                continue
            if token['pos'] != 'NOUN':
                break
            attribute = Attribute(entity_name=t1, name=token['word'])
            self.declare(attribute)
            
            if self.ends_with_s(token['word']) and token['word'] not in self.entities and pluralize_word(token['word']) not in self.entities:
                self.declare(Entity(name=token['word']))
                self.entities.append(token['word'])
                self.declare(Attribute(entity_name=t1, name=token['word']))
                relation = Relation(entity1=t1, r="OTM", entity2=token['word'])
                #relation2 = Relation(entity1=token['word'], r="OTO", entity2=t1)
                self.declare(relation)
                #self.declare(relation2)
                #self.relations.extend([relation, relation2])
                self.relations.extend([relation])
                self.attributes.setdefault(token['word'], []).append(nlp(t1)[0].lemma_ + "_id")
            elif self.ends_with_s(token['word']) and (token['word'] in self.entities or pluralize_word(token['word']) in self.entities):
                self.declare(Attribute(entity_name=t1, name=token['word']))
                relation = Relation(entity1=t1, r="OTM", entity2=token['word'])
                #relation2 = Relation(entity1=token['word'], r="OTO", entity2=t1)
                self.declare(relation)
                #self.declare(relation2)
                #self.relations.extend([relation, relation2])
                self.relations.extend([relation])
                self.attributes.setdefault(token['word'], []).append(nlp(t1)[0].lemma_ + "_id") 
            else:
                self.attributes[t1].append(token['word'])
            i += 1            
        
    @Rule(
        OR(
            Token(token=MATCH.t1, pos='NOUN', id=MATCH.id1),
            Token(token='it', id=MATCH.id1, coreference_resolver=MATCH.t1),
            Token(token='he', id=MATCH.id1, coreference_resolver=MATCH.t1),
            Token(token='she', id=MATCH.id1, coreference_resolver=MATCH.t1),
            Token(token='they', id=MATCH.id1, coreference_resolver=MATCH.t1)
        ),
      Token(token=MATCH.t2, pos='VERB', id=MATCH.id2),
      Token(token=MATCH.t3, pos='NOUN', id=MATCH.id3),
      TEST(lambda id1, id2, id3, t2: check_sequential_ids(id1, id2, id3) and t2 in ['has', 'have', 'contain', 'possess', 'own', 'include', 'includes', 'involve', 'consist', 'comprise', 'composed']))
    def extract_noun_verb_attribute(self, id1, id2, id3, t1, t2, t3):
        if t1 not in self.entities and pluralize_word(t1) not in self.entities:
            self.declare(Entity(name=pluralize_word(t1)))
            self.entities.append(pluralize_word(t1))
        if self.ends_with_s(t3) and t3 not in self.entities and pluralize_word(t3) not in self.entities:
            self.declare(Entity(name=pluralize_word(t3)))
            self.entities.append(pluralize_word(t3))
        if self.ends_with_s(t3) and (t3 in self.entities or pluralize_word(t3) in self.entities):
            relation = Relation(entity1=t1, r="OTM", entity2=t3)
            #relation2 = Relation(entity1=t3, r="OTO", entity2=t1)
            self.declare(relation)
            #self.declare(relation2)
            #self.relations.extend([relation, relation2])
            self.relations.extend([relation])
            self.attributes.setdefault(pluralize_word(t3), []).append(nlp(t1)[0].lemma_ + "_id")
        else:
            self.declare(Attribute(entity_name=pluralize_word(t1), name=t3))
            self.attributes.setdefault(pluralize_word(t1), []).append(t3)

        i = 1
        while id3 + i < len(self.text):
            token = self.text[id3 + i]
            if token['word'] == 'and':
                i += 1
                continue
            if token['pos'] != 'NOUN':
                break
                
            if self.ends_with_s(token['word']) and token['word'] not in self.entities and pluralize_word(token['word']) not in self.entities:
                self.declare(Entity(name=pluralize_word(token['word'])))
                self.entities.append(pluralize_word(token['word']))
                self.declare(Attribute(entity_name=pluralize_word(t1), name=token['word']))
                relation = Relation(entity1=pluralize_word(t1), r="OTM", entity2=token['word'])
                #relation2 = Relation(entity1=token['word'], r="OTO", entity2=t1)
                self.declare(relation)
                #self.declare(relation2)
                #self.relations.extend([relation, relation2])
                self.relations.extend([relation])
                self.attributes.setdefault(pluralize_word(token['word']), []).append(nlp(t1)[0].lemma_ + "_id")
            elif self.ends_with_s(token['word']) and (token['word'] in self.entities or pluralize_word(token['word']) in self.entities):
                self.declare(Attribute(entity_name=pluralize_word(t1), name=token['word']))
                relation = Relation(entity1=pluralize_word(t1), r="OTM", entity2=token['word'])
                #relation2 = Relation(entity1=token['word'], r="OTO", entity2=t1)
                self.declare(relation)
                #self.declare(relation2)
                #self.relations.extend([relation, relation2])
                self.relations.extend([relation])
                self.attributes.setdefault(pluralize_word(token['word']), []).append(nlp(t1)[0].lemma_ + "_id")    
            else:
                attribute = Attribute(entity_name=pluralize_word(t1), name=token['word'])
                self.declare(attribute)
                self.attributes.setdefault(pluralize_word(t1), []).append(token['word'])
        
            i += 1 

    
    @Rule(Token(token=MATCH.t1, pos='NOUN', id=MATCH.id1),
          Token(token="'s", id=MATCH.id2),
          Token(token=MATCH.t2, pos='NOUN', id=MATCH.id3),
          TEST(lambda id1, id2, id3, t2: check_sequential_ids(id1, id2, id3)))
    def extract_noun_attributes(self, t1, t2, id1, id2, id3):
        if t1 not in self.entities:
            self.declare(Entity(name=pluralize_word(t1)))
            self.entities.append(pluralize_word(t1))

        if self.ends_with_s(t2):
            if t2 not in self.entities:
                self.declare(Entity(name=pluralize_word(t2)))
                self.entities.append(pluralize_word(t2))
            self.declare(Attribute(entity_name=pluralize_word(t1), name=t2))
            relation = Relation(entity1=pluralize_word(t1), r="OTM", entity2=t2)
            #relation2 = Relation(entity1=t2, r="OTO", entity2=t1)
            self.declare(relation)
            #self.declare(relation2)
            self.relations.append(relation)
            #self.relations.append(relation2)
            
            if t2 in self.attributes:
                self.attributes[pluralize_word(t2)].append(nlp(t1)[0].lemma_ + "_id")
            else:
                self.attributes[pluralize_word(t2)] = [nlp(t1)[0].lemma_ + "_id"]
        else:
            self.declare(Attribute(entity_name=pluralize_word(t1), name=t2))
            self.attributes[pluralize_word(t1)] = [t2]

        i = 1
        while id3 + i < len(self.text):
            token = self.text[id3 + i]
            if token['word'] == 'and':
                i += 1
                continue
            if token['pos'] != 'NOUN':
                break
            attribute = Attribute(entity_name=pluralize_word(t1), name=token['word'])
            self.declare(attribute)
            self.attributes[pluralize_word(t1)].append(token['word'])
            i += 1        
        
    @Rule(
        Token(token=MATCH.t1, tag='CD', id=MATCH.id1),
        Token(token=MATCH.t2, id=MATCH.id2),
        Token(token=MATCH.t3, id=MATCH.id3),
        TEST(lambda id1, id2, id3: check_sequential_ids(id1, id2, id3)))
    def extract_entities_num(self, id1, id2, id3, t1):
        for i in range(0, w2n.word_to_num(t1)+1):
            token = self.text[id3 + i]
            if token['word'] == 'and':
                continue
            if token['pos'] != 'NOUN':
                break 
            if token['word'] not in self.entities:
                self.declare(Entity(name=pluralize_word(token['word'])))
                self.entities.append(pluralize_word(token['word']))
                


# In[ ]:




