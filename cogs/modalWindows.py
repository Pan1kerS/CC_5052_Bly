import disnake
from disnake.ext import commands

class ReportModal(disnake.ui.Modal):
    def __init__(self, arg):
        self.arg = arg
        if self.arg == "operation":
            components = [
                disnake.ui.TextInput(label="Укажите КМДО", placeholder="Введите позывной КМДО", custom_id="cmdo"),
                disnake.ui.TextInput(label="Укажите участников", placeholder="Перечислите всех участников", custom_id="units")
            ]
            title = "Рапорт об операции"
        elif self.arg == "training":
            components = [
                disnake.ui.TextInput(label="Укажите проводящего", placeholder="Введите позывной проводящего", custom_id="training_leader"),
                disnake.ui.TextInput(label="Укажите участников", placeholder="Перечислите всех участников", custom_id="units_training")
            ]
            title = "Рапорт об операции"
        super().__init__(title=title, components=components, custom_id="reportModal")

    async def callback(self, interaction: disnake.ModalInteraction) -> None:
        if self.arg == "operation":
            cmdo = interaction.text_values["cmdo"]
            units = interaction.text_values["units"]
        elif self.arg == "training":
            training_leader = interaction.text_values["training_leader"]
            units_training = interaction.text_values["units_training"]

        await interaction.response.send_message(f"Рапорт отправлен!", ephemeral=True)
        channel = interaction.guild.get_channel(1334403882872475707) #Номер канала
        await channel.send(f"Рапорт да да да")

#Окно выбора ответа
class ReportSelect(disnake.ui.Select):
    def __init__(self):
        options = [
            disnake.SelectOption(label="Операция", value="operation", description="Рапорт об операции"),
            disnake.SelectOption(label="Тренировка", value="training", description="Рапорт о тренировки")
        ]

        super().__init__(
            placeholder="Выберите о чем хотите доложить", options=options, min_values=0, max_values=1, custom_id="reports"
        )

    async def callback(self, interaction: disnake.MessageInteraction):
        if not interaction.values:
            await interaction.response.defer()
        else:
            await interaction.response.send_modal(ReportModal(interaction.values[0]))

#Отправка менюшки
class ReportWindow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.persistents_views_added = False

    @commands.command()
    async def report(self, ctx):
        view = disnake.ui.View()
        view.add_item(ReportSelect())
        await ctx.send("Выберите тип доклада", view=view)

    @commands.Cog.listener()
    async def on_connect(self):
        if self.persistents_views_added:
            return

        view = disnake.ui.View(timeout=None)
        view.add_item(ReportSelect())
        self.bot.add_view(view, message_id=15891512357)


def setup(bot):
    bot.add_cog(ReportWindow(bot))