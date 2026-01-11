import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, request, jsonify
import requests, time, random, string, threading

TOKEN = "MTQ2MDAzODg4Nzk3OTM1MjE2NA.GUkfhA.chxONhXukTw8Kd-jczepuSqnZjEBXMA6jzbFRI"
GUILD_ID = 1457474865673146453
ROLE_ID = 1460041416561529013
GAMEPASS_ID = 1669014534

linked = {}
codes = {}
verified = set()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
app = Flask(__name__)

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def roblox_id(username):
    r = requests.post("https://users.roblox.com/v1/usernames/users",
        json={"usernames":[username],"excludeBannedUsers":True})
    return r.json()["data"][0]["id"]

def owns_gamepass(uid):
    url = f"https://inventory.roblox.com/v1/users/{uid}/items/GamePass/{GAMEPASS_ID}"
    r = requests.get(url)
    return r.status_code == 200 and len(r.json()["data"]) > 0

@tree.command(name="roblox_gamepass_redeem")
async def redeem(interaction: discord.Interaction, username: str):
    if username in linked and linked[username] != interaction.user.id:
        await interaction.response.send_message(
            "Username already Linked To Different Discord User", ephemeral=True)
        return

    uid = roblox_id(username)
    if not owns_gamepass(uid):
        await interaction.response.send_message(
            "You do not own the required game pass", ephemeral=True)
        return

    linked[username] = interaction.user.id
    await interaction.response.send_message(
        "Success bought the game pass", ephemeral=True)

@tree.command(name="roblox_generate_code")
async def code(interaction: discord.Interaction):
    c = gen_code()
    codes[interaction.user.id] = {"code": c, "exp": time.time()+300}
    await interaction.response.send_message(
        f"Your code: `{c}` (expires in 5 minutes)", ephemeral=True)

@tree.command(name="supporter_redeem")
async def role(interaction: discord.Interaction):
    if interaction.user.id not in verified:
        await interaction.response.send_message(
            "Verify in-game first", ephemeral=True)
        return
    await interaction.user.add_roles(
        interaction.guild.get_role(ROLE_ID))
    await interaction.response.send_message(
        "Role granted", ephemeral=True)

@app.route("/verify", methods=["POST"])
def verify():
    d = request.json
    did = int(d["discord_id"])
    code = d["code"]

    if did not in codes:
        return jsonify({"valid": False})

    if time.time() > codes[did]["exp"]:
        del codes[did]
        return jsonify({"valid": False})

    if codes[did]["code"] != code:
        return jsonify({"valid": False})

    del codes[did]
    verified.add(did)
    return jsonify({"valid": True})

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("Bot Ready")

def run_api():
    app.run(host="0.0.0.0", port=3000)

threading.Thread(target=run_api).start()
bot.run(TOKEN)
