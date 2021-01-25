import Adafruit_BBIO.GPIO as gpio
from nanosleep import nanosleep

# WR: Low active
# RD: Low active
# CS: High -> ROM, Low -> RAM (probably not necessary)

#GND  = "P9_00"
AUDIO =	"P8_17"
RST   =	"P8_18"
DATA  = [
	"P8_26", # D_0
	"P8_25", # D_1
	"P8_24", # D_2
	"P8_23", # D_3
	"P8_22", # D_4
	"P8_21", # D_5
	"P8_11", # D_6
	"P8_12", # D_7  #P8_20 seemed not to want to be LOW
]
ADDR  = [
	"P8_42", # A_00
	"P8_41", # A_01
	"P8_40", # A_02
	"P8_39", # A_03
	"P8_38", # A_04
	"P8_37", # A_05
	"P8_36", # A_06
	"P8_35", # A_07
	"P8_34", # A_08
	"P8_33", # A_09
	"P8_32", # A_10
	"P8_31", # A_11
	"P8_30", # A_12
	"P8_29", # A_13
	"P8_28", # A_14
	"P8_27", # A_15
]
CS    =	"P8_43"; CS_RAM     = gpio.LOW; CS_ROM      = gpio.HIGH
RD    =	"P8_44"; RD_enabled = gpio.LOW; RD_disabled = gpio.HIGH
WD    =	"P8_45"; WD_enabled = gpio.LOW; WD_disabled = gpio.HIGH
CLK   =	"P8_46"
#VCC  = "P9_02"

OE    = "P8_16"

def set_address(address):
	assert address >= 0
	assert address.bit_length() <= 16
	for i, pin in enumerate(ADDR):
		mask = 1 << i
		level = gpio.HIGH if mask & address else gpio.LOW
		gpio.output(pin, level)

def set_data(data):
	assert gpio.input(RD) == RD_disabled # make sure we are not in read mode because then the cartridge would be writing the data
	for pin in DATA:
		gpio.setup(pin, gpio.OUT, gpio.PUD_OFF, gpio.LOW)
	
	assert data > 0
	assert data.bit_length() <= 8
	for i, pin in enumerate(DATA):
		mask = 1 << i
		level = gpio.HIGH if mask & data else gpio.LOW
		gpio.output(pin, level)

def unset_data():
	for pin in DATA:
		gpio.setup(pin, gpio.IN, gpio.PUD_OFF)

def read_data():
	assert gpio.input(RD) == RD_enabled # makes no sense to read if cartridge doesn't know it should output something
	data = 0
	for i, pin in enumerate(DATA):
		mask = 1 << i
		if gpio.input(pin) == gpio.HIGH:
			data |= mask
	return data

def enable_read():
	assert gpio.input(WD) == WD_disabled
	assert all(gpio.gpio_function(pin) == gpio.IN for pin in DATA)
	gpio.output(RD, RD_enabled)

def disable_read():
	gpio.output(RD, RD_disabled)

def enable_write():
	assert gpio.input(RD) == RD_disabled
	assert all(gpio.gpio_function(pin) == gpio.OUT for pin in DATA)
	gpio.output(WD, WD_enabled)

def disable_write():
	gpio.output(WD, WD_disabled)

def set_chipselect(cs):
	gpio.output(CS, cs)

def reset_chipselect():
	gpio.output(CS, CS_ROM)

def rise_clock():
	gpio.output(CLK, gpio.HIGH)

def fall_clock():
	gpio.output(CLK, gpio.LOW)

def init_gpio():
	print ("initializing GPIO")
	gpio.setup(RST, gpio.OUT, gpio.PUD_OFF, gpio.HIGH)
	for pin in DATA:
		gpio.setup(pin, gpio.IN, gpio.PUD_OFF)
	for pin in ADDR:
		gpio.setup(pin, gpio.OUT, gpio.PUD_OFF, gpio.LOW)
	gpio.setup(CS, gpio.OUT, gpio.PUD_OFF, gpio.HIGH)
	gpio.setup(RD, gpio.OUT, gpio.PUD_OFF, gpio.HIGH)
	gpio.setup(WD, gpio.OUT, gpio.PUD_OFF, gpio.HIGH)
	gpio.setup(OE, gpio.OUT, gpio.PUD_OFF, gpio.HIGH)
	gpio.setup(CLK, gpio.OUT, gpio.PUD_OFF, gpio.LOW)


