import pandas as pd

# Função para normalizar máscaras no padrão X.X.X.X.X.XX.XX
def normalizar_mascara(mascara):
    if pd.isna(mascara):  # Verifica se a máscara é NaN
        return None
    
    # Remove o padrão "200" de máscaras que contenham esse valor
    if isinstance(mascara, str) and '200' in mascara:
        mascara = mascara.replace('200', '')  # Remove "200"
    
    # Divide a máscara em partes usando o ponto como separador
    partes = mascara.split('.')
    
    # Trunca a máscara para garantir no máximo 7 níveis
    partes = partes[:7]
    
    # Preenche os níveis ausentes com zeros até atingir o formato completo: X.X.X.X.X.XX.XX
    while len(partes) < 7:  # O formato completo tem 7 níveis
        partes.append('00' if len(partes) >= 5 else '0')  # Níveis 6 e 7 têm dois dígitos
    
    # Garante que cada parte tenha o número correto de dígitos
    partes = [
        parte.zfill(2) if i >= 5 else parte.zfill(1)  # Níveis 6+ têm dois dígitos
        for i, parte in enumerate(partes)
    ]
    
    # Junta as partes novamente em uma máscara normalizada
    return '.'.join(partes[:7])  # Limita ao formato X.X.X.X.X.XX.XX

