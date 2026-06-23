import os
from pathlib import Path

from flask import Flask, abort, render_template, request, send_from_directory
import pandas as pd
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import RequestEntityTooLarge
import main
import conferidor_folha

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH", 32 * 1024 * 1024))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)

LICENSES = {
    "KYP12": {"GOVERNADOR CELSO RAMOS"},
    "KYP13": {"CANELINHA"},
    "KYP14": {"PREFEITURA DE BIGUACU"},
    "KYPMAU": {"*"},
}


class UserFacingError(Exception):
    pass


class LicenseError(UserFacingError):
    pass


ALLOWED_UPLOAD_EXTENSIONS = {".csv"}
ALLOWED_DOWNLOAD_EXTENSIONS = {".csv", ".xlsx"}


def normalize_text(value):
    return " ".join(str(value).upper().strip().split())


def has_allowed_extension(filename, allowed_extensions):
    _, extension = os.path.splitext(filename or "")
    return extension.lower() in allowed_extensions


def read_text_lines(path, encoding="ISO-8859-1", limit=8):
    with open(path, "r", encoding=encoding, errors="replace") as file:
        return [file.readline().strip() for _ in range(limit)]


def extract_tce_entity(path):
    lines = read_text_lines(path, limit=6)
    for line in lines:
        if line.upper().startswith("ENTE:"):
            entity = line.split(":", 1)[1].strip()
            if entity:
                return entity
    raise UserFacingError("O arquivo TCE não possui a linha 'Ente:' no cabeçalho esperado.")


def validate_betha_file(path):
    lines = read_text_lines(path, encoding="utf-8", limit=1)
    header = lines[0] if lines else ""
    required = ["Máscara", "Tipo", "Descrição", "Saldo anterior", "Saldo atual"]
    if ";" not in header or not all(column in header for column in required):
        raise UserFacingError("O arquivo Betha não está no padrão esperado.")


def validate_tce_file(path):
    lines = read_text_lines(path, limit=6)
    header = lines[5] if len(lines) >= 6 else ""
    required = ["Código conta", "Nome conta", "Saldo final"]
    if ";" not in header or not all(column in header for column in required):
        raise UserFacingError("O arquivo TCE não está no padrão esperado.")
    return extract_tce_entity(path)


def validate_license(license_code, entity):
    license_code = normalize_text(license_code)
    entity_key = normalize_text(entity)
    allowed_entities = LICENSES.get(license_code)
    if not allowed_entities:
        raise LicenseError("Licença inválida ou não cadastrada.")
    if "*" in allowed_entities:
        return
    if entity_key not in {normalize_text(item) for item in allowed_entities}:
        raise LicenseError(
            f"A licença informada não possui permissão para comparar o ente {entity}."
        )


def render_alert(message, title="Não foi possível processar os arquivos", detail=None):
    return render_template(
        "index.html",
        alert_title=title,
        alert_message=message,
        alert_detail=detail or (
            "Verifique se os arquivos selecionados são os CSVs corretos do Betha e do TCE. "
            "Caso acredite que os arquivos estejam corretos, entre em contato com o administrador."
        ),
    )

def normalize_folha_result_columns(df):
    df = df.copy()
    if "Tipo" not in df.columns and "Tipo Betha" in df.columns:
        df = df.rename(columns={"Tipo Betha": "Tipo"})
    if "Tipo TCE" in df.columns:
        df = df.drop(columns=["Tipo TCE"])
    return df


