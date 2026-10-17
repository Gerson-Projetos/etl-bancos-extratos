import unittest
from datetime import date
from decimal import Decimal

from Models.ExtratoItau import ExtratoItau
from Models.ExtratoMercadoPago import ExtratoMercadoPago
from Util.Util import Util


class TestEtapasUnit(unittest.TestCase):

    def setUp(self):
        self.util = Util()

    def test_model_hash_itau(self):
        """Etapa 4: Valida integridade e determinismo do hash do Itaú."""
        m1 = ExtratoItau(
            data_lancamento=date(2026, 1, 10),
            descricao="REND PAGO APLIC AUT MAIS",
            valor=10.50,
            saldo=1010.50
        )
        m2 = ExtratoItau(
            data_lancamento=date(2026, 1, 10),
            descricao="REND PAGO APLIC AUT MAIS",
            valor=10.50,
            saldo=1010.50
        )
        m3 = ExtratoItau(
            data_lancamento=date(2026, 1, 10),
            descricao="PIX TRANSF DIFERENTE",
            valor=10.50,
            saldo=1010.50
        )

        hash1 = m1.gerar_hash()
        hash2 = m2.gerar_hash()
        hash3 = m3.gerar_hash()

        self.assertEqual(len(hash1), 64)
        self.assertEqual(hash1, hash2, "Hashes para os mesmos dados devem ser idênticos")
        self.assertNotEqual(hash1, hash3, "Hashes para dados diferentes devem ser distintos")

    def test_model_hash_mercado_pago(self):
        """Etapa 4: Valida hash do Mercado Pago com e sem id_operacao."""
        m1 = ExtratoMercadoPago(
            data_lancamento=date(2026, 1, 2),
            descricao="Rendimentos",
            id_operacao="1738003634321",
            valor=4.44,
            saldo=9587.91
        )
        m2 = ExtratoMercadoPago(
            data_lancamento=date(2026, 1, 2),
            descricao="Rendimentos",
            id_operacao="1738003634321",
            valor=4.44,
            saldo=9587.91
        )
        m_sem_id = ExtratoMercadoPago(
            data_lancamento=date(2026, 1, 2),
            descricao="Rendimentos",
            id_operacao=None,
            valor=4.44,
            saldo=9587.91
        )

        h1 = m1.gerar_hash()
        h2 = m2.gerar_hash()
        h_sem_id = m_sem_id.gerar_hash()

        self.assertEqual(len(h1), 64)
        self.assertEqual(h1, h2)
        self.assertNotEqual(h1, h_sem_id)

    def test_util_converter_para_float(self):
        """Etapa 3 & 4: Valida conversão de moedas e formatos numéricos."""
        # Valores em formato string brasileiro com R$ e milhar
        self.assertEqual(self.util.converter_para_float("R$ 1.103,33"), 1103.33)
        self.assertEqual(self.util.converter_para_float("R$ 9.583,47"), 9583.47)
        self.assertEqual(self.util.converter_para_float("R$ -189,00"), -189.00)
        self.assertEqual(self.util.converter_para_float(" -32,95 "), -32.95)
        self.assertEqual(self.util.converter_para_float("4,36"), 4.36)

        # Já como float ou int
        self.assertEqual(self.util.converter_para_float(100.5), 100.5)
        self.assertEqual(self.util.converter_para_float(42), 42.0)

        # Valores nulos ou vazios
        self.assertIsNone(self.util.converter_para_float(None))
        self.assertIsNone(self.util.converter_para_float(""))
        self.assertIsNone(self.util.converter_para_float("   "))
        self.assertIsNone(self.util.converter_para_float("texto_invalido"))


if __name__ == "__main__":
    unittest.main()
