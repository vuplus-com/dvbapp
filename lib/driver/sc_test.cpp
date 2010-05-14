#include <lib/dvb/dvb.h>
#include <lib/dvb/frontendparms.h>

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/poll.h>
#include <fcntl.h>
#include <time.h>
#include <unistd.h>
#include <termios.h>
#include <lib/driver/sc_test.h>
#include <errno.h>
#include <lib/base/eerror.h>
#include <lib/base/estring.h>

#include <stdint.h>
#include <sys/time.h>
#include <poll.h>


#define SC_CHECK_TIMEOUT	5
#define SC_REMOVE_TIMEOUT	10


#define SMART_CARD0	"/dev/sci0"			/* upper smart card */
#define SMART_CARD1	"/dev/sci1"			/* lower smart card */

#define SC_SUCCESS			0
#define NO_DEV_FOUND		-1
#define SC_NOT_INSERTED	-2
#define SC_NOT_VALID_ATR	-3
#define SC_NOT_REMOVED		-4
#define SC_READ_TIMEOUT	-5


#define SCI_IOW_MAGIC			's'

/* ioctl cmd table */
//#include "sci_global.h"
#define IOCTL_SET_RESET			_IOW(SCI_IOW_MAGIC, 1,  unsigned long)
#define IOCTL_SET_MODES			_IOW(SCI_IOW_MAGIC, 2,  SCI_MODES)
#define IOCTL_GET_MODES			_IOW(SCI_IOW_MAGIC, 3,  SCI_MODES)
#define IOCTL_SET_PARAMETERS		_IOW(SCI_IOW_MAGIC, 4,  SCI_PARAMETERS)
#define IOCTL_GET_PARAMETERS		_IOW(SCI_IOW_MAGIC, 5,  SCI_PARAMETERS)
#define IOCTL_SET_CLOCK_START		_IOW(SCI_IOW_MAGIC, 6,  unsigned long)
#define IOCTL_SET_CLOCK_STOP		_IOW(SCI_IOW_MAGIC, 7,  unsigned long)
#define IOCTL_GET_IS_CARD_PRESENT	_IOW(SCI_IOW_MAGIC, 8,  unsigned long)
#define IOCTL_GET_IS_CARD_ACTIVATED	_IOW(SCI_IOW_MAGIC, 9,  unsigned long)
#define IOCTL_SET_DEACTIVATE		_IOW(SCI_IOW_MAGIC, 10, unsigned long)
#define IOCTL_SET_ATR_READY		_IOW(SCI_IOW_MAGIC, 11, unsigned long)
#define IOCTL_GET_ATR_STATUS		_IOW(SCI_IOW_MAGIC, 12, unsigned long)
#define IOCTL_DUMP_REGS			_IOW(SCI_IOW_MAGIC, 20, unsigned long)

eSctest *eSctest::instance;

eSctest::eSctest()
{
	instance = this;

}

eSctest::~eSctest()
{
	instance=NULL;

}

int eSctest::n_check_smart_card(char *dev_name)
{
	int fd;
	struct pollfd pollfd;
	unsigned char buf[64];
	int cnt = 0;
	int modem_status;
	int count = SC_CHECK_TIMEOUT;
	int readok=0;
	
	fd = ::open(dev_name, O_RDWR);
	
	if(fd < 0){
		eDebug("sci0 open error\n");
		return NO_DEV_FOUND;
	}
	else
		eDebug("sci0 is opened fd : %d\n", fd);


	::ioctl(fd, IOCTL_GET_IS_CARD_PRESENT, &modem_status);

	if( modem_status )
		eDebug("card is now inserted\n");
	else
	{
		eDebug("card is NOT inserted\n");
		::close(fd);
		return SC_NOT_INSERTED;
	}

	/* now smart card is inserted, let's do reset */

	::ioctl(fd, IOCTL_SET_RESET, &modem_status);

	/* now we can get the ATR */

	pollfd.fd = fd;
	pollfd.events = POLLIN|POLLOUT|POLLERR|POLLPRI;


	while(poll(&pollfd, 1, 1000)>=0 && count--){

		eDebug("pollfd.revents : 0x%x\n", pollfd.revents);
		if(pollfd.revents & POLLIN){
			eDebug(">>read \n");
			cnt = read(fd, buf, 64);
			eDebug("<<read cnt:%d\n", cnt);			
			if(cnt) 
			{
				if(buf[0]==0x3b||buf[0]==0x3f)
				{
					eDebug("read -%d : 0x%x",cnt, buf[0]);
					readok = 1;
				}
				break;
			}
			else
				eDebug("no data\n");
		}
	}

	::close(fd);
	
	if (readok == 0) return SC_NOT_VALID_ATR;
	if(!count) return SC_READ_TIMEOUT;
	return SC_SUCCESS;
}