# -------------------------------------------------------------------- #

def read_raw(address, cs=CS_ROM):
	# rising edge
	rise_clock()
	# wait 150ns
	nanosleep(150)
	# enable read / apply address
	enable_read()
	set_address(address)
	# wait 100ns
	nanosleep(100)
	# apply CS
	set_chipselect(cs)
	# wait 250ns
	nanosleep(250)
	# falling  edge / read data
	fall_clock()
	data = read_data()
	# wait 500ns
	nanosleep(500)
	# reset CS
	reset_chipselect()
	# return data
	return data

def write_raw(address, value, cs=CS_RAM):
	# rising edge
	rise_clock()
	# wait 150ns
	nanosleep(150)
	# disable read / apply address / apply data (no wait in before!?)
	disable_read()
	set_address(address)
	set_data(value)
	# wait 100ns
	nanosleep(100)
	# apply CS
	set_chipselect(cs)
	# wait 250ns
	nanosleep(250)
	# falling edge / enable write
	fall_clock()
	enable_write()
	# wait 300ns
	nanosleep(300)
	# disable write
	disable_write()
	# wait 200ns
	nanosleep(200)
	# reset CS
	reset_chipselect()
	# change pins back to input
	unset_data()

# -------------------------------------------------------------------- #

ROM_BANK_NUMBER_LOWER_5BITS_ADDR = 0x2000
ROM_BANK_NUMBER_UPPER_2BITS_ADDR = 0x4000
RAM_BANK_NUMBER_ADDR             = 0x4000 # yes those two are the same, thats why there is
ROM_RAM_BANKING_MODE_SELECT_ADDR = 0x6000 # this
ROM_BANKING_MODE = 0x00
RAM_BANKING_MODE = 0x01
MBC_TYPE = "uninitialized"
CURRENT_ROM_BANK = None
CURRENT_BANKING_MODE = None
def select_ROM_bank(bank):
	global CURRENT_ROM_BANK, CURRENT_RAM_BANK, CURRENT_BANKING_MODE
	if bank == CURRENT_ROM_BANK:
		return
	print ("selecting bank", bank)
	# make sure it is initialized
	if MBC_TYPE == "uninitialized":
		raise Exception("MBC_TYPE was not initialized, call read_cartridge_type() first")
	# No MBC
	elif MBC_TYPE == None:
		raise Exception("ROM address out of range")
	# MBC1
	elif MBC_TYPE == "MBC1":
		# check if ROM only banking mode is needed
		if bank > 0x1F and CURRENT_BANKING_MODE != "rom":
			print ("selecting ROM banking mode")
			write_raw(ROM_RAM_BANKING_MODE_SELECT_ADDR, ROM_BANKING_MODE, CS_ROM)
			CURRENT_BANKING_MODE = "rom"
			CURRENT_RAM_BANK = None
		# quirks of MBC1
		if bank & 0x0F == 0:
			print ("Warning: On MBC1 selecting bank %s will actually read from bank %s"
				% (bank, bank+1))
		# write lower bits
		lower_bits = bank & 0x1F
		write_raw(ROM_BANK_NUMBER_LOWER_5BITS_ADDR, lower_bits, CS_ROM)
		# if necessary, write upper bits
		if CURRENT_BANKING_MODE == "rom":
			upper_bits = bank >> 5
			write_raw(ROM_BANK_NUMBER_UPPER_2BITS_ADDR, upper_bits, CS_ROM)
	elif MBC_TYPE == "MBC3":
		# select bank
		write_raw(ROM_BANK_NUMBER_LOWER_5BITS_ADDR, bank, CS_ROM)

	# other kind of MBC
	else:
		raise NotImplementedError("MBC Type %s is currently not supported" % MBC_TYPE)
	CURRENT_ROM_BANK = bank