# Função para extrair e formatar a conta corrente ou outros padrões
def extrair_conta_corrente(descricao):
    """
    Extrai e formata descrições de acordo com diferentes padrões.
    Entrada: Descrição no formato específico do Betha.
    Saída: Descrição formatada conforme o padrão desejado.
    """
    if pd.isna(descricao):  # Verifica se a descrição é NaN
        return None

    # Caso 1: Remover "2-Destinação de Recursos - " e manter apenas o número
    if descricao.startswith("2-Destinação de Recursos - "):
        return descricao.replace("2-Destinação de Recursos - ", "").strip()

    # Caso 2: Transformar padrão "5-Conta Bancária+FR - ..." no formato TCE
    if descricao.startswith("5-Conta Bancária+FR - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("5-Conta Bancária+FR - ", "").strip()
            
            # Divide a descrição em partes usando espaços
            partes = descricao.split()
            
            if len(partes) >= 4:
                banco = partes[0].zfill(4)  # Garante 4 dígitos
                agencia = partes[1].zfill(5)  # Garante 5 dígitos
                
                # Conta e dígito verificador (mantém o formato original)
                conta_digito = partes[2]  # Ex: "9.633-4" ou "96.630-4"
                
                # Destino (última parte)
                destino = partes[3]  # Ex: "18997000"
                
                # Monta a conta corrente no formato desejado
                # Adiciona 8 espaços entre a conta e o destino
                conta_corrente = f"{banco}{'0'}{agencia}{conta_digito}{' ' * 8}{destino}"
                return conta_corrente
        except Exception as e:
            print(f"Erro ao processar '5-Conta Bancária+FR': {e}")
            return descricao  # Retorna a descrição original em caso de erro

    # Caso 3: Remover "6-Credor - " e normalizar o CPF
    elif descricao.startswith("6-Credor - "):
        cpf = descricao.replace("6-Credor - ", "").strip()
        return normalizar_cpf(cpf)  # Normaliza o CPF

    # Caso 4: Processar "1-Célula da Receita - ..."
    elif descricao.startswith("1-Célula da Receita - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("1-Célula da Receita - ", "").strip()
            # Remove todos os espaços
            descricao = descricao.replace(" ", "")
            return descricao
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro

    # Caso 5: Processar "7-Empenho - ..."
    elif descricao.startswith("7-Empenho - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("7-Empenho - ", "").strip()
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) >= 5:
                orgao = partes[0]  # Ex: "13001"
                ano = partes[1]  # Ex: "2024"
                empenho = partes[2].zfill(6)  # Preenche com zeros à esquerda (6 dígitos)
                fase = partes[3]  # Ex: "0"
                destino = partes[4]  # Ex: "16007000"
                # Monta o padrão desejado
                padrao_empenho = f"{orgao}{ano}{'0' * 12}{empenho}{'0' * 16}{destino}"
                return padrao_empenho
        except Exception:
            pass  # Ignora erros e retorna a descrição original
        return descricao  # Retorna a descrição original se não se encaixar no padrão

    # Caso 6: Processar "4-Fonte de Recurso para abertura de créditos - X"
    elif descricao.startswith("4-Fonte de Recurso para abertura de créditos - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("4-Fonte de Recurso para abertura de créditos - ", "").strip()
            return descricao  # Retorna apenas o número isolado
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro

    # Caso 7: Processar "14-Contratos e Convênios - ..."
    elif descricao.startswith("14-Contratos e Convênios - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("14-Contratos e Convênios - ", "").strip()
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) >= 4:
                ano_mes = partes[0]  # Ex: "2016"
                numero_contrato = partes[1]  # Ex: "Nº30/2016"
                cnpj = partes[2]  # Ex: "00456865000167"
                # Monta o padrão TCE
                padrao_contrato = f"{ano_mes}{numero_contrato}{' ' * 7}{cnpj}"
                return padrao_contrato
        except Exception:
            return descricao  # Retorna a descrição original em caso de erro

    # Caso 8: Processar "13-Consórcios - ..."   
    elif descricao.startswith("13-Consórcios - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("13-Consórcios - ", "").strip()
            # Divide a descrição em partes
            partes = descricao.split()
            
            if len(partes) == 8:
                ano_numero = partes[0]  # Ex: "2023"
                numero = partes[1]     # Ex: "Nº03/2023"
                cnpj = partes[2]       # Ex: "42499226000129"
                codigo1 = partes[3]    # Ex: "10"
                codigo2 = partes[4]    # Ex: "301"
                codigo3 = partes[5]    # Ex: "31717001"
                destino = partes[6]    # Ex: "15001002"

                # Formatação conforme o padrão TCE
                consorcio_formatado = f"{ano_numero}{' ' * 7}{numero}{cnpj}{codigo1}{codigo2}{codigo3}{destino}"
                return consorcio_formatado
        
        except Exception:
            pass  # Ignora erros e retorna a descrição original

    # Caso 9: Processar "3-Célula da Despesa - ..." (padrão TCE) REVISADOOOOOOO
    elif descricao.startswith("3-Célula da Despesa - "):
        try:
            # Remove o prefixo
            descricao = descricao.replace("3-Célula da Despesa - ", "").strip()
            # Divide a descrição em partes
            partes = descricao.split()
            if len(partes) == 4:
                orgao = partes[0]  # Ex: "13001"
                mascara = partes[1]  # Ex: "1037"
                conta = partes[2]  # Ex: "449000"
                destino = partes[3]  # Ex: "16017000"

                # Formatação conforme o padrão TCE
                orgao_formatado = orgao.zfill(5)  # Garante 5 dígitos
                primeiro_digito_mascara = mascara[0]  # Primeiro dígito (ex.: "1")
                resto_mascara = mascara[1:].zfill(5)  # Restante da máscara (ex.: "037" -> "00037")
                mascara_formatada = f"{primeiro_digito_mascara}{'0'}{resto_mascara}"  # Ex: "1000037"
                conta_formatada = conta.zfill(6)  # Garante 6 dígitos

                # Monta a conta no formato TCE
                conta_tce = f"{orgao_formatado}{'0'}{mascara_formatada}{conta_formatada}{destino}"
                return conta_tce
        except Exception:
            pass  # Ignora erros e retorna a descrição original
    return descricao  # Retorna a descrição original se não se encaixar no padrão

    # Caso genérico: Retorna a descrição original caso não se encaixe nos padrões
    return descricao

# Função para normalizar CPFs
def normalizar_cpf(cpf):
    """Normaliza um CPF para garantir que tenha 11 dígitos, adicionando zeros à esquerda se necessário."""
    if pd.isna(cpf):  # Verifica se o valor é NaN
        return None
    # Remove caracteres não numéricos (caso existam)
    cpf = ''.join(filter(str.isdigit, str(cpf)))
    # Adiciona zeros à esquerda até atingir 11 dígitos
    return cpf.zfill(11)

# Função para limpar saldos
def limpar_saldo(valor):
    if isinstance(valor, str):
        valor = valor.replace('.', '').replace(',', '.')
    return float(valor)

# Função para corrigir o tipo das contas
def corrigir_tipo(df):
    """
    Substitui valores NaN na coluna 'Tipo' por 'Analitica'.
    Mantém os valores existentes (ex.: 'Sintética') inalterados.
    """
    # Verifica se a coluna 'Tipo' existe no DataFrame
    if 'Tipo' in df.columns:
        # Substitui apenas os valores NaN por 'Analitica'
        df['Tipo'] = df['Tipo'].apply(lambda x: 'Analitica' if pd.isna(x) else x)
    return df

def normalizar_conta_tce(conta):
    """
    Normaliza uma conta do TCE para garantir que tenha 18 dígitos.
    - Adiciona zeros à esquerda se necessário.
    - Ignora contas que começam com "99".
    - Aplica a correção apenas para contas com exatamente 16 dígitos.
    """
    if pd.isna(conta):  # Verifica se a conta é NaN
        return None

    # Converte a conta para string (caso ainda não seja)
    conta = str(conta)

    # Ignora contas que começam com "99"
    if conta.startswith("99"):
        return conta

    # Verifica se a conta tem exatamente 16 dígitos
    if len(conta) == 16:
        # Adiciona "00" à esquerda para completar 18 dígitos
        conta_normalizada = "00" + conta
        return conta_normalizada

    # Retorna a conta inalterada se não tiver 16 dígitos
    return conta