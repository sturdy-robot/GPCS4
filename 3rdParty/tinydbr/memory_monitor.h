#pragma once

#include <cstdint>
#include <memory>

#include "structure.h"

class MemoryMonitorImpl;

enum MonitorFlag : uint64_t
{
	IgnoreCode        = 1 << 0,  // e.g. call [0x1234], jmp [0x1234]
	IgnoreStack       = 1 << 1,  // e.g. mov rax, [rsp + 0x8]
	IgnoreRipRelative = 1 << 2,  // e.g. mov rax, [rip + 0x8]

	// save processor extended states, e.g. xmm, ymm, fpu, mxcsr
	// before call into user callback.
	SaveExtendedState = 1 << 3,  // this is a very costive operation which will slow down the program severely
};

typedef uint64_t MonitorFlags;

// Library users should inherit this interface
class MemoryCallback
{
public:
	virtual ~MemoryCallback();

	// memory read callback
	// this will be called before the read instruction,
	// so you can prepare the memory for the target program to read
	virtual void OnMemoryRead(void* address, size_t size) = 0;

	// memory write callback
	// this will be called after the write instruction
	// so you can get the memory content been written by the target program
	virtual void OnMemoryWrite(void* address, size_t size) = 0;
};

class MemoryMonitor
{
public:
	MemoryMonitor(MonitorFlags flags, MemoryCallback* callback);
	~MemoryMonitor();

	void Init(const std::vector<TargetModule>& target_modules,
			  const Options&                   options);

	void Unit();

private:
	
	std::unique_ptr<MemoryMonitorImpl> m_impl;
};

