from __future__ import print_function
from multiprocessing import Process, Queue
from types import SimpleNamespace as Namespace
import requests, json, time


class Bot:
	def __init__(self, token, workers=10):
		self.base_url = f'https://api.telegram.org/bot{token}/'
		self.workers = {}
		self.req = requests.Session() # Used to get new updates
		self.create_workers(workers) 

	def create_workers(self, workers):
		processes = []
		for n in range(workers):
			q = Queue() # Where the update will be stored, each worker has his own 
			s = requests.Session() # Each worker has his own request instance
			p = Process(target=self.process_update, args=(q,n,))
			processes.append(p)
			self.workers[n] = {'session's:'update':q}
		[x.start() for x in processes] # Starting all workers

	def process_update(self, q, num):
		ses = self.workers[num]['session']
		while 1:
			if not q.empty(): # If there is an update passed to the Queue of this worker
				update = q.get() # Get and remove it
				self.filter(update, ses) 

	def filter(self, update, ses):
		"""
		Filter updates

		param update: update object
		param ses: session requests
		"""
		chat_id = update.message.chat.id
		message = update.message.text
		ses.get(self.base_url+f'sendMessage?chat_id={chat_id}&text={message}')

	def send(self, worker, update):
		# Update Queue of the given worker with the given update
		self.workers[worker]['update'].put(update)
		return True

	def get_updates(self, timeout, offset=0):
		"""
		To get_updates from telegram 

		return update object
		"""
		res = self.req.get(self.base_url+'getUpdates'+f'?offset={offset}&timeout={timeout}')
		data = res.text
		updates = json.loads(data, object_hook=lambda d: X(**d)) # Convert json to object
		if not updates.ok:
			return False
		return updates.result

	def start_polling(self, timeout=5, clear=False):
		"""
		Long polling function that get updates and
		pass them to process_updates() func.

		param timeout: int ... 10
		param clear: bool 
		"""
		offset = 0

		# Clear updates
		if clear:
			offset = self.get_updates(timeout=timeout)[-1].update_id + 1

		# Long Polling
		while 1:
			updates = self.get_updates(timeout=timeout, offset=offset)

			if updates:
				for update in updates:
					done = False
					while not done:
						for key, value in self.workers.items():
							if value['update'].empty():
								worker = key 
								self.send(worker, update)
								done = True
								break


				offset = updates[-1].update_id + 1
			else:
				pass
			


if __name__ == '__main__':
	a = Bot('BOT_TOKEN')
	a.start_polling()