import anyio as _anyio
from aevent import patch_ as _patch, await_ as _await

from queue import Queue

@_patch
class Queue:
	_size = 0
	_q_r,_q_w = None,None
	_count = 0
	_count_zero = None

	def __init__(self, maxsize=1):
		self._size = maxsize

	def qsize(self):
		return self._size


	def get(self, block=True, timeout=None):
		return _await(self._get(block, timeout))
	
	async def _get(self, block, timeout):
		if self._q_r is None:
			self._q_w,self._q_r = _anyio.create_memory_object_stream(self._size)
		if not block:
			timeout = 0.01 # TODO
		if timeout is None:
			return await self._q_r.receive()
		else:
			async with _anyio.fail_after(timeout):
				return await self._q_r.receive()


	def put(self, item, timeout=None):
		_await(self._put(item,timeout))
	
	async def _put(self, item, timeout):
		self._count += 1
		try:
			if self._q_r is None:
				self._q_w,self._q_r = _anyio.create_memory_object_stream(self._size)
			if timeout is None:
				await self._q_w.send(item)
			else:
				async with _anyio.fail_after(timeout):
					await self._q_w.send(item)
		except BaseException:
			await self._task_done()
			raise

	
	def task_done(self):
		_await(self._task_done())

	async def _task_done(self):
		if self._count > 0:
			self._count -= 1
		if self._count == 0 and self._count_zero is not None:
			await self._count_zero.set()
	

	def join(self):
		_await(self._join())
	
	async def _join(self):
		if self._count > 0:
			if self._count_zero is None or self._count_zero.is_set():
				self._count_zero = _anyio.create_event()
			await self._count_zero.wait()

