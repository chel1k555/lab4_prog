from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re

PHONE_RE = re.compile(r"^\+\d-\d{3}-\d{3}-\d{2}-\d{2}$")
PRIORITY_ORDER = {"MAX": 0, "MIDDLE": 1, "LOW": 2}


@dataclass(frozen=True)
class Order:
    number: str
    products: str
    customer: str
    address: str
    phone: str
    priority: str


def parse_order(line: str) -> Order:
    fields = line.rstrip("\n\r").split(";")
    if len(fields) != 6:
        raise ValueError("Order must contain exactly 6 fields")
    return Order(*fields)


def validate_order(order: Order) -> list[tuple[int, str]]:
    """Return (error_type, invalid_value) pairs for address and phone."""
    errors: list[tuple[int, str]] = []

    address_parts = [part.strip() for part in order.address.split(".")]
    if (
        not order.address.strip()
        or len(address_parts) != 4
        or any(not part for part in address_parts)
    ):
        errors.append((1, order.address if order.address else "no data"))

    if not PHONE_RE.fullmatch(order.phone):
        errors.append((2, order.phone if order.phone else "no data"))

    return errors


def format_products(products: str) -> str:
    names = [item.strip() for item in products.split(",") if item.strip()]
    counts = Counter(names)
    result = []
    for name in dict.fromkeys(names):
        count = counts[name]
        result.append(f"{name} x{count}" if count > 1 else name)
    return ", ".join(result)


def format_address(address: str) -> str:
    parts = [part.strip() for part in address.split(".")]
    return ". ".join(parts[1:])


def country(address: str) -> str:
    return address.split(".", 1)[0].strip()


def format_valid_order(order: Order) -> str:
    return ";".join(
        (
            order.number,
            format_products(order.products),
            order.customer,
            format_address(order.address),
            order.phone,
            order.priority,
        )
    )


def process_orders(
    input_file: str | Path = "orders.txt",
    output_file: str | Path = "order_country.txt",
    invalid_file: str | Path = "non_valid_orders.txt",
) -> None:
    input_path = Path(input_file)
    valid_orders: list[Order] = []
    invalid_lines: list[str] = []

    with input_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            if not raw_line.strip():
                continue

            order = parse_order(raw_line)
            errors = validate_order(order)

            for error_type, value in errors:
                invalid_lines.append(f"{order.number};{error_type};{value}")

            if not errors:
                valid_orders.append(order)

    def sort_key(order: Order):
        c = country(order.address)
        return (0 if c == "Россия" else 1, c.casefold(), PRIORITY_ORDER[order.priority])

    valid_orders.sort(key=sort_key)

    Path(output_file).write_text(
        "\n".join(format_valid_order(order) for order in valid_orders)
        + ("\n" if valid_orders else ""),
        encoding="utf-8",
    )
    Path(invalid_file).write_text(
        "\n".join(invalid_lines) + ("\n" if invalid_lines else ""),
        encoding="utf-8",
    )


def main() -> None:
    process_orders()


if __name__ == "__main__":
    main()
