#ifdef BUILD_VUPLUS /* ikseong  */
#ifndef __memtest_h
#define __memtest_h

#include <lib/base/object.h>
#include <lib/python/connections.h>

class eMemtest
{
	static eMemtest *instance;
public:
	eMemtest();
	~eMemtest();
	int dramtest();
	int flashtest();
	static eMemtest *getInstance() { return instance; }

};
#endif
#endif

