import disnake
from disnake.ext import commands
from config import CHANNELS, REPORTS, CHANNEL_TO_REPORT

class SetupButtons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="setup_buttons",
        description="Настроить кнопки для отчетов"
    )
    @commands.has_permissions(administrator=True)
    async def setup_buttons(self, interaction: disnake.ApplicationCommandInteraction):
        # Отправляем кнопки в каждый канал
        for channel_id in CHANNEL_TO_REPORT.keys():
            channel = interaction.guild.get_channel(channel_id)
            if channel:
                report_type = CHANNEL_TO_REPORT[channel_id]
                config = REPORTS[report_type]
                
                view = disnake.ui.View(timeout=None)
                button = disnake.ui.Button(
                    style=disnake.ButtonStyle.primary,
                    label=config['label'],
                    custom_id=config['custom_id']
                )
                view.add_item(button)

                # Привязываем колбэк к кнопке
                if config['custom_id'] == "report_combat_button":
                    button.callback = self.bot.get_cog('ReportOperation').start_report
                elif config['custom_id'] == "report_training_button":
                    button.callback = self.bot.get_cog('ReportTraining').start_report
                elif config['custom_id'] == "report_holiday_button":
                    button.callback = self.bot.get_cog('ReportHoliday').start_report
                elif config['custom_id'] == "report_rank_button":
                    button.callback = self.bot.get_cog('ReportRank').start_report
                elif config['custom_id'] == "report_attestation_button":
                    button.callback = self.bot.get_cog('ReportAttestation').start_report
                elif config['custom_id'] == "report_recommendation_button":
                    button.callback = self.bot.get_cog('ReportRecommendation').start_report
                elif config['custom_id'] == "report_reprimand_button":
                    button.callback = self.bot.get_cog('ReportReprimand').start_report

                embed = disnake.Embed(
                    title=config['title'],
                    description=config['description'],
                    color=disnake.Color.blue()
                )
                await channel.send(embed=embed, view=view)

        await interaction.response.send_message("Кнопки успешно настроены!", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        custom_id = interaction.component.custom_id
        for config in REPORTS.values():
            if config['custom_id'] == custom_id:
                command = self.bot.get_slash_command(config['command'])
                if command:
                    await command(interaction)
                break

    @commands.slash_command(
        name="setup_personal_file",
        description="Настроить кнопку личного дела"
    )
    @commands.has_permissions(administrator=True)
    async def setup_personal_file(self, interaction: disnake.ApplicationCommandInteraction):
        channel = interaction.guild.get_channel(1339829150113992745)
        if not channel:
            await interaction.response.send_message(
                "Канал для личного дела не найден!",
                ephemeral=True
            )
            return

        # Очищаем канал от старых сообщений, кроме последнего (если это кнопка)
        async for message in channel.history(limit=100):
            # Проверяем, есть ли у сообщения компоненты (кнопки)
            if not message.components:
                await message.delete()

        # Проверяем, есть ли уже кнопка в канале
        has_button = False
        async for message in channel.history(limit=1):
            if message.components:  # Если последнее сообщение содержит кнопку
                has_button = True
                break

        # Отправляем новую кнопку только если её ещё нет
        if not has_button:
            view = disnake.ui.View(timeout=None)
            personal_file_button = disnake.ui.Button(
                style=disnake.ButtonStyle.secondary,
                label="📋 Личное дело",
                custom_id="personal_file"
            )
            view.add_item(personal_file_button)

            embed = disnake.Embed(
                title="Личное дело",
                description="Нажмите на кнопку, чтобы посмотреть свое личное дело",
                color=disnake.Color.blue()
            )
            await channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "Канал личного дела успешно настроен!",
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(SetupButtons(bot)) 