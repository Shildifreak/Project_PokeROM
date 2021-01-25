import Adafruit_BBIO.GPIO as gpio

pins = [         # GND
	"P8_17", # AUDIO
	"P8_18", # RST
	"P8_12", # D_7
	"P8_11", # D_6
	"P8_21", # D_5
	"P8_22", # D_4
	"P8_23", # D_3
	"P8_24", # D_2
	"P8_25", # D_1
	"P8_26", # D_0
	"P8_27", # A_15
	"P8_28", # A_14
	"P8_29", # A_13
	"P8_30", # A_12
	"P8_31", # A_11
	"P8_32", # A_10
	"P8_33", # A_09
	"P8_34", # A_08
	"P8_35", # A_07
	"P8_36", # A_06
	"P8_37", # A_05
	"P8_38", # A_04
	"P8_39", # A_03
	"P8_40", # A_02
	"P8_41", # A_01
	"P8_42", # A_00
	"P8_43", # CS
	"P8_44", # R
	"P8_45", # W
	"P8_46", # CLK
]                # VCC

for pin in pins:
	gpio.setup(pin, gpio.IN, gpio.PUD_UP, delay=1)

for outpin in pins:
#	for pin in pins:
#		gpio.setup(pin, gpio.IN)
	gpio.setup(outpin, gpio.OUT)
	gpio.output(outpin, gpio.LOW)
	print (outpin, end=" ")
	for pin in pins:
		print (gpio.input(pin), end=" ")
	print ()
	gpio.setup(outpin, gpio.IN, gpio.PUD_UP)

try:
	while True:
		for pin in pins:
			print (gpio.input(pin), end=" ")
		print ()
except KeyboardInterrupt:
	pass

gpio.cleanup()
print ("clean exit")