def process_folha(betha_path, tce_path):
    result = conferidor_folha.processar_conferencia(betha_path, tce_path)
    rows = result["rows"]
    summary = result["summary"]
    df_resultado = normalize_folha_result_columns(pd.DataFrame(rows))
    display_columns = [column for column in conferidor_folha.RESULT_COLUMNS if column in df_resultado.columns]
    df_resultado = df_resultado[display_columns]

    csv_filename = "Conferencia_Folha.csv"
    xlsx_filename = "Conferencia_Folha.xlsx"
    highlighted_xlsx_filename = "Conferencia_Folha_Destacado.xlsx"

    df_resultado.to_csv(DATA_DIR / csv_filename, index=False, encoding="utf-8")
    with open(DATA_DIR / xlsx_filename, "wb") as file:
        file.write(conferidor_folha.gerar_excel_conferencia(rows, summary))
    with open(DATA_DIR / highlighted_xlsx_filename, "wb") as file:
        file.write(conferidor_folha.gerar_excel_conferencia_destacado(rows, summary))

    summary_cards = [
        ("Total Betha", summary.get("totalBetha", 0)),
        ("Total TCE", summary.get("totalTce", 0)),
        ("Diferenca total", summary.get("diferencaTotal", 0)),
        ("OK", summary.get("ok", 0)),
        ("Divergentes", summary.get("divergente", 0)),
        ("Nao encontrados", summary.get("naoEncontrado", 0)),
        ("Sobras TCE", summary.get("sobraTce", 0)),
    ]

    return render_template(
        "index.html",
        conferidor_type="folha",
        comparacao_html=df_resultado.to_html(classes="table table-striped", index=False),
        comparacao_file=f"data/{csv_filename}",
        excel_file=f"data/{xlsx_filename}",
        highlighted_excel_file=f"data/{highlighted_xlsx_filename}",
        result_title="Resultado da Conferencia",
        summary_cards=summary_cards,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Obter arquivos enviados pelo usuário
        betha_file = request.files.get("bethaFile")
        tce_file = request.files.get("tceFile")
        conferidor_type = request.form.get("conferidor_type", "contabil")
        mode = request.form.get("mode")
        saldo_type = request.form.get("saldo_type", "atual")  # Capturar o tipo de saldo selecionado (padrão: "atual")
        license_code = request.form.get("license_code", "")

        if conferidor_type not in {"contabil", "folha"}:
            return render_alert("Conferidor invalido.")
        if conferidor_type == "contabil" and mode not in {"analitico", "sintetico"}:
            return render_alert("Modo de comparação inválido.")
        if conferidor_type == "contabil" and saldo_type not in {"atual", "anterior"}:
            return render_alert("Tipo de saldo inválido.")
        if not betha_file or not tce_file:
            return render_alert("Selecione os arquivos Betha e TCE.")
        if not has_allowed_extension(betha_file.filename, ALLOWED_UPLOAD_EXTENSIONS):
            return render_alert("O arquivo Betha deve estar no formato CSV.")
        if not has_allowed_extension(tce_file.filename, ALLOWED_UPLOAD_EXTENSIONS):
            return render_alert("O arquivo TCE deve estar no formato CSV.")

        # Salvar os arquivos temporariamente
        UPLOAD_DIR.mkdir(exist_ok=True)
        DATA_DIR.mkdir(exist_ok=True)
        betha_path = UPLOAD_DIR / "betha.csv"
        tce_path = UPLOAD_DIR / "tce.csv"
        betha_file.save(str(betha_path))
        tce_file.save(str(tce_path))

        try:
            if conferidor_type == "folha":
                return process_folha(betha_path, tce_path)

            entity = validate_tce_file(tce_path)
            validate_license(license_code, entity)
            validate_betha_file(betha_path)

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
                    has_sem_corresp_betha=not df_sem_corresp_betha.empty,
                    has_sem_corresp_tce=not df_sem_corresp_tce.empty,
                    sem_correspondencia_betha_html=sem_corresp_betha_html,  # Nova variável
                    sem_correspondencia_tce_html=sem_corresp_tce_html,      # Nova variável
                    comparacao_file=f"data/Comparacao_Betha_TCE_Saldo_{saldo_label}.csv",
                    diferencas_file=f"data/Diferencas_Betha_TCE_Saldo_{saldo_label}.csv",
                    sem_corresp_betha_file=f"data/Mascaras_Sem_Correspondencia_Betha_Analitico_Saldo_{saldo_label}.csv",
                    sem_corresp_tce_file=f"data/Mascaras_Sem_Correspondencia_TCE_Analitico_Saldo_{saldo_label}.csv",
                    entity=entity,
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
                        has_sem_corresp_betha=not df_sem_corresp_betha.empty,
                        has_sem_corresp_tce=not df_sem_corresp_tce.empty,
                        sem_correspondencia_betha_html=sem_corresp_betha_html,  # Nova variável
                        sem_correspondencia_tce_html=sem_corresp_tce_html,      # Nova variável
                        comparacao_file=f"data/Comparacao_Betha_TCE_Sintetico_Saldo_{saldo_label}.csv",
                        diferencas_file=f"data/Diferencas_Betha_TCE_Sintetico_Saldo_{saldo_label}.csv",
                        sem_corresp_betha_file=f"data/Mascaras_Sem_Correspondencia_Betha_Sintetico_Saldo_{saldo_label}.csv",
                        sem_corresp_tce_file=f"data/Mascaras_Sem_Correspondencia_TCE_Sintetico_Saldo_{saldo_label}.csv",
                        entity=entity,
                    )
                return render_alert("Erro ao processar no modo sintético.")
            else:
                return render_alert("Modo de comparação inválido.")
        except LicenseError as error:
            return render_alert(
                str(error),
                title="Licença não autorizada",
                detail="Confira o código da licença informado ou solicite a liberação para esta entidade.",
            )
        except UserFacingError as error:
            return render_alert(str(error))
        except conferidor_folha.ConferenciaError as error:
            return render_alert(str(error))
        except (pd.errors.ParserError, UnicodeDecodeError, KeyError, ValueError):
            return render_alert("Os arquivos enviados não estão no layout esperado.")

    return render_template("index.html", conferidor_type="contabil")


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers.pop("X-Frame-Options", None)
    response.headers["Content-Security-Policy"] = (
        "frame-ancestors 'self' "
        "http://localhost:5173 http://127.0.0.1:5173 "
        "http://localhost:5174 http://127.0.0.1:5174"
    )
    response.headers["Referrer-Policy"] = "same-origin"
    return response


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(_error):
    return render_alert("Os arquivos enviados excedem o tamanho máximo permitido."), 413


@app.route("/download/<filename>")
def download(filename):
    if os.path.basename(filename) != filename:
        abort(404)
    if not has_allowed_extension(filename, ALLOWED_DOWNLOAD_EXTENSIONS):
        abort(404)
    return send_from_directory(DATA_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG") == "1"
    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("APP_PORT", "8091"))
    app.run(host=host, port=port, debug=debug)
