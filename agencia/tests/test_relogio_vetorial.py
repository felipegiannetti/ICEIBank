import threading
import unittest

from app.services.relogio_vetorial import RelacaoVetores, RelogioVetorial, comparar_vetores


class TestRelogioVetorial(unittest.TestCase):
    def test_evento_local_incrementa_apenas_a_propria_posicao(self):
        relogio = RelogioVetorial(id_agencia=1, numero_agencias=3)
        self.assertEqual(relogio.evento_local(), [0, 1, 0])
        self.assertEqual(relogio.evento_local(), [0, 2, 0])

    def test_ao_enviar_incrementa_e_retorna_o_vetor_inteiro(self):
        relogio = RelogioVetorial(id_agencia=0, numero_agencias=3)
        relogio.evento_local()
        self.assertEqual(relogio.ao_enviar(), [2, 0, 0])

    def test_ao_receber_faz_o_maximo_posicao_a_posicao_e_incrementa_a_propria(self):
        # Agencia 1 recebe uma mensagem da agencia 0, que ja estava em [3, 0, 0].
        relogio = RelogioVetorial(id_agencia=1, numero_agencias=3)
        relogio.evento_local()  # [0, 1, 0]
        vetor = relogio.ao_receber([3, 0, 0])
        self.assertEqual(vetor, [3, 2, 0])

    def test_sequencia_identica_ao_exemplo_do_roteiro(self):
        # Replica a sequencia de chamadas do roteiro do Sprint 2 (secao 9.1)
        # e confirma que produz os mesmos vetores que os exemplos em
        # Node/Java/Python la descritos.
        agencia0 = RelogioVetorial(id_agencia=0, numero_agencias=3)
        agencia1 = RelogioVetorial(id_agencia=1, numero_agencias=3)

        self.assertEqual(agencia0.evento_local(), [1, 0, 0])
        self.assertEqual(agencia1.evento_local(), [0, 1, 0])
        vetor_envio = agencia0.ao_enviar()
        self.assertEqual(vetor_envio, [2, 0, 0])
        self.assertEqual(agencia1.ao_receber(vetor_envio), [2, 2, 0])

    def test_concorrencia_de_threads_nao_perde_incremento(self):
        relogio = RelogioVetorial(id_agencia=0, numero_agencias=2)
        n_threads, n_eventos = 10, 200

        def trabalhar():
            for _ in range(n_eventos):
                relogio.evento_local()

        threads = [threading.Thread(target=trabalhar) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(relogio.evento_local()[0], n_threads * n_eventos + 1)


class TestCompararVetores(unittest.TestCase):
    def test_antes(self):
        # Exemplo do roteiro (secao 6.4, pergunta 2): V1=[3,1,0], V2=[3,2,0].
        self.assertEqual(comparar_vetores([3, 1, 0], [3, 2, 0]), RelacaoVetores.ANTES)

    def test_depois_e_o_espelho_de_antes(self):
        self.assertEqual(comparar_vetores([3, 2, 0], [3, 1, 0]), RelacaoVetores.DEPOIS)

    def test_concorrentes(self):
        # Exemplo do roteiro (secao 6.4, pergunta 3): V1=[3,1,0], V2=[1,3,0].
        self.assertEqual(comparar_vetores([3, 1, 0], [1, 3, 0]), RelacaoVetores.CONCORRENTES)

    def test_iguais(self):
        self.assertEqual(comparar_vetores([2, 2, 2], [2, 2, 2]), RelacaoVetores.IGUAIS)


if __name__ == "__main__":
    unittest.main()
