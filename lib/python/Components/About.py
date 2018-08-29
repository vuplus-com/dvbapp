from Tools.Directories import resolveFilename, SCOPE_SYSETC
from enigma import getEnigmaVersionString
from os import popen

class About:
	def __init__(self):
		pass

	def getVersionString(self):
		return self.getImageVersionString()

	def getImageVersionString(self):
		try:
			file = open(resolveFilename(SCOPE_SYSETC, 'image-version'), 'r')
			lines = file.readlines()
			for x in lines:
				splitted = x.split('=')
				if splitted[0] == "version":
					#     YYYY MM DD hh mm
					#0120 2005 11 29 01 16
					#0123 4567 89 01 23 45
					version = splitted[1]
					image_type = version[0] # 0 = release, 1 = experimental
					major = version[1]
					minor = version[2]
					revision = version[3]
					year = version[4:8]
					month = version[8:10]
					day = version[10:12]
					date = '-'.join((year, month, day))
					if image_type == '0':
						image_type = "Release"
						version = '.'.join((major, minor, revision))
						return ' '.join((image_type, version, date))
					else:
						image_type = "Experimental"
						return ' '.join((image_type, date))
			file.close()
		except IOError:
			pass

		return "unavailable"

	def getEnigmaVersionString(self):
		return getEnigmaVersionString()

	def getKernelVersionString(self):
		try:
			result = popen("uname -r","r").read().strip("\n").split('-')
			kernel_version = result[0]
			return kernel_version
		except:
			pass

		return "unknown"

	def getIfaces(self):
		import socket, fcntl, struct, array, sys
		SIOCGIFCONF = 0x8912 # sockios.h
		is_64bits = sys.maxsize > 2**32
		struct_size = 40 if is_64bits else 32
		max_possible = 8 # initial value
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		while True:
			# ifconf structure:
			# struct ifconf {
			#		int			ifc_len; /* size of buffer */
			# 		union {
			# 			char 		*ifc_buf; /* buffer address */
			#			struct ifreq	*ifc_req; /* array of structures */
			# 		};
			# 	};
			#
			# struct ifreq:
			# #define IFNAMSIZ	16
			# struct ifreq {
			# 	char ifr_name[IFNAMSIZ]; /* Interface name */
			# 	union {
			# 		struct sockaddr ifr_addr;
			# 		.....
			# 	};
			# };

			# Initialize ifc_buf
			bytes = max_possible * struct_size
			names = array.array('B')
			for i in range(0, bytes):
				names.append(0)

			input_buffer = struct.pack( 'iL', bytes, names.buffer_info()[0] )
			output_buffer = fcntl.ioctl( sock.fileno(), SIOCGIFCONF, input_buffer )
			output_size = struct.unpack('iL', output_buffer)[0]

			if output_size == bytes:
				max_possible *= 2
			else:
				break

		namestr = names.tostring()
		ifaces = []
		for i in range(0, output_size, struct_size):
			iface_name = namestr[i:i+16].split('\0', 1)[0]
			iface_addr = socket.inet_ntoa(namestr[i+20:i+24])
			if iface_name != 'lo':
				ifaces.append((iface_name, iface_addr))

		return ifaces

	def getNetworkInfo(self):
		data = ""
		for x in self.getIfaces():
			data += "%s : %s\n" % (x[0], x[1])
		return data or "\tnot connected"

about = About()
