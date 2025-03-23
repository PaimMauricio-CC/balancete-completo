import pandas as pd
import sys
from utils import normalizar_mascara, extrair_conta_corrente, limpar_saldo, corrigir_tipo, normalizar_conta_tce
# Processamento Analítico
def process_analitico():
    print("Iniciando processamento no modo Analítico...")
    
    # Carregar arquivos CSV
    df_betha = pd.read_csv('uploads/betha.csv', dtype={'descrição': str})
    #df_tce = pd.read_csv('uploads/tce.csv', dtype={'Nome conta': str})
    # Carregar arquivos CSV com tratamento inicial para o TCE
    df_tce = pd.read_csv('uploads/tce.csv', skiprows=5, dtype={'Nome conta': str})

# EXEMPLO Carregar o CSV forçando a coluna "Código conta" como texto
#df = pd.read_csv('Balancete TCE PMAW - 202410(Editado).csv', dtype={'Código conta': str})



    # Corrigir o tipo das contas no DataFrame Betha
    df_betha = corrigir_tipo(df_betha)

    # ------ Processamento do Betha ------
    # Filtrar apenas as máscaras analíticas (remover as sintéticas)
    df_betha = df_betha[df_betha['Tipo'] == 'Analitica']

    # Normalizar máscaras
    df_betha['Máscara Normalizada'] = df_betha['Máscara'].apply(normalizar_mascara)
## remover depois
    # Verificar as máscaras normalizadas
    print("\nMáscaras Normalizadas:")
    print(df_betha[['Máscara', 'Máscara Normalizada']].head(213))
    ##
    # Substituir NaN na coluna "Máscara Normalizada" com base na última máscara válida
    ultima_mascara_valida = None
    mascaras_preenchidas = []
    for mascara in df_betha['Máscara Normalizada']:
        if mascara is not None:
            ultima_mascara_valida = mascara  # Atualiza a última máscara válida
        mascaras_preenchidas.append(ultima_mascara_valida)
    df_betha['Máscara Normalizada'] = mascaras_preenchidas
    print(df_betha[['Máscara Normalizada']].head(50))

    # Criar uma nova coluna "Conta Corrente" aplicando a função
    df_betha['Conta Corrente'] = df_betha['Descrição'].apply(extrair_conta_corrente)
## remover depois }}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}}
    # Verificar as contas correntes extraídas
    print("\nContas Correntes Extraídas:")
    print(df_betha[['Descrição', 'Conta Corrente']].head(213))
##
    # Limpar e converter saldos para float
    df_betha['Saldo Atual'] = df_betha['Saldo atual'].apply(limpar_saldo)

    # Selecionar colunas relevantes para o DataFrame tratado
    colunas_tratadas_betha = ['Máscara Normalizada', 'Conta Corrente', 'Saldo Atual']
    df_betha_tratado = df_betha[colunas_tratadas_betha]

    # Salvar o DataFrame tratado em um arquivo CSV
    df_betha_tratado.to_csv('data/Betha_Tratado.csv', index=False, encoding='utf-8')

    # ------ Processamento do TCE ------
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
    df_tce['Saldo atual'] = df_tce['Saldo atual'].apply(limpar_saldo)

    # Extrair e formatar a coluna "Conta Corrente"
    df_tce['Conta Corrente'] = df_tce['Conta Corrente Normalizada'].apply(extrair_conta_corrente)
    print("\nContas Correntes Extraídas:")
    print(df_tce[['Conta Corrente']].head(143))
    
    colunas_tce = ['Máscara Normalizada', 'Conta Corrente', 'Saldo atual']
    df_tce_filtrado = df_tce[colunas_tce]

    # Salvar o DataFrame tratado do TCE para uso posterior
    df_tce_filtrado.to_csv('data/TCE_Tratado.csv', index=False, encoding='utf-8')

    # ------ Comparação entre Betha e TCE ------
    # Carregar os DataFrames tratados novamente (caso não estejam na memória)
    df_betha_tratado = pd.read_csv('data/Betha_Tratado.csv', encoding='utf-8')
    df_tce_tratado = pd.read_csv('data/TCE_Tratado.csv', encoding='utf-8')

    # Renomear as colunas de saldo para garantir consistência
    df_betha_tratado.rename(columns={'Saldo Atual': 'Saldo_atual_Betha'}, inplace=True)
    df_tce_tratado.rename(columns={'Saldo atual': 'Saldo_atual_TCE'}, inplace=True)

    # Realizar a comparação
    df_comparacao = pd.merge(
        df_betha_tratado,
        df_tce_tratado,
        on=['Máscara Normalizada', 'Conta Corrente'],
        how='inner'
    )

    # Calcular a diferença de saldos
    df_comparacao['Diferença de Saldo'] = df_comparacao['Saldo_atual_Betha'] - df_comparacao['Saldo_atual_TCE']

    # Filtrar apenas as linhas com diferenças de saldo
    df_diferencas = df_comparacao[df_comparacao['Diferença de Saldo'] != 0]

    # Exportar os resultados para arquivos CSV
    df_comparacao.to_csv('data/Comparacao_Betha_TCE.csv', index=False, encoding='utf-8')
    df_diferencas.to_csv('data/Diferencas_Betha_TCE.csv', index=False, encoding='utf-8')

    return df_comparacao, df_diferencas

