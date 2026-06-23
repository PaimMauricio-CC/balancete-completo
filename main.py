import pandas as pd
import sys
import logging
import re
import chardet
from utils import normalizar_mascara, extrair_conta_corrente, limpar_saldo, corrigir_tipo, normalizar_conta_tce, converter_notacao_cientifica,remover_sinal_negativo, ajustar_saldo, normalizar_conta_corrente_comparacao
# Processamento Analítico
def process_analitico(saldo_type="atual"):
    print(f"Iniciando processamento no modo Analítico com Saldo {saldo_type.capitalize()}...")
    
    # Carregar arquivos CSV
    df_betha = pd.read_csv('uploads/betha.csv', sep=';', dtype={'descrição': str}, encoding='utf-8')
    df_tce = pd.read_csv('uploads/tce.csv', sep=';', skiprows=5, dtype={'Nome Conta': str}, encoding='ISO-8859-1')

    # Corrigir o tipo das contas no DataFrame Betha
    df_betha = corrigir_tipo(df_betha)

    # ------ Processamento do Betha ------
    # Filtrar apenas as máscaras analíticas (remover as sintéticas)
    df_betha = df_betha[df_betha['Tipo'] == 'Analitica']

    # Normalizar máscaras
    df_betha['Máscara Normalizada'] = df_betha['Máscara'].apply(normalizar_mascara)

    # Substituir NaN na coluna "Máscara Normalizada" com base na última máscara válida
    ultima_mascara_valida = None
    mascaras_preenchidas = []
    for mascara in df_betha['Máscara Normalizada']:
        if mascara is not None:
            ultima_mascara_valida = mascara  # Atualiza a última máscara válida
        mascaras_preenchidas.append(ultima_mascara_valida)
    df_betha['Máscara Normalizada'] = mascaras_preenchidas

    # Criar uma nova coluna "Conta Corrente" aplicando a função
    df_betha['Conta Corrente'] = df_betha['Descrição'].apply(extrair_conta_corrente)
    df_betha['Conta Corrente'] = df_betha['Conta Corrente'].apply(normalizar_conta_corrente_comparacao)

    # Limpar e converter saldos para float (baseado no tipo de saldo escolhido)
    if saldo_type == "atual":
        saldo_coluna = 'Saldo atual'
        df_betha[saldo_coluna] = df_betha['Saldo atual'].apply(limpar_saldo)
    elif saldo_type == "anterior":
        saldo_coluna = 'Saldo anterior'
        df_betha[saldo_coluna] = df_betha['Saldo anterior'].apply(limpar_saldo)
    else:
        raise ValueError("Tipo de saldo inválido. Use 'atual' ou 'anterior'.")

    # Limpar e converter saldos no Betha
    df_betha['Saldo atual'] = df_betha['Saldo atual'].apply(limpar_saldo)
    df_betha['Saldo anterior'] = df_betha['Saldo anterior'].apply(limpar_saldo)
    # PEGAR O SEGUNDO TIPO SALDO QUE FICA 4 POSIÇÕES DEPOIS DO PRIMEIRO
    if (saldo_type == "atual"):
        df_betha['Tipo Saldo'] = df_betha.iloc[:, df_betha.columns.get_loc("Tipo Saldo") + 4]
    else: 
        df_betha['Tipo Saldo'] = df_betha.iloc[:, df_betha.columns.get_loc("Tipo Saldo")]
    
    # ADIÇÃO PARA CONSIDERAR CRÉDITO E DÉBITO
    #df_betha['Saldo Ajustado'] = df_betha.apply(ajustar_saldo, axis=1)
    # Aplicar a função ajustar_saldo para criar a coluna 'Saldo Ajustado'
    df_betha['Saldo Ajustado'] = df_betha.apply(ajustar_saldo, axis=1, saldo_type="atual")

    # FILTRO ADICIONAL: Remover contas correntes que não contêm números
    def contem_numeros(texto):
        """Verifica se o texto contém pelo menos um número."""
        if pd.isna(texto):  # Ignora valores NaN
            return False
        return bool(re.search(r'\d', str(texto)))  # Retorna True se houver pelo menos um número

    def parece_conta_corrente_tce(texto):
        """Remove linhas analíticas do TCE que usam descrição textual no lugar da conta corrente."""
        if pd.isna(texto):
            return False

        valor = str(texto).strip()
        if not valor:
            return False
        if valor[0].isalpha():
            return False
        if re.match(r'^\d+\.\s*[^\d\s]', valor):
            return False
        return True

    # Aplicar o filtro para remover contas correntes que são apenas texto
    df_betha = df_betha[df_betha['Conta Corrente'].apply(contem_numeros)]

    # Manter apenas as linhas detalhadas. A máscara original vem vazia nessas linhas,
    # e a coluna "Máscara Normalizada" já recebeu a última máscara analítica válida.
    df_betha = df_betha[df_betha['Máscara'].isna()]

    # Selecionar colunas relevantes para o DataFrame tratado
    colunas_tratadas_betha = ['Máscara Normalizada', 'Conta Corrente', saldo_coluna, 'Saldo Ajustado']
    df_betha_tratado = df_betha[colunas_tratadas_betha]

    # Agrupar por máscara e conta corrente e somar os saldos
    df_betha_agrupado = df_betha_tratado.groupby(['Máscara Normalizada', 'Conta Corrente'], as_index=False).agg({
        'Saldo Ajustado': 'sum'
    })
    # Renomear colunas para consistência
    df_betha_agrupado.rename(columns={
        'Saldo Ajustado': 'Saldo_atual_Betha'
    }, inplace=True)

    df_betha_agrupado['Saldo_atual_Betha'] = df_betha_agrupado['Saldo_atual_Betha'].apply(remover_sinal_negativo)

    # Salvar o DataFrame tratado em um arquivo CSV
    df_betha_agrupado.to_csv(f'data/Betha_Tratado_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')

    # ------ Processamento do TCE ------
    # Renomear colunas do TCE para facilitar a comparação
    df_tce.rename(columns={
        'Código conta': 'Máscara',
        'Nome conta': 'Conta Corrente',
        'Saldo final': 'Saldo atual'
    }, inplace=True)

    # Normalizar máscaras no TCE
    df_tce['Máscara Normalizada'] = df_tce['Máscara'].apply(normalizar_mascara)
    df_tce = df_tce[df_tce['Máscara Normalizada'].notna()]
    # Normalizar contas do TCE para garantir 18 dígitos
    df_tce['Conta Corrente Normalizada'] = df_tce['Conta Corrente'].apply(normalizar_conta_tce)

    # Limpar e converter saldos no TCE
    df_tce['Saldo atual'] = df_tce['Saldo atual'].apply(limpar_saldo)
    df_tce = df_tce[df_tce['Conta Corrente'].apply(parece_conta_corrente_tce)]
    df_tce = df_tce[df_tce['Conta Corrente'].apply(contem_numeros)]

    # Extrair e formatar a coluna "Conta Corrente"
    df_tce['Conta Corrente'] = df_tce['Conta Corrente Normalizada'].apply(extrair_conta_corrente)
    df_tce['Conta Corrente'] = df_tce['Conta Corrente'].apply(normalizar_conta_corrente_comparacao)
    colunas_tce = ['Máscara Normalizada', 'Conta Corrente', 'Saldo atual']
    df_tce_filtrado = df_tce[colunas_tce]

    # Salvar o DataFrame tratado do TCE para uso posterior
    df_tce_filtrado.to_csv('data/TCE_Tratado.csv', index=False, encoding='utf-8')

    # ------ Comparação entre Betha e TCE ------
    # Carregar os DataFrames tratados novamente (caso não estejam na memória)
    df_betha_tratado = pd.read_csv(f'data/Betha_Tratado_Saldo_{saldo_type.capitalize()}.csv', encoding='utf-8')
    df_tce_tratado = pd.read_csv('data/TCE_Tratado.csv', encoding='utf-8')

    # Renomear as colunas de saldo para garantir consistência
    df_tce_tratado.rename(columns={'Saldo atual': 'Saldo_atual_TCE'}, inplace=True)
    

    # Realizar a comparação
    df_comparacao = pd.merge(
        df_betha_tratado,
        df_tce_tratado,
        on=['Máscara Normalizada', 'Conta Corrente'],
        how='inner'
    )
    # Desativar a notação científica
    pd.set_option('display.float_format', '{:.2f}'.format)

    # Calcular a diferença de saldos
    df_comparacao['Diferença de Saldo'] = df_comparacao['Saldo_atual_Betha'] - df_comparacao['Saldo_atual_TCE']
    df_comparacao['Diferença de Saldo'] = df_comparacao['Diferença de Saldo'].round(2)

    # Filtrar apenas as linhas com diferenças de saldo
    df_diferencas = df_comparacao[df_comparacao['Diferença de Saldo'] != 0]
    # Processar os dados
    df_comparacao['Saldo_atual_Betha'] = df_comparacao['Saldo_atual_Betha'].apply(lambda x: f"{x:.2f}")
    df_comparacao['Saldo_atual_TCE'] = df_comparacao['Saldo_atual_TCE'].apply(lambda x: f"{x:.2f}")
    # Exportar os resultados para arquivos CSV
    df_comparacao.to_csv(f'data/Comparacao_Betha_TCE_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')
    df_diferencas.to_csv(f'data/Diferencas_Betha_TCE_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')

    # Realizar merge considerando ambas as colunas
    df_outer = pd.merge(
        df_betha_tratado,
        df_tce_tratado,
        how='outer',
        left_on=['Máscara Normalizada', 'Conta Corrente'],  # Chave composta
        right_on=['Máscara Normalizada', 'Conta Corrente'],  # Chave composta
        indicator=True,
        suffixes=('_betha', '_tce')
    )

    # Para registros exclusivos do Betha (ignorando saldos iguais a 0)
    df_sem_correspondencia_betha = df_outer[
        (df_outer['_merge'] == 'left_only') & 
        (df_outer['Saldo_atual_Betha'] != 0)  # Ignora saldos iguais a 0
    ][[
        'Máscara Normalizada', 
        'Conta Corrente', 
        'Saldo_atual_Betha'
    ]]

    # Para registros exclusivos do TCE (ignorando saldos iguais a 0)
    df_sem_correspondencia_tce = df_outer[
        (df_outer['_merge'] == 'right_only') & 
        (df_outer['Saldo_atual_TCE'] != 0)  # Ignora saldos iguais a 0
    ][[
        'Máscara Normalizada', 
        'Conta Corrente', 
        'Saldo_atual_TCE'
    ]]

    # Salvar os resultados filtrados
    df_sem_correspondencia_betha.to_csv(
        f"data/Mascaras_Sem_Correspondencia_Betha_Analitico_Saldo_{saldo_type.capitalize()}.csv", index=False, encoding="utf-8"
    )
    df_sem_correspondencia_tce.to_csv(
        f"data/Mascaras_Sem_Correspondencia_TCE_Analitico_Saldo_{saldo_type.capitalize()}.csv", index=False, encoding="utf-8"
    )

    logging.info("Máscaras sem correspondência identificadas e salvas com sucesso.")

    return df_comparacao, df_diferencas, df_sem_correspondencia_betha, df_sem_correspondencia_tce
