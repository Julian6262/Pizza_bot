from aiogram.utils.formatting import as_list, as_marked_section, Bold, Italic, Underline

text = as_list(
    as_marked_section(
        Bold("Варианты доставки/заказа:"),
        Italic("Курьер"),
        Underline("Самовынос (сейчас прибегу заберу)"),
        "Покушаю у Вас (сейчас прибегу)",
        marker='✅ '
    ),
    as_marked_section(
        Bold("Нельзя:"),
        "Почта",
        "Голуби",
        marker='❌ '
    ),
    sep='\n----------------------\n'
)
