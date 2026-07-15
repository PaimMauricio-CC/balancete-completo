def esocial_xml(
    period="2026-01",
    income="1000.00",
    inss="100.00",
    irrf="50.00",
    thirteenth="0.00",
    receipt=None,
    extra_consolidated="",
):
    receipt = receipt or f"1.1.{period.replace('-', '')}"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<eSocial xmlns="http://www.esocial.gov.br/schema/eventoCompleto/retornoEventoCompleto/v1_0_0">
  <retornoEventoCompleto><evento>
    <eSocial xmlns="http://www.esocial.gov.br/schema/evt/evtIrrfBenef/v_S_01_03_00">
      <evtIrrfBenef Id="ID{period.replace('-', '')}">
        <ideEvento><nrRecArqBase>{receipt}</nrRecArqBase><perApur>{period}</perApur></ideEvento>
        <ideEmpregador><tpInsc>1</tpInsc><nrInsc>12345678</nrInsc></ideEmpregador>
        <ideTrabalhador><cpfBenef>12345678909</cpfBenef><totInfoIR>
          <consolidApurMen><CRMen>056107</CRMen><vlrRendTrib>{income}</vlrRendTrib><vlrRendTrib13>{thirteenth}</vlrRendTrib13><vlrPrevOficial>{inss}</vlrPrevOficial><vlrPrevOficial13>0</vlrPrevOficial13><vlrCRMen>{irrf}</vlrCRMen></consolidApurMen>
          {extra_consolidated}
        </totInfoIR></ideTrabalhador>
      </evtIrrfBenef>
    </eSocial>
  </evento></retornoEventoCompleto>
</eSocial>""".encode()


def reference_files():
    values = [
        ("2026-01", "5880.00", "0.00", "512.54"),
        ("2026-02", "6109.32", "0.00", "606.14"),
        ("2026-03", "6109.32", "0.00", "606.14"),
        ("2026-04", "6109.32", "0.00", "606.14"),
        ("2026-05", "6109.32", "656.80", "606.14"),
        ("2026-06", "6109.32", "656.80", "606.14"),
    ]
    return [
        (f"evento-{period}.xml", esocial_xml(period, income, inss, irrf))
        for period, income, inss, irrf in values
    ]
