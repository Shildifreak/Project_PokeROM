import time
import ctypes
libc = ctypes.CDLL('libc.so.6')

class Timespec(ctypes.Structure):
  """ timespec struct for nanosleep, see:
      http://linux.die.net/man/2/nanosleep """
  _fields_ = [('tv_sec', ctypes.c_long),
              ('tv_nsec', ctypes.c_long)]

libc.nanosleep.argtypes = [ctypes.POINTER(Timespec),
                           ctypes.POINTER(Timespec)]
nanosleep_req = Timespec()
nanosleep_rem = Timespec()

def nanosleep(ns):
  """ Delay nanoseconds with libc nanosleep() using ctypes. """
  s, ns = divmod(ns, int(1e9))
  nanosleep_req.tv_sec = s
  nanosleep_req.tv_nsec = ns

  libc.nanosleep(nanosleep_req, nanosleep_rem)

if __name__ == "__main__":
	t0 = time.time()
	nanosleep(500000000)
	t1 = time.time()
	print(t1 - t0)

	def nanosleep(ns):
		time.sleep(ns*1e-9)

	t0 = time.time()
	nanosleep(500000000)
	t1 = time.time()
	print(t1 - t0)



