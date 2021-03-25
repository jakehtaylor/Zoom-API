from fuzzywuzzy import fuzz

mksh = 'Madison Krall (she/her) UT' 
mk =  'Madison Krall'

#print(fuzz.token_set_ratio(mksh, mk))

kn = 'kneil' 
kN = 'Katherine Neil'

#print(fuzz.token_set_ratio(kn, kN))

jason1 = 'Jason Katsoff'
jason2 = 'Jason Zahrndt'

#print(fuzz.token_set_ratio(jason1, jason2))

sc1 = 'Shraddha (shruh-the) Chaplot' 
sc =  'Shraddha Chaplot',

#print(fuzz.token_set_ratio(sc1, sc))

tlfMS = 'Thomas La Foe - Mississippi State' 
tlf  = 'Thomas La Foe'


#print(fuzz.token_sort_ratio(tlfMS, tlf))
#print(fuzz.token_set_ratio(tlfMS, tlf))


j1 = "FelipeB"
j2 = "Felipe Benutti"

print(fuzz.token_sort_ratio(j1,j2))
print(fuzz.token_set_ratio(j1,j2))
print(fuzz.partial_ratio(j1,j2))
print(fuzz.ratio(j1,j2))

