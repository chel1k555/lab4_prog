import tempfile
import unittest
from pathlib import Path

from orders import (
    Order,
    country,
    format_products,
    process_orders,
    validate_order,
)


class ValidationTests(unittest.TestCase):
    def test_valid_phone(self):
        order = Order("12345", "Хлеб", "Иванов Иван", "Россия. Москва. Москва. Ленина", "+7-123-456-78-90", "MAX")
        self.assertEqual(validate_order(order), [])

    def test_invalid_phone(self):
        order = Order("12345", "Хлеб", "Иванов Иван", "Россия. Москва. Москва. Ленина", "+34-93-1234-567", "MAX")
        self.assertEqual(validate_order(order), [(2, "+34-93-1234-567")])

    def test_empty_phone(self):
        order = Order("12345", "Хлеб", "Иванов Иван", "Россия. Москва. Москва. Ленина", "", "MAX")
        self.assertEqual(validate_order(order), [(2, "no data")])

    def test_invalid_address(self):
        order = Order("12345", "Хлеб", "Иванов Иван", "Япония. Шибуя. Шибуя-кроссинг", "+7-123-456-78-90", "MAX")
        self.assertEqual(
            validate_order(order),
            [(1, "Япония. Шибуя. Шибуя-кроссинг")],
        )

    def test_empty_address(self):
        order = Order("12345", "Хлеб", "Иванов Иван", "", "+7-123-456-78-90", "MAX")
        self.assertEqual(validate_order(order), [(1, "no data")])

    def test_multiple_errors(self):
        order = Order("12345", "Хлеб", "Иванов Иван", "Япония. Шибуя. Шибуя-кроссинг", "+34-93-1234-567", "MAX")
        self.assertEqual(
            validate_order(order),
            [(1, "Япония. Шибуя. Шибуя-кроссинг"), (2, "+34-93-1234-567")],
        )


class FormattingTests(unittest.TestCase):
    def test_products_are_counted_and_first_order_preserved(self):
        self.assertEqual(
            format_products("Сыр, Колбаса, Сыр, Макароны, Колбаса"),
            "Сыр x2, Колбаса x2, Макароны",
        )

    def test_single_products_have_no_x1(self):
        self.assertEqual(
            format_products("Молоко, Яблоки, Хлеб, Яблоки, Молоко"),
            "Молоко x2, Яблоки x2, Хлеб",
        )


class IntegrationTests(unittest.TestCase):
    SAMPLE = """\
31987;Сыр, Колбаса, Сыр, Макароны, Колбаса;Петрова Анна;Россия. Ленинградская область. Санкт-Петербург. набережная реки Фонтанки;+7-921-456-78-90;MIDDLE
87459;Молоко, Яблоки, Хлеб, Яблоки, Молоко;Иванов Иван Иванович;Россия. Московская область. Москва. улица Пушкина;+7-912-345-67-89;MAX
31987;Сыр, Колбаса, Макароны, Сыр, Колбаса;Петрова Анна Сергеевна;Франция. Иль-де-Франс. Париж. Шанз-Элизе;+3-214-020-50-50;MIDDLE
56342;Хлеб, Молоко, Хлеб, Молоко;Смирнова Мария Леонидовна;Германия. Бавария. Мюнхен. Мариенплац;+4-989-234-56;LOW
48276;Яблоки, Макароны, Яблоки;Алексеев Алексей Алексеевич;Италия. Лацио. Рим. Колизей;+3-061-234-56-78;MAX
65829;Сок, Вода, Сок, Вода;Белова Екатерина Михайловна;Испания. Каталония. Барселона. Рамбла;+34-93-1234-567;LOW
72901;Чай, Кофе, Чай, Кофе;Михайлов Сергей Петрович;Великобритания. Англия. Лондон. Бейкер-стрит;+4-207-946-09-58;LOW
84756;Печенье, Сыр, Печенье, Сыр;Васильева Анна Владимировна;Япония. Шибуя. Шибуя-кроссинг;+8-131-234-5678;MAX
90385;Макароны, Сыр, Макароны, Сыр;Николаев Николай;;+1-416-123-45-67;LOW
"""

    def test_process_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            input_file = tmp / "orders.txt"
            output_file = tmp / "order_country.txt"
            invalid_file = tmp / "non_valid_orders.txt"
            input_file.write_text(self.SAMPLE, encoding="utf-8")

            process_orders(input_file, output_file, invalid_file)

            self.assertEqual(
                output_file.read_text(encoding="utf-8"),
                """\
87459;Молоко x2, Яблоки x2, Хлеб;Иванов Иван Иванович;Московская область. Москва. улица Пушкина;+7-912-345-67-89;MAX
31987;Сыр x2, Колбаса x2, Макароны;Петрова Анна;Ленинградская область. Санкт-Петербург. набережная реки Фонтанки;+7-921-456-78-90;MIDDLE
72901;Чай x2, Кофе x2;Михайлов Сергей Петрович;Англия. Лондон. Бейкер-стрит;+4-207-946-09-58;LOW
48276;Яблоки x2, Макароны;Алексеев Алексей Алексеевич;Лацио. Рим. Колизей;+3-061-234-56-78;MAX
31987;Сыр x2, Колбаса x2, Макароны;Петрова Анна Сергеевна;Иль-де-Франс. Париж. Шанз-Элизе;+3-214-020-50-50;MIDDLE
""",
            )

            self.assertEqual(
                invalid_file.read_text(encoding="utf-8"),
                """\
56342;2;+4-989-234-56
65829;2;+34-93-1234-567
84756;1;Япония. Шибуя. Шибуя-кроссинг
84756;2;+8-131-234-5678
90385;1;no data
""",
            )


if __name__ == "__main__":
    unittest.main()
