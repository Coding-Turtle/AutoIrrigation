#Queue Class
from collections import deque


class Queue():
	def __init__(self):
		self.queue = deque()

	def __len__(self):
		return len(self.queue)
	
	def enqueueUnique(self,deviceName):
		rc = None
		if self.queue.count(deviceName) == 0:
			self.queue.append(deviceName)
			rc = 1
			print("adding unique load")
		else:
			rc = 0
			print("duplicate not adding to queue")
		return rc

	def dequeue(self):
		rc = -1
		if len(self) > 0:
			rc = self.queue.popleft()
		return rc

	#def remove(self,deviceName):
	#	self.queue.remove(deviceName)
	
	def peakFront(self):
		rc = -1
		if self.__len__() == 0:
			print("Empty Queue")
		else:
			rc = self.queue[0]
			print(self.queue[0])
		return rc

	def addLoad(self,jobList):
		for x in jobList:
			print(f"adding {x} to load")
			self.enqueueUnique(x)
	
