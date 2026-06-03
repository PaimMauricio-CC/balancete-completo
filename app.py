from flask import Flask, render_template, request, send_file
import pandas as pd
import main

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Obter arquivos enviados pelo usuário
        betha_file = request.files["bethaFile"]
        tce_file = request.files["tceFile"]
        mode = request.form.get("mode")
        saldo_type = request.form.get("saldo_type", "atual")  # Capturar o tipo de saldo selecionado (padrão: "atual")

        # Salvar os arquivos temporariamente
        betha_path = "uploads/betha.csv"
        tce_path = "uploads/tce.csv"
        betha_file.save(betha_path)
        tce_file.save(tce_path)

        # Processar os arquivos com base no modo selecionado
        if mode == "analitico":
            df_comparacao, df_diferencas, df_sem_corresp_betha, df_sem_corresp_tce = main.process_analitico(
                saldo_type=saldo_type  # Passar o tipo de saldo para a função
            )

            # Converter os DataFrames para HTML para exibição
            sem_corresp_betha_html = df_sem_corresp_betha.to_html(classes="table table-striped", index=False)
            sem_corresp_tce_html = df_sem_corresp_tce.to_html(classes="table table-striped", index=False)
            comparacao_html = df_comparacao.to_html(classes="table table-striped", index=False)
            diferencas_html = df_diferencas.to_html(classes="table table-striped", index=False)

            saldo_label = saldo_type.capitalize()

            return render_template(
                "index.html",
                comparacao_html=comparacao_html,
                diferencas_html=diferencas_html,
                has_diferencas=not df_diferencas.empty,
                sem_correspondencia_betha_html=sem_corresp_betha_html,  # Nova variável
                sem_correspondencia_tce_html=sem_corresp_tce_html,      # Nova variável
                comparacao_file=f"data/Comparacao_Betha_TCE_Saldo_{saldo_label}.csv",
                diferencas_file=f"data/Diferencas_Betha_TCE_Saldo_{saldo_label}.csv",
                sem_corresp_betha_file=f"data/Mascaras_Sem_Correspondencia_Betha_Analitico_Saldo_{saldo_label}.csv",
                sem_corresp_tce_file=f"data/Mascaras_Sem_Correspondencia_TCE_Analitico_Saldo_{saldo_label}.csv"
            )
            
        elif mode == "sintetico":
            # Chamar o processamento sintético com o tipo de saldo
            result = main.process_sintetico(saldo_type=saldo_type)  # Passar o tipo de saldo para a função

            # Verificar se o resultado é válido
            if isinstance(result, tuple):  # Se for uma tupla (df_comparacao, df_diferencas)
                df_comparacao, df_diferencas, df_sem_corresp_betha, df_sem_corresp_tce = result

                # Converter os DataFrames para HTML para exibição
                comparacao_html = df_comparacao.to_html(classes="table table-striped", index=False)
                diferencas_html = df_diferencas.to_html(classes="table table-striped", index=False)
                sem_corresp_betha_html = df_sem_corresp_betha.to_html(classes="table table-striped", index=False)
                sem_corresp_tce_html = df_sem_corresp_tce.to_html(classes="table table-striped", index=False)

                saldo_label = saldo_type.capitalize()

                return render_template(
                    "index.html",
                    comparacao_html=comparacao_html,
                    diferencas_html=diferencas_html,
                    has_diferencas=not df_diferencas.empty,
                    sem_correspondencia_betha_html=sem_corresp_betha_html,  # Nova variável
                    sem_correspondencia_tce_html=sem_corresp_tce_html,      # Nova variável
                    comparacao_file=f"data/Comparacao_Betha_TCE_Sintetico_Saldo_{saldo_label}.csv",
                    diferencas_file=f"data/Diferencas_Betha_TCE_Sintetico_Saldo_{saldo_label}.csv",
                    sem_corresp_betha_file=f"data/Mascaras_Sem_Correspondencia_Betha_Sintetico_Saldo_{saldo_label}.csv",
                    sem_corresp_tce_file=f"data/Mascaras_Sem_Correspondencia_TCE_Sintetico_Saldo_{saldo_label}.csv"
                )
            else:
                return "Erro ao processar no modo Sintético."
        else:
            return "Modo inválido."

    return render_template("index.html")

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"data/{filename}", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