ROM_BANK_0_BASE_ADDR = 0x0000
ROM_BANK_N_BASE_ADDR = 0x4000
def read_ROM(rom_address):
	assert ROM_BANK_SIZE == 0x4000
	if rom_address <= ROM_BANK_SIZE:
		address = ROM_BANK_0_BASE_ADDR + rom_address
	else:
		bank, in_bank_offset = divmod(rom_address, ROM_BANK_SIZE)
		select_ROM_bank(bank)
		address = ROM_BANK_N_BASE_ADDR + in_bank_offset
	return read_raw(address, CS_ROM)

def write_ROM(rom_address, value):
	raise Exception("ROM is readonly")

RAM_BANK_BASE_ADDR = 0xA000
RAM_ENABLE_ADDR = 0x0000
RAM_ENABLE  = 0x0A
RAM_DISABLE = 0x00

# -------------------------------------------------------------------- #

LOGO_BASE_ADDR = 0x0104
CORRECT_LOGO = [
0xCE, 0xED, 0x66, 0x66, 0xCC, 0x0D, 0x00, 0x0B, 0x03, 0x73, 0x00, 0x83, 0x00, 0x0C, 0x00, 0x0D,
0x00, 0x08, 0x11, 0x1F, 0x88, 0x89, 0x00, 0x0E, 0xDC, 0xCC, 0x6E, 0xE6, 0xDD, 0xDD, 0xD9, 0x99,
0xBB, 0xBB, 0x67, 0x63, 0x6E, 0x0E, 0xEC, 0xCC, 0xDD, 0xDC, 0x99, 0x9F, 0xBB, 0xB9, 0x33, 0x3E,
]
LOGO_WIDTH = 48
LOGO_HEIGH = 8
LOGO_BYTE_SIZE = 48
def read_logo():
	"""this prints the logo read from cartridge and also asserts it to be correct"""
	print("reading logo")
	logo = []
	for offset in range(LOGO_BYTE_SIZE):
		value = read_ROM(LOGO_BASE_ADDR + offset)
		logo.append(value)
	for o1 in range(0, LOGO_BYTE_SIZE, LOGO_WIDTH//2):
		for o2 in (0, 1):
			for nibbleshift in (4, 0):
				for o3 in range(0,LOGO_WIDTH//2,2):
					byte = logo[o1 + o2 + o3]
					nibble = (byte >> nibbleshift) & 0x0F
					pixels = bin(nibble)[2:].zfill(4)
					pixels = pixels.replace("0", " ")
					pixels = pixels.replace("1", "X")
					print (pixels, end="")
				print ()
	assert logo == CORRECT_LOGO
	return logo

TITLE_BASE_ADDR = 0x0134
TITLE_LENGTH = 16
def read_title():
	title = ""
	for offset in range(TITLE_LENGTH):
		value = read_ROM(TITLE_BASE_ADDR + offset)
		if value == 0x00:
			break
		title += chr(value)
	print ("Title:", title)
	return title

CGB_FLAG_ADDR = 0x0143
def read_CGB_flag():
	value = read_ROM(CGB_FLAG_ADDR)
	if value == 0x80:
		print ("Game supports CGB functions, but also works on old gameboys")
	elif value == 0xC0:
		print ("Game works on CGB only")
	else:
		print ("This game has no CGB functionality")

OLD_LICENSEE_CODE_ADDR  = 0x014B
OLD_LICENSEE_NAMES = {0x00:"none", 0x01:"nintendo", 0x08:"capcom", 0x09:"hot-b", 0x0A:"jaleco", 0x0B:"coconuts", 0x0C:"elite systems", 0x13:"electronic arts", 0x18:"hudsonsoft", 0x19:"itc entertainment", 0x1A:"yanoman", 0x1D:"clary", 0x1F:"virgin", 0x20:"KSS", 0x24:"pcm complete", 0x25:"san-x", 0x28:"kotobuki systems", 0x29:"seta", 0x30:"infogrames", 0x31:"nintendo", 0x32:"bandai", 0x33:"GBC - see above", 0x34:"konami", 0x35:"hector", 0x38:"Capcom", 0x39:"Banpresto", 0x3C:"*entertainment i", 0x3E:"gremlin", 0x41:"Ubisoft", 0x42:"Atlus", 0x44:"Malibu", 0x46:"angel", 0x47:"spectrum holoby", 0x49:"irem", 0x4A:"virgin", 0x4D:"malibu", 0x4F:"u.s. gold", 0x50:"absolute", 0x51:"acclaim", 0x52:"activision", 0x53:"american sammy", 0x54:"gametek", 0x55:"park place", 0x56:"ljn", 0x57:"matchbox", 0x59:"milton bradley", 0x5A:"mindscape", 0x5B:"romstar", 0x5C:"naxat soft", 0x5D:"tradewest", 0x60:"titus", 0x61:"virgin", 0x67:"ocean", 0x69:"electronic arts", 0x6E:"elite systems", 0x6F:"electro brain", 0x70:"Infogrammes", 0x71:"Interplay", 0x72:"broderbund", 0x73:"sculptered soft", 0x75:"the sales curve", 0x78:"t*hq", 0x79:"accolade", 0x7A:"triffix entertainment", 0x7C:"microprose", 0x7F:"kemco", 0x80:"misawa entertainment", 0x83:"lozc", 0x86:"tokuma shoten intermedia", 0x8B:"bullet-proof software", 0x8C:"vic tokai", 0x8E:"ape", 0x8F:"i'max", 0x91:"chun soft", 0x92:"video system", 0x93:"tsuburava", 0x95:"varie", 0x96:"yonezawa/s'pal", 0x97:"kaneko", 0x99:"arc", 0x9A:"nihon bussan", 0x9B:"Tecmo", 0x9C:"imagineer", 0x9D:"Banpresto", 0x9F:"nova", 0xA1:"Hori electric", 0xA2:"Bandai", 0xA4:"Konami", 0xA6:"kawada", 0xA7:"takara", 0xA9:"technos japan", 0xAA:"broderbund", 0xAC:"Toei animation", 0xAD:"toho", 0xAF:"Namco", 0xB0:"Acclaim", 0xB1:"ascii or nexoft", 0xB2:"Bandai", 0xB4:"Enix", 0xB6:"HAL", 0xB7:"SNK", 0xB9:"pony canyon", 0xBA:"*culture brain o", 0xBB:"Sunsoft", 0xBD:"Sony imagesoft", 0xBF:"sammy", 0xC0:"Taito", 0xC2:"Kemco", 0xC3:"Squaresoft", 0xC4:"tokuma shoten intermedia", 0xC5:"data east", 0xC6:"tonkin house", 0xC8:"koei", 0xC9:"ufl", 0xCA:"ultra", 0xCB:"vap", 0xCC:"use", 0xCD:"meldac ", 0xCE:"*pony canyon or ", 0xCF:"angel", 0xD0:"Taito", 0xD1:"sofel", 0xD2:"quest", 0xD3:"sigma enterprises", 0xD4:"ask kodansha", 0xD6:"naxat soft", 0xD7:"copya systems", 0xD9:"Banpresto", 0xDA:"tomy", 0xDB:"ljn", 0xDD:"ncs", 0xDE:"human", 0xDF:"altron", 0xE0:"jaleco", 0xE1:"towachiki", 0xE2:"uutaka", 0xE3:"varie", 0xE5:"epoch", 0xE7:"athena", 0xE8:"asmik", 0xE9:"natsume", 0xEA:"king records", 0xEB:"atlus", 0xEC:"Epic/Sony records", 0xEE:"igs", 0xF0:"a wave", 0xF3:"extreme entertainment", 0xFF:"ljn"}
NEW_LICENSEE_CODE_ADDR0 = 0x0144
NEW_LICENSEE_CODE_ADDR1 = 0x0145
NEW_LICENSEE_NAMES = {0x00:"none", 0x01:"nintendo", 0x08:"capcom", 0x13:"electronic arts", 0x18:"hudsonsoft", 0x19:"b-ai", 0x20:"kss" ,0x22:"pow", 0x24:"pcm complete", 0x25:"san-x", 0x28:"kemco japan", 0x29:"seta", 0x30:"viacom", 0x31:"nintendo", 0x32:"bandia", 0x33:"ocean/acclaim", 0x34:"konami", 0x35:"hector", 0x37:"taito", 0x38:"hudson", 0x39:"banpresto", 0x41:"ubi soft", 0x42:"atlus", 0x44:"malibu", 0x46:"angel", 0x47:"pullet-proof", 0x49:"irem", 0x50:"absolute", 0x51:"acclaim", 0x52:"activision", 0x53:"american sammy", 0x54:"konami", 0x55:"hi tech entertainment", 0x56:"ljn", 0x57:"matchbox", 0x58:"mattel", 0x59:"milton bradley", 0x60:"titus", 0x61:"virgin", 0x64:"lucasarts", 0x67:"ocean", 0x69:"electronic arts", 0x70:"infogrames", 0x71:"interplay", 0x72:"broderbund", 0x73:"sculptured", 0x75:"sci", 0x78:"t*hq", 0x79:"accolade", 0x80:"misawa", 0x83:"lozc", 0x86:"tokuma shoten i*", 0x87:"tsukuda ori*", 0x91:"chun soft", 0x92:"video system", 0x93:"ocean/acclaim", 0x95:"varie", 0x96:"yonezawa/s'pal", 0x97:"kaneko", 0x99:"pack in soft"}
def read_licensee_code():
	old_licensee_code = read_ROM(OLD_LICENSEE_CODE_ADDR)
	if old_licensee_code != 0x33:
		print ("Old Style Licensee Code detected")
		licensee_name = OLD_LICENSEE_NAMES.get(old_licensee_code, "")
		print ("Licensee:", hex(old_licensee_code), licensee_name)
		print ("(Super Gameboy functions will not be available)")
		return ["old", old_licensee_code]
	else:
		print ("New Style Licensee Code detected")
		new_licensee_code0 = read_ROM(NEW_LICENSEE_CODE_ADDR0)
		new_licensee_code1 = read_ROM(NEW_LICENSEE_CODE_ADDR1)
		new_licensee_code = (new_licensee_code0 & 0xF << 4) | (new_licensee_code1 & 0xF)
		licensee_name = NEW_LICENSEE_NAMES.get(new_licensee_code, "")
		print ("Licensee:", hex(new_licensee_code0), hex(new_licensee_code1), licensee_name)
		return ["new", new_licensee_code]

SGB_FLAG_ADDR = 0x0143
def read_SGB_flag():
	value = read_ROM(SGB_FLAG_ADDR)
	if value == 0x00:
		print ("Game does not support SGB functions")
	elif value == 0x03:
		print ("Game supports SGB functions")
	else:
		print ("Unknown value for SGB flag")
	return value

CARTRIDGE_TYPE_ADDR  = 0x0147
CARTRIDGE_TYPES = {
#     ( MBC   ,  RAM ,  Battery , Misc .. )
0x00: ( None  ,                 ),
0x01: ("MBC1" ,                 ),
0x02: ("MBC1" , "RAM"           ),
0x03: ("MBC1" , "RAM", "BATTERY"),
0x05: ("MBC2" ,                 ),
0x06: ("MBC2"        , "BATTERY"),
0x08: ( None  , "RAM"           ),
0x09: ( None  , "RAM", "BATTERY"),
0x0B: ("MMM01",                 ),
0x0C: ("MMM01", "RAM"           ),
0x0D: ("MMM01", "RAM", "BATTERY"),
0x0F: ("MBC3"        , "BATTERY", "TIMER" ),
0x10: ("MBC3" , "RAM", "BATTERY", "TIMER" ),
0x11: ("MBC3" ,                 ),
0x12: ("MBC3" , "RAM"           ),
0x13: ("MBC3" , "RAM", "BATTERY"),
0x15: ("MBC4"                   ),
0x16: ("MBC4" , "RAM"           ),
0x17: ("MBC4" , "RAM", "BATTERY"),
0x19: ("MBC5"                   ),
0x1A: ("MBC5" , "RAM"           ),
0x1B: ("MBC5" , "RAM", "BATTERY"),
0x1C: ("MBC5"                   , "RUMBLE"),
0x1D: ("MBC5" , "RAM"           , "RUMBLE"),
0x1E: ("MBC5" , "RAM", "BATTERY", "RUMBLE"),
0xFC: ("POCKET CAMERA",         ),
0xFD: ("BANDAI TAMA5",          ),
0xFE: ("HuC3" ,                 ),
0xFF: ("HuC1" , "RAM", "BATTERY"),
}
def read_cartridge_type():
	""" also initializes MBC type """
	global MBC_TYPE
	value = read_ROM(CARTRIDGE_TYPE_ADDR)
	cartridge_type = CARTRIDGE_TYPES.get(value, ["Unknown Cartridge Type"])
	print("Cartridge Type:", cartridge_type)
	MBC_TYPE = cartridge_type[0]
	return cartridge_type

ROM_SIZE_ADDR = 0x0148
ROM_BANK_SIZE = 16 * 1024
ROM_BANK_COUNT = None
ROM_SIZE = None
def read_ROM_size():
	global ROM_BANK_COUNT, ROM_SIZE
	value = read_ROM(ROM_SIZE_ADDR)
	print ("ROM size value", value)
	n0 = (value & 0x0F)
	n1 = (value & 0xF0) >> 4
	ROM_BANK_COUNT = (1 << n0) * 2
	if n1:
		ROM_BANK_COUNT += (1 << n1) * 2
	ROM_SIZE = ROM_BANK_COUNT * ROM_BANK_SIZE
	print ("ROM Bank Count:", ROM_BANK_COUNT)
	print ("ROM Size:", ROM_SIZE)
	return ROM_SIZE

RAM_SIZE_ADDR = 0x0149
RAM_SIZES = {
0x00: 0       ,
0x01: 2 * 1024,
0x02: 8 * 1024,
0x03:32 * 1024,
}
RAM_BANK_SIZE = 8 * 1024
RAM_BANK_COUNT = None
RAM_SIZE = None
def read_RAM_size():
	global RAM_SIZE, RAM_BANK_COUNT
	value = read_ROM(RAM_SIZE_ADDR)
	print ("RAM size value", value)
	RAM_SIZE = RAM_SIZES[value]
	RAM_BANK_COUNT = RAM_SIZE // RAM_BANK_SIZE
	print ("RAM Bank Count:", RAM_BANK_COUNT)
	print ("RAM SIZE", RAM_SIZE)
	return RAM_SIZE

DESTINATION_CODE_ADDR = 0x14A
def read_destination_code():
	value = read_ROM(DESTINATION_CODE_ADDR)
	if value == 0x00:
		print ("Intended for release in Japan")
	elif value == 0x01:
		print ("Intended for release outside of Japan")
	else:
		print ("unknown destination code")
	return value

VERSION_NUMBER_ADDR = 0x014C
def read_version_number():
	value = read_ROM(VERSION_NUMBER_ADDR)
	print ("Version:", value)
	return value

HEADER_CHECKSUM_ADDR = 0x014D
HEADER_CHECKSUM = None
def read_header_checksum():
	global HEADER_CHECKSUM
	HEADER_CHECKSUM = read_ROM(HEADER_CHECKSUM_ADDR)
	print ("Header Checksum:", HEADER_CHECKSUM)
	return HEADER_CHECKSUM

GLOBAL_CHECKSUM_MSB_ADDR = 0x014E
GLOBAL_CHECKSUM_LSB_ADDR = 0x014F
GLOBAL_CHECKSUM = None
def read_global_checksum():
	global GLOBAL_CHECKSUM
	msb = read_ROM(GLOBAL_CHECKSUM_MSB_ADDR)
	lsb = read_ROM(GLOBAL_CHECKSUM_LSB_ADDR)
	GLOBAL_CHECKSUM = (msb << 8) + lsb
	print ("ROM Checksum:", GLOBAL_CHECKSUM)
	return GLOBAL_CHECKSUM

def check_header_checksum():
	checksum = 0
	for address in range(0x0134, 0x014D):
		value = read_ROM(address)
		checksum -= value+1
	checksum &= 0xFF
	print ("Header Checksum (calculated):", checksum)
	assert checksum == HEADER_CHECKSUM

def save_ROM():
	assert ROM_SIZE != None
	rom = bytearray()

	if os.path.isfile("orig.gb"):
		with open("orig.gb", "rb") as f:
			orig = f.read()
	else:
		print("no orig.gb found for comparison")
		orig = None

	corrected = []
	different = []
	strange   = []

	for address in range(0, ROM_SIZE):
		if address % 16 == 0:
			print (len(corrected), len(different), len(strange))
			print (hex(address), end=": ")
		value = read_ROM(address)

		old_value = value
		if orig and value != orig[address]:
			select_ROM_bank(64)
			_ = read_ROM(address ^ 0xFFF)
			value = read_ROM(address)
			if value == orig:
				corrected.append(address)
			elif value == old_value:
				different.append(address)
			else:
				strange  .append(address)
			end = "!"
		else:
			end = " "
		print (hex(value)[2:].zfill(2), end=end)
		rom.append(value)
	with open("rom.gb","wb") as f:
		f.write(rom)

	print (corrected, different, strange)

def compare_to_ROM():
	with open("rom.gb", "rb") as f:
		rom = f.read()
	import random
	addr_and = -1
	addr_or  =  0
	while True:
		address = random.choice(range(ROM_SIZE))
		value = read_ROM(address)
		if value != rom[address]:
			addr_and &= address
			addr_or  |= address
			print (bin(address)[2:].zfill(20), bin(addr_and), bin(addr_or))

def fix_ROM_file():
	#addresses = [334, 335, 16021, 16023, 16037, 16039, 23905, 23907, 23928, 23930, 23937, 23939, 473632, 473634, 473754, 473756, 473765, 473767, 820344, 1045278, 1045280, 1045289, 1045291] + [45044, 60278, 62204, 63568, 64080, 82024, 82888, 82892, 82896, 105720, 126748, 191888, 198798, 228622, 228624, 230040, 231344, 231456, 233528, 234368, 244004, 247288, 258360, 258664, 259816, 259848, 273600, 304182, 330216, 339144, 409877, 419537, 419552, 423973, 432254, 445693, 446422, 446501, 446653, 454208, 459480, 461338, 461824, 467768, 494928, 498188, 524333, 524365, 524397, 538136, 547288, 547296, 558872, 558936, 565420, 592610, 608466, 614238, 615300, 616272, 617608, 617676, 624894, 663329, 712310, 720768, 802688, 819412, 820338, 820340, 820345, 827772, 828167, 834078, 835256, 837404, 844557, 844558, 854620, 856853, 856854, 868514, 868666, 868686, 877889, 877890, 877896, 877904, 881684, 892736, 905620, 905927, 913074, 913132, 921154, 921160, 921168, 928072, 954448, 960640, 976093, 988268, 994116, 994134, 1000448, 1001236, 1001248, 1004008, 1016088, 1018148, 1018676, 1022464, 1024787, 1033548, 1033552, 1033908, 1037184, 1037248, 1038844]
	addresses = [228624, 547296, 820340, 820344, 820345, 827772, 828167, 834078, 835256, 856854]
	addresses.sort()
	import collections
	values = collections.defaultdict(list)
	for i in range(10):
		print ("Round number",i)
		for addr in addresses:
			value = read_ROM(addr)
			values[addr].append(value)
			print (hex(addr)[2:].zfill(5), *[hex(x)[2:].zfill(2) for x in values[addr]])
	with open("rom.gb", "rb") as f:
		rom = f.read()
	rom = bytearray(rom)
	failed = []
	for addr in addresses:
		addr_values = values[addr]
		if min(addr_values) == max(addr_values):
			rom[addr] = addr_values[0]
			print ("fixed", addr)
		else:
			print ("failed", addr, addr_values)
			failed.append(addr)
	with open("rom_fixed.gb", "wb") as f:
		f.write(rom)
	print (failed)

# -------------------------------------------------------------------- #

def main():
	init_gpio()
	read_logo()
	read_title()
	read_version_number()
	read_licensee_code()
	read_destination_code()
	read_CGB_flag()
	read_SGB_flag()
	read_cartridge_type()
	read_ROM_size()
	read_RAM_size()
	read_header_checksum()
	check_header_checksum()
	read_global_checksum()

	#compare_to_ROM()

	input ("Press Enter to start copying ROM to file... ")
	save_ROM()
	#fix_ROM_file()
try:
	try:
		main()
	finally:
		gpio.cleanup()
except KeyboardInterrupt:
	print ("ended by keyboard interrupt")
else:
	print ("clean exit")
