import threading


class RelogioLamport:
    def __init__(self):
        self._contador = 0
        self._lock = threading.Lock()

    def evento_local(self) -> int:
        with self._lock:
            self._contador += 1
            return self._contador

    def ao_enviar(self) -> int:
        with self._lock:
            self._contador += 1
            return self._contador

    def ao_receber(self, timestamp_recebido: int) -> int:
        with self._lock:
            self._contador = max(self._contador, timestamp_recebido) + 1
            return self._contador