# Processamento Sintético (Em implementação)
def process_sintetico():
    logging.info("Iniciando processamento no modo Sintético...")
    
    # ------ Processamento do TCE ------
    try:
        # Renomear colunas do TCE para facilitar a comparação
        df_tce.rename(columns={
            'Código conta': 'Máscara',
            'Nome conta': 'Conta Corrente',
            'Saldo final': 'Saldo atual'
        }, inplace=True)
        
        # Remover duplicatas na coluna "Máscara", mantendo apenas a primeira ocorrência
        df_tce.drop_duplicates(subset='Máscara', keep='first', inplace=True)
        
        # Normalizar máscaras no TCE
        df_tce['Máscara Normalizada'] = df_tce['Máscara'].apply(normalizar_mascara)
        
        # Limpar e converter saldos no TCE
        df_tce['Saldo atual'] = df_tce['Saldo atual'].apply(limpar_saldo)
        
        # Selecionar colunas relevantes
        colunas_tce = ['Máscara Normalizada', 'Saldo atual']
        df_tce_filtrado = df_tce[colunas_tce]
        
        # Salvar o DataFrame tratado do TCE para uso posterior
        df_tce_filtrado.to_csv('data/TCE_Tratado_Sintetico.csv', index=False, encoding='utf-8')
        logging.info("Arquivo TCE tratado com sucesso no modo Sintético.")
    except Exception as e:
        logging.error(f"Erro ao processar o arquivo TCE: {e}")
        return None

    # ------ Processamento do Betha ------
    try:
        # Carregar o arquivo Betha
        df_betha = pd.read_csv('uploads/betha.csv', dtype={'Máscara': str})
        
        # Normalizar máscaras no Betha
        df_betha['Máscara Normalizada'] = df_betha['Máscara'].apply(normalizar_mascara)
        
        # Limpar e converter saldos no Betha
        df_betha['Saldo Atual'] = df_betha['Saldo atual'].apply(limpar_saldo)
        
        # Selecionar colunas relevantes
        colunas_tratadas_betha = ['Máscara Normalizada', 'Saldo Atual']
        df_betha_tratado = df_betha[colunas_tratadas_betha]
        
        # Salvar o DataFrame tratado do Betha para uso posterior
        df_betha_tratado.to_csv('data/Betha_Tratado_Sintetico.csv', index=False, encoding='utf-8')
        logging.info("Arquivo Betha tratado com sucesso no modo Sintético.")
    except Exception as e:
        logging.error(f"Erro ao processar o arquivo Betha: {e}")
        return None

    # ------ Comparação entre Betha e TCE ------
    try:
        # Carregar os DataFrames tratados novamente (caso não estejam na memória)
        df_betha_tratado = pd.read_csv('data/Betha_Tratado_Sintetico.csv', encoding='utf-8')
        df_tce_tratado = pd.read_csv('data/TCE_Tratado_Sintetico.csv', encoding='utf-8')

        # Realizar a comparação
        df_comparacao = pd.merge(
            df_betha_tratado,
            df_tce_tratado,
            on='Máscara Normalizada',
            how='inner'
        )

        # Calcular a diferença de saldos
        df_comparacao['Diferença de Saldo'] = df_comparacao['Saldo Atual'] - df_comparacao['Saldo atual']

        # Filtrar apenas as linhas com diferenças de saldo
        df_diferencas = df_comparacao[df_comparacao['Diferença de Saldo'] != 0]

        # Exportar os resultados para arquivos CSV
        df_comparacao.to_csv('data/Comparacao_Betha_TCE_Sintetico.csv', index=False, encoding='utf-8')
        df_diferencas.to_csv('data/Diferencas_Betha_TCE_Sintetico.csv', index=False, encoding='utf-8')

        logging.info("Comparação concluída com sucesso no modo Sintético.")
        return df_comparacao, df_diferencas
    except Exception as e:
        logging.error(f"Erro durante a comparação: {e}")
        return None

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "analitico"

    if mode == "analitico":
        df_comparacao, df_diferencas = process_analitico()
        print("DataFrame de Comparação:")
        print(df_comparacao)
        print("Diferenças Encontradas:")
        print(df_diferencas)
    elif mode == "sintetico":
        result = process_sintetico()
    else:
        result = "Modo inválido. Use 'analitico' ou 'sintetico'."

    print(result)