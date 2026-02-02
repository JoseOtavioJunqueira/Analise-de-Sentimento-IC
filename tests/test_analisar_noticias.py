"""
Testes das funções de normalização e deduplicação do pipeline de sentimento.
Não carrega o modelo BERT (apenas lógica auxiliar).
"""
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Garante import do módulo analisar_noticias (conftest já adiciona ROOT ao path)
from analisar_noticias import (
    carregar_noticias_existentes,
    limpar_arquivo_entrada,
    normalizar_data,
)


class TestNormalizarData:
    """Testes da função normalizar_data."""

    def test_none_retorna_none(self):
        assert normalizar_data(None) is None

    def test_string_vazia_retorna_none(self):
        assert normalizar_data("") is None

    def test_timestamp_10_digitos(self):
        # 1609459200 = 2021-01-01 00:00:00 UTC (aproximado)
        result = normalizar_data("1609459200")
        assert result is not None
        assert "2021" in result

    def test_timestamp_13_digitos(self):
        # 1609459200000 ms
        result = normalizar_data("1609459200000")
        assert result is not None
        assert "2021" in result


class TestCarregarNoticiasExistentes:
    """Testes da função carregar_noticias_existentes."""

    def test_arquivo_inexistente_retorna_dataframe_vazio_e_set_vazio(self):
        path_inexistente = os.path.join(tempfile.gettempdir(), "nao_existe_12345.json")
        df, titulos = carregar_noticias_existentes(path_inexistente)
        assert df.empty
        assert titulos == set()

    def test_arquivo_json_valido_retorna_df_e_titulos(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('[{"title": "Notícia A", "content": "Texto"}]')
            path = f.name
        try:
            df, titulos = carregar_noticias_existentes(path)
            assert len(df) == 1
            assert "Notícia A" in titulos
        finally:
            os.unlink(path)


class TestLimparArquivoEntrada:
    """Testes da função limpar_arquivo_entrada."""

    def test_limpar_escreve_lista_vazia(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('[{"x": 1}]')
            path = f.name
        try:
            limpar_arquivo_entrada(path)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert content.strip() == "[]"
        finally:
            os.unlink(path)
