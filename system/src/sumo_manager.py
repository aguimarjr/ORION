#!/usr/bin/env python
# title: sumo_manager.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 30.03.2021



import _thread
import socket
import os
import time
import sys
import signal

if 'SUMO_HOME' in os.environ:
	tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
	sys.path.append(tools)
else:
	sys.exit("Environment variable SUMO_HOME not defined")

class UnusedPortLock:
	"""
	Classe de bloqueio para sincronizar a busca por portas livres entre threads.

	A classe encapsula um lock global (`lock`) para garantir exclusão mútua
	em operações críticas, como a seleção de portas TCP disponíveis.
	Também mantém um estado interno (`acquired`) para evitar aquisições
	e liberações redundantes do lock.

	Métodos:
		- __init__(): Inicializa o estado de aquisição do lock.
		- __enter__(): Adquire o lock ao entrar no contexto `with`.
		- __exit__(): Libera o lock ao sair do contexto `with`.
		- acquire(): Adquire o lock global se ainda não estiver adquirido.
		- release(): Libera o lock global se estiver adquirido.

	Atributos:
		- lock (_thread.lock): Lock compartilhado entre instâncias da classe.
		- acquired (bool): Indica se a instância atual está com o lock adquirido.
	"""
	lock = _thread.allocate_lock()

	def __init__(self):
		"""
		Inicializa a instância com o lock não adquirido.
		"""
		self.acquired = False

	def __enter__(self):
		"""
		Adquire o lock ao entrar em um bloco de contexto.

		Side Effects:
			- Pode bloquear a execução até que o lock global esteja disponível.
			- Atualiza `acquired` para `True` quando a aquisição ocorrer.
		"""
		self.acquire()

	def __exit__(self):
		"""
		Libera o lock ao sair de um bloco de contexto.

		Side Effects:
			- Atualiza `acquired` para `False` quando a liberação ocorrer.
		"""
		self.release()

	def acquire(self):
		"""
		Adquire o lock global se esta instância ainda não o tiver adquirido.

		Side Effects:
			- Chama `UnusedPortLock.lock.acquire()`.
			- Define `acquired` como `True` após a aquisição.
		"""
		if not self.acquired:
			UnusedPortLock.lock.acquire()
			self.acquired = True

	def release(self):
		"""
		Libera o lock global se esta instância o tiver adquirido.

		Side Effects:
			- Chama `UnusedPortLock.lock.release()`.
			- Define `acquired` como `False` após a liberação.
		"""
		if self.acquired:
			UnusedPortLock.lock.release()
			self.acquired = False


def find_unused_port():
	"""
	Encontra uma porta TCP disponível no host local.

	A função abre um socket em `127.0.0.1` com porta `0`, permitindo que o
	sistema operacional selecione automaticamente uma porta livre. Em seguida,
	o socket é fechado e o número da porta é retornado.

	Returns:
		int: Número da porta TCP disponível no momento da verificação.

	Observação:
		A disponibilidade da porta não é garantida após o fechamento do socket,
		pois outro processo pode ocupá-la em seguida.
	"""
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
	sock.bind(('127.0.0.1', 0))
	sock.listen(socket.SOMAXCONN)
	ipaddr, port = sock.getsockname()
	sock.close()
	
	return port

def terminate_sumo(sumo):
	"""
	Encerra um processo SUMO de forma progressiva.

	A função tenta finalizar o processo usando sinais em etapas:
	1) `SIGTERM` para encerramento gracioso;
	2) `SIGKILL` caso o processo continue em execução.
	
	Args:
		sumo: Objeto de processo (ex.: `subprocess.Popen`) com os atributos
			`pid` e `returncode`.

	Side Effects:
		- Envia sinais de término para o processo identificado por `sumo.pid`.
		- Aguarda entre tentativas com `time.sleep`.
	"""
	if sumo.returncode == None:
		os.kill(sumo.pid, signal.SIGTERM)
		time.sleep(0.5)
		if sumo.returncode == None:
			os.kill(sumo.pid, signal.SIGKILL)
			time.sleep(1)
			if sumo.returncode == None:
				time.sleep(2)
