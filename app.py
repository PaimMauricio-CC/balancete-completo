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

        # Salvar os arquivos temporariamente
        betha_path = "uploads/betha.csv"
        tce_path = "uploads/tce.csv"
        betha_file.save(betha_path)
        tce_file.save(tce_path)

        # Processar os arquivos com base no modo selecionado
        if mode == "analitico":
            df_comparacao, df_diferencas, df_sem_corresp_betha, df_sem_corresp_tce = main.process_analitico()

            # Converter os DataFrames para HTML para exibição
            # Converta para HTML
            sem_corresp_betha_html = df_sem_corresp_betha.to_html(classes="table table-striped", index=False)
            sem_corresp_tce_html = df_sem_corresp_tce.to_html(classes="table table-striped", index=False)
            comparacao_html = df_comparacao.to_html(classes="table table-striped", index=False)
            diferencas_html = df_diferencas.to_html(classes="table table-striped", index=False)

            return render_template(
                "index.html",
                comparacao_html=comparacao_html,
                diferencas_html=diferencas_html,
                sem_correspondencia_betha_html=sem_corresp_betha_html,  # Nova variável
                sem_correspondencia_tce_html=sem_corresp_tce_html,      # Nova variável
                comparacao_file="data/Comparacao_Betha_TCE.csv",
                diferencas_file="data/Diferencas_Betha_TCE.csv",
                sem_corresp_betha_file="data/Mascaras_Sem_Correspondencia_Betha_Analitico.csv",
                sem_corresp_tce_file="data/Mascaras_Sem_Correspondencia_TCE_Analitico.csv"
            )
        elif mode == "sintetico":
            # Chamar o processamento sintético
            result = main.process_sintetico()

            # Verificar se o resultado é válido
            if isinstance(result, tuple):  # Se for uma tupla (df_comparacao, df_diferencas)
                df_comparacao, df_diferencas, df_sem_corresp_betha, df_sem_corresp_tce = result

                # Converter os DataFrames para HTML para exibição
                comparacao_html = df_comparacao.to_html(classes="table table-striped", index=False)
                diferencas_html = df_diferencas.to_html(classes="table table-striped", index=False)
                sem_corresp_betha_html = df_sem_corresp_betha.to_html(classes="table table-striped", index=False)
                sem_corresp_tce_html = df_sem_corresp_tce.to_html(classes="table table-striped", index=False)

                return render_template(
                    "index.html",
                    comparacao_html=comparacao_html,
                    diferencas_html=diferencas_html,
                    sem_correspondencia_betha_html=sem_corresp_betha_html,  # Nova variável
                    sem_correspondencia_tce_html=sem_corresp_tce_html,      # Nova variável
                    omparacao_file="data/Comparacao_Betha_TCE_Sintetico.csv",
                    diferencas_file="data/Diferencas_Betha_TCE_Sintetico.csv",
                    sem_corresp_betha_file="data/Mascaras_Sem_Correspondencia_Betha_Sintetico.csv",
                    sem_corresp_tce_file="data/Mascaras_Sem_Correspondencia_TCE_Sintetico.csv"
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
    app.run(debug=True)