int eSctest::check_smart_card(char *dev_name)
{
	int fd;
	struct pollfd pollfd;
	unsigned char buf[64];
	int cnt = 0;
	int modem_status;
	int count = SC_CHECK_TIMEOUT;
	int readok=0;
	fd = ::open(dev_name, O_RDWR);
	
	if(fd < 0){
		eDebug("sci0 open error");
		return NO_DEV_FOUND;
	}
	else
		eDebug("sci0 is opened fd : %d", fd);

	::tcflush(fd, TCIFLUSH);

	::ioctl(fd, TIOCMGET, &modem_status);

	if( modem_status & TIOCM_CAR)
		eDebug("card is now inserted");
	else
	{
		eDebug("card is NOT inserted");
		close(fd);
		return SC_NOT_INSERTED;
	}

	/* now smart card is inserted, let's do reset */

	modem_status |= TIOCM_RTS;
	::ioctl(fd, TIOCMSET, &modem_status);

	modem_status &= ~TIOCM_RTS;
	::ioctl(fd, TIOCMSET, &modem_status);


	/* now we can get the ATR */

	pollfd.fd = fd;
	pollfd.events = POLLIN|POLLOUT|POLLERR|POLLPRI;


	while(poll(&pollfd, 1, 1000)>=0 && count--){

		eDebug("pollfd.revents : 0x%x %d", pollfd.revents,count);
		if(pollfd.revents & POLLIN){
			eDebug(">>read ");
			cnt = ::read(fd, buf, 64);
			eDebug("<<read cnt:%d", cnt);
			if(cnt) 
			{
				int i;
				for( i = 0 ; i < cnt ; i ++)
				{
					if(buf[i]!=0x0)
						readok = 1;
					eDebug("read : 0x%x", buf[i]);
				}
				break;
			}
			else
				eDebug("no data");
		}
	}
	
	::close(fd);
	eDebug("readok = %d",readok);
	if (readok == 0) return SC_NOT_VALID_ATR;
	if(count<=0 ) return SC_READ_TIMEOUT;
	return SC_SUCCESS;
}
int eSctest::eject_smart_card(char *dev_name)
{
	int fd;
	struct pollfd pollfd;
	unsigned char buf[64];
	int cnt = 0;
	int modem_status;
	int count = SC_CHECK_TIMEOUT;
	
	fd = ::open(dev_name, O_RDWR);
	
	if(fd < 0){
		eDebug("sci0 open error");
		return NO_DEV_FOUND;
	}
	else
		eDebug("sci0 is opened fd : %d", fd);

	::tcflush(fd, TCIFLUSH);

	::ioctl(fd, TIOCMGET, &modem_status);

	if( modem_status & TIOCM_CAR)
		eDebug("card is now inserted");
	else
	{
		eDebug("card is NOT inserted");
		close(fd);
		return SC_NOT_INSERTED;
	}
	/* now we can get the ATR */

	pollfd.fd = fd;
	pollfd.events = POLLIN|POLLOUT|POLLERR|POLLPRI;

	/* let's wait until card is removed for count secs.*/
	count = SC_REMOVE_TIMEOUT;	
	do{
		::ioctl(fd, TIOCMGET, &modem_status);
		eDebug("modem_status : 0x%x %d", modem_status,count);
		sleep(1);	

	}
	while((modem_status&TIOCM_CAR) && count--);

	if(count<=0 ) return SC_NOT_REMOVED;
	
	::close(fd);		
	return SC_SUCCESS;
}


int eSctest::VFD_Open()
{
	VFD_fd = open("/dev/dbox/lcd0", O_RDWR);
	return VFD_fd;
}

int eSctest::turnon_VFD()
{ 
	ioctl(VFD_fd, 0xa0a0a0a0, 0);
}

int eSctest::turnoff_VFD()
{
	ioctl(VFD_fd, 0x01010101, 0);	
}

void eSctest::VFD_Close()
{
	close(VFD_fd);
}

extern int frontend0_fd;
extern int frontend1_fd;

int eSctest::getFrontendstatus(int fe)
{
	fe_status_t status;

	int m_fd;
	int res;

	if (fe == 0)
		m_fd = frontend0_fd;
	else if (fe==1)
		m_fd = frontend1_fd;
	else 
		return -1;

	if (m_fd < 0)
	{
		eDebug("%d open error ",fe);
		return -1;
	}
	else
		eDebug("%d open ok!!!! ",m_fd);
	
	if ( ioctl(m_fd, FE_READ_STATUS, &status) < 0)
		eDebug("%d read error ",fe);		

	if (status&FE_HAS_LOCK)
		return 1;
	else
		return 0;

}

