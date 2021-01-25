
with open("rom.gb", "rb") as f:
	text = f.read()

with open("expected_rom.gb", "rb") as f:
	text2 = f.read()

import random

addrs = []

state = True
eqs = 1
for i in range(len(text)):
	if i % (1 << 12) == 0:
		print()
	eq = (text[i] == text2[i])
	eqs <<= 1
	eqs |= not eq
	if eqs.bit_length() > (1<<8):
		print(hex(eqs)[3:])
		eqs = 1

	if not eq:
		addrs.append(i)

	#continue
	
	if state != eq:
		#state = eq
		if not eq:
			#print(bin(text [i])[2:].zfill(8), hex(text [i])[2:].zfill(2), end = " : ")
			#print(bin(text2[i])[2:].zfill(8), hex(text2[i])[2:].zfill(2))
			#print()
			from_i = i
		else:
			#print("from", bin(from_i)[2:].zfill(ADDR_WIDTH))
			#print("to  ", bin(     i)[2:].zfill(ADDR_WIDTH))
			#print("len ", i - from_i)
			pass
			#input()

input()

ADDR_WIDTH = 20
NUM_TRIES  = 20

#addrs = [random.getrandbits(ADDR_WIDTH) for _ in range(NUM_TRIES)]

import collections
stats = collections.defaultdict(int)

masks = [(1 << i) for i in range(12, ADDR_WIDTH)]

#for addr in addrs:
#	print(addr)
#	for mask in masks:
#		v  = text2[addr]
#		v2 = text2[addr & ~mask]
#		#print(hex(v)[2:].zfill(2), end="! " if (v==v2) else " ")
#		print("", end="X" if (v==v2) else ".")
#		if (v==v2):
#			stats[mask] += 1
#	print()
#	for mask in masks:
#		v = text2[addr]
#		v2 = text2[addr |  mask]
#		#print(hex(v)[2:].zfill(2), end="! " if (v==v2) else " ")
#		print("", end="X" if (v==v2) else ".")
#		if (v==v2):
#			stats[mask] += 1
#	print()
#	print()

for addr in addrs:
	print(hex(addr), end=": ")
	for bank in range(64):
		addr2 = (bank << 12) | (addr & 0xFFF)
		v  = text2[addr]
		v2 = text2[addr2]
		#print(hex(v)[2:].zfill(2), end="! " if (v==v2) else " ")
		print("", end="X" if (v==v2) else ".")
		if (v==v2):
			stats[bank] += 1
	print()

import pprint
pprint.pprint(dict(stats))
print(len(addrs))

checksum = sum(text) - text[0x014E] - text[0x014F]
print(hex(39977))
print(hex(checksum))


# 0:  1263, 
# 1:   644,
# 2:   680, 
# 3:   840, 
# 4:  1029, 
# 5:  1336, 
# 6:  2458, 
# 7:  3099, 
# 8:  5318, 
# 9:  9794, 
#10: 11025, 
#11: 15723, 
#12:  6580, 
#
#13:  3492, 
#14: 23667, 
#15: 45008, 
#16: 33478, 
#17: 25776, 
#18: 54614, 
#19: 62793
#
#-11: 34762, 
#-12: 59001, 
#-13: 70801, 
#-16: 30015, 
#-17: 53969, 
#-18: 28819, 
#-19: 15828, 
#-10: 19466, 
#-14: 58560, 
#-8: 6091, 
#-6: 1905, 
#-7: 3230, 
#-9: 10079, 
#-5: 1425, 
#-4: 972, 
#-3: 763, 
#-1: 657, 
#-2: 667, 
#-15: 28635, 
