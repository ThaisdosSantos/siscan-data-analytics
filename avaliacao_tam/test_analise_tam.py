"""Conferências reproduzíveis para a versão original do formulário de 2026."""
import unittest

from analise_tam import (
    ler_bases, analise_construtos, analise_funcionalidades, dificuldades,
    CONSTRUTOS, codificar, alpha_cronbach,
)


class TesteAvaliacaoTAM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bruto, cls.consentidos, cls.elegiveis = ler_bases()

    def test_selecao_amostral(self):
        self.assertEqual(len(self.bruto), 43)
        self.assertEqual(len(self.consentidos), 42)
        self.assertEqual(len(self.elegiveis), 41)

    def test_itens_tam(self):
        c, i, escores = analise_construtos(self.elegiveis)
        self.assertEqual(len(i), 16)
        self.assertEqual(sum(len(x) for x in CONSTRUTOS.values()), 16)
        self.assertEqual(int(c['n participantes'].min()), 41)
        self.assertFalse(escores.isna().any().any())
        self.assertAlmostEqual(c.loc[0, 'Média'], 4.570731707317074, places=5)
        self.assertAlmostEqual(c.loc[1, 'Alfa de Cronbach'], 0.9319, places=3)

    def test_pu_indicadores_passos(self):
        import pandas as pd
        _, itens, escores = analise_construtos(self.elegiveis)
        bloco = pd.DataFrame({
            f"PU{j}": codificar(self.elegiveis.iloc[:, ind])
            for j, ind in enumerate(CONSTRUTOS["PU"], start=1)
        })
        self.assertEqual(int(bloco.isin([4, 5]).sum().sum()), 193)
        self.assertEqual(int(bloco.notna().sum().sum()), 205)
        self.assertAlmostEqual(100 * 193 / 205, 94.146341, places=5)
        self.assertAlmostEqual(escores["PU"].mean(), 4.5707317, places=6)
        self.assertAlmostEqual(escores["PU"].median(), 4.80, places=6)
        soma_var = bloco.var(axis=0, ddof=1).sum()
        var_soma = bloco.sum(axis=1).var(ddof=1)
        calculo = 5/4 * (1 - soma_var / var_soma)
        self.assertAlmostEqual(calculo, alpha_cronbach(bloco), places=10)
        self.assertAlmostEqual(calculo, 0.932420, places=5)

    def test_funcionalidades_nao_se_aplica(self):
        func = analise_funcionalidades(self.elegiveis)
        self.assertEqual(len(func), 8)
        exportacao = func.loc[func['Código'] == 'F7'].iloc[0]
        self.assertEqual(int(exportacao['n válido']), 27)
        self.assertEqual(int(exportacao['Não utilizou (n)']), 14)

    def test_dificuldades(self):
        tabela, inconsistencias = dificuldades(self.elegiveis)
        self.assertEqual(inconsistencias, 1)
        self.assertEqual(int(tabela.loc[
            tabela['Dificuldade'].str.startswith('Tive dificuldades para utilizar os filtros'), 'n'
        ].iloc[0]), 7)


if __name__ == '__main__':
    unittest.main()
