"""Parse and consolidate eSocial S-1210/IRRF beneficiary XML events."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import BytesIO
import re
from typing import Iterable

from defusedxml import ElementTree as SafeElementTree
from defusedxml.common import DefusedXmlException


ZERO = Decimal("0.00")
MONTH_NAMES = (
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
)


class ESocialError(ValueError):
    """A validation error that is safe to show to the user."""


@dataclass(frozen=True)
class MonthlyIncome:
    period: str
    taxable_income: Decimal
    inss: Decimal
    irrf: Decimal
    thirteenth_salary: Decimal

    @property
    def period_label(self) -> str:
        year, month = self.period.split("-")
        return f"{MONTH_NAMES[int(month) - 1]}/{year}"


@dataclass(frozen=True)
class IncomeReport:
    worker_cpf: str
    employer_type: str
    employer_registration: str
    months: tuple[MonthlyIncome, ...]
    source_count: int

    @property
    def worker_cpf_formatted(self) -> str:
        return format_cpf(self.worker_cpf)

    @property
    def employer_registration_formatted(self) -> str:
        return format_employer_registration(self.employer_type, self.employer_registration)

    @property
    def totals(self) -> dict[str, Decimal]:
        return {
            "taxable_income": sum((month.taxable_income for month in self.months), ZERO),
            "inss": sum((month.inss for month in self.months), ZERO),
            "irrf": sum((month.irrf for month in self.months), ZERO),
            "thirteenth_salary": sum((month.thirteenth_salary for month in self.months), ZERO),
        }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element, name: str):
    return [child for child in list(element) if _local_name(child.tag) == name]


def _first_descendant(element, name: str):
    for descendant in element.iter():
        if _local_name(descendant.tag) == name:
            return descendant
    return None


def _required_text(element, name: str, file_label: str) -> str:
    child = _first_descendant(element, name)
    value = child.text.strip() if child is not None and child.text else ""
    if not value:
        raise ESocialError(f"{file_label}: campo {name} não encontrado no XML eSocial.")
    return value


def _decimal(element, name: str, file_label: str) -> Decimal:
    child = _first_descendant(element, name)
    raw_value = child.text.strip() if child is not None and child.text else "0"
    try:
        value = Decimal(raw_value).quantize(Decimal("0.01"))
        if not value.is_finite() or value < ZERO:
            raise InvalidOperation
        return value
    except InvalidOperation as error:
        raise ESocialError(f"{file_label}: valor inválido no campo {name}.") from error


def _decimal_sum(elements, name: str, file_label: str) -> Decimal:
    return sum((_decimal(element, name, file_label) for element in elements), ZERO)


def _valid_cpf(value: str) -> bool:
    if len(value) != 11 or value == value[0] * 11:
        return False
    numbers = [int(digit) for digit in value]
    for length in (9, 10):
        total = sum(numbers[index] * (length + 1 - index) for index in range(length))
        check = (total * 10 % 11) % 10
        if numbers[length] != check:
            return False
    return True


def _parse_one(xml_bytes: bytes, file_label: str):
    if not xml_bytes or not xml_bytes.strip():
        raise ESocialError(f"{file_label}: o arquivo está vazio.")
    try:
        root = SafeElementTree.parse(BytesIO(xml_bytes)).getroot()
    except (SafeElementTree.ParseError, DefusedXmlException, ValueError) as error:
        raise ESocialError(f"{file_label}: XML inválido ou malformado.") from error

    event = _first_descendant(root, "evtIrrfBenef")
    if event is None:
        raise ESocialError(
            f"{file_label}: evento não suportado. Envie o XML eSocial de IRRF do beneficiário."
        )
    if "esocial.gov.br/schema/evt/evtIrrfBenef/" not in event.tag:
        raise ESocialError(f"{file_label}: namespace do evento eSocial não reconhecido.")

    employer = _first_descendant(event, "ideEmpregador")
    worker = _first_descendant(event, "ideTrabalhador")
    totals = _first_descendant(event, "totInfoIR")
    consolidated = _children(totals, "consolidApurMen") if totals is not None else []
    if employer is None or worker is None or not consolidated:
        raise ESocialError(f"{file_label}: o evento não contém os dados consolidados esperados.")

    period = _required_text(event, "perApur", file_label)
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", period):
        raise ESocialError(f"{file_label}: período de apuração inválido.")

    cpf = re.sub(r"\D", "", _required_text(worker, "cpfBenef", file_label))
    registration_type = _required_text(employer, "tpInsc", file_label)
    registration = re.sub(r"\D", "", _required_text(employer, "nrInsc", file_label))
    if not _valid_cpf(cpf):
        raise ESocialError(f"{file_label}: CPF do beneficiário inválido.")
    expected_lengths = {"1": {8, 14}, "2": {11}}
    if registration_type not in expected_lengths or len(registration) not in expected_lengths[registration_type]:
        raise ESocialError(f"{file_label}: inscrição do empregador inválida.")
    receipt_node = _first_descendant(event, "nrRecArqBase")
    receipt = receipt_node.text.strip() if receipt_node is not None and receipt_node.text else ""
    event_id = event.attrib.get("Id", "")

    month = MonthlyIncome(
        period=period,
        taxable_income=_decimal_sum(consolidated, "vlrRendTrib", file_label),
        inss=_decimal_sum(consolidated, "vlrPrevOficial", file_label),
        irrf=_decimal_sum(consolidated, "vlrCRMen", file_label),
        thirteenth_salary=_decimal_sum(consolidated, "vlrRendTrib13", file_label),
    )
    return (cpf, registration_type, registration, period, receipt or event_id, month)


def parse_income_report(files: Iterable[tuple[str, bytes]]) -> IncomeReport:
    """Consolidate one or more uploaded eSocial XML files into an income report."""
    parsed = []
    seen_documents = set()
    for file_label, xml_bytes in files:
        item = _parse_one(xml_bytes, file_label)
        document_key = item[4]
        if document_key and document_key in seen_documents:
            continue
        seen_documents.add(document_key)
        parsed.append(item)

    if not parsed:
        raise ESocialError("Selecione ao menos um arquivo XML eSocial válido.")

    identities = {(item[0], item[1], item[2]) for item in parsed}
    if len(identities) != 1:
        raise ESocialError("Os XMLs pertencem a trabalhadores ou empregadores diferentes.")

    months_by_period = {}
    for *_, period, _document_key, month in parsed:
        existing = months_by_period.get(period)
        if existing is not None and existing != month:
            raise ESocialError(f"Há XMLs conflitantes para o período {month.period_label}.")
        months_by_period[period] = month

    cpf, registration_type, registration = next(iter(identities))
    return IncomeReport(
        worker_cpf=cpf,
        employer_type=registration_type,
        employer_registration=registration,
        months=tuple(months_by_period[key] for key in sorted(months_by_period)),
        source_count=len(parsed),
    )


def format_cpf(value: str) -> str:
    digits = re.sub(r"\D", "", value).zfill(11)
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_employer_registration(registration_type: str, value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if registration_type == "1" and len(digits) == 8:
        return f"CNPJ raiz {digits[:2]}.{digits[2:5]}.{digits[5:]}"
    if registration_type == "1" and len(digits) == 14:
        return f"CNPJ {digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    if registration_type == "2" and len(digits) == 11:
        return f"CPF {format_cpf(digits)}"
    return f"Inscrição {digits}"