def process_sintetico(saldo_type="atual"):
    logging.info(f"Iniciando processamento no modo Sintético com Saldo {saldo_type.capitalize()}...")
    try:
        # Carregar arquivos CSV
        df_betha = pd.read_csv('uploads/betha.csv', sep=';', dtype={'descrição': str}, encoding='utf-8')
        df_tce = pd.read_csv('uploads/tce.csv', sep=';', skiprows=5, dtype={'Nome Conta': str}, encoding='ISO-8859-1')

        # Aplicar a função de conversão ao campo "Nome conta" para corrigir notação científica
        df_tce['Nome conta'] = df_tce['Nome conta'].apply(converter_notacao_cientifica)

        # ------ Processamento do TCE ------
        try:
            # Renomear colunas do TCE para facilitar a comparação
            df_tce.rename(columns={
                'Código conta': 'Máscara',
                'Nome conta': 'Conta Corrente',
                'Saldo final': 'Saldo atual'
            }, inplace=True)

            # Normalizar máscaras no TCE
            df_tce['Máscara Normalizada'] = df_tce['Máscara'].apply(normalizar_mascara)

            # Normalizar contas do TCE para garantir 18 dígitos
            df_tce['Conta Corrente Normalizada'] = df_tce['Conta Corrente'].apply(normalizar_conta_tce)

            # Limpar e converter saldos no TCE
            if saldo_type == "atual":
                saldo_coluna_tce = 'Saldo atual'
            elif saldo_type == "anterior":
                saldo_coluna_tce = 'Saldo anterior'
            else:
                raise ValueError("Tipo de saldo inválido. Use 'atual' ou 'anterior'.")
            
            df_tce[saldo_coluna_tce] = df_tce[saldo_coluna_tce].apply(limpar_saldo)

            # Extrair e formatar a coluna "Conta Corrente"
            df_tce['Conta Corrente'] = df_tce['Conta Corrente Normalizada'].apply(extrair_conta_corrente)
            df_tce['Conta Corrente'] = df_tce['Conta Corrente'].apply(normalizar_conta_corrente_comparacao)

            # Remover duplicatas na coluna "Máscara Normalizada", mantendo apenas a primeira ocorrência
            df_tce = df_tce.drop_duplicates(subset='Máscara Normalizada', keep='first')

            # Selecionar colunas relevantes
            colunas_tce = ['Máscara Normalizada', 'Conta Corrente', saldo_coluna_tce]
            df_tce_filtrado = df_tce[colunas_tce]

            # Salvar o DataFrame tratado do TCE para uso posterior
            df_tce_filtrado.to_csv(f'data/TCE_Tratado_Sintetico_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')
            logging.info(f"Arquivo TCE tratado com sucesso no modo Sintético com Saldo {saldo_type.capitalize()}.")
        except Exception as e:
            logging.error(f"Erro ao processar o arquivo TCE: {e}")
            return None

        # ------ Processamento do Betha ------
        try:
            # Normalizar máscaras no Betha
            df_betha['Máscara Normalizada'] = df_betha['Máscara'].apply(normalizar_mascara)

            # Criar uma nova coluna "Conta Corrente" aplicando a função
            df_betha['Conta Corrente'] = df_betha['Descrição'].apply(extrair_conta_corrente)
            df_betha['Conta Corrente'] = df_betha['Conta Corrente'].apply(normalizar_conta_corrente_comparacao)
            df_betha = df_betha[df_betha['Tipo'] == 'Sintética']

            # Limpar e converter saldos no Betha
            if saldo_type == "atual":
                saldo_coluna_betha = 'Saldo atual'
            elif saldo_type == "anterior":
                saldo_coluna_betha = 'Saldo anterior'
            else:
                raise ValueError("Tipo de saldo inválido. Use 'atual' ou 'anterior'.")

            df_betha[saldo_coluna_betha] = df_betha[saldo_coluna_betha].apply(limpar_saldo)
            # Remover o sinal negativo dos valores relevantes
            df_betha[saldo_coluna_betha] = df_betha[saldo_coluna_betha].apply(remover_sinal_negativo)

            # FILTRO ADICIONAL: Remover contas correntes que não contêm números
            # df_betha = df_betha[df_betha['Conta Corrente'].apply(contem_numeros)]

            # Selecionar colunas relevantes
            colunas_tratadas_betha = ['Máscara Normalizada', 'Conta Corrente', saldo_coluna_betha]
            df_betha_tratado = df_betha[colunas_tratadas_betha]

            # Salvar o DataFrame tratado do Betha para uso posterior
            df_betha_tratado.to_csv(f'data/Betha_Tratado_Sintetico_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')
            logging.info(f"Arquivo Betha tratado com sucesso no modo Sintético com Saldo {saldo_type.capitalize()}.")
        except Exception as e:
            logging.error(f"Erro ao processar o arquivo Betha: {e}")
            return None

        # ------ Comparação entre Betha e TCE ------
        try:
            # Carregar os DataFrames tratados novamente (caso não estejam na memória)
            df_betha_tratado = pd.read_csv(f'data/Betha_Tratado_Sintetico_Saldo_{saldo_type.capitalize()}.csv', encoding='utf-8')
            df_tce_tratado = pd.read_csv(f'data/TCE_Tratado_Sintetico_Saldo_{saldo_type.capitalize()}.csv', encoding='utf-8')

            # Renomear as colunas de saldo para garantir consistência
            df_betha_tratado.rename(columns={saldo_coluna_betha: 'Saldo_atual_Betha'}, inplace=True)
            df_tce_tratado.rename(columns={saldo_coluna_tce: 'Saldo_atual_TCE'}, inplace=True)

            # Realizar a comparação usando chave composta
            df_comparacao = pd.merge(
                df_betha_tratado,
                df_tce_tratado,
                on=['Máscara Normalizada', 'Conta Corrente'],  # Chave composta
                how='inner'
            )

            # Calcular a diferença de saldos
            df_comparacao['Diferença de Saldo'] = df_comparacao['Saldo_atual_Betha'] - df_comparacao['Saldo_atual_TCE']
            df_comparacao['Diferença de Saldo'] = df_comparacao['Diferença de Saldo'].round(2)

            # Filtrar apenas as linhas com diferenças de saldo
            df_diferencas = df_comparacao[df_comparacao['Diferença de Saldo'] != 0]

            # Exportar os resultados da comparação e das diferenças
            df_comparacao.to_csv(f'data/Comparacao_Betha_TCE_Sintetico_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')
            df_diferencas.to_csv(f'data/Diferencas_Betha_TCE_Sintetico_Saldo_{saldo_type.capitalize()}.csv', index=False, encoding='utf-8')

            # Identificar máscaras sem correspondência
            df_outer = pd.merge(
                df_betha_tratado,
                df_tce_tratado,
                how='outer',
                on=['Máscara Normalizada', 'Conta Corrente'],  # Chave composta
                indicator=True,
                suffixes=('_betha', '_tce')
            )

            # Para registros exclusivos do Betha (ignorando saldos iguais a 0)
            df_sem_correspondencia_betha = df_outer[
                (df_outer['_merge'] == 'left_only') & 
                (df_outer['Saldo_atual_Betha'] != 0)  # Ignora saldos iguais a 0
            ][[
                'Máscara Normalizada', 
                'Conta Corrente', 
                'Saldo_atual_Betha'
            ]]

            # Para registros exclusivos do TCE (ignorando saldos iguais a 0)
            df_sem_correspondencia_tce = df_outer[
                (df_outer['_merge'] == 'right_only') & 
                (df_outer['Saldo_atual_TCE'] != 0)  # Ignora saldos iguais a 0
            ][[
                'Máscara Normalizada', 
                'Conta Corrente', 
                'Saldo_atual_TCE'
            ]]

            # Salvar os resultados filtrados
            df_sem_correspondencia_betha.to_csv(
                f"data/Mascaras_Sem_Correspondencia_Betha_Sintetico_Saldo_{saldo_type.capitalize()}.csv", index=False, encoding="utf-8"
            )
            df_sem_correspondencia_tce.to_csv(
                f"data/Mascaras_Sem_Correspondencia_TCE_Sintetico_Saldo_{saldo_type.capitalize()}.csv", index=False, encoding="utf-8"
            )

            logging.info("Máscaras sem correspondência identificadas e salvas com sucesso.")
            return df_comparacao, df_diferencas, df_sem_correspondencia_betha, df_sem_correspondencia_tce
        except Exception as e:
            logging.error(f"Erro durante a comparação: {e}")
            return None
    except Exception as e:
        logging.error(f"Erro geral no processamento sintético: {e}")
        return None

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "analitico"

    if mode == "analitico":
        df_comparacao, df_diferencas, df_sem_correspondencia_betha, df_sem_correspondencia_tce = process_analitico()
        print("Diferenças Encontradas:")
        print(df_diferencas)
        print("DataFrame de Comparação:")
        print(df_comparacao)
    elif mode == "sintetico":
        result = process_sintetico()
    elif mode == "inicial":
        df_comparacao, df_diferencas = process_inicial()
        print("Diferenças Encontradas:")
        print(df_diferencas)
        print("DataFrame de Comparação:")
        print(df_comparacao)
    else:
        result = "Modo inválido. Use 'analitico' ou 'sintetico' ou 'inicial'."
        print(result)
