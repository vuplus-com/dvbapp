#include <lib/driver/memtest.h>
#include <errno.h>
#include <lib/base/eerror.h>
#include <lib/base/estring.h>

#define TESTSIZE 32*1024

eMemtest *eMemtest::instance;

eMemtest::eMemtest()
{
	instance = this;

}

eMemtest::~eMemtest()
{
	instance=NULL;

}
/*
*	return value
*	0 - ok
*	1 - fail
*/
int eMemtest::dramtest()
{
	int result=0;
	int i;
	char memt[TESTSIZE];
	eDebug("dramtest start");

	
	for(i=0;i<TESTSIZE;i++)
		memt[i]=0x13;
	
	for(i=0;i<TESTSIZE;i++)
	{
		if(memt[i]!=0x13)
		{
			result=1;
			break;
		}
	}
	
	return result;
		
}

int eMemtest::flashtest()
{
	int result=0;
	
	return result;
}
